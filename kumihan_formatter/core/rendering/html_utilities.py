"""
HTMLユーティリティ機能
HTMLFormatterの分割版 - ヘルパー関数モジュール
"""

import html
import logging
import re
from typing import Any, Dict, List, Optional, Union


class HTMLUtilities:
    """HTML ユーティリティクラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """ユーティリティ初期化"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self._heading_counter = 0

    def escape_html(self, text: str) -> str:
        """HTMLエスケープ"""
        if not text:
            return ""
        return html.escape(str(text), quote=True)

    def unescape_html(self, text: str) -> str:
        """HTMLアンエスケープ"""
        if not text:
            return ""
        return html.unescape(str(text))

    def heading_counter(self, value: Optional[int] = None) -> int:
        """見出しカウンター"""
        if value is not None:
            self._heading_counter = value
        return self._heading_counter

    def generate_heading_id(self, heading_text: str) -> str:
        """見出しID生成"""
        if not heading_text:
            return f"heading-{self._heading_counter}"

        # 日本語・英語対応のID生成
        heading_id = heading_text.strip().lower()

        # 特殊文字を置換
        heading_id = re.sub(
            r"[^\w\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf-]", "", heading_id
        )
        heading_id = re.sub(r"\s+", "-", heading_id)
        heading_id = heading_id.strip("-")

        # 空の場合はカウンターを使用
        if not heading_id:
            heading_id = f"heading-{self._heading_counter}"

        return heading_id

    def generate_toc_from_headings(self, headings: List[Dict[str, Any]]) -> str:
        """見出しから目次生成"""
        if not headings:
            return ""

        toc_parts = []
        toc_parts.append('<div class="table-of-contents">')
        toc_parts.append("<h3>目次</h3>")
        toc_parts.append('<ul class="toc-list">')

        for heading in headings:
            level = heading.get("level", 1)
            title = heading.get("title", "")
            heading_id = heading.get("id", self.generate_heading_id(title))

            # インデントクラス
            indent_class = f"toc-level-{level}"

            if heading_id:
                toc_item = f'<li class="{indent_class}"><a href="#{heading_id}">{self.escape_html(title)}</a></li>'
            else:
                toc_item = f'<li class="{indent_class}">{self.escape_html(title)}</li>'

            toc_parts.append(toc_item)

        toc_parts.append("</ul>")
        toc_parts.append("</div>")

        return "\n".join(toc_parts)

    def strip_html_tags(self, html_text: str) -> str:
        """HTMLタグ除去"""
        if not html_text:
            return ""

        # HTMLタグを除去
        clean_text = re.sub(r"<[^>]+>", "", html_text)

        # HTMLエンティティをデコード
        clean_text = self.unescape_html(clean_text)

        return clean_text.strip()

    def extract_text_content(self, html_text: str) -> str:
        """テキストコンテンツ抽出"""
        if not html_text:
            return ""

        # スクリプト・スタイルタグを除去
        clean_text = re.sub(
            r"<(script|style)[^>]*>.*?</\1>",
            "",
            html_text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # HTMLタグを除去
        clean_text = self.strip_html_tags(clean_text)

        # 余分な空白を整理
        clean_text = re.sub(r"\s+", " ", clean_text)

        return clean_text.strip()

    def word_count(self, text: str) -> Dict[str, int]:
        """文字数・単語数カウント"""
        if not text:
            return {"characters": 0, "words": 0, "lines": 0}

        # HTMLタグを除去
        plain_text = self.strip_html_tags(text)

        # 文字数（空白除く）
        char_count = len(re.sub(r"\s", "", plain_text))

        # 単語数（日英対応）
        # 英単語
        english_words = len(re.findall(r"\b[a-zA-Z]+\b", plain_text))
        # 日本語（ひらがな・カタカナ・漢字の塊）
        japanese_words = len(
            re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+", plain_text)
        )

        word_count = english_words + japanese_words

        # 行数
        line_count = len(plain_text.split("\n"))

        return {"characters": char_count, "words": word_count, "lines": line_count}

    def create_anchor_link(
        self, text: str, anchor_id: str, css_class: Optional[str] = None
    ) -> str:
        """アンカーリンク作成"""
        class_attr = f' class="{css_class}"' if css_class else ""
        return f'<a href="#{anchor_id}"{class_attr}>{self.escape_html(text)}</a>'

    def create_external_link(
        self,
        text: str,
        url: str,
        css_class: Optional[str] = None,
        target: str = "_blank",
        title: Optional[str] = None,
    ) -> str:
        """外部リンク作成"""
        class_attr = f' class="{css_class}"' if css_class else ""
        target_attr = f' target="{target}"' if target else ""
        title_attr = f' title="{self.escape_html(title)}"' if title else ""

        return f'<a href="{self.escape_html(url)}"{class_attr}{target_attr}{title_attr}>{self.escape_html(text)}</a>'

    def wrap_with_tag(
        self, content: str, tag: str, attributes: Optional[Dict[str, str]] = None
    ) -> str:
        """タグでラップ"""
        attr_str = ""
        if attributes:
            attrs = []
            for key, value in attributes.items():
                attrs.append(f'{key}="{self.escape_html(value)}"')
            attr_str = " " + " ".join(attrs)

        return f"<{tag}{attr_str}>{content}</{tag}>"

    def create_list_html(
        self, items: List[str], ordered: bool = False, css_class: Optional[str] = None
    ) -> str:
        """リスト HTML 作成"""
        if not items:
            return ""

        list_tag = "ol" if ordered else "ul"
        class_attr = f' class="{css_class}"' if css_class else ""

        list_items = []
        for item in items:
            list_items.append(f"<li>{self.escape_html(item)}</li>")

        return (
            f"<{list_tag}{class_attr}>\n" + "\n".join(list_items) + f"\n</{list_tag}>"
        )

    def create_table_html(
        self,
        data: List[List[str]],
        headers: Optional[List[str]] = None,
        css_class: Optional[str] = None,
    ) -> str:
        """テーブル HTML 作成"""
        if not data:
            return ""

        class_attr = f' class="{css_class}"' if css_class else ""
        table_parts = [f"<table{class_attr}>"]

        # ヘッダー
        if headers:
            table_parts.append("<thead>")
            table_parts.append("<tr>")
            for header in headers:
                table_parts.append(f"<th>{self.escape_html(header)}</th>")
            table_parts.append("</tr>")
            table_parts.append("</thead>")

        # ボディ
        table_parts.append("<tbody>")
        for row in data:
            table_parts.append("<tr>")
            for cell in row:
                table_parts.append(f"<td>{self.escape_html(cell)}</td>")
            table_parts.append("</tr>")
        table_parts.append("</tbody>")

        table_parts.append("</table>")
        return "\n".join(table_parts)

    def minify_html(self, html_text: str) -> str:
        """HTML最小化"""
        if not html_text:
            return ""

        # 改行と余分な空白を除去（pre/code内は保持）
        minified = re.sub(r">\s+<", "><", html_text)
        minified = re.sub(r"\s+", " ", minified)
        minified = minified.strip()

        return minified

    def format_html(self, html_text: str, indent: str = "  ") -> str:
        """HTML整形"""
        if not html_text:
            return ""

        # 簡易的な整形
        formatted = re.sub(r"><", ">\n<", html_text)

        lines = formatted.split("\n")
        formatted_lines = []
        indent_level = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 終了タグの場合、インデントを減らす
            if line.startswith("</") and not line.startswith("</"):
                indent_level = max(0, indent_level - 1)

            formatted_lines.append(indent * indent_level + line)

            # 開始タグの場合、インデントを増やす
            if (
                line.startswith("<")
                and not line.startswith("</")
                and not line.endswith("/>")
            ):
                # 自己完結タグでない場合
                tag_match = re.match(r"<(\w+)", line)
                if tag_match:
                    tag_name = tag_match.group(1)
                    if f"</{tag_name}>" not in line:
                        indent_level += 1

        return "\n".join(formatted_lines)

    def validate_html_syntax(self, html_text: str) -> List[str]:
        """HTML構文検証"""
        errors = []

        if not html_text:
            return errors

        # タグのバランスチェック
        stack = []
        self_closing_tags = {
            "img",
            "br",
            "hr",
            "meta",
            "link",
            "input",
            "area",
            "base",
            "col",
            "embed",
            "source",
            "track",
            "wbr",
        }

        tag_pattern = re.compile(r"<(/?)(\w+)(?:\s[^>]*)?>|<!--.*?-->", re.DOTALL)

        for match in tag_pattern.finditer(html_text):
            full_tag = match.group(0)

            # コメントはスキップ
            if full_tag.startswith("<!--"):
                continue

            is_closing = match.group(1) == "/"
            tag_name = match.group(2).lower()

            if tag_name in self_closing_tags:
                continue

            if is_closing:
                if not stack:
                    errors.append(f"対応する開始タグがありません: {full_tag}")
                elif stack[-1] != tag_name:
                    errors.append(
                        f"タグが正しく閉じられていません: <{stack[-1]}> vs {full_tag}"
                    )
                else:
                    stack.pop()
            else:
                # 自己完結タグチェック
                if full_tag.endswith("/>"):
                    continue
                stack.append(tag_name)

        # 未閉じタグ
        for tag in stack:
            errors.append(f"終了タグがありません: <{tag}>")

        return errors

    def extract_links(self, html_text: str) -> List[Dict[str, str]]:
        """リンク抽出"""
        links = []

        link_pattern = re.compile(
            r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )

        for match in link_pattern.finditer(html_text):
            url = match.group(1)
            text = self.strip_html_tags(match.group(2))

            links.append(
                {
                    "url": url,
                    "text": text,
                    "type": (
                        "external"
                        if url.startswith(("http://", "https://"))
                        else "internal"
                    ),
                }
            )

        return links

    def get_utility_info(self) -> Dict[str, Any]:
        """ユーティリティ情報取得"""
        return {
            "name": "HTMLUtilities",
            "version": "1.0.0",
            "features": [
                "html_escaping",
                "heading_management",
                "toc_generation",
                "text_extraction",
                "html_formatting",
                "syntax_validation",
            ],
            "heading_counter": self._heading_counter,
        }
