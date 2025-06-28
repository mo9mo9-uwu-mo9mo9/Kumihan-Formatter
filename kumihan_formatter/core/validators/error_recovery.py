"""Error recovery for validation issues

This module handles error recovery and suggestion generation for
validation issues in Kumihan-Formatter documents.
"""

from typing import TYPE_CHECKING, Dict, List

from .validation_issue import ValidationIssue

if TYPE_CHECKING:
    from .document_validator import DocumentValidator


class ErrorRecovery:
    """Handles error recovery and suggestion generation"""

    def __init__(self, validator: "DocumentValidator"):
        self.validator = validator

    def suggest_fixes(self, issues: List[ValidationIssue]) -> Dict[str, List[str]]:
        """
        Generate fix suggestions for validation issues

        Args:
            issues: List of validation issues

        Returns:
            Dict mapping issue codes to fix suggestions
        """
        suggestions = {}

        for issue in issues:
            if issue.code and issue.suggestion:
                if issue.code not in suggestions:
                    suggestions[issue.code] = []
                suggestions[issue.code].append(issue.suggestion)

        return suggestions

    def auto_fix_text(self, text: str, issues: List[ValidationIssue]) -> str:
        """
        Attempt to automatically fix simple issues

        Args:
            text: Original text
            issues: List of validation issues

        Returns:
            str: Text with automatic fixes applied
        """
        lines = text.split("\n")

        for issue in issues:
            if issue.line_number and issue.code in ["TRAILING_WHITESPACE"]:
                # Fix trailing whitespace
                line_idx = issue.line_number - 1
                if line_idx < len(lines):
                    lines[line_idx] = lines[line_idx].rstrip()

        return "\n".join(lines)
