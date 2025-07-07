"""HTML formatting utilities for Kumihan-Formatter

This module provides utilities for HTML formatting, pretty-printing,
and validation of generated HTML.
"""

import re
from typing import List, Optional


class HTMLFormatter:
    """
    HTML整形・フォーマット（Pretty-print、バリデーション）

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
    """

    def __init__(self, indent_size: int = 2):
        """
        Initialize HTML formatter

        Args:
            indent_size: Number of spaces per indentation level
        """
        self.indent_size = indent_size

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
        tag_stack: list[str] = []

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
