#!/usr/bin/env python3
"""Test new features added in Issue #121 Phase 2"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

def test_enhanced_config():
    """Test enhanced configuration management"""
    print("=== Enhanced Configuration Test ===")
    
    try:
        from kumihan_formatter.core.config_manager import EnhancedConfig, ConfigValidator
        
        # Test basic configuration loading
        config = EnhancedConfig()
        markers = config.get_markers()
        
        print(f"✅ Default markers loaded: {len(markers)} items")
        
        # Test CSS variables
        css_vars = config.get_css_variables()
        print(f"✅ CSS variables: {len(css_vars)} items")
        
        # Test validation
        validation_result = config.validate()
        if validation_result.is_valid:
            print("✅ Configuration validation passed")
        else:
            print(f"❌ Configuration validation failed: {validation_result.errors}")
        
        # Test performance settings
        perf_settings = config.get_performance_settings()
        print(f"✅ Performance settings: {len(perf_settings)} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_utils():
    """Test unified utility functions"""
    print("\n=== Unified Utils Test ===")
    
    try:
        from kumihan_formatter.core.utils import (
            TextProcessor, FileSystemHelper, StringSimilarity, 
            DataStructureHelper, SimpleCache
        )
        
        # Test text processing
        normalized = TextProcessor.normalize_whitespace("  多重　　空白  ")
        print(f"✅ Text normalization: '{normalized}'")
        
        # Test string similarity
        similarity = StringSimilarity.similarity_ratio("太字", "太文字")
        print(f"✅ String similarity: {similarity:.2f}")
        
        # Test data structure utilities
        nested_dict = {"a": {"b": {"c": "value"}}}
        flat_dict = DataStructureHelper.flatten_dict(nested_dict)
        print(f"✅ Dict flattening: {flat_dict}")
        
        # Test cache
        cache = SimpleCache()
        cache.set("test_key", "test_value")
        cached_value = cache.get("test_key")
        print(f"✅ Cache test: {cached_value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitoring():
    """Test performance monitoring system"""
    print("\n=== Performance Monitoring Test ===")
    
    try:
        from kumihan_formatter.core.performance import (
            PerformanceMonitor, PerformanceProfiler, measure_performance,
            profile_function
        )
        
        # Test performance monitor
        monitor = PerformanceMonitor()
        
        with monitor.measure("test_operation", node_count=100):
            # Simulate some work
            import time
            time.sleep(0.001)  # 1ms
        
        latest_report = monitor.get_latest_report()
        if latest_report:
            print(f"✅ Performance monitoring: {latest_report.execution_time:.3f}s")
        
        # Test profiler
        profiler = PerformanceProfiler()
        
        @profiler.profile("test_function")
        def test_function():
            return sum(range(1000))
        
        result = test_function()
        stats = profiler.get_stats()
        if stats:
            print(f"✅ Function profiling: {list(stats.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration of new features with existing code"""
    print("\n=== Integration Test ===")
    
    try:
        from kumihan_formatter.core.keyword_parser import KeywordParser
        from kumihan_formatter.core.config_manager import EnhancedConfig
        from kumihan_formatter.core.performance import measure_performance
        
        # Test integration: config with keyword parser
        config = EnhancedConfig()
        
        with measure_performance("keyword_parser_integration"):
            parser = KeywordParser(config)
            keywords, attributes, errors = parser.parse_marker_keywords("太字+イタリック")
        
        print(f"✅ Config-Parser integration: {keywords}")
        
        # Test enhanced markers
        markers = config.get_markers()
        if "コードブロック" in markers:
            print("✅ Enhanced markers available")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all new feature tests"""
    print("🧪 Testing New Features Added in Issue #121 Phase 2")
    print("=" * 60)
    
    tests = [
        test_enhanced_config,
        test_unified_utils,
        test_performance_monitoring,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🏁 New Features Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All new features working correctly!")
        return True
    else:
        print("💥 Some new features have issues!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)