"""Validation issue data structure

This module defines the ValidationIssue class for representing
validation problems in Kumihan-Formatter documents.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    level: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'structure', 'performance', 'style'
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    code: Optional[str] = None  # Error code for programmatic handling
    
    def is_error(self) -> bool:
        """Check if this is an error-level issue"""
        return self.level == 'error'
    
    def is_warning(self) -> bool:
        """Check if this is a warning-level issue"""
        return self.level == 'warning'
    
    def is_info(self) -> bool:
        """Check if this is an info-level issue"""
        return self.level == 'info'
    
    def format_message(self) -> str:
        """Format the issue message for display"""
        parts = []
        
        if self.line_number:
            parts.append(f"Line {self.line_number}")
            if self.column_number:
                parts.append(f":{self.column_number}")
        
        level_prefix = {
            'error': '❌ ERROR',
            'warning': '⚠️  WARNING', 
            'info': 'ℹ️  INFO'
        }.get(self.level, self.level.upper())
        
        parts.append(f"{level_prefix}: {self.message}")
        
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        
        return " ".join(parts)