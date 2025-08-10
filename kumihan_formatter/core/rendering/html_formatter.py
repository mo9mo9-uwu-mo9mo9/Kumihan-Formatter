"""HTML formatting utilities for Kumihan-Formatter

This module provides utilities for HTML formatting, pretty-printing,
and validation of generated HTML.
"""

import re
from typing import Any, List


class FootnoteManager:
    """脚注管理クラス"""

    def __init__(self):
        self.footnotes = []
        self._counter = 0

    def add_footnote(self, content: str) -> int:
        """脚注を追加し、番号を返す"""
        self._counter += 1
        self.footnotes.append({"number": self._counter, "content": content})
        return self._counter

    def get_footnotes(self) -> List[dict]:
        """全脚注を取得"""
        return self.footnotes

    def clear(self):
        """脚注をクリア"""
        self.footnotes = []
        self._counter = 0

    def register_footnotes(self, footnote_data: list) -> list:
        """脚注データを登録し、処理済み脚注リストを返す"""
        processed_footnotes = []
        for data in footnote_data:
            footnote_number = self.add_footnote(data.get("content", ""))
            processed_footnote = {
                "content": data.get("content", ""),
                "number": footnote_number,
                "global_number": footnote_number,
            }
            processed_footnotes.append(processed_footnote)
        return processed_footnotes


