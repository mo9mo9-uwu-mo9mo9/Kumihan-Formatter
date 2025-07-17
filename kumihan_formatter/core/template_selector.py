"""Template Selection Logic

テンプレート選択ロジックとファイルシステム操作
"""

from pathlib import Path
from typing import Any


class TemplateSelector:
    """Template selection and filesystem utilities"""

    @staticmethod
    def select_template_name(
        source_text: str | None = None,
        template: str | None = None,
        experimental: str | None = None,
    ) -> str:
        """Select appropriate template name based on requirements

        Args:
            source_text: Source text (indicates source toggle needed)
            template: Explicitly specified template
            experimental: Experimental feature flag

        Returns:
            str: Template filename
        """
        # Priority 1: Explicitly specified template
        if template:
            return template

        # Priority 2: Experimental features
        if experimental:
            experimental_template = f"experimental_{experimental}.html"
            return experimental_template

        # Priority 3: Source toggle requirement
        if source_text:
            return "kumihan_with_source.html"

        # Priority 4: Default template
        return "kumihan.html"

    @staticmethod
    def get_available_templates(template_dir: Path) -> list[str]:
        """Get list of available template files

        Args:
            template_dir: Directory to search for templates

        Returns:
            list[str]: List of template filenames
        """
        if not template_dir.exists():
            return []

        templates = []
        for template_file in template_dir.glob("*.html"):
            templates.append(template_file.name)

        return sorted(templates)

    @staticmethod
    def validate_template_exists(template_dir: Path, template_name: str) -> bool:
        """Validate that a template file exists

        Args:
            template_dir: Directory containing templates
            template_name: Name of template to check

        Returns:
            bool: True if template exists
        """
        template_path = template_dir / template_name
        return template_path.exists() and template_path.is_file()

    @staticmethod
    def get_template_info(template_dir: Path, template_name: str) -> dict[str, Any]:
        """Get information about a template file

        Args:
            template_dir: Directory containing templates
            template_name: Name of template

        Returns:
            dict: Template information
        """
        template_path = template_dir / template_name

        if not template_path.exists():
            return {
                "exists": False,
                "name": template_name,
                "path": str(template_path),
            }

        stat = template_path.stat()
        return {
            "exists": True,
            "name": template_name,
            "path": str(template_path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
        }

    @staticmethod
    def find_fallback_template(template_dir: Path, preferred_name: str) -> str:
        """Find fallback template if preferred doesn't exist

        Args:
            template_dir: Directory containing templates
            preferred_name: Preferred template name

        Returns:
            str: Available template name
        """
        # Check if preferred template exists
        if TemplateSelector.validate_template_exists(template_dir, preferred_name):
            return preferred_name

        # Fallback hierarchy
        fallbacks = [
            "kumihan.html",
            "base.html",
            "default.html",
        ]

        for fallback in fallbacks:
            if TemplateSelector.validate_template_exists(template_dir, fallback):
                return fallback

        # If no fallbacks exist, return preferred (will cause error)
        return preferred_name
