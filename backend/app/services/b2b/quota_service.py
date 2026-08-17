import uuid
from datetime import UTC, datetime

from app.core.cache import cache_get, cache_set

_PREFIXE_CLE_QUOTA = "b2b:quota:"
_TTL_QUOTA_SECONDES = 26 * 3600  # marge sur 24h pour couvrir tout le jour calendaire


def _cle_quota(api_key_id: uuid.UUID, jour: str) -> str:
    return f"{_PREFIXE_CLE_QUOTA}{api_key_id}:{jour}"


async def consommer_quota(api_key_id: uuid.UUID, quota_quotidien: int) -> bool:
    """Incrémente le compteur d'appels du jour pour cette clé et renvoie False si le
    quota quotidien est dépassé. Lecture puis écriture (non atomique), comme le
    compteur de tentatives OTP (`AuthCandidatService`) — un quota B2B indicatif,
    pas une limite de facturation stricte (pas de facturation automatisée pour
    l'instant, voir docs/ROADMAP.md § Phase 4)."""
    jour = datetime.now(UTC).date().isoformat()
    cle = _cle_quota(api_key_id, jour)
    compteur = await cache_get(cle) or 0
    if compteur >= quota_quotidien:
        return False
    await cache_set(cle, compteur + 1, ttl_secondes=_TTL_QUOTA_SECONDES)
    return True
