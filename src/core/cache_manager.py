"""
Cache manager for market data with TTL and size limits.
"""

import time
from typing import Dict, Any, Optional, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL."""
    
    def __init__(self, value: Any, ttl: float):
        """
        Initialize cache entry.
        
        Args:
            value: Cached value
            ttl: Time-to-live in seconds
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_access = self.created_at
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return (time.time() - self.created_at) > self.ttl
    
    def access(self) -> Any:
        """Access cached value and update statistics."""
        self.access_count += 1
        self.last_access = time.time()
        return self.value


class CacheManager:
    """In-memory cache with TTL and LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 60.0):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = asyncio.Lock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.info(f"CacheManager initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired():
                    del self.cache[key]
                    self.misses += 1
                    return None
                
                self.hits += 1
                return entry.access()
            
            self.misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        async with self.lock:
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict_lru()
            
            entry_ttl = ttl if ttl is not None else self.default_ttl
            self.cache[key] = CacheEntry(value, entry_ttl)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self):
        """Clear all cache entries."""
        async with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_access)
        del self.cache[lru_key]
        self.evictions += 1
        logger.debug(f"Evicted LRU entry: {lru_key}")
    
    async def cleanup_expired(self):
        """Remove all expired entries."""
        async with self.lock:
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
