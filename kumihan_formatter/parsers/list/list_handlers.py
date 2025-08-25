"""List Parser Handlers - リスト処理ハンドラ

分離された責任:
- リスト処理・解析ロジック
- 各種リスト形式のハンドラ
- ネスト構造の処理
"""

from typing import Any, Dict, List, Optional
import re
from ...core.utilities.logger import get_logger
from .list_utils import (
    detect_list_type,
    get_list_nesting_level,
    extract_list_content,
    is_kumihan_list_block,
    detect_full_list_type,
    extract_list_block,
    is_compatible_list_type,
    has_nested_structure,
    validate_regular_lists,
    validate_kumihan_list_block,
    validate_checklist_format,
    validate_definition_format,
)
from .list_item_handlers import ListItemHandler


class ListHandler:
    """リスト処理ハンドラクラス"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def parse_kumihan_list_block(self, content: str) -> Dict[str, Any]:
        """Kumihanリストブロックの解析"""
        kumihan_pattern = re.compile(r"^# リスト #(.*)##$", re.MULTILINE)
        matches = kumihan_pattern.findall(content)

        parsed_blocks = []
        for match in matches:
            list_content = match.strip()
            if list_content:
                block_result = self.parse_regular_lists(list_content)
                parsed_blocks.append(
                    {
                        "type": "kumihan_list",
                        "content": list_content,
                        "parsed": block_result,
                    }
                )

        return {
            "kumihan_blocks": parsed_blocks,
            "block_count": len(parsed_blocks),
        }

    def parse_regular_lists(self, content: str) -> Dict[str, Any]:
        """通常のリスト解析"""
        lines = content.split("\n")
        list_items = []
        current_item = None

        for line in lines:
            if not line.strip():
                continue

            list_type = detect_list_type(line)
            indent_level = get_list_nesting_level(line)

            if list_type:
                # 新しいリストアイテム
                if current_item:
                    list_items.append(current_item)

                current_item = {
                    "type": list_type,
                    "content": line.strip(),
                    "indent_level": indent_level,
                    "children": [],
                    "raw_line": line,
                }
            elif current_item and line.startswith(("  ", "\t")):
                # 継続行
                current_item["children"].append(line.strip())

        if current_item:
            list_items.append(current_item)

        return {
            "items": list_items,
            "item_count": len(list_items),
            "list_type": detect_full_list_type(content),
            "has_nested": has_nested_structure(content),
        }

    def parse_nested_structure(self, content: str) -> Dict[str, Any]:
        """ネスト構造の解析"""
        lines = content.split("\n")
        nested_items = []
        item_stack = []

        for line in lines:
            if not line.strip():
                continue

            list_type = detect_list_type(line)
            indent_level = get_list_nesting_level(line)

            if list_type:
                item = {
                    "type": list_type,
                    "content": line.strip(),
                    "indent_level": indent_level,
                    "children": [],
                    "parent": None,
                }

                # ネスト構造の構築
                while item_stack and item_stack[-1]["indent_level"] >= indent_level:
                    item_stack.pop()

                if item_stack:
                    parent = item_stack[-1]
                    parent["children"].append(item)
                    item["parent"] = parent
                else:
                    nested_items.append(item)

                item_stack.append(item)

        return {
            "nested_items": nested_items,
            "max_depth": self._calculate_max_depth(nested_items),
            "total_items": self._count_total_items(nested_items),
        }

    def parse_specialized_list(self, content: str, list_type: str) -> Dict[str, Any]:
        """特殊リスト形式の解析"""
        if list_type == "checklist":
            return self._parse_checklist(content)
        elif list_type == "definition":
            return self._parse_definition_list(content)
        else:
            return self.parse_regular_lists(content)

    def _parse_checklist(self, content: str) -> Dict[str, Any]:
        """チェックリストの解析"""
        lines = content.split("\n")
        checklist_items = []

        for line in lines:
            match = re.match(r"^\s*- \[([x ])\]\s+(.+)$", line)
            if match:
                checked = match.group(1) == "x"
                item_text = match.group(2)

                checklist_items.append(
                    {
                        "checked": checked,
                        "text": item_text,
                        "raw_line": line,
                    }
                )

        checked_count = sum(1 for item in checklist_items if item["checked"])

        return {
            "items": checklist_items,
            "total_items": len(checklist_items),
            "checked_items": checked_count,
            "completion_rate": (
                checked_count / len(checklist_items) if checklist_items else 0
            ),
        }

    def _parse_definition_list(self, content: str) -> Dict[str, Any]:
        """定義リストの解析"""
        lines = content.split("\n")
        definitions = []
        current_term = None
        current_definitions = []

        for line in lines:
            if line.strip().endswith(":") and not line.startswith(" "):
                # 新しい定義項目
                if current_term:
                    definitions.append(
                        {
                            "term": current_term,
                            "definitions": current_definitions.copy(),
                        }
                    )

                current_term = line.strip()[:-1]  # コロンを除去
                current_definitions = []

            elif line.startswith((" ", "\t")) and line.strip():
                # 定義内容
                current_definitions.append(line.strip())

        if current_term:
            definitions.append(
                {
                    "term": current_term,
                    "definitions": current_definitions,
                }
            )

        return {
            "definitions": definitions,
            "term_count": len(definitions),
            "avg_definitions_per_term": (
                sum(len(d["definitions"]) for d in definitions) / len(definitions)
                if definitions
                else 0
            ),
        }

    def _calculate_max_depth(self, items: List[Dict[str, Any]]) -> int:
        """最大ネスト深度の計算"""
        if not items:
            return 0

        max_depth = 1
        for item in items:
            if item.get("children"):
                child_depth = self._calculate_max_depth(item["children"])
                max_depth = max(max_depth, 1 + child_depth)

        return max_depth

    def _count_total_items(self, items: List[Dict[str, Any]]) -> int:
        """総アイテム数の計算"""
        total = len(items)
        for item in items:
            if item.get("children"):
                total += self._count_total_items(item["children"])

        return total

    def validate_list_structure(self, content: str) -> List[str]:
        """リスト構造の検証"""
        errors = []

        # 通常のリスト検証
        regular_errors = validate_regular_lists(content)
        errors.extend(regular_errors)

        # Kumihanリストブロック検証
        if is_kumihan_list_block(content):
            kumihan_errors = validate_kumihan_list_block(content)
            errors.extend(kumihan_errors)

        # チェックリスト検証
        if "- [" in content:
            checklist_errors = validate_checklist_format(content)
            errors.extend(checklist_errors)

        # 定義リスト検証
        if any(line.strip().endswith(":") for line in content.split("\n")):
            definition_errors = validate_definition_format(content)
            errors.extend(definition_errors)

        return errors
