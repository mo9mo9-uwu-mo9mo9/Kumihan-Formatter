"""Regex pattern builders used by ParserUtils.

Functions return new dictionaries each call to avoid cross-instance sharing.
"""

from __future__ import annotations

import re
from typing import Dict, Pattern


def build_keyword_patterns() -> Dict[str, Pattern[str]]:
    return {
        "basic": re.compile(r"[a-zA-Z\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+"),
        "compound": re.compile(
            r"[a-zA-Z\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf][\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]*"
        ),
        "numeric": re.compile(r"\d+[a-zA-Z\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]*"),
        "special": re.compile(
            r"[a-zA-Z\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf][\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\-_]*"
        ),
    }


def build_validation_patterns() -> Dict[str, Pattern[str]]:
    return {
        "valid_chars": re.compile(r"^[a-zA-Z\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\d\-_]*$"),
        "invalid_start": re.compile(r"^[\d\-_]"),
        "invalid_end": re.compile(r"[\-_]$"),
        "consecutive_special": re.compile(r"[\-_]{2,}"),
    }


def build_utility_patterns() -> Dict[str, Pattern[str]]:
    return {
        "whitespace": re.compile(r"\s+"),
        "line_break": re.compile(r"\r?\n"),
        "tab": re.compile(r"\t+"),
        "punctuation": re.compile(r"[^\w\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]"),
    }


__all__ = [
    "build_keyword_patterns",
    "build_validation_patterns",
    "build_utility_patterns",
]

