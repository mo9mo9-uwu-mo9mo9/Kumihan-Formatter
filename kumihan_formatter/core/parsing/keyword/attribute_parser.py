"""Attribute parsing functionality."""

import re
from typing import Any, Dict

from .base_parser import BaseParser


class AttributeParser(BaseParser):
    """Parser for marker attributes and properties."""

    def __init__(self) -> None:
        """Initialize attribute parser."""
        super().__init__()

    def extract_color_attribute(self, marker_content: Any) -> tuple[str, str]:
        """Extract color attribute from marker content.

        Args:
            marker_content: Content to extract color from

        Returns:
            Tuple of (color_value, cleaned_content)
        """
        if not isinstance(marker_content, str):
            return "", marker_content

        # Basic color extraction implementation
        # 色抽出ロジック実装
        import re

        color_patterns = [
            r"#[0-9a-fA-F]{6}",  # hex
            r"rgb\(\d+,\s*\d+,\s*\d+\)",  # rgb
            r"rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)",  # rgba
        ]
        for pattern in color_patterns:
            if re.match(pattern, marker_content):
                return marker_content, ""
        return "", marker_content

    def parse_attributes_from_content(self, content: Any) -> Dict[str, Any]:
        """Parse all attributes from content.

        Args:
            content: Content to parse attributes from

        Returns:
            Dictionary of parsed attributes
        """
        if not isinstance(content, str):
            return {}

        # Basic attribute parsing implementation
        attributes: Dict[str, Any] = {}
        # 属性解析ロジック実装
        import re

        # 引用符で囲まれた属性と引用符なし属性の両方に対応
        attr_pattern = r'(\w+)=(?:["\']([^"\']*)["\']|([^\s>]+))'
        matches = re.findall(attr_pattern, content)
        for key, quoted_value, unquoted_value in matches:
            # 引用符ありの値を優先、なければ引用符なしの値を使用
            value = quoted_value if quoted_value else unquoted_value

            # class属性の場合は最初のクラス名のみを取得
            if key.lower() == "class" and value:
                value = value.split()[0]

            attributes[key] = value
        return attributes

    def _extract_size_attributes(self, content: Any) -> Dict[str, Any]:
        """Extract size-related attributes.

        Args:
            content: Content to extract from

        Returns:
            Dictionary of size attributes
        """
        attributes: Dict[str, Any] = {}

        # Size pattern: [size:value]
        size_pattern = re.compile(r"\[size:([^]]+)\]")
        size_match = size_pattern.search(content)

        if size_match:
            size_value = size_match.group(1).strip()
            if self._is_valid_size_value(size_value):
                attributes["size"] = size_value

        return attributes

    def _extract_style_attributes(self, content: Any) -> Dict[str, Any]:
        """Extract style-related attributes.

        Args:
            content: Content to extract from

        Returns:
            Dictionary of style attributes
        """
        attributes: Dict[str, Any] = {}

        # Style pattern: [style:value]
        style_pattern = re.compile(r"\[style:([^]]+)\]")
        style_match = style_pattern.search(content)

        if style_match:
            style_value = style_match.group(1).strip()
            if self._is_valid_style_value(style_value):
                attributes["style"] = style_value

        return attributes

    def _is_valid_size_value(self, size_value: Any) -> bool:
        """Validate size attribute value.

        Args:
            size_value: Size value to validate

        Returns:
            True if valid size value
        """
        if not isinstance(size_value, str):
            return False

        # Basic size validation (px, em, rem, %, etc.)
        size_pattern = re.compile(
            r"^\d+(\.\d+)?(px|em|rem|%|pt|vh|vw)$|^(small|medium|large|x-large|xx-large)$"
        )
        return bool(size_pattern.match(size_value.strip().lower()))

    def _is_valid_style_value(self, style_value: Any) -> bool:
        """Validate style attribute value.

        Args:
            style_value: Style value to validate

        Returns:
            True if valid style value
        """
        if not isinstance(style_value, str):
            return False

        valid_styles = {
            "normal",
            "italic",
            "bold",
            "underline",
            "strikethrough",
            "uppercase",
            "lowercase",
            "capitalize",
        }

        return style_value.lower() in valid_styles

    def _sanitize_color_attribute(self, color_value: Any) -> str:
        """Sanitize color attribute value.

        Args:
            color_value: Color value to sanitize

        Returns:
            Sanitized color value
        """
        if not isinstance(color_value, str):
            return ""

        sanitized = color_value.strip()

        # Validate hex color pattern
        hex_pattern = re.compile(r"^#([a-fA-F0-9]{3}|[a-fA-F0-9]{6})$")
        if hex_pattern.match(sanitized):
            return sanitized.lower()

        # Validate named colors
        named_colors = {
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "pink",
            "brown",
            "black",
            "white",
            "gray",
            "grey",
            "cyan",
            "magenta",
        }

        if sanitized.lower() in named_colors:
            return sanitized.lower()

        return ""
