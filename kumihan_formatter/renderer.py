"""Refactored HTML renderer for Kumihan-Formatter

This is the new, modular renderer implementation that replaces the monolithic
renderer.py file. Each rendering responsibility is now handled by specialized modules.
"""

import time
from pathlib import Path
from typing import Any, List

from .core.ast_nodes import Node
from .core.rendering import HTMLRenderer
from .core.template_context import RenderContext
from .core.template_manager import TemplateManager
from .core.toc_generator import TOCGenerator
from .core.utilities.logger import get_logger, log_performance
from .simple_config import create_simple_config


class Renderer:
    """
    Kumihan記法のメインレンダラー（各特化レンダラーを統括）

    設計ドキュメント:
    - 記法仕様: /SPEC.md
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - HTMLRenderer: HTML出力の中核処理
    - TemplateManager: Jinja2テンプレート管理
    - TOCGenerator: 目次生成処理
    - SimpleConfig: 設定値取得
    - Node: 入力となるASTノード

    責務:
    - レンダリング全体フロー制御
    - AST→HTML変換の統括
    - テンプレート適用とHTML出力
    """

    def __init__(self, template_dir: Path | None = None):
        """
        Initialize renderer with optional template directory

        Args:
            template_dir: Custom template directory (defaults to package templates)
        """
        self.logger = get_logger(__name__)
        self.html_renderer = HTMLRenderer()
        self.template_manager = TemplateManager(template_dir)
        self.toc_generator = TOCGenerator()

        self.logger.debug("Renderer initialized with template_dir: %s", template_dir)

    def render(
        self,
        ast: list[Node],
        config: "Any | None" = None,  # BaseConfig | ConfigManager
        template: str | None = None,
        title: str | None = None,
        source_text: str | None = None,
        source_filename: str | None = None,
        navigation_html: str | None = None,
        original_source_text: str | None = None,
    ) -> str:
        """
        Render AST to HTML

        Args:
            ast: List of AST nodes to render
            config: Optional configuration (BaseConfig or ConfigManager)
            template: Optional template name
            title: Page title
            source_text: Source text for toggle feature (footnotes already removed)
            source_filename: Source filename for toggle feature
            navigation_html: Navigation HTML
            original_source_text: Original source text with footnotes for footnote processing

        Returns:
            str: Complete HTML document
        """
        start_time = time.time()
        self.logger.info(f"Starting render of {len(ast)} AST nodes")

        # Use processed source text (footnotes already removed for display)
        processed_source_text = source_text

        # Use all nodes for body content (no more TOC marker filtering)
        body_ast = ast
        self.logger.debug(f"Using all {len(body_ast)} nodes for body content")

        # Generate body HTML
        body_content = self.html_renderer.render_nodes(body_ast)
        self.logger.debug(f"Generated body HTML: {len(body_content)} characters")

        # Generate table of contents
        toc_data = self.toc_generator.generate_toc(ast)
        should_show_toc = toc_data["has_toc"]

        # Select template
        template_name = self.template_manager.select_template_name(
            source_text=processed_source_text, template=template
        )

        # Build rendering context
        simple_config = create_simple_config()
        context = (
            RenderContext()
            .title(title or "Document")
            .body_content(body_content)
            .toc_html(toc_data["html"])
            .has_toc(should_show_toc)
            .css_vars(simple_config.get_css_variables())
        )

        # Check if footnote data was set in HTML renderer
        footnotes_html = None
        has_footnotes = False

        if (
            hasattr(self.html_renderer, "footnotes_data")
            and self.html_renderer.footnotes_data
        ):
            try:
                footnotes_data = self.html_renderer.footnotes_data
                footnote_html = footnotes_data["manager"].generate_footnote_html(
                    footnotes_data["footnotes"]
                )
                if footnote_html:
                    footnotes_html = footnote_html
                    has_footnotes = True
                    self.logger.debug(
                        f"Added footnotes HTML to context: {len(footnote_html)} characters"
                    )

            except Exception as e:
                self.logger.warning(f"Failed to generate footnote HTML: {e}")

        # Add footnotes to context
        context.custom("footnotes_html", footnotes_html)
        context.custom("has_footnotes", has_footnotes)

        # Add source toggle if needed (use processed text)
        if processed_source_text and source_filename:
            context.source_toggle(processed_source_text, source_filename)

        # Add navigation if provided
        if navigation_html:
            context.navigation(navigation_html)

        # Render template
        result = self.template_manager.render_template(template_name, context.build())

        duration = time.time() - start_time
        log_performance("render", duration, len(result))
        self.logger.info(f"Render complete: {len(result)} characters")

        return result

    def render_nodes_only(self, nodes: list[Node]) -> str:
        """
        Render only the nodes without template wrapper

        Args:
            nodes: Nodes to render

        Returns:
            str: HTML content without template
        """
        self.logger.debug(f"Rendering {len(nodes)} nodes without template")
        return self.html_renderer.render_nodes(nodes)

    def render_with_custom_context(
        self, ast: list[Node], template_name: str, custom_context: dict[str, Any]
    ) -> str:
        """
        Render with custom template context

        Args:
            ast: AST nodes to render
            template_name: Template to use
            custom_context: Custom context variables

        Returns:
            str: Rendered HTML
        """
        self.logger.info(
            f"Rendering with custom context using template: {template_name}"
        )

        # Generate basic content
        body_content = self.html_renderer.render_nodes(ast)
        toc_data = self.toc_generator.generate_toc(ast)

        # Build base context
        context = (
            RenderContext()
            .body_content(body_content)
            .toc_html(toc_data["html"])
            .has_toc(toc_data["has_toc"])
        )

        # Add custom variables
        base_context = context.build()
        base_context.update(custom_context)

        return self.template_manager.render_template(template_name, base_context)

    def get_toc_data(self, ast: list[Node]) -> dict[str, Any]:
        """
        Get table of contents data without rendering

        Args:
            ast: AST nodes to analyze

        Returns:
            Dict: TOC data
        """
        return self.toc_generator.generate_toc(ast)

    def get_headings(self, ast: list[Node]) -> List[dict[str, Any]]:
        """
        Get list of headings from AST

        Args:
            ast: AST nodes to analyze

        Returns:
            List: Heading information
        """
        return self.html_renderer.collect_headings(ast)

    def validate_template(self, template_name: str) -> tuple[bool, str | None]:
        """
        Validate a template

        Args:
            template_name: Template to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        return self.template_manager.validate_template(template_name)

    def get_available_templates(self) -> list[str]:
        """Get list of available templates"""
        return self.template_manager.get_available_templates()

    def clear_caches(self) -> None:
        """Clear all internal caches"""
        self.template_manager.clear_cache()
        self.html_renderer.reset_counters()


def render(
    ast: list[Node],
    config: Any = None,
    template: str | None = None,
    title: str | None = None,
    source_text: str | None = None,
    source_filename: str | None = None,
    navigation_html: str | None = None,
) -> str:
    """
    Main rendering function (compatibility with existing API)

    Args:
        ast: List of AST nodes to render
        config: Optional configuration
        template: Optional template name
        title: Page title
        source_text: Source text for toggle feature
        source_filename: Source filename for toggle feature
        navigation_html: Navigation HTML

    Returns:
        str: Complete HTML document
    """
    renderer = Renderer()
    return renderer.render(
        ast=ast,
        config=config,
        template=template,
        title=title,
        source_text=source_text,
        source_filename=source_filename,
        navigation_html=navigation_html,
    )


# HTMLRenderer = Renderer  # Removed: conflicts with imported HTMLRenderer
