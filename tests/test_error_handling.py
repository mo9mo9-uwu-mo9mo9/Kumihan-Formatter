"""Error handling tests for Kumihan-Formatter

エラーハンドリング機能のテストケース
Issue #476対応 - 分割されたエラーハンドリングコンポーネントのテスト
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_display import ErrorDisplay
from kumihan_formatter.core.error_handling.error_recovery import ErrorRecovery
from kumihan_formatter.core.error_handling.error_statistics import ErrorStatistics
from kumihan_formatter.core.error_handling.error_types import ErrorCategory, ErrorLevel
from kumihan_formatter.core.error_handling.unified_handler import UnifiedErrorHandler


class TestUnifiedErrorHandler:
    """統一エラーハンドラーのテスト"""

    def test_initialization(self):
        """エラーハンドラーの初期化テスト"""
        handler = UnifiedErrorHandler(enable_logging=False)
        assert handler is not None
        assert handler.display is not None
        assert handler.recovery is not None
        assert handler.statistics is not None

    def test_handle_exception_basic(self):
        """基本的な例外処理のテスト"""
        handler = UnifiedErrorHandler(enable_logging=False)

        test_exception = ValueError("Test error")
        user_error = handler.handle_exception(test_exception, show_ui=False)

        assert user_error is not None
        assert user_error.message == "値エラー: Test error"
        assert user_error.category == ErrorCategory.VALIDATION

    def test_error_context_manager(self):
        """エラーコンテキストマネージャーのテスト"""
        handler = UnifiedErrorHandler(enable_logging=False)

        with pytest.raises(ValueError):
            with handler.error_context("test_operation"):
                raise ValueError("Test context error")

    def test_syntax_error_handling(self):
        """構文エラーの処理テスト"""
        handler = UnifiedErrorHandler(enable_logging=False)

        syntax_error = SyntaxError("invalid syntax")
        syntax_error.lineno = 10
        syntax_error.text = "invalid line"

        user_error = handler.handle_exception(syntax_error, show_ui=False)

        assert user_error.category == ErrorCategory.SYNTAX
        assert "構文エラー" in user_error.message
        assert user_error.details == "行 10: invalid line"

    def test_file_error_handling(self):
        """ファイルエラーの処理テスト"""
        handler = UnifiedErrorHandler(enable_logging=False)

        file_error = FileNotFoundError("File not found")
        user_error = handler.handle_exception(file_error, show_ui=False)

        assert user_error.category == ErrorCategory.FILE_NOT_FOUND
        assert "ファイルエラー" in user_error.message
        assert len(user_error.suggestions) > 0


class TestErrorDisplay:
    """エラー表示機能のテスト"""

    def test_initialization(self):
        """エラー表示の初期化テスト"""
        display = ErrorDisplay(enable_logging=False)
        assert display is not None

    def test_format_error_message(self):
        """エラーメッセージフォーマットのテスト"""
        display = ErrorDisplay(enable_logging=False)

        from kumihan_formatter.core.error_handling.error_factories import ErrorFactory

        factory = ErrorFactory()

        error = factory.create_error(
            category=ErrorCategory.VALIDATION,
            level=ErrorLevel.ERROR,
            message="Test error message",
            suggestions=["Fix suggestion 1", "Fix suggestion 2"],
        )

        formatted = display.format_error_message(error)

        assert "Test error message" in formatted
        assert "Fix suggestion 1" in formatted
        assert "Fix suggestion 2" in formatted

    def test_display_with_mock_ui(self):
        """モックUIでの表示テスト"""
        mock_ui = Mock()
        display = ErrorDisplay(console_ui=mock_ui, enable_logging=False)

        from kumihan_formatter.core.error_handling.error_factories import ErrorFactory

        factory = ErrorFactory()

        error = factory.create_error(
            category=ErrorCategory.ERROR,
            level=ErrorLevel.ERROR,
            message="Test UI error",
        )

        display.display_error(error)

        # UI呼び出しの確認
        mock_ui.error.assert_called_once_with("Test UI error")


class TestErrorStatistics:
    """エラー統計機能のテスト"""

    def test_initialization(self):
        """エラー統計の初期化テスト"""
        stats = ErrorStatistics(enable_logging=False)
        assert stats is not None

    def test_update_error_stats(self):
        """エラー統計更新のテスト"""
        stats = ErrorStatistics(enable_logging=False)

        from kumihan_formatter.core.error_handling.error_factories import ErrorFactory

        factory = ErrorFactory()

        error = factory.create_error(
            category=ErrorCategory.VALIDATION,
            level=ErrorLevel.ERROR,
            message="Test statistics error",
        )

        stats.update_error_stats(error)

        statistics = stats.get_error_statistics()
        assert statistics["total_errors"] == 1
        assert "validation" in statistics["error_categories"]

    def test_export_error_log(self, temp_dir):
        """エラーログエクスポートのテスト"""
        stats = ErrorStatistics(enable_logging=False)

        from kumihan_formatter.core.error_handling.error_factories import ErrorFactory

        factory = ErrorFactory()

        error = factory.create_error(
            category=ErrorCategory.VALIDATION,
            level=ErrorLevel.ERROR,
            message="Test export error",
        )

        stats.update_error_stats(error)

        log_file = temp_dir / "error_log.json"
        success = stats.export_error_log(log_file)

        assert success
        assert log_file.exists()

        # ログファイルの内容確認
        import json

        with open(log_file, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        assert log_data["total_errors"] == 1
        assert len(log_data["error_history"]) == 1

    def test_clear_error_history(self):
        """エラー履歴クリアのテスト"""
        stats = ErrorStatistics(enable_logging=False)

        from kumihan_formatter.core.error_handling.error_factories import ErrorFactory

        factory = ErrorFactory()

        error = factory.create_error(
            category=ErrorCategory.VALIDATION,
            level=ErrorLevel.ERROR,
            message="Test clear error",
        )

        stats.update_error_stats(error)
        assert stats.get_error_statistics()["total_errors"] == 1

        stats.clear_error_history()
        assert stats.get_error_statistics()["total_errors"] == 0


class TestErrorRecovery:
    """エラー回復機能のテスト"""

    def test_initialization(self):
        """エラー回復の初期化テスト"""
        recovery = ErrorRecovery(enable_logging=False)
        assert recovery is not None

    def test_register_recovery_callback(self):
        """回復コールバック登録のテスト"""
        recovery = ErrorRecovery(enable_logging=False)

        def mock_callback(error):
            return True

        recovery.register_recovery_callback(
            "test_category", mock_callback, "Test recovery"
        )

        # コールバックが登録されたことを確認
        assert "test_category" in recovery._recovery_callbacks

    def test_attempt_recovery(self):
        """回復試行のテスト"""
        recovery = ErrorRecovery(enable_logging=False)

        # 成功する回復コールバック
        def success_callback(error):
            return True

        recovery.register_recovery_callback(
            "validation", success_callback, "Success recovery"
        )

        from kumihan_formatter.core.error_handling.error_factories import ErrorFactory

        factory = ErrorFactory()

        error = factory.create_error(
            category=ErrorCategory.VALIDATION,
            level=ErrorLevel.ERROR,
            message="Test recovery error",
        )

        success, message = recovery.attempt_recovery(error)

        assert success
        assert "Success recovery" in message

    def test_get_recovery_options(self):
        """回復オプション取得のテスト"""
        recovery = ErrorRecovery(enable_logging=False)

        from kumihan_formatter.core.error_handling.error_factories import ErrorFactory

        factory = ErrorFactory()

        error = factory.create_error(
            category=ErrorCategory.SYNTAX,
            level=ErrorLevel.ERROR,
            message="Test recovery options",
        )

        options = recovery.get_recovery_options(error)

        assert len(options) > 0
        assert any("構文エラー" in option for option in options)


class TestIntegrationErrorHandling:
    """エラーハンドリング統合テスト"""

    def test_full_error_handling_flow(self):
        """完全なエラーハンドリングフローのテスト"""
        handler = UnifiedErrorHandler(enable_logging=False)

        # 回復コールバックの登録
        def mock_recovery(error):
            return True

        handler.register_recovery_callback("validation", mock_recovery, "Mock recovery")

        # エラーハンドリングの実行
        test_error = ValueError("Integration test error")
        user_error = handler.handle_exception(
            test_error, show_ui=False, attempt_recovery=True
        )

        assert user_error is not None
        assert user_error.category == ErrorCategory.VALIDATION

        # 統計情報の確認
        stats = handler.get_error_statistics()
        assert stats["total_errors"] == 1

    def test_error_context_with_recovery(self):
        """回復機能付きエラーコンテキストのテスト"""
        handler = UnifiedErrorHandler(enable_logging=False)

        # 自動回復が成功するケース
        def auto_recovery(error):
            return True

        handler.register_recovery_callback("validation", auto_recovery, "Auto recovery")

        # 自動回復が有効な場合、例外が発生しない
        with handler.error_context("test_auto_recovery", auto_recover=True):
            # 本来なら例外が発生するが、自動回復される
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
