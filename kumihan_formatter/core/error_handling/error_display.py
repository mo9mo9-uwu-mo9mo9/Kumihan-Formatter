"""Error display and UI integration

Single Responsibility Principle適用: エラー表示機能の分離
Issue #476 Phase5対応 - unified_handler.py分割
"""

from __future__ import annotations

from typing import Any

from ..utilities.logger import get_logger
from .error_types import ErrorCategory, ErrorLevel, UserFriendlyError


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
            # エラーレベルに応じたUI表示
            if error.level == ErrorLevel.CRITICAL:
                self.console_ui.error(error.message)
            elif error.level == ErrorLevel.ERROR:
                self.console_ui.error(error.message)
            elif error.level == ErrorLevel.WARNING:
                self.console_ui.warning(error.message)
            else:
                self.console_ui.info(error.message)

            # 詳細情報の表示
            if show_details and error.details:
                self.console_ui.info(f"詳細: {error.details}")

            # 修正提案の表示
            if show_suggestions and error.suggestions:
                self.console_ui.info("修正提案:")
                for i, suggestion in enumerate(error.suggestions, 1):
                    self.console_ui.info(f"  {i}. {suggestion}")

            # コンテキスト情報の表示
            if show_context and error.context:
                self.console_ui.info("コンテキスト:")
                for key, value in error.context.items():
                    self.console_ui.info(f"  {key}: {value}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"UI display failed: {str(e)}")
            self._display_error_fallback(
                error, show_details, show_suggestions, show_context
            )

    def _display_error_fallback(
        self,
        error: UserFriendlyError,
        show_details: bool,
        show_suggestions: bool,
        show_context: bool,
    ) -> None:
        """フォールバック表示（標準出力）"""
        # エラーレベルに応じた表示
        level_prefix = {
            ErrorLevel.CRITICAL: "🚨 CRITICAL",
            ErrorLevel.ERROR: "❌ ERROR",
            ErrorLevel.WARNING: "⚠️  WARNING",
            ErrorLevel.INFO: "ℹ️  INFO",
        }

        level_str = level_prefix.get(error.level, "❓ UNKNOWN")
        print(f"{level_str}: {error.message}")

        # 詳細情報
        if show_details and error.details:
            print(f"詳細: {error.details}")

        # 修正提案
        if show_suggestions and error.suggestions:
            print("修正提案:")
            for i, suggestion in enumerate(error.suggestions, 1):
                print(f"  {i}. {suggestion}")

        # コンテキスト情報
        if show_context and error.context:
            print("コンテキスト:")
            for key, value in error.context.items():
                print(f"  {key}: {value}")

        # ログ出力
        if self.logger:
            log_level = {
                ErrorLevel.CRITICAL: "critical",
                ErrorLevel.ERROR: "error",
                ErrorLevel.WARNING: "warning",
                ErrorLevel.INFO: "info",
            }

            logger_method = getattr(self.logger, log_level.get(error.level, "info"))
            logger_method(
                f"Error displayed: {error.message}",
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
                    "error_details": error.details,
                    "error_suggestions": error.suggestions,
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
        message_parts = [error.message]

        if error.details:
            message_parts.append(f"詳細: {error.details}")

        if include_suggestions and error.suggestions:
            message_parts.append("修正提案:")
            for i, suggestion in enumerate(error.suggestions, 1):
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

        return f"{color}{error.message}{reset}"
