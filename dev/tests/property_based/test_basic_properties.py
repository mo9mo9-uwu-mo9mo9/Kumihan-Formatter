"""Basic property-based tests without external dependencies

These tests implement simple property-based testing concepts
without requiring hypothesis or pytest.
"""

import sys
import time
import random
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kumihan_formatter.parser import Parser
from kumihan_formatter.core.common import SmartCache


def test_parser_never_crashes():
    """Test that parser handles various inputs without crashing"""
    parser = Parser()
    
    # Test cases with different characteristics
    test_inputs = [
        "",
        "   ",
        "\n\n\n",
        "Simple text",
        ";;;太字\nテスト\n;;;",
        ";;;見出し1\nタイトル\n;;;",
        "- リスト項目",
        "・別のリスト",
        "1. 番号付きリスト",
        "普通の段落\n\n別の段落",
        ";;;invalid_keyword\ncontent\n;;;",
        ";;;太字\n\n;;;",  # Empty block
        ";;;太字+イタリック\n複合\n;;;",
        "text with ;;; in middle",
        "text\n;;;太字\nblock\n;;;\nmore text",
    ]
    
    # Add some random inputs
    for _ in range(10):
        length = random.randint(1, 100)
        chars = ''.join(random.choices('abcdefg\n ;;;太字イタリック見出し1', k=length))
        test_inputs.append(chars)
    
    passed = 0
    failed = 0
    
    for i, test_input in enumerate(test_inputs):
        try:
            result = parser.parse(test_input)
            
            # Basic assertions
            assert isinstance(result, list), f"Result should be list, got {type(result)}"
            
            # All items should be nodes (basic duck typing check)
            for item in result:
                assert hasattr(item, 'type'), f"Node should have 'type' attribute"
            
            passed += 1
            print(f"✅ Test {i+1}: PASSED")
            
        except Exception as e:
            failed += 1
            print(f"❌ Test {i+1}: FAILED - {e}")
            print(f"   Input: {repr(test_input[:50])}")
    
    print(f"\nParser Crash Test Results: {passed} passed, {failed} failed")
    return failed == 0


def test_cache_properties():
    """Test cache properties and invariants"""
    cache = SmartCache("property_test", enable_file_cache=False)
    
    passed = 0
    failed = 0
    
    # Test 1: Set-Get roundtrip
    try:
        test_data = [
            ("key1", "value1"),
            ("key2", 42),
            ("key3", [1, 2, 3]),
            ("key4", {"nested": "dict"}),
        ]
        
        for key, value in test_data:
            cache.set(key, value)
            result = cache.get(key)
            assert result == value, f"Roundtrip failed: {value} != {result}"
        
        passed += 1
        print("✅ Cache roundtrip test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Cache roundtrip test: FAILED - {e}")
    
    # Test 2: Default values
    try:
        default_val = "default"
        result = cache.get("nonexistent_key", default_val)
        assert result == default_val, f"Default value failed: {result} != {default_val}"
        
        result_none = cache.get("another_nonexistent")
        assert result_none is None, f"None default failed: {result_none}"
        
        passed += 1
        print("✅ Cache default values: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Cache default values: FAILED - {e}")
    
    # Test 3: TTL expiration
    try:
        cache.set("ttl_key", "ttl_value", ttl=1)
        
        # Should be available immediately
        result = cache.get("ttl_key")
        assert result == "ttl_value", f"TTL immediate get failed"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        result_expired = cache.get("ttl_key", "expired")
        assert result_expired == "expired", f"TTL expiration failed"
        
        passed += 1
        print("✅ Cache TTL test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Cache TTL test: FAILED - {e}")
    
    # Test 4: Size limits
    try:
        # Create cache with small limit
        small_cache = SmartCache("small_test", max_memory_entries=3, enable_file_cache=False)
        
        # Add more than limit
        for i in range(5):
            small_cache.set(f"key_{i}", f"value_{i}")
        
        stats = small_cache.get_stats()
        assert stats['memory_entries'] <= 3, f"Size limit violated: {stats['memory_entries']}"
        
        small_cache.clear()
        passed += 1
        print("✅ Cache size limit test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Cache size limit test: FAILED - {e}")
    
    # Test 5: Statistics consistency
    try:
        cache.clear()
        initial_stats = cache.get_stats()
        
        cache.set("stats_key", "stats_value")
        cache.get("stats_key")  # Hit
        cache.get("nonexistent")  # Miss
        
        final_stats = cache.get_stats()
        
        assert final_stats['hits'] > initial_stats['hits'], "Hits should increase"
        assert final_stats['misses'] > initial_stats['misses'], "Misses should increase"
        assert final_stats['total_requests'] == final_stats['hits'] + final_stats['misses'], "Total should equal hits + misses"
        
        passed += 1
        print("✅ Cache statistics test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Cache statistics test: FAILED - {e}")
    
    cache.clear()
    print(f"\nCache Property Test Results: {passed} passed, {failed} failed")
    return failed == 0