class HTMLFormatter:
    """
    HTML整形・フォーマット（Pretty-print、バリデーション、セマンティック改善）

    Phase 4対応:
    - セマンティックHTML生成の改善
    - アクセシビリティ対応
    - CSSクラス名統一化
    - カラー属性処理

    設計ドキュメント:
    - 仕様: /SPEC.md#出力形式オプション
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - レンダリング詳細: /docs/rendering.md

    関連クラス:
    - Renderer: このクラスを使用してHTML出力を整形
    - Node: 整形対象のASTノード
    - TemplateManager: テンプレートベースの整形と連携

    責務:
    - HTML文字列のインデント整形
    - タグの改行・圧縮制御
    - 空白文字の正規化
    - HTML妥当性チェック
    - セマンティックHTML生成
    - アクセシビリティ属性管理
    """

    def __init__(self, indent_size: int = 2, semantic_mode: bool = True):
        """
        Initialize HTML formatter

        Args:
            indent_size: Number of spaces per indentation level
            semantic_mode: Enable semantic HTML generation
        """
        self.indent_size = indent_size
        self.semantic_mode = semantic_mode

        # CSS class naming conventions (Issue #665 Phase 4)
        self.css_class_prefix = "kumihan"

        # Color processing support
        self.supported_color_formats = ["hex", "rgb", "rgba", "hsl", "hsla", "named"]

    def handle_special_element(
        self, keyword: str, content: str, attributes: dict[str, Any] | None = None
    ) -> str:
        """
        特殊キーワード（special_handler指定）の処理

        Args:
            keyword: キーワード名
            content: コンテンツ
            attributes: 属性辞書

        Returns:
            str: 処理済みHTML
        """
        if attributes is None:
            attributes = {}

        # footnoteキーワードの処理
        if keyword == "脚注":
            return self._handle_footnote(content, attributes)

        # 未知のspecial_handlerキーワードの場合はデフォルト処理
        return f'<span class="{self.generate_css_class(keyword)}">{content}</span>'

    def _handle_footnote(self, content: str, attributes: dict[str, Any]) -> str:
        """
        脚注キーワードの処理

        Args:
            content: 脚注内容
            attributes: 属性辞書

        Returns:
            str: 脚注プレースホルダーHTML
        """
        # FootnoteManagerの共有インスタンスを取得または作成
        if not hasattr(self, "_footnote_manager"):
            self._footnote_manager = FootnoteManager()

        footnote_manager = self._footnote_manager

        # 脚注データを作成
        footnote_data = {
            "content": content,
            "number": None,  # FootnoteManagerが自動採番
        }

        # 脚注を登録
        processed_footnotes = footnote_manager.register_footnotes([footnote_data])

        if processed_footnotes:
            footnote = processed_footnotes[0]
            footnote_number = footnote.get("global_number", 1)

            # 本文中に挿入する脚注リンクプレースホルダーを生成
            placeholder = (
                f'<sup><a href="#footnote-{footnote_number}" '
                f'id="footnote-ref-{footnote_number}" class="footnote-ref">'
                f"[{footnote_number}]</a></sup>"
            )

            return placeholder

        # エラー時のフォールバック
        return f'<span class="footnote-error">[脚注エラー: {content}]</span>'

    def format_html(self, html: str, preserve_inline: bool = True) -> str:
        """
        Format HTML with proper indentation

        Args:
            html: Raw HTML string
            preserve_inline: Whether to preserve inline elements on same line

        Returns:
            str: Formatted HTML
        """
        if not html.strip():
            return html

        # Split into tokens
        tokens = self._tokenize_html(html)

        # Format with indentation
        formatted_lines = []
        indent_level = 0

        for token in tokens:
            if self._is_closing_tag(token):
                indent_level = max(0, indent_level - 1)

            if token.strip():
                indent = " " * (indent_level * self.indent_size)
                formatted_lines.append(f"{indent}{token.strip()}")

            if self._is_opening_tag(token) and not self._is_self_closing_tag(token):
                if not preserve_inline or not self._is_inline_element(token):
                    indent_level += 1

        return "\n".join(formatted_lines)

    def minify_html(self, html: str) -> str:
        """
        Minify HTML by removing unnecessary whitespace

        Args:
            html: HTML to minify

        Returns:
            str: Minified HTML
        """
        # Remove comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # Remove extra whitespace
        html = re.sub(r"\s+", " ", html)

        # Remove whitespace around tags
        html = re.sub(r">\s+<", "><", html)

        return html.strip()

    def validate_html_structure(self, html: str) -> list[str]:
        """
        Validate HTML structure and return list of issues

        Args:
            html: HTML to validate

        Returns:
            list[str]: List of validation issues
        """
        issues = []

        # Check for unclosed tags
        tags = self._extract_tags(html)
        tag_stack: List[str] = []

        for tag in tags:
            if self._is_self_closing_tag(tag):
                continue
            elif self._is_closing_tag(tag):
                tag_name = self._extract_tag_name(tag).lstrip("/")
                if not tag_stack:
                    issues.append(f"Closing tag without opening: {tag}")
                elif tag_stack[-1] != tag_name:
                    issues.append(f"Mismatched tags: expected {tag_stack[-1]}, got {tag_name}")
                else:
                    tag_stack.pop()
            else:
                tag_name = self._extract_tag_name(tag)
                tag_stack.append(tag_name)

        # Check for unclosed tags
        for tag in tag_stack:
            issues.append(f"Unclosed tag: {tag}")

        return issues

    def extract_text_content(self, html: str) -> str:
        """
        Extract plain text content from HTML

        Args:
            html: HTML string

        Returns:
            str: Plain text content
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)

        # Replace HTML entities
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')
        text = text.replace("&#x27;", "'")

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def generate_css_class(self, element_type: str, modifier: str = "") -> str:
        """
        Generate standardized CSS class name (Issue #665 Phase 4)

        Args:
            element_type: Type of element (e.g., 'heading', 'emphasis')
            modifier: Optional modifier (e.g., 'level-1', 'highlight')

        Returns:
            str: Standardized CSS class name
        """
        base_class = f"{self.css_class_prefix}-{element_type}"
        if modifier:
            return f"{base_class}--{modifier}"
        return base_class

    def add_accessibility_attributes(
        self, tag: str, attributes: dict[str, Any], content: str = ""
    ) -> dict[str, Any]:
        """
        Add accessibility attributes to HTML elements (Issue #665 Phase 4)

        Args:
            tag: HTML tag name
            attributes: Existing attributes dictionary
            content: Element content for generating alt text

        Returns:
            dict: Updated attributes with accessibility enhancements
        """
        updated_attributes = attributes.copy()

        # Add ARIA attributes based on element type
        if tag == "img" and "alt" not in updated_attributes:
            # Generate alt text from content or filename
            if content:
                updated_attributes["alt"] = self._generate_alt_text(content)
            else:
                updated_attributes["alt"] = ""

        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            # Add heading role for screen readers
            if "role" not in updated_attributes:
                updated_attributes["role"] = "heading"

        elif tag == "details":
            # Add expandable region role
            if "role" not in updated_attributes:
                updated_attributes["role"] = "region"

        elif tag == "code":
            # Add code role
            if "role" not in updated_attributes:
                updated_attributes["role"] = "code"

        return updated_attributes

    def process_footnote_links(self, text: str, footnotes: list[dict[str, Any]]) -> str:
        """
        テキスト内の脚注記法を適切なHTMLリンクに変換

        Args:
            text: 処理対象のテキスト
            footnotes: 脚注情報のリスト

        Returns:
            str: 脚注リンクが埋め込まれたHTML
        """
        if not footnotes:
            return text

        processed_text = text
        footnote_pattern = re.compile(r"\(\(([^)]+)\)\)")

        # 脚注記法を番号リンクに置換（後ろから処理）
        for i, footnote in enumerate(reversed(footnotes), 1):
            footnote_number = len(footnotes) - i + 1
            replacement = (
                f'<sup><a href="#footnote-{footnote_number}" '
                f'id="footnote-ref-{footnote_number}" class="footnote-ref">'
                f"[{footnote_number}]</a></sup>"
            )

            # 最後から順に置換（インデックスのずれを防ぐ）
            matches = list(footnote_pattern.finditer(processed_text))
            if matches and len(matches) >= footnote_number:
                match = matches[footnote_number - 1]
                processed_text = (
                    processed_text[: match.start()] + replacement + processed_text[match.end() :]
                )

        return processed_text

    def _escape_html_content(self, content: str) -> str:
        """
        HTMLコンテンツのエスケープ処理

        Args:
            content: エスケープ対象のコンテンツ

        Returns:
            str: エスケープ済みコンテンツ
        """
        import html

        return html.escape(content, quote=True)

    def _tokenize_html(self, html: str) -> list[str]:
        """
        Tokenize HTML into tags and text content

        Args:
            html: HTML to tokenize

        Returns:
            list[str]: List of tokens
        """
        tokens = []
        current_pos = 0

        # Find all tags
        for match in re.finditer(r"<[^>]+>", html):
            # Add text before tag
            text_before = html[current_pos : match.start()].strip()
            if text_before:
                tokens.append(text_before)

            # Add tag
            tokens.append(match.group())
            current_pos = match.end()

        # Add remaining text
        remaining_text = html[current_pos:].strip()
        if remaining_text:
            tokens.append(remaining_text)

        return tokens

    def _is_closing_tag(self, token: str) -> bool:
        """
        Check if token is a closing HTML tag

        Args:
            token: HTML token to check

        Returns:
            bool: True if token is closing tag
        """
        return token.startswith("</") and token.endswith(">")

    def _is_opening_tag(self, token: str) -> bool:
        """
        Check if token is an opening HTML tag

        Args:
            token: HTML token to check

        Returns:
            bool: True if token is opening tag
        """
        return (
            token.startswith("<")
            and token.endswith(">")
            and not token.startswith("</")
            and not token.endswith("/>")
        )

    def _is_self_closing_tag(self, token: str) -> bool:
        """
        Check if token is a self-closing HTML tag

        Args:
            token: HTML token to check

        Returns:
            bool: True if token is self-closing tag
        """
        if not token.startswith("<") or not token.endswith(">"):
            return False

        # Self-closing syntax
        if token.endswith("/>"):
            return True

        # Standard self-closing HTML elements
        self_closing_tags = {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }

        tag_name = self._extract_tag_name(token)
        return tag_name.lower() in self_closing_tags

    def _is_inline_element(self, token: str) -> bool:
        """
        Check if token represents an inline HTML element

        Args:
            token: HTML token to check

        Returns:
            bool: True if token is inline element
        """
        if not token.startswith("<") or not token.endswith(">"):
            return False

        inline_tags = {
            "a",
            "abbr",
            "acronym",
            "b",
            "bdi",
            "bdo",
            "big",
            "br",
            "button",
            "cite",
            "code",
            "dfn",
            "em",
            "i",
            "img",
            "input",
            "kbd",
            "label",
            "map",
            "mark",
            "meter",
            "noscript",
            "object",
            "output",
            "progress",
            "q",
            "ruby",
            "s",
            "samp",
            "script",
            "select",
            "small",
            "span",
            "strong",
            "sub",
            "sup",
            "textarea",
            "time",
            "tt",
            "u",
            "var",
            "wbr",
        }

        tag_name = self._extract_tag_name(token)
        return tag_name.lower() in inline_tags

    def _extract_tags(self, html: str) -> list[str]:
        """
        Extract all HTML tags from HTML string

        Args:
            html: HTML string to extract tags from

        Returns:
            list[str]: List of HTML tags
        """
        import re

        tag_pattern = re.compile(r"<[^>]+>")
        return tag_pattern.findall(html)

    def _extract_tag_name(self, tag: str) -> str:
        """
        Extract tag name from HTML tag string

        Args:
            tag: HTML tag string (e.g., '<div class="test">' or '</div>')

        Returns:
            str: Tag name (e.g., 'div')
        """
        import re

        if not tag.startswith("<") or not tag.endswith(">"):
            return ""

        # Remove angle brackets and handle closing tags
        content = tag[1:-1].strip()

        # Handle closing tags (remove /)
        if content.startswith("/"):
            content = content[1:].strip()

        # Handle self-closing tags (remove trailing /)
        if content.endswith("/"):
            content = content[:-1].strip()

        # Extract just the tag name (first word)
        tag_name_match = re.match(r"^([a-zA-Z][a-zA-Z0-9]*)", content)
        if tag_name_match:
            return tag_name_match.group(1)

        return ""

    def _generate_alt_text(self, content: str) -> str:
        """
        Generate alt text for images from content or filename

        Args:
            content: Content to generate alt text from

        Returns:
            str: Generated alt text
        """
        if not content:
            return ""

        # If content looks like a filename, use it as basis
        if "." in content and len(content.split(".")) == 2:
            name = content.split(".")[0]
            # Convert underscores and hyphens to spaces
            alt_text = name.replace("_", " ").replace("-", " ")
            # Capitalize first letter of each word
            alt_text = " ".join(word.capitalize() for word in alt_text.split())
            return alt_text

        # For other content, limit length and clean up
        alt_text = content[:100]  # Limit to 100 characters

        # Remove HTML tags if present
        import re

        alt_text = re.sub(r"<[^>]+>", "", alt_text)

        # Clean up whitespace
        alt_text = re.sub(r"\s+", " ", alt_text).strip()

        return alt_text
