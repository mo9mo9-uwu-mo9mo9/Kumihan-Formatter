"""Core syntax validation logic

This module contains the main validation logic for Kumihan markup syntax,
including block validation, keyword validation, and line-by-line checking.
"""

import re
from pathlib import Path

from ...core.error_handling import ErrorCatalog, UserFriendlyError
from .syntax_errors import ErrorSeverity, ErrorTypes, SyntaxError
from .syntax_rules import SyntaxRules


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

    # Methods delegated to specialized modules - removed to reduce file size
