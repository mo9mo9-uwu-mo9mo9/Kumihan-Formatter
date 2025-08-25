"""List Item Handlers - 個別リストアイテム処理ハンドラ

分離された責任:
- 個別リストアイテムの処理
- 各種マーカー形式のハンドラ（順序なし、数字、チェック、定義、アルファベット、ローマ数字）
"""

from typing import Any, Dict
import re
from ...core.utilities.logger import get_logger
from .list_utils import get_list_nesting_level


class ListItemHandler:
    """個別のリストアイテム処理ハンドラ"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def handle_unordered_item(self, line: str) -> Dict[str, Any]:
        """順序なしリストアイテムの処理"""
        match = re.match(r"^\s*([-*+])\s+(.+)$", line)
        if match:
            marker = match.group(1)
            content = match.group(2)

            return {
                "type": "unordered",
                "marker": marker,
                "content": content,
                "indent_level": get_list_nesting_level(line),
            }

        return {"type": "unknown", "content": line}

    def handle_ordered_numeric_item(self, line: str) -> Dict[str, Any]:
        """数字順序付きリストアイテムの処理"""
        match = re.match(r"^\s*(\d+)\.\s+(.+)$", line)
        if match:
            number = int(match.group(1))
            content = match.group(2)

            return {
                "type": "ordered_numeric",
                "number": number,
                "content": content,
                "indent_level": get_list_nesting_level(line),
            }

        return {"type": "unknown", "content": line}

    def handle_checklist_item(self, line: str) -> Dict[str, Any]:
        """チェックリストアイテムの処理"""
        match = re.match(r"^\s*- \[([x ])\]\s+(.+)$", line)
        if match:
            checked = match.group(1) == "x"
            content = match.group(2)

            return {
                "type": "checklist",
                "checked": checked,
                "content": content,
                "indent_level": get_list_nesting_level(line),
            }

        return {"type": "unknown", "content": line}

    def handle_definition_item(self, line: str) -> Dict[str, Any]:
        """定義リストアイテムの処理"""
        if line.strip().endswith(":") and not line.startswith(" "):
            term = line.strip()[:-1]

            return {
                "type": "definition_term",
                "term": term,
                "indent_level": get_list_nesting_level(line),
            }
        elif line.startswith((" ", "\t")) and line.strip():
            return {
                "type": "definition_content",
                "content": line.strip(),
                "indent_level": get_list_nesting_level(line),
            }

        return {"type": "unknown", "content": line}

    def handle_alpha_item(self, line: str) -> Dict[str, Any]:
        """アルファベット順序付きリストアイテムの処理"""
        match = re.match(r"^\s*([a-zA-Z])\.\s+(.+)$", line)
        if match:
            letter = match.group(1)
            content = match.group(2)

            return {
                "type": "ordered_alpha",
                "letter": letter,
                "content": content,
                "indent_level": get_list_nesting_level(line),
            }

        return {"type": "unknown", "content": line}

    def handle_roman_item(self, line: str) -> Dict[str, Any]:
        """ローマ数字順序付きリストアイテムの処理"""
        match = re.match(r"^\s*([ivxlcdm]+)\.\s+(.+)$", line, re.IGNORECASE)
        if match:
            roman = match.group(1)
            content = match.group(2)

            return {
                "type": "ordered_roman",
                "roman": roman,
                "content": content,
                "indent_level": get_list_nesting_level(line),
            }

        return {"type": "unknown", "content": line}
