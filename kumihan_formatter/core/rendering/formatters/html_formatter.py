"""HTML出力専用フォーマッター

Issue #912 Renderer系統合リファクタリング対応
HTML出力に特化した統合フォーマッタークラス
"""

from typing import Any, Dict, List, Optional

from ...ast_nodes import Node
from ...utilities.logger import get_logger
from ..base.renderer_protocols import (
    HtmlRendererProtocol,
    RenderContext,
    RenderResult,
    create_render_result,
)
from ..compound_renderer import CompoundElementRenderer
from ..content_processor import ContentProcessor
from ..element_renderer import ElementRenderer
from ..heading_collector import HeadingCollector
from ..html_formatter import HTMLFormatter as BaseHTMLFormatter


class HtmlFormatter(HtmlRendererProtocol):
    """HTML出力専用フォーマッター

    統合された機能:
    - HTML要素レンダリング
    - 複合要素処理
    - 見出し収集・ID生成
    - HTMLエスケープ・セキュリティ対応
    """

    def __init__(self, config: Optional[Any] = None) -> None:
        """HTML フォーマッターを初期化

        Args:
            config: 設定オブジェクト（オプショナル）
        """
        self.logger = get_logger(__name__)
        self.config = config

        # 統合されたレンダラーコンポーネント
        self.element_renderer = ElementRenderer()
        self.compound_renderer = CompoundElementRenderer()
        self.base_formatter = BaseHTMLFormatter()

        # 専用プロセッサー（型エラー回避のためAnyキャスト）
        from typing import cast

        self.content_processor = ContentProcessor(cast(Any, self))
        self.heading_collector = HeadingCollector()

        # メインレンダラーとして自身を設定
        self.element_renderer.set_main_renderer(self)

        # Graceful Error Handling (Issue #700)
        self.graceful_errors: List[Any] = []
        self.embed_errors_in_html = False

        # 脚注統合サポート
        self.footnotes_data: Optional[dict[str, Any]] = None

        self.logger.debug("HtmlFormatter initialized")

    def format(self, nodes: List[Node]) -> str:
        """ノードリストをHTML形式でフォーマット

        Args:
            nodes: フォーマットするASTノードリスト

        Returns:
            str: 生成されたHTML
        """
        self.logger.debug(f"Formatting {len(nodes)} nodes to HTML")

        # Issue #700: graceful errors対応
        if self.graceful_errors and self.embed_errors_in_html:
            return self._format_with_errors(nodes)

        html_parts = []
        for node in nodes:
            html = self.format_node(node)
            html_parts.append(html)

        # メインコンテンツHTML生成
        main_html = "\n".join(html_parts)

        # 脚注プレースホルダー処理
        main_html = self._process_footnote_placeholders(main_html)

        # 新記法脚注システム：文書末尾に脚注セクション追加
        main_html = self._append_footnotes_section(main_html)

        self.logger.debug(f"Generated HTML: {len(main_html)} characters")
        return main_html

    def format_node(self, node: Node) -> str:
        """単一ノードをHTML化

        Args:
            node: フォーマットするASTノード

        Returns:
            str: 生成されたHTML
        """
        if not isinstance(node, Node):
            raise TypeError(f"Expected Node instance, got {type(node)}")

        # デリゲートメソッドを動的に検索して呼び出し
        method_name = f"_format_{node.type}"
        formatter_method = getattr(self, method_name, self._format_generic)
        return formatter_method(node)

    def generate_toc(self, nodes: List[Node]) -> str:
        """目次生成

        Args:
            nodes: 見出し抽出対象のノードリスト

        Returns:
            str: 生成された目次HTML
        """
        headings = self.heading_collector.collect_headings(nodes)

        if not headings:
            return ""

        toc_parts = ['<div class="table-of-contents">', "<h2>目次</h2>", "<ul>"]

        for heading in headings:
            level = heading.get("level", 1)
            title = heading.get("title", "")
            heading_id = heading.get("id", "")

            # ネストレベルに応じたクラス
            indent_class = f"toc-level-{level}"

            if heading_id:
                toc_item = (
                    f'<li class="{indent_class}">'
                    f'<a href="#{heading_id}">{title}</a></li>'
                )
            else:
                toc_item = f'<li class="{indent_class}">{title}</li>'

            toc_parts.append(toc_item)

        toc_parts.extend(["</ul>", "</div>"])

        return "\n".join(toc_parts)

    def set_footnote_data(self, footnotes_data: dict[str, Any]) -> None:
        """脚注データを設定

        Args:
            footnotes_data: 脚注データ辞書
        """
        try:
            self.footnotes_data = footnotes_data
            self.logger.debug(
                f"Set footnote data: "
                f"{len(footnotes_data.get('footnotes', []))} footnotes"
            )
        except Exception as e:
            self.logger.error(f"Failed to set footnote data: {e}")
            self.footnotes_data = None

    def set_graceful_errors(
        self, errors: List[Any], embed_in_html: bool = True
    ) -> None:
        """Graceful Error Handlingのエラー情報を設定

        Args:
            errors: エラーリスト
            embed_in_html: HTMLにエラーを埋め込むかどうか
        """
        self.graceful_errors = errors
        self.embed_errors_in_html = embed_in_html

    def reset_counters(self) -> None:
        """内部カウンターをリセット"""
        self.heading_collector.reset_counters()
        self.element_renderer.heading_counter = 0

    # === プライベートメソッド: ノード別フォーマット ===

    def _format_generic(self, node: Node) -> str:
        """汎用ノードフォーマット"""
        return self.element_renderer.render_generic(node)

    def _format_p(self, node: Node) -> str:
        """段落ノードフォーマット"""
        return self.element_renderer.render_paragraph(node)

    def _format_strong(self, node: Node) -> str:
        """太字ノードフォーマット"""
        return self.element_renderer.render_strong(node)

    def _format_em(self, node: Node) -> str:
        """斜体ノードフォーマット"""
        return self.element_renderer.render_emphasis(node)

    def _format_div(self, node: Node) -> str:
        """divノードフォーマット"""
        return self.element_renderer.render_div(node)

    def _format_h1(self, node: Node) -> str:
        """h1見出しフォーマット"""
        return self.element_renderer.render_heading(node, 1)

    def _format_h2(self, node: Node) -> str:
        """h2見出しフォーマット"""
        return self.element_renderer.render_heading(node, 2)

    def _format_h3(self, node: Node) -> str:
        """h3見出しフォーマット"""
        return self.element_renderer.render_heading(node, 3)

    def _format_h4(self, node: Node) -> str:
        """h4見出しフォーマット"""
        return self.element_renderer.render_heading(node, 4)

    def _format_h5(self, node: Node) -> str:
        """h5見出しフォーマット"""
        return self.element_renderer.render_heading(node, 5)

    def _format_ul(self, node: Node) -> str:
        """順序なしリストフォーマット"""
        return self.element_renderer.render_unordered_list(node)

    def _format_ol(self, node: Node) -> str:
        """順序ありリストフォーマット"""
        return self.element_renderer.render_ordered_list(node)

    def _format_li(self, node: Node) -> str:
        """リスト項目フォーマット"""
        return self.element_renderer.render_list_item(node)

    def _format_details(self, node: Node) -> str:
        """details要素フォーマット"""
        return self.element_renderer.render_details(node)

    def _format_pre(self, node: Node) -> str:
        """整形済みテキストフォーマット"""
        return self.element_renderer.render_preformatted(node)

    def _format_code(self, node: Node) -> str:
        """インラインコードフォーマット"""
        return self.element_renderer.render_code(node)

    def _format_image(self, node: Node) -> str:
        """画像要素フォーマット"""
        return self.element_renderer.render_image(node)

    def _format_error(self, node: Node) -> str:
        """エラーノードフォーマット"""
        return self.element_renderer.render_error(node)

    def _format_toc(self, node: Node) -> str:
        """目次マーカーフォーマット"""
        return self.element_renderer.render_toc_placeholder(node)

    def _format_ruby(self, node: Node) -> str:
        """ルビ要素フォーマット"""
        return self.element_renderer.render_ruby(node)

    # === プライベートメソッド: ヘルパー機能 ===

    def _process_footnote_placeholders(self, html: str) -> str:
        """脚注プレースホルダーを処理"""
        if not self.footnotes_data:
            return html

        try:
            footnotes = self.footnotes_data.get("footnotes", [])

            if footnotes:
                for footnote in footnotes:
                    placeholder = f"[FOOTNOTE_REF_{footnote['number']}]"
                    footnote_link = (
                        f'<sup><a href="#footnote-{footnote["number"]}" '
                        f'id="footnote-ref-{footnote["number"]}">'
                        f'[{footnote["number"]}]</a></sup>'
                    )
                    html = html.replace(placeholder, footnote_link)

                self.logger.debug(
                    f"Replaced {len(footnotes)} footnote placeholders with HTML links"
                )

        except Exception as e:
            self.logger.warning(f"Failed to process footnote placeholders: {e}")

        return html

    def _append_footnotes_section(self, html: str) -> str:
        """文書末尾に脚注セクションを追加"""
        footnote_manager = (
            self.footnotes_data.get("manager") if self.footnotes_data else None
        )

        if footnote_manager and footnote_manager.get_footnotes():
            footnotes_html = footnote_manager.generate_footnotes_html(
                footnote_manager.get_footnotes()
            )

            if footnotes_html[0]:  # エラーがない場合
                html += "\n" + footnotes_html[0]
            elif footnotes_html[1]:  # エラーがある場合はログ出力
                self.logger.warning(f"Footnote generation errors: {footnotes_html[1]}")

        return html

    def _format_with_errors(self, nodes: List[Node]) -> str:
        """エラー情報を埋め込みながらフォーマット"""
        html_parts = []

        for node in nodes:
            html = self.format_node(node)
            if html:
                html_parts.append(html)

        # エラー情報をHTMLに埋め込み
        if self.embed_errors_in_html and self.graceful_errors:
            error_summary_html = self._render_error_summary()
            html_parts.insert(0, error_summary_html)

            # 各エラー箇所にマーカーを挿入
            html_with_markers = self._embed_error_markers("\n".join(html_parts))
            return html_with_markers

        return "\n".join(html_parts)

    def _render_error_summary(self) -> str:
        """エラーサマリーをHTMLで生成"""
        if not self.graceful_errors:
            return ""

        # エラーサマリーのヘッダー部分
        error_count = len(self.graceful_errors)
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
        for i, error in enumerate(self.graceful_errors, 1):
            from ..html_utils import escape_html

            # XSS対策: エラー情報のエスケープ処理
            safe_title = escape_html(error.display_title)
            safe_severity = escape_html(error.severity.upper())
            safe_content = (
                error.html_content
            )  # html_contentプロパティ内で既にエスケープ済み

            error_html = f"""
            <div class="error-item {error.html_class}" data-line="{error.line_number}">
                <div class="error-header">
                    <span class="error-number">#{i}</span>
                    <span class="error-title">{safe_title}</span>
                    <span class="error-severity">{safe_severity}</span>
                </div>
                <div class="error-content">
                    {safe_content}
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
        """HTML内のエラー発生箇所にマーカーを埋め込み"""
        if not self.graceful_errors:
            return html

        modified_lines = html.split("\n")

        for error in self.graceful_errors:
            if error.line_number and error.line_number <= len(modified_lines):
                from ..html_utils import escape_html

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

    # === メインレンダラー互換性メソッド ===

    def render_node(self, node: Node, context: Optional[RenderContext] = None) -> str:
        """単一ノードレンダリング（BaseRendererProtocol準拠）"""
        return self.format_node(node)

    def _render_node_with_depth(self, node: Node, depth: int = 0) -> str:
        """深度トラッキング付きノードレンダリング"""
        return self.content_processor.render_node_with_depth(node, depth)

    def _render_content(self, content: Any, depth: int = 0) -> str:
        """コンテンツレンダリング（再帰的）"""
        return self.content_processor.render_content(content, depth)

    @property
    def heading_counter(self) -> int:
        """現在の見出しカウンターを取得"""
        return self.element_renderer.heading_counter

    @heading_counter.setter
    def heading_counter(self, value: int) -> None:
        """見出しカウンターを設定"""
        self.element_renderer.heading_counter = value
        self.heading_collector.heading_counter = value

    # ==========================================
    # プロトコル準拠メソッド（HtmlRendererProtocol実装）
    # ==========================================

    def render(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> RenderResult:
        """統一レンダリングインターフェース（プロトコル準拠）"""
        try:
            if not nodes:
                return create_render_result(content="", success=True)

            # 複数ノードを順次処理
            html_parts = []
            for node in nodes:
                html_content = self.format_node(node)
                html_parts.append(html_content)

            combined_content = "\n".join(html_parts)
            return create_render_result(content=combined_content, success=True)
        except Exception as e:
            result = create_render_result(success=False)
            result.add_error(f"HTMLレンダリング失敗: {e}")
            return result

    def validate(
        self, node: Node, context: Optional[RenderContext] = None
    ) -> List[str]:
        """バリデーション実装（プロトコル準拠）"""
        errors = []
        try:
            # HTML特有の検証
            if not node:
                errors.append("ノードが空です")
            elif not hasattr(node, "node_type"):
                errors.append("ノードタイプが設定されていません")
            # HTMLレンダリング可能性の確認
            elif not hasattr(node, "content"):
                errors.append("ノードにコンテンツが設定されていません")
        except Exception as e:
            errors.append(f"HTMLバリデーションエラー: {e}")
        return errors

    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報（プロトコル準拠）"""
        return {
            "name": "HtmlFormatter",
            "version": "2.0.0",
            "supported_formats": ["html"],
            "capabilities": ["html_formatting", "error_embedding", "graceful_errors"],
            "output_format": "html",
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
        return format_hint in ["html", "text"]

    def render_html(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> str:
        """HTML固有レンダリングメソッド（プロトコル準拠）"""
        if not nodes:
            return ""

        # 複数ノードを順次処理
        html_parts = []
        for node in nodes:
            html_content = self.format_node(node)
            html_parts.append(html_content)

        return "\n".join(html_parts)

    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧を取得（BaseRendererProtocol準拠）"""
        return ["html", "text"]

    def validate_options(self, options: Dict[str, Any]) -> List[str]:
        """オプション検証（BaseRendererProtocol準拠）"""
        errors = []

        if not isinstance(options, dict):
            errors.append("オプションは辞書形式で指定してください")
            return errors

        # 有効なオプションキーの定義
        valid_keys = {
            "include_css",
            "include_js",
            "template_path",
            "theme",
            "custom_classes",
            "meta_tags",
            "lang",
            "charset",
        }

        # 不明なキーがないかチェック
        for key in options.keys():
            if key not in valid_keys:
                errors.append(f"不明なオプションキー: {key}")

        return errors

    def render_with_template(
        self,
        nodes: List[Node],
        template_path: str,
        context: Optional[RenderContext] = None,
    ) -> str:
        """テンプレート使用レンダリング（HtmlRendererProtocol準拠）"""
        # 基本実装：テンプレート機能を簡単に実装
        if not nodes:
            return ""

        # まずはテンプレートなしでレンダリング
        content = self.render_html(nodes, context)

        # 簡単なHTMLテンプレート適用
        template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Kumihan Formatter Output</title>
</head>
<body>
{content}
</body>
</html>"""
        return template

    def get_css_classes(self) -> Dict[str, str]:
        """使用可能なCSSクラス一覧を取得（HtmlRendererProtocol準拠）"""
        return {
            "header": "ヘッダー要素",
            "content": "メインコンテンツ",
            "footer": "フッター要素",
            "heading": "見出し要素",
            "paragraph": "段落要素",
            "list": "リスト要素",
            "code": "コード要素",
            "quote": "引用要素",
        }

    def escape_html(self, text: str) -> str:
        """HTMLエスケープ処理（HtmlRendererProtocol準拠）"""
        import html

        return html.escape(text)
