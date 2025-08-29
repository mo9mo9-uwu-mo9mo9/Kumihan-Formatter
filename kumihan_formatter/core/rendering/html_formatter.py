"""
統合HTML フォーマッター
分割されたモジュールを統合する新しいHTMLFormatter
"""

import logging
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.ast_nodes.node import Node
from .css_processor import CSSProcessor
from .html_utilities import HTMLUtilities
from .html_formatter_core import HTMLFormatterCore, HTMLValidator
from .html_footnote_processor import FootnoteManager


class HtmlFormatter:
    """統合HTML フォーマッター（分割版統合）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """統合フォーマッター初期化"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 分割されたコンポーネントを初期化
        self.core = HTMLFormatterCore(config)
        self.validator = HTMLValidator(config)
        self.css_processor = CSSProcessor(config)
        self.footnote_manager = FootnoteManager(config)
        self.utilities = HTMLUtilities(config)

        # 状態管理（互換性維持）
        self.graceful_errors: List[Dict[str, Any]] = []
        self.embed_errors_in_html = True
        self.footnotes_data: Optional[Dict[str, Any]] = None

    # コア機能の委譲
    def format(self, nodes: List[Node]) -> str:
        """ノードリストをHTMLにフォーマット"""
        return self.core.format(nodes)

    def format_node(self, node: Node) -> str:
        """単一ノードをHTMLにフォーマット"""
        return self.core.format_node(node)

    def render(
        self, nodes: List[Node], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """ノードリストをレンダリング"""
        return self.core.render(nodes, context)

    def render_html(
        self, nodes: List[Node], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """HTML特化レンダリング"""
        return self.core.render_html(nodes, context)

    def render_node(self, node: Node, context: Optional[Dict[str, Any]] = None) -> str:
        """単一ノードレンダリング"""
        return self.core.render_node(node, context)

    # 検証機能の委譲
    def validate(
        self, node: Node, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """ノード検証"""
        return self.validator.validate(node, context)

    def validate_options(self, options: Dict[str, Any]) -> List[str]:
        """オプション検証"""
        return self.validator.validate_options(options)

    # CSS機能の委譲
    def get_css_classes(self) -> Dict[str, List[str]]:
        """CSSクラス一覧取得"""
        return self.css_processor.get_css_classes()

    # 脚注機能の委譲
    def set_footnote_data(self, footnotes_data: Dict[str, Any]) -> None:
        """脚注データ設定"""
        self.footnotes_data = footnotes_data
        self.footnote_manager.set_footnote_data(footnotes_data)

    def set_graceful_errors(
        self, errors: List[Dict[str, Any]], embed_in_html: bool = True
    ) -> None:
        """グレースフル エラー設定"""
        self.graceful_errors = errors
        self.embed_errors_in_html = embed_in_html
        self.core.graceful_errors = errors
        self.core.embed_errors_in_html = embed_in_html

    def reset_counters(self) -> None:
        """カウンタリセット"""
        self.core.reset_counters()
        self.utilities.heading_counter(0)

    # ユーティリティ機能の委譲
    def escape_html(self, text: str) -> str:
        """HTML エスケープ"""
        return self.utilities.escape_html(text)

    def heading_counter(self, value: Optional[int] = None) -> int:
        """見出しカウンター"""
        return self.utilities.heading_counter(value)

    # 目次生成
    def generate_toc(self, nodes: List[Node]) -> str:
        """目次生成"""
        headings = []

        # ノードから見出し要素を抽出
        for node in nodes:
            if hasattr(node, "tag") and node.tag.lower() in [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
            ]:
                level = int(node.tag[1])
                title = getattr(node, "content", "")
                heading_id = self.utilities.generate_heading_id(title)

                headings.append({"level": level, "title": title, "id": heading_id})

        return self.utilities.generate_toc_from_headings(headings)

    # 拡張機能
    def render_with_template(
        self,
        nodes: List[Node],
        template_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """テンプレート使用レンダリング"""
        try:
            if not nodes:
                return ""

            context = context or {}

            # 基本コンテンツ生成
            content = self.render_html(nodes, context)

            # テンプレート適用（簡易版）
            if template_path:
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        template = f.read()

                    # 基本的な変数置換
                    template = template.replace("{{content}}", content)
                    template = template.replace(
                        "{{title}}", context.get("title", "ドキュメント")
                    )

                    return template

                except Exception as e:
                    self.logger.error(f"テンプレート読み込みエラー: {e}")
                    return content

            return content

        except Exception as e:
            self.logger.error(f"テンプレートレンダリングエラー: {e}")
            return f'<div class="error">テンプレートエラー: {str(e)}</div>'

    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報"""
        return {
            "name": "HtmlFormatter (Integrated)",
            "version": "2.0.0",
            "components": {
                "core": self.core.get_renderer_info(),
                "validator": "HTMLValidator v1.0.0",
                "css_processor": "CSSProcessor v1.0.0",
                "footnote_manager": "FootnoteManager v1.0.0",
                "utilities": self.utilities.get_utility_info(),
            },
            "formats": self.get_supported_formats(),
            "features": [
                "advanced_formatting",
                "validation",
                "css_processing",
                "footnote_management",
                "template_support",
                "accessibility_features",
            ],
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応確認"""
        return self.core.supports_format(format_hint)

    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧"""
        return self.core.get_supported_formats()

    # プライベートメソッド（内部実装）
    def _format_with_errors(self, nodes: List[Node]) -> str:
        """エラー付きフォーマット"""
        html_parts = []

        for node in nodes:
            html = self.format_node(node)
            if html:
                html_parts.append(html)

        main_html = "\n".join(html_parts)

        # エラー情報を埋め込み
        if self.graceful_errors and self.embed_errors_in_html:
            error_summary_html = self._render_error_summary()
            if error_summary_html:
                main_html = f"{error_summary_html}\n{main_html}"

            # エラーマーカーを埋め込み
            html_with_markers = self._embed_error_markers(main_html)
            return html_with_markers

        return main_html

    def _render_error_summary(self) -> str:
        """エラーサマリーレンダリング"""
        if not self.graceful_errors:
            return ""

        error_count = len(self.graceful_errors)
        summary_html = f"""
<div class="error-summary" role="alert">
    <h3>⚠️ 解析エラー ({error_count}件)</h3>
    <details>
        <summary>詳細を表示</summary>
        <ol class="error-list">
"""

        for i, error in enumerate(self.graceful_errors, 1):
            safe_title = self.escape_html(error.get("title", f"エラー {i}"))
            safe_severity = self.escape_html(error.get("severity", "warning"))
            safe_content = self.escape_html(error.get("content", ""))

            error_html = f"""
            <li class="error-item severity-{safe_severity}">
                <strong>{safe_title}</strong>: {safe_content}
            </li>"""

            summary_html += error_html

        summary_html += """
        </ol>
    </details>
</div>
"""
        return summary_html

    def _embed_error_markers(self, html: str) -> str:
        """エラーマーカー埋め込み"""
        if not self.graceful_errors:
            return html

        modified_lines = html.split("\n")

        for error in self.graceful_errors:
            if "line_number" in error:
                line_num = error.get("line_number", 1) - 1
                if 0 <= line_num < len(modified_lines):
                    safe_message = self.escape_html(error.get("message", ""))
                    safe_suggestion = self.escape_html(error.get("suggestion", ""))

                    # エラーアイコン
                    error_icon = "⚠️" if error.get("severity") == "warning" else "❌"

                    error_marker = f"""
                    <span class="inline-error" title="{safe_message}">
                        {error_icon} {safe_suggestion}
                    </span>"""

                    modified_lines[line_num] += error_marker

        return "\n".join(modified_lines)

    def _process_footnote_placeholders(self, html: str) -> str:
        """脚注プレースホルダー処理"""
        return self.footnote_manager.process_footnote_placeholders(html)

    def _append_footnotes_section(self, html: str) -> str:
        """脚注セクション追加"""
        return self.footnote_manager.append_footnotes_section(html)

    # 互換性維持のための個別フォーマッターメソッド
    def _format_generic(self, node: Node) -> str:
        return self.core._format_generic(node)

    def _format_p(self, node: Node) -> str:
        return self.core._format_p(node)

    def _format_strong(self, node: Node) -> str:
        return self.core._format_strong(node)

    def _format_em(self, node: Node) -> str:
        return self.core._format_em(node)

    def _format_div(self, node: Node) -> str:
        return self.core._format_div(node)

    def _format_h1(self, node: Node) -> str:
        return self.core._format_h1(node)

    def _format_h2(self, node: Node) -> str:
        return self.core._format_h2(node)

    def _format_h3(self, node: Node) -> str:
        return self.core._format_h3(node)

    def _format_h4(self, node: Node) -> str:
        return self.core._format_h4(node)

    def _format_h5(self, node: Node) -> str:
        return self.core._format_h5(node)

    def _format_ul(self, node: Node) -> str:
        return self.core._format_ul(node)

    def _format_ol(self, node: Node) -> str:
        return self.core._format_ol(node)

    def _format_li(self, node: Node) -> str:
        return self.core._format_li(node)

    def _format_details(self, node: Node) -> str:
        return self.core._format_details(node)

    def _format_pre(self, node: Node) -> str:
        return self.core._format_pre(node)

    def _format_code(self, node: Node) -> str:
        return self.core._format_code(node)

    def _format_image(self, node: Node) -> str:
        return self.core._format_image(node)

    def _format_error(self, node: Node) -> str:
        return self.core._format_error(node)

    def _format_toc(self, node: Node) -> str:
        return self.core._format_toc(node)

    def _format_ruby(self, node: Node) -> str:
        return self.core._format_ruby(node)
