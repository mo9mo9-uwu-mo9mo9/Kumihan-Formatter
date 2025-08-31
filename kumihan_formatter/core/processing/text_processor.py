import re

from typing import Dict, List, Optional


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

        truncated = text[: max_length - len(suffix)]
        return truncated + suffix

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text (Japanese-aware)"""
        # Japanese text doesn't use spaces between words
        # Count characters for Japanese, words for Latin
        japanese_chars = len(
            re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
        )
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

    @staticmethod
    def normalize_line_endings(text: str, line_ending: str = "\n") -> str:
        """Normalize line endings to specified format"""
        # Replace all variations of line endings with the specified one
        normalized = re.sub(r"\r\n|\r|\n", line_ending, text)
        return normalized

    @staticmethod
    def remove_empty_lines(text: str) -> str:
        """Remove empty lines from text"""
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        return "\n".join(non_empty_lines)

    @staticmethod
    def extract_markers(text: str, marker_pattern: str = r"#\s*\w+\s*#") -> List[str]:
        """Extract markers from text using regex pattern"""

        markers = re.findall(marker_pattern, text)
        return [marker.strip() for marker in markers]

    @staticmethod
    def count_characters(text: str, include_spaces: bool = True) -> int:
        """Count characters in text"""
        if include_spaces:
            return len(text)
        else:
            return len(text.replace(" ", "").replace("\t", "").replace("\n", ""))

    @staticmethod
    def get_text_statistics(text: str) -> Dict[str, int]:
        """Get comprehensive text statistics"""
        return {
            "characters": len(text),
            "characters_no_spaces": TextProcessor.count_characters(
                text, include_spaces=False
            ),
            "words": TextProcessor.count_words(text),
            "lines": len(text.split("\n")),
            "paragraphs": len([p for p in text.split("\n\n") if p.strip()]),
        }

    @staticmethod
    def sanitize_text(text: str, allowed_chars: Optional[str] = None) -> str:
        """Sanitize text by removing or replacing unwanted characters"""
        if allowed_chars is None:
            # Default: keep alphanumeric, spaces, and basic punctuation
            allowed_chars = r"[^\w\s\.\,\!\?\-\(\)]"

        sanitized = re.sub(allowed_chars, "", text)
        return TextProcessor.normalize_whitespace(sanitized)

    @staticmethod
    def detect_encoding(text_bytes: bytes) -> str:
        """Detect text encoding (simple implementation)"""
        try:
            # Try UTF-8 first
            text_bytes.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            # Try common encodings
            for encoding in ["shift_jis", "euc-jp", "iso-2022-jp", "cp932"]:
                try:
                    text_bytes.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    continue

        # Default fallback
        return "utf-8"
