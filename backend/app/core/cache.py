"""Cache Redis avec repli en mémoire si Redis est indisponible (voir CLAUDE.md :
« Cache agressif obligatoire (Redis, fallback mémoire) »).
"""

import asyncio
import json
import time
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

_cache_memoire: dict[str, tuple[float, str]] = {}
# Bound on the fallback cache: keys embed user input (one per PV number searched), so
# with Redis down on a proclamation day an unbounded dict would grow with every
# distinct search until the process runs out of memory.
TAILLE_MAX_CACHE_MEMOIRE = 10_000
_redis_client: redis.Redis | None = None
_redis_client_loop: asyncio.AbstractEventLoop | None = None


def _get_redis_client() -> redis.Redis:
    """Un client par event loop actif : en production il n'y en a qu'un (celui d'uvicorn),
    donc le client est créé une seule fois. En tests, chaque test peut tourner sur une
    nouvelle event loop ; réutiliser un client lié à une loop fermée casse la connexion,
    d'où la recréation automatique si la loop courante a changé.
    """
    global _redis_client, _redis_client_loop
    loop = asyncio.get_running_loop()
    if _redis_client is None or _redis_client_loop is not loop:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=1)
        _redis_client_loop = loop
    return _redis_client


async def cache_get(cle: str) -> Any | None:
    try:
        valeur = await _get_redis_client().get(cle)
        if valeur is not None:
            return json.loads(valeur)
        return None
    except (redis.RedisError, OSError):
        entree = _cache_memoire.get(cle)
        if entree is None:
            return None
        expiration, valeur_brute = entree
        if expiration < time.monotonic():
            _cache_memoire.pop(cle, None)
            return None
        return json.loads(valeur_brute)


async def cache_set(cle: str, valeur: Any, ttl_secondes: int) -> None:
    payload = json.dumps(valeur)
    try:
        await _get_redis_client().set(cle, payload, ex=ttl_secondes)
    except (redis.RedisError, OSError):
        if len(_cache_memoire) >= TAILLE_MAX_CACHE_MEMOIRE and cle not in _cache_memoire:
            _liberer_place()
        _cache_memoire[cle] = (time.monotonic() + ttl_secondes, payload)


def _liberer_place() -> None:
    """Drops expired entries; if none expired, the oldest inserted ones (dicts keep
    insertion order), a tenth of the cache at once so this rarely runs."""
    maintenant = time.monotonic()
    for cle in [c for c, (expiration, _) in _cache_memoire.items() if expiration < maintenant]:
        del _cache_memoire[cle]
    if len(_cache_memoire) >= TAILLE_MAX_CACHE_MEMOIRE:
        for cle in list(_cache_memoire)[: TAILLE_MAX_CACHE_MEMOIRE // 10]:
            del _cache_memoire[cle]


async def cache_delete(cle: str) -> None:
    _cache_memoire.pop(cle, None)
    try:
        await _get_redis_client().delete(cle)
    except (redis.RedisError, OSError):
        pass


async def cache_clear() -> None:
    """Vide le cache (Redis + mémoire). Utilisé entre les tests pour éviter les fuites d'état."""
    _cache_memoire.clear()
    try:
        await _get_redis_client().flushdb()
    except (redis.RedisError, OSError):
        pass
