"""
マークダウン パーサー

マークダウン構文解析・パターンマッチング機能
Issue #492 Phase 5A - markdown_converter.py分割

⚠️  DEPRECATION NOTICE - Issue #880 Phase 2C:
このMarkdownParserは非推奨です。新しい統一パーサーシステムをご利用ください:
from kumihan_formatter.core.parsing import UnifiedMarkdownParser, get_global_coordinator
"""

import re
import warnings
from typing import Any, Pattern


class MarkdownParser:
    """Markdown parsing functionality

    Handles pattern compilation and basic markdown syntax parsing
    including headings, lists, and inline elements.
    """

    def __init__(self) -> None:
        """Initialize parser with compiled patterns"""
        warnings.warn(
            "MarkdownParserは非推奨です。kumihan_formatter.core.parsing.UnifiedMarkdownParserを使用してください。",
            DeprecationWarning,
            stacklevel=2,
        )
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict[str, Pattern[str]]:
        """正規表現パターンをコンパイル"""
        return {
            # 見出し
            "h1": re.compile(r"^# (.+)$", re.MULTILINE),
            "h2": re.compile(r"^## (.+)$", re.MULTILINE),
            "h3": re.compile(r"^### (.+)$", re.MULTILINE),
            "h4": re.compile(r"^#### (.+)$", re.MULTILINE),
            "h5": re.compile(r"^##### (.+)$", re.MULTILINE),
            "h6": re.compile(r"^###### (.+)$", re.MULTILINE),
            # 強調
            "strong": re.compile(r"\*\*(.+?)\*\*"),
            "em": re.compile(r"\*(.+?)\*"),
            "strong_alt": re.compile(r"__(.+?)__"),
            "em_alt": re.compile(r"_(.+?)_"),
            # リンク
            "link": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
            # コード（インライン）
            "code": re.compile(r"`([^`]+)`"),
            # 水平線
            "hr": re.compile(r"^---+$", re.MULTILINE),
            # 番号付きリスト
            "ol_item": re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE),
            # 番号なしリスト
            "ul_item": re.compile(r"^[-*+]\s+(.+)$", re.MULTILINE),
        }

    def _convert_headings(self, text: str) -> str:
        """見出しを変換"""
        for level in range(1, 7):  # h1からh6まで
            pattern_name = f"h{level}"
            if pattern_name in self.patterns:

                def make_heading_replacer(h_level: int) -> Any:
                    def replace_heading(match: Any) -> str:
                        heading_text = match.group(1).strip()
                        # ID生成（リンク用）
                        heading_id = self._generate_heading_id(heading_text)
                        return (
                            f'<h{h_level} id="{heading_id}">{heading_text}</h{h_level}>'
                        )

                    return replace_heading

        return text

    def _generate_heading_id(self, heading_text: str) -> str:
        """見出しからIDを生成"""
        # 英数字以外を除去してIDを生成
        clean_text = re.sub(r"[^\w\s-]", "", heading_text.lower())
        clean_text = re.sub(r"[-\s]+", "-", clean_text)
        return clean_text.strip("-")

    def _convert_lists(self, text: str) -> str:
        """リストを変換"""
        lines = text.split("\n")
        result = []
        in_ul = False
        in_ol = False

        for line in lines:
            ul_match = self.patterns["ul_item"].match(line)
            ol_match = self.patterns["ol_item"].match(line)

            if ul_match:
                if not in_ul:
                    if in_ol:
                        result.append("</ol>")
                        in_ol = False
                    result.append("<ul>")
                    in_ul = True
                result.append(f"<li>{ul_match.group(1)}</li>")
            elif ol_match:
                if not in_ol:
                    if in_ul:
                        result.append("</ul>")
                        in_ul = False
                    result.append("<ol>")
                    in_ol = True
                result.append(f"<li>{ol_match.group(1)}</li>")
            else:
                if in_ul:
                    result.append("</ul>")
                    in_ul = False
                if in_ol:
                    result.append("</ol>")
                    in_ol = False
                result.append(line)

        # 最後のリストを閉じる
        if in_ul:
            result.append("</ul>")
        if in_ol:
            result.append("</ol>")

        return "\n".join(result)

    def _convert_inline_elements(self, text: str) -> str:
        """インライン要素を変換"""
        # リンク
        text = self.patterns["link"].sub(r'<a href="\2">\1</a>', text)

        # 強調（太字）
        text = self.patterns["strong"].sub(r"<strong>\1</strong>", text)
        text = self.patterns["strong_alt"].sub(r"<strong>\1</strong>", text)

        # 強調（イタリック）
        text = self.patterns["em"].sub(r"<em>\1</em>", text)
        text = self.patterns["em_alt"].sub(r"<em>\1</em>", text)

        # インラインコード
        text = self.patterns["code"].sub(r"<code>\1</code>", text)

        # 水平線
        text = self.patterns["hr"].sub("<hr>", text)

        return text
