"""
performance_logger.py分割のためのテスト

TDD: 分割後の新しいモジュール構造のテスト
Issue #492 Phase 5A - performance_logger.py分割
"""

from unittest.mock import Mock, patch

import pytest


class TestPerformanceDecorators:
    """パフォーマンスデコレーター関数のテスト"""

    def test_performance_decorators_module_import(self):
        """RED: パフォーマンスデコレーターモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_decorators import (
                log_performance_decorator,
            )

    def test_log_performance_decorator_function(self):
        """RED: パフォーマンスデコレーター関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_decorators import (
                log_performance_decorator,
            )

            @log_performance_decorator(include_memory=True)
            def test_function():
                return "test"


class TestPerformanceTrackers:
    """パフォーマンストラッキング関数のテスト"""

    def test_performance_trackers_module_import(self):
        """RED: パフォーマンストラッカーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_trackers import (
                call_chain_tracker,
            )

    def test_call_chain_tracker_function(self):
        """RED: コールチェーントラッカー関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_trackers import (
                call_chain_tracker,
            )

            tracker = call_chain_tracker(max_depth=5)

    def test_memory_usage_tracker_function(self):
        """RED: メモリ使用量トラッカー関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_trackers import (
                memory_usage_tracker,
            )

            memory_info = memory_usage_tracker()


class TestPerformanceOptimizer:
    """パフォーマンス最適化クラスのテスト"""

    def test_performance_optimizer_module_import(self):
        """RED: パフォーマンス最適化モジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_optimizer import (
                LogPerformanceOptimizer,
            )

    def test_log_performance_optimizer_class(self):
        """RED: ログパフォーマンス最適化クラステスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_optimizer import (
                LogPerformanceOptimizer,
            )

            mock_logger = Mock()
            optimizer = LogPerformanceOptimizer(mock_logger)

    def test_should_log_method(self):
        """RED: ログ判定メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_optimizer import (
                LogPerformanceOptimizer,
            )

            mock_logger = Mock()
            optimizer = LogPerformanceOptimizer(mock_logger)
            result = optimizer.should_log(20, "test_key")

    def test_get_performance_report_method(self):
        """RED: パフォーマンスレポート生成メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_optimizer import (
                LogPerformanceOptimizer,
            )

            mock_logger = Mock()
            optimizer = LogPerformanceOptimizer(mock_logger)
            report = optimizer.get_performance_report()


class TestPerformanceFactory:
    """パフォーマンスファクトリー関数のテスト"""

    def test_performance_factory_module_import(self):
        """RED: パフォーマンスファクトリーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_factory import (
                get_log_performance_optimizer,
            )

    def test_get_log_performance_optimizer_function(self):
        """RED: ログパフォーマンス最適化取得関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.utilities.performance_factory import (
                get_log_performance_optimizer,
            )

            optimizer = get_log_performance_optimizer("test_module")


class TestOriginalPerformanceLogger:
    """元のperformance_loggerクラスとの互換性テスト"""

    def test_original_performance_logger_still_works(self):
        """元のperformance_loggerが正常動作することを確認"""
        from kumihan_formatter.core.utilities.performance_logger import (
            LogPerformanceOptimizer,
            call_chain_tracker,
            get_log_performance_optimizer,
            log_performance_decorator,
            memory_usage_tracker,
        )

        # 基本機能が存在することを確認
        assert callable(log_performance_decorator)
        assert callable(call_chain_tracker)
        assert callable(memory_usage_tracker)
        assert LogPerformanceOptimizer is not None
        assert callable(get_log_performance_optimizer)

    def test_original_decorator_functionality(self):
        """元のデコレーター機能テスト"""
        from kumihan_formatter.core.utilities.performance_logger import (
            log_performance_decorator,
        )

        # デコレーターが正常に動作することを確認
        @log_performance_decorator(operation="test_op")
        def test_function():
            return "test_result"

        # 実行できることを確認
        result = test_function()
        assert result == "test_result"

    def test_original_tracker_functionality(self):
        """元のトラッカー機能テスト"""
        from kumihan_formatter.core.utilities.performance_logger import (
            call_chain_tracker,
            memory_usage_tracker,
        )

        # トラッカー機能が正常に動作することを確認
        call_info = call_chain_tracker(max_depth=3)
        assert isinstance(call_info, dict)
        assert "call_chain" in call_info

        memory_info = memory_usage_tracker()
        assert isinstance(memory_info, dict)
        assert "memory_rss_mb" in memory_info

    def test_original_optimizer_functionality(self):
        """元の最適化機能テスト"""
        from kumihan_formatter.core.utilities.performance_logger import (
            get_log_performance_optimizer,
        )

        # 最適化機能が正常に動作することを確認
        optimizer = get_log_performance_optimizer("test_module")
        assert optimizer is not None

        # 基本メソッドが存在することを確認
        assert hasattr(optimizer, "should_log")
        assert hasattr(optimizer, "get_performance_report")
        assert hasattr(optimizer, "record_log_event")
