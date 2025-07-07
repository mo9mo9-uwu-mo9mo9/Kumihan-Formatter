"""String similarity utilities

This module provides string similarity calculation functions
including Levenshtein distance and fuzzy matching.
"""

from typing import List, Tuple


class StringSimilarity:
    """String similarity calculation utilities"""

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return StringSimilarity.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def similarity_ratio(s1: str, s2: str) -> float:
        """Calculate similarity ratio (0.0 to 1.0)"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0

        distance = StringSimilarity.levenshtein_distance(s1, s2)
        return (max_len - distance) / max_len

    @staticmethod
    def find_closest_matches(
        target: str,
        candidates: list[str],
        min_similarity: float = 0.6,
        max_results: int = 3,
    ) -> List[tuple[str, float]]:
        """Find closest matching strings"""
        matches = []

        for candidate in candidates:
            similarity = StringSimilarity.similarity_ratio(
                target.lower(), candidate.lower()
            )
            if similarity >= min_similarity:
                matches.append((candidate, similarity))

        # Sort by similarity (descending) and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]
