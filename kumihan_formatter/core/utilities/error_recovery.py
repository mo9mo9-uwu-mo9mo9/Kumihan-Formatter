"""Error recovery utilities

This module provides error recovery and suggestion utilities
for improving user experience when errors occur.
"""

import re
from typing import List
from .string_similarity import StringSimilarity


class ErrorRecovery:
    """Error recovery and suggestion utilities"""
    
    @staticmethod
    def suggest_corrections(error_msg: str, valid_options: List[str]) -> List[str]:
        """Suggest corrections based on error message"""
        suggestions = []
        
        # Extract potential misspelled word from error message
        words = re.findall(r'\b\w+\b', error_msg.lower())
        
        for word in words:
            if len(word) >= 3:  # Only suggest for words with 3+ characters
                matches = StringSimilarity.find_closest_matches(word, valid_options)
                suggestions.extend([match[0] for match in matches])
        
        # Remove duplicates while preserving order
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:3]  # Return top 3 suggestions