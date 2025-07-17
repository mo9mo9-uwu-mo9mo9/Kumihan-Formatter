"""
リスト バリデーター

リスト構文・構造の検証機能
Issue #492 Phase 5A - list_parser.py分割
"""

from typing import List

from .list_parser_core import ListParserCore


class ListValidator:
    """Validator for list syntax and structure"""

    def __init__(self, list_parser: ListParserCore):
        self.list_parser = list_parser

    def validate_list_structure(self, lines: List[str]) -> List[str]:
        """
        Validate list structure and return any issues

        Args:
            lines: Lines to validate

        Returns:
            list[str]: List of validation issues
        """
        issues = []
        current_list_type = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if not line_stripped:
                current_list_type = None
                continue

            list_type = self.list_parser.is_list_line(line_stripped)

            if list_type:
                # Check for list type consistency
                if current_list_type and current_list_type != list_type:
                    issues.append(
                        f"行 {i+1}: リストタイプが混在しています ({current_list_type} → {list_type})"
                    )

                current_list_type = list_type

                # Validate keyword syntax in list items
                if list_type == "ul" and ";;;" in line_stripped:
                    keyword_issues = self._validate_keyword_list_item(
                        line_stripped, i + 1
                    )
                    issues.extend(keyword_issues)
            else:
                current_list_type = None

        return issues

    def _validate_keyword_list_item(self, line: str, line_number: int) -> List[str]:
        """Validate keyword syntax in a list item"""
        issues: List[str] = []

        # Extract content after "- " or "・"
        if line.startswith("- "):
            content = line[2:]
        elif line.startswith("・"):
            content = line[1:]
        else:
            return issues

        # Check keyword format
        if content.startswith(";;;"):
            if ";;; " not in content:
                issues.append(f"行 {line_number}: キーワードリスト項目の構文が不正です")
            else:
                # Extract and validate keyword
                parts = content.split(";;; ", 1)
                if len(parts) == 2:
                    keyword_part = parts[0][3:]  # Remove ;;;
                    keywords, _, errors = (
                        self.list_parser.keyword_parser.parse_marker_keywords(
                            keyword_part
                        )
                    )

                    for error in errors:
                        issues.append(f"行 {line_number}: {error}")

                    valid_keywords, validation_errors = (
                        self.list_parser.keyword_parser.validate_keywords(keywords)
                    )
                    for error in validation_errors:
                        issues.append(f"行 {line_number}: {error}")

        return issues
