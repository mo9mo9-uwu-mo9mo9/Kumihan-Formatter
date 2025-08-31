"""
MarkdownParser - Markdown解析クラス（Deprecated）
================================================

Issue #1215対応: 不足していたmarkdown_parserモジュールの基本実装

注意: 本モジュールは非推奨です。新規コードでは
`kumihan_formatter.parsers.unified_markdown_parser.UnifiedMarkdownParser`
の使用へ移行してください。
"""

import re
import logging
import warnings
from typing import Any, Dict, Match, Optional


class MarkdownParser:
    """Markdown解析クラス - 基本実装

    ⚠️ DEPRECATED: このクラスは非推奨です
    代わりに kumihan_formatter.parsers.unified_markdown_parser.UnifiedMarkdownParser を使用してください

    統合版では以下の機能が追加されています:
    - Node型インターフェース対応
    - MainParserとの完全互換性
    - より詳細なエラーハンドリング
    - パフォーマンス最適化
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        MarkdownParser初期化

        ⚠️ DEPRECATED: このクラスは非推奨です
        """
        warnings.warn(
            "MarkdownParser (core.parsing.markdown_parser) is deprecated. "
            "Use kumihan_formatter.parsers.unified_markdown_parser.UnifiedMarkdownParser instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 基本的なMarkdownパターン
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

    def parse(self, content: str) -> Dict[str, Any]:
        """
        Markdownコンテンツを解析

        ⚠️ DEPRECATED: このメソッドは非推奨です

        Args:
            content: 解析対象Markdownテキスト

        Returns:
            解析結果辞書
        """

        warnings.warn(
            "MarkdownParser.parse() is deprecated. "
            "Use UnifiedMarkdownParser.parse() for Node-based results.",
            DeprecationWarning,
            stacklevel=2,
        )

        try:
            lines = content.split("\n")
            elements = []

            for line_num, line in enumerate(lines, 1):
                element = self._parse_line(line, line_num)
                if element:
                    elements.append(element)

            return {
                "status": "success",
                "elements": elements,
                "total_elements": len(elements),
                "parser_type": "markdown",
                "deprecated_notice": "Use UnifiedMarkdownParser for new implementations",
            }

        except Exception as e:
            self.logger.error(f"Markdown解析中にエラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "elements": [],
                "total_elements": 0,
                "deprecated_notice": "Use UnifiedMarkdownParser for new implementations",
            }

    def _parse_line(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """行単位の解析 (レガシー実装)"""
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
        """インライン要素の処理 (レガシー実装)"""
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

    def _convert_headings(self, text: str) -> str:
        """見出し変換（互換性のため）"""

        def replace_heading(match: Match[str]) -> str:
            level = len(match.group(1))
            content = match.group(2)
            return f"<h{level}>{content}</h{level}>"

        return self.patterns["heading"].sub(replace_heading, text)

    def _generate_heading_id(self, heading_text: str) -> str:
        """見出しID生成（互換性のため）"""
        # 英数字とハイフンのみの安全なID生成
        safe_id = re.sub(r"[^\w\s-]", "", heading_text.lower())
        safe_id = re.sub(r"[\s_-]+", "-", safe_id)
        return safe_id.strip("-") or "heading"

    def _convert_lists(self, text: str) -> str:
        """リスト変換（互換性のため）"""
        lines = text.split("\n")
        result_lines = []

        for line in lines:
            list_match = self.patterns["list_item"].match(line)
            if list_match:
                result_lines.append(f"<li>{list_match.group(1)}</li>")
            else:
                result_lines.append(line)

        return "\n".join(result_lines)

    def _convert_inline_elements(self, text: str) -> str:
        """インライン要素変換（互換性のため）"""
        return self._process_inline_elements(text)
