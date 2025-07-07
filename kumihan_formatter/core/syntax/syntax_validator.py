"""Core syntax validation logic

This module contains the main validation logic for Kumihan markup syntax,
including block validation, keyword validation, and line-by-line checking.
"""

import re
from pathlib import Path
from typing import List

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

    def _check_multiline_syntax(
        self,
        line_num: int,
        stripped: str,
        block_start_line: int,
        existing_keywords: list[str],
    ) -> None:
        """Check for invalid multi-line syntax patterns"""
        keywords = SyntaxRules.parse_keywords(stripped[3:])

        if keywords:
            # This is a multi-line syntax error
            combined_keywords = existing_keywords + keywords
            suggestion = f";;;{'+'.join(combined_keywords)}"

            self._add_error(
                line_num,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.MULTILINE_SYNTAX,
                f"複数行記法は無効です。行 {block_start_line} からのブロックを1行にまとめてください",
                stripped,
                suggestion,
            )

    def _validate_block_keywords(self, line_num: int, line: str) -> None:
        """Validate block keyword syntax"""
        keyword_part = line[3:].strip()

        if not keyword_part:
            # Allow empty keywords for simple blocks
            return

        # Parse compound keywords
        keywords = SyntaxRules.parse_keywords(keyword_part)

        # Check each keyword
        for keyword in keywords:
            self._validate_single_keyword(line_num, keyword, line)

        # Check keyword combination validity
        self._validate_keyword_combination(line_num, keywords, line)

    def _validate_single_keyword(
        self, line_num: int, keyword: str, context: str
    ) -> None:
        """Validate a single keyword for validity"""
        # Check for color attribute
        if SyntaxRules.has_color_attribute(keyword):
            base_keyword = SyntaxRules.extract_base_keyword(keyword)
            color_value = SyntaxRules.extract_color_value(keyword)

            if not SyntaxRules.supports_color(base_keyword):
                self._add_error(
                    line_num,
                    1,
                    ErrorSeverity.ERROR,
                    ErrorTypes.INVALID_COLOR_USAGE,
                    f"'{base_keyword}' キーワードはcolor属性をサポートしていません",
                    context,
                    f"color属性は {', '.join(SyntaxRules.COLOR_KEYWORDS)} でのみ使用可能です",
                )

            # Check color format
            if not SyntaxRules.validate_color_format(color_value):
                self._add_error(
                    line_num,
                    1,
                    ErrorSeverity.WARNING,
                    ErrorTypes.INVALID_COLOR_FORMAT,
                    f"色の形式が正しくありません: {color_value}",
                    context,
                    "色は #RRGGBB 形式で指定してください（例: #ff0000）",
                )

        # Check for alt attribute
        elif SyntaxRules.has_alt_attribute(keyword):
            base_keyword = SyntaxRules.extract_base_keyword(keyword)

            if not SyntaxRules.supports_alt(base_keyword):
                self._add_error(
                    line_num,
                    1,
                    ErrorSeverity.ERROR,
                    ErrorTypes.INVALID_ALT_USAGE,
                    f"'{base_keyword}' キーワードはalt属性をサポートしていません",
                    context,
                    f"alt属性は {', '.join(SyntaxRules.ALT_KEYWORDS)} でのみ使用可能です",
                )

        else:
            # Check base keyword validity
            if not SyntaxRules.is_valid_keyword(keyword):
                self._add_error(
                    line_num,
                    1,
                    ErrorSeverity.ERROR,
                    ErrorTypes.UNKNOWN_KEYWORD,
                    f"未知のキーワードです: '{keyword}'",
                    context,
                    f"有効なキーワード: {', '.join(SyntaxRules.get_sorted_keywords())}",
                )

    def _validate_keyword_combination(
        self, line_num: int, keywords: list[str], context: str
    ) -> None:
        """Validate if keyword combination is valid"""
        # Check for duplicate keywords
        duplicates = SyntaxRules.find_duplicate_keywords(keywords)
        for duplicate in duplicates:
            self._add_error(
                line_num,
                1,
                ErrorSeverity.WARNING,
                ErrorTypes.DUPLICATE_KEYWORD,
                f"重複するキーワードがあります: '{duplicate}'",
                context,
                "重複するキーワードを削除してください",
            )

        # Check for conflicting heading levels
        conflicting_headings = SyntaxRules.find_conflicting_headings(keywords)
        if conflicting_headings:
            self._add_error(
                line_num,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.MULTIPLE_HEADINGS,
                f"複数の見出しレベルが指定されています: {', '.join(conflicting_headings)}",
                context,
                "見出しレベルは1つだけ指定してください",
            )

    def _validate_line_syntax(self, line_num: int, line: str) -> None:
        """Validate individual line for syntax issues"""
        # Check for invalid ;;; usage (but allow list item syntax: - ;;;keyword;;; text)
        if ";;;" in line and not line.strip().startswith(";;;"):
            # Check if it's a valid list item syntax
            stripped = line.strip()
            is_list_item = (
                stripped.startswith("- ;;;") and stripped.count(";;;") >= 2
            ) or (re.match(r"^\d+\.\s+;;;", stripped) and stripped.count(";;;") >= 2)
            if not is_list_item:
                self._add_error(
                    line_num,
                    line.find(";;;") + 1,
                    ErrorSeverity.WARNING,
                    ErrorTypes.INLINE_MARKER,
                    ";;; は行頭でのみ有効です（リスト内記法以外）",
                    line,
                    ";;; は行の先頭に配置するか、リスト内記法 '- ;;;キーワード;;; テキスト' を使用してください",
                )

        # Check for empty block markers with spaces
        stripped = line.strip()
        if re.match(r"^;;;[\s]+$", stripped):
            self._add_error(
                line_num,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.INVALID_BLOCK_MARKER,
                "空白文字が含まれた無効なブロックマーカーです",
                line,
                "単純に ;;; のみ記述してください",
            )

    def _add_error(
        self,
        line_num: int,
        column: int,
        severity: ErrorSeverity,
        error_type: str,
        message: str,
        context: str,
        suggestion: str = "",
    ) -> None:
        """Add an error to the list"""
        self.errors.append(
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
