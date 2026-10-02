from functools import lru_cache
from typing import Literal

from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict

_MESSAGE_CLE_CHIFFREMENT_INVALIDE = (
    "CANDIDAT_ENCRYPTION_KEY manquante ou invalide. Générer une clé avec : "
    'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
)

# Valeurs par défaut de développement, publiques dans le code source : jamais
# acceptables en production (audit 2026-07-08). Contrairement à
# candidat_encryption_key, ces deux champs ont une valeur par défaut
# fonctionnelle (l'app démarre sans .env local) — le risque est donc qu'un
# déploiement production oublie de les surcharger et démarre quand même,
# silencieusement vulnérable (JWT forgeables, pepper de hash public).
_VALEURS_DEV_INSECURES = {
    "jwt_secret_key": "change-me-in-production",
    "candidat_hash_pepper": "change-me-in-production",
    "api_key_pepper": "change-me-in-production",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "staging", "production"] = "development"
    cors_origins: str = "http://localhost:8080"

    database_url: str = "postgresql+asyncpg://faso:faso_secret@db:5432/faso_resultats"

    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 300

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Profil candidat (plateforme, transversal aux tenants) — docs/PROFIL_CANDIDAT_UNIFIE.md
    candidat_jwt_expire_minutes: int = 60 * 24 * 30  # session 30 jours (§ 4.2)
    # Pas de valeur par défaut fonctionnelle : une clé de chiffrement partagée par tout
    # déploiement qui oublierait de la surcharger serait un risque de sécurité réel
    # (déchiffrement de tous les CNIB/téléphones/dates de naissance avec la clé publiée
    # dans le code source). Validée au premier accès aux settings, voir get_settings().
    candidat_encryption_key: str | None = None
    candidat_hash_pepper: str = "change-me-in-production"
    candidat_otp_expire_minutes: int = 5
    candidat_otp_max_tentatives: int = 3
    # Verrouillage du numéro de téléphone après candidat_otp_max_tentatives échecs,
    # indépendant de toute nouvelle génération de code (sans quoi redemander un OTP
    # débloquait immédiatement le numéro — voir docs/ROADMAP.md, correctif de sécurité).
    candidat_otp_lockout_minutes: int = 15
    candidat_abus_seuil_rejets_par_jour: int = 5
    candidat_abus_taux_rejet_suspension: float = 0.3
    candidat_abus_minimum_tentatives: int = 5
    # Rétention (docs/PROFIL_CANDIDAT_UNIFIE.md § 7, docs/CIL_PROFIL_CANDIDAT.md § 5) :
    # durées provisoires, à valider avec la CIL avant mise en production réelle.
    candidat_purge_candidature_resiliee_jours: int = 180  # 6 mois, § 7
    candidat_purge_inactivite_jours: int = 730  # 2 ans, valeur provisoire non validée CIL
    # Canal de contact dédié aux demandes d'exercice de droits qui ne passent pas par
    # les endpoints existants (docs/CIL_PROFIL_CANDIDAT.md § 8) — à remplacer par une
    # vraie adresse avant mise en production.
    candidat_dpo_contact_email: str = "dpo@fasoresultats.bf"

    rate_limit_public: str = "30/minute"
    rate_limit_login: str = "5/minute"
    # Where request counters live. "memory://" counts per process: fine for one dev
    # server, wrong with several uvicorn workers (each worker gets its own quota). In
    # production, point it at Redis (e.g. redis://redis:6379/1) so all workers share
    # the counters.
    rate_limit_storage_uri: str = "memory://"
    # Verrouillage de compte admin après échecs répétés (audit 2026-08-17) :
    # indépendant du rate-limit IP ci-dessus, qui ne protège pas contre un
    # brute-force distribué sur plusieurs IP visant un seul compte.
    admin_login_max_tentatives: int = 5
    admin_login_lockout_minutes: int = 15

    # API B2B (Phase 4, docs/ROADMAP.md) — pepper dédié : jamais le même que
    # candidat_hash_pepper, un domaine de secret différent (clés API partenaires,
    # pas des données candidat).
    api_key_pepper: str = "change-me-in-production"

    uploads_dir: str = "/app/uploads"
    max_upload_size_mb: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def _valider_cle_chiffrement_candidat(cle: str | None) -> None:
    if not cle:
        raise RuntimeError(_MESSAGE_CLE_CHIFFREMENT_INVALIDE)
    try:
        Fernet(cle.encode())
    except Exception as exc:
        raise RuntimeError(_MESSAGE_CLE_CHIFFREMENT_INVALIDE) from exc


def _valider_secrets_production(settings: Settings) -> None:
    if settings.environment != "production":
        return
    champs_non_surcharges = [
        champ
        for champ, defaut in _VALEURS_DEV_INSECURES.items()
        if getattr(settings, champ) == defaut
    ]
    if champs_non_surcharges:
        noms = ", ".join(champ.upper() for champ in champs_non_surcharges)
        raise RuntimeError(
            f"ENVIRONMENT=production mais {noms} garde sa valeur de développement "
            "par défaut (publique dans le code source). Définir une vraie valeur "
            "secrète via les variables d'environnement avant de démarrer."
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _valider_cle_chiffrement_candidat(settings.candidat_encryption_key)
    _valider_secrets_production(settings)
    return settings
