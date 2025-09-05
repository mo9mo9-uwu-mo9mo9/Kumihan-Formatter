"""MainRenderer - 統合レンダラーシステム緊急実装 (Issue #1221対応)"""

from ...core.utilities.logger import get_logger
from .markdown_renderer import MarkdownRenderer
from .simple_compat_renderer import SimpleCompatRenderer
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class MainRenderer:
    """統合MainRendererクラス - 緊急対応版"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """MainRenderer初期化"""
        self.logger = get_logger(__name__)
        self.config = config or {}

        # テンプレート管理
        from ..templates import TemplateSelector

        self.template_selector = TemplateSelector()

        # レンダラー初期化
        from .markdown_renderer import MarkdownRenderer
        from ..processing.markdown_converter import SimpleMarkdownConverter
        from ..processing.markdown_factory import MarkdownFactory

        self.markdown_renderer = MarkdownRenderer()
        self.markdown_converter = SimpleMarkdownConverter()
        self.markdown_factory = MarkdownFactory()

        # HTML関連 - use functions instead of class
        from ..utilities import css_utils

        self.css_utils = css_utils

        # HTML formatter - create a simple placeholder
        self.html_formatter = self._create_html_formatter()

        # Fix for delegate compatibility
        from ..common.error_base import GracefulSyntaxError

        self.graceful_errors: List[GracefulSyntaxError] = []
        self.embed_errors_in_html: bool = False
        self.heading_counter: int = 0
        self._element_delegate: Optional[Any] = None
        # Simple互換出力を専用モジュールに委譲
        self._simple_renderer = SimpleCompatRenderer()

    def _create_html_formatter(self) -> Any:
        """HTML formatter placeholder for compatibility"""

        class SimpleHtmlFormatter:
            def render(
                self, elements: List[Any], context: Optional[Dict[str, Any]] = None
            ) -> str:
                # Simple HTML rendering fallback
                html_parts = []
                for element in elements:
                    if hasattr(element, "type") and element.type:
                        if element.type == "p":
                            html_parts.append(f"<p>{str(element.content)}</p>")
                        elif element.type.startswith("h"):
                            html_parts.append(
                                f"<{element.type}>{str(element.content)}</{element.type}>"
                            )
                        else:
                            html_parts.append(
                                f"<div class='{element.type}'>{str(element.content)}</div>"
                            )
                    else:
                        html_parts.append(f"<p>{str(element)}</p>")
                return "\n".join(html_parts)

        return SimpleHtmlFormatter()

    def render(
        self, parsed_result: Any, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        メインレンダリング処理 - 複数レンダラー統合対応

        Args:
            parsed_result: パーサーからの解析結果
                - str: Markdownテキスト → MarkdownRenderer使用
                - dict: パース結果辞書 → Kumihan専用レンダリング使用
                - list: ASTノードリスト → HtmlFormatter使用
                - その他: 文字列変換後MarkdownRenderer使用
            context: レンダリングコンテキスト
                - template: テンプレート名 (default, minimal, docs等)
                - その他レンダリングオプション

        Returns:
            HTML文字列 (UTF-8エンコード済み)

        Raises:
            レンダリングエラー時はエラーHTMLを返却（例外なし）
        """
        try:
            context = context or {}
            parsed_type = type(parsed_result).__name__

            self.logger.debug(
                f"Rendering started: type={parsed_type}, context_keys={list(context.keys())}"
            )

            # 解析結果の型判定・適切なレンダラー選択
            if isinstance(parsed_result, dict) and "elements" in parsed_result:
                # パーサー辞書結果の場合: Kumihan専用レンダリング
                self.logger.debug(
                    "Using Kumihan-specific rendering for parser dictionary"
                )
                html_content = self._render_kumihan_elements(parsed_result, context)

            elif isinstance(parsed_result, str):
                # 文字列の場合: MarkdownRenderer使用
                self.logger.debug("Using MarkdownRenderer for string input")
                html_content = self.markdown_renderer.render(parsed_result)

            elif isinstance(parsed_result, list):
                # Nodeリストの場合: HtmlFormatter使用（完全HTML文書生成）
                template = context.get("template", "default")
                self.logger.debug(
                    f"Using HtmlFormatter for list input, template={template}"
                )

                # 完全HTML文書テンプレートを使用
                html_content = self._render_complete_html_document(
                    parsed_result, context
                )

            elif hasattr(parsed_result, "type") and hasattr(parsed_result, "content"):
                # 単一Nodeオブジェクトの場合: HtmlFormatter使用（完全HTML文書生成）
                self.logger.debug(f"Converting single Node to list: type={parsed_type}")
                html_content = self._render_complete_html_document(
                    [parsed_result], context
                )

            elif hasattr(parsed_result, "__iter__") and not isinstance(
                parsed_result, str
            ):
                # 反復可能オブジェクトの場合: HtmlFormatter使用
                self.logger.debug(f"Converting iterable to list: type={parsed_type}")
                html_content = self.html_formatter.render(list(parsed_result), context)

            else:
                # その他の場合: 文字列化してMarkdownRenderer使用
                self.logger.warning(
                    f"Fallback to string conversion: type={parsed_type}"
                )
                str_content = str(parsed_result) if parsed_result is not None else ""
                html_content = self.markdown_renderer.render(str_content)

            # 結果検証
            if not html_content:
                html_content = "<p>（空のコンテンツ）</p>"
                self.logger.warning("Empty rendering result, using fallback")

            self.logger.info(
                f"Rendering completed successfully: {len(html_content)} chars, type={parsed_type}"
            )
            return html_content

        except Exception as e:
            error_msg = (
                f"Rendering failed for type {type(parsed_result).__name__}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            return f'<div class="error" role="alert">⚠️ {error_msg}</div>'

    def render_to_file(
        self,
        parsed_result: Any,
        output_file: Union[str, Path],
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        ファイル出力レンダリング - tmp配下強制出力対応

        Args:
            parsed_result: パーサーからの解析結果（renderメソッドと同様）
            output_file: 出力ファイルパス（パス・ファイル名のみ使用）
            template: テンプレート名（contextに統合、後方互換性維持）
            context: レンダリングコンテキスト
                - template: テンプレート名
                - その他レンダリングオプション

        Returns:
            bool: 成功時True、失敗時False

        Notes:
            - 出力パスは呼び出し元指定を基本的に尊重し、必要なディレクトリを自動作成します。
        """
        try:
            # 入力検証
            if not output_file:
                raise ValueError("output_file is required")

            # 出力パス決定（テスト環境対応）
            output_path = Path(output_file)

            # 以前は tmp/ 強制出力。現在は指定パスを尊重

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # コンテキスト準備
            context = context or {}
            if template:
                context["template"] = template
                self.logger.debug(f"Template specified: {template}")

            # メインレンダリング処理実行
            self.logger.debug("Starting file rendering process")
            html_content = self.render(parsed_result, context)

            # 結果検証
            if not html_content:
                raise ValueError("レンダリング結果が空またはNullです")

            if not html_content.strip():
                self.logger.warning("レンダリング結果が空白のみです - 出力継続")

            # ファイル出力実行
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                f.write(html_content)

            # 出力検証
            if not output_path.exists():
                raise IOError(f"出力ファイルが作成されませんでした: {output_path}")

            file_size = output_path.stat().st_size

            self.logger.info(
                f"File output completed successfully: {output_path} "
                f"({file_size} bytes, {len(html_content)} chars)"
            )
            return True

        except Exception as e:
            error_detail = f"File output failed: {str(e)} [output_file={output_file}]"
            self.logger.error(error_detail, exc_info=True)
            return False

    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報取得"""
        return {
            "name": "MainRenderer (Integrated)",
            "version": "1.0.0-emergency",
            "components": {
                "markdown_renderer": "MarkdownRenderer v1.0.0",
                "html_formatter": "HtmlFormatter v2.0.0",
            },
            "status": "emergency_implementation",
            "supported_types": ["string", "list", "nodes"],
            "emergency_fix": "Issue #1221 - Critical import error resolved",
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応確認"""
        supported_formats = ["html", "markdown", "kumihan", "auto"]
        return format_hint.lower() in supported_formats

    def _render_complete_html_document(
        self, nodes: List[Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """完全なHTML文書生成"""
        try:
            context = context or {}

            # コンテンツ部分をレンダリング
            body_content = self.html_formatter.render(nodes, context)

            # ページタイトル決定
            title = context.get("title", "Kumihan文書")

            # 完全HTML文書テンプレート
            complete_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .error {{
            color: #d32f2f;
            background: #ffebee;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #d32f2f;
        }}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""

            return complete_html

        except Exception as e:
            self.logger.error(f"Complete HTML document generation failed: {e}")
            return f'<div class="error">HTML文書生成エラー: {str(e)}</div>'

    def _render_kumihan_elements(
        self, parsed_dict: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Kumihan要素専用レンダリング"""
        try:
            context = context or {}
            elements = parsed_dict.get("elements", [])

            # 個別要素をHTMLに変換
            html_parts = []
            for element in elements:
                html_part = self._render_single_element(element)
                if html_part:
                    html_parts.append(html_part)

            # 完全HTML文書として組み立て
            body_content = "\n".join(html_parts)

            # ページタイトル決定
            title = context.get("title", "Kumihan文書")

            # 完全HTML文書テンプレート（Kumihanスタイル付き）
            complete_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .error {{
            color: #d32f2f;
            background: #ffebee;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #d32f2f;
        }}
        .kumihan-block {{
            margin: 16px 0;
            padding: 12px 16px;
            border-radius: 6px;
            border-left: 4px solid;
        }}
        .kumihan-block.important {{
            background-color: #fff3e0;
            border-color: #f57c00;
            color: #e65100;
        }}
        .kumihan-block.info {{
            background-color: #e3f2fd;
            border-color: #1976d2;
            color: #0d47a1;
        }}
        .kumihan-block.warning {{
            background-color: #fff8e1;
            border-color: #f9a825;
            color: #f57f17;
        }}
        .kumihan-block.note {{
            background-color: #f3e5f5;
            border-color: #7b1fa2;
            color: #4a148c;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin: 24px 0 16px 0;
            font-weight: 600;
        }}
        p {{
            margin: 16px 0;
        }}
        ul, ol {{
            margin: 16px 0;
            padding-left: 32px;
        }}
        li {{
            margin: 4px 0;
        }}
        strong {{
            font-weight: 600;
        }}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""

            return complete_html

        except Exception as e:
            self.logger.error(f"Kumihan elements rendering failed: {e}")
            return f'<div class="error">Kumihan要素レンダリングエラー: {str(e)}</div>'

    def _render_single_element(self, element: Dict[str, Any]) -> str:
        """単一要素のHTMLレンダリング"""
        try:
            element_type = element.get("type", "")
            content = element.get("content", "")
            attributes = element.get("attributes", {})

            if element_type == "kumihan_block":
                # Kumihanブロックの特別処理
                decoration = attributes.get("decoration", "").lower()
                css_class = self._get_kumihan_css_class(decoration)
                return f'<div class="kumihan-block {css_class}">{self._escape_html(content)}</div>'

            elif element_type.startswith("heading_"):
                # 見出しレンダリング
                level = attributes.get("level", "1")
                return f"<h{level}>{self._escape_html(content)}</h{level}>"

            elif element_type == "paragraph":
                # 段落レンダリング（インライン書式対応）
                return f"<p>{content}</p>"  # contentは既にprocessed

            elif element_type == "list_item":
                # リスト項目レンダリング
                return f"<li>{self._escape_html(content)}</li>"

            else:
                # その他の要素
                return f'<div class="element-{element_type}">{self._escape_html(content)}</div>'

        except Exception as e:
            self.logger.error(f"Single element rendering failed: {e}")
            return f'<div class="error">要素レンダリングエラー: {str(e)}</div>'

    def _get_kumihan_css_class(self, decoration: str) -> str:
        """Kumihan装飾からCSS class取得"""
        decoration = decoration.lower().strip()

        # 装飾名のマッピング
        decoration_map = {
            "重要": "important",
            "情報": "info",
            "注意": "warning",
            "注目": "warning",
            "メモ": "note",
            "覚書": "note",
            # 英語版
            "important": "important",
            "info": "info",
            "warning": "warning",
            "note": "note",
        }

        return decoration_map.get(decoration, "note")

    def _escape_html(self, text: str) -> str:
        """HTML エスケープ処理"""
        if not text:
            return ""

        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def render_simple_parsed_data(self, parsed_data: Dict[str, Any]) -> str:
        """SimpleHTMLRendererとの互換性確保（統合版）

        互換性のため、本メソッドは内部のラッパー経由で処理します。
        テストが `self._render_simple_elements` をパッチできるように、
        主要処理はラッパーを呼び出す構成にしています。
        """
        try:
            if parsed_data.get("status") != "success":
                return self._render_error_page(
                    parsed_data.get("error", "Unknown error")
                )

            elements = parsed_data.get("elements", [])
            if not elements:
                return self._render_empty_page()

            html_body = self._render_simple_elements(elements)
            return self._wrap_in_simple_html_document(html_body)
        except Exception as e:
            self.logger.error(f"Simple render error: {e}")
            return self._render_error_page(str(e))

    # --- Simple互換処理のラッパー（委譲） ------------------------------
    def _render_simple_elements(self, elements: List[Dict[str, Any]]) -> str:
        return self._simple_renderer._render_simple_elements(elements)

    def _render_simple_kumihan_block(
        self, content: str, attributes: Dict[str, str]
    ) -> str:
        return self._simple_renderer._render_simple_kumihan_block(content, attributes)

    def _render_simple_heading(self, content: str, level: int) -> str:
        return self._simple_renderer._render_simple_heading(content, level)

    def _render_simple_paragraph(self, content: str) -> str:
        return self._simple_renderer._render_simple_paragraph(content)

    def _render_simple_list_item(self, content: str, list_type: str) -> str:
        return self._simple_renderer._render_simple_list_item(content, list_type)

    def _get_simple_decoration_class(self, decoration: str) -> str:
        return self._simple_renderer._get_simple_decoration_class(decoration)

    def _wrap_in_simple_html_document(self, body_content: str) -> str:
        return self._simple_renderer._wrap_in_simple_html_document(body_content)

    def _render_error_page(self, error_message: str) -> str:
        return self._simple_renderer._render_error_page(error_message)

    def _render_empty_page(self) -> str:
        return self._simple_renderer._render_empty_page()

    def _get_simple_default_styles(self) -> str:
        return self._simple_renderer._get_simple_default_styles()

    # Simple互換詳細実装は simple_compat_renderer へ分離済み

    # （委譲化）

    # （委譲化）

    # （委譲化）

    # （委譲化）

    # （委譲化）

    # （委譲化）

    # （委譲化）

    # （委譲化）

    # （委譲化）

    def close(self) -> None:
        """リソース解放（将来拡張用）"""
        try:
            self.logger.debug("MainRenderer resources released")
        except Exception as e:
            self.logger.error(f"Resource cleanup error: {e}")

    def render_node(self, node: Any) -> str:
        """単一ノードをレンダリング (delegate compatibility)"""
        try:
            if hasattr(node, "type"):
                if node.type == "error":
                    return f"<div class='error'>{self._escape_html(str(node.content))}</div>"
                elif node.type in ["h1", "h2", "h3", "h4", "h5"]:
                    level = node.type[1]
                    return f"<{node.type}>{self._escape_html(str(node.content))}</{node.type}>"
                elif node.type == "p":
                    return f"<p>{self._escape_html(str(node.content))}</p>"
                else:
                    return f"<div class='{node.type}'>{self._escape_html(str(node.content))}</div>"
            return f"<div>{self._escape_html(str(node.content))}</div>"
        except Exception as e:
            self.logger.error(f"ノードレンダリングエラー: {e}")
            return f"<div class='error'>レンダリングエラー: {e}</div>"
