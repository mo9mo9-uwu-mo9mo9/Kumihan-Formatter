"""リストパーサー共通ユーティリティ"""

from typing import Any, Dict, List, Optional

# ノードインポート
try:
    from ....ast_nodes.node import Node
except ImportError:
    try:
        from ....ast_nodes import Node
    except ImportError:
        # フォールバック実装
        class Node:  # type: ignore
            def __init__(
                self,
                type: str,
                content: Any,
                attributes: Optional[Dict[str, Any]] = None,
            ):
                self.type = type
                self.content = content
                self.attributes = attributes or {}


class ListUtilities:
    """リストパーサー共通ユーティリティクラス"""

    @staticmethod
    def create_nodes_from_parsed_data(
        data: Any, create_items: bool = False
    ) -> List[Node]:
        """パースデータからノード作成

        Args:
            data: パース済みデータ
            create_items: アイテム作成フラグ

        Returns:
            List[Node]: 作成されたノードリスト
        """
        nodes = []

        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, list):
                    # ネストリスト
                    child_nodes = ListUtilities.create_nodes_from_parsed_data(
                        item, create_items
                    )
                    node = Node(
                        type="nested_list",
                        content=child_nodes,
                        attributes={"level": 1, "item_count": len(child_nodes)},
                    )
                    nodes.append(node)
                else:
                    # リストアイテム
                    node = Node(
                        type="list_item",
                        content=str(item).strip() if item else "",
                        attributes={"index": i, "level": 0},
                    )
                    nodes.append(node)
        else:
            # 単一アイテム
            node = Node(
                type="list_item",
                content=str(data).strip() if data else "",
                attributes={"index": 0, "level": 0},
            )
            nodes.append(node)

        return nodes

    @staticmethod
    def create_nested_nodes(data: Any, level: int) -> List[Node]:
        """ネストノード作成（レベル指定）

        Args:
            data: パース済みデータ
            level: ネストレベル

        Returns:
            List[Node]: 作成されたネストノードリスト
        """
        nodes = []

        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, list):
                    child_nodes = ListUtilities.create_nested_nodes(item, level + 1)
                    node = Node(
                        type="nested_list",
                        content=child_nodes,
                        attributes={"level": level + 1, "item_count": len(child_nodes)},
                    )
                    nodes.append(node)
                else:
                    node = Node(
                        type="list_item",
                        content=str(item).strip() if item else "",
                        attributes={"index": i, "level": level},
                    )
                    nodes.append(node)

        return nodes

    @staticmethod
    def calculate_list_depth(data: Any, current_depth: int = 0) -> int:
        """リスト深度計算

        Args:
            data: 計算対象データ
            current_depth: 現在の深度

        Returns:
            int: 最大深度
        """
        if not isinstance(data, list):
            return current_depth

        max_depth = current_depth
        for item in data:
            if isinstance(item, list):
                depth = ListUtilities.calculate_list_depth(item, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth

    @staticmethod
    def count_total_items(data: Any) -> int:
        """総アイテム数カウント

        Args:
            data: カウント対象データ

        Returns:
            int: 総アイテム数
        """
        if not isinstance(data, list):
            return 1

        count = 0
        for item in data:
            if isinstance(item, list):
                count += ListUtilities.count_total_items(item)
            else:
                count += 1

        return count
