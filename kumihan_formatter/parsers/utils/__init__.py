"""Parsers utility subpackage.

This namespace provides small focused helpers and default data used by
`parser_utils.ParserUtils`. Public re-exports are intentionally minimal.
"""

from .keyword_data import (
    DEFAULT_KEYWORD_CONFIG,
    DEFAULT_VALIDATION_RULES,
    DEFAULT_EXTRACTION_CONFIG,
)
from .patterns import (
    build_keyword_patterns,
    build_validation_patterns,
    build_utility_patterns,
)
from .normalization_utils import normalize_with_patterns

__all__ = [
    "DEFAULT_KEYWORD_CONFIG",
    "DEFAULT_VALIDATION_RULES",
    "DEFAULT_EXTRACTION_CONFIG",
    "build_keyword_patterns",
    "build_validation_patterns",
    "build_utility_patterns",
    "normalize_with_patterns",
]
