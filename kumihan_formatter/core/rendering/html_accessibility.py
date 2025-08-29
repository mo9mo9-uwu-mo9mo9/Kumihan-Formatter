"""HTML Accessibility - アクセシビリティ処理専用モジュール

HTMLFormatter分割により抽出 (Phase3最適化)
アクセシビリティ関連の処理をすべて統合
"""

import re
from typing import Dict, List, Optional, Tuple


class HTMLAccessibilityProcessor:
    """HTMLアクセシビリティ処理専用クラス"""

    def __init__(self) -> None:
        self.validation_errors: List[str] = []

    def add_accessibility_attributes(
        self, tag: str, attributes: Dict[str, str], content: str = ""
    ) -> Dict[str, str]:
        """要素にアクセシビリティ属性を追加"""
        enhanced_attributes = attributes.copy()

        if tag == "img":
            # 画像のalt属性
            if "alt" not in enhanced_attributes or not enhanced_attributes["alt"]:
                alt_text = self._generate_alt_text(
                    enhanced_attributes.get("src", ""), content
                )
                enhanced_attributes["alt"] = alt_text

            # 装飾画像の場合
            if enhanced_attributes["alt"] == "":
                enhanced_attributes["role"] = "presentation"

        elif tag == "a":
            # リンクのtitle属性
            if "title" not in enhanced_attributes and content:
                if len(content) > 30:
                    enhanced_attributes["title"] = content[:30] + "..."
                else:
                    enhanced_attributes["title"] = content

        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            # 見出しのid属性（アンカーリンク用）
            if "id" not in enhanced_attributes and content:
                heading_id = self._generate_heading_id(content)
                enhanced_attributes["id"] = heading_id

        elif tag == "table":
            # テーブルのsummary属性
            if "summary" not in enhanced_attributes:
                enhanced_attributes["summary"] = "データテーブル"

        elif tag == "button":
            # ボタンのaria-label
            if "aria-label" not in enhanced_attributes and not content:
                enhanced_attributes["aria-label"] = "ボタン"

        return enhanced_attributes

    def _generate_alt_text(self, src: str, content: str) -> str:
        """画像のalt属性テキストを生成"""
        # コンテンツがある場合はそれを使用
        if content and content.strip():
            return content.strip()[:100]

        # ファイル名から推測
        if src:
            # ファイル名を抽出
            filename = src.split("/")[-1].split(".")[0]

            # アンダースコアやハイフンを空白に変換
            alt_text = filename.replace("_", " ").replace("-", " ")

            # 拡張子を除去
            alt_text = re.sub(r"\.\w+$", "", alt_text)

            if alt_text:
                return alt_text.title()

        # デフォルトのalt属性
        return "画像"

    def _generate_heading_id(self, content: str) -> str:
        """見出しテキストからID属性を生成"""
        # HTML タグを除去
        clean_content = re.sub(r"<[^>]+>", "", content)

        # 日本語文字を含む場合の処理
        if re.search(r"[ひらがなカタカナ漢字]", clean_content):
            # 日本語の場合は英数字のみ抽出して使用
            alphanumeric = re.findall(r"[a-zA-Z0-9]+", clean_content)
            if alphanumeric:
                id_text = "-".join(alphanumeric[:3])  # 最初の3つの英数字グループ
            else:
                id_text = "heading"
        else:
            # 英語の場合は通常の処理
            id_text = clean_content.lower()
            id_text = re.sub(r"[^a-z0-9\s-]", "", id_text)
            id_text = re.sub(r"\s+", "-", id_text.strip())

        return id_text[:50]  # 長さ制限

    def validate_html(self, html_content: str) -> Tuple[bool, List[str]]:
        """HTMLの基本的なアクセシビリティ検証"""
        self.validation_errors = []

        # 画像のalt属性チェック
        img_pattern = r"<img[^>]*>"
        for match in re.finditer(img_pattern, html_content, re.IGNORECASE):
            img_tag = match.group(0)
            if "alt=" not in img_tag.lower():
                self.validation_errors.append(
                    f"画像タグにalt属性がありません: {img_tag[:50]}..."
                )

        # 見出し階層のチェック
        heading_pattern = r"<(h[1-6])[^>]*>"
        headings = re.findall(heading_pattern, html_content, re.IGNORECASE)
        if headings:
            prev_level = 0
            for heading in headings:
                level = int(heading[1])
                if prev_level > 0 and level > prev_level + 1:
                    self.validation_errors.append(
                        f"見出し階層が飛び越えています: {heading} (前レベル: h{prev_level})"
                    )
                prev_level = level

        # リンクテキストのチェック
        link_pattern = r"<a[^>]*>(.*?)</a>"
        for match in re.finditer(link_pattern, html_content, re.IGNORECASE | re.DOTALL):
            link_text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if not link_text or link_text in ["こちら", "ここ", "click here", "more"]:
                self.validation_errors.append(
                    f"意味のないリンクテキスト: '{link_text}'"
                )

        # 色のみの情報伝達チェック（簡易版）
        style_pattern = r'style=["\'][^"\']*color:[^;"\']+'
        color_matches = re.findall(style_pattern, html_content, re.IGNORECASE)
        if color_matches and len(color_matches) > 5:  # 多用している場合
            self.validation_errors.append("色のみで情報を伝達している可能性があります")

        # 表のヘッダーチェック
        table_pattern = r"<table[^>]*>.*?</table>"
        for match in re.finditer(
            table_pattern, html_content, re.IGNORECASE | re.DOTALL
        ):
            table_content = match.group(0)
            if (
                "<th" not in table_content.lower()
                and "<thead" not in table_content.lower()
            ):
                self.validation_errors.append(
                    "テーブルにヘッダー（th要素）がありません"
                )

        return len(self.validation_errors) == 0, self.validation_errors
