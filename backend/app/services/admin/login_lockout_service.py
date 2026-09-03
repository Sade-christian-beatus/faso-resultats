from app.config import get_settings
from app.core.cache import cache_delete, cache_get, cache_set

settings = get_settings()

_PREFIXE_CLE_TENTATIVES = "admin:login_tentatives:"
_PREFIXE_CLE_VERROUILLAGE = "admin:login_lockout:"


def _cle_tentatives(email: str) -> str:
    return f"{_PREFIXE_CLE_TENTATIVES}{email.lower()}"


def _cle_verrouillage(email: str) -> str:
    return f"{_PREFIXE_CLE_VERROUILLAGE}{email.lower()}"


class AdminLoginLockoutService:
    """Verrouille un compte admin après des échecs de connexion répétés (audit
    2026-08-17), indépendamment du rate-limit IP (`RATE_LIMIT_LOGIN`) qui ne protège
    pas contre un brute-force distribué sur plusieurs IP visant un seul compte. Même
    schéma que le verrouillage OTP candidat (`AuthCandidatService`) : le verrou porte
    sur l'identifiant du compte (l'email), pas sur une tentative isolée — redemander
    ne le contourne pas.

    Verrouille aussi bien un email inexistant qu'un email réel : le comportement est
    identique dans les deux cas, donc ce mécanisme ne permet pas de deviner si un
    compte existe."""

    @staticmethod
    async def est_verrouille(email: str) -> bool:
        return await cache_get(_cle_verrouillage(email)) is not None

    @staticmethod
    async def enregistrer_echec(email: str) -> None:
        cle = _cle_tentatives(email)
        tentatives = (await cache_get(cle) or 0) + 1
        ttl = settings.admin_login_lockout_minutes * 60
        if tentatives >= settings.admin_login_max_tentatives:
            await cache_delete(cle)
            await cache_set(_cle_verrouillage(email), {"verrouille": True}, ttl_secondes=ttl)
            return
        await cache_set(cle, tentatives, ttl_secondes=ttl)

    @staticmethod
    async def reinitialiser(email: str) -> None:
        await cache_delete(_cle_tentatives(email))
