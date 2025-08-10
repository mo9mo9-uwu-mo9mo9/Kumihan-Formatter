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

        # Check for required fields first
        self._validate_required_fields(entries)

        # Check for proper heading hierarchy
        self._validate_heading_hierarchy(entries)

        # Check for duplicate IDs
        self._validate_unique_ids(entries)

        # Check for empty titles
        self._validate_titles(entries)

        return self.issues

    def _validate_required_fields(self, entries: list[Any]) -> None:
        """Validate that all entries have required fields"""

        def check_required_fields(entry_list: list[Any]) -> None:
            for i, entry in enumerate(entry_list):
                if isinstance(entry, dict):
                    self._validate_dict_entry(entry, i)
                    children = entry.get("children", [])
                    if children:
                        check_required_fields(children)
                elif hasattr(entry, "level") and hasattr(entry, "heading_id"):
                    children = getattr(entry, "children", [])
                    if children:
                        check_required_fields(children)
                else:
                    self.issues.append(f"エントリー {i}: Invalid entry format or structure")

        check_required_fields(entries)

    def _validate_dict_entry(self, entry: dict[str, Any], index: int) -> None:
        """Validate a single dictionary entry"""
        # Check for required fields
        self._check_required_fields(entry, index)

        # Validate level type and range
        self._validate_level_field(entry, index)

        # Validate ID format and content
        self._validate_id_field(entry, index)

    def _check_required_fields(self, entry: dict[str, Any], index: int) -> None:
        """Check if all required fields are present"""
        if "title" not in entry:
            self.issues.append(f"エントリー {index}: 必須フィールド 'title' が見つかりません")
        if "level" not in entry:
            self.issues.append(f"エントリー {index}: 必須フィールド 'level' が見つかりません")
        if "id" not in entry:
            self.issues.append(f"エントリー {index}: 必須フィールド 'id' が見つかりません")

    def _validate_level_field(self, entry: dict[str, Any], index: int) -> None:
        """Validate level field type and range"""
        level = entry.get("level")
        if level is not None:
            if not isinstance(level, int):
                msg = (
                    f"エントリー {index}: invalid level type - 'level' は整数である"
                    f"必要があります（現在: {type(level).__name__}）"
                )
                self.issues.append(msg)
            elif level < 1 or level > 6:
                msg = (
                    f"エントリー {index}: invalid level range - 'level' は1から6の"
                    f"間である必要があります（現在: {level}）"
                )
                self.issues.append(msg)

    def _validate_id_field(self, entry: dict[str, Any], index: int) -> None:
        """Validate ID field format and content"""
        id_value = entry.get("id")
        if id_value is not None:
            if not id_value or not str(id_value).strip():
                self.issues.append(f"エントリー {index}: Empty ID detected")
            elif not isinstance(id_value, str):
                self.issues.append(f"エントリー {index}: Invalid ID format - ID must be string")
            elif not self._is_valid_id_format(str(id_value)):
                self.issues.append(f"エントリー {index}: Invalid ID format - '{id_value}'")

    def _is_valid_id_format(self, id_value: str) -> bool:
        """Check if ID has valid format (basic validation)"""
        # Basic validation: should contain only alphanumeric, hyphens, underscores
        import re

        return bool(re.match(r"^[a-zA-Z0-9_-]+$", id_value))

    def _validate_heading_hierarchy(self, entries: list[Any]) -> None:
        """Validate that heading levels follow proper hierarchy"""

        def check_hierarchy(entry_list: list[Any], parent_level: int = 0) -> None:
            for entry in entry_list:
                # Get level from dict/object with validation
                if isinstance(entry, dict):
                    entry_level = entry.get("level")
                    title = entry.get("title", "Unknown")
                else:
                    entry_level = getattr(entry, "level", None)
                    title = getattr(entry, "get_text_content", lambda: "Unknown")()

                # Skip hierarchy check if level is invalid
                if not isinstance(entry_level, int):
                    continue

                # Check if level jump is too large
                if entry_level > parent_level + 1 and parent_level > 0:
                    self.issues.append(
                        f"見出しレベルの飛び越し: h{parent_level} から h{entry_level} "
                        f"('{title}')"
                    )

                # Recursively check children if they exist
                children = (
                    entry.get("children", [])
                    if isinstance(entry, dict)
                    else getattr(entry, "children", [])
                )
                check_hierarchy(children, entry_level)

        check_hierarchy(entries)

    def _validate_unique_ids(self, entries: list[Any]) -> None:
        """Validate that all heading IDs are unique"""
        seen_ids = set()

        def check_ids(entry_list: list[Any]) -> None:
            for entry in entry_list:
                # Get heading ID from dict/object
                if isinstance(entry, dict):
                    heading_id = entry.get("id")
                    title = entry.get("title", "Unknown")
                else:
                    heading_id = getattr(entry, "heading_id", None)
                    title = getattr(entry, "get_text_content", lambda: "Unknown")()

                # Skip if ID is None or empty
                if not heading_id:
                    continue

                if heading_id in seen_ids:
                    self.issues.append(f"重複する見出しID: '{heading_id}' " f"('{title}')")
                else:
                    seen_ids.add(heading_id)

                # Check children if they exist
                children = (
                    entry.get("children", [])
                    if isinstance(entry, dict)
                    else getattr(entry, "children", [])
                )
                check_ids(children)

        check_ids(entries)

    def _validate_titles(self, entries: list[Any]) -> None:
        """Validate that all entries have non-empty titles"""

        def check_titles(entry_list: list[Any]) -> None:
            for entry in entry_list:
                # Get title and ID from dict/object
                if isinstance(entry, dict):
                    title = entry.get("title", "")
                    heading_id = entry.get("id", "Unknown")
                else:
                    title = getattr(entry, "get_text_content", lambda: "")()
                    heading_id = getattr(entry, "heading_id", "Unknown")

                if not title or not title.strip():
                    self.issues.append(f"Empty title detected (ID: {heading_id})")

                # Check children if they exist
                children = (
                    entry.get("children", [])
                    if isinstance(entry, dict)
                    else getattr(entry, "children", [])
                )
                check_titles(children)

        check_titles(entries)
