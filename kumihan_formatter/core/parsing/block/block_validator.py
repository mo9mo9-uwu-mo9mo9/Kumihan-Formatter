"""Block validation utilities for Kumihan-Formatter

This module handles validation of block structures and syntax.
"""

# import re  # 未使用import削除（Phase 1）
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
        issues: list[str] = []

        # ;;;記法チェックは削除されました（Phase 1完了）
        # 新記法のチェックが必要な場合はここに追加します

        return issues

    def _is_valid_nested_marker(self, content: str) -> bool:
        """Check if nested markers are valid（;;;記法削除により未使用）"""
        # ;;;記法は削除されました（Phase 1完了）
        return True
