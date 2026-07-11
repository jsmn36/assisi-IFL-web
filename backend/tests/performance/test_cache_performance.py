import pytest
import time
from app.core.cache import cache
from app.services.cached_dashboard_service import CachedDashboardService


def test_cache_set_get_performance():
    """Test basic cache operations performance"""

    # Test set performance
    start = time.time()
    for i in range(1000):
        cache.set(f"test_key_{i}", f"value_{i}", namespace="perf_test", ttl=60)
    set_time = time.time() - start

    if set_time > 0:
        print(f"Set 1000 keys in {set_time:.3f}s ({1000/set_time:.0f} ops/sec)")
    else:
        print(f"Set 1000 keys in {set_time:.3f}s (∞ ops/sec)")
    assert set_time < 5.0  # Should complete in under 5 seconds

    # Test get performance
    start = time.time()
    for i in range(1000):
        cache.get(f"test_key_{i}", namespace="perf_test")
    get_time = time.time() - start

    if get_time > 0:
        print(f"Get 1000 keys in {get_time:.3f}s ({1000/get_time:.0f} ops/sec)")
    else:
        print(f"Get 1000 keys in {get_time:.3f}s (∞ ops/sec)")
    assert get_time < 5.0  # Gets should be faster than sets

    # Cleanup
    cache.clear_namespace("perf_test")


def test_cached_decorator_performance(test_db):
    """Test cached decorator performance"""

    service = CachedDashboardService(test_db)

    # First call - cache miss (slower)
    start = time.time()
    stats1 = service.get_dashboard_stats()
    first_call_time = time.time() - start

    # Second call - cache hit (faster)
    start = time.time()
    stats2 = service.get_dashboard_stats()
    second_call_time = time.time() - start

    print(f"First call (cache miss): {first_call_time:.3f}s")
    print(f"Second call (cache hit): {second_call_time:.3f}s")
    if second_call_time > 0:
        print(f"Speedup: {first_call_time/second_call_time:.1f}x")
    else:
        print(f"Speedup: ∞x (cache hit time rounds to 0)")

    # Cache hit should be significantly faster
    assert second_call_time < first_call_time / 10
    assert stats1 == stats2


def test_cache_memory_usage():
    """Test cache memory usage"""

    # Store large objects
    large_data = {"data": "x" * 10000}  # 10KB string

    for i in range(100):
        cache.set(f"large_key_{i}", large_data, namespace="memory_test", ttl=60)

    # Get cache stats
    stats = cache.get_stats()
    print(f"Cache memory: {stats.get('used_memory', 'N/A')}")

    # Cleanup
    cache.clear_namespace("memory_test")


def test_cache_hit_rate():
    """Test cache hit rate"""

    namespace = "hit_rate_test"

    # Set some values
    for i in range(10):
        cache.set(f"key_{i}", f"value_{i}", namespace=namespace, ttl=60)

    # Mix of hits and misses
    for i in range(20):
        cache.get(f"key_{i % 15}", namespace=namespace)  # Some misses

    stats = cache.get_stats()
    hit_rate = stats.get("hit_rate", 0)

    print(f"Cache hit rate: {hit_rate}%")

    # Cleanup
    cache.clear_namespace(namespace)


def test_cache_expiration():
    """Test cache TTL expiration"""

    key = "expiring_key"

    # Set with 1 second TTL
    cache.set(key, "value", namespace="expire_test", ttl=1)

    # Should exist immediately
    assert cache.exists(key, namespace="expire_test")

    # Wait for expiration
    time.sleep(1.5)

    # Should be expired
    assert not cache.exists(key, namespace="expire_test")


def test_cache_pattern_deletion():
    """Test pattern-based deletion performance"""

    # Create many keys with pattern
    for i in range(100):
        cache.set(
            f"pattern_test:user:{i}", f"data_{i}", namespace="pattern_test", ttl=60
        )

    # Delete by pattern
    start = time.time()
    deleted = cache.delete_pattern("pattern_test:user:*", namespace="pattern_test")
    delete_time = time.time() - start

    print(f"Deleted {deleted} keys in {delete_time:.3f}s")

    assert deleted == 100
    assert delete_time < 1.0
