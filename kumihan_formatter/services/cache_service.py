"""Cache service implementation

This module provides a unified caching interface that can
work with different cache backends and strategies.
"""

from typing import Any, Dict, Optional, List, Callable
from pathlib import Path

from ..core.interfaces import CacheService
from ..core.common import SmartCache, get_cache, LRUStrategy, LFUStrategy


class CacheServiceImpl(CacheService):
    """Centralized cache service implementation
    
    Provides a unified interface to multiple cache instances
    with different policies and use cases.
    """
    
    def __init__(self, default_cache_name: str = "default"):
        """Initialize cache service
        
        Args:
            default_cache_name: Name of default cache instance
        """
        self.default_cache_name = default_cache_name
        self._cache_instances: Dict[str, SmartCache] = {}
        self._default_ttl = 3600  # 1 hour
        
        # Create default cache instance
        self._get_or_create_cache(default_cache_name)
    
    def _get_or_create_cache(self, cache_name: str) -> SmartCache:
        """Get or create a cache instance
        
        Args:
            cache_name: Name of cache instance
            
        Returns:
            SmartCache: Cache instance
        """
        if cache_name not in self._cache_instances:
            self._cache_instances[cache_name] = get_cache(cache_name)
        return self._cache_instances[cache_name]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get cached value from default cache
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        return self.get_from_cache(self.default_cache_name, key, default)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value in default cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        self.set_in_cache(self.default_cache_name, key, value, ttl)
    
    def remove(self, key: str) -> bool:
        """Remove cached value from default cache
        
        Args:
            key: Cache key to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        return self.remove_from_cache(self.default_cache_name, key)
    
    def clear(self) -> None:
        """Clear default cache"""
        self.clear_cache(self.default_cache_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for default cache
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        return self.get_cache_stats(self.default_cache_name)
    
    # Extended interface for multiple cache instances
    
    def get_from_cache(self, cache_name: str, key: str, default: Any = None) -> Any:
        """Get cached value from specific cache
        
        Args:
            cache_name: Name of cache instance
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        cache = self._get_or_create_cache(cache_name)
        return cache.get(key, default)
    
    def set_in_cache(self, cache_name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value in specific cache
        
        Args:
            cache_name: Name of cache instance
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        cache = self._get_or_create_cache(cache_name)
        cache.set(key, value, ttl or self._default_ttl)
    
    def remove_from_cache(self, cache_name: str, key: str) -> bool:
        """Remove cached value from specific cache
        
        Args:
            cache_name: Name of cache instance
            key: Cache key to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if cache_name not in self._cache_instances:
            return False
        
        cache = self._cache_instances[cache_name]
        return cache.remove(key)
    
    def clear_cache(self, cache_name: str) -> None:
        """Clear specific cache
        
        Args:
            cache_name: Name of cache instance to clear
        """
        if cache_name in self._cache_instances:
            self._cache_instances[cache_name].clear()
    
    def create_cache(
        self,
        name: str,
        max_entries: int = 1000,
        max_memory_mb: float = 100.0,
        default_ttl: int = 3600,
        strategy: str = "lru",
        enable_file_cache: bool = True
    ) -> bool:
        """Create a new cache instance with specific configuration
        
        Args:
            name: Cache name
            max_entries: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default time-to-live in seconds
            strategy: Cache eviction strategy ('lru' or 'lfu')
            enable_file_cache: Whether to enable file caching
            
        Returns:
            bool: True if created successfully
        """
        if name in self._cache_instances:
            return False  # Cache already exists
        
        # Select strategy
        if strategy.lower() == "lfu":
            cache_strategy = LFUStrategy()
        else:
            cache_strategy = LRUStrategy()
        
        # Create cache with custom configuration
        cache = SmartCache(
            name=name,
            max_memory_entries=max_entries,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl,
            strategy=cache_strategy,
            enable_file_cache=enable_file_cache
        )
        
        self._cache_instances[name] = cache
        return True
    
    def delete_cache(self, cache_name: str) -> bool:
        """Delete a cache instance
        
        Args:
            cache_name: Name of cache to delete
            
        Returns:
            bool: True if deleted successfully
        """
        if cache_name == self.default_cache_name:
            return False  # Cannot delete default cache
        
        if cache_name in self._cache_instances:
            self._cache_instances[cache_name].clear()
            del self._cache_instances[cache_name]
            return True
        
        return False
    
    def list_caches(self) -> List[str]:
        """List all cache instance names
        
        Returns:
            List[str]: Cache names
        """
        return list(self._cache_instances.keys())
    
    def get_cache_stats(self, cache_name: str) -> Dict[str, Any]:
        """Get statistics for specific cache
        
        Args:
            cache_name: Name of cache instance
            
        Returns:
            Dict[str, Any]: Cache statistics
        """
        if cache_name not in self._cache_instances:
            return {}
        
        return self._cache_instances[cache_name].get_stats()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all cache instances
        
        Returns:
            Dict[str, Dict[str, Any]]: Statistics by cache name
        """
        return {
            name: cache.get_stats()
            for name, cache in self._cache_instances.items()
        }
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Cleanup expired entries from all caches
        
        Returns:
            Dict[str, int]: Number of expired entries removed by cache
        """
        results = {}
        for name, cache in self._cache_instances.items():
            results[name] = cache.cleanup_expired()
        return results
    
    def cache_function(
        self,
        cache_name: Optional[str] = None,
        ttl: Optional[int] = None,
        key_func: Optional[Callable] = None
    ):
        """Decorator for caching function results
        
        Args:
            cache_name: Name of cache to use (default if None)
            ttl: Time-to-live for cached results
            key_func: Function to generate cache key
        """
        target_cache_name = cache_name or self.default_cache_name
        cache = self._get_or_create_cache(target_cache_name)
        
        return cache.cache_function(ttl=ttl, key_func=key_func)
    
    def invalidate_pattern(self, pattern: str, cache_name: Optional[str] = None) -> int:
        """Invalidate cache entries matching a pattern
        
        Args:
            pattern: Pattern to match (simple wildcard support)
            cache_name: Cache to invalidate (all caches if None)
            
        Returns:
            int: Number of entries invalidated
        """
        import fnmatch
        
        total_invalidated = 0
        
        if cache_name:
            caches_to_check = [cache_name] if cache_name in self._cache_instances else []
        else:
            caches_to_check = list(self._cache_instances.keys())
        
        for name in caches_to_check:
            cache = self._cache_instances[name]
            
            # Get all keys (this is a limitation of current SmartCache implementation)
            # In a real implementation, we'd want to iterate through keys efficiently
            stats = cache.get_stats()
            # For now, we'll clear the entire cache if pattern is '*'
            if pattern == '*':
                cache.clear()
                total_invalidated += stats.get('memory_entries', 0)
        
        return total_invalidated
    
    def warm_cache(self, cache_name: str, data: Dict[str, Any]) -> int:
        """Warm up cache with initial data
        
        Args:
            cache_name: Name of cache to warm
            data: Dictionary of key-value pairs to cache
            
        Returns:
            int: Number of entries added
        """
        cache = self._get_or_create_cache(cache_name)
        
        count = 0
        for key, value in data.items():
            cache.set(key, value)
            count += 1
        
        return count
    
    def set_default_ttl(self, ttl: int) -> None:
        """Set default TTL for new cache entries
        
        Args:
            ttl: Time-to-live in seconds
        """
        self._default_ttl = ttl
    
    def get_cache_instance(self, cache_name: str) -> Optional[SmartCache]:
        """Get direct access to cache instance
        
        Args:
            cache_name: Name of cache instance
            
        Returns:
            Optional[SmartCache]: Cache instance or None if not found
        """
        return self._cache_instances.get(cache_name)