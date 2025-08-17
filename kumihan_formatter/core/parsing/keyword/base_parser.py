"""Base parser class for marker parsing functionality."""

import re
from typing import Any, Optional

from kumihan_formatter.core.utilities.logger import get_logger


class BaseParser:
    """Base class for marker parsing components."""

    def __init__(self) -> None:
        """Initialize base parser."""
        self.logger = get_logger(self.__class__.__name__)

        # Core patterns used across parsers
        self._NEW_FORMAT_PATTERN = re.compile(
            r"^#\s*([^#]+?)\s*#([^#]*?)##$", re.MULTILINE
        )
        self._INLINE_CONTENT_PATTERN = re.compile(r"^#\s*([^#]+?)\s*#([^#]*?)##$")
        self._FORMAT_CHECK_PATTERN = re.compile(r"^#[^#]*#[^#]*##$")
        self._COLOR_ATTRIBUTE_PATTERN = re.compile(r"\[color:([#a-zA-Z0-9]+)\]")
        self._KEYWORD_SPLIT_PATTERN = re.compile(r"[+\-,]")

        # Hash markers for validation
        self.HASH_MARKERS = ["#", "##", "###", "####", "#####"]
        self.BLOCK_END_MARKERS = ["##", "###", "####", "#####"]

    def _contains_malicious_content(self, content: Any) -> bool:
        """Check if content contains potentially malicious patterns.

        Args:
            content: Content to check

        Returns:
            True if malicious patterns found
        """
        if not isinstance(content, str):
            return False

        # Check for potentially malicious patterns
        malicious_patterns = [
            "<script",
            "javascript:",
            "onload=",
            "onerror=",
        ]
        content_lower = content.lower()

        for pattern in malicious_patterns:
            if pattern in content_lower:
                self.logger.warning(
                    f"Potentially malicious pattern detected: {pattern}"
                )
                return True

        return False

    def _sanitize_content(self, content: Any) -> str:
        """Sanitize content by removing potentially dangerous elements.

        Args:
            content: Content to sanitize

        Returns:
            Sanitized content
        """
        if not isinstance(content, str):
            return ""

        # Basic sanitization - remove script tags and javascript
        dangerous_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
        ]

        sanitized = content
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

        return sanitized.strip()

    def _find_matching_marker(
        self, text: str, start_pos: int, start_marker: str
    ) -> Optional[int]:
        """Find the position of matching end marker.

        Args:
            text: Text to search in
            start_pos: Starting position of search
            start_marker: Starting marker string

        Returns:
            Position of matching end marker, or None if not found
        """
        if not isinstance(text, str) or start_pos < 0 or start_pos >= len(text):
            return None

        # Find matching end marker based on start marker
        if start_marker == "#":
            end_marker = "##"
        elif start_marker in ["##", "###", "####", "#####"]:
            end_marker = start_marker
        else:
            return None

        # Search for end marker after start position
        search_start = start_pos + len(start_marker)
        end_pos = text.find(end_marker, search_start)

        if end_pos != -1:
            # Validate the content between markers
            content = text[start_pos + len(start_marker) : end_pos]
            if self._is_valid_marker_content(content):
                return end_pos

        return None

    def _is_valid_marker_content(self, content: Any) -> bool:
        """Validate marker content for basic structure.

        Args:
            content: Content to validate

        Returns:
            True if content appears valid
        """
        if not isinstance(content, str):
            return False

        content = content.strip()
        if not content:
            return False

        # Check for malicious patterns
        if self._contains_malicious_content(content):
            return False

        # Basic content validation
        parts = content.split("#")
        if not parts or not parts[0].strip():
            return False

        keyword_part = parts[0].strip()
        invalid_patterns = [
            r"^[^a-zA-Z]",  # Starts with non-letter
            r"^\d+$",  # Only digits
        ]

        for pattern in invalid_patterns:
            if re.match(pattern, keyword_part):
                return False

        return True
