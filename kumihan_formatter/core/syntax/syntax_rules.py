"""Syntax rules and keyword definitions

This module contains the definition of valid keywords, rules for keyword
combinations, and validation logic for Kumihan markup syntax.
"""

import re


class SyntaxRules:
    """Defines syntax rules and keyword validation for Kumihan markup"""

    # Valid keywords
    VALID_KEYWORDS: set[str] = {
        "太字",
        "イタリック",
        "枠線",
        "ハイライト",
        "見出し1",
        "見出し2",
        "見出し3",
        "見出し4",
        "見出し5",
        "折りたたみ",
        "ネタバレ",
        "目次",
        "画像",
    }

    # Keywords that accept color attribute
    COLOR_KEYWORDS: set[str] = {"ハイライト"}

    # Keywords that accept alt attribute
    ALT_KEYWORDS: set[str] = {"画像"}

    # Heading keywords for conflict detection
    HEADING_KEYWORDS: set[str] = {"見出し1", "見出し2", "見出し3", "見出し4", "見出し5"}

    @classmethod
    def is_valid_keyword(cls, keyword: str) -> bool:
        """Check if a keyword is valid"""
        return keyword in cls.VALID_KEYWORDS

    @classmethod
    def supports_color(cls, keyword: str) -> bool:
        """Check if a keyword supports color attribute"""
        return keyword in cls.COLOR_KEYWORDS

    @classmethod
    def supports_alt(cls, keyword: str) -> bool:
        """Check if a keyword supports alt attribute"""
        return keyword in cls.ALT_KEYWORDS

    @classmethod
    def is_heading(cls, keyword: str) -> bool:
        """Check if a keyword is a heading"""
        return keyword in cls.HEADING_KEYWORDS

    @classmethod
    def parse_keywords(cls, keyword_part: str) -> list[str]:
        """Parse compound keywords separated by + or ＋"""
        if not keyword_part:
            return []

        # Split by + or ＋
        keywords = re.split(r"[+＋]", keyword_part)

        # Clean and validate
        result = []
        for kw in keywords:
            kw = kw.strip()
            if kw:
                result.append(kw)

        return result

    @classmethod
    def validate_color_format(cls, color: str) -> bool:
        """Validate color format (#RRGGBB)"""
        return bool(re.match(r"^#[0-9a-fA-F]{6}$", color))

    @classmethod
    def extract_base_keyword(cls, keyword: str) -> str:
        """Extract base keyword from keyword with attributes"""
        # Check for color attribute (with or without space)
        if "color=" in keyword:
            if " color=" in keyword:
                return keyword.split(" color=")[0].strip()
            else:
                return keyword.split("color=")[0].strip()
        # Check for alt attribute (with or without space)
        elif "alt=" in keyword:
            if " alt=" in keyword:
                return keyword.split(" alt=")[0].strip()
            else:
                return keyword.split("alt=")[0].strip()
        else:
            return keyword

    @classmethod
    def extract_color_value(cls, keyword: str) -> str:
        """Extract color value from keyword with color attribute"""
        if " color=" in keyword:
            return keyword.split(" color=")[1].strip()
        elif "color=" in keyword:
            return keyword.split("color=")[1].strip()
        return ""

    @classmethod
    def extract_alt_value(cls, keyword: str) -> str:
        """Extract alt value from keyword with alt attribute"""
        if " alt=" in keyword:
            return keyword.split(" alt=")[1].strip()
        elif "alt=" in keyword:
            return keyword.split("alt=")[1].strip()
        return ""

    @classmethod
    def has_color_attribute(cls, keyword: str) -> bool:
        """Check if keyword has color attribute"""
        return "color=" in keyword

    @classmethod
    def has_alt_attribute(cls, keyword: str) -> bool:
        """Check if keyword has alt attribute"""
        return "alt=" in keyword

    @classmethod
    def find_duplicate_keywords(cls, keywords: list[str]) -> list[str]:
        """Find duplicate base keywords in list"""
        base_keywords = [cls.extract_base_keyword(kw) for kw in keywords]
        seen = set()
        duplicates = []

        for kw in base_keywords:
            if kw in seen:
                duplicates.append(kw)
            seen.add(kw)

        return duplicates

    @classmethod
    def find_conflicting_headings(cls, keywords: list[str]) -> list[str]:
        """Find conflicting heading keywords"""
        base_keywords = [cls.extract_base_keyword(kw) for kw in keywords]
        headings = [kw for kw in base_keywords if cls.is_heading(kw)]

        if len(headings) > 1:
            return headings
        return []

    @classmethod
    def get_sorted_keywords(cls) -> list[str]:
        """Get sorted list of valid keywords for error messages"""
        return sorted(cls.VALID_KEYWORDS)
