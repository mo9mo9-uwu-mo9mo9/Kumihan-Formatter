"""Caching utilities

This module provides simple in-memory caching with TTL support
for performance optimization.
"""

import time
from typing import Any, Optional


class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache = {}
        self._timestamps = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            return None
        
        # Check if expired
        if self._is_expired(key):
            self.remove(key)
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        self._cache[key] = value
        self._timestamps[key] = {
            'created': time.time(),
            'ttl': ttl or self._default_ttl
        }
    
    def remove(self, key: str) -> None:
        """Remove value from cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._timestamps.clear()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._timestamps:
            return True
        
        timestamp_info = self._timestamps[key]
        elapsed = time.time() - timestamp_info['created']
        return elapsed > timestamp_info['ttl']
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        expired_keys = [key for key in self._cache.keys() if self._is_expired(key)]
        
        for key in expired_keys:
            self.remove(key)
        
        return len(expired_keys)