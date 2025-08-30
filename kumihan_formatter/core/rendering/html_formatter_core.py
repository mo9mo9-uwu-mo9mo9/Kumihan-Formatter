"""
HTMLFormatterCore - HTMLフォーマッター中核処理
=============================================

Issue #1215対応: 不足していたHTMLFormatterCoreクラスの実装
"""

import logging
from typing import Any, Dict, List, Optional

from ..ast_nodes import Node


class HTMLFormatterCore:
    """HTMLフォーマッター中核処理クラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        HTMLFormatterCore初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # エラー処理用設定
        self.graceful_errors: List[Dict[str, Any]] = []
        self.embed_errors_in_html = True

    def format(self, nodes: List[Node]) -> str:
        """
        ノードリストをHTML文字列にフォーマット

        Args:
            nodes: フォーマット対象ノードリスト

        Returns:
            HTML文字列
        """
        try:
            if not nodes:
                return ""

            html_parts = []
            for node in nodes:
                formatted = self.format_node(node)
                if formatted:
                    html_parts.append(formatted)

            return "\n".join(html_parts)

        except Exception as e:
            self.logger.error(f"HTML フォーマット中にエラー: {e}")
            return f'<div class="error">フォーマットエラー: {str(e)}</div>'

    def format_node(self, node: Node) -> str:
        """
        単一ノードをHTML文字列にフォーマット

        Args:
            node: フォーマット対象ノード

        Returns:
            HTML文字列
        """
        try:
            tag = getattr(node, "tag", "div")
            content = getattr(node, "content", "")

            # 基本的なHTMLタグ生成
            if tag == "p":
                return f"<p>{self._escape_html(str(content))}</p>"
            elif tag.startswith("h") and tag[1:].isdigit():
                level = tag[1:]
                return f"<h{level}>{self._escape_html(str(content))}</h{level}>"
            elif tag == "div":
                return f"<div>{self._escape_html(str(content))}</div>"
            elif tag == "span":
                return f"<span>{self._escape_html(str(content))}</span>"
            else:
                return f"<{tag}>{self._escape_html(str(content))}</{tag}>"

        except Exception as e:
            self.logger.error(f"ノードフォーマット中にエラー: {e}")
            return f'<div class="error">ノードフォーマットエラー: {str(e)}</div>'

    def render(
        self, nodes: List[Node], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        ノードリストをコンテキスト付きでレンダリング

        Args:
            nodes: レンダリング対象ノードリスト
            context: レンダリングコンテキスト

        Returns:
            レンダリング結果HTML
        """
        try:
            # 基本的にはformatと同じだが、コンテキストを考慮
            return self.format(nodes)

        except Exception as e:
            self.logger.error(f"レンダリング中にエラー: {e}")
            return f'<div class="error">レンダリングエラー: {str(e)}</div>'

    def render_html(
        self, nodes: List[Node], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        HTML特化レンダリング

        Args:
            nodes: レンダリング対象ノードリスト
            context: レンダリングコンテキスト

        Returns:
            HTML文字列
        """
        return self.render(nodes, context)

    def render_node(self, node: Node, context: Optional[Dict[str, Any]] = None) -> str:
        """
        単一ノードレンダリング

        Args:
            node: レンダリング対象ノード
            context: レンダリングコンテキスト

        Returns:
            レンダリング結果HTML
        """
        return self.format_node(node)

    def reset_counters(self) -> None:
        """カウンター類をリセット"""
        # 基本実装では特にカウンターなし
        pass

    def _escape_html(self, text: str) -> str:
        """HTML文字列のエスケープ"""
        import html

        return html.escape(str(text))

    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報を取得"""
        return {
            "name": "HTMLFormatterCore",
            "version": "1.0.0",
            "config": self.config,
            "graceful_errors_count": len(self.graceful_errors),
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応確認"""
        supported_formats = ["html", "xhtml", "xml"]
        return format_hint.lower() in supported_formats

    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧"""
        return ["html", "xhtml", "xml"]

    # 基本フォーマッターメソッド群
    def _format_generic(self, node: Node) -> str:
        """汎用フォーマット"""
        return self.format_node(node)

    def _format_p(self, node: Node) -> str:
        """段落フォーマット"""
        content = getattr(node, "content", "")
        return f"<p>{self._escape_html(str(content))}</p>"

    def _format_strong(self, node: Node) -> str:
        """太字フォーマット"""
        content = getattr(node, "content", "")
        return f"<strong>{self._escape_html(str(content))}</strong>"

    def _format_em(self, node: Node) -> str:
        """イタリックフォーマット"""
        content = getattr(node, "content", "")
        return f"<em>{self._escape_html(str(content))}</em>"

    def _format_div(self, node: Node) -> str:
        """div要素フォーマット"""
        content = getattr(node, "content", "")
        return f"<div>{self._escape_html(str(content))}</div>"

    def _format_h1(self, node: Node) -> str:
        """H1見出しフォーマット"""
        content = getattr(node, "content", "")
        return f"<h1>{self._escape_html(str(content))}</h1>"

    def _format_h2(self, node: Node) -> str:
        """H2見出しフォーマット"""
        content = getattr(node, "content", "")
        return f"<h2>{self._escape_html(str(content))}</h2>"

    def _format_h3(self, node: Node) -> str:
        """H3見出しフォーマット"""
        content = getattr(node, "content", "")
        return f"<h3>{self._escape_html(str(content))}</h3>"

    def _format_h4(self, node: Node) -> str:
        """H4見出しフォーマット"""
        content = getattr(node, "content", "")
        return f"<h4>{self._escape_html(str(content))}</h4>"

    def _format_h5(self, node: Node) -> str:
        """H5見出しフォーマット"""
        content = getattr(node, "content", "")
        return f"<h5>{self._escape_html(str(content))}</h5>"

    def _format_ul(self, node: Node) -> str:
        """箇条書きリストフォーマット"""
        content = getattr(node, "content", "")
        return f"<ul>{content}</ul>"

    def _format_ol(self, node: Node) -> str:
        """番号付きリストフォーマット"""
        content = getattr(node, "content", "")
        return f"<ol>{content}</ol>"

    def _format_li(self, node: Node) -> str:
        """リスト項目フォーマット"""
        content = getattr(node, "content", "")
        return f"<li>{self._escape_html(str(content))}</li>"

    def _format_details(self, node: Node) -> str:
        """詳細要素フォーマット"""
        content = getattr(node, "content", "")
        return f"<details>{content}</details>"

    def _format_pre(self, node: Node) -> str:
        """整形済みテキストフォーマット"""
        content = getattr(node, "content", "")
        return f"<pre>{self._escape_html(str(content))}</pre>"

    def _format_code(self, node: Node) -> str:
        """コードフォーマット"""
        content = getattr(node, "content", "")
        return f"<code>{self._escape_html(str(content))}</code>"

    def _format_image(self, node: Node) -> str:
        """画像フォーマット"""
        src = getattr(node, "src", "")
        alt = getattr(node, "alt", "")
        return f'<img src="{src}" alt="{alt}">'

    def _format_error(self, node: Node) -> str:
        """エラーフォーマット"""
        content = getattr(node, "content", "Error")
        return f'<div class="error">{self._escape_html(str(content))}</div>'

    def _format_toc(self, node: Node) -> str:
        """目次フォーマット"""
        content = getattr(node, "content", "")
        return f'<nav class="toc">{content}</nav>'

    def _format_ruby(self, node: Node) -> str:
        """ルビフォーマット"""
        content = getattr(node, "content", "")
        ruby = getattr(node, "ruby", "")
        return f"<ruby>{self._escape_html(str(content))}<rt>{self._escape_html(str(ruby))}</rt></ruby>"


class HTMLValidator:
    """HTML検証クラス - 基本実装"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def validate(
        self, node: Node, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """ノード検証"""
        errors = []

        # 基本的な検証
        if not hasattr(node, "tag"):
            errors.append("ノードにタグが設定されていません")

        return errors

    def validate_options(self, options: Dict[str, Any]) -> List[str]:
        """オプション検証"""
        return []  # 基本実装では常に有効


class CSSProcessor:
    """CSS処理クラス - 基本実装"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def get_css_classes(self) -> Dict[str, List[str]]:
        """CSSクラス一覧取得"""
        return {
            "basic": ["container", "content", "error"],
            "text": ["paragraph", "heading", "emphasis"],
            "structure": ["section", "article", "aside"],
        }
