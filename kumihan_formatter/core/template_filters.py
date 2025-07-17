"""Custom Jinja2 Template Filters

カスタムフィルターとヘルパー機能を提供
"""

import html
import re
from pathlib import Path
from typing import Any


class TemplateFilters:
    """Custom Jinja2 template filters"""

    @staticmethod
    def escape_html(text: str) -> str:
        """HTML escape filter"""
        return html.escape(text)

    @staticmethod
    def format_path(path: Path | str) -> str:
        """Format path for display"""
        return str(path)

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text for output"""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text.strip())
        return text

    @staticmethod
    def safe_filename(filename: str) -> str:
        """Make filename safe for filesystem"""
        # Remove or replace dangerous characters
        safe = re.sub(r'[<>:"/\\|?*]', "_", filename)
        return safe.strip()

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        size_value: float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_value < 1024.0:
                return f"{size_value:.1f}{unit}"
            size_value = size_value / 1024.0
        return f"{size_value:.1f}TB"

    @staticmethod
    def highlight_keywords(text: str, keywords: list[str]) -> str:
        """Highlight keywords in text"""
        for keyword in keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            text = pattern.sub(f"<mark>{keyword}</mark>", text)
        return text

    @classmethod
    def get_all_filters(cls) -> dict[str, Any]:
        """Get all custom filters as dictionary"""
        return {
            "escape_html": cls.escape_html,
            "format_path": cls.format_path,
            "clean_text": cls.clean_text,
            "safe_filename": cls.safe_filename,
            "truncate_text": cls.truncate_text,
            "format_size": cls.format_size,
            "highlight_keywords": cls.highlight_keywords,
        }
