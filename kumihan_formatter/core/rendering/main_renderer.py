"""
MainRenderer - 統合レンダリングシステム
HTML・CSS・テンプレート処理の統合管理
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from kumihan_formatter.core.ast_nodes.node import Node
from .html_formatter import HtmlFormatter
from .css_processor import CSSProcessor
from .html_utilities import HTMLUtilities
from .css_utilities import CSSUtilities
from .html_accessibility import HTMLAccessibilityProcessor as HTMLAccessibility
from .heading_collector import HeadingCollector


class MainRenderer:
    """統合レンダリングシステム - HTML・CSS・テンプレート処理の中央管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        MainRenderer初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # コア レンダリング コンポーネント
        self.html_formatter = HtmlFormatter(config)
        self.css_processor = CSSProcessor(config)

        # ユーティリティ コンポーネント
        self.html_utils = HTMLUtilities()
        self.css_utils = CSSUtilities()
        self.accessibility = HTMLAccessibility()
        self.heading_collector = HeadingCollector()

        # レンダリング設定
        self.output_format = self.config.get("output_format", "html")
        self.enable_accessibility = self.config.get("enable_accessibility", True)
        self.enable_responsive = self.config.get("enable_responsive", True)
        self.css_theme = self.config.get("css_theme", "default")

    def render(
        self, nodes: Union[Node, List[Node]], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        統合レンダリング実行

        Args:
            nodes: レンダリング対象ノード
            context: レンダリングコンテキスト

        Returns:
            レンダリング結果HTML
        """
        try:
            # ノードリストの正規化
            if isinstance(nodes, Node):
                node_list = [nodes]
            else:
                node_list = nodes

            # コンテキスト準備
            render_context = self._prepare_context(context)

            # HTML本体生成
            html_body = self._render_html_body(node_list, render_context)

            # CSS処理
            css_content = self._process_css(render_context)

            # 最終HTML統合
            final_html = self._integrate_html_css(
                html_body, css_content, render_context
            )

            # アクセシビリティ最適化
            if self.enable_accessibility:
                final_html = self.accessibility.enhance_html(final_html)

            return final_html

        except Exception as e:
            self.logger.error(f"統合レンダリング中にエラー: {e}")
            return f'<div class="error">レンダリングエラー: {str(e)}</div>'

    def _prepare_context(
        self, user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """レンダリングコンテキスト準備"""
        base_context = {
            "css_theme": self.css_theme,
            "enable_accessibility": self.enable_accessibility,
            "enable_responsive": self.enable_responsive,
            "output_format": self.output_format,
        }

        if user_context:
            base_context.update(user_context)

        return base_context

    def _render_html_body(self, nodes: List[Node], context: Dict[str, Any]) -> str:
        """HTML本体レンダリング"""
        try:
            return self.html_formatter.render_html(nodes, context)
        except Exception as e:
            self.logger.error(f"HTML本体レンダリング中にエラー: {e}")
            return f'<div class="error">HTML生成エラー: {str(e)}</div>'

    def _process_css(self, context: Dict[str, Any]) -> str:
        """CSS処理"""
        try:
            # ベースCSS取得
            base_css = self.css_processor.get_base_css(
                context.get("css_theme", "default")
            )

            # レスポンシブ対応
            if context.get("enable_responsive", True):
                responsive_css = self.css_utils.generate_responsive_css()
                base_css += f"\n\n/* Responsive CSS */\n{responsive_css}"

            # アクセシビリティ対応
            if context.get("enable_accessibility", True):
                a11y_css = self.css_utils.generate_accessibility_css()
                base_css += f"\n\n/* Accessibility CSS */\n{a11y_css}"

            return base_css

        except Exception as e:
            self.logger.error(f"CSS処理中にエラー: {e}")
            return "/* CSS処理エラー */"

    def _integrate_html_css(
        self, html_body: str, css_content: str, context: Dict[str, Any]
    ) -> str:
        """HTML・CSS統合"""
        try:
            # 基本HTMLテンプレート
            html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{context.get('title', 'Kumihan Document')}</title>
    <style>
{css_content}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

            return html_template

        except Exception as e:
            self.logger.error(f"HTML・CSS統合中にエラー: {e}")
            return html_body  # フォールバック

    def render_with_template(
        self,
        nodes: Union[Node, List[Node]],
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        テンプレート使用レンダリング

        Args:
            nodes: レンダリング対象ノード
            template_name: テンプレート名
            context: レンダリングコンテキスト

        Returns:
            テンプレート適用済みHTML
        """
        try:
            # ノードリストの正規化
            if isinstance(nodes, Node):
                node_list = [nodes]
            else:
                node_list = nodes

            return self.html_formatter.render_with_template(
                node_list, template_name, context
            )

        except Exception as e:
            self.logger.error(f"テンプレートレンダリング中にエラー: {e}")
            return self.render(nodes, context)  # フォールバック

    def generate_toc(self, nodes: Union[Node, List[Node]]) -> str:
        """
        目次生成

        Args:
            nodes: 目次生成対象ノード

        Returns:
            目次HTML
        """
        try:
            # ノードリストの正規化
            if isinstance(nodes, Node):
                node_list = [nodes]
            else:
                node_list = nodes

            # 見出し収集
            headings = self.heading_collector.collect_headings(node_list)

            # 目次HTML生成
            return self.html_utils.generate_toc_html(headings)

        except Exception as e:
            self.logger.error(f"目次生成中にエラー: {e}")
            return '<div class="error">目次生成エラー</div>'

    def render_to_file(
        self,
        nodes: Union[Node, List[Node]],
        output_path: Union[str, Path],
        template_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        ファイル出力レンダリング

        Args:
            nodes: レンダリング対象ノード
            output_path: 出力パス
            template_name: テンプレート名（オプション）
            context: レンダリングコンテキスト

        Returns:
            成功フラグ
        """
        try:
            # レンダリング実行
            if template_name:
                html_content = self.render_with_template(nodes, template_name, context)
            else:
                html_content = self.render(nodes, context)

            # ファイル出力
            output_file = Path(output_path)

            # tmpディレクトリ配下への強制（CLAUDE.md準拠）
            if not str(output_file).startswith("tmp/"):
                output_file = Path("tmp") / output_file

            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.logger.info(f"レンダリング結果を出力: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"ファイル出力中にエラー: {output_path}, {e}")
            return False

    def get_css_themes(self) -> List[str]:
        """利用可能なCSSテーマ一覧取得"""
        try:
            return self.css_processor.get_available_themes()
        except Exception as e:
            self.logger.error(f"CSSテーマ一覧取得中にエラー: {e}")
            return ["default"]

    def optimize_css(self, css_content: str) -> str:
        """CSS最適化"""
        try:
            return self.css_utils.optimize_css(css_content)
        except Exception as e:
            self.logger.error(f"CSS最適化中にエラー: {e}")
            return css_content

    def validate_html(self, html_content: str) -> Dict[str, Any]:
        """HTML検証"""
        try:
            return self.html_utils.validate_html(html_content)
        except Exception as e:
            self.logger.error(f"HTML検証中にエラー: {e}")
            return {"valid": False, "errors": [str(e)]}

    def get_renderer_statistics(self) -> Dict[str, Any]:
        """レンダラー統計情報取得"""
        return {
            "output_format": self.output_format,
            "css_theme": self.css_theme,
            "accessibility_enabled": self.enable_accessibility,
            "responsive_enabled": self.enable_responsive,
            "available_themes": self.get_css_themes(),
            "config": self.config,
        }
