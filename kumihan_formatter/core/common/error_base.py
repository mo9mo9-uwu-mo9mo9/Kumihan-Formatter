"""Unified Error System - 統合エラーシステム

Issue #1207対応: error_types.pyとerror_base.pyを統合
過度なファイル分割を解消し、エラーシステムの一元化を実現

統合内容:
- ErrorSeverity, ErrorCategory, ErrorContext (旧error_types.py)
- KumihanError基底クラスと具体的エラー型
- GracefulSyntaxError拡張クラス
"""

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# Error Types - 旧error_types.pyから統合
class ErrorSeverity(Enum):
    """Standardized error severity levels"""

    CRITICAL = "critical"  # System-breaking errors
    ERROR = "error"  # Component failures
    WARNING = "warning"  # Potentially problematic situations
    INFO = "info"  # Informational messages


class ErrorCategory(Enum):
    """Error categorization for better organization"""

    FILE_SYSTEM = "file_system"  # File operations
    SYNTAX = "syntax"  # Markup syntax issues
    VALIDATION = "validation"  # Data validation
    RENDERING = "rendering"  # HTML generation
    CONFIGURATION = "configuration"  # Config issues
    PERFORMANCE = "performance"  # Performance problems
    NETWORK = "network"  # Network operations
    PERMISSION = "permission"  # Access control
    ENCODING = "encoding"  # Text encoding
    SYSTEM = "system"  # OS/environment
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class ErrorContext:
    """Context information for errors"""

    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    operation: str | None = None
    user_input: str | None = None
    system_info: dict[str, Any] | None = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "operation": self.operation,
            "user_input": self.user_input,
            "system_info": self.system_info,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """String representation of context"""
        parts = []
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.line_number:
            parts.append(f"Line: {self.line_number}")
        if self.column_number:
            parts.append(f"Column: {self.column_number}")
        if self.operation:
            parts.append(f"Operation: {self.operation}")

        return " | ".join(parts) if parts else "No context"


