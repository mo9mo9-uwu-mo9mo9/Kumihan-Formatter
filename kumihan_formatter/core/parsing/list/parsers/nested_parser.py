"""ネストリストパーサー

ネストリスト構造の解析・インデント管理・動的構造構築を担当
"""

import re
from typing import Any, Dict, List

from ....ast_nodes import Node, list_item, unordered_list


class NestedListParser:
    """ネストリスト解析専用クラス

    担当機能:
    - ネストリスト構造解析
    - インデント管理・レベル判定
    - 動的構造構築（最大3レベル）
    - 階層整合性検証
    """

    def __init__(self) -> None:
        """初期化"""
        self._setup_patterns()
        self.max_nest_level = 3

    def _setup_patterns(self) -> None:
        """ネストリスト用パターンの設定"""
        self.patterns = {
            # インデント検出用
            "indent": re.compile(r"^(\s*)"),
            # ネストアイテム用
            "nested_item": re.compile(r"^(\s*)(.+)$"),
        }

    def can_handle_nesting(self, content: str) -> bool:
        """ネスト構造を処理可能か判定"""
        lines = content.split("\n")
        indent_levels = set()

        for line in lines:
            if line.strip():
                indent_match = self.patterns["indent"].match(line)
                if indent_match:
                    indent_levels.add(len(indent_match.group(1)))

        return len(indent_levels) > 1  # 複数のインデントレベルがある

    def build_nested_structure_list(self, items: List[Node]) -> List[Node]:
        """ネスト構造の構築（リスト版）"""
        if not items:
            return []

        result = []
        stack: list[tuple[Node, int]] = []  # (node, level) のスタック

        for item in items:
            current_level = item.metadata.get("relative_level", 0)

            # スタックから現在のレベル以上の項目を削除
            while stack and stack[-1][1] >= current_level:
                stack.pop()

            if current_level == 0:
                # ルートレベルの項目
                result.append(item)
                stack.append((item, current_level))
            else:
                # ネストした項目
                if stack:
                    parent_node, parent_level = stack[-1]

                    # 親ノードの子リストを作成
                    if "children" not in parent_node.metadata:
                        parent_node.metadata["children"] = []

                    parent_node.metadata["children"].append(item)
                    stack.append((item, current_level))
                else:
                    # 親がない場合はルートレベルに追加
                    result.append(item)
                    stack.append((item, current_level))

        return result

    def build_nested_structure(self, items: List[Node]) -> Node:
        """フラットなアイテムリストからネスト構造を構築"""
        if not items:
            return unordered_list([])

        root_items = []
        stack: List[Node] = []

        for item in items:
            level = item.metadata.get("nest_level", 0)

            # スタックを現在のレベルに調整
            while len(stack) > level:
                stack.pop()

            if level == 0:
                # ルートレベル
                root_items.append(item)
                stack = [item]
            else:
                # ネストレベル
                if stack:
                    parent = stack[-1]
                    if "children" not in parent.metadata:
                        parent.metadata["children"] = []
                    parent.metadata["children"].append(item)
                    stack.append(item)

        return unordered_list(root_items)

    def parse_nested_list(self, content: str, level: int = 0) -> List[Node]:
        """ネストリストをパース

        Args:
            content: ネストリストコンテンツ
            level: ネストレベル

        Returns:
            パースされたネストリストのノードリスト
        """
        if level > self.max_nest_level:
            return []  # 最大レベル制限

        lines = content.split("\n")
        nodes = []

        for line in lines:
            if not line.strip():
                continue

            # インデントでネストレベルを判定
            indent_match = self.patterns["indent"].match(line)
            if indent_match:
                current_indent = len(indent_match.group(1))
                expected_indent = level * 2  # 2スペース = 1レベル

                if current_indent == expected_indent:
                    # 現在のレベルのアイテム
                    node = self._create_list_item_node(line.strip(), level)
                    nodes.append(node)
                elif current_indent > expected_indent:
                    # より深いネストは再帰処理
                    nested_nodes = self.parse_nested_list(line, level + 1)
                    nodes.extend(nested_nodes)

        return nodes

    def calculate_relative_levels(
        self, items: List[Node], base_indent: int = 0
    ) -> None:
        """相対的なネストレベルを計算"""
        for item in items:
            absolute_indent = item.metadata.get("indent", 0)
            relative_level = max(0, (absolute_indent - base_indent) // 2)
            item.metadata["relative_level"] = relative_level

    def validate_nesting_structure(self, items: List[Node]) -> List[str]:
        """ネスト構造の妥当性検証"""
        errors = []
        prev_level = 0

        for i, item in enumerate(items):
            current_level = item.metadata.get("relative_level", 0)

            # レベルジャンプのチェック（1レベルずつのみ許可）
            if current_level > prev_level + 1:
                errors.append(
                    f"項目{i+1}: ネストレベルが急激に変化 "
                    f"(前レベル: {prev_level}, 現レベル: {current_level})"
                )

            # 最大レベル制限チェック
            if current_level > self.max_nest_level:
                errors.append(
                    f"項目{i+1}: ネストレベル{current_level}は制限を超えています "
                    f"(最大: {self.max_nest_level})"
                )

            prev_level = current_level

        return errors

    def has_nested_items(self, items: List[Node]) -> bool:
        """ネストした項目があるかチェック"""
        for item in items:
            if item.metadata.get("relative_level", 0) > 0:
                return True
        return False

    def get_nesting_statistics(self, items: List[Node]) -> Dict[str, Any]:
        """ネスト構造の統計情報を取得"""
        level_counts: Dict[int, int] = {}
        max_level = 0

        for item in items:
            level = item.metadata.get("relative_level", 0)
            level_counts[level] = level_counts.get(level, 0) + 1
            max_level = max(max_level, level)

        return {
            "max_level": max_level,
            "level_distribution": level_counts,
            "total_items": len(items),
            "has_nesting": max_level > 0,
        }

    def _create_list_item_node(self, content: str, level: int) -> Node:
        """リストアイテムノードを作成"""
        node = list_item(content)
        node.metadata.update({"level": level, "nest_level": level})
        return node
