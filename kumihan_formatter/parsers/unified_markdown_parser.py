"""Unified Markdown Parser - マークダウン解析統合パーサー

Phase2最適化により作成された統合パーサー
"""

import re
import logging
from typing import Any, Dict, List, Optional
from ..core.ast_nodes import Node, create_node


class UnifiedMarkdownParser:
    """統合マークダウンパーサー - 全マークダウン解析を統合

    core/parsing/markdown_parser.py の詳細機能を統合し、
    Node型インターフェースで統一API提供
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 詳細なMarkdownパターン (core版から移植)
        self.patterns = {
            "heading": re.compile(r"^(#{1,6})\s+(.+)$"),
            "bold": re.compile(r"\*\*([^*]+)\*\*"),
            "italic": re.compile(r"\*([^*]+)\*"),
            "code": re.compile(r"`([^`]+)`"),
            "list_item": re.compile(r"^[\s]*[-*+]\s+(.+)$"),
            "numbered_list": re.compile(r"^[\s]*\d+\.\s+(.+)$"),
            "link": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
            "image": re.compile(r"!\[([^\]]*)\]\(([^)]+)\)"),
        }

    def parse(self, content: str, context: Optional[Any] = None) -> Node:
        """マークダウン内容を解析 (統合版・詳細機能付き)"""
        try:
            # 詳細解析実行 (core版ロジック統合)
            elements = self._parse_detailed(content)

            # Node型で結果構築 (MainParserとの互換性維持)
            # metadataパラメータで適切にメタデータ設定
            metadata = {
                "parser_type": "markdown",
                "total_elements": len(elements),
                "elements": elements,
            }

            node = create_node("markdown_document", content, metadata=metadata)

            return node

        except Exception as e:
            self.logger.error(f"Unified Markdown parsing error: {e}")
            from ..core.ast_nodes import error_node

            return error_node(f"Markdown parse error: {e}")

    def _parse_detailed(self, content: str) -> List[Dict[str, Any]]:
        """詳細解析実行 (core版から移植・最適化)"""
        lines = content.split("\n")
        elements = []

        for line_num, line in enumerate(lines, 1):
            element = self._parse_line(line, line_num)
            if element:
                elements.append(element)

        return elements

    def _parse_line(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """行単位の解析 (core版から移植)"""
        line = line.strip()

        if not line:
            return None

        # 見出し
        heading_match = self.patterns["heading"].match(line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            return {
                "type": f"heading_{level}",
                "content": text,
                "line_number": line_num,
                "attributes": {"level": str(level)},
            }

        # リスト項目
        list_match = self.patterns["list_item"].match(line)
        if list_match:
            return {
                "type": "list_item",
                "content": list_match.group(1),
                "line_number": line_num,
                "attributes": {"list_type": "unordered"},
            }

        # 番号付きリスト
        numbered_match = self.patterns["numbered_list"].match(line)
        if numbered_match:
            return {
                "type": "list_item",
                "content": numbered_match.group(1),
                "line_number": line_num,
                "attributes": {"list_type": "ordered"},
            }

        # 通常の段落（インライン要素も処理）
        processed_text = self._process_inline_elements(line)
        return {
            "type": "paragraph",
            "content": processed_text,
            "line_number": line_num,
            "attributes": {},
        }

    def _process_inline_elements(self, text: str) -> str:
        """インライン要素の処理 (core版から移植)"""
        # 太字
        text = self.patterns["bold"].sub(r"<strong>\1</strong>", text)

        # イタリック
        text = self.patterns["italic"].sub(r"<em>\1</em>", text)

        # コード
        text = self.patterns["code"].sub(r"<code>\1</code>", text)

        # リンク
        text = self.patterns["link"].sub(r'<a href="\2">\1</a>', text)

        # 画像
        text = self.patterns["image"].sub(r'<img src="\2" alt="\1">', text)

        return text

    def convert_to_html(self, text: str) -> str:
        """マークダウンをHTMLに変換 (拡張実装)"""
        # 詳細なHTML変換実装
        text = self._convert_headings(text)
        text = self._convert_lists(text)
        text = self._process_inline_elements(text)
        return text

    def _convert_headings(self, text: str) -> str:
        """見出し変換 (core版から移植)"""

        def replace_heading(match: re.Match[str]) -> str:
            level = len(match.group(1))
            content = match.group(2)
            return f"<h{level}>{content}</h{level}>"

        return self.patterns["heading"].sub(replace_heading, text)

    def _convert_lists(self, text: str) -> str:
        """リスト変換 (core版から移植)"""
        lines = text.split("\n")
        result_lines = []

        for line in lines:
            list_match = self.patterns["list_item"].match(line)
            if list_match:
                result_lines.append(f"<li>{list_match.group(1)}</li>")
            else:
                result_lines.append(line)

        return "\n".join(result_lines)

    def _generate_heading_id(self, heading_text: str) -> str:
        """見出しID生成 (core版から移植)"""
        # 英数字とハイフンのみの安全なID生成
        safe_id = re.sub(r"[^\w\s-]", "", heading_text.lower())
        safe_id = re.sub(r"[\s_-]+", "-", safe_id)
        return safe_id.strip("-") or "heading"  # 基本実装
