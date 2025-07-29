"""Core syntax validation logic

This module contains the main validation logic for Kumihan markup syntax,
including block validation, keyword validation, and line-by-line checking.
"""

from pathlib import Path

from .syntax_errors import ErrorSeverity, ErrorTypes, SyntaxError
from .syntax_rules import SyntaxRules


class UserFriendlyError:
    """Simple error class for user-friendly error messages"""

    def __init__(self, message: str, details: str = "", severity: str = "error"):
        self.message = message
        self.details = details
        self.severity = severity


class ErrorCatalog:
    """Simple error catalog for creating user-friendly errors"""

    @staticmethod
    def create_encoding_error(file_path: str) -> UserFriendlyError:
        return UserFriendlyError(
            f"エラー: {file_path} のエンコーディングが UTF-8 ではありません",
            "ファイルを UTF-8 エンコーディングで保存し直してください。",
            "error",
        )

    @staticmethod
    def create_file_not_found_error(file_path: str) -> UserFriendlyError:
        return UserFriendlyError(
            f"エラー: ファイル {file_path} が見つかりません",
            "ファイルパスを確認してください。",
            "error",
        )

    @staticmethod
    def create_syntax_error(
        line_num: int, invalid_content: str, file_path: str
    ) -> UserFriendlyError:
        return UserFriendlyError(
            f"構文エラー: {file_path} の {line_num} 行目",
            f"無効な内容: {invalid_content}",
            "error",
        )


class KumihanSyntaxValidator:
    """Core Kumihan markup syntax validator"""

    def __init__(self) -> None:
        self.errors: list[SyntaxError] = []
        self.current_file = ""

    def get_friendly_errors(self) -> list[UserFriendlyError]:
        """Convert SyntaxError to UserFriendlyError instances"""
        friendly_errors = []

        for error in self.errors:
            if error.error_type == ErrorTypes.ENCODING:
                friendly_error = ErrorCatalog.create_encoding_error(self.current_file)
            elif error.error_type == ErrorTypes.FILE_NOT_FOUND:
                friendly_error = ErrorCatalog.create_file_not_found_error(
                    self.current_file
                )
            elif error.error_type in [
                ErrorTypes.INVALID_KEYWORD,
                ErrorTypes.UNKNOWN_KEYWORD,
            ]:
                # Extract invalid content from context
                invalid_content = error.context.replace(";;;", "").strip()
                friendly_error = ErrorCatalog.create_syntax_error(
                    line_num=error.line_number,
                    invalid_content=invalid_content,
                    file_path=self.current_file,
                )
            else:
                # Other errors as general syntax errors
                friendly_error = ErrorCatalog.create_syntax_error(
                    line_num=error.line_number,
                    invalid_content=error.message,
                    file_path=self.current_file,
                )

            friendly_errors.append(friendly_error)

        return friendly_errors

    def validate_file(self, file_path: Path) -> list[SyntaxError]:
        """Validate a single file for syntax errors"""
        self.errors.clear()
        self.current_file = str(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            self._add_error(
                1,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.ENCODING,
                "ファイルのエンコーディングが UTF-8 ではありません",
                str(file_path),
            )
            return self.errors
        except FileNotFoundError:
            self._add_error(
                1,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.FILE_NOT_FOUND,
                "ファイルが見つかりません",
                str(file_path),
            )
            return self.errors

        lines = content.splitlines()
        self._validate_syntax(lines)

        return self.errors

    def _validate_syntax(self, lines: list[str]) -> None:
        """Validate syntax for all lines"""
        in_block = False
        block_start_line = 0
        block_keywords = []  # type: ignore

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for block markers
            if stripped.startswith(";;;"):
                if stripped == ";;;":
                    # Standalone ;;; marker
                    if not in_block:
                        # Standalone ;;; without being in a block is always an error
                        self._add_error(
                            line_num,
                            1,
                            ErrorSeverity.ERROR,
                            ErrorTypes.UNMATCHED_BLOCK_END,
                            "ブロック開始マーカーなしに ;;; が見つかりました",
                            line,
                        )
                    else:
                        # End of block
                        in_block = False
                        block_keywords.clear()
                else:
                    # Block start marker or keyword line
                    if in_block:
                        # If we're in an empty block, this is a new block (not multi-line syntax)
                        if not block_keywords:
                            # End the empty block and start a new one
                            in_block = True
                            block_start_line = line_num
                            block_keywords = SyntaxRules.parse_keywords(stripped[3:])
                            self._validate_block_keywords(line_num, stripped)
                        else:
                            # Check for multi-line syntax error
                            self._check_multiline_syntax(
                                line_num, stripped, block_start_line, block_keywords
                            )
                    else:
                        # Start of new block
                        in_block = True
                        block_start_line = line_num
                        block_keywords = SyntaxRules.parse_keywords(stripped[3:])
                        self._validate_block_keywords(line_num, stripped)

            # Check for other syntax issues
            self._validate_line_syntax(line_num, line)

        # Check for unclosed blocks
        if in_block:
            self._add_error(
                block_start_line,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.UNCLOSED_BLOCK,
                "ブロックが ;;; で閉じられていません",
                lines[block_start_line - 1] if block_start_line <= len(lines) else "",
                "ブロックの最後に ;;; を追加してください",
            )

    def _validate_block_keywords(self, line_num: int, line: str) -> None:
        """ブロックキーワードの妥当性をチェック"""
        # 基本的な妥当性チェック（簡易実装）
        keywords_part = line[3:].strip()  # ;;; を除いた部分
        if not keywords_part:
            self._add_error(
                line_num,
                1,
                ErrorSeverity.WARNING,
                ErrorTypes.INVALID_KEYWORD,
                "空のキーワードブロックです",
                line,
            )

    def _check_multiline_syntax(
        self, line_num: int, line: str, block_start_line: int, block_keywords: list[str]
    ) -> None:
        """マルチライン構文エラーをチェック"""
        self._add_error(
            line_num,
            1,
            ErrorSeverity.ERROR,
            ErrorTypes.INVALID_SYNTAX,
            "ブロック内で新しいブロックが開始されています",
            line,
            f"ブロックは{block_start_line}行目で開始されていますが、まだ閉じられていません",
        )

    def _add_error(
        self,
        line_number: int,
        column: int,
        severity: ErrorSeverity,
        error_type: ErrorTypes | str,
        message: str,
        context: str,
        suggestion: str = "",
    ) -> None:
        """エラーをエラーリストに追加"""
        error = SyntaxError(
            line_number=line_number,
            column=column,
            severity=severity,
            error_type=getattr(error_type, "value", str(error_type)),
            message=message,
            context=context,
            suggestion=suggestion,
        )
        self.errors.append(error)

    def _validate_line_syntax(self, line_num: int, line: str) -> None:
        """行単位の構文チェック"""
        # 基本的な構文チェック（簡易実装）
        stripped = line.strip()

        # 無効な文字パターンをチェック
        if "(((" in stripped or ")))" in stripped:
            self._add_error(
                line_num,
                1,
                ErrorSeverity.WARNING,
                ErrorTypes.INVALID_SYNTAX,
                "無効な括弧パターンが検出されました",
                line,
                "脚注記法は (()) を使用してください",
            )
