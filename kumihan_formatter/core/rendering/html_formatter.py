"""HTML formatting utilities for Kumihan-Formatter

This module provides utilities for HTML formatting, pretty-printing,
and validation of generated HTML.
"""

import re
from pathlib import Path
from typing import Any, Dict, List


class HTMLFormatter:
    """
    HTML整形・フォーマット（Pretty-print、バリデーション、セマンティック改善）

    Phase 4対応:
    - セマンティックHTML生成の改善
    - アクセシビリティ対応
    - CSSクラス名統一化
    - カラー属性処理

    設計ドキュメント:
    - 仕様: /SPEC.md#出力形式オプション
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - レンダリング詳細: /docs/rendering.md

    関連クラス:
    - Renderer: このクラスを使用してHTML出力を整形
    - Node: 整形対象のASTノード
    - TemplateManager: テンプレートベースの整形と連携

    責務:
    - HTML文字列のインデント整形
    - タグの改行・圧縮制御
    - 空白文字の正規化
    - HTML妥当性チェック
    - セマンティックHTML生成
    - アクセシビリティ属性管理
    """

    def __init__(self, indent_size: int = 2, semantic_mode: bool = True):
        """
        Initialize HTML formatter

        Args:
            indent_size: Number of spaces per indentation level
            semantic_mode: Enable semantic HTML generation
        """
        self.indent_size = indent_size
        self.semantic_mode = semantic_mode
        # Initialize tag stack with proper type
        self.tag_stack: List[str] = []

        # CSS class naming conventions (Issue #665 Phase 4)
        self.css_class_prefix = "kumihan"

        # Color processing support
        self.supported_color_formats = ["hex", "rgb", "rgba", "hsl", "hsla", "named"]

    def handle_special_element(
        self, keyword: str, content: str, attributes: dict[str, Any] | None = None
    ) -> str:
        """
        特殊キーワード（special_handler指定）の処理

        Args:
            keyword: キーワード名
            content: コンテンツ
            attributes: 属性辞書

        Returns:
            str: 処理済みHTML
        """
        if attributes is None:
            attributes = {}

        # footnoteキーワードの処理
        if keyword == "脚注":
            return self._handle_footnote(content, attributes)

        # 未知のspecial_handlerキーワードの場合はデフォルト処理
        return f'<span class="{self.generate_css_class(keyword)}">{content}</span>'

    def _handle_footnote(self, content: str, attributes: dict[str, Any]) -> str:
        """
        脚注キーワードの処理

        Args:
            content: 脚注内容
            attributes: 属性辞書

        Returns:
            str: 脚注プレースホルダーHTML
        """
        # FootnoteManagerの共有インスタンスを取得または作成
        if not hasattr(self, "_footnote_manager"):
            self._footnote_manager = FootnoteManager()

        footnote_manager = self._footnote_manager

        # 脚注データを作成
        footnote_data = {
            "content": content,
            "attributes": attributes,
        }

        # 脚注を登録し、プレースホルダーを取得
        footnote_id = footnote_manager.add_footnote(footnote_data)
        placeholder = footnote_manager.create_placeholder(footnote_id)

        return placeholder

    def generate_css_class(
        self, keyword: str, modifiers: List[str] | None = None
    ) -> str:
        """
        CSS class名を生成（CSS-naming統一対応）

        Args:
            keyword: キーワード名
            modifiers: モディファイアー（オプション）

        Returns:
            str: 統一化されたCSSクラス名
        """
        if modifiers is None:
            modifiers = []

        # ベースクラス名の生成
        base_class = f"{self.css_class_prefix}-{self._normalize_keyword(keyword)}"

        # モディファイアーがある場合は追加
        if modifiers:
            modifier_classes = [
                f"{base_class}--{self._normalize_keyword(mod)}" for mod in modifiers
            ]
            return f"{base_class} " + " ".join(modifier_classes)

        return base_class

    def _normalize_keyword(self, keyword: str) -> str:
        """
        キーワードをCSS class名として正規化

        Args:
            keyword: 正規化対象の文字列

        Returns:
            str: 正規化されたクラス名
        """
        # 日本語文字の翻訳・英語変換ロジック
        translation_map = {
            "太字": "bold",
            "イタリック": "italic",
            "下線": "underline",
            "見出し1": "h1",
            "見出し2": "h2",
            "見出し3": "h3",
            "見出し4": "h4",
            "見出し5": "h5",
            "見出し6": "h6",
            "ハイライト": "highlight",
            "目次": "toc",
            "脚注": "footnote",
        }

        normalized = translation_map.get(keyword, keyword)
        # 英数字・ハイフンのみに制限
        normalized = re.sub(r"[^a-zA-Z0-9\-]", "-", normalized).lower()
        # 連続ハイフンを削除
        normalized = re.sub(r"-+", "-", normalized).strip("-")

        return normalized

    def process_color_attribute(self, color_value: str) -> str:
        """
        カラー属性の処理・正規化

        Args:
            color_value: カラー値（16進数、名前、RGB等）

        Returns:
            str: 正規化されたカラー値
        """
        # 16進数カラーの処理
        if color_value.startswith("#"):
            return self._normalize_hex_color(color_value)

        # RGB/RGBA形式の処理
        if color_value.startswith(("rgb(", "rgba(")):
            return self._normalize_rgb_color(color_value)

        # 色名の処理
        if color_value in self._get_named_colors():
            return color_value.lower()

        # 不正な色値の場合はデフォルトに
        return "#000000"

    def _normalize_hex_color(self, hex_color: str) -> str:
        """
        16進数カラー値の正規化

        Args:
            hex_color: 16進数カラー値

        Returns:
            str: 正規化された16進数カラー値
        """
        # # を除去して正規化
        color = hex_color.strip("#").upper()

        # 3桁の場合は6桁に拡張
        if len(color) == 3:
            color = "".join([c + c for c in color])

        # 6桁以外は無効として黒を返す
        if len(color) != 6 or not re.match(r"^[0-9A-F]{6}$", color):
            return "#000000"

        return f"#{color}"

    def _normalize_rgb_color(self, rgb_color: str) -> str:
        """
        RGB/RGBA カラー値の正規化

        Args:
            rgb_color: RGB/RGBAカラー値

        Returns:
            str: 正規化されたRGBカラー値
        """
        # 基本的な検証のみ実装
        if re.match(
            r"^rgba?\s*\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}"
            r"(\s*,\s*[01]?\.?\d*)?\s*\)$",
            rgb_color,
        ):
            return rgb_color

        return "rgb(0,0,0)"

    def _get_named_colors(self) -> set[Any]:
        """
        サポートされている色名の一覧を取得

        Returns:
            set: サポートされている色名のセット
        """
        return {
            "black",
            "white",
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "pink",
            "brown",
            "gray",
            "grey",
        }

    def format_html(self, html: str, options: dict[str, Any] | None = None) -> str:
        """
        HTML文字列を整形

        Args:
            html: 整形対象のHTML文字列
            options: 整形オプション

        Returns:
            str: 整形済みHTML文字列
        """
        if options is None:
            options = {}

        # 基本的なPretty-print処理
        formatted = self._apply_indentation(html)

        # セマンティックモードが有効な場合の処理
        if self.semantic_mode:
            formatted = self._apply_semantic_improvements(formatted)

        # 最終的な空白文字正規化
        formatted = self._normalize_whitespace(formatted)

        return formatted

    def _apply_indentation(self, html: str) -> str:
        """
        インデント処理を適用

        Args:
            html: HTML文字列

        Returns:
            str: インデント適用済みHTML
        """
        lines = html.split("\n")
        formatted_lines = []
        indent_level = 0
        indent_str = " " * self.indent_size

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # 終了タグの場合はインデントレベルを下げる
            if stripped.startswith("</"):
                indent_level = max(0, indent_level - 1)

            # インデント適用
            formatted_line = indent_str * indent_level + stripped
            formatted_lines.append(formatted_line)

            # 開始タグの場合はインデントレベルを上げる（自己完結タグは除く）
            if (
                stripped.startswith("<")
                and not stripped.startswith("</")
                and not stripped.endswith("/>")
                and not self._is_inline_tag(stripped)
            ):
                indent_level += 1

        return "\n".join(formatted_lines)

    def _is_inline_tag(self, tag_line: str) -> bool:
        """
        インライン要素かどうかを判定

        Args:
            tag_line: タグを含む行

        Returns:
            bool: インライン要素の場合True
        """
        inline_tags = {"span", "a", "em", "strong", "code", "small", "sup", "sub"}

        # タグ名を抽出
        tag_match = re.match(r"<(\w+)", tag_line.strip())
        if tag_match:
            tag_name = tag_match.group(1).lower()
            return tag_name in inline_tags

        return False

    def _apply_semantic_improvements(self, html: str) -> str:
        """
        セマンティックHTML改善の適用

        Args:
            html: HTML文字列

        Returns:
            str: セマンティック改善済みHTML
        """

        improved_html = html

        # 見出しタグの変換を先に実行（開始タグ）
        improved_html = re.sub(
            r'<div class="kumihan-h([1-6])">', r"<h\1>", improved_html
        )

        # 見出しタグの終了タグを個別に処理
        for i in range(1, 7):
            improved_html = re.sub(
                f"</div><!--/kumihan-h{i}-->", f"</h{i}>", improved_html
            )

        # その他のセマンティック変換を実行
        other_rules = [
            (r'<span class="kumihan-bold">', r"<strong>"),
            (r"</span><!--/kumihan-bold-->", r"</strong>"),
            (r'<span class="kumihan-italic">', r"<em>"),
            (r"</span><!--/kumihan-italic-->", r"</em>"),
        ]

        for pattern, replacement in other_rules:
            improved_html = re.sub(pattern, replacement, improved_html)

        return improved_html

    def _normalize_whitespace(self, html: str) -> str:
        """
        空白文字の正規化

        Args:
            html: HTML文字列

        Returns:
            str: 正規化済みHTML
        """
        # 空行の削除
        normalized = re.sub(r"\n\s*\n", "\n", html)

        # 行末空白の削除
        normalized = re.sub(r"[ \t]+$", "", normalized, flags=re.MULTILINE)

        return normalized.strip()

    def validate_html(self, html: str) -> dict[str, Any]:
        """
        HTML妥当性チェック

        Args:
            html: チェック対象のHTML文字列

        Returns:
            dict: バリデーション結果
        """
        validation_result: Dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # 基本的なタグ閉じチェック
        tag_stack: list[str] = []
        self_closing_tags = {
            "br",
            "hr",
            "img",
            "input",
            "meta",
            "link",
            "area",
            "base",
            "col",
            "embed",
            "source",
            "track",
            "wbr",
        }

        # タグをすべて抽出
        tag_pattern = r"<(/?)(\w+)[^>]*/?>"
        for match in re.finditer(tag_pattern, html):
            is_closing = bool(match.group(1))
            tag_name = match.group(2).lower()

            if is_closing:
                # 閉じタグの処理
                if not tag_stack:
                    validation_result["errors"].append(
                        f"Unexpected closing tag: </{tag_name}>"
                    )
                    validation_result["valid"] = False
                elif tag_stack[-1] != tag_name:
                    validation_result["errors"].append(
                        f"Mismatched tag: expected </{tag_stack[-1]}>, "
                        f"found </{tag_name}>"
                    )
                    validation_result["valid"] = False
                else:
                    tag_stack.pop()
            elif tag_name not in self_closing_tags:
                # 開始タグの処理（自己完結タグ以外）
                tag_stack.append(tag_name)

        # 未閉じタグのチェック
        if tag_stack:
            for unclosed_tag in tag_stack:
                validation_result["errors"].append(f"Unclosed tag: <{unclosed_tag}>")
                validation_result["valid"] = False

        return validation_result

    def _generate_alt_text(self, filename: str) -> str:
        """
        画像ファイル名からalt属性用のテキストを生成

        Args:
            filename: 画像ファイル名

        Returns:
            str: alt属性用テキスト
        """
        if not filename:
            return "Image"

        # ファイル拡張子を除去
        name = Path(filename).stem

        # アンダースコアやハイフンをスペースに変換
        alt_text = re.sub(r"[_-]", " ", name)

        # 数字の後にアルファベットが来る場合にスペースを挿入
        alt_text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", alt_text)

        # 大文字小文字の境界にスペースを挿入
        alt_text = re.sub(r"([a-z])([A-Z])", r"\1 \2", alt_text)

        # 先頭を大文字にし、余分なスペースを削除
        alt_text = " ".join(alt_text.split()).capitalize()

        return alt_text if alt_text else "Image"

    def add_accessibility_attributes(self, html: str) -> str:
        """
        アクセシビリティ属性の追加

        Args:
            html: HTML文字列

        Returns:
            str: アクセシビリティ改善済みHTML
        """
        accessibility_rules = [
            # 画像にalt属性が無い場合の警告・追加
            (
                r"<img(?![^>]*alt=)",
                r'<img alt=""',
            ),
            # 見出しレベルのスキップチェック（警告のみ）
            # リンクにtitle属性追加（外部リンクの場合）
            (
                r'<a href="http[s]?://[^"]+">([^<]+)</a>',
                r'<a href="\1" title="\1 (外部サイト)">\1</a>',
            ),
        ]

        improved_html = html
        for pattern, replacement in accessibility_rules:
            improved_html = re.sub(pattern, replacement, improved_html)

        return improved_html

    def compress_html(self, html: str) -> str:
        """
        HTML圧縮（改行・空白削除）

        Args:
            html: HTML文字列

        Returns:
            str: 圧縮済みHTML
        """
        # コメントの削除
        compressed = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # 不要な空白・改行の削除
        compressed = re.sub(r"\s+", " ", compressed)
        compressed = re.sub(r">\s+<", "><", compressed)

        return compressed.strip()

    def create_document_structure(
        self, content: str, options: dict[str, Any] | None = None
    ) -> str:
        """
        完全なHTMLドキュメント構造の生成

        Args:
            content: ボディ部分のコンテンツ
            options: ドキュメントオプション

        Returns:
            str: 完全なHTMLドキュメント
        """
        if options is None:
            options = {}

        title = options.get("title", "Kumihan-Formatter Generated Document")
        lang = options.get("lang", "ja")
        charset = options.get("charset", "UTF-8")
        css_files = options.get("css_files", [])
        js_files = options.get("js_files", [])

        # CSS link要素の生成
        css_links = "\n".join(
            [f'  <link rel="stylesheet" href="{css}">' for css in css_files]
        )

        # JavaScript script要素の生成
        js_scripts = "\n".join([f'  <script src="{js}"></script>' for js in js_files])

        # HTMLテンプレート
        template = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="{charset}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="generator" content="Kumihan-Formatter">
{css_links}
</head>
<body>
{content}
{js_scripts}
</body>
</html>"""

        return template


class FootnoteManager:
    """
    脚注管理クラス

    責務:
    - 脚注の登録・管理
    - プレースホルダーの生成
    - 脚注リストの出力
    """

    def __init__(self) -> None:
        self.footnotes: dict[str, dict[str, Any]] = {}  # footnote_id -> footnote_data
        self.footnote_counter = 0

    def add_footnote(self, footnote_data: dict[str, Any]) -> str:
        """
        脚注を追加

        Args:
            footnote_data: 脚注データ

        Returns:
            str: 脚注ID
        """
        self.footnote_counter += 1
        footnote_id = f"footnote-{self.footnote_counter}"
        self.footnotes[footnote_id] = footnote_data
        return footnote_id

    def create_placeholder(self, footnote_id: str) -> str:
        """
        脚注プレースホルダーの生成

        Args:
            footnote_id: 脚注ID

        Returns:
            str: プレースホルダーHTML
        """
        footnote_number = footnote_id.split("-")[-1]
        return (
            f'<sup><a href="#{footnote_id}" class="footnote-ref">'
            f"[{footnote_number}]</a></sup>"
        )

    def generate_footnote_list(self) -> str:
        """
        脚注リストのHTML生成

        Returns:
            str: 脚注リストHTML
        """
        if not self.footnotes:
            return ""

        footnote_items = []
        for footnote_id, footnote_data in self.footnotes.items():
            # TODO: 脚注番号付けシステムの実装 (Issue #921で対応予定)
            # 複雑な脚注システム全体の設計が必要なため、別途Issue化して対応
            content = footnote_data["content"]
            footnote_item = (
                f'<li id="{footnote_id}">'
                f"{content} "
                f'<a href="#ref-{footnote_id}">↩</a>'
                f"</li>"
            )
            footnote_items.append(footnote_item)

        footnote_list = (
            '<div class="footnotes">\n'
            "<h3>脚注</h3>\n"
            "<ol>\n" + "\n".join(footnote_items) + "\n</ol>\n"
            "</div>"
        )

        return footnote_list

    def clear_footnotes(self) -> None:
        """
        脚注データのクリア
        """
        self.footnotes.clear()
        self.footnote_counter = 0


# Utility functions for backward compatibility
def format_html(html: str, indent_size: int = 2) -> str:
    """
    HTML整形のユーティリティ関数

    Args:
        html: 整形対象のHTML
        indent_size: インデントサイズ

    Returns:
        str: 整形済みHTML
    """
    formatter = HTMLFormatter(indent_size=indent_size)
    return formatter.format_html(html)


def validate_html_string(html: str) -> dict[str, Any]:
    """
    HTMLバリデーションのユーティリティ関数

    Args:
        html: バリデーション対象のHTML

    Returns:
        dict: バリデーション結果
    """
    formatter = HTMLFormatter()
    return formatter.validate_html(html)


def create_full_html_document(content: str, **options: Any) -> str:
    """
    完全なHTMLドキュメント生成のユーティリティ関数

    Args:
        content: コンテンツ
        **options: ドキュメントオプション

    Returns:
        str: 完全なHTMLドキュメント
    """
    formatter = HTMLFormatter()
    return formatter.create_document_structure(content, options)
