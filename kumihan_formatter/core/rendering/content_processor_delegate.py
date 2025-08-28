"""コンテンツ処理・最適化委譲モジュール

Issue #912 Renderer系統合リファクタリング対応
main_renderer.pyから分離されたコンテンツ処理・最適化機能
"""

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from ..main_renderer import MainRenderer

from ....core.ast_nodes import Node
import logging


class ContentProcessorDelegate:
    """コンテンツ処理・最適化委譲クラス

    MainRendererから分離されたコンテンツ処理・最適化機能を担当
    - 最適化されたノードリストレンダリング
    - エラー情報埋め込み最適化処理
    - HTML文字列処理・最適化
    - パフォーマンス改善機能
    """

    def __init__(self, main_renderer: "MainRenderer") -> None:
        """初期化

        Args:
            main_renderer: メインレンダラーインスタンス
        """
        self.main_renderer = main_renderer
        self.logger = logging.getLogger(__name__)

    def render_nodes_optimized(self, nodes: List[Node]) -> str:
        """最適化されたノードリストのHTML生成

        Issue #727 パフォーマンス最適化対応

        改善点:
        - StringBuilder パターンでガベージコレクション負荷軽減
        - HTML文字列結合の最適化
        - メモリ効率向上
        - 処理速度75%改善目標

        Args:
            nodes: レンダリングするASTノードリスト

        Returns:
            str: 最適化されたHTML出力
        """
        # Issue #700: graceful errors対応
        if (
            self.main_renderer.graceful_errors
            and self.main_renderer.embed_errors_in_html
        ):
            return self.render_nodes_with_errors_optimized(nodes)

        html_parts: List[str] = []
        html_parts_append = html_parts.append
        for node in nodes:
            html = self.main_renderer.render_node(node)
            html_parts_append(html)

        # 高速文字列結合（join最適化）
        return "\n".join(html_parts)

    def render_nodes_with_errors_optimized(self, nodes: List[Node]) -> str:
        """Issue #700: 最適化されたエラー情報埋め込みレンダリング

        Args:
            nodes: レンダリングするASTノードリスト

        Returns:
            str: エラー情報付きHTML出力
        """
        # StringBuilder パターン
        html_parts: List[str] = []
        html_parts_append = html_parts.append

        for node in nodes:
            html = self.main_renderer._element_delegate.render_node_optimized(node)
            if html:
                html_parts_append(html)

        # エラー情報をHTML前に効率的に挿入
        if (
            self.main_renderer.embed_errors_in_html
            and self.main_renderer.graceful_errors
        ):
            error_summary_html = self._render_error_summary_optimized()
            html_parts.insert(0, error_summary_html)

            # 効率的なエラーマーカー埋め込み
            html_with_markers = self._embed_error_markers_optimized(
                "\n".join(html_parts)
            )
            return html_with_markers

        return "\n".join(html_parts)

    def _render_error_summary_optimized(self) -> str:
        """最適化されたエラーサマリーHTML生成

        Returns:
            str: エラーサマリーHTML
        """
        if not self.main_renderer.graceful_errors:
            return ""

        error_count = 0
        warning_count = 0

        for error in self.main_renderer.graceful_errors:
            if error.severity == "error":
                error_count += 1
            elif error.severity == "warning":
                warning_count += 1

        total_count = len(self.main_renderer.graceful_errors)

        # StringBuilder パターンでHTML構築
        html_parts = [
            '<div class="kumihan-error-summary" id="error-summary">',
            "    <h3>🔍 記法エラーレポート</h3>",
            '    <div class="error-stats">',
            f'        <span class="error-count">❌ エラー: {error_count}件</span>',
            f'        <span class="warning-count">⚠️ 警告: {warning_count}件</span>',
            f'        <span class="total-count">📊 合計: {total_count}件</span>',
            "    </div>",
            '    <details class="error-details">',
            "        <summary>詳細を表示</summary>",
            '        <div class="error-list">',
        ]

        # 各エラーの詳細を効率的に追加
        for i, error in enumerate(self.main_renderer.graceful_errors, 1):
            error_html = self._render_single_error_optimized(error, i)
            html_parts.append(error_html)

        html_parts.extend(["        </div>", "    </details>", "</div>"])

        return "\n".join(html_parts)

    def _render_single_error_optimized(self, error: Any, error_number: int) -> str:
        """単一エラーの最適化レンダリング

        Args:
            error: エラーオブジェクト
            error_number: エラー番号

        Returns:
            str: 単一エラーHTML
        """

        # HTMLエスケープ関数の直接実装
        def escape_html(text):
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # XSS対策: エラー情報のエスケープ処理（最適化）
        safe_title = escape_html(error.display_title)
        safe_severity = escape_html(error.severity.upper())
        safe_content = error.html_content  # 既にエスケープ済み

        # 文字列テンプレート最適化
        return f"""
            <div class="error-item {error.html_class}" data-line="{error.line_number}">
                <div class="error-header">
                    <span class="error-number">#{error_number}</span>
                    <span class="error-title">{safe_title}</span>
                    <span class="error-severity">{safe_severity}</span>
                </div>
                <div class="error-content">
                    {safe_content}
                </div>
            </div>"""

    def _embed_error_markers_optimized(self, html: str) -> str:
        """最適化されたエラーマーカー埋め込み

        Args:
            html: 処理対象HTML

        Returns:
            str: エラーマーカー埋め込み済みHTML
        """
        if not self.main_renderer.graceful_errors:
            return html

        lines = html.split("\n")
        error_by_line: Dict[int, List[Any]] = {}
        modified_lines = []

        # エラーを行番号でグループ化
        for error in self.main_renderer.graceful_errors:
            line_no = getattr(error, "line_number", 1)
            if line_no not in error_by_line:
                error_by_line[line_no] = []
            error_by_line[line_no].append(error)

        # 効率的な行処理
        for line_no, line in enumerate(lines, 1):
            modified_lines.append(line)

            # エラーマーカー挿入（最適化）
            if line_no in error_by_line:
                for error in error_by_line[line_no]:
                    error_marker = self._create_error_marker_optimized(error)
                    modified_lines.append(error_marker)

        return "\n".join(modified_lines)

    def _create_error_marker_optimized(self, error: Any) -> str:
        """最適化されたエラーマーカー作成

        Args:
            error: エラーオブジェクト

        Returns:
            str: エラーマーカーHTML
        """

        # HTMLエスケープ関数の直接実装
        def escape_html(text):
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        safe_message = escape_html(error.message)
        safe_suggestion = escape_html(error.suggestion) if error.suggestion else ""
        error_icon = "❌" if error.severity == "error" else "⚠️"

        # f-string最適化
        suggestion_html = (
            f'<div class="error-suggestion">💡 {safe_suggestion}</div>'
            if safe_suggestion
            else ""
        )

        return (
            f"""<div class="kumihan-error-marker {error.html_class}" """
            f"""data-line="{error.line_number}">
    <div class="error-indicator">
        <span class="error-icon">{error_icon}</span>
        <span class="error-message">{safe_message}</span>
        {suggestion_html}
    </div>
</div>"""
        )
