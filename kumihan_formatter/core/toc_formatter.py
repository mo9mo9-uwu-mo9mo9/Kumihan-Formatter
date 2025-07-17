"""TOC Formatter class for Kumihan-Formatter

This module contains the TOC formatting logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .toc_generator import TOCEntry


class TOCFormatter:
    """
    目次のHTMLフォーマット（スタイル・リンク・インデント）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#目次出力形式
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - スタイル詳細: /docs/toc_styling.md

    関連クラス:
    - TOCGenerator: フォーマット対象の目次データ
    - TOCEntry: フォーマット対象のエントリー
    - HTMLFormatter: HTML整形と連携

    責務:
    - 目次のHTMLリスト生成
    - アンカーリンクの作成
    - インデントと階層表現
    - CSSクラスの付与
    """

    def __init__(self) -> None:
        pass

    def format_simple_list(self, entries: list[TOCEntry]) -> str:
        """Format TOC as a simple flat list"""
        lines: list[str] = []

        def add_entry(entry: TOCEntry) -> None:
            indent = "  " * (entry.level - 1)
            title = entry.get_text_content()
            lines.append(f"{indent}- {title}")

            for child in entry.children:
                add_entry(child)

        for entry in entries:
            add_entry(entry)

        return "\n".join(lines)

    def format_numbered_list(self, entries: list[TOCEntry]) -> str:
        """Format TOC as a numbered list"""
        lines: list[str] = []
        counters: dict[int, int] = {}  # Track counters for each level

        def add_entry(entry: TOCEntry) -> None:
            level = entry.level

            # Initialize or increment counter for this level
            if level not in counters:
                counters[level] = 1
            else:
                counters[level] += 1

            # Reset counters for deeper levels
            levels_to_reset = [l for l in counters.keys() if l > level]
            for l in levels_to_reset:
                del counters[l]

            # Build number prefix
            number_parts = []
            for i in range(1, level + 1):
                if i in counters:
                    number_parts.append(str(counters[i]))

            number = ".".join(number_parts)
            indent = "  " * (level - 1)
            title = entry.get_text_content()
            lines.append(f"{indent}{number}. {title}")

            for child in entry.children:
                add_entry(child)

        for entry in entries:
            add_entry(entry)

        return "\n".join(lines)

    def format_json(self, entries: list[TOCEntry]) -> str:
        """Format TOC as JSON structure"""
        import json

        def entry_to_dict(entry: TOCEntry) -> dict[str, Any]:
            return {
                "level": entry.level,
                "title": entry.get_text_content(),
                "id": entry.heading_id,
                "children": [entry_to_dict(child) for child in entry.children],
            }

        toc_data = [entry_to_dict(entry) for entry in entries]
        return json.dumps(toc_data, ensure_ascii=False, indent=2)
