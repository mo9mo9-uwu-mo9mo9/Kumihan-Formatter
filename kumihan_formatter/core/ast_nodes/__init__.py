"""AST Node package

本パッケージはASTノード周辺の公開エントリです。後方互換のために
工場関数・基本クラスを再エクスポートしていますが、今後は各モジュール
（`.node`, `.factories` 等）からの直接importを推奨します（#1279）。
"""

# Factory functions
from .factories import (
    create_node,
    details,
    div_box,
    emphasis,
    error_node,
    heading,
    highlight,
    image_node,
    list_item,
    ordered_list,
    paragraph,
    strong,
    unordered_list,
)

# Core classes
from .node import Node
from .node_builder import NodeBuilder

# Utility functions - temporarily commented out due to import issues
# from ...core.utilities import (
#     count_nodes_by_type,
#     find_all_headings,
#     flatten_text_nodes,
#     validate_ast,
# )

__all__ = [
    # Core classes
    "Node",
    "NodeBuilder",
    # Factory functions
    "create_node",
    "paragraph",
    "heading",
    "strong",
    "emphasis",
    "div_box",
    "highlight",
    "unordered_list",
    "ordered_list",
    "list_item",
    "details",
    "error_node",
    "image_node",
    # Utility functions - temporarily commented out due to import issues
    # "flatten_text_nodes",
    # "count_nodes_by_type",
    # "find_all_headings",
    # "validate_ast",
]
