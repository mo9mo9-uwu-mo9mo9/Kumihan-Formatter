"""Text processing utilities

This module provides advanced text processing functions including
normalization, extraction, truncation, and word counting.
"""

import re


class TextProcessor:
    """Advanced text processing utilities"""

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text"""
        # Replace multiple whitespace with single space
        normalized = re.sub(r"\s+", " ", text.strip())
        return normalized

    @staticmethod
    def extract_text_from_html(html: str) -> str:
        """Extract plain text from HTML (simple implementation)"""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)
        # Decode HTML entities (basic ones)
        text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        return TextProcessor.normalize_whitespace(text)

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to specified length with suffix"""
        if len(text) <= max_length:
            return text

        truncated_length = max_length - len(suffix)
        if truncated_length <= 0:
            return suffix[:max_length]

        return text[:truncated_length] + suffix

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text (Japanese-aware)"""
        # Japanese text doesn't use spaces between words
        # Count characters for Japanese, words for Latin
        japanese_chars = len(re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text))
        latin_words = len(re.findall(r"\b[a-zA-Z]+\b", text))

        # Estimate: Japanese characters count as words, plus Latin words
        return japanese_chars + latin_words

    @staticmethod
    def generate_slug(text: str, max_length: int = 50) -> str:
        """Generate URL-friendly slug from text"""
        # Remove HTML tags
        text = TextProcessor.extract_text_from_html(text)

        # Convert to lowercase and replace non-alphanumeric with hyphens
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s_-]+", "-", slug)
        slug = slug.strip("-")

        # Truncate if necessary
        if len(slug) > max_length:
            slug = slug[:max_length].rstrip("-")

        return slug
