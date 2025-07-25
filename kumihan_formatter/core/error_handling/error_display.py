"""Error display and UI integration

Single Responsibility Principle適用: エラー表示機能の分離
Issue #476 Phase5対応 - unified_handler.py分割
"""

from __future__ import annotations

from typing import Any

from ..utilities.logger import get_logger
from .error_types import ErrorLevel, UserFriendlyError


class ErrorDisplay:
    """Error display and UI integration

    Handles:
    - Error message formatting
    - UI integration
    - Display fallback mechanisms
    """

    def __init__(self, console_ui: Any = None, enable_logging: bool = True):
        self.console_ui = console_ui
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__) if enable_logging else None

    def display_error(
        self,
        error: UserFriendlyError,
        show_details: bool = False,
        show_suggestions: bool = True,
        show_context: bool = False,
    ) -> None:
        """エラーを表示

        Args:
            error: 表示するエラー
            show_details: 詳細情報を表示するか
            show_suggestions: 修正提案を表示するか
            show_context: コンテキスト情報を表示するか
        """
        if self.console_ui:
            self._display_with_ui(error, show_details, show_suggestions, show_context)
        else:
            self._display_error_fallback(
                error, show_details, show_suggestions, show_context
            )

    def _display_with_ui(
        self,
        error: UserFriendlyError,
        show_details: bool,
        show_suggestions: bool,
        show_context: bool,
    ) -> None:
        """UI経由でエラーを表示"""
        try:
            self._display_error_message(error)
            self._display_details_if_needed(error, show_details)
            self._display_suggestions_if_needed(error, show_suggestions)
            self._display_context_if_needed(error, show_context)

        except Exception as e:
            if self.logger:
                self.logger.error(f"UI display failed: {str(e)}")
            self._display_error_fallback(
                error, show_details, show_suggestions, show_context
            )

    def _display_error_message(self, error: UserFriendlyError) -> None:
        """エラーレベルに応じたメッセージを表示"""
        if error.level == ErrorLevel.CRITICAL:
            self.console_ui.error(error.user_message)
        elif error.level == ErrorLevel.ERROR:
            self.console_ui.error(error.user_message)
        elif error.level == ErrorLevel.WARNING:
            self.console_ui.warning(error.user_message)
        else:
            self.console_ui.info(error.user_message)

    def _display_details_if_needed(
        self, error: UserFriendlyError, show_details: bool
    ) -> None:
        """詳細情報の表示"""
        if show_details and error.technical_details:
            self.console_ui.info(f"詳細: {error.technical_details}")

    def _display_suggestions_if_needed(
        self, error: UserFriendlyError, show_suggestions: bool
    ) -> None:
        """修正提案の表示"""
        if show_suggestions and error.solution.detailed_steps:
            self.console_ui.info("修正提案:")
            for i, suggestion in enumerate(error.solution.detailed_steps, 1):
                self.console_ui.info(f"  {i}. {suggestion}")

    def _display_context_if_needed(
        self, error: UserFriendlyError, show_context: bool
    ) -> None:
        """コンテキスト情報の表示"""
        if show_context and error.context:
            self.console_ui.info("コンテキスト:")
            for key, value in error.context.items():
                self.console_ui.info(f"  {key}: {value}")

    def _display_error_fallback(
        self,
        error: UserFriendlyError,
        show_details: bool,
        show_suggestions: bool,
        show_context: bool,
    ) -> None:
        """フォールバック表示（標準出力）"""
        self._print_error_message(error)
        self._print_details_if_needed(error, show_details)
        self._print_suggestions_if_needed(error, show_suggestions)
        self._print_context_if_needed(error, show_context)
        self._log_error_if_enabled(error)

    def _print_error_message(self, error: UserFriendlyError) -> None:
        """エラーレベルに応じた標準出力表示"""
        level_prefix = {
            ErrorLevel.CRITICAL: "🚨 CRITICAL",
            ErrorLevel.ERROR: "❌ ERROR",
            ErrorLevel.WARNING: "⚠️  WARNING",
            ErrorLevel.INFO: "ℹ️  INFO",
        }
        level_str = level_prefix.get(error.level, "❓ UNKNOWN")
        print(f"{level_str}: {error.user_message}")

    def _print_details_if_needed(
        self, error: UserFriendlyError, show_details: bool
    ) -> None:
        """詳細情報の標準出力表示"""
        if show_details and error.technical_details:
            print(f"詳細: {error.technical_details}")

    def _print_suggestions_if_needed(
        self, error: UserFriendlyError, show_suggestions: bool
    ) -> None:
        """修正提案の標準出力表示"""
        if show_suggestions and error.solution.detailed_steps:
            print("修正提案:")
            for i, suggestion in enumerate(error.solution.detailed_steps, 1):
                print(f"  {i}. {suggestion}")

    def _print_context_if_needed(
        self, error: UserFriendlyError, show_context: bool
    ) -> None:
        """コンテキスト情報の標準出力表示"""
        if show_context and error.context:
            print("コンテキスト:")
            for key, value in error.context.items():
                print(f"  {key}: {value}")

    def _log_error_if_enabled(self, error: UserFriendlyError) -> None:
        """ログ出力（有効な場合のみ）"""
        if self.logger:
            log_level = {
                ErrorLevel.CRITICAL: "critical",
                ErrorLevel.ERROR: "error",
                ErrorLevel.WARNING: "warning",
                ErrorLevel.INFO: "info",
            }

            logger_method = getattr(self.logger, log_level.get(error.level, "info"))
            logger_method(
                f"Error displayed: {error.user_message}",
                extra={
                    "error_category": (
                        error.category.value
                        if hasattr(error.category, "value")
                        else str(error.category)
                    ),
                    "error_level": (
                        error.level.value
                        if hasattr(error.level, "value")
                        else str(error.level)
                    ),
                    "error_details": error.technical_details,
                    "error_suggestions": error.solution.detailed_steps,
                    "error_context": error.context,
                },
            )

    def format_error_message(
        self, error: UserFriendlyError, include_suggestions: bool = True
    ) -> str:
        """エラーメッセージをフォーマット

        Args:
            error: フォーマットするエラー
            include_suggestions: 修正提案を含めるか

        Returns:
            フォーマットされたエラーメッセージ
        """
        message_parts = [error.user_message]

        if error.technical_details:
            message_parts.append(f"詳細: {error.technical_details}")

        if include_suggestions and error.solution.detailed_steps:
            message_parts.append("修正提案:")
            for i, suggestion in enumerate(error.solution.detailed_steps, 1):
                message_parts.append(f"  {i}. {suggestion}")

        return "\n".join(message_parts)

    def get_display_color(self, error_level: ErrorLevel) -> str:
        """エラーレベルに応じた表示色を取得

        Args:
            error_level: エラーレベル

        Returns:
            色コード（ANSI色コード）
        """
        color_map = {
            ErrorLevel.CRITICAL: "\033[91m",  # 赤
            ErrorLevel.ERROR: "\033[91m",  # 赤
            ErrorLevel.WARNING: "\033[93m",  # 黄
            ErrorLevel.INFO: "\033[94m",  # 青
        }

        return color_map.get(error_level, "\033[0m")  # デフォルト（リセット）

    def format_colored_message(self, error: UserFriendlyError) -> str:
        """色付きエラーメッセージをフォーマット

        Args:
            error: フォーマットするエラー

        Returns:
            色付きメッセージ
        """
        color = self.get_display_color(error.level)
        reset = "\033[0m"

        return f"{color}{error.user_message}{reset}"
