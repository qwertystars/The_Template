"""
Comprehensive tests for app/core/cache.py
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from redis.asyncio import Redis

from app.core.cache import CacheManager, get_redis, init_redis, close_redis


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock(spec=Redis)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock(return_value=0)
    redis.incr = AsyncMock(return_value=1)
    redis.decr = AsyncMock(return_value=0)
    redis.expire = AsyncMock()
    redis.ttl = AsyncMock(return_value=-1)
    redis.lpush = AsyncMock(return_value=1)
    redis.rpush = AsyncMock(return_value=1)
    redis.lrange = AsyncMock(return_value=[])
    redis.llen = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def cache_manager(mock_redis):
    """Create a CacheManager instance with mock Redis."""
    return CacheManager(mock_redis)


class TestCacheManager:
    """Tests for CacheManager class."""

    @pytest.mark.asyncio
    async def test_get_existing_value(self, cache_manager, mock_redis):
        """Test getting existing value from cache."""
        mock_redis.get.return_value = "test_value"
        
        result = await cache_manager.get("test_key")
        
        assert result == "test_value"
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_non_existing_value(self, cache_manager, mock_redis):
        """Test getting non-existing value returns None."""
        mock_redis.get.return_value = None
        
        result = await cache_manager.get("missing_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("missing_key")

    @pytest.mark.asyncio
    async def test_set_without_expiration(self, cache_manager, mock_redis):
        """Test setting value without expiration."""
        await cache_manager.set("key1", "value1")
        
        mock_redis.set.assert_called_once_with("key1", "value1")
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_with_expiration(self, cache_manager, mock_redis):
        """Test setting value with expiration."""
        await cache_manager.set("key2", "value2", expire=3600)
        
        mock_redis.setex.assert_called_once_with("key2", 3600, "value2")
        mock_redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete(self, cache_manager, mock_redis):
        """Test deleting key from cache."""
        await cache_manager.delete("delete_key")
        
        mock_redis.delete.assert_called_once_with("delete_key")

    @pytest.mark.asyncio
    async def test_exists_true(self, cache_manager, mock_redis):
        """Test checking if key exists (returns True)."""
        mock_redis.exists.return_value = 1
        
        result = await cache_manager.exists("existing_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("existing_key")

    @pytest.mark.asyncio
    async def test_exists_false(self, cache_manager, mock_redis):
        """Test checking if key exists (returns False)."""
        mock_redis.exists.return_value = 0
        
        result = await cache_manager.exists("missing_key")
        
        assert result is False
        mock_redis.exists.assert_called_once_with("missing_key")

    @pytest.mark.asyncio
    async def test_get_json_valid(self, cache_manager, mock_redis):
        """Test getting JSON value from cache."""
        json_data = {"name": "test", "count": 42}
        mock_redis.get.return_value = json.dumps(json_data)
        
        result = await cache_manager.get_json("json_key")
        
        assert result == json_data
        mock_redis.get.assert_called_once_with("json_key")

    @pytest.mark.asyncio
    async def test_get_json_none(self, cache_manager, mock_redis):
        """Test getting JSON when key doesn't exist."""
        mock_redis.get.return_value = None
        
        result = await cache_manager.get_json("missing_json")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_json_without_expiration(self, cache_manager, mock_redis):
        """Test setting JSON value without expiration."""
        data = {"key": "value", "num": 123}
        
        await cache_manager.set_json("json_key", data)
        
        expected_json = json.dumps(data)
        mock_redis.set.assert_called_once_with("json_key", expected_json)

    @pytest.mark.asyncio
    async def test_set_json_with_expiration(self, cache_manager, mock_redis):
        """Test setting JSON value with expiration."""
        data = {"test": True}
        
        await cache_manager.set_json("json_key", data, expire=1800)
        
        expected_json = json.dumps(data)
        mock_redis.setex.assert_called_once_with("json_key", 1800, expected_json)

    @pytest.mark.asyncio
    async def test_increment(self, cache_manager, mock_redis):
        """Test incrementing counter."""
        mock_redis.incr.return_value = 5
        
        result = await cache_manager.increment("counter")
        
        assert result == 5
        mock_redis.incr.assert_called_once_with("counter")

    @pytest.mark.asyncio
    async def test_decrement(self, cache_manager, mock_redis):
        """Test decrementing counter."""
        mock_redis.decr.return_value = 3
        
        result = await cache_manager.decrement("counter")
        
        assert result == 3
        mock_redis.decr.assert_called_once_with("counter")

    @pytest.mark.asyncio
    async def test_expire(self, cache_manager, mock_redis):
        """Test setting expiration on key."""
        await cache_manager.expire("expire_key", 300)
        
        mock_redis.expire.assert_called_once_with("expire_key", 300)

    @pytest.mark.asyncio
    async def test_ttl(self, cache_manager, mock_redis):
        """Test getting TTL for key."""
        mock_redis.ttl.return_value = 120
        
        result = await cache_manager.ttl("ttl_key")
        
        assert result == 120
        mock_redis.ttl.assert_called_once_with("ttl_key")


