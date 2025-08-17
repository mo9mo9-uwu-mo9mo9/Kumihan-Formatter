"""基本リストハンドラー - specialized list_parser分割

基本的なリスト処理機能を提供:
- 順序なしリスト処理
- 順序付きリスト処理
- 定義リスト処理
- チェックリスト処理
"""

import re
from typing import Any, Dict, Optional

from ....ast_nodes import Node, create_node


class BasicListHandler:
    """基本リスト処理ハンドラー"""

    def __init__(self):
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """基本リスト解析パターンの設定"""
        self.patterns = {
            # 順序なしリスト: - item, * item, + item
            "unordered": re.compile(r"^(\s*)[-*+]\s+(.+)$"),
            # 順序付きリスト: 1. item, 2. item
            "ordered": re.compile(r"^(\s*)(\d+)\.\s+(.+)$"),
            # 定義リスト: term :: definition
            "definition": re.compile(r"^(\s*)(.+?)\s*::\s*(.+)$"),
            # チェックリスト: - [ ] item, - [x] item
            "checklist": re.compile(r"^(\s*)[-*+]\s*\[([x\s])\]\s*(.+)$"),
        }

    def handle_unordered_list(self, line: str) -> Node:
        """順序なしリストの処理"""
        match = self.patterns["unordered"].match(line)
        if match:
            indent = match.group(1)
            content = match.group(2)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {
                    "type": "unordered",
                    "marker": line.strip()[0],  # -, *, +
                    "indent": len(indent),
                }
            )
            return node

        return create_node("list_item", content=line.strip())

    def handle_ordered_list(self, line: str) -> Node:
        """順序付きリストの処理"""
        match = self.patterns["ordered"].match(line)
        if match:
            indent = match.group(1)
            number = int(match.group(2))
            content = match.group(3)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {"type": "ordered", "number": number, "indent": len(indent)}
            )
            return node

        return create_node("list_item", content=line.strip())

    def handle_definition_list(self, line: str) -> Node:
        """定義リストの処理"""
        match = self.patterns["definition"].match(line)
        if match:
            indent = match.group(1)
            term = match.group(2)
            definition = match.group(3)

            node = create_node("definition_item", content=definition)
            node.metadata.update(
                {
                    "type": "definition",
                    "term": term,
                    "definition": definition,
                    "indent": len(indent),
                }
            )
            return node

        return create_node("definition_item", content=line.strip())

    def handle_checklist(self, line: str) -> Node:
        """チェックリストの処理"""
        match = self.patterns["checklist"].match(line)
        if match:
            indent = match.group(1)
            checked_char = match.group(2)
            content = match.group(3)

            is_checked = checked_char.lower() == "x"

            node = create_node("checklist_item", content=content)
            node.metadata.update(
                {
                    "type": "checklist",
                    "checked": is_checked,
                    "indent": len(indent),
                }
            )
            return node

        return create_node("checklist_item", content=line.strip())

    def detect_list_type(self, line: str) -> Optional[str]:
        """行からリストタイプを検出"""
        for list_type, pattern in self.patterns.items():
            if pattern.match(line):
                return list_type
        return None

    def get_handlers(self) -> Dict[str, Any]:
        """ハンドラー辞書を返す"""
        return {
            "unordered": self.handle_unordered_list,
            "ordered": self.handle_ordered_list,
            "definition": self.handle_definition_list,
            "checklist": self.handle_checklist,
        }
