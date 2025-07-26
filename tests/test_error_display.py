"""
エラー表示機能のテスト

Important Tier Phase 2-1対応 - Issue #593
エラー表示とコンソール出力機能の体系的テスト実装
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_display import ErrorDisplay
from kumihan_formatter.core.error_handling.error_types import (
    ErrorCategory,
    ErrorLevel,
    ErrorSolution,
    UserFriendlyError,
)


class TestErrorDisplay:
    """エラー表示機能のテストクラス"""

    def test_init_with_defaults(self):
        """デフォルト設定での初期化テスト"""
        # When
        display = ErrorDisplay()

        # Then
        assert display.console_ui is None
        assert display.enable_logging is True

    def test_init_with_console_ui(self):
        """コンソールUI付き初期化テスト"""
        # Given
        mock_console = Mock()

        # When
        display = ErrorDisplay(console_ui=mock_console)

        # Then
        assert display.console_ui is mock_console
        assert display.enable_logging is True

    def test_init_without_logging(self):
        """ログなし初期化テスト"""
        # When
        display = ErrorDisplay(enable_logging=False)

        # Then
        assert display.console_ui is None
        assert display.enable_logging is False

    def test_display_error_with_ui(self):
        """UI経由でのエラー表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            error_code="TEST_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.UNKNOWN,
            user_message="Test error message",
            solution=ErrorSolution(
                quick_fix="Quick test fix", detailed_steps=["Step 1", "Step 2"]
            ),
        )

        # When
        display.display_error(error)

        # Then
        mock_console.error.assert_called_once_with(error.user_message)

    @patch("builtins.print")
    def test_display_error_fallback(self, mock_print):
        """フォールバック表示テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        error = UserFriendlyError(
            error_code="TEST_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.UNKNOWN,
            user_message="Test error message",
            solution=ErrorSolution(
                quick_fix="Quick test fix", detailed_steps=["Step 1", "Step 2"]
            ),
        )

        # When
        display.display_error(error)

        # Then
        mock_print.assert_called()
        printed_content = " ".join(
            str(call[0][0]) for call in mock_print.call_args_list
        )
        assert "Test error message" in printed_content

    def test_display_error_basic(self):
        """基本的なエラー表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            error_code="BASIC_ERROR",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.UNKNOWN,
            user_message="Basic error test",
            solution=ErrorSolution(
                quick_fix="Basic fix", detailed_steps=["Basic step 1"]
            ),
        )

        # When
        display.display_error(error)

        # Then
        mock_console.warning.assert_called_once_with(error.user_message)

    def test_display_error_levels(self):
        """エラーレベル別の表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)

        error_info = UserFriendlyError(
            error_code="INFO_ERROR",
            level=ErrorLevel.INFO,
            category=ErrorCategory.UNKNOWN,
            user_message="Info message",
            solution=ErrorSolution(
                quick_fix="Info fix", detailed_steps=["Info step 1"]
            ),
        )

        # When
        display.display_error(error_info, show_suggestions=False)

        # Then
        mock_console.info.assert_called_once_with(error_info.user_message)

    def test_format_error_message(self):
        """エラーメッセージフォーマットのテスト"""
        # Given
        display = ErrorDisplay()
        error = UserFriendlyError(
            error_code="FORMAT_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.UNKNOWN,
            user_message="Test error with special characters: <>&\"'",
            solution=ErrorSolution(
                quick_fix="Format fix", detailed_steps=["Format step 1"]
            ),
        )

        # When
        formatted = display.format_error_message(error)

        # Then
        assert "Test error with special characters" in formatted

    @patch("builtins.print")
    def test_display_empty_error(self, mock_print):
        """空のエラー表示テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        error = UserFriendlyError(
            error_code="EMPTY_ERROR",
            level=ErrorLevel.INFO,
            category=ErrorCategory.UNKNOWN,
            user_message="",
            solution=ErrorSolution(
                quick_fix="Empty fix", detailed_steps=["Empty step 1"]
            ),
        )

        # When
        display.display_error(error)

        # Then
        mock_print.assert_called()

    @patch("kumihan_formatter.core.error_handling.error_display.get_logger")
    def test_logging_behavior(self, mock_get_logger):
        """ログ出力動作のテスト"""
        # Given
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        display = ErrorDisplay(enable_logging=True)
        error = UserFriendlyError(
            error_code="LOG_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.UNKNOWN,
            user_message="Test error",
            solution=ErrorSolution(quick_fix="Log fix", detailed_steps=["Log step 1"]),
        )

        # When
        display.display_error(error)

        # Then
        mock_get_logger.assert_called_once()
