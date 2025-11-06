"""
Redis cache configuration and helpers.
Provides caching, rate limiting, and session storage.
"""
import json
from typing import Any, Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis
from app.core.config import settings


# Global Redis client
redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get Redis client instance.

    Returns:
        Redis client

    Raises:
        RuntimeError: If Redis is not initialized
    """
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global redis_client

    redis_client = await aioredis.from_url(
        str(settings.REDIS_URL),
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )


async def close_redis() -> None:
    """Close Redis connection."""
    if redis_client:
        await redis_client.close()


class CacheManager:
    """Helper class for cache operations."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.redis.get(key)

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
        """
        if expire:
            await self.redis.setex(key, expire, value)
        else:
            await self.redis.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return bool(await self.redis.exists(key))

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> None:
        """Set JSON value in cache."""
        await self.set(key, json.dumps(value), expire)

    async def increment(self, key: str) -> int:
        """Increment counter."""
        return await self.redis.incr(key)

    async def decrement(self, key: str) -> int:
        """Decrement counter."""
        return await self.redis.decr(key)

    async def expire(self, key: str, seconds: int) -> None:
        """Set expiration on key."""
        await self.redis.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        return await self.redis.ttl(key)

    # List operations
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to left of list."""
        return await self.redis.lpush(key, *values)

    async def rpush(self, key: str, *values: str) -> int:
        """Push values to right of list."""
        return await self.redis.rpush(key, *values)

    async def lpop(self, key: str) -> Optional[str]:
        """Pop value from left of list."""
        return await self.redis.lpop(key)

    async def rpop(self, key: str) -> Optional[str]:
        """Pop value from right of list."""
        return await self.redis.rpop(key)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        """Get range of values from list."""
        return await self.redis.lrange(key, start, end)

    # Set operations
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set."""
        return await self.redis.sadd(key, *members)

    async def srem(self, key: str, *members: str) -> int:
        """Remove members from set."""
        return await self.redis.srem(key, *members)

    async def smembers(self, key: str) -> set[str]:
        """Get all members of set."""
        return await self.redis.smembers(key)

    async def sismember(self, key: str, member: str) -> bool:
        """Check if member is in set."""
        return await self.redis.sismember(key, member)

    # Hash operations
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field."""
        return await self.redis.hset(name, key, value)

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field."""
        return await self.redis.hget(name, key)

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields."""
        return await self.redis.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        return await self.redis.hdel(name, *keys)

    # Pattern matching
    async def keys(self, pattern: str) -> list[str]:
        """Get keys matching pattern."""
        return await self.redis.keys(pattern)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        keys = await self.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0


# Decorator for caching function results
def cache_result(expire: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache function results.

    Args:
        expire: Cache expiration in seconds
        key_prefix: Prefix for cache keys

    Example:
        @cache_result(expire=600, key_prefix="user")
        async def get_user(user_id: int):
            # Expensive operation
            return user
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            redis = await get_redis()
            cache_manager = CacheManager(redis)
            cached = await cache_manager.get_json(cache_key)

            if cached is not None:
                return cached

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set_json(cache_key, result, expire)

            return result

        return wrapper
    return decorator
