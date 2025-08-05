"""HTML formatting utilities for Kumihan-Formatter

This module provides utilities for HTML formatting, pretty-printing,
and validation of generated HTML.
"""

import re
from typing import List


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
                    issues.append(
                        f"Mismatched tags: expected {tag_stack[-1]}, got {tag_name}"
                    )
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
        self, tag: str, attributes: dict, content: str = ""
    ) -> dict:
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

    def generate_footnotes_html(self, footnotes: list[dict]) -> str:
        """
        脚注リストからHTML形式の脚注セクションを生成

        Args:
            footnotes: 脚注情報のリスト

        Returns:
            str: 脚注セクションHTML
        """
        if not footnotes:
            return ""

        footnotes_html = ['<div class="footnotes">', "<ol>"]

        for footnote in footnotes:
            footnote_number = footnote.get("number", 1)
            footnote_content = footnote.get("content", "")

            # HTMLエスケープ処理
            escaped_content = self._escape_html_content(footnote_content)

            # 戻りリンクを含む脚注項目
            footnote_item = (
                f'<li id="footnote-{footnote_number}">'
                f"{escaped_content} "
                f'<a href="#footnote-ref-{footnote_number}" class="footnote-backref">↩</a>'
                f"</li>"
            )
            footnotes_html.append(footnote_item)

        footnotes_html.extend(["</ol>", "</div>"])
        return "\n".join(footnotes_html)

    def process_footnote_links(self, text: str, footnotes: list[dict]) -> str:
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
                    processed_text[: match.start()]
                    + replacement
                    + processed_text[match.end() :]
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


