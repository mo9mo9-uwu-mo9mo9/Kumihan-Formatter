"""非順序リストパーサー

非順序リスト・チェックリスト・定義リストの解析を担当
"""

import re
from typing import Any, Dict, List

from ....ast_nodes import Node, create_node


class UnorderedListParser:
    """非順序リスト解析専用クラス

    担当機能:
    - 非順序リスト (-, *, +)
    - チェックリスト ([ ], [x])
    - 定義リスト (term :: definition)
    """

    def __init__(self) -> None:
        """初期化"""
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """非順序リスト用パターンの設定"""
        self.patterns = {
            # 順序なしリスト: - item, * item, + item
            "unordered": re.compile(r"^(\s*)[-*+]\s+(.+)$"),
            # 定義リスト: term :: definition
            "definition": re.compile(r"^(\s*)(.+?)\s*::\s*(.+)$"),
            # チェックリスト: - [ ] item, - [x] item
            "checklist": re.compile(r"^(\s*)[-*+]\s*\[([x\s])\]\s*(.+)$"),
        }

    def can_handle(self, line: str, list_type: str) -> bool:
        """指定された行とリストタイプを処理可能か判定"""
        return list_type in ["unordered", "definition", "checklist"] and bool(
            self.patterns[list_type].match(line)
        )

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

        return create_node("list_item", content=line.strip())

    def handle_checklist(self, line: str) -> Node:
        """チェックリストの処理"""
        match = self.patterns["checklist"].match(line)
        if match:
            indent = match.group(1)
            checked = match.group(2).lower() == "x"
            content = match.group(3)

            node = create_node("checklist_item", content=content)
            node.metadata.update(
                {"type": "checklist", "checked": checked, "indent": len(indent)}
            )
            return node

        return create_node("list_item", content=line.strip())

    def extract_item_content(self, line: str, list_type: str) -> str:
        """非順序リストアイテムからコンテンツを抽出"""
        pattern = self.patterns.get(list_type)
        if pattern:
            match = pattern.match(line)
            if match:
                if list_type == "unordered":
                    return match.group(2)
                elif list_type == "definition":
                    return match.group(3)  # definition部分
                elif list_type == "checklist":
                    return match.group(3)

        return line.strip()

    def extract_checklist_status(self, list_node: Node) -> Dict[str, Any]:
        """チェックリストの完了状況を抽出"""
        if list_node.metadata.get("type") != "checklist":
            return {"error": "Not a checklist"}

        total_items = 0
        checked_items = 0

        def count_items(node: Node) -> None:
            nonlocal total_items, checked_items

            if node.node_type == "checklist_item":
                total_items += 1
                if node.metadata.get("checked", False):
                    checked_items += 1

            # ネストした項目もカウント
            for child in node.metadata.get("children", []):
                count_items(child)

        count_items(list_node)

        completion_rate = (checked_items / total_items * 100) if total_items > 0 else 0

        return {
            "total_items": total_items,
            "checked_items": checked_items,
            "unchecked_items": total_items - checked_items,
            "completion_rate": completion_rate,
            "completed": checked_items == total_items and total_items > 0,
        }

    def validate_marker_consistency(self, items: List[Node]) -> List[str]:
        """マーカーの一貫性チェック"""
        errors = []
        markers_by_level = {}

        for i, item in enumerate(items):
            if item.metadata.get("type") == "unordered":
                marker = item.metadata.get("marker", "-")
                level = item.metadata.get("indent", 0)

                if level not in markers_by_level:
                    markers_by_level[level] = marker
                elif markers_by_level[level] != marker:
                    errors.append(
                        f"項目{i+1}: レベル{level}のマーカーが不一致 "
                        f"(期待: {markers_by_level[level]}, 実際: {marker})"
                    )

        return errors

    def get_supported_types(self) -> List[str]:
        """サポートするリストタイプを取得"""
        return list(self.patterns.keys())

    def toggle_checklist_item(self, node: Node) -> Node:
        """チェックリスト項目の状態切り替え"""
        if node.metadata.get("type") == "checklist_item":
            current_checked = node.metadata.get("checked", False)
            node.metadata["checked"] = not current_checked
        return node

    def convert_to_bullet_list(self, node: Node, bullet_marker: str = "-") -> Node:
        """チェックリストを通常の箇条書きに変換"""
        if node.metadata.get("type") == "checklist_item":
            node.metadata["type"] = "list_item"
            node.metadata["marker"] = bullet_marker
            if "checked" in node.metadata:
                del node.metadata["checked"]
        return node

    def get_marker_from_line(self, line: str) -> str | None:
        """行からリストマーカーを抽出"""
        for pattern in self.patterns.values():
            match = pattern.match(line)
            if match:
                if "[-*+]" in str(pattern.pattern):
                    # 非順序リストのマーカーを抽出
                    return (
                        line.strip()[0]
                        if line.strip() and line.strip()[0] in "-*+"
                        else None
                    )
        return None
