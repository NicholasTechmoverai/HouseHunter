import time
import logging
import fnmatch
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("app.cache")

class InMemoryCache:
    """A thread-safe-ish simple in-memory cache with TTL support."""
    def __init__(self):
        self._store: Dict[str, Tuple[Any, float]] = {}

    async def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        value, expiry = self._store[key]
        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        expiry = time.time() + expire if expire is not None else None
        self._store[key] = (value, expiry)
        return True

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def delete_pattern(self, pattern: str) -> int:
        # Translate redis-like glob pattern (e.g. "prefix:*") to fnmatch/python glob
        matched_keys = [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
        count = 0
        for k in matched_keys:
            if await self.delete(k):
                count += 1
        return count

class RedisCache:
    """Wrapper around redis client if installed and configured."""
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
        self._initialized = False

    def _init_client(self):
        if self._initialized:
            return
        try:
            import redis.asyncio as aioredis
            self.client = aioredis.from_url(self.redis_url, decode_responses=True)
            self._initialized = True
            logger.info("Redis cache client initialized successfully")
        except ImportError:
            logger.warning("redis-py is not installed. Falling back to InMemoryCache.")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")

    async def get(self, key: str) -> Optional[Any]:
        self._init_client()
        if not self.client:
            return None
        try:
            import json
            val = await self.client.get(key)
            if val is not None:
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return val
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        self._init_client()
        if not self.client:
            return False
        try:
            import json
            serialized = json.dumps(value)
            if expire:
                await self.client.setex(key, expire, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        self._init_client()
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        self._init_client()
        if not self.client:
            return 0
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete_pattern error: {e}")
            return 0

class CacheManager:
    """Manages application caching, resolving to Redis if configured, otherwise falling back to InMemory."""
    def __init__(self):
        self._in_memory = InMemoryCache()
        self._redis = None
        
        # Try to read settings dynamically to avoid circular imports during startup
        try:
            from core.settings import settings
            if settings.REDIS_URL:
                self._redis = RedisCache(settings.REDIS_URL)
        except Exception:
            pass

    @property
    def _active_cache(self):
        if self._redis:
            # Check if redis-py is available by checking if import succeeds
            try:
                import redis
                return self._redis
            except ImportError:
                pass
        return self._in_memory

    async def get(self, key: str) -> Optional[Any]:
        return await self._active_cache.get(key)

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        return await self._active_cache.set(key, value, expire)

    async def delete(self, key: str) -> bool:
        return await self._active_cache.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        return await self._active_cache.delete_pattern(pattern)

cache_manager = CacheManager()
