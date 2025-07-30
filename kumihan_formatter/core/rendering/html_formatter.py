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
