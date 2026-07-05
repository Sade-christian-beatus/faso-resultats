import secrets
import uuid

from app.config import get_settings
from app.core.cache import cache_delete, cache_get, cache_set
from app.core.security import create_candidat_access_token

settings = get_settings()

_PREFIXE_CLE_OTP = "candidat:otp:"


def _cle_otp(telephone: str) -> str:
    return f"{_PREFIXE_CLE_OTP}{telephone}"


class AuthCandidatService:
    """Authentification candidat par OTP SMS (docs/PROFIL_CANDIDAT_UNIFIE.md § 4.2, § 8).
    L'envoi SMS est un stub en Phase 1 (voir NotificationEngine) : le code est généré et
    stocké, mais ce service ne l'envoie pas lui-même — l'appelant décide du canal."""

    @staticmethod
    async def generer_otp(telephone: str) -> str:
        """Génère un code à 6 chiffres, le stocke (TTL configurable, 3 tentatives max),
        et le renvoie pour que l'appelant l'achemine (SMS réel en phase 2, log en dev)."""
        code = f"{secrets.randbelow(1_000_000):06d}"
        await cache_set(
            _cle_otp(telephone),
            {"code": code, "tentatives": 0},
            ttl_secondes=settings.candidat_otp_expire_minutes * 60,
        )
        return code

    @staticmethod
    async def verifier_otp(telephone: str, code: str) -> bool:
        """Consomme une tentative. Le code est invalidé après un succès ou après avoir
        atteint le nombre maximal de tentatives (anti brute-force sur 6 chiffres)."""
        cle = _cle_otp(telephone)
        entree = await cache_get(cle)
        if entree is None:
            return False

        if entree["tentatives"] >= settings.candidat_otp_max_tentatives:
            await cache_delete(cle)
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
