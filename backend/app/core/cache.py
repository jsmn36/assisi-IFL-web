"""
Core Cache Module — Redis-backed with in-memory fallback.
"""
import json, time, logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InMemoryCache:
    def __init__(self):
        self._store: dict = {}
        self._hits = self._misses = 0

    def _make_key(self, key, namespace=None):
        return f"{namespace}:{key}" if namespace else key

    def get(self, key, namespace=None):
        actual_key = self._make_key(key, namespace)
        entry = self._store.get(actual_key)
        if entry is None:
            self._misses += 1
            return None
        value, expiry = entry
        if expiry and time.time() > expiry:
            del self._store[actual_key]
            self._misses += 1
            return None
        self._hits += 1
        return value

    def set(self, key, value, ttl=300, namespace=None):
        actual_key = self._make_key(key, namespace)
        self._store[actual_key] = (value, time.time() + ttl if ttl else 0)
        return True

    def delete(self, key, namespace=None):
        actual_key = self._make_key(key, namespace)
        return self._store.pop(actual_key, None) is not None

    def exists(self, key, namespace=None):
        actual_key = self._make_key(key, namespace)
        entry = self._store.get(actual_key)
        if entry is None:
            return False
        value, expiry = entry
        if expiry and time.time() > expiry:
            del self._store[actual_key]
            return False
        return True

    def clear_namespace(self, namespace):
        prefix = f"{namespace}:"
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def delete_pattern(self, pattern, namespace=None):
        actual_pattern = f"{namespace}:{pattern}" if namespace else pattern
        prefix = actual_pattern.rstrip("*")
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def get_stats(self):
        total = self._hits + self._misses
        return {
            "backend": "in-memory",
            "total_keys": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total else 0.0,
        }


class RedisCache:
    def __init__(self, client):
        self._r = client
        self._hits = self._misses = 0

    def get(self, key):
        raw = self._r.get(key)
        if raw is None:
            self._misses += 1
            return None
        self._hits += 1
        return json.loads(raw)

    def set(self, key, value, ttl=300):
        return bool(self._r.setex(key, ttl, json.dumps(value)))

    def delete(self, key):
        return bool(self._r.delete(key))

    def delete_pattern(self, pattern):
        keys = self._r.keys(pattern)
        return self._r.delete(*keys) if keys else 0

    def get_stats(self):
        total = self._hits + self._misses
        return {
            "backend": "redis",
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total else 0.0,
        }


def _build_cache():
    try:
        from app.config import settings

        if not settings.is_postgresql_mode:
            raise Exception("PostgreSQL mode disabled")
        import redis

        client = redis.Redis(
            host=settings.REDIS_URL or "localhost",
            port=6379,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            socket_connect_timeout=2,
            decode_responses=True,
        )
        client.ping()
        logger.info("Cache: Redis connected")
        return RedisCache(client)
    except Exception as e:
        logger.warning("Cache: Redis unavailable (%s); using in-memory", e)
        return InMemoryCache()


cache = _build_cache()
