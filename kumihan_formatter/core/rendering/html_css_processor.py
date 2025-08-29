"""HTML CSS Processing - CSS処理専用モジュール

HTMLFormatter分割により抽出 (Phase3最適化)
CSS関連の処理をすべて統合
"""

from typing import Optional, Dict, Any


class HTMLCSSProcessor:
    """HTML CSS処理専用クラス"""

    def __init__(self, css_class_prefix: str = "kf") -> None:
        self.css_class_prefix = css_class_prefix

    def generate_css_class(
        self,
        keyword: str,
        content: str = "",
        attributes: Optional[Dict[Any, Any]] = None,
    ) -> str:
        """キーワードに基づいてCSSクラス名を生成"""
        if not keyword:
            return ""

        # キーワードを正規化
        normalized = self._normalize_keyword(keyword)
        if not normalized:
            return ""

        # 基本クラス名を生成
        base_class = f"{self.css_class_prefix}-{normalized}"

        # 属性に基づく追加クラス
        additional_classes = []

        if attributes:
            # カラー属性
            if "color" in attributes:
                color_class = self._generate_color_class(attributes["color"])
                if color_class:
                    additional_classes.append(color_class)

            # サイズ属性
            if "size" in attributes:
                size_class = f"{self.css_class_prefix}-size-{attributes['size']}"
                additional_classes.append(size_class)

            # 配置属性
            if "align" in attributes:
                align_class = f"{self.css_class_prefix}-align-{attributes['align']}"
                additional_classes.append(align_class)

        # コンテンツに基づく特殊クラス
        if content:
            if len(content) > 100:
                additional_classes.append(f"{self.css_class_prefix}-long")
            elif len(content.split()) > 20:
                additional_classes.append(f"{self.css_class_prefix}-verbose")

        # 全クラスを結合
        all_classes = [base_class] + additional_classes
        return " ".join(all_classes)

    def _normalize_keyword(self, keyword: str) -> str:
        """キーワードをCSS class名として適切な形式に正規化"""
        import re

        if not keyword:
            return ""

        # 日本語キーワードマッピング
        jp_keyword_map = {
            "太字": "bold",
            "ボールド": "bold",
            "イタリック": "italic",
            "斜体": "italic",
            "見出し": "heading",
            "ヘッダー": "header",
            "タイトル": "title",
            "脚注": "footnote",
            "注釈": "annotation",
            "リンク": "link",
            "画像": "image",
            "図": "figure",
            "コード": "code",
            "引用": "quote",
            "リスト": "list",
            "テーブル": "table",
            "表": "table",
        }

        # 日本語キーワードを英語に変換
        keyword_lower = keyword.lower().strip()
        if keyword_lower in jp_keyword_map:
            keyword = jp_keyword_map[keyword_lower]

        # 英数字とハイフンのみに正規化
        normalized = re.sub(r"[^a-zA-Z0-9\-_]", "-", keyword.lower())

        # 連続するハイフンを単一に
        normalized = re.sub(r"-+", "-", normalized)

        # 先頭・末尾のハイフンを除去
        normalized = normalized.strip("-_")

        # 数字で始まる場合は接頭辞を追加
        if normalized and normalized[0].isdigit():
            normalized = f"n{normalized}"

        return normalized if normalized else ""

    def _generate_color_class(self, color: str) -> str:
        """カラー値からCSSクラス名を生成"""
        if not color:
            return ""

        color = color.strip().lower()

        # 名前付きカラーの場合
        named_colors = [
            "red",
            "blue",
            "green",
            "yellow",
            "orange",
            "purple",
            "pink",
            "brown",
            "black",
            "white",
            "gray",
            "grey",
        ]

        if color in named_colors:
            return f"{self.css_class_prefix}-color-{color}"

        # Hexカラーの場合
        if color.startswith("#"):
            hex_part = color[1:]
            if len(hex_part) == 3 or len(hex_part) == 6:
                return f"{self.css_class_prefix}-color-hex-{hex_part}"

        return ""
