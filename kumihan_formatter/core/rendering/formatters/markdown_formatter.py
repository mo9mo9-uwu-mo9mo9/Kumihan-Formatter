"""Markdown出力専用フォーマッター

Issue #912 Renderer系統合リファクタリング対応
Markdown出力に特化した統合フォーマッタークラス
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...ast_nodes import Node
from ...utilities.logger import get_logger
from ..base.renderer_protocols import (
    MarkdownRendererProtocol,
    RenderContext,
    RenderResult,
    create_render_result,
)


class MarkdownFormatter(MarkdownRendererProtocol):
    """Markdown出力専用フォーマッター

    統合された機能:
    - Markdown要素レンダリング
    - HTML→Markdownパターン変換
    - 段落・見出し処理
    - Markdown記法準拠出力
    """

    def __init__(self, config: Optional[Any] = None) -> None:
        """Markdown フォーマッターを初期化

        Args:
            config: 設定オブジェクト（オプショナル）
        """
        self.logger = get_logger(__name__)
        self.config = config

        # Markdownパターン定義
        self.patterns = {
            "h1": re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL),
            "h2": re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL),
            "h3": re.compile(r"<h3[^>]*>(.*?)</h3>", re.IGNORECASE | re.DOTALL),
            "h4": re.compile(r"<h4[^>]*>(.*?)</h4>", re.IGNORECASE | re.DOTALL),
            "h5": re.compile(r"<h5[^>]*>(.*?)</h5>", re.IGNORECASE | re.DOTALL),
            "h6": re.compile(r"<h6[^>]*>(.*?)</h6>", re.IGNORECASE | re.DOTALL),
            "strong": re.compile(
                r"<strong[^>]*>(.*?)</strong>", re.IGNORECASE | re.DOTALL
            ),
            "em": re.compile(r"<em[^>]*>(.*?)</em>", re.IGNORECASE | re.DOTALL),
            "code": re.compile(r"<code[^>]*>(.*?)</code>", re.IGNORECASE | re.DOTALL),
            "pre": re.compile(r"<pre[^>]*>(.*?)</pre>", re.IGNORECASE | re.DOTALL),
            "ul": re.compile(r"<ul[^>]*>(.*?)</ul>", re.IGNORECASE | re.DOTALL),
            "ol": re.compile(r"<ol[^>]*>(.*?)</ol>", re.IGNORECASE | re.DOTALL),
            "li": re.compile(r"<li[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL),
            "a": re.compile(
                r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL
            ),
            "img": re.compile(
                r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?>', re.IGNORECASE
            ),
            "br": re.compile(r"<br\s*/?>\s*", re.IGNORECASE),
            "p": re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL),
        }

        self.logger.debug("MarkdownFormatter initialized")

    def format(self, nodes: List[Node]) -> str:
        """ノードリストをMarkdown形式でフォーマット

        Args:
            nodes: フォーマットするASTノードリスト

        Returns:
            str: 生成されたMarkdown
        """
        self.logger.debug(f"Formatting {len(nodes)} nodes to Markdown")

        markdown_parts = []
        for node in nodes:
            markdown = self.format_node(node)
            if markdown:
                markdown_parts.append(markdown)

        result = "\n\n".join(markdown_parts)
        self.logger.debug(f"Generated Markdown: {len(result)} characters")
        return result

    def format_node(self, node: Node) -> str:
        """単一ノードをMarkdown化

        Args:
            node: フォーマットするASTノード

        Returns:
            str: 生成されたMarkdown
        """
        if not isinstance(node, Node):
            raise TypeError(f"Expected Node instance, got {type(node)}")

        # デリゲートメソッドを動的に検索して呼び出し
        method_name = f"_format_{node.type}"
        formatter_method = getattr(self, method_name, self._format_generic)
        return formatter_method(node)

    def convert_html_to_markdown(self, html_content: str) -> str:
        """HTMLコンテンツをMarkdownに変換

        Args:
            html_content: 変換するHTMLコンテンツ

        Returns:
            str: 変換されたMarkdown
        """
        content = html_content

        # 見出しの変換
        content = self.patterns["h1"].sub(r"# \1", content)
        content = self.patterns["h2"].sub(r"## \1", content)
        content = self.patterns["h3"].sub(r"### \1", content)
        content = self.patterns["h4"].sub(r"#### \1", content)
        content = self.patterns["h5"].sub(r"##### \1", content)
        content = self.patterns["h6"].sub(r"###### \1", content)

        # 強調・斜体の変換
        content = self.patterns["strong"].sub(r"**\1**", content)
        content = self.patterns["em"].sub(r"*\1*", content)

        # コードの変換
        content = self.patterns["code"].sub(r"`\1`", content)
        content = self.patterns["pre"].sub(r"```\n\1\n```", content)

        # リンクの変換
        content = self.patterns["a"].sub(r"[\2](\1)", content)

        # 画像の変換
        content = self.patterns["img"].sub(r"![\2](\1)", content)

        # リストの変換
        content = self._convert_lists(content)

        # 改行の変換
        content = self.patterns["br"].sub("\n", content)

        # 段落の変換
        content = self.patterns["p"].sub(r"\1\n", content)

        # 余分な空白を削除
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = content.strip()

        return content

    def create_full_markdown_document(
        self, title: str, content: str, source_filename: str
    ) -> str:
        """完全なMarkdownドキュメントを作成

        Args:
            title: ドキュメントタイトル
            content: Markdownコンテンツ
            source_filename: 元ファイル名

        Returns:
            str: 完全なMarkdownドキュメント
        """
        generation_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        markdown_document = f"""# {title}

