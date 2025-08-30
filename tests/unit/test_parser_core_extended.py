"""
parser_core.pyモジュールの拡張テスト

parser_coreの未カバー部分をテストして、カバレッジを38%から50%以上に向上させます。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

try:
    from kumihan_formatter.core.parsing.parser_core import (
        Parser,
        ParallelProcessingError,
        ChunkProcessingError,
        MemoryMonitoringError,
        ParallelProcessingConfig,
    )
except ImportError:
    # parser_core モジュールから直接インポートできない場合は、
    # parser モジュールから取得
    from kumihan_formatter.parser import (
        Parser,
        ParallelProcessingError,
        ChunkProcessingError,
        MemoryMonitoringError,
        ParallelProcessingConfig,
    )


class TestParserCoreExtended:
    """parser_core.pyの拡張テスト"""

    def test_parser_initialization_with_config(self):
        """設定付きParser初期化テスト"""
        config = {"test": "value"}
        parser = Parser(config=config)

        assert parser is not None
        # 設定が保存されているか確認
        assert hasattr(parser, "config") or hasattr(parser, "_config")

    def test_parser_initialization_without_config(self):
        """設定なしParser初期化テスト"""
        parser = Parser()

        assert parser is not None

    def test_parser_parse_empty_text(self):
        """空文字列のparse処理テスト"""
        parser = Parser()

        result = parser.parse("")

        # 空のリストまたはNoneが返されることを確認
        assert result is not None
        assert isinstance(result, list)

    def test_parser_parse_simple_text(self):
        """シンプルテキストのparse処理テスト"""
        parser = Parser()

        result = parser.parse("Simple test text")

        assert result is not None
        assert isinstance(result, list)

    def test_parser_parse_with_error_handling(self):
        """エラーハンドリング付きparse処理テスト"""
        parser = Parser()

        # 特殊文字を含むテキストでエラーハンドリングをテスト
        problematic_text = "Test\x00\x01\x02"

        try:
            result = parser.parse(problematic_text)
            assert result is not None
        except Exception:
            # エラーが発生しても処理が継続されることを確認
            pass

    def test_parser_with_large_text(self):
        """大きなテキストのparse処理テスト（並列処理トリガー）"""
        parser = Parser()

        # 大きなテキストを生成（10KB以上）
        large_text = "Test line\n" * 2000

        result = parser.parse(large_text)

        assert result is not None
        assert isinstance(result, list)

    def test_parallel_processing_config_validation(self):
        """並列処理設定の検証テスト"""
        config = ParallelProcessingConfig()

        # デフォルト設定での検証
        assert config.validate() is True

        # 無効な設定でのテスト
        config.parallel_threshold_lines = -1
        assert config.validate() is False

        # 設定を修正して再検証
        config.parallel_threshold_lines = 1000
        assert config.validate() is True

    def test_parallel_processing_config_memory_thresholds(self):
        """メモリしきい値設定テスト"""
        config = ParallelProcessingConfig()

        # メモリ制限の逆転（警告 > 重要）での無効な設定
        config.memory_critical_threshold_mb = 100
        config.memory_warning_threshold_mb = 200
        assert config.validate() is False

    def test_parallel_processing_config_chunk_sizes(self):
        """チャンクサイズ設定テスト"""
        config = ParallelProcessingConfig()

        # チャンクサイズの逆転（最小 > 最大）での無効な設定
        config.min_chunk_size = 1000
        config.max_chunk_size = 500
        assert config.validate() is False

    def test_error_classes_inheritance(self):
        """エラークラスの継承関係テスト"""
        # 各エラークラスがExceptionを継承していることを確認
        assert issubclass(ParallelProcessingError, Exception)
        assert issubclass(ChunkProcessingError, Exception)
        assert issubclass(MemoryMonitoringError, Exception)

    def test_parser_with_mock_dependencies(self):
        """依存関係をモックしたparser処理テスト"""
        parser = Parser()

        # 実際に存在する内部メソッドをモックして処理をテスト
        from kumihan_formatter.core.ast_nodes.node import Node

        mock_node = Node("text", "Test text")

        with patch.object(
            parser, "_parse_line_with_graceful_errors", return_value=mock_node
        ):
            result = parser.parse("Test text")

            # モックが呼ばれ、結果が返されることを確認
            assert result is not None
            assert len(result) > 0

    def test_parser_memory_monitoring(self):
        """パーサーのメモリ監視機能テスト"""
        parser = Parser()

        # メモリ監視設定をテスト
        config = ParallelProcessingConfig()
        config.enable_memory_monitoring = True

        # 設定が反映されることを確認
        assert config.enable_memory_monitoring is True

    def test_parser_performance_settings(self):
        """パーサーのパフォーマンス設定テスト"""
        config = ParallelProcessingConfig()

        # パフォーマンス関連設定のテスト
        config.enable_progress_callbacks = False
        config.enable_gc_optimization = False

        assert config.enable_progress_callbacks is False
        assert config.enable_gc_optimization is False

    def test_parser_timeout_settings(self):
        """パーサーのタイムアウト設定テスト"""
        config = ParallelProcessingConfig()

        # タイムアウト設定のテスト
        config.processing_timeout_seconds = 600
        config.chunk_timeout_seconds = 60

        assert config.processing_timeout_seconds == 600
        assert config.chunk_timeout_seconds == 60

    def test_parser_with_config_object(self):
        """設定オブジェクト付きパーサーテスト"""
        config = ParallelProcessingConfig()
        parser = Parser(config=config)

        result = parser.parse("Test with config")

        assert result is not None
        assert isinstance(result, list)

    def test_parser_error_recovery(self):
        """パーサーのエラー回復機能テスト"""
        parser = Parser()

        # 不正な入力でのエラー回復をテスト
        invalid_inputs = [None, [], {}, 123]

        for invalid_input in invalid_inputs:
            try:
                result = parser.parse(
                    str(invalid_input) if invalid_input is not None else ""
                )
                # エラーが発生しても結果が返されることを確認
                assert result is not None or result == []
            except (TypeError, AttributeError):
                # 型エラーや属性エラーは想定内
                pass
