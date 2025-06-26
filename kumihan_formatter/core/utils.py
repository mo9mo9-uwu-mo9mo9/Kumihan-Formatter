"""Unified utility functions for Kumihan-Formatter

This module consolidates all utility functions used across the codebase
into a single, well-organized module with clear categorization.
"""

import re
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Iterator
from dataclasses import dataclass
from functools import wraps


# ============================================================================
# Text Processing Utilities
# ============================================================================

class TextProcessor:
    """Advanced text processing utilities"""
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text"""
        # Replace multiple whitespace with single space
        normalized = re.sub(r'\s+', ' ', text.strip())
        return normalized
    
    @staticmethod
    def extract_text_from_html(html: str) -> str:
        """Extract plain text from HTML (simple implementation)"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities (basic ones)
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return TextProcessor.normalize_whitespace(text)
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to specified length with suffix"""
        if len(text) <= max_length:
            return text
        
        truncated_length = max_length - len(suffix)
        if truncated_length <= 0:
            return suffix[:max_length]
        
        return text[:truncated_length] + suffix
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text (Japanese-aware)"""
        # Japanese text doesn't use spaces between words
        # Count characters for Japanese, words for Latin
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        latin_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        # Estimate: Japanese characters count as words, plus Latin words
        return japanese_chars + latin_words
    
    @staticmethod
    def generate_slug(text: str, max_length: int = 50) -> str:
        """Generate URL-friendly slug from text"""
        # Remove HTML tags
        text = TextProcessor.extract_text_from_html(text)
        
        # Convert to lowercase and replace non-alphanumeric with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = slug.strip('-')
        
        # Truncate if necessary
        if len(slug) > max_length:
            slug = slug[:max_length].rstrip('-')
        
        return slug


# ============================================================================
# File System Utilities
# ============================================================================

class FileSystemHelper:
    """File system operation utilities"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
        """Get file hash for change detection"""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def get_safe_filename(filename: str, replacement: str = '_') -> str:
        """Get safe filename by replacing invalid characters"""
        # Characters that are problematic in filenames
        invalid_chars = r'<>:"/\\|?*'
        safe_name = filename
        
        for char in invalid_chars:
            safe_name = safe_name.replace(char, replacement)
        
        # Remove leading/trailing dots and spaces
        safe_name = safe_name.strip('. ')
        
        # Ensure it's not empty
        if not safe_name:
            safe_name = 'untitled'
        
        return safe_name
    
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = '*', 
                  recursive: bool = True) -> Iterator[Path]:
        """Find files matching pattern"""
        directory = Path(directory)
        
        if recursive:
            return directory.rglob(pattern)
        else:
            return directory.glob(pattern)


# ============================================================================
# Performance Utilities
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Performance measurement results"""
    execution_time: float
    memory_usage: Optional[int] = None
    operations_count: Optional[int] = None
    
    def __str__(self) -> str:
        parts = [f"Time: {self.execution_time:.3f}s"]
        if self.memory_usage:
            parts.append(f"Memory: {self.memory_usage:,} bytes")
        if self.operations_count:
            parts.append(f"Operations: {self.operations_count:,}")
        return " | ".join(parts)


class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    @staticmethod
    def measure_time(func):
        """Decorator to measure function execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            print(f"{func.__name__} executed in {execution_time:.3f} seconds")
            
            return result
        return wrapper
    
    @staticmethod
    def measure_performance(func):
        """Decorator to measure comprehensive performance metrics"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss
            start_time = time.perf_counter()
            
            result = func(*args, **kwargs)
            
            end_time = time.perf_counter()
            end_memory = process.memory_info().rss
            
            metrics = PerformanceMetrics(
                execution_time=end_time - start_time,
                memory_usage=end_memory - start_memory
            )
            
            print(f"{func.__name__} performance: {metrics}")
            
            return result
        return wrapper


# ============================================================================
# Data Structure Utilities
# ============================================================================

class DataStructureHelper:
    """Utilities for working with data structures"""
    
    @staticmethod
    def deep_merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge multiple dictionaries"""
        result = {}
        
        for d in dicts:
            for key, value in d.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = DataStructureHelper.deep_merge_dicts(result[key], value)
                else:
                    result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataStructureHelper.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    @staticmethod
    def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
        """Unflatten dictionary with dot notation keys"""
        result = {}
        for key, value in d.items():
            parts = key.split(sep)
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result
    
    @staticmethod
    def get_nested_value(d: Dict[str, Any], key_path: str, default: Any = None, sep: str = '.') -> Any:
        """Get nested dictionary value using dot notation"""
        keys = key_path.split(sep)
        current = d
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def set_nested_value(d: Dict[str, Any], key_path: str, value: Any, sep: str = '.') -> None:
        """Set nested dictionary value using dot notation"""
        keys = key_path.split(sep)
        current = d
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


# ============================================================================
# String Similarity Utilities  
# ============================================================================

class StringSimilarity:
    """String similarity calculation utilities"""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return StringSimilarity.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def similarity_ratio(s1: str, s2: str) -> float:
        """Calculate similarity ratio (0.0 to 1.0)"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        distance = StringSimilarity.levenshtein_distance(s1, s2)
        return (max_len - distance) / max_len
    
    @staticmethod
    def find_closest_matches(target: str, candidates: List[str], 
                           min_similarity: float = 0.6, max_results: int = 3) -> List[Tuple[str, float]]:
        """Find closest matching strings"""
        matches = []
        
        for candidate in candidates:
            similarity = StringSimilarity.similarity_ratio(target.lower(), candidate.lower())
            if similarity >= min_similarity:
                matches.append((candidate, similarity))
        
        # Sort by similarity (descending) and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]


# ============================================================================
# Error Handling Utilities
# ============================================================================

class ErrorRecovery:
    """Error recovery and suggestion utilities"""
    
    @staticmethod
    def suggest_corrections(error_msg: str, valid_options: List[str]) -> List[str]:
        """Suggest corrections based on error message"""
        suggestions = []
        
        # Extract potential misspelled word from error message
        words = re.findall(r'\b\w+\b', error_msg.lower())
        
        for word in words:
            if len(word) >= 3:  # Only suggest for words with 3+ characters
                matches = StringSimilarity.find_closest_matches(word, valid_options)
                suggestions.extend([match[0] for match in matches])
        
        # Remove duplicates while preserving order
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:3]  # Return top 3 suggestions


# ============================================================================
# Caching Utilities
# ============================================================================

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


# ============================================================================
# Logging Utilities
# ============================================================================

class LogHelper:
    """Logging utility functions"""
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format byte size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 1:
            return f"{seconds*1000:.1f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


# ============================================================================
# Convenience Functions
# ============================================================================

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to boolean"""
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    elif isinstance(value, (int, float)):
        return bool(value)
    else:
        return default


def chunks(lst: List[Any], n: int) -> Iterator[List[Any]]:
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]