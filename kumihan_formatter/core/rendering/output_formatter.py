"""
出力整形機能
MainRendererの分割版 - 出力フォーマッター
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..ast_nodes.node import ASTNode


class OutputFormatter:
    """出力整形クラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """出力フォーマッター初期化"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

    def render_to_file(
        self,
        nodes: List[ASTNode],
        output_path: Union[str, Path],
        format: str = "html",
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """ファイル出力レンダリング"""
        try:
            if not nodes:
                self.logger.warning("空のノードリストです")
                return False

            context = context or {}

            # コンテンツ生成
            content = self.render_to_format(nodes, format, context)

            if not content:
                self.logger.error("コンテンツ生成に失敗しました")
                return False

            # ファイル出力
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"出力完了: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"ファイル出力エラー: {e}")
            return False

    def render_to_format(
        self,
        nodes: List[ASTNode],
        format: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """指定フォーマットでレンダリング"""
        try:
            context = context or {}
            format_lower = format.lower()

            if format_lower == "html":
                return self.render_to_html(nodes, context)
            elif format_lower == "markdown":
                return self.render_to_markdown(nodes)
            elif format_lower == "text":
                return self.render_to_text(nodes)
            elif format_lower == "json":
                return self.render_to_json(nodes)
            else:
                self.logger.warning(f"未対応フォーマット: {format}")
                return self.render_to_html(nodes, context)

        except Exception as e:
            self.logger.error(f"フォーマットレンダリングエラー: {e}")
            return f'<div class="error">フォーマットエラー: {str(e)}</div>'

    def render_to_html(
        self, nodes: List[ASTNode], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """HTMLレンダリング"""
        try:
            if not nodes:
                return ""

            context = context or {}
            html_parts = []

            # HTML文書構造
            if context.get("full_document", False):
                html_parts.append(self._create_html_header(context))

            # コンテンツ部分
            for node in nodes:
                html = self._render_node_to_html(node)
                if html:
                    html_parts.append(html)

            if context.get("full_document", False):
                html_parts.append(self._create_html_footer(context))

            return "\n".join(html_parts)

        except Exception as e:
            self.logger.error(f"HTMLレンダリングエラー: {e}")
            return f'<div class="error">HTMLレンダリングエラー: {str(e)}</div>'

    def render_to_markdown(self, nodes: List[ASTNode]) -> str:
        """Markdownレンダリング"""
        try:
            if not nodes:
                return ""

            md_parts = []

            for node in nodes:
                md = self._render_node_to_markdown(node)
                if md:
                    md_parts.append(md)

            return "\n\n".join(md_parts)

        except Exception as e:
            self.logger.error(f"Markdownレンダリングエラー: {e}")
            return f"Markdownレンダリングエラー: {str(e)}"

    def render_to_text(self, nodes: List[ASTNode]) -> str:
        """プレーンテキストレンダリング"""
        try:
            if not nodes:
                return ""

            text_parts = []

            for node in nodes:
                text = self._extract_text_from_node(node)
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)

        except Exception as e:
            self.logger.error(f"テキストレンダリングエラー: {e}")
            return f"テキストレンダリングエラー: {str(e)}"

    def render_to_json(self, nodes: List[ASTNode]) -> str:
        """JSONレンダリング"""
        try:
            import json

            if not nodes:
                return json.dumps([], ensure_ascii=False, indent=2)

            json_data = []

            for node in nodes:
                node_data = self._node_to_dict(node)
                json_data.append(node_data)

            return json.dumps(json_data, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"JSONレンダリングエラー: {e}")
            return f'{{"error": "{str(e)}"}}'

    def _render_node_to_html(self, node: ASTNode) -> str:
        """単一ノードHTMLレンダリング"""
        try:
            if not hasattr(node, "tag"):
                return str(node)

            tag = node.tag
            content = getattr(node, "content", "")
            attributes = getattr(node, "attributes", {})

            # 属性文字列作成
            attr_str = ""
            if attributes:
                attr_parts = []
                for key, value in attributes.items():
                    attr_parts.append(f'{key}="{value}"')
                attr_str = " " + " ".join(attr_parts)

            # 自己完結タグ
            if tag.lower() in ["img", "br", "hr", "meta", "link", "input"]:
                return f"<{tag}{attr_str} />"

            return f"<{tag}{attr_str}>{content}</{tag}>"

        except Exception as e:
            self.logger.error(f"ノードHTMLレンダリングエラー: {e}")
            return f'<span class="error">{str(e)}</span>'

    def _render_node_to_markdown(self, node: ASTNode) -> str:
        """単一ノードMarkdownレンダリング"""
        try:
            if not hasattr(node, "tag"):
                return str(node)

            tag = node.tag.lower()
            content = getattr(node, "content", "")

            if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(tag[1])
                return "#" * level + " " + content
            elif tag == "p":
                return content
            elif tag == "strong":
                return f"**{content}**"
            elif tag == "em":
                return f"*{content}*"
            elif tag == "code":
                return f"`{content}`"
            elif tag == "ul":
                # リスト処理は簡略化
                return content
            elif tag == "ol":
                return content
            elif tag == "li":
                return f"- {content}"
            else:
                return content

        except Exception as e:
            self.logger.error(f"ノードMarkdownレンダリングエラー: {e}")
            return str(node)

    def _extract_text_from_node(self, node: ASTNode) -> str:
        """ノードからテキスト抽出"""
        try:
            if hasattr(node, "content"):
                content = node.content
                # HTMLタグを除去する簡易処理
                import re

                text = re.sub(r"<[^>]+>", "", str(content))
                return text.strip()

            return str(node).strip()

        except Exception as e:
            self.logger.error(f"テキスト抽出エラー: {e}")
            return str(node)

    def _node_to_dict(self, node: ASTNode) -> Dict[str, Any]:
        """ノードを辞書に変換"""
        try:
            result = {
                "type": "node",
                "tag": getattr(node, "tag", None),
                "content": getattr(node, "content", ""),
            }

            # 属性があれば追加
            if hasattr(node, "attributes"):
                result["attributes"] = node.attributes

            # 子ノードがあれば再帰的に処理
            if hasattr(node, "children") and node.children:
                result["children"] = [
                    self._node_to_dict(child) for child in node.children
                ]

            return result

        except Exception as e:
            self.logger.error(f"ノード辞書変換エラー: {e}")
            return {"type": "error", "message": str(e)}

    def _create_html_header(self, context: Dict[str, Any]) -> str:
        """HTML文書ヘッダー作成"""
        title = context.get("title", "ドキュメント")
        lang = context.get("lang", "ja")

        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {self._create_default_styles()}
</head>
<body>"""

    def _create_html_footer(self, context: Dict[str, Any]) -> str:
        """HTML文書フッター作成"""
        return "</body>\n</html>"

    def _create_default_styles(self) -> str:
        """デフォルトスタイル作成"""
        return """<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    color: #333;
}
h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    margin-top: 2rem;
    margin-bottom: 1rem;
}
p {
    margin-bottom: 1.2rem;
}
code {
    background-color: #f4f4f4;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', monospace;
}
.error {
    background-color: #fff5f5;
    border: 1px solid #fed7d7;
    color: #9b2c2c;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}
</style>"""

    def validate_output_options(self, options: Dict[str, Any]) -> List[str]:
        """出力オプション検証"""
        errors = []

        if not isinstance(options, dict):
            errors.append("オプションは辞書形式である必要があります")
            return errors

        # 有効なオプションキー
        valid_keys = {
            "format",
            "output_path",
            "full_document",
            "title",
            "lang",
            "include_styles",
            "custom_styles",
            "encoding",
        }

        # 未知のキーチェック
        for key in options.keys():
            if key not in valid_keys:
                errors.append(f"未知のオプション: {key}")

        # フォーマット検証
        if "format" in options:
            format_value = options["format"]
            if format_value not in ["html", "markdown", "text", "json"]:
                errors.append(f"未対応フォーマット: {format_value}")

        # パス検証
        if "output_path" in options:
            output_path = options["output_path"]
            if not isinstance(output_path, (str, Path)):
                errors.append(
                    "output_pathは文字列またはPathオブジェクトである必要があります"
                )

        return errors

    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧"""
        return ["html", "markdown", "text", "json"]

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応確認"""
        return format_hint.lower() in self.get_supported_formats()

    def get_formatter_info(self) -> Dict[str, Any]:
        """フォーマッター情報"""
        return {
            "name": "OutputFormatter",
            "version": "1.0.0",
            "formats": self.get_supported_formats(),
            "features": [
                "multi_format_output",
                "file_output",
                "html_document_generation",
                "markdown_conversion",
                "text_extraction",
                "json_serialization",
            ],
        }
