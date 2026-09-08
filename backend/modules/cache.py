"""
Cache Management

Redis-based and in-memory caching for improved performance.
"""
from typing import Optional, Any, Dict
import json
from datetime import datetime, timedelta
from config import settings
import redis


class CacheManager:
    """Manage caching layer"""

    def __init__(self, backend: str = None):
        """Initialize cache manager"""
        self.backend = backend or settings.CACHE_BACKEND
        
        if self.backend == "redis":
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}. Falling back to memory cache.")
                self.backend = "memory"
                self.cache = {}
        else:
            self.cache = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if self.backend == "redis":
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                print(f"Cache get error: {e}")
        else:
            return self.cache.get(key)
        
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful
        """
        ttl = ttl or settings.CACHE_TTL
        
        try:
            if self.backend == "redis":
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
            else:
                # Store with expiration time
                self.cache[key] = {
                    'value': value,
                    'expires_at': datetime.now() + timedelta(seconds=ttl)
                }
                
                # Clean up expired entries
                self._cleanup_memory_cache()
            
            return True
        
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.backend == "redis":
                self.redis_client.delete(key)
            else:
                self.cache.pop(key, None)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache"""
        try:
            if self.backend == "redis":
                self.redis_client.flushdb()
            else:
                self.cache.clear()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        now = datetime.now()
        expired_keys = [
            k for k, v in self.cache.items()
            if v['expires_at'] < now
        ]
        for k in expired_keys:
            del self.cache[k]

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        if self.backend == "redis":
            try:
                info = self.redis_client.info()
                return {
                    'backend': 'redis',
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0)
                }
            except Exception as e:
                return {'error': str(e)}
        else:
            return {
                'backend': 'memory',
                'cache_size': len(self.cache),
                'max_size': settings.CACHE_MAX_SIZE
            }


class QueryCache:
    """Cache for Q&A queries and answers"""

    def __init__(self, cache_manager: CacheManager = None):
        """Initialize query cache"""
        self.manager = cache_manager or CacheManager()

    def get_answer(self, query: str) -> Optional[Dict]:
        """
        Get cached answer for query
        
        Args:
            query: User question
            
        Returns:
            Cached answer dict or None
        """
        key = self._make_key(query)
        return self.manager.get(key)

    def set_answer(self, query: str, answer: Dict, ttl: int = None):
        """
        Cache answer for query
        
        Args:
            query: User question
            answer: Answer dict
            ttl: Time to live
        """
        key = self._make_key(query)
        self.manager.set(key, answer, ttl)

    def _make_key(self, query: str) -> str:
        """Generate cache key from query"""
        # Normalize query: lowercase, strip whitespace
        normalized = query.lower().strip()
        return f"qa:{normalized}"

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return self.manager.get_stats()


class EmbeddingCache:
    """Cache for document embeddings"""

    def __init__(self, cache_manager: CacheManager = None):
        """Initialize embedding cache"""
        self.manager = cache_manager or CacheManager()

    def get_embedding(self, text: str) -> Optional[list]:
        """Get cached embedding"""
        key = f"emb:{hash(text)}"
        return self.manager.get(key)

    def set_embedding(self, text: str, embedding: list, ttl: int = None):
        """Cache embedding"""
        key = f"emb:{hash(text)}"
        self.manager.set(key, embedding, ttl or settings.CACHE_TTL * 7)  # Longer TTL

    def clear(self):
        """Clear embedding cache"""
        self.manager.clear()
