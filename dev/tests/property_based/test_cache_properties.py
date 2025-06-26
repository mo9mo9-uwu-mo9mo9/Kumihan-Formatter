"""Property-based tests for the SmartCache system

These tests verify cache behavior across various scenarios
and ensure cache invariants hold under all conditions.
"""

import pytest
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from . import HAS_HYPOTHESIS

if HAS_HYPOTHESIS:
    from hypothesis import given, strategies as st, settings, assume
    from hypothesis.strategies import text, integers, dictionaries, composite
else:
    # Create dummy decorators if hypothesis not available
    def given(*args, **kwargs):
        def decorator(func):
            def wrapper(*args, **kwargs):
                pytest.skip("hypothesis not available")
            return wrapper
        return decorator
    
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class DummyStrategies:
        text = lambda *args, **kwargs: None
        integers = lambda *args, **kwargs: None
        dictionaries = lambda *args, **kwargs: None
    
    st = DummyStrategies()
    composite = lambda func: func
    assume = lambda x: None

from kumihan_formatter.core.common import SmartCache, LRUStrategy, LFUStrategy


@composite
def cache_key_value(draw):
    """Generate cache key-value pairs"""
    if not HAS_HYPOTHESIS:
        return ("test_key", "test_value")
    
    key = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))))
    value = draw(st.one_of(
        st.text(max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.lists(st.text(max_size=20), max_size=10)
    ))
    return (key, value)


@composite
def cache_operations(draw):
    """Generate a sequence of cache operations"""
    if not HAS_HYPOTHESIS:
        return [("set", "key1", "value1"), ("get", "key1")]
    
    operations = []
    num_ops = draw(st.integers(min_value=1, max_value=20))
    
    for _ in range(num_ops):
        op_type = draw(st.sampled_from(["set", "get", "remove"]))
        key = draw(st.text(min_size=1, max_size=20))
        
        if op_type == "set":
            value = draw(st.text(max_size=50))
            operations.append((op_type, key, value))
        else:
            operations.append((op_type, key))
    
    return operations


class TestCacheProperties:
    """Property-based tests for cache behavior"""
    
    @given(cache_key_value())
    @settings(max_examples=50)
    def test_set_get_roundtrip(self, key_value):
        """What you set should be what you get"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        key, value = key_value
        cache = SmartCache("test_roundtrip", enable_file_cache=False)
        
        try:
            cache.set(key, value)
            retrieved = cache.get(key)
            
            assert retrieved == value, f"Set {value}, got {retrieved}"
            
        except Exception as e:
            pytest.fail(f"Set-get roundtrip failed for {key}: {value}, error: {e}")
        finally:
            cache.clear()
    
    @given(st.lists(cache_key_value(), min_size=1, max_size=10))
    @settings(max_examples=30)
    def test_multiple_entries_independence(self, key_values):
        """Multiple cache entries should not interfere with each other"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        # Ensure unique keys
        unique_items = {}
        for key, value in key_values:
            unique_items[key] = value
        
        assume(len(unique_items) >= 2)  # Need at least 2 items
        
        cache = SmartCache("test_independence", enable_file_cache=False)
        
        try:
            # Set all values
            for key, value in unique_items.items():
                cache.set(key, value)
            
            # Verify all values
            for key, expected_value in unique_items.items():
                actual_value = cache.get(key)
                assert actual_value == expected_value, f"Key {key}: expected {expected_value}, got {actual_value}"
            
        except Exception as e:
            pytest.fail(f"Independence test failed: {e}")
        finally:
            cache.clear()
    
    @given(cache_key_value())
    @settings(max_examples=30)
    def test_nonexistent_key_returns_default(self, key_value):
        """Getting a nonexistent key should return the default value"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        key, default_value = key_value
        cache = SmartCache("test_default", enable_file_cache=False)
        
        try:
            # Key should not exist
            result = cache.get(key + "_nonexistent", default_value)
            assert result == default_value
            
            # Should also work with None default
            result_none = cache.get(key + "_nonexistent")
            assert result_none is None
            
        except Exception as e:
            pytest.fail(f"Default value test failed: {e}")
        finally:
            cache.clear()
    
    @given(cache_operations())
    @settings(max_examples=20)
    def test_cache_operations_sequence(self, operations):
        """Cache should handle any sequence of operations"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        cache = SmartCache("test_sequence", enable_file_cache=False)
        stored_values = {}
        
        try:
            for operation in operations:
                op_type = operation[0]
                key = operation[1]
                
                if op_type == "set":
                    value = operation[2]
                    cache.set(key, value)
                    stored_values[key] = value
                
                elif op_type == "get":
                    result = cache.get(key)
                    expected = stored_values.get(key)
                    if expected is not None:
                        assert result == expected, f"Get {key}: expected {expected}, got {result}"
                
                elif op_type == "remove":
                    cache.remove(key)
                    if key in stored_values:
                        del stored_values[key]
            
            # Verify final state
            for key, expected_value in stored_values.items():
                actual_value = cache.get(key)
                assert actual_value == expected_value
            
        except Exception as e:
            pytest.fail(f"Operations sequence failed: {e}")
        finally:
            cache.clear()
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=15)
    def test_ttl_expiration(self, ttl_seconds):
        """Entries should expire after TTL"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        # Use very short TTL for testing
        short_ttl = min(ttl_seconds, 2)  # Cap at 2 seconds for test speed
        
        cache = SmartCache("test_ttl", enable_file_cache=False)
        
        try:
            cache.set("ttl_key", "ttl_value", ttl=short_ttl)
            
            # Should be available immediately
            result = cache.get("ttl_key")
            assert result == "ttl_value"
            
            # Wait for expiration (with small buffer)
            time.sleep(short_ttl + 0.1)
            
            # Should be expired now
            result_expired = cache.get("ttl_key", "expired")
            assert result_expired == "expired"
            
        except Exception as e:
            pytest.fail(f"TTL test failed: {e}")
        finally:
            cache.clear()


class TestCacheInvariants:
    """Test cache invariants that should always hold"""
    
    @given(st.integers(min_value=1, max_value=50))
    @settings(max_examples=20)
    def test_size_limits_respected(self, max_entries):
        """Cache should respect size limits"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        cache = SmartCache(
            "test_limits",
            max_memory_entries=max_entries,
            enable_file_cache=False
        )
        
        try:
            # Add more entries than the limit
            for i in range(max_entries + 10):
                cache.set(f"key_{i}", f"value_{i}")
            
            # Check that we don't exceed the limit
            stats = cache.get_stats()
            assert stats['memory_entries'] <= max_entries, f"Exceeded limit: {stats['memory_entries']} > {max_entries}"
            
        except Exception as e:
            pytest.fail(f"Size limit test failed: {e}")
        finally:
            cache.clear()
    
    @given(cache_key_value())
    @settings(max_examples=30)
    def test_cache_stats_consistency(self, key_value):
        """Cache statistics should be consistent"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        key, value = key_value
        cache = SmartCache("test_stats", enable_file_cache=False)
        
        try:
            initial_stats = cache.get_stats()
            
            # Perform operations
            cache.set(key, value)
            cache.get(key)  # Hit
            cache.get("nonexistent")  # Miss
            
            final_stats = cache.get_stats()
            
            # Stats should increase
            assert final_stats['hits'] >= initial_stats['hits']
            assert final_stats['misses'] >= initial_stats['misses']
            assert final_stats['total_requests'] >= initial_stats['total_requests']
            
            # Total should equal hits + misses
            assert final_stats['total_requests'] == final_stats['hits'] + final_stats['misses']
            
        except Exception as e:
            pytest.fail(f"Stats consistency test failed: {e}")
        finally:
            cache.clear()


class TestCacheStrategies:
    """Test different cache eviction strategies"""
    
    @given(st.lists(st.text(min_size=1, max_size=10), min_size=5, max_size=15, unique=True))
    @settings(max_examples=15)
    def test_lru_strategy_behavior(self, keys):
        """LRU strategy should evict least recently used items"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        assume(len(keys) >= 5)
        
        cache = SmartCache(
            "test_lru",
            max_memory_entries=3,  # Small limit to force eviction
            strategy=LRUStrategy(),
            enable_file_cache=False
        )
        
        try:
            # Fill cache beyond capacity
            for i, key in enumerate(keys[:5]):
                cache.set(key, f"value_{i}")
            
            # Access the first key to make it recently used
            cache.get(keys[0])
            
            # Add another key to force eviction
            cache.set("new_key", "new_value")
            
            # The first key should still be there (was recently accessed)
            result = cache.get(keys[0])
            assert result is not None, "Recently accessed item was evicted"
            
        except Exception as e:
            pytest.fail(f"LRU strategy test failed: {e}")
        finally:
            cache.clear()


if __name__ == "__main__":
    # Run property-based tests
    if HAS_HYPOTHESIS:
        pytest.main([__file__, "-v"])
    else:
        print("Hypothesis not available. Install with: pip install hypothesis")
        print("Skipping property-based tests.")