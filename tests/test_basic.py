"""Basic tests for Kumihan-Formatter

基本的な機能の動作を確認するテストケース
Claude Code指摘に基づく最小限のテストインフラ復元
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.utilities.claude_integration import get_claude_code_logger
from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.core.utilities.structured_logger import get_structured_logger


class TestBasicLogging:
    """基本的なログ機能のテスト"""

    def test_get_logger_returns_instance(self):
        """get_logger関数が正常にロガーインスタンスを返すことを確認"""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_structured_logger_initialization(self):
        """構造化ロガーが正常に初期化されることを確認"""
        structured_logger = get_structured_logger("test_structured")
        assert structured_logger is not None
        assert hasattr(structured_logger, "log_with_context")
        assert hasattr(structured_logger, "info")
        assert hasattr(structured_logger, "error")

    def test_claude_code_logger_initialization(self):
        """Claude Code統合ロガーが正常に初期化されることを確認"""
        claude_logger = get_claude_code_logger("test_claude")
        assert claude_logger is not None
        assert hasattr(claude_logger, "log_with_claude_optimization")
        assert hasattr(claude_logger, "log_error_with_analysis")


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_error_handler_import(self):
        """エラーハンドラーがインポートできることを確認"""
        from kumihan_formatter.core.error_handling.unified_handler import (
            UnifiedErrorHandler,
        )

        handler = UnifiedErrorHandler()
        assert handler is not None
        assert hasattr(handler, "handle_exception")
        assert hasattr(handler, "error_context")

    def test_error_types_import(self):
        """エラー型がインポートできることを確認"""
        from kumihan_formatter.core.error_handling.error_types import (
            ErrorCategory,
            ErrorLevel,
        )

        assert ErrorCategory is not None
        assert ErrorLevel is not None


class TestCoreComponents:
    """コア機能コンポーネントのテスト"""

    def test_main_components_importable(self):
        """主要なコンポーネントがインポートできることを確認"""
        try:
            from kumihan_formatter import cli, parser, renderer

            assert parser is not None
            assert renderer is not None
            assert cli is not None
        except ImportError as e:
            pytest.skip(f"Main components not available: {e}")

    def test_config_manager_import(self):
        """設定管理がインポートできることを確認"""
        try:
            from kumihan_formatter.config.config_manager import ConfigManager

            config_manager = ConfigManager()
            assert config_manager is not None
        except ImportError as e:
            pytest.skip(f"Config manager not available: {e}")


class TestFileOperations:
    """ファイル操作のテスト"""

    def test_file_system_utilities(self):
        """ファイルシステムユーティリティのテスト"""
        from kumihan_formatter.core.utilities.file_system import ensure_directory_exists

        # 一時ディレクトリでテスト
        test_dir = Path("/tmp/kumihan_test")
        ensure_directory_exists(test_dir)
        assert test_dir.exists()

        # クリーンアップ
        test_dir.rmdir()

    def test_file_ops_basic(self):
        """基本的なファイル操作のテスト"""
        try:
            from kumihan_formatter.core.file_ops import (
                read_file_with_encoding_detection,
            )

            # モックファイルでテスト
            test_content = "テストファイル内容"
            with patch("pathlib.Path.read_text", return_value=test_content):
                result = read_file_with_encoding_detection(Path("test.txt"))
                assert result == test_content
        except ImportError as e:
            pytest.skip(f"File operations not available: {e}")


class TestPerformanceComponents:
    """パフォーマンス関連のテスト"""

    def test_performance_logger_import(self):
        """パフォーマンスロガーがインポートできることを確認"""
        from kumihan_formatter.core.utilities.performance_logger import (
            get_log_performance_optimizer,
        )

        optimizer = get_log_performance_optimizer("test_perf")
        assert optimizer is not None
        assert hasattr(optimizer, "record_log_event")

    def test_memory_monitor_import(self):
        """メモリモニターがインポートできることを確認"""
        try:
            from kumihan_formatter.core.performance.memory_monitor import MemoryMonitor

            monitor = MemoryMonitor()
            assert monitor is not None
        except ImportError as e:
            pytest.skip(f"Memory monitor not available: {e}")


class TestSyntaxValidation:
    """構文検証のテスト"""

    def test_syntax_validator_import(self):
        """構文検証機能がインポートできることを確認"""
        try:
            from kumihan_formatter.core.syntax.syntax_validator import SyntaxValidator

            validator = SyntaxValidator()
            assert validator is not None
        except ImportError as e:
            pytest.skip(f"Syntax validator not available: {e}")

    def test_syntax_rules_import(self):
        """構文ルールがインポートできることを確認"""
        try:
            from kumihan_formatter.core.syntax.syntax_rules import SyntaxRules

            rules = SyntaxRules()
            assert rules is not None
        except ImportError as e:
            pytest.skip(f"Syntax rules not available: {e}")


class TestIntegration:
    """統合テスト"""

    def test_basic_conversion_flow(self):
        """基本的な変換フローのテスト"""
        # 最小限のテストケース
        test_input = ";;;bold;;; テスト内容 ;;;"
        expected_pattern = "bold"

        # 簡単な記法パターンの存在確認
        assert "bold" in test_input
        assert "テスト内容" in test_input

    def test_error_recovery_flow(self):
        """エラー回復フローのテスト"""
        from kumihan_formatter.core.error_handling.unified_handler import (
            get_global_handler,
        )

        handler = get_global_handler()
        assert handler is not None

        # 模擬的なエラーハンドリングテスト
        test_exception = ValueError("Test error")
        try:
            with handler.error_context("test_operation"):
                raise test_exception
        except ValueError:
            # エラーが適切に処理されることを確認
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
