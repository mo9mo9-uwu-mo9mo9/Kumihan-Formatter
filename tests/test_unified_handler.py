"""
統一エラーハンドラーのテスト

Important Tier Phase 2-1対応 - Issue #593
エラーハンドリング系の体系的テスト実装
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_display import ErrorDisplay
from kumihan_formatter.core.error_handling.error_factories import ErrorFactory
from kumihan_formatter.core.error_handling.error_recovery import ErrorRecovery
from kumihan_formatter.core.error_handling.error_statistics import ErrorStatistics
from kumihan_formatter.core.error_handling.error_types import UserFriendlyError
from kumihan_formatter.core.error_handling.unified_handler import UnifiedErrorHandler


class TestUnifiedErrorHandler:
    """統一エラーハンドラーのテストクラス"""

    def test_init_with_defaults(self):
        """デフォルト設定での初期化テスト"""
        # When
        handler = UnifiedErrorHandler()

        # Then
        assert handler.console_ui is None
        assert handler.enable_logging is True
        assert handler.logger is not None
        assert isinstance(handler.display, ErrorDisplay)
        assert isinstance(handler.recovery, ErrorRecovery)
        assert isinstance(handler.statistics, ErrorStatistics)

    def test_init_with_custom_console_ui(self):
        """カスタムコンソールUIでの初期化テスト"""
        # Given
        mock_console = Mock()

        # When
        handler = UnifiedErrorHandler(console_ui=mock_console)

        # Then
        assert handler.console_ui is mock_console
        assert handler.display.console_ui is mock_console

    def test_init_without_logging(self):
        """ログ無効での初期化テスト"""
        # When
        handler = UnifiedErrorHandler(enable_logging=False)

        # Then
        assert handler.enable_logging is False
        assert handler.logger is None

    @patch("kumihan_formatter.core.error_handling.unified_handler.get_logger")
    def test_logger_initialization(self, mock_get_logger):
        """ロガー初期化のテスト"""
        # Given
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # When
        handler = UnifiedErrorHandler(enable_logging=True)

        # Then
        mock_get_logger.assert_called_with(
            "kumihan_formatter.core.error_handling.unified_handler"
        )
        assert handler.logger is mock_logger

    def test_error_context_manager(self):
        """error_contextコンテキストマネージャーの正常系テスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.logger = Mock()
        handler.statistics = Mock()
        handler.display = Mock()

        # When
        with handler.error_context("test_operation"):
            # 正常に処理が完了
            pass

        # Then
        # 正常終了時は統計に記録されない（例外時のみ）

    def test_error_context_with_exception(self):
        """error_contextコンテキストマネージャーの異常系テスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.logger = Mock()
        handler.statistics = Mock()
        handler.display = Mock()
        handler.recovery = Mock()
        handler.recovery.attempt_recovery.return_value = False
        test_error = ValueError("Test error")

        # When
        with pytest.raises(ValueError):
            with handler.error_context("test_operation"):
                raise test_error

        # Then
        handler.statistics.update_error_stats.assert_called()
        handler.display.display_error.assert_called()

    def test_handle_error_with_user_friendly_error(self):
        """UserFriendlyErrorの処理テスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.logger = Mock()
        handler.stats = Mock()
        handler.display = Mock()
        user_error = UserFriendlyError(
            message="ユーザー向けメッセージ",
            original_error=ValueError("元のエラー"),
            suggestions=["修正案1", "修正案2"],
        )

        # When
        with pytest.raises(UserFriendlyError):
            with handler.handle_error("test_operation"):
                raise user_error

        # Then
        handler.logger.error.assert_called()
        handler.stats.record_error.assert_called_once_with("test_operation", user_error)
        handler.display.show_error.assert_called_once_with(user_error)

    def test_handle_error_no_logging(self):
        """ログ無効時のhandle_errorテスト"""
        # Given
        handler = UnifiedErrorHandler(enable_logging=False)
        handler.stats = Mock()
        handler.display = Mock()

        # When
        with handler.handle_error("test_operation"):
            pass

        # Then
        handler.stats.record_success.assert_called_once_with("test_operation")
        # ログ出力されないことを確認
        assert handler.logger is None

    def test_handle_file_error_file_not_found(self):
        """handle_file_error: ファイルが見つからない場合のテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.display = Mock()
        file_path = Path("/nonexistent/file.txt")
        original_error = FileNotFoundError("File not found")

        # When
        result = handler.handle_file_error(file_path, original_error)

        # Then
        assert isinstance(result, UserFriendlyError)
        assert "ファイルが見つかりません" in result.message
        assert str(file_path) in result.message
        handler.display.show_error.assert_called_once_with(result)

    def test_handle_file_error_permission_denied(self):
        """handle_file_error: 権限エラーのテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.display = Mock()
        file_path = Path("/protected/file.txt")
        original_error = PermissionError("Permission denied")

        # When
        result = handler.handle_file_error(file_path, original_error)

        # Then
        assert isinstance(result, UserFriendlyError)
        assert "アクセス権限がありません" in result.message
        assert len(result.suggestions) > 0
        handler.display.show_error.assert_called_once_with(result)

    def test_handle_parse_error_encoding_issue(self):
        """handle_parse_error: エンコーディングエラーのテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.display = Mock()
        file_path = Path("test.txt")
        original_error = UnicodeDecodeError(
            "utf-8", b"\x80\x81", 0, 2, "invalid start byte"
        )

        # When
        result = handler.handle_parse_error(file_path, original_error, line_number=10)

        # Then
        assert isinstance(result, UserFriendlyError)
        assert "エンコーディングエラー" in result.message
        assert "10行目" in result.message
        handler.display.show_error.assert_called_once_with(result)

    def test_handle_parse_error_syntax_error(self):
        """handle_parse_error: 構文エラーのテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.display = Mock()
        file_path = Path("test.md")
        original_error = ValueError("Invalid markdown syntax")

        # When
        result = handler.handle_parse_error(
            file_path, original_error, line_number=20, line_content=";;;invalid;;;"
        )

        # Then
        assert isinstance(result, UserFriendlyError)
        assert "パースエラー" in result.message
        assert "20行目" in result.message
        assert ";;;invalid;;;" in result.message
        handler.display.show_error.assert_called_once_with(result)

    def test_handle_render_error_template_not_found(self):
        """handle_render_error: テンプレートエラーのテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.display = Mock()
        template_name = "missing_template.jinja2"
        original_error = FileNotFoundError("Template not found")

        # When
        result = handler.handle_render_error(template_name, original_error)

        # Then
        assert isinstance(result, UserFriendlyError)
        assert "テンプレートが見つかりません" in result.message
        assert template_name in result.message
        handler.display.show_error.assert_called_once_with(result)

    def test_handle_render_error_rendering_failure(self):
        """handle_render_error: レンダリングエラーのテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.display = Mock()
        template_name = "template.jinja2"
        original_error = ValueError("Undefined variable: foo")

        # When
        result = handler.handle_render_error(
            template_name, original_error, context={"bar": "value"}
        )

        # Then
        assert isinstance(result, UserFriendlyError)
        assert "レンダリングエラー" in result.message
        assert "Undefined variable: foo" in result.message
        handler.display.show_error.assert_called_once_with(result)

    def test_handle_config_error_invalid_value(self):
        """handle_config_error: 設定値エラーのテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.display = Mock()
        config_key = "max_file_size"
        original_error = ValueError("Invalid configuration value")

        # When
        result = handler.handle_config_error(
            config_key, original_error, expected_type=int, actual_value="not_a_number"
        )

        # Then
        assert isinstance(result, UserFriendlyError)
        assert "設定エラー" in result.message
        assert config_key in result.message
        assert "int" in result.message
        handler.display.show_error.assert_called_once_with(result)

    def test_recover_with_fallback_success(self):
        """recover_with_fallback: フォールバック成功のテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.recovery = Mock()
        handler.recovery.recover_with_fallback.return_value = "fallback_result"
        handler.logger = Mock()

        operation = Mock(side_effect=ValueError("Operation failed"))
        fallback = Mock(return_value="fallback_result")

        # When
        result = handler.recover_with_fallback(
            operation, fallback, operation_name="test_op"
        )

        # Then
        assert result == "fallback_result"
        handler.recovery.recover_with_fallback.assert_called_once()
        handler.logger.warning.assert_called()

    def test_recover_with_fallback_failure(self):
        """recover_with_fallback: フォールバック失敗のテスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.recovery = Mock()
        handler.recovery.recover_with_fallback.side_effect = Exception(
            "Recovery failed"
        )
        handler.logger = Mock()

        operation = Mock(side_effect=ValueError("Operation failed"))
        fallback = Mock(side_effect=Exception("Fallback failed"))

        # When/Then
        with pytest.raises(Exception):
            handler.recover_with_fallback(operation, fallback, operation_name="test_op")

    def test_create_user_friendly_error(self):
        """create_user_friendly_error: エラー生成テスト"""
        # Given
        handler = UnifiedErrorHandler()
        original_error = ValueError("Original error")
        error_type = "file"
        context = {"file_path": "/test/path.txt"}

        # When
        result = handler.create_user_friendly_error(original_error, error_type, context)

        # Then
        assert isinstance(result, UserFriendlyError)
        assert result.original_error is original_error
        assert result.context["error_type"] == error_type
        assert result.context["file_path"] == "/test/path.txt"

    def test_integration_file_operation_with_recovery(self):
        """統合テスト: ファイル操作とリカバリー"""
        # Given
        handler = UnifiedErrorHandler()
        handler.logger = Mock()

        # Create a temporary file with invalid encoding
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"\x80\x81\x82")  # Invalid UTF-8
            temp_path = Path(f.name)

        try:
            # When
            with handler.handle_error("file_read"):
                # This should raise UnicodeDecodeError
                with open(temp_path, "r", encoding="utf-8") as f:
                    content = f.read()
        except UnicodeDecodeError as e:
            # Then
            error = handler.handle_file_error(temp_path, e)
            assert isinstance(error, UserFriendlyError)
            assert "エンコーディング" in error.message
        finally:
            temp_path.unlink()

    def test_error_statistics_tracking(self):
        """エラー統計の追跡テスト"""
        # Given
        handler = UnifiedErrorHandler()
        handler.stats = Mock()

        # When - 成功ケース
        with handler.handle_error("successful_op"):
            pass

        # When - エラーケース
        try:
            with handler.handle_error("failed_op"):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Then
        assert handler.stats.record_success.call_count == 1
        assert handler.stats.record_error.call_count == 1
        handler.stats.record_success.assert_called_with("successful_op")
        handler.stats.record_error.assert_called_with(
            "failed_op", pytest.raises(ValueError).value.__class__
        )
