"""AST Node definitions for Kumihan-Formatter

This module contains the Abstract Syntax Tree node definitions
used throughout the parsing and rendering pipeline.

This package maintains backward compatibility by re-exporting
all classes and functions from the original ast_nodes.py module.
"""

# Factory functions
from .factories import (
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
    toc_marker,
    unordered_list,
)

# Core classes
from .node import Node
from .node_builder import NodeBuilder

# Utility functions
from .utilities import (
    count_nodes_by_type,
    find_all_headings,
    flatten_text_nodes,
    validate_ast,
)

__all__ = [
    # Core classes
    "Node",
    "NodeBuilder",
    # Factory functions
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
    "toc_marker",
    # Utility functions
    "flatten_text_nodes",
    "count_nodes_by_type",
    "find_all_headings",
    "validate_ast",
]
