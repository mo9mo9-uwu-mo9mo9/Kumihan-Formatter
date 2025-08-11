"""Keyword and Block Validation

キーワードとブロック構文の検証機能
"""

# re module removed in Phase 1
from typing import Any

from .syntax_errors import ErrorSeverity, ErrorTypes
from .syntax_rules import SyntaxRules
from .syntax_validator_utils import SyntaxValidatorUtils


class KeywordBlockValidator:
    """Keyword and block validation functionality"""

    @staticmethod
    def validate_block_keywords(errors: list[Any], line_num: int, line: str) -> None:
        """Validate block keyword syntax"""
        keyword_part = line[3:].strip()

        if not keyword_part:
            # Allow empty keywords for simple blocks
            return

        # Parse compound keywords
        keywords = SyntaxRules.parse_keywords(keyword_part)

        # Check each keyword
        for keyword in keywords:
            KeywordBlockValidator._validate_single_keyword(
                errors, line_num, keyword, line
            )

        # Check keyword combination validity
        KeywordBlockValidator._validate_keyword_combination(
            errors, line_num, keywords, line
        )

    @staticmethod
    def _validate_single_keyword(
        errors: list[Any], line_num: int, keyword: str, context: str
    ) -> None:
        """Validate a single keyword for validity"""
        # Check for color attribute
        if SyntaxRules.has_color_attribute(keyword):
            base_keyword = SyntaxRules.extract_base_keyword(keyword)
            color_value = SyntaxRules.extract_color_value(keyword)

            if not SyntaxRules.supports_color(base_keyword):
                SyntaxValidatorUtils.add_error(
                    errors,
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
                SyntaxValidatorUtils.add_error(
                    errors,
                    line_num,
                    1,
                    ErrorSeverity.WARNING,
                    ErrorTypes.INVALID_COLOR_FORMAT,
                    f"色の形式が正しくありません: {color_value}",
                    context,
                    "色は #RRGGBB 形式で指定してください（例: #ff0000）",
                )

        # alt属性は削除されました（Phase 1）

        else:
            # Check base keyword validity
            if not SyntaxRules.is_valid_keyword(keyword):
                SyntaxValidatorUtils.add_error(
                    errors,
                    line_num,
                    1,
                    ErrorSeverity.ERROR,
                    ErrorTypes.UNKNOWN_KEYWORD,
                    f"未知のキーワードです: '{keyword}'",
                    context,
                    f"有効なキーワード: {', '.join(SyntaxRules.get_sorted_keywords())}",
                )

    @staticmethod
    def _validate_keyword_combination(
        errors: list[Any], line_num: int, keywords: list[str], context: str
    ) -> None:
        """Validate if keyword combination is valid"""
        # Check for duplicate keywords
        duplicates = SyntaxRules.find_duplicate_keywords(keywords)
        for duplicate in duplicates:
            SyntaxValidatorUtils.add_error(
                errors,
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
            SyntaxValidatorUtils.add_error(
                errors,
                line_num,
                1,
                ErrorSeverity.ERROR,
                ErrorTypes.MULTIPLE_HEADINGS,
                f"複数の見出しレベルが指定されています: {', '.join(conflicting_headings)}",
                context,
                "見出しレベルは1つだけ指定してください",
            )

    @staticmethod
    def check_multiline_syntax(
        errors: list[Any],
        line_num: int,
        stripped: str,
        block_start_line: int,
        existing_keywords: list[str],
    ) -> None:
        """Check for invalid multi-line syntax patterns"""
        # ;;;記法は削除されました（Phase 1）
        # この機能は新記法で置き換えられます
        pass

    @staticmethod
    def validate_line_syntax(errors: list[Any], line_num: int, line: str) -> None:
        """Validate individual line for syntax issues"""
        # ;;;記法は削除されました（Phase 1）
        # この機能は新記法で置き換えられます
        pass
