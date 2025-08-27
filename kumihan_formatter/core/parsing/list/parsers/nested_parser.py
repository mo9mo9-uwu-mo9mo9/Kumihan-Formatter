"""ネストリストパーサー

ネストリスト構造の解析・インデント管理・動的構造構築を担当
"""

import re
from typing import Any, Dict, List, Optional

from ....ast_nodes import Node, list_item, unordered_list


class NestedListParser:
    """ネストリストパーサー - 統合版
    
    nested_list_parser.py の詳細実装を統合
    機能: インデント管理、階層構造構築、深度計算
    """

    def __init__(self) -> None:
        """初期化: ネストリスト処理の設定"""
        from kumihan_formatter.core.utilities.logger import get_logger
        
        self.logger = get_logger(__name__)
        self.indent_pattern = re.compile(r"^(\s*)")
        self.max_nesting_level = 10  # 最大ネストレベル制限

    def parse_nested_list(self, content: str, level: int = 0, context: dict[str, Any] | None = None) -> list[Node]:
        """ネストリストをパース - レベル指定対応

        Args:
            content: ネストリストコンテンツ
            level: ネストレベル
            context: パースコンテキスト（オプション）

        Returns:
            パースされたネストリストのノードリスト
        """
        if not content:
            return []

        lines = content.split('\n')
        parsed_items = self.build_nested_structure(lines)
        
        # ノード作成
        nodes = []
        for item in parsed_items:
            node = self.create_list_item_node(item, level)
            if node:
                nodes.append(node)
        
        return nodes

    def build_nested_structure(self, lines: list[str]) -> list[dict[str, Any]]:
        """行リストからネスト構造を構築

        Args:
            lines: 処理対象の行リスト

        Returns:
            ネスト構造を持つアイテムリスト
        """
        if not lines:
            return []

        # 空行をフィルタ
        non_empty_lines = [(i, line) for i, line in enumerate(lines) if line.strip()]
        
        if not non_empty_lines:
            return []

        # インデントレベルを計算
        items = []
        for original_index, line in non_empty_lines:
            indent_level = self.get_indent_level(line)
            
            # 最大ネストレベル制限
            if indent_level > self.max_nesting_level:
                self.logger.warning(f"インデントレベル {indent_level} が最大値 {self.max_nesting_level} を超えています")
                indent_level = self.max_nesting_level

            items.append({
                "content": line.strip(),
                "indent_level": indent_level,
                "original_line": line,
                "original_index": original_index,
                "children": []
            })

        # 階層構造を構築
        return self.build_hierarchy_from_groups(items)

    def build_nested_structure_list(self, lines: list[str]) -> list[Any]:
        """既存API互換用: リスト形式でネスト構造を返す
        
        Args:
            lines: 処理対象の行リスト
            
        Returns:
            ネストされたリスト構造
        """
        structured_items = self.build_nested_structure(lines)
        return self._convert_to_list_format(structured_items)

    def _convert_to_list_format(self, structured_items: list[dict[str, Any]]) -> list[Any]:
        """構造化アイテムをリスト形式に変換"""
        result = []
        for item in structured_items:
            if item["children"]:
                result.append([item["content"], self._convert_to_list_format(item["children"])])
            else:
                result.append(item["content"])
        return result

    def group_by_indent_level(self, items: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
        """アイテムをインデントレベル別にグループ化

        Args:
            items: グループ化対象のアイテムリスト

        Returns:
            インデントレベルをキーとするアイテム辞書
        """
        groups = {}
        for item in items:
            level = item["indent_level"]
            if level not in groups:
                groups[level] = []
            groups[level].append(item)
        return groups

    def build_hierarchy_from_groups(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """アイテムリストから階層構造を構築

        Args:
            items: 階層化対象のアイテムリスト

        Returns:
            階層構造を持つルートレベルアイテムリスト
        """
        if not items:
            return []

        # ルートレベル（最小インデント）を決定
        min_indent = min(item["indent_level"] for item in items)
        
        # ルートアイテムを抽出
        root_items = [item for item in items if item["indent_level"] == min_indent]
        
        # 各ルートアイテムに子要素を付与
        for root_item in root_items:
            self.attach_children(root_item, items)
        
        return root_items

    def attach_children(self, parent: dict[str, Any], all_items: list[dict[str, Any]]) -> None:
        """親アイテムに子要素を付与

        Args:
            parent: 親アイテム
            all_items: 全アイテムリスト
        """
        parent_index = parent["original_index"]
        parent_indent = parent["indent_level"]

        # 直接の子要素（親の次のレベル）を特定
        child_indent_level = parent_indent + 1
        children = []

        for item in all_items:
            if (item["original_index"] > parent_index and 
                item["indent_level"] == child_indent_level):
                
                # 次の同レベル以上のアイテムまでを子として扱う
                next_sibling_index = self._get_next_parent_index(item, all_items, parent_indent)
                
                if next_sibling_index == -1 or item["original_index"] < next_sibling_index:
                    children.append(item)

        # 各子要素に再帰的に子要素を付与
        for child in children:
            self.attach_children(child, all_items)

        parent["children"] = children

    def _binary_search_first_greater(self, arr: list[dict[str, Any]], target_index: int, target_level: int) -> int:
        """二分探索で最初の大きな値を見つける

        Args:
            arr: 検索対象配列
            target_index: ターゲットインデックス
            target_level: ターゲットレベル

        Returns:
            条件を満たす最初のインデックス、見つからない場合は-1
        """
        left, right = 0, len(arr) - 1
        result = -1

        while left <= right:
            mid = (left + right) // 2
            item = arr[mid]
            
            if (item["original_index"] > target_index and 
                item["indent_level"] <= target_level):
                result = mid
                right = mid - 1
            else:
                left = mid + 1

        return result

    def _get_next_parent_index(self, current_item: dict[str, Any], all_items: list[dict[str, Any]], target_level: int) -> int:
        """次の親レベルアイテムのインデックスを取得

        Args:
            current_item: 現在のアイテム
            all_items: 全アイテムリスト
            target_level: ターゲットレベル

        Returns:
            次の親レベルアイテムのインデックス、見つからない場合は-1
        """
        current_index = current_item["original_index"]

        for item in all_items:
            if (item["original_index"] > current_index and 
                item["indent_level"] <= target_level):
                return item["original_index"]

        return -1  # 見つからない場合

    def get_indent_level(self, line: str) -> int:
        """行のインデントレベルを取得（スペース数/4）

        Args:
            line: 検査対象の行

        Returns:
            インデントレベル
        """
        match = self.indent_pattern.match(line)
        if match:
            indent_str = match.group(1)
            # タブを4スペースとして計算
            space_count = len(indent_str.replace('\t', '    '))
            return space_count // 4
        return 0

    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得（ブラケット深度計算）

        Args:
            line: 検査対象の行

        Returns:
            ネストレベル（0=ルートレベル）
        """
        bracket_depth = 0
        for char in line:
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
        
        return max(0, bracket_depth)

    def create_list_item_node(self, item: dict[str, Any], base_level: int = 0) -> Node:
        """アイテムからリストアイテムノードを作成

        Args:
            item: ノード作成元アイテム
            base_level: ベースレベル

        Returns:
            作成されたリストアイテムノード
        """
        from ...ast_nodes import Node, NodeType
        
        content = item.get("content", "")
        indent_level = item.get("indent_level", 0) + base_level
        
        # 子要素も処理
        children = []
        for child_item in item.get("children", []):
            child_node = self.create_list_item_node(child_item, base_level)
            if child_node:
                children.append(child_node)

        # リストアイテムノードを作成
        node = Node(
            node_type=NodeType.LIST_ITEM,
            content=content,
            level=indent_level,
            children=children
        )
        
        return node

    def has_nested_items(self, lines: list[str]) -> bool:
        """行リストにネストアイテムが含まれているかを判定

        Args:
            lines: 判定対象の行リスト

        Returns:
            ネストアイテムが含まれている場合True
        """
        if len(lines) < 2:
            return False

        # 複数の異なるインデントレベルがあるかチェック
        indent_levels = set()
        for line in lines:
            if line.strip():  # 空行は無視
                indent_level = self.get_indent_level(line)
                indent_levels.add(indent_level)
        
        return len(indent_levels) > 1

    def flatten_nested_list(self, nested_items: list[dict[str, Any]]) -> list[str]:
        """ネストリストをフラット化

        Args:
            nested_items: フラット化対象のネストアイテムリスト

        Returns:
            フラット化された文字列リスト
        """
        flattened = []
        
        def _flatten_recursive(items: list[dict[str, Any]], level: int = 0):
            for item in items:
                # インデント付きで追加
                indent = "    " * level
                flattened.append(f"{indent}{item['content']}")
                
                # 子要素を再帰的に処理
                if item.get("children"):
                    _flatten_recursive(item["children"], level + 1)
        
        _flatten_recursive(nested_items)
        return flattened

    def calculate_nesting_depth(self, nested_items: list[dict[str, Any]]) -> int:
        """ネストアイテムの最大深度を計算

        Args:
            nested_items: 深度計算対象のネストアイテムリスト

        Returns:
            最大深度
        """
        if not nested_items:
            return 0

        max_depth = 0
        
        def _calculate_recursive(items: list[dict[str, Any]], current_depth: int = 1):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for item in items:
                if item.get("children"):
                    _calculate_recursive(item["children"], current_depth + 1)
        
        _calculate_recursive(nested_items)
        return max_depth

    def normalize_indentation(self, lines: list[str], tab_size: int = 4) -> list[str]:
        """インデントを正規化（タブをスペースに変換）

        Args:
            lines: 正規化対象の行リスト
            tab_size: タブのスペース数

        Returns:
            正規化された行リスト
        """
        normalized = []
        
        for line in lines:
            # タブをスペースに変換
            normalized_line = line.replace('\t', ' ' * tab_size)
            
            # 行末の空白を除去
            normalized_line = normalized_line.rstrip()
            
            normalized.append(normalized_line)
        
        return normalized

    # API互換性メソッド（簡素版からの移行用）
    def parse_lines(self, lines: list[str]) -> list[Node]:
        """行リストを解析してノードリストを返す"""
        return self.parse_nested_list('\n'.join(lines))

    def detect_nesting_structure(self, lines: list[str]) -> dict[str, Any]:
        """ネスト構造を検出して分析結果を返す"""
        structured_items = self.build_nested_structure(lines)
        
        return {
            "has_nesting": self.has_nested_items(lines),
            "max_depth": self.calculate_nesting_depth(structured_items),
            "total_items": len(lines),
            "root_items": len([item for item in structured_items if item["indent_level"] == 0])
        }

    def create_flat_representation(self, lines: list[str]) -> list[str]:
        """フラット表現を作成"""
        structured_items = self.build_nested_structure(lines)
        return self.flatten_nested_list(structured_items)
