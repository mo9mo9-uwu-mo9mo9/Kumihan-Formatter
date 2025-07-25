"""
エラー表示機能のテスト

Important Tier Phase 2-1対応 - Issue #593
エラー表示・UI統合機能の体系的テスト実装
"""

from io import StringIO
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_display import ErrorDisplay
from kumihan_formatter.core.error_handling.error_types import (
    ErrorLevel,
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
        assert display.logger is not None

    def test_init_with_console_ui(self):
        """コンソールUI付き初期化テスト"""
        # Given
        mock_console = Mock()

        # When
        display = ErrorDisplay(console_ui=mock_console)

        # Then
        assert display.console_ui is mock_console

    def test_init_without_logging(self):
        """ログ無効での初期化テスト"""
        # When
        display = ErrorDisplay(enable_logging=False)

        # Then
        assert display.enable_logging is False
        assert display.logger is None

    def test_display_error_with_ui(self):
        """UI経由でのエラー表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            message="Test error message",
            original_error=ValueError("Original error"),
            level=ErrorLevel.ERROR,
        )

        # When
        display.display_error(error)

        # Then
        mock_console.show_error.assert_called_once_with(error)

    @patch("builtins.print")
    def test_display_error_fallback(self, mock_print):
        """フォールバック表示テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        error = UserFriendlyError(
            message="Test error message",
            original_error=ValueError("Original error"),
            level=ErrorLevel.ERROR,
        )

        # When
        display.display_error(error)

        # Then
        # フォールバック表示が呼ばれる
        mock_print.assert_called()
        printed_content = " ".join(
            str(call[0][0]) for call in mock_print.call_args_list
        )
        assert "エラー" in printed_content
        assert "Test error message" in printed_content

    def test_display_error_with_suggestions(self):
        """修正提案付きエラー表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            message="Encoding error",
            original_error=UnicodeDecodeError("utf-8", b"", 0, 1, "error"),
            suggestions=["Try shift_jis encoding", "Check file encoding"],
        )

        # When
        display.display_error(error, show_suggestions=True)

        # Then
        mock_console.show_error.assert_called_once()
        # UI側で提案が表示されることを期待

    @patch("builtins.print")
    def test_display_error_fallback_with_suggestions(self, mock_print):
        """フォールバック表示での修正提案テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        error = UserFriendlyError(
            message="Syntax error",
            original_error=ValueError("Invalid syntax"),
            suggestions=["Add closing bracket", "Check indentation"],
        )

        # When
        display.display_error(error, show_suggestions=True)

        # Then
        printed_content = " ".join(
            str(call[0][0]) for call in mock_print.call_args_list
        )
        assert "修正提案" in printed_content
        assert "Add closing bracket" in printed_content
        assert "Check indentation" in printed_content

    def test_display_error_with_context(self):
        """コンテキスト情報付きエラー表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            message="Parse error",
            original_error=ValueError("Invalid markdown"),
            context={
                "file_path": "test.md",
                "line_number": 10,
                "column": 5,
            },
        )

        # When
        display.display_error(error, show_context=True)

        # Then
        mock_console.show_error.assert_called_once()

    @patch("builtins.print")
    def test_display_error_fallback_with_context(self, mock_print):
        """フォールバック表示でのコンテキスト情報テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        error = UserFriendlyError(
            message="File error",
            original_error=FileNotFoundError("Not found"),
            context={
                "file_path": "/path/to/file.txt",
                "operation": "read",
                "cwd": "/home/user",
            },
        )

        # When
        display.display_error(error, show_context=True)

        # Then
        printed_content = " ".join(
            str(call[0][0]) for call in mock_print.call_args_list
        )
        assert "コンテキスト" in printed_content
        assert "file_path" in printed_content
        assert "/path/to/file.txt" in printed_content

    def test_display_error_with_details(self):
        """詳細情報付きエラー表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            message="Complex error",
            original_error=RuntimeError("Runtime issue"),
            level=ErrorLevel.CRITICAL,
        )

        # When
        display.display_error(error, show_details=True)

        # Then
        mock_console.show_error.assert_called_once()

    @patch("builtins.print")
    def test_display_error_fallback_with_details(self, mock_print):
        """フォールバック表示での詳細情報テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        original_error = ValueError("Detailed error information")
        error = UserFriendlyError(
            message="High level error",
            original_error=original_error,
        )

        # When
        display.display_error(error, show_details=True)

        # Then
        printed_content = " ".join(
            str(call[0][0]) for call in mock_print.call_args_list
        )
        assert "詳細" in printed_content
        assert "ValueError" in printed_content
        assert "Detailed error information" in printed_content

    def test_display_different_error_levels(self):
        """異なるエラーレベルの表示テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)

        error_levels = [
            (ErrorLevel.WARNING, "警告"),
            (ErrorLevel.ERROR, "エラー"),
            (ErrorLevel.CRITICAL, "重大"),
        ]

        for level, expected_text in error_levels:
            with patch("builtins.print") as mock_print:
                error = UserFriendlyError(
                    message=f"{level.name} level error",
                    original_error=ValueError("Test"),
                    level=level,
                )

                # When
                display.display_error(error)

                # Then
                printed_content = " ".join(
                    str(call[0][0]) for call in mock_print.call_args_list
                )
                assert expected_text in printed_content

    def test_show_error_alias(self):
        """show_errorエイリアスメソッドのテスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            message="Test error",
            original_error=ValueError("Original"),
        )

        # When
        display.show_error(error)

        # Then
        mock_console.show_error.assert_called_once_with(error)

    def test_format_error_message(self):
        """エラーメッセージフォーマットのテスト"""
        # Given
        display = ErrorDisplay()
        error = UserFriendlyError(
            message="Test error with special characters: <>&\"'",
            original_error=ValueError("Original"),
        )

        # When
        formatted = display._format_error_message(error)

        # Then
        assert "Test error with special characters" in formatted
        assert error.level.to_japanese() in formatted

    def test_display_multiple_suggestions(self):
        """複数の修正提案表示テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        error = UserFriendlyError(
            message="Multiple issues found",
            original_error=ValueError("Complex error"),
            suggestions=[
                "First suggestion",
                "Second suggestion",
                "Third suggestion with a very long text that might wrap",
            ],
        )

        with patch("builtins.print") as mock_print:
            # When
            display.display_error(error, show_suggestions=True)

            # Then
            printed_content = " ".join(
                str(call[0][0]) for call in mock_print.call_args_list
            )
            assert "First suggestion" in printed_content
            assert "Second suggestion" in printed_content
            assert "Third suggestion" in printed_content

    def test_display_empty_error(self):
        """空のエラー表示テスト"""
        # Given
        display = ErrorDisplay(console_ui=None)
        error = UserFriendlyError(
            message="",
            original_error=ValueError(""),
        )

        with patch("builtins.print") as mock_print:
            # When
            display.display_error(error)

            # Then
            # 空でもエラーレベルは表示される
            mock_print.assert_called()

    def test_display_with_all_options(self):
        """全オプション有効での表示テスト"""
        # Given
        mock_console = Mock()
        display = ErrorDisplay(console_ui=mock_console)
        error = UserFriendlyError(
            message="Complete error",
            original_error=RuntimeError("Runtime error"),
            suggestions=["Fix 1", "Fix 2"],
            context={"key": "value"},
            level=ErrorLevel.ERROR,
        )

        # When
        display.display_error(
            error,
            show_details=True,
            show_suggestions=True,
            show_context=True,
        )

        # Then
        mock_console.show_error.assert_called_once_with(error)

    @patch("kumihan_formatter.core.error_handling.error_display.get_logger")
    def test_logging_behavior(self, mock_get_logger):
        """ログ出力動作のテスト"""
        # Given
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        display = ErrorDisplay(enable_logging=True)
        error = UserFriendlyError(
            message="Test error",
            original_error=ValueError("Original"),
        )

        # When
        display.display_error(error)

        # Then
        mock_get_logger.assert_called_once()