class FootnoteManager:
    """
    脚注番号管理および処理を行うクラス

    複数ファイル間での脚注番号管理と、HTML出力の統一的な処理を提供
    """

    def __init__(self):
        self.footnote_counter = 0
        self.footnotes_storage = []
        self.footnote_references = {}

    def register_footnotes(self, footnotes: list[dict]) -> list[dict]:
        """
        脚注を登録し、グローバル番号を割り当て

        Args:
            footnotes: 脚注情報のリスト

        Returns:
            list[dict]: 番号が割り当てられた脚注リスト
        """
        processed_footnotes = []

        for footnote in footnotes:
            self.footnote_counter += 1
            processed_footnote = footnote.copy()
            processed_footnote["global_number"] = self.footnote_counter
            processed_footnotes.append(processed_footnote)
            self.footnotes_storage.append(processed_footnote)

        return processed_footnotes

    def get_all_footnotes(self) -> list[dict]:
        """
        登録されたすべての脚注を取得

        Returns:
            list[dict]: 全脚注情報
        """
        return self.footnotes_storage.copy()

    def reset_counter(self):
        """
        脚注カウンターをリセット（新しいドキュメント開始時に使用）
        """
        self.footnote_counter = 0
        self.footnotes_storage.clear()
        self.footnote_references.clear()

    def generate_footnote_html(self, footnotes: list[dict]) -> str:
        """
        脚注のHTML生成

        Args:
            footnotes: 脚注情報のリスト

        Returns:
            str: 脚注セクションHTML
        """
        if not footnotes:
            return ""

        html_parts = ['<div class="footnotes">', "<ol>"]

        for footnote in footnotes:
            number = footnote.get("global_number", footnote.get("number", 1))
            content = footnote.get("content", "")

            # セキュアなHTMLエスケープ
            import html

            escaped_content = html.escape(content, quote=True)

            footnote_html = (
                f'<li id="footnote-{number}">'
                f"{escaped_content} "
                f'<a href="#footnote-ref-{number}" class="footnote-backref" '
                f'aria-label="戻る">↩</a>'
                f"</li>"
            )
            html_parts.append(footnote_html)

        html_parts.extend(["</ol>", "</div>"])
        return "\n".join(html_parts)

    def validate_footnote_data(self, footnotes: list[dict]) -> tuple[bool, list[str]]:
        """
        脚注データの妥当性検証

        Args:
            footnotes: 検証対象の脚注リスト

        Returns:
            tuple: (検証結果, エラーメッセージリスト)
        """
        errors = []

        if not isinstance(footnotes, list):
            errors.append("脚注データはリスト形式である必要があります")
            return False, errors

        for i, footnote in enumerate(footnotes, 1):
            if not isinstance(footnote, dict):
                errors.append(f"脚注{i}: 辞書形式である必要があります")
                continue

            # 必須フィールドの確認
            required_fields = ["content"]
            for field in required_fields:
                if field not in footnote:
                    errors.append(f"脚注{i}: 必須フィールド'{field}'が不足しています")

            # コンテンツの検証
            content = footnote.get("content", "")
            if not isinstance(content, str):
                errors.append(f"脚注{i}: コンテンツは文字列である必要があります")
            elif len(content.strip()) == 0:
                errors.append(f"脚注{i}: コンテンツが空です")
            elif len(content) > 2000:
                errors.append(
                    f"脚注{i}: コンテンツが長すぎます（{len(content)}/2000文字）"
                )

            # 番号の検証
            number = footnote.get("number")
            if number is not None and (not isinstance(number, int) or number < 1):
                errors.append(f"脚注{i}: 番号は1以上の整数である必要があります")

        return len(errors) == 0, errors

    def safe_generate_footnote_html(
        self, footnotes: list[dict]
    ) -> tuple[str, list[str]]:
        """
        安全な脚注HTML生成（エラーハンドリング付き）

        Args:
            footnotes: 脚注情報のリスト

        Returns:
            tuple: (生成されたHTML, エラーメッセージリスト)
        """
        errors = []

        try:
            # データ検証
            is_valid, validation_errors = self.validate_footnote_data(footnotes)
            if not is_valid:
                errors.extend(validation_errors)
                return "", errors

            # 空の場合の処理
            if not footnotes:
                return "", errors

            html_parts = ['<div class="footnotes" role="doc-endnotes">', "<ol>"]

            for footnote in footnotes:
                try:
                    number = footnote.get("global_number", footnote.get("number", 1))
                    content = footnote.get("content", "")

                    # セキュアなHTMLエスケープ
                    import html

                    escaped_content = html.escape(content, quote=True)

                    # XSS攻撃の追加防御
                    escaped_content = self._additional_xss_protection(escaped_content)

                    footnote_html = (
                        f'<li id="footnote-{number}" role="doc-endnote">'
                        f"{escaped_content} "
                        f'<a href="#footnote-ref-{number}" class="footnote-backref" '
                        f'role="doc-backlink" aria-label="本文に戻る">↩</a>'
                        f"</li>"
                    )
                    html_parts.append(footnote_html)

                except Exception as e:
                    errors.append(f"脚注{number}の処理中にエラー: {str(e)}")
                    continue

            html_parts.extend(["</ol>", "</div>"])
            return "\n".join(html_parts), errors

        except Exception as e:
            errors.append(f"脚注HTML生成中の予期しないエラー: {str(e)}")
            return "", errors

    def _additional_xss_protection(self, content: str) -> str:
        """
        追加のXSS保護処理

        Args:
            content: 保護対象のコンテンツ

        Returns:
            str: 保護されたコンテンツ
        """
        # すでにエスケープされた内容に対する追加保護
        dangerous_patterns = [
            (r"&lt;script", "&amp;lt;script"),
            (r"&lt;iframe", "&amp;lt;iframe"),
            (r"&lt;object", "&amp;lt;object"),
            (r"&lt;embed", "&amp;lt;embed"),
            (r"javascript:", "blocked:"),
            (r"vbscript:", "blocked:"),
            (r"data:", "blocked:"),
        ]

        for pattern, replacement in dangerous_patterns:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        return content

    def process_color_attribute(self, color: str) -> str:
        """
        Process and validate color attribute values (Issue #665 Phase 4)

        Args:
            color: Color value in various formats

        Returns:
            str: Processed and validated color value
        """
        if not color:
            return ""

        color = color.strip()

        # Hex color validation and normalization
        if color.startswith("#"):
            return self._process_hex_color(color)

        # RGB/RGBA validation
        elif color.startswith(("rgb(", "rgba(")):
            return self._process_rgb_color(color)

        # HSL/HSLA validation
        elif color.startswith(("hsl(", "hsla(")):
            return self._process_hsl_color(color)

        # Named colors
        elif self._is_named_color(color):
            return color.lower()

        # Invalid color - return empty string
        return ""

    def _generate_alt_text(self, content: str) -> str:
        """Generate meaningful alt text from content"""
        if not content:
            return ""

        # If it's a filename, extract meaningful part
        if "." in content:
            base_name = content.split(".")[0]
            # Replace underscores and hyphens with spaces
            return base_name.replace("_", " ").replace("-", " ").strip()

        return content[:100]  # Limit alt text length

    def _process_hex_color(self, color: str) -> str:
        """Process hex color format"""
        # Remove # and validate
        hex_part = color[1:]

        # Validate hex format (3 or 6 characters)
        if len(hex_part) == 3:
            # Expand short hex (e.g., #abc to #aabbcc)
            return f"#{hex_part[0] * 2}{hex_part[1] * 2}{hex_part[2] * 2}"
        elif len(hex_part) == 6:
            # Validate all characters are hex
            try:
                int(hex_part, 16)
                return color.lower()
            except ValueError:
                return ""

        return ""

    def _process_rgb_color(self, color: str) -> str:
        """Process RGB/RGBA color format"""
        import re

        # Extract numbers from rgb() or rgba()
        if color.startswith("rgb("):
            pattern = r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
            match = re.match(pattern, color)
            if match:
                r, g, b = map(int, match.groups())
                if all(0 <= val <= 255 for val in [r, g, b]):
                    return f"rgb({r}, {g}, {b})"

        elif color.startswith("rgba("):
            pattern = r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)"
            match = re.match(pattern, color)
            if match:
                r, g, b, a = match.groups()
                r, g, b = map(int, [r, g, b])
                a = float(a)
                if all(0 <= val <= 255 for val in [r, g, b]) and 0 <= a <= 1:
                    return f"rgba({r}, {g}, {b}, {a})"

        return ""

    def _process_hsl_color(self, color: str) -> str:
        """Process HSL/HSLA color format"""
        import re

        if color.startswith("hsl("):
            pattern = r"hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)"
            match = re.match(pattern, color)
            if match:
                h, s, light = map(int, match.groups())
                if 0 <= h <= 360 and 0 <= s <= 100 and 0 <= light <= 100:
                    return f"hsl({h}, {s}%, {light}%)"

        elif color.startswith("hsla("):
            pattern = r"hsla\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*,\s*([\d.]+)\s*\)"
            match = re.match(pattern, color)
            if match:
                h, s, light, a = match.groups()
                h, s, light = map(int, [h, s, light])
                a = float(a)
                if (
                    0 <= h <= 360
                    and 0 <= s <= 100
                    and 0 <= light <= 100
                    and 0 <= a <= 1
                ):
                    return f"hsla({h}, {s}%, {light}%, {a})"

        return ""

    def _is_named_color(self, color: str) -> bool:
        """Check if color is a valid named color"""
        named_colors = {
            "black",
            "white",
            "red",
            "green",
            "blue",
            "yellow",
            "cyan",
            "magenta",
            "gray",
            "grey",
            "orange",
            "purple",
            "pink",
            "brown",
            "navy",
            "teal",
            "lime",
            "olive",
            "maroon",
            "aqua",
            "fuchsia",
            "silver",
            "darkred",
            "darkgreen",
            "darkblue",
            "lightred",
            "lightgreen",
            "lightblue",
            "transparent",
        }
        return color.lower() in named_colors

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

    def _extract_tags(self, html: str) -> list[str]:
        """Extract all HTML tags from string"""
        return re.findall(r"<[^>]+>", html)

    def _extract_tag_name(self, tag: str) -> str:
        """Extract tag name from tag string"""
        match = re.match(r"</?([a-zA-Z0-9]+)", tag)
        return match.group(1) if match else ""

    def _is_opening_tag(self, token: str) -> bool:
        """Check if token is an opening HTML tag"""
        return bool(re.match(r"<[a-zA-Z][^/>]*>$", token))

    def _is_closing_tag(self, token: str) -> bool:
        """Check if token is a closing HTML tag"""
        return bool(re.match(r"</[a-zA-Z][^>]*>$", token))

    def _is_self_closing_tag(self, token: str) -> bool:
        """Check if token is a self-closing HTML tag"""
        return bool(re.match(r"<[^>]+/>$", token))

    def _is_inline_element(self, token: str) -> bool:
        """Check if token is an inline HTML element"""
        inline_elements = {
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
        return tag_name.lower() in inline_elements
