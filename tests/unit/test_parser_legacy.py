"""
parser.pyモジュールのユニットテスト

このテストファイルは、kumihan_formatter.parser モジュールの
後方互換性機能、設定クラス、エラーハンドリングをテストします。
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from typing import Any, Dict, List

from kumihan_formatter.parser import (
    ParallelProcessingError,
    ChunkProcessingError,
    MemoryMonitoringError,
    ParallelProcessingConfig,
    Parser,
    parse,
    parse_with_error_config,
)

# TYPE_CHECKINGブロックのテスト用インポート
import kumihan_formatter.parser


class TestParallelProcessingErrors:
    """並列処理エラークラスのテスト"""

    def test_parallel_processing_error_creation(self):
        """ParallelProcessingErrorの生成テスト"""
        error = ParallelProcessingError("Test parallel error")
        assert str(error) == "Test parallel error"
        assert isinstance(error, Exception)

    def test_chunk_processing_error_creation(self):
        """ChunkProcessingErrorの生成テスト"""
        error = ChunkProcessingError("Test chunk error")
        assert str(error) == "Test chunk error"
        assert isinstance(error, Exception)

    def test_memory_monitoring_error_creation(self):
        """MemoryMonitoringErrorの生成テスト"""
        error = MemoryMonitoringError("Test memory error")
        assert str(error) == "Test memory error"
        assert isinstance(error, Exception)


class TestParallelProcessingConfig:
    """ParallelProcessingConfigクラスのテスト"""

    def test_default_initialization(self):
        """デフォルト初期化のテスト"""
        config = ParallelProcessingConfig()

        # デフォルト値の確認
        assert config.parallel_threshold_lines == 10000
        assert config.parallel_threshold_size == 10 * 1024 * 1024
        assert config.min_chunk_size == 50
        assert config.max_chunk_size == 2000
        assert config.target_chunks_per_core == 2
        assert config.memory_warning_threshold_mb == 150
        assert config.memory_critical_threshold_mb == 250
        assert config.memory_check_interval == 10
        assert config.processing_timeout_seconds == 300
        assert config.chunk_timeout_seconds == 30
        assert config.enable_progress_callbacks is True
        assert config.progress_update_interval == 100
        assert config.enable_memory_monitoring is True
        assert config.enable_gc_optimization is True

    def test_from_environment_with_no_env_vars(self):
        """環境変数なしでのfrom_environment実行テスト"""
        config = ParallelProcessingConfig.from_environment()

        # デフォルト値と同じであることを確認
        default_config = ParallelProcessingConfig()
        assert (
            config.parallel_threshold_lines == default_config.parallel_threshold_lines
        )
        assert config.parallel_threshold_size == default_config.parallel_threshold_size

    def test_from_environment_with_env_vars(self):
        """環境変数ありでのfrom_environment実行テスト"""
        env_vars = {
            "KUMIHAN_PARALLEL_THRESHOLD_LINES": "5000",
            "KUMIHAN_PARALLEL_THRESHOLD_SIZE": "5242880",  # 5MB
            "KUMIHAN_MEMORY_LIMIT_MB": "200",
            "KUMIHAN_PROCESSING_TIMEOUT": "600",
        }

        with patch.dict(os.environ, env_vars):
            config = ParallelProcessingConfig.from_environment()

            assert config.parallel_threshold_lines == 5000
            assert config.parallel_threshold_size == 5242880
            assert config.memory_critical_threshold_mb == 200
            assert config.memory_warning_threshold_mb == 120  # 60% of 200
            assert config.processing_timeout_seconds == 600

    def test_from_environment_with_invalid_env_vars(self):
        """不正な環境変数でのfrom_environment実行テスト"""
        env_vars = {
            "KUMIHAN_PARALLEL_THRESHOLD_LINES": "invalid",
            "KUMIHAN_PARALLEL_THRESHOLD_SIZE": "not_a_number",
            "KUMIHAN_MEMORY_LIMIT_MB": "abc",
            "KUMIHAN_PROCESSING_TIMEOUT": "xyz",
        }

        with patch.dict(os.environ, env_vars):
            config = ParallelProcessingConfig.from_environment()

            # 不正な値は無視されてデフォルト値が使用される
            default_config = ParallelProcessingConfig()
            assert (
                config.parallel_threshold_lines
                == default_config.parallel_threshold_lines
            )
            assert (
                config.parallel_threshold_size == default_config.parallel_threshold_size
            )

    def test_validate_success(self):
        """正常な設定値でのvalidate成功テスト"""
        config = ParallelProcessingConfig()
        assert config.validate() is True

    def test_validate_failure_cases(self):
        """設定値の検証失敗テスト"""
        config = ParallelProcessingConfig()

        # parallel_threshold_linesが0以下
        config.parallel_threshold_lines = -1
        assert config.validate() is False

        # max_chunk_sizeがmin_chunk_size以下
        config = ParallelProcessingConfig()
        config.max_chunk_size = config.min_chunk_size - 1
        assert config.validate() is False

        # memory_critical_threshold_mbがmemory_warning_threshold_mb以下
        config = ParallelProcessingConfig()
        config.memory_critical_threshold_mb = config.memory_warning_threshold_mb - 1
        assert config.validate() is False


class TestParserLegacyInterface:
    """パーサーのレガシーインターフェースのテスト"""

    def test_parser_import_alias(self):
        """Parserエイリアスのインポートテスト"""
        assert Parser is not None
        # インスタンス生成可能性を確認
        parser = Parser()
        assert parser is not None

    def test_parse_function_basic(self):
        """parse関数の基本テスト"""
        with patch("kumihan_formatter.parser.Parser") as MockParser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse.return_value = []
            MockParser.return_value = mock_parser_instance

            result = parse("test text")

            MockParser.assert_called_once_with(None)
            mock_parser_instance.parse.assert_called_once_with("test text")
            assert result == []

    def test_parse_function_with_config(self):
        """設定付きparse関数のテスト"""
        config = {"test": "value"}
        with patch("kumihan_formatter.parser.Parser") as MockParser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse.return_value = []
            MockParser.return_value = mock_parser_instance

            result = parse("test text", config=config)

            MockParser.assert_called_once_with(config)
            mock_parser_instance.parse.assert_called_once_with("test text")

    def test_parse_with_error_config_small_text(self):
        """小さなテキストでのparse_with_error_config実行テスト"""
        small_text = "Small text"

        with patch("kumihan_formatter.parser.Parser") as MockParser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse.return_value = []
            MockParser.return_value = mock_parser_instance

            result = parse_with_error_config(small_text)

            MockParser.assert_called_once()
            mock_parser_instance.parse.assert_called_once_with(small_text)

    def test_parse_with_error_config_large_text(self):
        """大きなテキストでのparse_with_error_config実行テスト"""
        # 1MB超のテキストを生成
        large_text = "Large text " * 100000

        with patch(
            "kumihan_formatter.parser.StreamingParser", create=True
        ) as MockStreamingParser:
            mock_streaming_instance = MagicMock()
            mock_streaming_instance.parse_streaming_from_text.return_value = iter([])
            MockStreamingParser.return_value = mock_streaming_instance

            result = parse_with_error_config(large_text)

            MockStreamingParser.assert_called_once_with(json_path="")
            assert result == []

    def test_parse_with_error_config_explicit_streaming_true(self):
        """明示的にストリーミング=Trueでのparse_with_error_config実行テスト"""
        text = "Test text"

        with patch(
            "kumihan_formatter.parser.StreamingParser", create=True
        ) as MockStreamingParser:
            mock_streaming_instance = MagicMock()
            mock_streaming_instance.parse_streaming_from_text.return_value = iter([])
            MockStreamingParser.return_value = mock_streaming_instance

            result = parse_with_error_config(text, use_streaming=True)

            MockStreamingParser.assert_called_once_with(json_path="")

    def test_parse_with_error_config_explicit_streaming_false(self):
        """明示的にストリーミング=Falseでのparse_with_error_config実行テスト"""
        text = "Test text"

        with patch("kumihan_formatter.parser.Parser") as MockParser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse.return_value = []
            MockParser.return_value = mock_parser_instance

            result = parse_with_error_config(text, use_streaming=False)

            MockParser.assert_called_once()
            mock_parser_instance.parse.assert_called_once_with(text)

    def test_module_exports_all_required_items(self):
        """__all__で定義されたアイテムがすべてエクスポートされることをテスト"""
        from kumihan_formatter import parser

        required_exports = [
            "ParallelProcessingError",
            "ChunkProcessingError",
            "MemoryMonitoringError",
            "ParallelProcessingConfig",
            "Parser",
            "parse",
            "parse_with_error_config",
        ]

        for item in required_exports:
            assert hasattr(parser, item), f"Missing export: {item}"

    def test_type_checking_imports(self):
        """TYPE_CHECKINGブロック内のインポートテスト"""
        import typing

        # TYPE_CHECKINGの状態を模擬的に確認
        with patch.object(typing, "TYPE_CHECKING", True):
            # TYPE_CHECKINGがTrueの時の動作をテスト
            # パーサーモジュールを再インポートして、条件付きインポートをトリガー
            import importlib
            import kumihan_formatter.parser as parser_module

            importlib.reload(parser_module)

            # モジュールが正常にインポートされることを確認
            assert parser_module is not None
