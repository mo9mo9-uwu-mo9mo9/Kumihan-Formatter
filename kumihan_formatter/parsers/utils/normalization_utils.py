"""Normalization helpers for textual content.

Separated to keep ParserUtils focused on orchestration.
"""

from __future__ import annotations

from typing import Dict, Pattern


def normalize_with_patterns(text: str, utility_patterns: Dict[str, Pattern[str]]) -> str:
    if not text:
        return ""

    normalized = utility_patterns["line_break"].sub("\n", text)
    normalized = utility_patterns["whitespace"].sub(" ", normalized)
    normalized = utility_patterns["tab"].sub("    ", normalized)
    return normalized.strip()


__all__ = ["normalize_with_patterns"]

