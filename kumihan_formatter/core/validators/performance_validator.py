"""Performance validation for Kumihan documents

This module validates performance-related aspects such as file size,
memory usage, and processing complexity.
"""

from pathlib import Path
from typing import List

from ..ast_nodes import Node
from .validation_issue import ValidationIssue


class PerformanceValidator:
    """Validator for performance-related issues"""

    def __init__(self, config: dict | None = None) -> None:  # type: ignore # type: ignore
        """Initialize performance validator"""
        self.config = config
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_ast_nodes = 100000
        self.max_nesting_depth = 10

    def validate_file_size(self, file_path: Path) -> list[ValidationIssue]:
        """Validate file size"""
        issues = []

        if file_path.exists():
            file_size = file_path.stat().st_size

            if file_size > self.max_file_size:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        category="performance",
                        message=f"File size is large ({file_size / 1024 / 1024:.1f}MB)",
                        suggestion="Consider splitting the file for better performance",
                        code="LARGE_FILE_SIZE",
                    )
                )

            if file_size == 0:
                issues.append(
                    ValidationIssue(
                        level="error",
                        category="performance",
                        message="File is empty",
                        code="EMPTY_FILE",
                    )
                )

        return issues

    def validate_ast_performance(self, ast: list[Node]) -> list[ValidationIssue]:
        """Validate AST performance characteristics"""
        issues = []

        # Check total node count
        total_nodes = len(ast)
        if total_nodes > self.max_ast_nodes:
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="performance",
                    message=f"Document has many nodes ({total_nodes})",
                    suggestion="Large documents may impact performance",
                    code="MANY_AST_NODES",
                )
            )

        # Check nesting depth
        max_depth = self._calculate_max_nesting_depth(ast)
        if max_depth > self.max_nesting_depth:
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="performance",
                    message=f"Deep nesting detected (depth: {max_depth})",
                    suggestion="Simplify document structure",
                    code="DEEP_NESTING",
                )
            )

        # Check for large blocks
        issues.extend(self._check_large_blocks(ast))

        return issues

    def validate_memory_usage(self, text: str) -> list[ValidationIssue]:
        """Validate potential memory usage"""
        issues = []

        # Check text size
        text_size = len(text.encode("utf-8"))
        if text_size > 50 * 1024 * 1024:  # 50MB
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="performance",
                    message=f"Large text size may impact memory usage ({text_size / 1024 / 1024:.1f}MB)",
                    suggestion="Consider processing in chunks",
                    code="HIGH_MEMORY_USAGE",
                )
            )

        # Check line count
        line_count = text.count("\n")
        if line_count > 100000:
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="performance",
                    message=f"Many lines in document ({line_count})",
                    suggestion="Large line counts may slow processing",
                    code="MANY_LINES",
                )
            )

        return issues

    def _calculate_max_nesting_depth(self, ast: list[Node], depth: int = 0) -> int:
        """Calculate maximum nesting depth in AST"""
        max_depth = depth

        for node in ast:
            if hasattr(node, "children") and node.children:
                child_depth = self._calculate_max_nesting_depth(
                    node.children, depth + 1
                )
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _check_large_blocks(self, ast: list[Node]) -> list[ValidationIssue]:
        """Check for large content blocks"""
        issues = []

        for i, node in enumerate(ast):
            if hasattr(node, "content") and isinstance(node.content, str):
                content_size = len(node.content)
                if content_size > 100000:  # 100KB per block
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            category="performance",
                            message=f"Large content block at position {i + 1} ({content_size} characters)",
                            suggestion="Consider breaking up large blocks",
                            code="LARGE_CONTENT_BLOCK",
                        )
                    )

        return issues
