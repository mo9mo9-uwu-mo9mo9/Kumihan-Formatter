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
