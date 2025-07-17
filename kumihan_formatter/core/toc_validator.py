"""TOC Validator class for Kumihan-Formatter

This module contains the TOC structure validation logic.
"""

from __future__ import annotations

from typing import Any


class TOCValidator:
    """
    目次構造の検証（見出しレベル・数・範囲）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#目次検証ルール
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要

    関連クラス:
    - TOCGenerator: 検証対象の目次生成クラス
    - TOCEntry: 検証対象のエントリー

    責務:
    - 見出しレベルの連続性チェック
    - 目次エントリー数の制限検証
    - 無効な目次構造の検出
    """

    def __init__(self) -> None:
        self.issues: list[str] = []

    def validate_toc_structure(self, entries: list[Any]) -> list[str]:
        """
        Validate TOC structure and return issues

        Args:
            entries: TOC entries to validate

        Returns:
            list[str]: List of validation issues
        """
        self.issues = []

        # Check for proper heading hierarchy
        self._validate_heading_hierarchy(entries)

        # Check for duplicate IDs
        self._validate_unique_ids(entries)

        # Check for empty titles
        self._validate_titles(entries)

        return self.issues

    def _validate_heading_hierarchy(self, entries: list[Any]) -> None:
        """Validate that heading levels follow proper hierarchy"""

        def check_hierarchy(entry_list: list[Any], parent_level: int = 0) -> None:
            for entry in entry_list:
                # Check if level jump is too large
                if entry.level > parent_level + 1 and parent_level > 0:
                    self.issues.append(
                        f"見出しレベルの飛び越し: h{parent_level} から h{entry.level} "
                        f"('{entry.get_text_content()}')"
                    )

                # Recursively check children
                check_hierarchy(entry.children, entry.level)

        check_hierarchy(entries)

    def _validate_unique_ids(self, entries: list[Any]) -> None:
        """Validate that all heading IDs are unique"""
        seen_ids = set()

        def check_ids(entry_list: list[Any]) -> None:
            for entry in entry_list:
                if entry.heading_id in seen_ids:
                    self.issues.append(
                        f"重複する見出しID: '{entry.heading_id}' "
                        f"('{entry.get_text_content()}')"
                    )
                else:
                    seen_ids.add(entry.heading_id)

                check_ids(entry.children)

        check_ids(entries)

    def _validate_titles(self, entries: list[Any]) -> None:
        """Validate that all entries have non-empty titles"""

        def check_titles(entry_list: list[Any]) -> None:
            for entry in entry_list:
                if not entry.get_text_content().strip():
                    self.issues.append(f"空の見出しタイトル (ID: {entry.heading_id})")

                check_titles(entry.children)

        check_titles(entries)
