"""Block validation utilities for Kumihan-Formatter

This module handles validation of block structures and syntax.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .block_parser import BlockParser


class BlockValidator:
    """
    ブロック構造と構文の検証

    設計ドキュメント:
    - 記法仕様: /SPEC.md#ブロック構造
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要

    関連クラス:
    - BlockParser: 検証対象のパーサー
    - MarkerValidator: マーカー構文検証と連携

    責務:
    - ブロックの入れ子構造検証
    - マーカー対応の検証
    - エラーメッセージの生成
    """

    def __init__(self, block_parser: "BlockParser") -> None:
        self.block_parser = block_parser

    def validate_document_structure(self, lines: list[str]) -> list[str]:
        """
        Validate overall document structure

        Args:
            lines: Document lines to validate

        Returns:
            list[str]: List of validation issues
        """
        issues: list[str] = []
        open_blocks = []

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if self.block_parser.is_opening_marker(line_stripped):
                # Track opening markers
                open_blocks.append((i + 1, line_stripped))
            elif self.block_parser.is_closing_marker(line_stripped):
                # Check for matching opening marker
                if not open_blocks:
                    issues.append(f"行 {i + 1}: 対応する開始マーカーのない閉じマーカー")
                else:
                    open_blocks.pop()

        # Check for unclosed blocks
        for line_num, marker in open_blocks:
            issues.append(f"行 {line_num}: 閉じマーカーのないブロック: {marker}")

        return issues

    def validate_block_nesting(self, lines: list[str]) -> list[str]:
        """Validate block nesting rules"""
        issues: list[str] = []
        nesting_stack = []  # Stack to track nested blocks

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if self.block_parser.is_opening_marker(line_stripped):
                # Extract marker content for nesting validation
                marker_content = line_stripped[3:].strip()
                nesting_stack.append(
                    {
                        "line_num": i + 1,
                        "marker": marker_content,
                        "full_line": line_stripped,
                    }
                )

                # Check for invalid nested marker content
                if not self._is_valid_nested_marker(marker_content):
                    issues.append(
                        f"行 {i + 1}: 入れ子構造で無効なマーカー: {marker_content}"
                    )

                # Check nesting depth (limit to reasonable depth)
                if len(nesting_stack) > 10:
                    issues.append(f"行 {i + 1}: 入れ子構造が深すぎます (最大10レベル)")

            elif self.block_parser.is_closing_marker(line_stripped):
                if not nesting_stack:
                    issues.append(f"行 {i + 1}: 対応する開始マーカーのない閉じマーカー")
                else:
                    # Validate proper closing
                    _ = nesting_stack.pop()
                    # Additional validation could be added here for specific block types

        # Check for unclosed nested blocks
        for block in nesting_stack:
            issues.append(
                f"行 {block['line_num']}: 閉じマーカーのない入れ子ブロック: {block['marker']}"
            )

        return issues

    def validate_content_structure(self, content: str) -> list[str]:
        """Validate content within blocks"""
        issues = []

        # Check for invalid content patterns
        if ";;;" in content and not self._is_valid_nested_marker(content):
            issues.append("ブロック内での不正なマーカー使用")

        return issues

    def _is_valid_nested_marker(self, content: str) -> bool:
        """Check if nested markers are valid"""
        if not content:
            return True  # Empty markers are valid

        # Special markers that are always valid
        special_markers = {"目次", "画像"}
        if content in special_markers:
            return True

        # Check if content contains disallowed nested markers
        nested_marker_pattern = r";;;.*?;;;"
        if ";;;" in content:
            # Look for nested ;;; patterns within the marker content
            matches = re.findall(nested_marker_pattern, content)
            if matches:
                return False  # Nested ;;; markers are not allowed

        # Check for valid keyword patterns
        # Allow keywords separated by spaces and attributes
        parts = content.split()
        if not parts:
            return True

        # Extract first part as potential keyword
        first_part = parts[0]

        # Valid keywords from keyword parser
        valid_keywords = {
            "太字",
            "イタリック",
            "枠線",
            "ハイライト",
            "見出し1",
            "見出し2",
            "見出し3",
            "見出し4",
            "見出し5",
            "折りたたみ",
            "ネタバレ",
            "目次",
            "画像",
        }

        # If first part is a valid keyword, consider it valid
        if first_part in valid_keywords:
            return True

        # Check for attribute patterns (key=value)
        if "=" in content:
            # Allow attribute-only markers for flexibility
            return True

        # For unknown patterns, be permissive but log warning
        # This allows for future extension
        return True
