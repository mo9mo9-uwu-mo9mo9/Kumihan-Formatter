"""AST utility functions

This module provides utility functions for working with
AST nodes and node collections.
"""

from typing import Any, Dict

from .node import Node


def flatten_text_nodes(content: list[Any]) -> list[Any]:
    """Flatten consecutive text nodes in a content list"""
    if not content:
        return content

    result = []
    current_text = ""

    for item in content:
        if isinstance(item, str):
            current_text += item
        else:
            if current_text:
                result.append(current_text)
                current_text = ""
            result.append(item)

    if current_text:
        result.append(current_text)

    return result


def count_nodes_by_type(nodes: list[Node]) -> dict[str, int]:
    """Count nodes by type in a list"""
    counts: Dict[str, int] = {}
    for node in nodes:
        if isinstance(node, Node):
            counts[node.type] = counts.get(node.type, 0) + 1
    return counts


def find_all_headings(nodes: list[Node]) -> list[Node]:
    """Find all heading nodes recursively"""
    headings = []
    for node in nodes:
        if isinstance(node, Node):
            if node.is_heading():
                headings.append(node)
            # Recursively search in content
            if isinstance(node.content, list):
                headings.extend(find_all_headings(node.content))
    return headings


def validate_ast(nodes: list[Node]) -> list[str]:
    """Validate AST structure and return list of issues"""
    issues = []

    for i, node in enumerate(nodes):
        if not isinstance(node, Node):
            issues.append(
                f"Item {i} is not a Node instance: {type(node)}"
            )  # type: ignore
            continue

        if not node.type:
            issues.append(f"Node {i} has empty type")
            continue

        if node.content is None:
            issues.append(f"Node {i} ({node.type}) has None content")
            continue

        # Validate heading hierarchy
        if node.is_heading():
            level = node.get_heading_level()
            if level and not (1 <= level <= 5):
                issues.append(f"Node {i} has invalid heading level: {level}")

    return issues
