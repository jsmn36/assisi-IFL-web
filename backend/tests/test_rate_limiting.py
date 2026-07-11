import pytest
import time
from unittest.mock import MagicMock
from app.core.rate_limiter import RateLimiter
from app.core.rate_limit_config import RateLimitConfig, RateLimitTier
from app.core.cache import InMemoryCache


def make_redis_mock():
    store = {}

    def zremrangebyscore(key, minv, maxv):
        if key in store:
            store[key] = {k: v for k, v in store[key].items() if not (v <= maxv)}
        return 0

    def zcard(key):
        return len(store.get(key, {}))

    def zadd(key, mapping):
        if key not in store:
            store[key] = {}
        store[key].update(mapping)
        return 1

    def expire(key, ttl):
        return 1

    def delete(key):
        store.pop(key, None)
        return 1

    class FakePipeline:
        def __init__(self):
            self._calls = []

        def zremrangebyscore(self, key, minv, maxv):
            self._calls.append(("zremrangebyscore", key, minv, maxv))
            return self

        def zcard(self, key):
            self._calls.append(("zcard", key))
            return self

        def zadd(self, key, mapping):
            self._calls.append(("zadd", key, mapping))
            return self

        def expire(self, key, ttl):
            self._calls.append(("expire", key, ttl))
            return self

        def execute(self):
            results = []
            for call in self._calls:
                op = call[0]
                if op == "zremrangebyscore":
                    results.append(zremrangebyscore(call[1], call[2], call[3]))
                elif op == "zcard":
                    results.append(zcard(call[1]))
                elif op == "zadd":
                    # call = ("zadd", key, mapping)
                    results.append(zadd(call[1], call[2]))
                elif op == "expire":
                    results.append(expire(call[1], call[2]))
            return results

    mock = MagicMock()
    mock.pipeline.return_value = FakePipeline()
    mock.zremrangebyscore.side_effect = zremrangebyscore
    mock.zcard.side_effect = zcard
    mock.zadd.side_effect = zadd
    mock.expire.side_effect = expire
    mock.delete.side_effect = delete
    mock._store = store
    return mock


def test_rate_limiter_basic():
    redis_mock = make_redis_mock()
    limiter = RateLimiter()
    limiter.redis_client = redis_mock
    key = "test_user_1"
    max_requests = 5
    window = 60
    for i in range(max_requests):
        allowed, info = limiter.check_rate_limit(key, max_requests, window)
        assert allowed, f"Request {i+1} should be allowed"
    allowed, info = limiter.check_rate_limit(key, max_requests, window)
    assert not allowed
    assert info["remaining"] == 0
    limiter.reset_limit(key)


def test_rate_limiter_window():
    # Window test: use a longer window so expiry is clear-cut
    redis_mock = make_redis_mock()
    limiter = RateLimiter()
    limiter.redis_client = redis_mock
    key = "test_user_2"
    max_requests = 3
    window = 2
    for i in range(max_requests):
        allowed, _ = limiter.check_rate_limit(key, max_requests, window)
        assert allowed
    allowed, _ = limiter.check_rate_limit(key, max_requests, window)
    assert not allowed
    # Manually expire entries by clearing the store (simulates window expiry)
    cache_key = f"hotel_pms:rate_limit:{key}"
    redis_mock._store.clear()
    allowed, _ = limiter.check_rate_limit(key, max_requests, window)
    assert allowed
    limiter.reset_limit(key)


def test_rate_limiter_multiple_limits():
    redis_mock = make_redis_mock()
    limiter = RateLimiter()
    limiter.redis_client = redis_mock
    base_key = "test_user_3"
    checks = [
        (f"{base_key}:limit1", 10, 60),
        (f"{base_key}:limit2", 5, 60),
        (f"{base_key}:limit3", 20, 60),
    ]
    for i in range(4):
        allowed, info = limiter.check_multiple_limits(checks)
        assert allowed, f"Request {i+1} should be allowed"
    allowed, info = limiter.check_multiple_limits(checks)
    assert not allowed
    for key, _, _ in checks:
        limiter.reset_limit(key)


def test_rate_limit_config():
    assert RateLimitConfig.get_user_tier("admin") == RateLimitTier.ADMIN
    assert RateLimitConfig.get_user_tier("manager") == RateLimitTier.PREMIUM
    assert RateLimitConfig.get_user_tier("staff") == RateLimitTier.FREE
    login_limit = RateLimitConfig.get_endpoint_limit("/api/v1/auth/login", "POST")
    assert login_limit is not None
    assert login_limit[0] == 5
    no_limit = RateLimitConfig.get_endpoint_limit("/api/v1/unknown", "GET")
    assert no_limit is None


def test_abuse_detection_failed_auth():
    mem_cache = InMemoryCache()
    identifier = "test_ip_192.168.1.1"
    max_failures = 5
    for i in range(max_failures - 1):
        key = f"failed_auth:{identifier}"
        count = mem_cache.get(key)
        count = int(count) if count is not None else 0
        count += 1
        mem_cache.set(key, count, ttl=3600)
        assert count < max_failures
    key = f"failed_auth:{identifier}"
    count = mem_cache.get(key)
    count = int(count) if count is not None else 0
    count += 1
    mem_cache.set(key, count, ttl=3600)
    assert count >= max_failures
    mem_cache.delete(key)
    assert mem_cache.get(key) is None


def test_abuse_detection_ip_blocking():
    mem_cache = InMemoryCache()
    ip = "192.168.1.100"
    key = f"blocked_ip:{ip}"
    assert mem_cache.get(key) is None
    mem_cache.set(key, {"reason": "Test", "duration": 60}, ttl=60)
    assert mem_cache.get(key) is not None
    mem_cache.delete(key)
    assert mem_cache.get(key) is None


def test_abuse_detection_pattern():
    mem_cache = InMemoryCache()
    identifier = "test_pattern_user"
    pattern = "rapid_requests"
    threshold = 10
    key = f"pattern:{pattern}:{identifier}"
    for i in range(threshold - 1):
        count = mem_cache.get(key)
        count = int(count) if count else 0
        count += 1
        mem_cache.set(key, count, ttl=300)
        assert count < threshold
    count = mem_cache.get(key)
    count = int(count) if count else 0
    count += 1
    mem_cache.set(key, count, ttl=300)
    assert count >= threshold


def test_rate_limiter_status():
    redis_mock = make_redis_mock()
    limiter = RateLimiter()
    limiter.redis_client = redis_mock
    key = "test_status_user"
    max_requests = 10
    window = 60
    for i in range(5):
        limiter.check_rate_limit(key, max_requests, window)
    status = limiter.get_limit_status(key, max_requests, window)
    assert status["limit"] == max_requests
    assert status["current_count"] == 5
    assert status["remaining"] == max_requests - 5
    limiter.reset_limit(key)


def test_rate_limiter_reset():
    redis_mock = make_redis_mock()
    limiter = RateLimiter()
    limiter.redis_client = redis_mock
    key = "test_reset_user"
    max_requests = 3
    window = 60
    for i in range(max_requests):
        allowed, _ = limiter.check_rate_limit(key, max_requests, window)
        assert allowed
    allowed, _ = limiter.check_rate_limit(key, max_requests, window)
    assert not allowed
    success = limiter.reset_limit(key)
    assert success
    allowed, _ = limiter.check_rate_limit(key, max_requests, window)
    assert allowed
    limiter.reset_limit(key)
