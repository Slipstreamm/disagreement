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


def test_get_or_fetch_uses_cache():
    cache = Cache()
    cache.set("a", 1)

    def fetch():
        raise AssertionError("fetch should not be called")

    assert cache.get_or_fetch("a", fetch) == 1


def test_get_or_fetch_fetches_and_stores():
    cache = Cache()
    called = False

    def fetch():
        nonlocal called
        called = True
        return 2

    assert cache.get_or_fetch("b", fetch) == 2
    assert called
    assert cache.get("b") == 2


def test_get_or_fetch_fetches_expired_item():
    cache = Cache(ttl=0.01)
    cache.set("c", 1)
    time.sleep(0.02)
    called = False

    def fetch():
        nonlocal called
        called = True
        return 3

    assert cache.get_or_fetch("c", fetch) == 3
    assert called
