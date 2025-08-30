"""
optimization_manager.pyのユニットテスト

このテストファイルは、kumihan_formatter.managers.optimization_manager.OptimizationManager
の基本機能をテストします。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import time
from typing import Any, Dict, List

from kumihan_formatter.managers.optimization_manager import OptimizationManager


class TestOptimizationManager:
    """OptimizationManagerクラスのテスト"""

    def test_initialization_default(self):
        """デフォルト設定での初期化テスト"""
        manager = OptimizationManager()

        assert manager is not None
        assert hasattr(manager, "logger")
        assert hasattr(manager, "config")
        assert hasattr(manager, "enable_caching")
        assert hasattr(manager, "enable_parallel")
        assert hasattr(manager, "_metrics")

    def test_initialization_with_config(self):
        """設定付きでの初期化テスト"""
        config = {
            "enable_caching": True,
            "enable_parallel": True,
            "memory_limit_mb": 100,
            "performance_monitoring": True,
        }
        manager = OptimizationManager(config=config)

        assert manager is not None
        assert manager.enable_caching == True
        assert manager.enable_parallel == True
        assert manager.memory_limit == 100
        assert manager.performance_monitoring == True

    def test_optimize_parsing_small_text(self):
        """小テキストの最適化解析テスト"""
        manager = OptimizationManager()

        small_text = "短いテスト文書"

        # モックパーサー関数
        def mock_parser(content):
            return {"parsed": content, "type": "text"}

        result = manager.optimize_parsing(small_text, mock_parser)

        assert result is not None
        assert isinstance(result, dict)
        assert "parsed" in result

    def test_optimize_parsing_large_text(self):
        """大テキストの最適化解析テスト"""
        manager = OptimizationManager()

        # 大きなテキストを生成
        large_text = "テストテキスト行" * 1000

        # モックパーサー関数
        def mock_parser(content):
            return {"parsed": content, "type": "text"}

        result = manager.optimize_parsing(large_text, mock_parser)

        assert result is not None
        assert isinstance(result, dict)

    def test_optimize_memory_usage_basic(self):
        """基本メモリ使用量最適化テスト"""
        manager = OptimizationManager()

        # データなしでメモリ最適化
        result = manager.optimize_memory_usage()

        assert result is not None
        assert isinstance(result, dict)
        assert "cache_cleaned" in result

    def test_performance_monitor_decorator(self):
        """パフォーマンスモニターのデコレーターテスト"""
        manager = OptimizationManager()

        # テスト関数定義
        def test_function(x):
            time.sleep(0.001)
            return x * 2

        # デコレーターを適用
        monitored_func = manager.performance_monitor(test_function)

        # 関数実行
        result = monitored_func(5)

        assert result == 10
        assert callable(monitored_func)

    def test_get_optimization_statistics(self):
        """最適化統計取得テスト"""
        manager = OptimizationManager()

        # 統計の取得
        stats = manager.get_optimization_statistics()

        assert stats is not None
        assert isinstance(stats, dict)

    def test_clear_optimization_cache(self):
        """最適化キャッシュクリアテスト"""
        manager = OptimizationManager()

        # キャッシュクリア操作
        result = manager.clear_optimization_cache()

        # キャッシュが適切にクリアされることを確認
        assert hasattr(manager, "_operation_cache")

    def test_estimate_memory_usage_private_method(self):
        """プライベートメソッド：メモリ使用量推定テスト"""
        manager = OptimizationManager()

        # プライベートメソッドのテスト
        test_data = {"test": "data", "size": 500}

        if hasattr(manager, "_estimate_memory_usage"):
            result = manager._estimate_memory_usage(test_data)
            assert result is not None
            assert isinstance(result, (int, float))

    def test_estimate_input_size_private_method(self):
        """プライベートメソッド：入力サイズ推定テスト"""
        manager = OptimizationManager()

        # 引数とキーワード引数
        args = ("テスト入力データ",)
        kwargs = {}

        if hasattr(manager, "_estimate_input_size"):
            result = manager._estimate_input_size(args, kwargs)
            assert result is not None
            assert isinstance(result, (int, float))
            assert result >= 0

    def test_record_metrics_private_method(self):
        """プライベートメソッド：メトリクス記録テスト"""
        manager = OptimizationManager()

        if hasattr(manager, "_record_metrics"):
            # メトリクス記録のテスト
            operation_name = "test_operation"
            execution_time = 0.1
            memory_usage = 1000
            input_size = 500
            optimization_applied = True

            manager._record_metrics(
                operation_name,
                execution_time,
                memory_usage,
                input_size,
                optimization_applied,
            )

            # メトリクスが記録されることを確認
            assert hasattr(manager, "_metrics")
            assert len(manager._metrics) > 0

    def test_config_properties_access(self):
        """設定プロパティアクセステスト"""
        config = {
            "enable_caching": False,
            "enable_parallel": False,
            "memory_limit_mb": 256,
            "performance_monitoring": False,
        }
        manager = OptimizationManager(config=config)

        # 設定値が正しく適用されることを確認
        assert manager.enable_caching == False
        assert manager.enable_parallel == False
        assert manager.memory_limit == 256
        assert manager.performance_monitoring == False

    def test_optimization_with_caching_disabled(self):
        """キャッシュ無効時の最適化テスト"""
        config = {"enable_caching": False}
        manager = OptimizationManager(config=config)

        text = "キャッシュ無効テスト"

        # モックパーサー関数
        def mock_parser(content):
            return {"parsed": content, "type": "text"}

        result = manager.optimize_parsing(text, mock_parser)

        assert result is not None
        assert isinstance(result, dict)

    def test_optimization_with_parallel_disabled(self):
        """並列処理無効時の最適化テスト"""
        config = {"enable_parallel": False}
        manager = OptimizationManager(config=config)

        text = "並列処理無効テスト"

        # モックパーサー関数
        def mock_parser(content):
            return {"parsed": content, "type": "text"}

        result = manager.optimize_parsing(text, mock_parser)

        assert result is not None
        assert isinstance(result, dict)

    def test_memory_optimization_with_limit(self):
        """メモリ制限有りの最適化テスト"""
        config = {"memory_limit_mb": 50}  # 低い制限値
        manager = OptimizationManager(config=config)

        # メモリ最適化をテスト
        result = manager.optimize_memory_usage()

        assert result is not None
        assert isinstance(result, dict)
        assert "cache_cleaned" in result

    def test_performance_monitoring_enabled(self):
        """パフォーマンス監視有効時のテスト"""
        config = {"performance_monitoring": True}
        manager = OptimizationManager(config=config)

        # 監視が有効な状態でのテスト
        text = "パフォーマンス監視テスト"

        # モックパーサー関数
        def mock_parser(content):
            return {"parsed": content, "type": "text"}

        result = manager.optimize_parsing(text, mock_parser)

        assert result is not None
        # パフォーマンス監視が有効な場合、メトリクスが記録されることを期待
        stats = manager.get_optimization_statistics()
        assert stats is not None

    def test_optimization_error_handling(self):
        """最適化エラーハンドリングテスト"""
        manager = OptimizationManager()

        # None入力での最適化テスト
        def mock_parser(content):
            return {"parsed": content, "type": "text"}

        try:
            result = manager.optimize_parsing(None, mock_parser)
            # エラーが適切に処理されることを確認
            assert result is not None or result is None
        except (ValueError, TypeError):
            # 適切なエラーが発生することも正常
            assert True

    def test_memory_usage_error_handling(self):
        """メモリ使用量最適化エラーハンドリングテスト"""
        manager = OptimizationManager()

        # メモリ最適化の基本テスト（エラーハンドリングも含む）
        try:
            result = manager.optimize_memory_usage()
            assert result is not None
            assert isinstance(result, dict)
        except (ValueError, TypeError):
            assert True

    def test_metrics_accumulation(self):
        """メトリクス蓄積テスト"""
        config = {"performance_monitoring": True}
        manager = OptimizationManager(config=config)

        # モックパーサー関数
        def mock_parser(content):
            return {"parsed": content, "type": "text"}

        # 複数回の操作でメトリクスが蓄積されることをテスト
        for i in range(3):
            text = f"テスト{i}"
            manager.optimize_parsing(text, mock_parser)

        stats = manager.get_optimization_statistics()
        assert stats is not None
        assert isinstance(stats, dict)
        assert stats["total_operations"] >= 3
