"""統一ログフォーマッター

Issue #770対応: ログフォーマット・レベルの統一化
一貫性のあるログ出力とエラー表示を提供
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from ..common.error_base import KumihanError
from ..common.error_types import ErrorSeverity


@dataclass
class ErrorHandleResult:
    """エラー処理結果（unified_handlerと共通利用）"""

    should_continue: bool
    user_message: str
    logged: bool
    graceful_handled: bool
    original_error: Exception
    kumihan_error: KumihanError


class UnifiedLogFormatter(logging.Formatter):
    """統一ログフォーマッター

    全モジュール共通のログフォーマットを提供:
    - [LEVEL] [COMPONENT] MESSAGE
    - Context: file:line
    - Suggestions: 1. xxx 2. yyy
    - Timestamp: ISO format
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        component_name: str = "KUMIHAN",
    ):
        """初期化

        Args:
            fmt: フォーマット文字列（None時はデフォルト使用）
            datefmt: 日付フォーマット（None時はISO使用）
            component_name: コンポーネント名
        """
        # デフォルトフォーマット
        if fmt is None:
            fmt = "[%(levelname)s] [%(component)s] %(message)s"

        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt, datefmt)
        self.component_name = component_name.upper()

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをフォーマット

        Args:
            record: ログレコード

        Returns:
            str: フォーマット済みログメッセージ
        """
        # コンポーネント名を設定
        if not hasattr(record, "component"):
            record.component = self.component_name

        # KumihanError の場合は専用フォーマット
        if hasattr(record, "kumihan_error"):
            return self._format_kumihan_error(record, record.kumihan_error)

        # 標準フォーマットを使用
        return super().format(record)

    def _format_kumihan_error(
        self, record: logging.LogRecord, error: KumihanError
    ) -> str:
        """KumihanError専用フォーマット

        Args:
            record: ログレコード
            error: KumihanError

        Returns:
            str: フォーマット済みメッセージ
        """
        # 基本メッセージ
        parts = [
            f"[{record.levelname}]",
            f"[{getattr(record, 'component', self.component_name)}]",
            error.message,
        ]

        # コンテキスト情報
        if error.context and str(error.context) != "No context":
            context_info = []
            if error.context.file_path:
                context_info.append(str(error.context.file_path))
            if error.context.line_number:
                context_info.append(f"line {error.context.line_number}")
            if context_info:
                parts.append(f"Context: {':'.join(context_info)}")

        # 操作情報
        if error.context and error.context.operation:
            parts.append(f"Operation: {error.context.operation}")

        # 提案（最初の2つのみ）
        if error.suggestions:
            suggestions_str = "; ".join(error.suggestions[:2])
            parts.append(f"Suggestions: {suggestions_str}")

        return " | ".join(parts)


class ComponentLoggerFactory:
    """コンポーネント別ロガーファクトリ

    各コンポーネント用に統一フォーマッターを適用したロガーを生成
    """

    _formatters: Dict[str, UnifiedLogFormatter] = {}
    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(
        cls, name: str, component_name: Optional[str] = None, level: int = logging.INFO
    ) -> logging.Logger:
        """コンポーネント別ロガー取得

        Args:
            name: ロガー名（通常は__name__）
            component_name: コンポーネント名（None時はnameから推定）
            level: ログレベル

        Returns:
            logging.Logger: 設定済みロガー
        """
        if name in cls._loggers:
            return cls._loggers[name]

        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Determine component name
        if component_name is None:
            component_name = cls._extract_component_name(name)

        # Set formatter
        formatter = cls._get_formatter(component_name)

        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Cache and return
        cls._loggers[name] = logger
        return logger

    @classmethod
    def _extract_component_name(cls, name: str) -> str:
        """モジュール名からコンポーネント名を抽出

        Args:
            name: モジュール名

        Returns:
            str: コンポーネント名
        """
        # kumihan_formatter.core.parser.xxx → PARSER
        parts = name.split(".")

        if len(parts) >= 3 and parts[1] == "core":
            component = parts[2]
        elif len(parts) >= 2:
            component = parts[1]
        else:
            component = parts[0] if parts else "UNKNOWN"

        # 特殊ケース対応
        component_mapping = {
            "parsing": "PARSER",
            "rendering": "RENDERER",
            "parser": "PARSER",
            "renderer": "RENDERER",
            "keyword_parsing": "PARSER",
            "block_parser": "PARSER",
            "utilities": "UTILS",
            "error_handling": "ERROR",
            "commands": "CLI",
            "convert": "CONVERT",
            "lint": "LINT",
        }

        return component_mapping.get(component.lower(), component.upper())

    @classmethod
    def _get_formatter(cls, component_name: str) -> UnifiedLogFormatter:
        """コンポーネント用フォーマッター取得

        Args:
            component_name: コンポーネント名

        Returns:
            UnifiedLogFormatter: フォーマッター
        """
        if component_name not in cls._formatters:
            cls._formatters[component_name] = UnifiedLogFormatter(
                component_name=component_name
            )
        return cls._formatters[component_name]


class ErrorMessageBuilder:
    """エラーメッセージビルダー

    ユーザー向けエラーメッセージの標準化
    """

    @staticmethod
    def build_user_message(
        error: KumihanError,
        show_suggestions: bool = True,
        show_context: bool = True,
        max_suggestions: int = 3,
    ) -> str:
        """ユーザー向けメッセージ構築

        Args:
            error: KumihanError
            show_suggestions: 提案表示有無
            show_context: コンテキスト表示有無
            max_suggestions: 最大提案数

        Returns:
            str: ユーザー向けメッセージ
        """
        parts = []

        # メインメッセージ
        severity_icon = {
            ErrorSeverity.CRITICAL: "🔴",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.INFO: "ℹ️",
        }.get(error.severity, "")

        parts.append(f"{severity_icon} {error.message}")

        # コンテキスト情報
        if show_context and error.context:
            context_parts = []
            if error.context.file_path:
                context_parts.append(f"ファイル: {error.context.file_path}")
            if error.context.line_number:
                context_parts.append(f"行: {error.context.line_number}")
            if context_parts:
                parts.append(f"場所: {', '.join(context_parts)}")

        # 提案
        if show_suggestions and error.suggestions:
            parts.append("💡 解決方法:")
            for i, suggestion in enumerate(error.suggestions[:max_suggestions], 1):
                parts.append(f"  {i}. {suggestion}")

        return "\n".join(parts)

    @staticmethod
    def build_console_message(error: KumihanError, colored: bool = True) -> str:
        """コンソール表示用メッセージ構築

        Args:
            error: KumihanError
            colored: 色付け有無

        Returns:
            str: コンソール用メッセージ
        """
        if not colored:
            return ErrorMessageBuilder.build_user_message(error)

        colors = {
            "error": "\033[31m",
            "warning": "\033[33m",
            "info": "\033[34m",
            "critical": "\033[35m",
        }
        reset = "\033[0m"

        # ErrorSeverityがEnumの場合、valueを使用
        severity_value = (
            error.severity.value
            if hasattr(error.severity, "value")
            else str(error.severity)
        )
        color = colors.get(severity_value, "")

        # 色付きメッセージ
        message = f"{color}{error.message}{reset}"

        # コンテキスト（グレー）
        if error.context and str(error.context) != "No context":
            message += f"\n\033[90m{error.context}{reset}"

        # 提案（緑）
        if error.suggestions:
            message += f"\n\033[92m💡 解決方法:{reset}"
            for i, suggestion in enumerate(error.suggestions[:2], 1):
                message += f"\n\033[92m  {i}. {suggestion}{reset}"

        return message


def get_component_logger(
    name: str, component_name: Optional[str] = None
) -> logging.Logger:
    """コンポーネント用ロガー取得（便利関数）

    Args:
        name: ロガー名
        component_name: コンポーネント名

    Returns:
        logging.Logger: 設定済みロガー
    """
    return ComponentLoggerFactory.get_logger(name, component_name)


def log_kumihan_error(
    logger: logging.Logger, error: KumihanError, level: Optional[int] = None
) -> None:
    """KumihanError専用ログ出力

    Args:
        logger: ロガー
        error: KumihanError
        level: ログレベル（None時はerror.severityに基づく）
    """
    if level is None:
        level_mapping = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.INFO: logging.INFO,
        }
        level = level_mapping.get(error.severity, logging.ERROR)

    # KumihanError情報を追加してログ出力
    logger.log(level, error.message, extra={"kumihan_error": error})
