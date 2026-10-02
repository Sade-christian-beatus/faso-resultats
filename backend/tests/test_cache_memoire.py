"""Fallback in-memory cache (Redis unavailable): must stay bounded."""

import pytest

from app.core import cache


@pytest.fixture(autouse=True)
def _petit_cache(monkeypatch):
    monkeypatch.setattr(cache, "TAILLE_MAX_CACHE_MEMOIRE", 10)
    cache._cache_memoire.clear()
    yield
    cache._cache_memoire.clear()


@pytest.mark.asyncio
async def test_le_cache_memoire_reste_borne_sans_redis():
    # No Redis in the test environment: every write goes to the fallback.
    for i in range(50):
        await cache.cache_set(f"public:results:{i}", {"i": i}, 300)

    assert len(cache._cache_memoire) <= 10
    # The most recent searches are still served.
    assert await cache.cache_get("public:results:49") == {"i": 49}


@pytest.mark.asyncio
async def test_les_entrees_expirees_sont_liberees_en_premier():
    for i in range(5):
        await cache.cache_set(f"vieux:{i}", i, -1)  # already expired
    for i in range(5):
        await cache.cache_set(f"frais:{i}", i, 300)

    await cache.cache_set("nouveau", "x", 300)

    assert all(not cle.startswith("vieux:") for cle in cache._cache_memoire)
    for i in range(5):
        assert await cache.cache_get(f"frais:{i}") == i
    assert await cache.cache_get("nouveau") == "x"
