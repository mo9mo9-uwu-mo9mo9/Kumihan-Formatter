"""Chunking utilities for large-text processing.

Small, focused helper extracted to reduce responsibilities in
ProcessingManager. Behavior matches previous ad-hoc implementation.
"""

from __future__ import annotations

from typing import Iterable, List


class Chunker:
    """Create line-based chunks for large inputs.

    This mirrors the previous logic used inside ProcessingManager._optimize_large_parsing
    to keep behavior unchanged while making the code testable and reusable.
    """

    def create_chunks(self, lines: Iterable[str], chunk_size: int) -> List[List[str]]:
        if chunk_size <= 0:
            # Fallback: treat the entire content as a single chunk
            return [list(lines)]

        # Materialize to support slicing in a deterministic way
        line_list = list(lines)
        return [line_list[i : i + chunk_size] for i in range(0, len(line_list), chunk_size)]


__all__ = ["Chunker"]

