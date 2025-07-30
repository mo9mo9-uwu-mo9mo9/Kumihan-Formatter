"""Syntax Validator Utilities

エラー作成とユーティリティ機能を提供するモジュール
"""

from pathlib import Path

from .syntax_validator import ErrorCatalog, UserFriendlyError
from .syntax_errors import ErrorSeverity, ErrorTypes, SyntaxError

# typing.Any removed as unused


class SyntaxValidatorUtils:
    """Syntax validator utility functions"""

    @staticmethod
    def create_friendly_errors(
        errors: list[SyntaxError], current_file: str
    ) -> list[UserFriendlyError]:
        """Convert SyntaxError to UserFriendlyError instances"""
        friendly_errors = []

        for error in errors:
            if error.error_type == ErrorTypes.ENCODING:
                friendly_error = ErrorCatalog.create_encoding_error(current_file)
            elif error.error_type == ErrorTypes.FILE_NOT_FOUND:
                friendly_error = ErrorCatalog.create_file_not_found_error(current_file)
            elif error.error_type in [
                ErrorTypes.INVALID_KEYWORD,
                ErrorTypes.UNKNOWN_KEYWORD,
            ]:
                # Extract invalid content from context
                invalid_content = error.context.replace(";;;", "").strip()
                friendly_error = ErrorCatalog.create_syntax_error(
                    line_num=error.line_number,
                    invalid_content=invalid_content,
                    file_path=current_file,
                )
            else:
                # Other errors as general syntax errors
                friendly_error = ErrorCatalog.create_syntax_error(
                    line_num=error.line_number,
                    invalid_content=error.message,
                    file_path=current_file,
                )

            friendly_errors.append(friendly_error)

        return friendly_errors

    @staticmethod
    def add_error(
        errors: list[SyntaxError],
        line_num: int,
        column: int,
        severity: ErrorSeverity,
        error_type: str,
        message: str,
        context: str,
        suggestion: str = "",
    ) -> None:
        """Add an error to the list"""
        errors.append(
            SyntaxError(
                line_number=line_num,
                column=column,
                severity=severity,
                error_type=error_type,
                message=message,
                context=context,
                suggestion=suggestion,
            )
        )

    @staticmethod
    def validate_file_access(file_path: Path) -> tuple[str, list[SyntaxError]]:
        """Validate file access and return content

        Returns:
            tuple: (content, errors)
        """
        errors: list[SyntaxError] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content, errors
        except UnicodeDecodeError:
            SyntaxValidatorUtils.add_error(
                errors,
                1,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.ENCODING,
                "ファイルのエンコーディングが UTF-8 ではありません",
                str(file_path),
            )
            return "", errors
        except FileNotFoundError:
            SyntaxValidatorUtils.add_error(
                errors,
                1,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.FILE_NOT_FOUND,
                "ファイルが見つかりません",
                str(file_path),
            )
            return "", errors