{content}

---

**📄 文書情報**
- 元ファイル: {source_filename}
- 変換日時: {generation_time}
- 変換ツール: Kumihan-Formatter
"""

        return markdown_document

    # === プライベートメソッド: ノード別フォーマット ===

    def _format_generic(self, node: Node) -> str:
        """汎用ノードフォーマット"""
        content = self._format_content(node.content)
        return content

    def _format_p(self, node: Node) -> str:
        """段落ノードフォーマット"""
        content = self._format_content(node.content)
        return content

    def _format_strong(self, node: Node) -> str:
        """太字ノードフォーマット"""
        content = self._format_content(node.content)
        return f"**{content}**"

    def _format_em(self, node: Node) -> str:
        """斜体ノードフォーマット"""
        content = self._format_content(node.content)
        return f"*{content}*"

    def _format_h1(self, node: Node) -> str:
        """h1見出しフォーマット"""
        content = self._format_content(node.content)
        return f"# {content}"

    def _format_h2(self, node: Node) -> str:
        """h2見出しフォーマット"""
        content = self._format_content(node.content)
        return f"## {content}"

    def _format_h3(self, node: Node) -> str:
        """h3見出しフォーマット"""
        content = self._format_content(node.content)
        return f"### {content}"

    def _format_h4(self, node: Node) -> str:
        """h4見出しフォーマット"""
        content = self._format_content(node.content)
        return f"#### {content}"

    def _format_h5(self, node: Node) -> str:
        """h5見出しフォーマット"""
        content = self._format_content(node.content)
        return f"##### {content}"

    def _format_h6(self, node: Node) -> str:
        """h6見出しフォーマット"""
        content = self._format_content(node.content)
        return f"###### {content}"

    def _format_ul(self, node: Node) -> str:
        """順序なしリストフォーマット"""
        items = []
        if isinstance(node.content, list):
            for item in node.content:
                if hasattr(item, "type") and item.type == "li":
                    item_content = self._format_content(item.content)
                    items.append(f"- {item_content}")
                else:
                    item_content = self._format_content(item)
                    items.append(f"- {item_content}")
        else:
            content = self._format_content(node.content)
            items.append(f"- {content}")

        return "\n".join(items)

    def _format_ol(self, node: Node) -> str:
        """順序ありリストフォーマット"""
        items = []
        if isinstance(node.content, list):
            for i, item in enumerate(node.content, 1):
                if hasattr(item, "type") and item.type == "li":
                    item_content = self._format_content(item.content)
                    items.append(f"{i}. {item_content}")
                else:
                    item_content = self._format_content(item)
                    items.append(f"{i}. {item_content}")
        else:
            content = self._format_content(node.content)
            items.append(f"1. {content}")

        return "\n".join(items)

    def _format_li(self, node: Node) -> str:
        """リスト項目フォーマット"""
        content = self._format_content(node.content)
        return content

    def _format_code(self, node: Node) -> str:
        """インラインコードフォーマット"""
        content = self._format_content(node.content)
        return f"`{content}`"

    def _format_pre(self, node: Node) -> str:
        """整形済みテキストフォーマット"""
        content = self._format_content(node.content)
        language = (
            node.get_attribute("language", "") if hasattr(node, "get_attribute") else ""
        )

        if language:
            return f"```{language}\n{content}\n```"
        else:
            return f"```\n{content}\n```"

    def _format_image(self, node: Node) -> str:
        """画像要素フォーマット"""
        filename = node.content if isinstance(node.content, str) else str(node.content)
        src = f"images/{filename}"
        alt = (
            node.get_attribute("alt", filename)
            if hasattr(node, "get_attribute")
            else filename
        )

        return f"![{alt}]({src})"

    def _format_div(self, node: Node) -> str:
        """div要素フォーマット（Markdownでは内容のみ）"""
        content = self._format_content(node.content)
        return content

    def _format_details(self, node: Node) -> str:
        """details要素フォーマット（Markdownでは展開形式）"""
        summary = (
            node.get_attribute("summary", "詳細")
            if hasattr(node, "get_attribute")
            else "詳細"
        )
        content = self._format_content(node.content)

        return f"**{summary}**\n\n{content}"

    def _format_toc(self, node: Node) -> str:
        """目次マーカーフォーマット"""
        return "<!-- TOC -->"

    def _format_error(self, node: Node) -> str:
        """エラーノードフォーマット"""
        content = str(node.content)
        return f"[ERROR: {content}]"

    # === プライベートメソッド: ヘルパー機能 ===

    def _format_content(self, content: Any) -> str:
        """コンテンツをフォーマット（再帰的）

        Args:
            content: フォーマットするコンテンツ

        Returns:
            str: フォーマット結果
        """
        # 単一ノードの場合
        if hasattr(content, "type"):
            return self.format_node(content)

        # リストの場合
        if isinstance(content, list):
            parts = []
            for item in content:
                if hasattr(item, "type"):
                    parts.append(self.format_node(item))
                elif isinstance(item, str):
                    parts.append(self._process_text_content(item))
                else:
                    parts.append(self._process_text_content(str(item)))
            return "".join(parts)

        # 文字列の場合
        if isinstance(content, str):
            return self._process_text_content(content)

        # その他
        return self._process_text_content(str(content))

    def _process_text_content(self, text: str) -> str:
        """テキストコンテンツを処理

        Args:
            text: 処理するテキスト

        Returns:
            str: 処理されたテキスト
        """
        # Markdownエスケープ処理
        text = text.replace("\\", "\\\\")
        text = text.replace("`", "\\`")
        text = text.replace("*", "\\*")
        text = text.replace("_", "\\_")
        text = text.replace("#", "\\#")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        text = text.replace("(", "\\(")
        text = text.replace(")", "\\)")

        return text

    def _convert_lists(self, content: str) -> str:
        """リストをMarkdown形式に変換

        Args:
            content: 変換するHTMLコンテンツ

        Returns:
            str: 変換されたコンテンツ
        """

        # 順序なしリストの変換
        def convert_ul(match: Any) -> str:
            ul_content = match.group(1)
            items = self.patterns["li"].findall(ul_content)
            markdown_items = [f"- {item.strip()}" for item in items]
            return "\n".join(markdown_items)

        content = self.patterns["ul"].sub(convert_ul, content)

        # 順序ありリストの変換
        def convert_ol(match: Any) -> str:
            ol_content = match.group(1)
            items = self.patterns["li"].findall(ol_content)
            markdown_items = [f"{i+1}. {item.strip()}" for i, item in enumerate(items)]
            return "\n".join(markdown_items)

        content = self.patterns["ol"].sub(convert_ol, content)

        return content

    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """コンテンツから最初のH1見出しを抽出

        Args:
            content: 抽出対象のコンテンツ

        Returns:
            Optional[str]: 抽出されたタイトル
        """
        match = self.patterns["h1"].search(content)
        return match.group(1).strip() if match else None

    def _convert_paragraphs(self, text: str) -> str:
        """段落を作成

        Args:
            text: 変換するテキスト

        Returns:
            str: 段落が作成されたテキスト
        """
        lines = text.split("\n")
        result = []
        current_paragraph: List[str] = []

        for line in lines:
            line = line.strip()

            # Markdownタグが含まれる行はそのまま追加
            if (
                line.startswith("#")
                or line.startswith("-")
                or line.startswith("*")
                or line.startswith("1.")
                or line == ""
                or line.startswith("---")
                or line.startswith("```")
            ):
                # 現在の段落を終了
                if current_paragraph:
                    para_text = " ".join(current_paragraph).strip()
                    if para_text:
                        result.append(para_text)
                    current_paragraph = []

                # Markdownタグの行をそのまま追加
                if line:
                    result.append(line)
            else:
                # 通常のテキスト行
                if line:
                    current_paragraph.append(line)
                else:
                    # 空行で段落を区切る
                    if current_paragraph:
                        para_text = " ".join(current_paragraph).strip()
                        if para_text:
                            result.append(para_text)
                        current_paragraph = []

        # 最後の段落を処理
        if current_paragraph:
            para_text = " ".join(current_paragraph).strip()
            if para_text:
                result.append(para_text)

        return "\n\n".join(result)

    # ==========================================
    # プロトコル準拠メソッド（MarkdownRendererProtocol実装）
    # ==========================================

    def render(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> RenderResult:
        """統一レンダリングインターフェース（プロトコル準拠）"""
        try:
            if not nodes:
                return create_render_result(content="", success=True)

            # 複数ノードを順次処理
            markdown_parts = []
            for node in nodes:
                markdown_content = self.format_node(node)
                markdown_parts.append(markdown_content)

            combined_content = "\n\n".join(markdown_parts)
            return create_render_result(content=combined_content, success=True)
        except Exception as e:
            result = create_render_result(success=False)
            result.add_error(f"Markdownレンダリング失敗: {e}")
            return result

    def validate(
        self, node: Node, context: Optional[RenderContext] = None
    ) -> List[str]:
        """バリデーション実装（プロトコル準拠）"""
        errors = []
        try:
            # Markdown特有の検証
            if not node:
                errors.append("ノードが空です")
            elif not hasattr(node, "node_type"):
                errors.append("ノードタイプが設定されていません")
            # Markdownレンダリング可能性の確認
            elif not hasattr(node, "content"):
                errors.append("ノードにコンテンツが設定されていません")
        except Exception as e:
            errors.append(f"Markdownバリデーションエラー: {e}")
        return errors

    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報（プロトコル準拠）"""
        return {
            "name": "MarkdownFormatter",
            "version": "2.0.0",
            "supported_formats": ["markdown"],
            "capabilities": ["markdown_formatting", "html_to_markdown_conversion"],
            "output_format": "markdown",
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
        return format_hint in ["markdown", "md", "text"]

    def render_markdown(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> str:
        """Markdown固有レンダリングメソッド（プロトコル準拠）"""
        if not nodes:
            return ""

        # 複数ノードを順次処理
        markdown_parts = []
        for node in nodes:
            markdown_content = self.format_node(node)
            markdown_parts.append(markdown_content)

        return "\n\n".join(markdown_parts)

    def to_html(self, markdown_content: str) -> str:
        """MarkdownからHTMLに変換（プロトコル準拠）"""
        # 簡単な変換実装（実際にはより詳細な実装が必要）
        content = markdown_content

        # 見出し変換: # Title -> <h1>Title</h1>
        content = re.sub(r"^# (.+)$", r"<h1>\1</h1>", content, flags=re.MULTILINE)
        content = re.sub(r"^## (.+)$", r"<h2>\1</h2>", content, flags=re.MULTILINE)

        # 強調変換: **text** -> <strong>text</strong>
        content = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", content)

        return content

    def convert_from_kumihan(
        self, kumihan_text: str, context: Optional[RenderContext] = None
    ) -> str:
        """Kumihan記法からMarkdownに変換（プロトコル準拠）"""
        # 基本的な変換実装
        return self._convert_from_html(kumihan_text)

    def _convert_from_html(self, html_content: str) -> str:
        """HTMLからMarkdownに変換（内部メソッド）"""
        # 基本的なHTML→Markdown変換
        # より複雑な変換が必要な場合は外部ライブラリ（html2text等）を使用
        content = html_content

        # 簡単なHTML要素をMarkdownに変換
        content = content.replace("<strong>", "**").replace("</strong>", "**")
        content = content.replace("<em>", "*").replace("</em>", "*")
        content = content.replace("<br>", "\n").replace("<br/>", "\n")
        content = content.replace("<p>", "").replace("</p>", "\n\n")
        content = content.replace("<h1>", "# ").replace("</h1>", "\n")
        content = content.replace("<h2>", "## ").replace("</h2>", "\n")
        content = content.replace("<h3>", "### ").replace("</h3>", "\n")

        return content.strip()

    def get_markdown_extensions(self) -> List[str]:
        """サポートするMarkdown拡張機能のリストを返す（抽象メソッド実装）"""
        return ["tables", "fenced_code", "toc", "strikethrough"]

    def validate_options(self, options: Dict[str, Any]) -> List[str]:
        """オプションの妥当性をチェック（プロトコル準拠）"""
        errors = []

        # 基本的な検証実装
        if not isinstance(options, dict):
            errors.append("オプションは辞書形式で指定してください")
            return errors

        # 有効なオプションキーの定義
        valid_keys = {
            "include_title",
            "include_metadata",
            "table_of_contents",
            "code_highlight",
            "strict_mode",
            "extensions",
        }

        # 不明なキーがないかチェック
        for key in options.keys():
            if key not in valid_keys:
                errors.append(f"不明なオプションキー: {key}")

        return errors

    def render_node(self, node: Node, context: Optional[RenderContext] = None) -> str:
        """単一ノードレンダリング（BaseRendererProtocol準拠）"""
        return self.format_node(node)

    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧を取得（BaseRendererProtocol準拠）"""
        return ["markdown", "md", "text"]

    def validate_markdown_syntax(self, markdown: str) -> List[str]:
        """Markdown構文検証（MarkdownRendererProtocol準拠）"""
        errors = []
        try:
            # 基本的なMarkdown構文チェック
            lines = markdown.split("\n")
            for i, line in enumerate(lines, 1):
                # 見出し形式チェック
                if line.startswith("#"):
                    if not line.startswith("# ") and len(line) > 1:
                        errors.append(f"行 {i}: 見出し記号の後にスペースが必要です")

                # リスト形式チェック
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    stripped = line.strip()
                    if len(stripped) > 1 and not stripped[1] == " ":
                        errors.append(f"行 {i}: リスト記号の後にスペースが必要です")
        except Exception as e:
            errors.append(f"Markdown構文検証エラー: {e}")

        return errors
