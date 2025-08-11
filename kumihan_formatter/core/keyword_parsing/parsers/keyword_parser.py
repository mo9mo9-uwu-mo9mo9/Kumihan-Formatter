"""Keyword parsing functionality."""

import re
from typing import Any, Dict, List, Tuple

from .base_parser import BaseParser


class KeywordParser(BaseParser):
    """Parser for keyword extraction and validation."""

    def __init__(self, definitions):
        """Initialize keyword parser.

        Args:
            definitions: Keyword definitions for validation
        """
        super().__init__()
        self.definitions = definitions

    def parse_marker_keywords(
        self, marker_content: str
    ) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """Parse keywords from marker content.

        Args:
            marker_content: Content of marker to parse

        Returns:
            Tuple of (keywords, attributes, errors)
        """
        if not isinstance(marker_content, str):
            return [], {}, ["Invalid marker content type"]

        keywords = []
        attributes = {}
        errors = []

        marker_content = marker_content.strip()
        if not marker_content:
            return keywords, attributes, errors

        # Check for ruby content
        if marker_content.startswith("ルビ "):
            ruby_content = marker_content[3:].strip()
            ruby_result = self._parse_ruby_content(ruby_content)
            if ruby_result:
                attributes["ruby"] = ruby_result
                return keywords, attributes, errors

        # Check for compound keywords (with + separator)
        if "+" in marker_content or "＋" in marker_content:
            compound_keywords = self.split_compound_keywords(marker_content)
            for part in compound_keywords:
                if part and self._is_valid_keyword(part):
                    keywords.append(part)
        else:
            # Single keyword
            keyword = marker_content.strip()
            if keyword and self._is_valid_keyword(keyword):
                keywords.append(keyword)

        return keywords, attributes, errors

    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワードを個別のキーワードに分割

        Args:
            keyword_content: 分割対象のキーワード文字列

        Returns:
            List of individual keywords
        """
        if not isinstance(keyword_content, str):
            return []

        keywords = []
        # Check for compound keywords (+ or ＋)
        if "+" in keyword_content or "＋" in keyword_content:
            parts = re.split(r"[+＋]", keyword_content)
            for part in parts:
                part = part.strip()
                if part and self._is_valid_keyword(part):
                    keywords.append(part)
        else:
            # Single keyword
            keyword = keyword_content.strip()
            if keyword and self._is_valid_keyword(keyword):
                keywords.append(keyword)

        return keywords

    def _is_valid_keyword(self, keyword: str) -> bool:
        """Check if keyword is valid.

        Args:
            keyword: Keyword to validate

        Returns:
            True if keyword is valid
        """
        if not isinstance(keyword, str) or not keyword.strip():
            return False

        return self.definitions.is_valid_keyword(keyword) if self.definitions else True

    def _parse_ruby_content(self, content: str) -> Dict[str, str]:
        """Parse ruby content for Japanese text formatting.

        Args:
            content: Content to parse for ruby text

        Returns:
            Dictionary with base_text and ruby_text if found
        """
        if not isinstance(content, str):
            return {}

        # Pattern for ruby notation: base_text(ruby_text) or base_text（ruby_text）
        ruby_pattern = r"([^()（）]+)[()（]([^()（）]+)[)）]"
        match = re.search(ruby_pattern, content)

        if match:
            base_text = match.group(1).strip()
            ruby_text = match.group(2).strip()

            if base_text and ruby_text:
                return {"base_text": base_text, "ruby_text": ruby_text}

        return {}

    def _sanitize_color_attribute(self, color_value: str) -> str:
        """Sanitize color attribute value.

        Args:
            color_value: Color value to sanitize

        Returns:
            Sanitized color value
        """
        if not isinstance(color_value, str):
            return ""

        sanitized = color_value.strip()

        # Basic validation for hex colors
        if sanitized.startswith("#") and len(sanitized) in [4, 7]:
            hex_part = sanitized[1:]
            if all(c in "0123456789abcdefABCDEF" for c in hex_part):
                return sanitized

        # Named colors
        named_colors = {
            "red",
            "blue",
            "green",
            "yellow",
            "orange",
            "purple",
            "black",
            "white",
            "gray",
            "pink",
            "brown",
            "cyan",
            "magenta",
            "lime",
            "navy",
            "silver",
        }

        if sanitized.lower() in named_colors:
            return sanitized.lower()

        return "#000000"  # Default fallback color
