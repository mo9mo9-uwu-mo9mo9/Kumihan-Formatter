"""出力フォーマット・エラーハンドリング委譲モジュール

Issue #912 Renderer系統合リファクタリング対応
main_renderer.pyから分離された出力フォーマット・エラーハンドリング機能
"""

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from .main_renderer import MainRenderer

from ..ast_nodes import Node
import logging


class OutputFormatterDelegate:
    """出力フォーマット・エラーハンドリング委譲クラス

    MainRendererから分離された出力フォーマット・エラーハンドリング機能を担当
    - graceful errors処理
    - エラー情報HTML埋め込み
    - 出力フォーマット処理
    - レンダリングメトリクス
    """

    def __init__(self, main_renderer: "MainRenderer") -> None:
        """初期化

        Args:
            main_renderer: メインレンダラーインスタンス
        """
        self.main_renderer = main_renderer
        self.logger = logging.getLogger(__name__)

    def set_graceful_errors(
        self, errors: List[Any], embed_in_html: bool = True
    ) -> None:
        """Issue #700: graceful error handlingのエラー情報を設定

        Args:
            errors: エラーリスト
            embed_in_html: HTML埋め込みフラグ
        """
        self.main_renderer.graceful_errors = errors
        self.main_renderer.embed_errors_in_html = embed_in_html

    def render_nodes_with_errors(self, nodes: List[Node]) -> str:
        """Issue #700: エラー情報を埋め込みながらノードをレンダリング

        Args:
            nodes: レンダリングするASTノードリスト

        Returns:
            str: エラー情報付きHTML出力
        """
        html_parts = []

        for node in nodes:
            html = self.main_renderer.render_node(node)
            if html:
                html_parts.append(html)

        # エラー情報をHTMLに埋め込み
        if (
            self.main_renderer.embed_errors_in_html
            and self.main_renderer.graceful_errors
        ):
            error_summary_html = self._render_error_summary()
            html_parts.insert(0, error_summary_html)

            # 各エラー箇所にマーカーを挿入
            html_with_markers = self._embed_error_markers("\n".join(html_parts))
            return html_with_markers

        return "\n".join(html_parts)

    def _render_error_summary(self) -> str:
        """エラーサマリーをHTMLで生成

        Returns:
            str: エラーサマリーHTML
        """
        if not self.main_renderer.graceful_errors:
            return ""

        # エラーサマリーのヘッダー部分
        error_count = len(self.main_renderer.graceful_errors)
        summary_html = f"""
<div class="kumihan-error-summary">
    <details open>
        <summary class="error-summary-header">
            <span class="error-count-badge">{error_count}</span>
            <span class="error-summary-title">構文エラー・警告一覧</span>
        </summary>
        <div class="error-list">
"""

        # 各エラーの詳細を追加
        for i, error in enumerate(self.main_renderer.graceful_errors, 1):
            import html

            # XSS対策: エラー情報のエスケープ処理  
            safe_title = html.escape(error.display_title)
            safe_severity = html.escape(error.severity.upper())
            safe_content = (
                error.html_content
            )  # html_contentプロパティ内で既にエスケープ済み

            # ハイライト付きコンテキストと修正提案を追加
            highlighted_context = error.get_highlighted_context()
            correction_suggestions_html = error.get_correction_suggestions_html()

            error_html = f"""
            <div class="error-item {error.html_class}" data-line="{error.line_number}">
                <div class="error-header">
                    <span class="error-number">#{i}</span>
                    <span class="error-title">{safe_title}</span>
                    <span class="error-severity">{safe_severity}</span>
                </div>
                <div class="error-content">
                    {safe_content}
                    {(f'<div class="error-context-highlighted">'
                      f'{highlighted_context}</div>')
                     if highlighted_context != error.context else ''}
                    {correction_suggestions_html
                     and f'<div class="correction-suggestions">'
                         f'<h4>修正提案:</h4>{correction_suggestions_html}</div>' or ''}
                </div>
            </div>
"""
            summary_html += error_html

        summary_html += """
        </div>
    </details>
</div>
"""
        return summary_html

    def _embed_error_markers(self, html: str) -> str:
        """HTML内のエラー発生箇所にマーカーを埋め込み

        Args:
            html: 処理対象HTML

        Returns:
            str: エラーマーカー埋め込み済みHTML
        """
        if not self.main_renderer.graceful_errors:
            return html

        modified_lines = html.split("\n")

        for error in self.main_renderer.graceful_errors:
            if error.line_number and error.line_number <= len(modified_lines):
                from ..html_escaping import escape_html

                # XSS対策: エラー情報のエスケープ処理
                safe_message = escape_html(error.message)
                safe_suggestion = (
                    escape_html(error.suggestion) if error.suggestion else ""
                )
                error_icon = "❌" if error.severity == "error" else "⚠️"

                error_marker = f"""
<div class="kumihan-error-marker {error.html_class}" data-line="{error.line_number}">
    <div class="error-indicator">
        <span class="error-icon">{error_icon}</span>
        <span class="error-message">{safe_message}</span>
        {f'<div class="suggestion">💡{safe_suggestion}</div>' if safe_suggestion else ''}
    </div>
</div>"""
                modified_lines.insert(error.line_number - 1, error_marker)

        return "\n".join(modified_lines)

    def get_rendering_metrics(self) -> Dict[str, Any]:
        """レンダリングメトリクスを取得

        Returns:
            Dict[str, Any]: メトリクス情報
        """
        cache_size = len(
            getattr(self.main_renderer._element_delegate, "_renderer_method_cache", {})
        )
        return {
            "renderer_cache_size": cache_size,
            "graceful_errors_count": len(self.main_renderer.graceful_errors),
            "embed_errors_enabled": self.main_renderer.embed_errors_in_html,
            "heading_counter": self.main_renderer.heading_counter,
        }