class TestCacheManagerEdgeCases:
    """Tests for edge cases in CacheManager."""

    @pytest.mark.asyncio
    async def test_set_empty_string(self, cache_manager, mock_redis):
        """Test setting empty string value."""
        await cache_manager.set("key", "")
        
        mock_redis.set.assert_called_once_with("key", "")

    @pytest.mark.asyncio
    async def test_set_zero_expiration(self, cache_manager, mock_redis):
        """Test setting value with zero expiration."""
        await cache_manager.set("key", "value", expire=0)
        
        # Zero is falsy, should use set instead of setex
        mock_redis.set.assert_called_once_with("key", "value")

    @pytest.mark.asyncio
    async def test_get_json_invalid_json(self, cache_manager, mock_redis):
        """Test getting invalid JSON raises error."""
        mock_redis.get.return_value = "invalid json"
        
        with pytest.raises(json.JSONDecodeError):
            await cache_manager.get_json("invalid_key")

    @pytest.mark.asyncio
    async def test_set_json_complex_data(self, cache_manager, mock_redis):
        """Test setting complex JSON data."""
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "metadata": {
                "total": 2,
                "page": 1
            }
        }
        
        await cache_manager.set_json("complex", data)
        
        expected_json = json.dumps(data)
        mock_redis.set.assert_called_once_with("complex", expected_json)


class TestRedisLifecycle:
    """Tests for Redis initialization and cleanup."""

    @pytest.mark.asyncio
    async def test_get_redis_not_initialized(self):
        """Test getting Redis when not initialized raises error."""
        # Clear the global redis_client
        import app.core.cache as cache_module
        original_client = cache_module.redis_client
        cache_module.redis_client = None
        
        try:
            with pytest.raises(RuntimeError, match="Redis not initialized"):
                await get_redis()
        finally:
            cache_module.redis_client = original_client

    @pytest.mark.asyncio
    @patch('app.core.cache.aioredis.from_url')
    async def test_init_redis(self, mock_from_url):
        """Test Redis initialization."""
        mock_client = AsyncMock(spec=Redis)
        mock_from_url.return_value = mock_client
        
        await init_redis()
        
        mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_redis_when_initialized(self):
        """Test closing Redis when initialized."""
        import app.core.cache as cache_module
        mock_client = AsyncMock(spec=Redis)
        original_client = cache_module.redis_client
        cache_module.redis_client = mock_client
        
        try:
            await close_redis()
            mock_client.close.assert_called_once()
        finally:
            cache_module.redis_client = original_client

    @pytest.mark.asyncio
    async def test_close_redis_when_not_initialized(self):
        """Test closing Redis when not initialized (should not raise)."""
        import app.core.cache as cache_module
        original_client = cache_module.redis_client
        cache_module.redis_client = None
        
        try:
            # Should not raise
            await close_redis()
        finally:
            cache_module.redis_client = original_client