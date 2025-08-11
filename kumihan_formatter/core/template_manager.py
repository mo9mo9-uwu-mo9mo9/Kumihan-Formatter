"""Template management for Kumihan-Formatter

This module handles Jinja2 template loading, caching, and rendering.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

# from .template_context import RenderContext  # Removed: unused import
from .template_filters import TemplateFilters

# .template_selector.TemplateSelector removed as unused


class TemplateManager:
    """
    Jinja2テンプレート管理クラス（HTML出力の制御）

    設計ドキュメント:
    - 記法仕様: /SPEC.md
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - Renderer: このクラスを使用してHTML生成
    - RenderContext: レンダリング文脈の構築
    - Environment: Jinja2テンプレートエンジン
    - SimpleConfig: 設定値の取得

    責務:
    - Jinja2テンプレートの読み込み・キャッシュ
    - テンプレート選択とレンダリング実行
    - HTMLエスケープとセキュリティ設定
    - カスタムテンプレートディレクトリ対応
    """

    def __init__(self, template_dir: Path | None = None):
        """
        Initialize template manager

        Args:
            template_dir: Directory containing templates (defaults to package templates)
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Template cache
        self._template_cache: dict[str, Any] = {}

        # Add custom filters
        self._register_custom_filters()

    def get_template(self, template_name: str) -> Template:
        """
        Get a template by name with caching

        Args:
            template_name: Name of the template file

        Returns:
            Template: Jinja2 template object
        """
        if template_name not in self._template_cache:
            self._template_cache[template_name] = self.env.get_template(template_name)

        template: Template = self._template_cache[template_name]
        return template

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a template with the given context

        Args:
            template_name: Name of the template file
            context: Template context variables

        Returns:
            str: Rendered HTML
        """
        template = self.get_template(template_name)
        result: str = template.render(**context)
        return result

    def select_template_name(
        self,
        source_text: str | None = None,
        template: str | None = None,
        experimental: str | None = None,
    ) -> str:
        """
        Select appropriate template name based on requirements

        Args:
            source_text: Source text (indicates source toggle needed)
            template: Explicitly specified template
            experimental: Experimental feature flag

        Returns:
            str: Template name to use
        """
        if template:
            # Map short template names to full file names
            template_mapping = {
                "base": "base.html.j2",
                "base-with-source-toggle": "base-with-source-toggle.html.j2",
                "docs": "docs.html.j2",
            }
            return template_mapping.get(template, template)

    def get_available_templates(self) -> list[str]:
        """Get list of available template files"""
        templates = []
        for template_file in self.template_dir.rglob("*.j2"):
            relative_path = template_file.relative_to(self.template_dir)
            templates.append(str(relative_path))
        return sorted(templates)

    def validate_template(self, template_name: str) -> tuple[bool, str | None]:
        """
        Validate that a template exists and is valid

        Args:
            template_name: Name of template to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            template = self.get_template(template_name)
            # Try to parse the template to check for syntax errors
            # Get the template source code and parse it
            _ = template.environment.get_template(
                template_name
            )  # テンプレート取得（構文チェック用）
            # Access source through loader
            if template.environment.loader is not None:
                source, _, _ = template.environment.loader.get_source(
                    template.environment, template_name
                )
            else:
                raise Exception("Template loader is not available")
            template.environment.parse(source)
            return True, None
        except Exception as e:
            return False, str(e)

    def clear_cache(self) -> None:
        """Clear template cache"""
        self._template_cache.clear()

    def _register_custom_filters(self) -> None:
        """Register custom Jinja2 filters"""
        # Register standard template filters
        filters = TemplateFilters.get_all_filters()
        for name, filter_func in filters.items():
            self.env.filters[name] = filter_func

        # Register legacy filters for backward compatibility
        def safe_html(text: str) -> str:
            """Mark text as safe HTML (no escaping)"""
            from markupsafe import Markup

            return Markup(text)

        def truncate_words(text: str, length: int = 50, suffix: str = "...") -> str:
            """Truncate text to specified number of words"""
            words = text.split()
            if len(words) <= length:
                return text

        def extract_text(content: Any) -> str:
            """Extract plain text from complex content"""
            if isinstance(content, str):
                return content

        def format_toc_level(level: int) -> str:
            """Format TOC indentation based on heading level"""
            return "    " * (level - 1)


class TemplateValidator:
    """Validator for template files and structure"""

    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager

    def validate_all_templates(self) -> dict[str, tuple[bool, str | None]]:
        """
        Validate all available templates

        Returns:
            Dict: Mapping of template names to (is_valid, error_message)
        """
        results = {}
        templates = self.template_manager.get_available_templates()

        for template_name in templates:
            is_valid, error = self.template_manager.validate_template(template_name)
            results[template_name] = (is_valid, error)

        return results

    def check_required_templates(self) -> dict[str, bool]:
        """Check that required templates exist"""
        required_templates = ["base.html.j2", "base-with-source-toggle.html.j2"]

        results = {}
        for template_name in required_templates:
            try:
                self.template_manager.get_template(template_name)
                results[template_name] = True
            except Exception:
                results[template_name] = False

        return results

    def validate_template_variables(
        self, template_name: str, required_vars: list[str]
    ) -> tuple[bool, list[str]]:
        """
        Validate that template uses required variables

        Args:
            template_name: Template to validate
            required_vars: List of required variable names

        Returns:
            tuple: (all_present, missing_vars)
        """
        try:
            template = self.template_manager.get_template(template_name)
            # Get the template source code via the environment loader
            if template.environment.loader is None:
                return False, required_vars

            missing_vars = []
            for var in required_vars:
                if var not in template.globals:
                    missing_vars.append(var)

            return len(missing_vars) == 0, missing_vars
        except Exception:
            return False, required_vars
