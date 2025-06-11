import time

from disagreement.cache import Cache


def test_cache_store_and_get():
    cache = Cache()
    cache.set("a", 123)
    assert cache.get("a") == 123


def test_cache_ttl_expiry():
    cache = Cache(ttl=0.01)
    cache.set("b", 1)
    assert cache.get("b") == 1
    time.sleep(0.02)
    assert cache.get("b") is None


def test_cache_lru_eviction():
    cache = Cache(maxlen=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
