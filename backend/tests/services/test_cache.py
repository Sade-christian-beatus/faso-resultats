import pytest
import redis.asyncio as redis

from app.core import cache


class _RedisIndisponible:
    async def get(self, cle: str) -> None:
        raise redis.RedisError("Redis indisponible")

    async def set(self, cle: str, valeur: str, ex: int) -> None:
        raise redis.RedisError("Redis indisponible")


@pytest.fixture(autouse=True)
def _forcer_redis_indisponible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache, "_get_redis_client", lambda: _RedisIndisponible())


@pytest.mark.asyncio
async def test_cache_utilise_la_memoire_si_redis_indisponible() -> None:
    await cache.cache_set("cle-test", {"valeur": 42}, ttl_secondes=60)

    assert await cache.cache_get("cle-test") == {"valeur": 42}


@pytest.mark.asyncio
async def test_cache_memoire_respecte_le_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    horloge = {"maintenant": 1000.0}
    monkeypatch.setattr(cache.time, "monotonic", lambda: horloge["maintenant"])

    await cache.cache_set("cle-expiree", "valeur", ttl_secondes=10)
    horloge["maintenant"] += 11

    assert await cache.cache_get("cle-expiree") is None


@pytest.mark.asyncio
async def test_cache_get_absent_renvoie_none() -> None:
    assert await cache.cache_get("cle-inexistante") is None