class KumihanError(Exception):
    """Base exception class for all Kumihan-Formatter errors"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: ErrorContext | None = None,
        suggestions: list[str] | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize Kumihan error

        Args:
            message: Error message
            severity: Error severity level
            category: Error category
            context: Error context information
            suggestions: User-friendly suggestions
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext()
        self.suggestions = suggestions or []
        self.original_error = original_error
        self._info = traceback.format_exc() if original_error else None

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary representation"""
        return {
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context.to_dict(),
            "suggestions": self.suggestions,
            "original_error": str(self.original_error) if self.original_error else None,
            "": self._info,
        }

    def __str__(self) -> str:
        """String representation of error"""
        parts = [f"[{self.severity.value.upper()}] {self.message}"]

        if self.context and str(self.context) != "No context":
            parts.append(f"Context: {self.context}")

        if self.suggestions:
            parts.append(f"Suggestions: {'; '.join(self.suggestions)}")

        return "\n".join(parts)

    def get_user_message(self) -> str:
        """Get user-friendly error message"""
        user_msg = self.message

        if self.suggestions:
            user_msg += "\n\nSuggestions:\n"
            for i, suggestion in enumerate(self.suggestions, 1):
                user_msg += f"{i}. {suggestion}\n"

        return user_msg

    def is_critical(self) -> bool:
        """Check if error is critical"""
        return self.severity == ErrorSeverity.CRITICAL

    def is_recoverable(self) -> bool:
        """Check if error is recoverable"""
        return self.severity in [ErrorSeverity.WARNING, ErrorSeverity.INFO]

    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to the error"""
        self.suggestions.append(suggestion)

    def with_context(self, **context_updates: Any) -> "KumihanError":
        """Create a new error with updated context"""
        new_context = ErrorContext(
            file_path=context_updates.get("file_path", self.context.file_path),
            line_number=context_updates.get("line_number", self.context.line_number),
            column_number=context_updates.get(
                "column_number", self.context.column_number
            ),
            operation=context_updates.get("operation", self.context.operation),
            user_input=context_updates.get("user_input", self.context.user_input),
            system_info=context_updates.get("system_info", self.context.system_info),
        )

        return KumihanError(
            message=self.message,
            severity=self.severity,
            category=self.category,
            context=new_context,
            suggestions=self.suggestions.copy(),
            original_error=self.original_error,
        )


# Specific error types
class FileSystemError(KumihanError):
    """File system operation errors"""

    def __init__(
        self, message: str, file_path: str | None = None, **kwargs: Any
    ) -> None:
        context = ErrorContext(file_path=file_path, operation="file_system")
        super().__init__(
            message, category=ErrorCategory.FILE_SYSTEM, context=context, **kwargs
        )


class SyntaxError(KumihanError):
    """Syntax parsing errors"""

    def __init__(
        self, message: str, line_number: int | None = None, **kwargs: Any
    ) -> None:
        context = ErrorContext(line_number=line_number, operation="syntax_parsing")
        super().__init__(
            message, category=ErrorCategory.SYNTAX, context=context, **kwargs
        )


@dataclass
class GracefulSyntaxError:
    """
    Issue #700対応: graceful error handling用の拡張SyntaxErrorデータクラス

    Phase 1: 基本的なエラー継続処理
    - エラー詳細情報の保持
    - HTML埋め込み用の詳細データ
    - 修正提案情報
    """

    line_number: int
    column: int
    error_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    context: str  # エラー発生箇所の前後コンテキスト
    suggestion: str = ""  # 修正提案
    file_path: str = ""

    # 高度なエラー表示機能
    highlight_start: int = 0  # ハイライト開始位置
    highlight_end: int = 0  # ハイライト終了位置
    correction_suggestions: list[str] | None = None  # 具体的な修正提案リスト
    error_pattern: str = ""  # エラーパターン識別子（統計用）

    def __post_init__(self) -> None:
        if self.correction_suggestions is None:
            self.correction_suggestions = []

    # Phase 1: HTML表示用プロパティ
    @property
    def html_class(self) -> str:
        """エラー表示用のCSSクラス名を返す"""
        return f"kumihan-error-{self.severity}"

    @property
    def display_title(self) -> str:
        """エラー表示用のタイトルを返す"""
        return f"記法エラー (行 {self.line_number})"

    @property
    def html_content(self) -> str:
        """HTML埋め込み用のエラー内容を返す"""
        # HTMLエスケープ処理（セキュリティ対策）
        import html

        safe_message = html.escape(self.message)
        content = f"<strong>{safe_message}</strong>"

        if self.context:
            safe_context = html.escape(self.context)
            content += f"<br><code>{safe_context}</code>"

        if self.suggestion:
            safe_suggestion = html.escape(self.suggestion)
            content += f"<br><em>提案: {safe_suggestion}</em>"

        return content

    def to_dict(self) -> dict[str, Any]:
        """辞書形式でエラー情報を返す"""
        return {
            "line_number": self.line_number,
            "column": self.column,
            "error_type": self.error_type,
            "severity": self.severity,
            "message": self.message,
            "context": self.context,
            "suggestion": self.suggestion,
            "file_path": self.file_path,
            "html_class": self.html_class,
            "display_title": self.display_title,
            # 拡張フィールド
            "highlight_start": self.highlight_start,
            "highlight_end": self.highlight_end,
            "correction_suggestions": self.correction_suggestions,
            "error_pattern": self.error_pattern,
            "html_content": self.html_content,
        }

    # 高度なエラー表示機能メソッド
    def get_highlighted_context(self) -> str:
        """ハイライト付きコンテキストを返す"""
        if not self.context or self.highlight_start == self.highlight_end:
            return self.context or ""
        # ハイライト処理を実装
        return self.context or ""

    def get_correction_suggestions_html(self) -> str:
        """修正提案のHTML形式を返す"""
        if not self.correction_suggestions:
            return ""
        # HTML形式で修正提案を返す
        return (
            "<ul>"
            + "".join(
                [f"<li>{suggestion}</li>" for suggestion in self.correction_suggestions]
            )
            + "</ul>"
        )

    def add_correction_suggestion(self, suggestion: str) -> None:
        """修正提案を追加"""
        if self.correction_suggestions is None:
            self.correction_suggestions = []
        if suggestion not in self.correction_suggestions:
            self.correction_suggestions.append(suggestion)

    def set_highlight_range(self, start: int, end: int) -> None:
        """ハイライト範囲を設定"""
        self.highlight_start = max(0, start)
        self.highlight_end = max(self.highlight_start, end)

    def classify_error_pattern(self) -> str:
        """エラーパターンを分類して統計用IDを返す"""
        if self.error_pattern:
            return self.error_pattern
        return "unknown"


class ValidationError(KumihanError):
    """Data validation errors"""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)


class ConfigurationError(KumihanError):
    """Configuration errors"""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)
