"""Parse result data model for marker parsing."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ParseResult:
    """Result of parsing a text with markers.

    Attributes:
        markers: List of found marker tuples (start, end, marker_text)
        content: Processed content after parsing
        keywords: List of extracted keywords
        attributes: Dictionary of parsed attributes
        errors: List of parsing errors
    """

    markers: List[tuple[int, int, str]] = field(default_factory=list)
    content: str = ""
    keywords: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize fields - dataclass fields with default_factory are never None."""
        # All fields have default_factory, so no None checks needed
        pass