def test_error_framework_properties():
    """Test error framework properties"""
    from kumihan_formatter.core.common import KumihanError, ErrorSeverity, ErrorCategory
    
    passed = 0
    failed = 0
    
    # Test 1: Error creation and formatting
    try:
        error = KumihanError(
            "Test error message",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.SYNTAX,
            user_message="User friendly message",
            suggestions=["Fix this", "Try that"]
        )
        
        # Test formatting
        user_format = error.format_for_user()
        dev_format = error.format_for_developer()
        
        assert "User friendly message" in user_format, "User message not in user format"
        assert "Fix this" in user_format, "Suggestions not in user format"
        assert "Test error message" in dev_format, "Technical message not in dev format"
        assert error.error_code.startswith("SX"), "Error code should start with category prefix"
        
        passed += 1
        print("✅ Error framework basic test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Error framework basic test: FAILED - {e}")
    
    # Test 2: Error serialization
    try:
        error_dict = error.to_dict()
        
        required_fields = ['error_code', 'severity', 'category', 'message', 'user_message']
        for field in required_fields:
            assert field in error_dict, f"Missing field: {field}"
        
        assert error_dict['severity'] == 'warning', "Severity serialization failed"
        assert error_dict['category'] == 'syntax', "Category serialization failed"
        
        passed += 1
        print("✅ Error serialization test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Error serialization test: FAILED - {e}")
    
    print(f"\nError Framework Test Results: {passed} passed, {failed} failed")
    return failed == 0


def test_validation_mixin_properties():
    """Test validation mixin properties"""
    from kumihan_formatter.core.common import ValidationMixin
    
    passed = 0
    failed = 0
    
    # Test 1: Basic validation rules
    try:
        class TestValidator(ValidationMixin):
            def __init__(self):
                super().__init__()
                self.require_not_empty("name")
                self.require_type("age", int)
                self.require_in_range("score", min_val=0, max_val=100)
        
        validator = TestValidator()
        
        # Valid data
        valid_data = {"name": "test", "age": 25, "score": 85}
        assert validator.is_valid(valid_data), "Valid data should pass validation"
        
        # Invalid data
        invalid_data = {"name": "", "age": "not_int", "score": 150}
        assert not validator.is_valid(invalid_data), "Invalid data should fail validation"
        
        errors = validator.get_validation_errors()
        assert len(errors) > 0, "Should have validation errors"
        
        passed += 1
        print("✅ Validation mixin basic test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Validation mixin basic test: FAILED - {e}")
    
    # Test 2: Custom validation rules
    try:
        class CustomValidator(ValidationMixin):
            def __init__(self):
                super().__init__()
                self.add_simple_rule(
                    "email",
                    lambda x: "@" in str(x),
                    "Email must contain @",
                    suggestion="Add @ symbol to email"
                )
        
        custom_validator = CustomValidator()
        
        # Valid email
        assert custom_validator.is_valid({"email": "test@example.com"}), "Valid email should pass"
        
        # Invalid email
        assert not custom_validator.is_valid({"email": "invalid"}), "Invalid email should fail"
        
        passed += 1
        print("✅ Validation mixin custom rules test: PASSED")
        
    except Exception as e:
        failed += 1
        print(f"❌ Validation mixin custom rules test: FAILED - {e}")
    
    print(f"\nValidation Mixin Test Results: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all property-based tests"""
    print("🧪 Running Property-Based Tests for Kumihan-Formatter")
    print("=" * 60)
    
    all_passed = True
    
    print("\n📝 Testing Parser Properties...")
    parser_result = test_parser_never_crashes()
    all_passed &= parser_result
    
    print("\n💾 Testing Cache Properties...")
    cache_result = test_cache_properties()
    all_passed &= cache_result
    
    print("\n🚨 Testing Error Framework Properties...")
    error_result = test_error_framework_properties()
    all_passed &= error_result
    
    print("\n✅ Testing Validation Mixin Properties...")
    validation_result = test_validation_mixin_properties()
    all_passed &= validation_result
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All property-based tests PASSED!")
        return True
    else:
        print("💥 Some property-based tests FAILED!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)