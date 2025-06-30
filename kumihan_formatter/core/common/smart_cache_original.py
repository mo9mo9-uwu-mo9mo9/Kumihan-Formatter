"""Intelligent caching system for Kumihan-Formatter

This module provides smart caching capabilities including:
- File-based caching with hash validation
- Memory caching with TTL support
- Performance-optimized cache strategies
- Automatic cache invalidation
"""

import hashlib
import json
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

from .error_framework import ErrorCategory, ErrorSeverity, KumihanError

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata"""

    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: Optional[int] = None

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl_seconds is None:
            return False

        age = datetime.now() - self.created_at
        return age.total_seconds() > self.ttl_seconds

    def update_access(self) -> None:
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class CacheStrategy(ABC):
    """Abstract base class for cache strategies"""

    @abstractmethod
    def should_evict(self, entry: CacheEntry) -> bool:
        """Determine if entry should be evicted"""
        pass

    @abstractmethod
    def get_priority(self, entry: CacheEntry) -> float:
        """Get eviction priority (lower = evict first)"""
        pass


class LRUStrategy(CacheStrategy):
    """Least Recently Used cache strategy"""

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        return entry.last_accessed.timestamp()


class LFUStrategy(CacheStrategy):
    """Least Frequently Used cache strategy"""

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        return float(entry.access_count)


class SmartCache:
    """Intelligent caching system with multiple strategies

    Features:
    - Memory and file-based caching
    - Multiple eviction strategies
    - Automatic size management
    - Performance metrics
    - Hash-based cache validation
    """

    def __init__(
        self,
        name: str = "default",
        max_memory_entries: int = 1000,
        max_memory_mb: float = 100.0,
        default_ttl: int = 3600,  # 1 hour
        strategy: CacheStrategy = None,
        cache_dir: Optional[Path] = None,
        enable_file_cache: bool = True,
    ):
        """Initialize smart cache

        Args:
            name: Cache instance name
            max_memory_entries: Maximum number of memory entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default time-to-live in seconds
            strategy: Cache eviction strategy
            cache_dir: Directory for file cache
            enable_file_cache: Whether to enable file caching
        """
        self.name = name
        self.max_memory_entries = max_memory_entries
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.default_ttl = default_ttl
        self.strategy = strategy or LRUStrategy()
        self.enable_file_cache = enable_file_cache

        # Memory cache
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._memory_size = 0

        # File cache
        if enable_file_cache:
            self.cache_dir = cache_dir or Path.cwd() / ".kumihan_cache" / name
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "file_cache_hits": 0,
            "file_cache_misses": 0,
        }

    def _calculate_size(self, value: Any) -> int:
        """Estimate size of value in bytes"""
        try:
            if isinstance(value, str):
                return len(value.encode("utf-8"))
            elif isinstance(value, (bytes, bytearray)):
                return len(value)
            else:
                # Use pickle for other types
                return len(pickle.dumps(value))
        except Exception:
            # Fallback estimation
            return 1024  # 1KB default

    def _generate_cache_key(self, key: str) -> str:
        """Generate a safe cache key for file storage"""
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        if not self.cache_dir:
            raise KumihanError(
                "File cache not enabled", category=ErrorCategory.CONFIGURATION
            )

        safe_key = self._generate_cache_key(key)
        return self.cache_dir / f"{safe_key}.cache"

    def _save_to_file(self, key: str, entry: CacheEntry) -> bool:
        """Save cache entry to file"""
        if not self.enable_file_cache:
            return False

        try:
            file_path = self._get_file_path(key)

            cache_data = {
                "value": entry.value,
                "created_at": entry.created_at.isoformat(),
                "ttl_seconds": entry.ttl_seconds,
                "key": key,  # Store original key for verification
            }

            with open(file_path, "wb") as f:
                pickle.dump(cache_data, f)

            return True

        except Exception as e:
            # Log error but don't fail
            print(f"Warning: Failed to save cache entry to file: {e}")
            return False

    def _load_from_file(self, key: str) -> Optional[CacheEntry]:
        """Load cache entry from file"""
        if not self.enable_file_cache:
            return None

        try:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return None

            with open(file_path, "rb") as f:
                cache_data = pickle.load(f)

            # Verify key matches
            if cache_data.get("key") != key:
                return None

            # Reconstruct entry
            entry = CacheEntry(
                value=cache_data["value"],
                created_at=datetime.fromisoformat(cache_data["created_at"]),
                last_accessed=datetime.now(),
                ttl_seconds=cache_data.get("ttl_seconds"),
            )

            # Check if expired
            if entry.is_expired():
                file_path.unlink(missing_ok=True)
                return None

            return entry

        except Exception as e:
            # Remove corrupted file
            try:
                self._get_file_path(key).unlink(missing_ok=True)
            except:
                pass
            return None

    def _evict_entries(self) -> None:
        """Evict entries based on strategy"""
        if not self._memory_cache:
            return

        # Remove expired entries first
        expired_keys = [
            key for key, entry in self._memory_cache.items() if entry.is_expired()
        ]

        for key in expired_keys:
            self._remove_from_memory(key)
            self.stats["evictions"] += 1

        # If still over limits, use strategy
        while (
            len(self._memory_cache) > self.max_memory_entries
            or self._memory_size > self.max_memory_bytes
        ):

            if not self._memory_cache:
                break

            # Find entry with lowest priority
            min_priority = float("inf")
            evict_key = None

            for key, entry in self._memory_cache.items():
                priority = self.strategy.get_priority(entry)
                if priority < min_priority:
                    min_priority = priority
                    evict_key = key

            if evict_key:
                self._remove_from_memory(evict_key)
                self.stats["evictions"] += 1
            else:
                break

    def _remove_from_memory(self, key: str) -> None:
        """Remove entry from memory cache"""
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if entry.size_bytes:
                self._memory_size -= entry.size_bytes
            del self._memory_cache[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        # Try memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]

            if entry.is_expired():
                self._remove_from_memory(key)
            else:
                entry.update_access()
                self.stats["hits"] += 1
                return entry.value

        # Try file cache
        entry = self._load_from_file(key)
        if entry:
            # Promote to memory cache
            self.set(key, entry.value, ttl=entry.ttl_seconds)
            self.stats["file_cache_hits"] += 1
            return entry.value

        # Cache miss
        self.stats["misses"] += 1
        if self.enable_file_cache:
            self.stats["file_cache_misses"] += 1

        return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        # Calculate size
        size_bytes = self._calculate_size(value)

        # Create entry
        entry = CacheEntry(
            value=value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl or self.default_ttl,
            size_bytes=size_bytes,
        )

        # Remove existing entry if present
        if key in self._memory_cache:
            self._remove_from_memory(key)

        # Add to memory cache
        self._memory_cache[key] = entry
        self._memory_size += size_bytes

        # Save to file cache
        self._save_to_file(key, entry)

        # Evict if necessary
        self._evict_entries()

    def remove(self, key: str) -> bool:
        """Remove entry from cache

        Args:
            key: Cache key to remove

        Returns:
            True if entry was removed, False if not found
        """
        removed = False

        # Remove from memory
        if key in self._memory_cache:
            self._remove_from_memory(key)
            removed = True

        # Remove from file
        if self.enable_file_cache:
            try:
                file_path = self._get_file_path(key)
                if file_path.exists():
                    file_path.unlink()
                    removed = True
            except Exception:
                pass

        return removed

    def clear(self) -> None:
        """Clear all cache entries"""
        # Clear memory cache
        self._memory_cache.clear()
        self._memory_size = 0

        # Clear file cache
        if self.enable_file_cache and self.cache_dir:
            try:
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
            except Exception:
                pass

    def cache_function(
        self, ttl: Optional[int] = None, key_func: Optional[Callable] = None
    ):
        """Decorator for caching function results

        Args:
            ttl: Time-to-live for cached results
            key_func: Function to generate cache key from args
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            def wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    key_parts = [func.__name__]
                    key_parts.extend(str(arg) for arg in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = "|".join(key_parts)

                # Try to get from cache
                result = self.get(cache_key)
                if result is not None:
                    return result

                # Call function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl=ttl)

                return result

            return wrapper

        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "name": self.name,
            "memory_entries": len(self._memory_cache),
            "memory_size_mb": self._memory_size / (1024 * 1024),
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            **self.stats,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        removed_count = 0

        # Clean memory cache
        expired_keys = [
            key for key, entry in self._memory_cache.items() if entry.is_expired()
        ]

        for key in expired_keys:
            self._remove_from_memory(key)
            removed_count += 1

        # Clean file cache
        if self.enable_file_cache and self.cache_dir:
            try:
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        with open(cache_file, "rb") as f:
                            cache_data = pickle.load(f)

                        created_at = datetime.fromisoformat(cache_data["created_at"])
                        ttl = cache_data.get("ttl_seconds")

                        if ttl and (datetime.now() - created_at).total_seconds() > ttl:
                            cache_file.unlink()
                            removed_count += 1
                    except Exception:
                        # Remove corrupted files
                        cache_file.unlink()
                        removed_count += 1
            except Exception:
                pass

        return removed_count


# Global cache instances for common use cases
_global_caches: Dict[str, SmartCache] = {}


def get_cache(name: str = "default", **kwargs) -> SmartCache:
    """Get or create a named cache instance

    Args:
        name: Cache name
        **kwargs: Additional arguments for cache creation

    Returns:
        SmartCache instance
    """
    if name not in _global_caches:
        _global_caches[name] = SmartCache(name=name, **kwargs)

    return _global_caches[name]


def cached(
    cache_name: str = "default",
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None,
):
    """Convenience decorator for caching function results

    Args:
        cache_name: Name of cache to use
        ttl: Time-to-live for cached results
        key_func: Function to generate cache key
    """
    cache = get_cache(cache_name)
    return cache.cache_function(ttl=ttl, key_func=key_func)
