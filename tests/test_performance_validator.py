"""Tests for performance validator module

This module tests performance validation functionality including file size,
memory usage, and processing complexity validation.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.validators.performance_validator import PerformanceValidator
from kumihan_formatter.core.validators.validation_issue import ValidationIssue


class TestPerformanceValidator:
    """Test performance validator functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.validator = PerformanceValidator()

    def test_init_without_config(self):
        """Test validator initialization without config"""
        validator = PerformanceValidator()
        assert isinstance(validator, PerformanceValidator)
        assert validator.config is None
        assert validator.max_file_size == 10 * 1024 * 1024  # 10MB
        assert validator.max_ast_nodes == 100000
        assert validator.max_nesting_depth == 10

    def test_init_with_config(self):
        """Test validator initialization with config"""
        config = {"test": "value"}
        validator = PerformanceValidator(config)
        assert validator.config == config

    def test_validate_file_size_normal(self):
        """Test validation of normal-sized file"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Normal content")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                issues = self.validator.validate_file_size(file_path)

                # Should have no issues for normal-sized file
                size_issues = [
                    issue
                    for issue in issues
                    if issue.code in ["LARGE_FILE_SIZE", "EMPTY_FILE"]
                ]
                assert len(size_issues) == 0
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_file_size_empty(self):
        """Test validation of empty file"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            # Don't write anything - file is empty
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                issues = self.validator.validate_file_size(file_path)

                # Should have empty file error
                empty_issues = [issue for issue in issues if issue.code == "EMPTY_FILE"]
                assert len(empty_issues) == 1
                assert empty_issues[0].level == "error"
                assert empty_issues[0].category == "performance"
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_file_size_large(self):
        """Test validation of large file (using patch)"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Content")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)

                # Mock stat to return large size
                from unittest.mock import patch

                with patch.object(Path, "stat") as mock_stat:
                    mock_stat_result = Mock()
                    mock_stat_result.st_size = 20 * 1024 * 1024  # 20MB
                    mock_stat.return_value = mock_stat_result

                    issues = self.validator.validate_file_size(file_path)

                    # Should have large file warning
                    large_issues = [
                        issue for issue in issues if issue.code == "LARGE_FILE_SIZE"
                    ]
                    assert len(large_issues) == 1
                    assert large_issues[0].level == "warning"
                    assert large_issues[0].category == "performance"
                    assert "20.0MB" in large_issues[0].message
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_file_size_nonexistent(self):
        """Test validation of non-existent file"""
        # Use platform-agnostic path that doesn't exist
        non_existent_file = Path(tempfile.gettempdir()) / "non_existent_test_file.txt"
        issues = self.validator.validate_file_size(non_existent_file)

        # Should have no issues (file doesn't exist to check)
        assert len(issues) == 0

    def test_validate_ast_performance_normal(self):
        """Test validation of normal AST"""
        # Create small AST with normal characteristics
        mock_nodes = []
        for i in range(10):
            mock_node = Mock(spec=Node)
            mock_node.content = f"Content {i}"
            mock_node.children = []  # Ensure children is a list, not Mock
            mock_nodes.append(mock_node)

        issues = self.validator.validate_ast_performance(mock_nodes)

        # Should have no performance issues
        perf_issues = [
            issue
            for issue in issues
            if issue.code in ["MANY_AST_NODES", "DEEP_NESTING"]
        ]
        assert len(perf_issues) == 0

    def test_validate_ast_performance_many_nodes(self):
        """Test validation of AST with many nodes"""
        # Create AST with too many nodes
        mock_nodes = []
        for i in range(100001):
            mock_node = Mock(spec=Node)
            mock_node.children = []  # Ensure children is a list, not Mock
            mock_nodes.append(mock_node)

        issues = self.validator.validate_ast_performance(mock_nodes)

        # Should have many nodes warning
        many_nodes_issues = [
            issue for issue in issues if issue.code == "MANY_AST_NODES"
        ]
        assert len(many_nodes_issues) == 1
        assert many_nodes_issues[0].level == "warning"
        assert many_nodes_issues[0].category == "performance"
        assert "100001" in many_nodes_issues[0].message

    def test_validate_ast_performance_deep_nesting(self):
        """Test validation of deeply nested AST"""
        # Create deeply nested structure
        root_node = Mock(spec=Node)
        current_node = root_node

        # Create 12 levels of nesting (exceeds max of 10)
        for i in range(12):
            child_node = Mock(spec=Node)
            child_node.children = []
            current_node.children = [child_node]
            current_node = child_node

        issues = self.validator.validate_ast_performance([root_node])

        # Should have deep nesting warning
        deep_nesting_issues = [
            issue for issue in issues if issue.code == "DEEP_NESTING"
        ]
        assert len(deep_nesting_issues) == 1
        assert deep_nesting_issues[0].level == "warning"
        assert "depth: 12" in deep_nesting_issues[0].message

    def test_validate_ast_performance_large_blocks(self):
        """Test validation of AST with large content blocks"""
        mock_node = Mock(spec=Node)
        mock_node.content = "x" * 100001  # 100KB+ content
        mock_node.children = []  # Ensure children is a list, not Mock

        issues = self.validator.validate_ast_performance([mock_node])

        # Should have large content block warning
        large_block_issues = [
            issue for issue in issues if issue.code == "LARGE_CONTENT_BLOCK"
        ]
        assert len(large_block_issues) == 1
        assert large_block_issues[0].level == "warning"
        assert "100001 characters" in large_block_issues[0].message

    def test_validate_memory_usage_normal(self):
        """Test validation of normal text memory usage"""
        normal_text = "This is normal text content"
        issues = self.validator.validate_memory_usage(normal_text)

        # Should have no memory issues
        memory_issues = [
            issue
            for issue in issues
            if issue.code in ["HIGH_MEMORY_USAGE", "MANY_LINES"]
        ]
        assert len(memory_issues) == 0

    def test_validate_memory_usage_large_text(self):
        """Test validation of large text"""
        # Create text larger than 50MB (simplified simulation)
        large_text = "x" * (51 * 1024 * 1024)  # 51MB of text
        issues = self.validator.validate_memory_usage(large_text)

        # Should have high memory usage warning
        memory_issues = [issue for issue in issues if issue.code == "HIGH_MEMORY_USAGE"]
        assert len(memory_issues) == 1
        assert memory_issues[0].level == "warning"
        assert memory_issues[0].category == "performance"

    def test_validate_memory_usage_moderate_text_for_ci(self):
        """Test validation of moderate-sized text for CI environments"""
        # CI-friendly test with smaller memory footprint
        moderate_text = "Content line\n" * 50000  # ~650KB instead of 50MB
        issues = self.validator.validate_memory_usage(moderate_text)
        
        # Should not trigger high memory usage warning for moderate size
        memory_issues = [issue for issue in issues if issue.code == "HIGH_MEMORY_USAGE"]
        assert len(memory_issues) == 0
        
        # But might trigger many lines warning
        line_issues = [issue for issue in issues if issue.code == "MANY_LINES"]
        # 50000 lines should not trigger warning (threshold is 100000)
        assert len(line_issues) == 0

    def test_validate_memory_usage_many_lines(self):
        """Test validation of text with many lines"""
        # Create text with many lines
        many_lines_text = "\n" * 100001  # 100,001 newlines
        issues = self.validator.validate_memory_usage(many_lines_text)

        # Should have many lines warning
        line_issues = [issue for issue in issues if issue.code == "MANY_LINES"]
        assert len(line_issues) == 1
        assert line_issues[0].level == "warning"
        assert "100001" in line_issues[0].message

    def test_calculate_max_nesting_depth_flat(self):
        """Test calculation of nesting depth for flat structure"""
        # Create flat structure (no children)
        mock_nodes = []
        for i in range(5):
            mock_node = Mock(spec=Node)
            mock_node.children = []
            mock_nodes.append(mock_node)

        depth = self.validator._calculate_max_nesting_depth(mock_nodes)
        assert depth == 0

    def test_calculate_max_nesting_depth_nested(self):
        """Test calculation of nesting depth for nested structure"""
        # Create nested structure: root -> child -> grandchild
        grandchild = Mock(spec=Node)
        grandchild.children = []

        child = Mock(spec=Node)
        child.children = [grandchild]

        root = Mock(spec=Node)
        root.children = [child]

        depth = self.validator._calculate_max_nesting_depth([root])
        assert depth == 2  # root (0) -> child (1) -> grandchild (2)

    def test_calculate_max_nesting_depth_no_children_attribute(self):
        """Test depth calculation when nodes don't have children attribute"""
        mock_node = Mock(spec=Node)
        # Don't set children attribute, but ensure the Mock doesn't have it
        if hasattr(mock_node, "children"):
            delattr(mock_node, "children")

        depth = self.validator._calculate_max_nesting_depth([mock_node])
        assert depth == 0

    def test_check_large_blocks_normal(self):
        """Test checking for large blocks with normal content"""
        mock_nodes = []
        for i in range(3):
            mock_node = Mock(spec=Node)
            mock_node.content = f"Normal content {i}"
            mock_nodes.append(mock_node)

        issues = self.validator._check_large_blocks(mock_nodes)
        assert len(issues) == 0

    def test_check_large_blocks_large_content(self):
        """Test checking for large blocks with large content"""
        mock_node = Mock(spec=Node)
        mock_node.content = "x" * 100001  # Large content

        issues = self.validator._check_large_blocks([mock_node])

        assert len(issues) == 1
        assert issues[0].code == "LARGE_CONTENT_BLOCK"
        assert "position 1" in issues[0].message
        assert "100001 characters" in issues[0].message

    def test_check_large_blocks_no_content_attribute(self):
        """Test checking blocks when nodes don't have content attribute"""
        mock_node = Mock(spec=Node)
        # Don't set content attribute

        issues = self.validator._check_large_blocks([mock_node])
        assert len(issues) == 0

    def test_check_large_blocks_non_string_content(self):
        """Test checking blocks when content is not a string"""
        mock_node = Mock(spec=Node)
        mock_node.content = 12345  # Non-string content

        issues = self.validator._check_large_blocks([mock_node])
        assert len(issues) == 0

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Empty AST
        issues = self.validator.validate_ast_performance([])
        assert len(issues) == 0

        # Empty text
        issues = self.validator.validate_memory_usage("")
        assert len(issues) == 0

        # Exactly at threshold values
        exact_threshold_nodes = []
        for i in range(100000):
            mock_node = Mock(spec=Node)
            mock_node.children = []
            exact_threshold_nodes.append(mock_node)

        issues = self.validator.validate_ast_performance(exact_threshold_nodes)
        many_nodes_issues = [
            issue for issue in issues if issue.code == "MANY_AST_NODES"
        ]
        assert len(many_nodes_issues) == 0  # Exactly at threshold, not over

    def test_performance_scalability_ci_friendly(self):
        """Test performance with CI-friendly smaller datasets"""
        # Test with smaller node counts for CI efficiency
        moderate_node_count = 50000  # Half the threshold
        moderate_nodes = []
        for i in range(moderate_node_count):
            mock_node = Mock(spec=Node)
            mock_node.children = []
            mock_node.content = f"Node {i}"  # Small content
            moderate_nodes.append(mock_node)
        
        issues = self.validator.validate_ast_performance(moderate_nodes)
        
        # Should not trigger any performance warnings
        perf_issues = [
            issue for issue in issues 
            if issue.code in ["MANY_AST_NODES", "DEEP_NESTING", "LARGE_CONTENT_BLOCK"]
        ]
        assert len(perf_issues) == 0
        
        # Test memory efficiency
        text_size_kb = len(str(moderate_nodes)) / 1024
        assert text_size_kb < 10240  # Should be under 10MB for CI

    def test_multiple_performance_issues(self):
        """Test AST with multiple performance issues"""
        # Create AST with many nodes AND deep nesting AND large blocks
        large_content_node = Mock(spec=Node)
        large_content_node.content = "x" * 100001
        large_content_node.children = []

        # Create many nodes
        many_nodes = []
        for i in range(100001):
            mock_node = Mock(spec=Node)
            mock_node.children = []
            many_nodes.append(mock_node)

        many_nodes.append(large_content_node)

        # Create deep nesting
        root_node = Mock(spec=Node)
        current_node = root_node
        for i in range(12):  # Deep nesting
            child_node = Mock(spec=Node)
            child_node.children = []
            current_node.children = [child_node]
            current_node = child_node

        many_nodes.append(root_node)

        issues = self.validator.validate_ast_performance(many_nodes)

        # Should have multiple types of issues
        many_nodes_issues = [
            issue for issue in issues if issue.code == "MANY_AST_NODES"
        ]
        deep_nesting_issues = [
            issue for issue in issues if issue.code == "DEEP_NESTING"
        ]
        large_block_issues = [
            issue for issue in issues if issue.code == "LARGE_CONTENT_BLOCK"
        ]

        assert len(many_nodes_issues) == 1
        assert len(deep_nesting_issues) == 1
        assert len(large_block_issues) == 1

    def test_validation_issue_properties(self):
        """Test that validation issues have correct properties"""
        # Create condition that generates issues
        large_text = "x" * (51 * 1024 * 1024)
        issues = self.validator.validate_memory_usage(large_text)

        for issue in issues:
            assert isinstance(issue, ValidationIssue)
            assert issue.level in ["error", "warning", "info"]
            assert issue.category == "performance"
            assert isinstance(issue.message, str)
            assert len(issue.message) > 0
            if issue.code:
                assert isinstance(issue.code, str)
