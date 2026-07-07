import secrets
import uuid

from app.config import get_settings
from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import create_candidat_access_token

settings = get_settings()

_PREFIXE_CLE_OTP = "candidat:otp:"
_PREFIXE_CLE_VERROUILLAGE = "candidat:otp_lockout:"


def _cle_otp(telephone: str) -> str:
    return f"{_PREFIXE_CLE_OTP}{telephone}"


def _cle_verrouillage(telephone: str) -> str:
    return f"{_PREFIXE_CLE_VERROUILLAGE}{telephone}"


class AuthCandidatService:
    """Authentification candidat par OTP SMS (docs/PROFIL_CANDIDAT_UNIFIE.md § 4.2, § 8).
    L'envoi SMS est un stub en Phase 1 (voir NotificationEngine) : le code est généré et
    stocké, mais ce service ne l'envoie pas lui-même — l'appelant décide du canal.

    Le verrouillage après échecs répétés porte sur le **numéro de téléphone**
    (`candidat_otp_lockout_minutes`, une clé de cache distincte de l'OTP lui-même) :
    demander un nouveau code pendant la fenêtre de verrouillage ne le contourne pas,
    contrairement à une version antérieure qui ne verrouillait que le code courant."""

    @staticmethod
    async def est_verrouille(telephone: str) -> bool:
        return await cache_get(_cle_verrouillage(telephone)) is not None

    @staticmethod
    async def generer_otp(telephone: str) -> str | None:
        """Génère un code à 6 chiffres et le stocke (TTL configurable). Renvoie `None`
        si le numéro est actuellement verrouillé (trop de tentatives échouées
        récemment) : l'appelant ne doit alors envoyer aucun SMS."""
        if await AuthCandidatService.est_verrouille(telephone):
            return None

        code = f"{secrets.randbelow(1_000_000):06d}"
        await cache_set(
            _cle_otp(telephone),
            {"code": code, "tentatives": 0},
            ttl_secondes=settings.candidat_otp_expire_minutes * 60,
        )
        return code

    @staticmethod
    async def verifier_otp(telephone: str, code: str) -> bool:
        """Consomme une tentative. Le code est invalidé après un succès ; après avoir
        atteint le nombre maximal de tentatives, le **numéro** est verrouillé pendant
        `candidat_otp_lockout_minutes`, indépendamment de toute nouvelle génération
        de code (anti brute-force sur 6 chiffres)."""
        if await AuthCandidatService.est_verrouille(telephone):
            return False

        cle = _cle_otp(telephone)
        entree = await cache_get(cle)
        if entree is None:
            return False

        if entree["tentatives"] >= settings.candidat_otp_max_tentatives:
            await cache_delete(cle)
            await cache_set(
                _cle_verrouillage(telephone),
                {"verrouille": True},
                ttl_secondes=settings.candidat_otp_lockout_minutes * 60,
            )
            return False

        if entree["code"] != code:
            entree["tentatives"] += 1
            await cache_set(cle, entree, ttl_secondes=settings.candidat_otp_expire_minutes * 60)
            return False

        await cache_delete(cle)
        return True

    @staticmethod
    def creer_session(profil_id: uuid.UUID) -> str:
        return create_candidat_access_token(subject=str(profil_id))
