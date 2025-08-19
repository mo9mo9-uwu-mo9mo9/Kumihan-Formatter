"""ネストリスト専用パーサー"""

import re
from typing import Any, Dict, List, Optional

# ノードインポート
from kumihan_formatter.core.ast_nodes import Node


class NestedListParser:
    """ネストリスト専用パーサー"""

    def __init__(self) -> None:
        """初期化"""
        self.indent_pattern = re.compile(r"^(\s*)")
        self.max_nesting_level = 3  # 最大ネストレベル

    def parse_nested_list(
        self, content: str, level: int = 0, context: Optional[Dict[str, Any]] = None
    ) -> List[Node]:
        """ネストリストをパース

        Args:
            content: ネストリストコンテンツ
            level: ネストレベル
            context: パースコンテキスト（オプション）

        Returns:
            List[Node]: パースされたネストリストのノードリスト
        """
        lines = content.split("\n") if isinstance(content, str) else content
        return self.build_nested_structure(lines, level)

    def build_nested_structure(
        self, lines: List[str], base_level: int = 0
    ) -> List[Node]:
        """ネスト構造を構築

        Args:
            lines: 構築対象の行リスト
            base_level: 基準レベル

        Returns:
            List[Node]: 構築されたネスト構造
        """
        if not lines:
            return []

        nodes = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if not line.strip():
                i += 1
                continue

            indent_level = self.get_indent_level(line)

            # 基準レベルより浅い場合は終了
            if indent_level < base_level:
                break

            # 同レベルの項目として処理
            if indent_level == base_level:
                node = self.create_list_item_node(line, indent_level)
                if node:
                    # 次の行以降で子要素をチェック
                    child_lines = []
                    j = i + 1

                    while j < len(lines):
                        next_line = lines[j].rstrip()
                        if not next_line.strip():
                            j += 1
                            continue

                        next_indent = self.get_indent_level(next_line)

                        # より深いインデント = 子要素
                        if next_indent > indent_level:
                            child_lines.append(next_line)
                            j += 1
                        else:
                            break

                    # 子要素がある場合は再帰処理
                    if child_lines:
                        child_nodes = self.build_nested_structure(
                            child_lines, base_level + 1
                        )
                        if child_nodes:
                            node.children = child_nodes

                    nodes.append(node)
                    i = j
                else:
                    i += 1
            else:
                i += 1

        return nodes

    def build_nested_structure_list(self, items: List[Node]) -> List[Node]:
        """ノードリストからネスト構造を構築

        Args:
            items: 構築対象のノードリスト

        Returns:
            List[Node]: 構築されたネスト構造
        """
        if not items:
            return []

        # インデントレベルでグループ化
        level_groups = self.group_by_indent_level(items)
        return self.build_hierarchy_from_groups(level_groups)

    def group_by_indent_level(self, items: List[Node]) -> Dict[int, List[Node]]:
        """インデントレベルでノードをグループ化

        Args:
            items: グループ化対象のノードリスト

        Returns:
            Dict[int, List[Node]]: レベル別グループ
        """
        groups: Dict[int, List[Node]] = {}

        for item in items:
            level = item.metadata.get("relative_level", 0)
            if level not in groups:
                groups[level] = []
            groups[level].append(item)

        return groups

    def build_hierarchy_from_groups(
        self, level_groups: Dict[int, List[Node]]
    ) -> List[Node]:
        """レベル別グループから階層構造を構築

        Args:
            level_groups: レベル別グループ

        Returns:
            List[Node]: 構築された階層構造
        """
        if not level_groups:
            return []

        # レベル0（ルートレベル）から開始
        root_nodes = level_groups.get(0, [])

        # 各ルートノードに子要素を追加
        for root_node in root_nodes:
            self.attach_children(root_node, level_groups, 1)

        return root_nodes

    def attach_children(
        self, parent_node: Node, level_groups: Dict[int, List[Node]], target_level: int
    ) -> None:
        """親ノードに子要素を追加

        Args:
            parent_node: 親ノード
            level_groups: レベル別グループ
            target_level: 対象レベル
        """
        if target_level not in level_groups or target_level > self.max_nesting_level:
            return

        children = []
        parent_index = parent_node.metadata.get("index", 0)

        # 同じ親の下にある子要素を特定
        for child_node in level_groups[target_level]:
            # 簡単な親子関係の判定（実際の実装では更に詳細な判定が必要）
            child_index = child_node.metadata.get("index", 0)
            if child_index > parent_index:
                children.append(child_node)
                # 再帰的に子要素の子要素も追加
                self.attach_children(child_node, level_groups, target_level + 1)

        if children:
            parent_node.children = children

    def get_indent_level(self, line: str) -> int:
        """行のインデントレベルを取得

        Args:
            line: 対象の行

        Returns:
            int: インデントレベル（スペース数）
        """
        match = self.indent_pattern.match(line)
        return len(match.group(1)) if match else 0

    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得

        Args:
            line: 検査対象の行

        Returns:
            int: ネストレベル（0=ルートレベル）
        """
        indent_level = self.get_indent_level(line)
        # 通常、インデント4スペース = 1レベル
        return indent_level // 4

    def create_list_item_node(self, line: str, indent_level: int) -> Optional[Node]:
        """リスト項目ノードを作成

        Args:
            line: 対象の行
            indent_level: インデントレベル

        Returns:
            Optional[Node]: 作成されたノード
        """
        content = line.strip()
        if not content:
            return None

        # リスト記号を除去してコンテンツを取得
        list_markers = ["-", "*", "+"]
        for marker in list_markers:
            if content.startswith(marker + " "):
                content = content[2:].strip()
                break

        # 順序リスト記号を除去
        ordered_pattern = re.compile(r"^\d+\.\s+")
        if ordered_pattern.match(content):
            content = ordered_pattern.sub("", content).strip()

        node = Node(
            type="list_item",
            content=content,
            attributes={
                "indent_level": indent_level,
                "nesting_level": indent_level // 4,
            },
        )

        return node

    def has_nested_items(self, items: List[Node]) -> bool:
        """ネストした項目があるかチェック

        Args:
            items: チェック対象のノードリスト

        Returns:
            bool: ネストした項目があるかどうか
        """
        if not items:
            return False

        base_level = items[0].metadata.get("relative_level", 0)

        for item in items[1:]:
            if item.metadata.get("relative_level", 0) > base_level:
                return True

        return False

    def flatten_nested_list(self, node: Node) -> List[Node]:
        """ネストリストを平坦化

        Args:
            node: 平坦化対象のノード

        Returns:
            List[Node]: 平坦化されたノードリスト
        """
        flattened = []

        def flatten_recursive(current_node: Node, level: int = 0) -> None:
            # 現在のノードを追加
            if current_node.type in ["list_item", "checklist_item", "definition_item"]:
                flat_node = Node(
                    type=current_node.type,
                    content=current_node.content,
                    attributes=current_node.attributes.copy(),
                )
                flat_node.attributes["original_level"] = level
                flattened.append(flat_node)

            # 子ノードを再帰的に処理
            if current_node.children:
                for child in current_node.children:
                    flatten_recursive(child, level + 1)

        flatten_recursive(node)
        return flattened

    def calculate_nesting_depth(self, items: List[Node]) -> int:
        """ネストの深度を計算

        Args:
            items: 計算対象のノードリスト

        Returns:
            int: 最大ネスト深度
        """
        if not items:
            return 0

        max_depth = 0

        def calculate_depth_recursive(node: Node, current_depth: int = 0) -> int:
            depth = current_depth
            if node.children:
                for child in node.children:
                    child_depth = calculate_depth_recursive(child, current_depth + 1)
                    depth = max(depth, child_depth)
            return depth

        for item in items:
            item_depth = calculate_depth_recursive(item)
            max_depth = max(max_depth, item_depth)

        return max_depth

    def normalize_indentation(
        self, lines: List[str], spaces_per_level: int = 4
    ) -> List[str]:
        """インデントを正規化

        Args:
            lines: 正規化対象の行リスト
            spaces_per_level: レベルあたりのスペース数

        Returns:
            List[str]: 正規化された行リスト
        """
        if not lines:
            return lines

        normalized_lines = []

        for line in lines:
            if not line.strip():
                normalized_lines.append(line)
                continue

            current_indent = self.get_indent_level(line)
            content = line.lstrip()

            # インデントレベルを計算
            level = current_indent // spaces_per_level
            new_indent = " " * (level * spaces_per_level)

            normalized_lines.append(new_indent + content)

        return normalized_lines
