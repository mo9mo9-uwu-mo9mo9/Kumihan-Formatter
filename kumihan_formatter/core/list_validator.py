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
                        f"行 {i + 1}: リストタイプが混在しています ({current_list_type} → {list_type})"
                    )

                current_list_type = list_type

                # ;;;記法は削除されました（Phase 1）
                # この機能は新記法で置き換えられます
            else:
                current_list_type = None

        return issues

    def _validate_keyword_list_item(self, line: str, line_number: int) -> List[str]:
        """Validate keyword syntax in a list item"""
        # ;;;記法は削除されました（Phase 1）
        # この機能は新記法で置き換えられます
        return []
