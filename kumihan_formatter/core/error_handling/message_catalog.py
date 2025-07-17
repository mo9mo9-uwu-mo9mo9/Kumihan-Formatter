"""
メッセージ カタログ

日本語エラーメッセージ生成・カテゴリ管理機能
Issue #492 Phase 5A - japanese_messages.py分割
"""

from pathlib import Path
from typing import Any, Optional, Union

from .error_message_templates import ErrorMessageTemplates
from .error_types import ErrorCategory, ErrorLevel, ErrorSolution, UserFriendlyError


class MessageCatalog:
    """Japanese error message catalog

    Provides categorized Japanese error messages with detailed
    explanations and solution steps for user-friendly error handling.
    """

    # 後方互換性のためのクラス属性
    FILE_SYSTEM_MESSAGES = ErrorMessageTemplates.FILE_SYSTEM_MESSAGES
    ENCODING_MESSAGES = ErrorMessageTemplates.ENCODING_MESSAGES
    SYNTAX_MESSAGES = ErrorMessageTemplates.SYNTAX_MESSAGES
    RENDERING_MESSAGES = ErrorMessageTemplates.RENDERING_MESSAGES
    SYSTEM_MESSAGES = ErrorMessageTemplates.SYSTEM_MESSAGES

    def __init__(self) -> None:
        """Initialize message catalog with templates"""
        self.templates = ErrorMessageTemplates()

    @classmethod
    def get_file_system_error(
        cls, error_type: str, file_path: Optional[str] = None, **kwargs: Any
    ) -> UserFriendlyError:
        """ファイルシステムエラーのメッセージを生成"""
        if error_type not in ErrorMessageTemplates.FILE_SYSTEM_MESSAGES:
            error_type = "file_not_found"  # デフォルト

        template = ErrorMessageTemplates.FILE_SYSTEM_MESSAGES[error_type]

        # ファイルパスを含むメッセージに調整
        title = str(template["title"])
        if file_path:
            title += f"（ファイル: {Path(file_path).name}）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=str(template["quick_fix"]),
                detailed_steps=list(template["detailed_steps"]),
                alternative_approaches=list(template.get("alternatives", [])),
            ),
            context={"file_path": file_path, **kwargs},
        )

    @classmethod
    def get_encoding_error(
        cls, error_type: str, file_path: Optional[str] = None, **kwargs: Any
    ) -> UserFriendlyError:
        """エンコーディングエラーのメッセージを生成"""
        if error_type not in ErrorMessageTemplates.ENCODING_MESSAGES:
            error_type = "decode_error"  # デフォルト

        template = ErrorMessageTemplates.ENCODING_MESSAGES[error_type]

        title = str(template["title"])
        if file_path:
            title += f"（ファイル: {Path(file_path).name}）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.ENCODING,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=str(template["quick_fix"]),
                detailed_steps=list(template["detailed_steps"]),
                alternative_approaches=list(template.get("alternatives", [])),
            ),
            context={"file_path": file_path, **kwargs},
        )

    @classmethod
    def get_syntax_error(
        cls, error_type: str, line_number: Optional[int] = None, **kwargs: Any
    ) -> UserFriendlyError:
        """構文エラーのメッセージを生成"""
        if error_type not in ErrorMessageTemplates.SYNTAX_MESSAGES:
            error_type = "invalid_marker"  # デフォルト

        template = ErrorMessageTemplates.SYNTAX_MESSAGES[error_type]

        title = str(template["title"])
        if line_number:
            title += f"（{line_number}行目）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.SYNTAX,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=str(template["quick_fix"]),
                detailed_steps=list(template["detailed_steps"]),
                alternative_approaches=list(template.get("alternatives", [])),
            ),
            context={"line_number": line_number, **kwargs},
        )

    @classmethod
    def get_rendering_error(
        cls, error_type: str, template_name: Optional[str] = None, **kwargs: Any
    ) -> UserFriendlyError:
        """レンダリングエラーのメッセージを生成"""
        if error_type not in ErrorMessageTemplates.RENDERING_MESSAGES:
            error_type = "html_generation_failed"  # デフォルト

        template = ErrorMessageTemplates.RENDERING_MESSAGES[error_type]

        title = str(template["title"])
        if template_name:
            title += f"（テンプレート: {template_name}）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.RENDERING,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=str(template["quick_fix"]),
                detailed_steps=list(template["detailed_steps"]),
                alternative_approaches=list(template.get("alternatives", [])),
            ),
            context={"template_name": template_name, **kwargs},
        )

    @classmethod
    def get_system_error(cls, error_type: str, **kwargs: Any) -> UserFriendlyError:
        """システムエラーのメッセージを生成"""
        if error_type not in ErrorMessageTemplates.SYSTEM_MESSAGES:
            error_type = "unexpected_error"  # デフォルト

        template = ErrorMessageTemplates.SYSTEM_MESSAGES[error_type]

        level = (
            ErrorLevel.CRITICAL
            if error_type == "unexpected_error"
            else ErrorLevel.ERROR
        )

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=level,
            category=ErrorCategory.SYSTEM,
            user_message=str(template["title"]),
            solution=ErrorSolution(
                quick_fix=str(template["quick_fix"]),
                detailed_steps=list(template["detailed_steps"]),
                alternative_approaches=list(template.get("alternatives", [])),
            ),
            context=kwargs,
        )


# For backward compatibility
JapaneseMessageCatalog = MessageCatalog
