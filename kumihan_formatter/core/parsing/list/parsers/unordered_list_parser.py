"""非順序リスト専用パーサー"""

import re
from typing import Any, Dict, List, Optional

# ノードインポート
from kumihan_formatter.core.ast_nodes import Node


class UnorderedListParser:
    """非順序リスト専用パーサー"""

    def __init__(self) -> None:
        """初期化"""
        self.unordered_patterns = {
            "bullet": re.compile(r"^(\s*)[-*+]\s+(?!\[)(.+)$"),  # チェックリストを除外
            "checklist": re.compile(r"^(\s*)[-*+]\s*\[([xX\s])\]\s*(.+)$"),
            "definition": re.compile(r"^(\s*)(.+?)\s*::\s*(.+)$"),
        }

    def detect_unordered_type(self, line: str) -> Optional[str]:
        """非順序リストタイプを検出

        Args:
            line: 検査対象の行

        Returns:
            Optional[str]: 検出されたタイプ（bullet/checklist/definition/None）
        """
        line = line.strip()
        for pattern_type, pattern in self.unordered_patterns.items():
            if pattern.match(line):
                return pattern_type
        return None

    def parse_unordered_list(self, lines: List[str]) -> List[Node]:
        """非順序リストを解析

        Args:
            lines: 解析対象の行リスト

        Returns:
            List[Node]: 解析されたノードリスト
        """
        nodes = []
        for i, line in enumerate(lines):
            if line.strip():
                node = self.parse_unordered_item(line, i)
                if node:
                    nodes.append(node)
        return nodes

    def parse_unordered_item(self, line: str, index: int = 0) -> Optional[Node]:
        """非順序リスト項目を解析

        Args:
            line: 解析対象の行
            index: 項目インデックス

        Returns:
            Optional[Node]: 解析されたノード
        """
        unordered_type = self.detect_unordered_type(line)
        if not unordered_type:
            return None

        pattern = self.unordered_patterns[unordered_type]
        match = pattern.match(line.strip())
        if not match:
            return None

        if unordered_type == "bullet":
            indent, content = match.groups()
            marker = line.strip()[len(indent) : line.strip().find(" ", len(indent))]

            node = Node(
                type="list_item",
                content=content.strip(),
                attributes={
                    "ordered": False,
                    "marker": marker,
                    "marker_type": "bullet",
                    "index": index,
                    "indent_level": len(indent),
                },
            )

        elif unordered_type == "checklist":
            indent, check_state, content = match.groups()
            checked = check_state.lower() == "x"

            node = Node(
                type="checklist_item",
                content=content.strip(),
                attributes={
                    "ordered": False,
                    "checked": checked,
                    "marker_type": "checklist",
                    "index": index,
                    "indent_level": len(indent),
                },
            )

        elif unordered_type == "definition":
            indent, term, definition = match.groups()

            node = Node(
                type="definition_item",
                content=definition.strip(),
                attributes={
                    "ordered": False,
                    "term": term.strip(),
                    "marker_type": "definition",
                    "index": index,
                    "indent_level": len(indent),
                },
            )

        else:
            return None

        return node

    def handle_unordered_list(self, line: str) -> Optional[Node]:
        """非順序リストハンドラー（統合用）

        Args:
            line: 処理対象の行

        Returns:
            Optional[Node]: 処理されたノード
        """
        return self.parse_unordered_item(line)

    def handle_checklist(self, line: str) -> Optional[Node]:
        """チェックリストハンドラー

        Args:
            line: 処理対象の行

        Returns:
            Optional[Node]: 処理されたノード
        """
        pattern = self.unordered_patterns["checklist"]
        match = pattern.match(line.strip())
        if not match:
            return None

        indent, check_state, content = match.groups()
        checked = check_state.lower() == "x"

        node = Node(
            type="checklist_item",
            content=content.strip(),
            attributes={
                "ordered": False,
                "checked": checked,
                "marker_type": "checklist",
                "indent_level": len(indent),
            },
        )
        return node

    def handle_definition_list(self, line: str) -> Optional[Node]:
        """定義リストハンドラー

        Args:
            line: 処理対象の行

        Returns:
            Optional[Node]: 処理されたノード
        """
        pattern = self.unordered_patterns["definition"]
        match = pattern.match(line.strip())
        if not match:
            return None

        indent, term, definition = match.groups()

        node = Node(
            type="definition_item",
            content=definition.strip(),
            attributes={
                "ordered": False,
                "term": term.strip(),
                "marker_type": "definition",
                "indent_level": len(indent),
            },
        )
        return node

    def extract_checklist_status(self, list_node: Node) -> Dict[str, Any]:
        """チェックリストの完了状況を抽出

        Args:
            list_node: チェックリストノード

        Returns:
            Dict[str, Any]: 完了状況統計
        """
        if not list_node.children:
            return {"total": 0, "checked": 0, "unchecked": 0, "completion_rate": 0.0}

        total = 0
        checked = 0

        def count_checklist_items(node: Node) -> None:
            nonlocal total, checked

            if node.type == "checklist_item":
                total += 1
                if node.attributes is not None and node.attributes.get(
                    "checked", False
                ):
                    checked += 1

            if node.children:
                for child in node.children:
                    count_checklist_items(child)

        count_checklist_items(list_node)

        unchecked = total - checked
        completion_rate = (checked / total) if total > 0 else 0.0

        return {
            "total": total,
            "checked": checked,
            "unchecked": unchecked,
            "completion_rate": completion_rate,
        }

    def toggle_checklist_item(self, node: Node) -> Node:
        """チェックリスト項目のチェック状態を切り替え

        Args:
            node: 切り替え対象のノード

        Returns:
            Node: 切り替え後のノード
        """
        if node.type != "checklist_item":
            return node

        new_node = Node(
            type=node.type,
            content=node.content,
            attributes=node.attributes.copy() if node.attributes is not None else {},
        )

        current_checked = (
            new_node.attributes.get("checked", False)
            if new_node.attributes is not None
            else False
        )
        if new_node.attributes is not None:
            new_node.attributes["checked"] = not current_checked

        return new_node

    def convert_to_bullet_list(self, node: Node, bullet_marker: str = "-") -> Node:
        """チェックリストを通常のリストに変換

        Args:
            node: 変換対象のノード
            bullet_marker: 使用するマーカー

        Returns:
            Node: 変換されたノード
        """
        if node.type != "checklist_item":
            return node

        new_node = Node(
            type="list_item",
            content=node.content,
            attributes=node.attributes.copy() if node.attributes is not None else {},
        )

        if new_node.attributes is not None:
            new_node.attributes.update(
                {
                    "marker": bullet_marker,
                    "marker_type": "bullet",
                }
            )

            # チェック状態関連の属性を削除
            new_node.attributes.pop("checked", None)

        return new_node

    def get_marker_from_line(self, line: str) -> Optional[str]:
        """行からマーカーを抽出

        Args:
            line: 抽出対象の行

        Returns:
            Optional[str]: 抽出されたマーカー
        """
        line = line.strip()
        if not line:
            return None

        # bulletパターンのマーカー抽出
        for marker in ["-", "*", "+"]:
            if line.startswith(marker + " "):
                return marker

        # checklistパターンのマーカー抽出
        checklist_pattern = re.compile(r"^([-*+])\s*\[[x\s]\]")
        match = checklist_pattern.match(line)
        if match:
            return match.group(1)

        return None

    def normalize_marker(self, lines: List[str], target_marker: str = "-") -> List[str]:
        """リストマーカーを統一

        Args:
            lines: 対象の行リスト
            target_marker: 統一するマーカー

        Returns:
            List[str]: マーカーが統一された行リスト
        """
        normalized_lines = []

        for line in lines:
            unordered_type = self.detect_unordered_type(line)
            if unordered_type == "bullet":
                pattern = self.unordered_patterns["bullet"]
                match = pattern.match(line.strip())
                if match:
                    indent, content = match.groups()
                    normalized_line = indent + target_marker + " " + content
                    normalized_lines.append(normalized_line)
                else:
                    normalized_lines.append(line)
            else:
                normalized_lines.append(line)

        return normalized_lines
