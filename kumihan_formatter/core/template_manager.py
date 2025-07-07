"""Template management for Kumihan-Formatter

This module handles Jinja2 template loading, caching, and rendering.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape


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

    def __init__(self, template_dir: Optional[Path] = None):
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
        self._template_cache: Dict[str, Any] = {}

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

        return self._template_cache[template_name]  # type: ignore[no-any-return]

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context

        Args:
            template_name: Name of the template file
            context: Template context variables

        Returns:
            str: Rendered HTML
        """
        template = self.get_template(template_name)
        return template.render(**context)

    def select_template_name(
        self,
        source_text: Optional[str] = None,
        template: Optional[str] = None,
        experimental: Optional[str] = None,
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
            return template
        elif source_text is not None:
            if experimental == "scroll-sync":
                return "experimental/base-with-scroll-sync.html.j2"
            else:
                return "base-with-source-toggle.html.j2"
        else:
            return "base.html.j2"

    def get_available_templates(self) -> list[str]:
        """Get list of available template files"""
        templates = []
        for template_file in self.template_dir.rglob("*.j2"):
            relative_path = template_file.relative_to(self.template_dir)
            templates.append(str(relative_path))
        return sorted(templates)

    def validate_template(self, template_name: str) -> tuple[bool, Optional[str]]:
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
            source = template.environment.get_template(template_name).source  # type: ignore[attr-defined]
            template.environment.parse(source)
            return True, None
        except Exception as e:
            return False, str(e)

    def clear_cache(self) -> None:
        """Clear template cache"""
        self._template_cache.clear()

    def _register_custom_filters(self) -> None:
        """Register custom Jinja2 filters"""

        def safe_html(text: str) -> str:
            """Mark text as safe HTML (no escaping)"""
            from markupsafe import Markup

            return Markup(text)

        def truncate_words(text: str, length: int = 50, suffix: str = "...") -> str:
            """Truncate text to specified number of words"""
            words = text.split()
            if len(words) <= length:
                return text
            return " ".join(words[:length]) + suffix

        def extract_text(content: Any) -> str:
            """Extract plain text from complex content"""
            if isinstance(content, str):
                return content
            elif hasattr(content, "get_text_content"):
                return content.get_text_content()  # type: ignore
            else:
                return str(content)

        def format_toc_level(level: int) -> str:
            """Format TOC indentation based on heading level"""
            return "    " * (level - 1)

        # Register filters
        self.env.filters["safe_html"] = safe_html
        self.env.filters["truncate_words"] = truncate_words
        self.env.filters["extract_text"] = extract_text
        self.env.filters["format_toc_level"] = format_toc_level


class RenderContext:
    """Builder for template rendering context"""

    def __init__(self) -> None:
        self._context = {}  # type: ignore

    def title(self, title: str) -> "RenderContext":
        """Set page title"""
        self._context["title"] = title
        return self

    def body_content(self, content: str) -> "RenderContext":
        """Set main body content"""
        self._context["body_content"] = content
        return self

    def toc_html(self, toc: str) -> "RenderContext":
        """Set table of contents HTML"""
        self._context["toc_html"] = toc
        return self

    def has_toc(self, has_toc: bool) -> "RenderContext":
        """Set whether TOC should be displayed"""
        self._context["has_toc"] = has_toc
        return self

    def source_toggle(self, source_text: str, source_filename: str) -> "RenderContext":
        """Add source toggle functionality"""
        self._context["source_text"] = source_text
        self._context["source_filename"] = source_filename
        self._context["has_source_toggle"] = True
        return self

    def navigation(self, nav_html: str) -> "RenderContext":
        """Add navigation HTML"""
        self._context["navigation_html"] = nav_html
        return self

    def css_vars(self, css_vars: Dict[str, str]) -> "RenderContext":
        """Set CSS variables for styling"""
        self._context["css_vars"] = css_vars
        return self

    def custom(self, key: str, value: Any) -> "RenderContext":
        """Add custom context variable"""
        self._context[key] = value
        return self

    def metadata(
        self, description: Optional[str] = None, keywords: Optional[str] = None
    ) -> "RenderContext":
        """Add page metadata"""
        if description:
            self._context["meta_description"] = description
        if keywords:
            self._context["meta_keywords"] = keywords
        return self

    def build(self) -> Dict[str, Any]:
        """Build the context dictionary"""
        # Set defaults
        defaults = {
            "title": "Document",
            "body_content": "",
            "toc_html": "",
            "has_toc": False,
            "has_source_toggle": False,
            "navigation_html": "",
            "meta_description": "",
            "meta_keywords": "",
            "css_vars": {},  # Empty CSS variables dict for template compatibility
        }

        # Merge with provided context
        result = defaults.copy()
        result.update(self._context)

        return result


class TemplateValidator:
    """Validator for template files and structure"""

    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager

    def validate_all_templates(self) -> Dict[str, tuple[bool, Optional[str]]]:
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

    def check_required_templates(self) -> Dict[str, bool]:
        """Check that required templates exist"""
        required_templates = ["base.html.j2", "base-with-source-toggle.html.j2"]

        results = {}
        for template_name in required_templates:
            try:
                self.template_manager.get_template(template_name)
                results[template_name] = True
            except:
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
            # Get the template source code via the environment
            source = template.environment.get_template(template_name).source  # type: ignore[attr-defined]

            missing_vars = []
            for var in required_vars:
                # Simple check for variable usage
                if f"{{{{{ var }}}}}" not in source and f"{{{{{ var }|" not in source:
                    missing_vars.append(var)

            return len(missing_vars) == 0, missing_vars
        except:
            return False, required_vars
