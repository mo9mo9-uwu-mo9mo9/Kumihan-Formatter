"""順序付きリスト専用パーサー"""

import re
from typing import List, Optional, Pattern

# ノードインポート
from kumihan_formatter.core.ast_nodes import Node


class OrderedListParser:
    """順序付きリスト専用パーサー"""

    def __init__(self) -> None:
        """初期化"""
        # パターンの検証順序を制御するため、リストで定義
        # より具体的なパターン（roman）を先に検証
        self.ordered_patterns = [
            ("numeric", re.compile(r"^(\s*)(\d+)\.\s+(.+)$")),
            (
                "roman",
                re.compile(
                    r"^(\s*)(i{1,3}|iv|v|vi{0,3}|ix|x|xi{0,3}|xiv|xv|xvi{0,3}|xix|xx)"
                    r"\.\s+(.+)$",
                    re.IGNORECASE,
                ),
            ),
            ("alpha", re.compile(r"^(\s*)([a-zA-Z])\.\s+(.+)$")),
        ]

    def _get_pattern(self, pattern_type: str) -> Optional[Pattern[str]]:
        """パターンタイプに対応する正規表現パターンを取得

        Args:
            pattern_type: パターンタイプ（numeric/alpha/roman）

        Returns:
            対応するパターン、見つからない場合はNone
        """
        for ptype, pattern in self.ordered_patterns:
            if ptype == pattern_type:
                return pattern
        return None

    def detect_ordered_type(self, line: str) -> Optional[str]:
        """順序リストタイプを検出

        Args:
            line: 検査対象の行

        Returns:
            Optional[str]: 検出されたタイプ（numeric/alpha/roman/None）
        """
        line = line.strip()
        for pattern_type, pattern in self.ordered_patterns:
            if pattern.match(line):
                return pattern_type
        return None

    def parse_ordered_list(self, lines: List[str]) -> List[Node]:
        """順序付きリストを解析

        Args:
            lines: 解析対象の行リスト

        Returns:
            List[Node]: 解析されたノードリスト
        """
        nodes = []
        for i, line in enumerate(lines):
            if line.strip():
                node = self.parse_ordered_item(line, i)
                if node:
                    nodes.append(node)
        return nodes

    def parse_ordered_item(self, line: str, index: int = 0) -> Optional[Node]:
        """順序付きリスト項目を解析

        Args:
            line: 解析対象の行
            index: 項目インデックス

        Returns:
            Optional[Node]: 解析されたノード
        """
        ordered_type = self.detect_ordered_type(line)
        if not ordered_type:
            return None

        # パターンタイプに対応するパターンを取得
        pattern = self._get_pattern(ordered_type)
        if not pattern:
            return None
        match = pattern.match(line)
        if not match:
            return None

        indent, marker, content = match.groups()
        indent_level = len(indent)

        node = Node(
            type="list_item",
            content=content.strip(),
            attributes={
                "ordered": True,
                "marker": marker,
                "marker_type": ordered_type,
                "index": index,
                "indent_level": indent_level,
            },
        )
        return node

    def handle_ordered_list(self, line: str) -> Optional[Node]:
        """順序付きリストハンドラー（統合用）

        Args:
            line: 処理対象の行

        Returns:
            Optional[Node]: 処理されたノード
        """
        return self.parse_ordered_item(line)

    def handle_alpha_list(self, line: str) -> Optional[Node]:
        """アルファベットリストハンドラー

        Args:
            line: 処理対象の行

        Returns:
            Optional[Node]: 処理されたノード
        """
        pattern = self._get_pattern("alpha")
        if not pattern:
            return None
        match = pattern.match(line)
        if not match:
            return None

        indent, marker, content = match.groups()
        node = Node(
            type="list_item",
            content=content.strip(),
            attributes={
                "ordered": True,
                "marker": marker,
                "marker_type": "alpha",
                "indent_level": len(indent),
            },
        )
        return node

    def handle_roman_list(self, line: str) -> Optional[Node]:
        """ローマ数字リストハンドラー

        Args:
            line: 処理対象の行

        Returns:
            Optional[Node]: 処理されたノード
        """
        pattern = self._get_pattern("roman")
        if not pattern:
            return None
        match = pattern.match(line)
        if not match:
            return None

        indent, marker, content = match.groups()
        node = Node(
            type="list_item",
            content=content.strip(),
            attributes={
                "ordered": True,
                "marker": marker.lower(),
                "marker_type": "roman",
                "indent_level": len(indent),
            },
        )
        return node

    def validate_sequence(self, lines: List[str]) -> List[str]:
        """順序の連続性を検証

        Args:
            lines: 検証対象の行リスト

        Returns:
            List[str]: エラーメッセージリスト
        """
        errors = []
        numeric_counter = 1
        alpha_counter = ord("a")

        for i, line in enumerate(lines):
            ordered_type = self.detect_ordered_type(line)
            if not ordered_type:
                continue

            pattern = self._get_pattern(ordered_type)
            if not pattern:
                continue
            match = pattern.match(line)
            if not match:
                continue

            marker = match.group(2)

            if ordered_type == "numeric":
                try:
                    number = int(marker)
                    if number != numeric_counter:
                        errors.append(
                            f"行{i+1}: 順序が不正 (期待値: {numeric_counter}, 実際: {number})"
                        )
                    numeric_counter += 1
                except ValueError:
                    errors.append(f"行{i+1}: 無効な数値マーカー: {marker}")

            elif ordered_type == "alpha":
                expected_char = chr(alpha_counter)
                if marker.lower() != expected_char:
                    errors.append(
                        f"行{i+1}: アルファベット順序が不正 (期待値: {expected_char}, 実際: {marker})"
                    )
                alpha_counter += 1

        return errors

    def convert_to_numeric(self, node: Node) -> Node:
        """ノードを数値順序リストに変換

        Args:
            node: 変換対象のノード

        Returns:
            Node: 変換されたノード
        """
        if (
            node.attributes is not None
            and node.attributes.get("marker_type") == "numeric"
        ):
            return node

        new_node = Node(
            type=node.type,
            content=node.content,
            attributes=node.attributes.copy() if node.attributes is not None else {},
        )

        # 数値マーカーに変換
        index = node.attributes.get("index", 0) if node.attributes is not None else 0
        if new_node.attributes is not None:
            new_node.attributes.update(
                {
                    "marker": str(index + 1),
                    "marker_type": "numeric",
                }
            )

        return new_node

    def get_next_marker(self, marker_type: str, current_marker: str) -> str:
        """次のマーカーを取得

        Args:
            marker_type: マーカータイプ
            current_marker: 現在のマーカー

        Returns:
            str: 次のマーカー
        """
        if marker_type == "numeric":
            try:
                return str(int(current_marker) + 1)
            except ValueError:
                return "1"

        elif marker_type == "alpha":
            if len(current_marker) == 1 and current_marker.isalpha():
                next_ord = ord(current_marker.lower()) + 1
                if next_ord <= ord("z"):
                    return chr(next_ord)
                return "a"
            return "a"

        elif marker_type == "roman":
            roman_numerals = [
                "i",
                "ii",
                "iii",
                "iv",
                "v",
                "vi",
                "vii",
                "viii",
                "ix",
                "x",
            ]
            try:
                current_index = roman_numerals.index(current_marker.lower())
                if current_index + 1 < len(roman_numerals):
                    return roman_numerals[current_index + 1]
                return "i"
            except ValueError:
                return "i"

        return current_marker
