"""リスト共通ユーティリティ - specialized list_parser分割

リスト処理の共通機能を提供:
- リストノード作成・管理
- タイプ変換・判定
- チェックリスト状況分析
- ファクトリーメソッド
"""

from typing import Any, Dict, List

from ....ast_nodes import Node, create_node


class ListUtilities:
    """リスト共通ユーティリティ"""

    @staticmethod
    def create_list_node(items: List[Node], list_type: str) -> Node:
        """リストノードを作成"""
        if not items:
            return create_node("list", content="")

        # リストタイプに基づいてノードタイプを決定
        node_type_map = {
            "unordered": "ul",
            "ordered": "ol",
            "definition": "dl",
            "checklist": "checklist",
            "alpha": "ol",
            "roman": "ol",
            "block": "list",
            "character_delimited": "list",
        }

        node_type = node_type_map.get(list_type, "ul")
        list_node = create_node(node_type, content="")

        # メタデータの設定
        list_node.metadata.update(
            {
                "type": list_type,
                "item_count": len(items),
                "has_nested": ListUtilities.has_nested_items(items),
            }
        )

        # 子項目の追加
        list_node.children = items

        return list_node

    @staticmethod
    def determine_primary_list_type(items: List[Node]) -> str:
        """主要なリストタイプを決定"""
        type_counts: Dict[str, int] = {}

        for item in items:
            item_type = item.metadata.get("type", "unordered")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        # 最も多いタイプを返す
        if type_counts:
            return max(type_counts, key=type_counts.get)

        return "unordered"

    @staticmethod
    def has_nested_items(items: List[Node]) -> bool:
        """ネストした項目があるかチェック"""
        for item in items:
            if item.metadata.get("relative_level", 0) > 0:
                return True
            if item.metadata.get("indent_level", 0) > 0:
                return True
        return False

    @staticmethod
    def convert_list_type(list_node: Node, target_type: str) -> Node:
        """リストタイプの変換"""
        # 新しいリストノードを作成
        new_list = create_node("list", content=list_node.content)
        new_list.metadata.update(list_node.metadata)
        new_list.metadata["type"] = target_type

        # 子項目のタイプを変更
        for child in list_node.children:
            if child.node_type == "list_item":
                child.metadata["type"] = target_type
                # タイプ固有のメタデータを更新
                if target_type == "ordered":
                    child.metadata["number"] = child.metadata.get("number", 1)
                elif target_type == "alpha":
                    child.metadata["letter"] = chr(
                        ord("a") + child.metadata.get("number", 1) - 1
                    )

        new_list.children = list_node.children
        return new_list

    @staticmethod
    def extract_checklist_status(list_node: Node) -> Dict[str, Any]:
        """チェックリストの完了状況を抽出"""
        if list_node.metadata.get("type") != "checklist":
            return {"error": "Not a checklist"}

        total_items = 0
        checked_items = 0

        def count_items(node: Node):
            nonlocal total_items, checked_items

            if node.node_type == "checklist_item":
                total_items += 1
                if node.metadata.get("checked", False):
                    checked_items += 1

            # 子項目も再帰的にカウント
            for child in node.children:
                count_items(child)

        count_items(list_node)

        completion_rate = (checked_items / total_items * 100) if total_items > 0 else 0

        return {
            "total_items": total_items,
            "checked_items": checked_items,
            "completion_rate": completion_rate,
            "is_complete": checked_items == total_items and total_items > 0,
        }

    @staticmethod
    def validate_list_structure(list_node: Node) -> List[str]:
        """リスト構造の妥当性をチェック"""
        errors = []

        if not list_node.children:
            errors.append("Empty list")
            return errors

        # リスト項目の型一貫性チェック
        expected_type = list_node.metadata.get("type")
        for i, child in enumerate(list_node.children):
            child_type = child.metadata.get("type")
            if child_type != expected_type:
                errors.append(
                    f"Inconsistent item type at index {i}: "
                    f"expected {expected_type}, got {child_type}"
                )

        # ネスト構造の妥当性チェック
        max_indent = 0
        for child in list_node.children:
            indent = child.metadata.get("indent_level", 0)
            if indent > max_indent + 1:
                errors.append(
                    f"Invalid nesting: indent jump from {max_indent} to {indent}"
                )
            max_indent = max(max_indent, indent)

        return errors

    @staticmethod
    def get_list_statistics(list_node: Node) -> Dict[str, Any]:
        """リストの統計情報を取得"""

        def analyze_node(node: Node, depth: int = 0) -> Dict[str, Any]:
            stats = {
                "total_items": 0,
                "max_depth": depth,
                "type_counts": {},
                "avg_content_length": 0,
            }

            content_lengths = []

            def traverse(n: Node, d: int):
                if n.node_type in ["list_item", "checklist_item", "definition_item"]:
                    stats["total_items"] += 1
                    stats["max_depth"] = max(stats["max_depth"], d)

                    item_type = n.metadata.get("type", "unknown")
                    stats["type_counts"][item_type] = (
                        stats["type_counts"].get(item_type, 0) + 1
                    )

                    if n.content:
                        content_lengths.append(len(str(n.content)))

                for child in n.children:
                    traverse(child, d + 1)

            traverse(node, depth)

            if content_lengths:
                stats["avg_content_length"] = sum(content_lengths) / len(
                    content_lengths
                )

            return stats

        return analyze_node(list_node)
