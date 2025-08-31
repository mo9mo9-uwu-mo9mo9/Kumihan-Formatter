"""
HTMLUtilities - HTML処理ユーティリティクラス
==========================================

Issue #1215対応: 不足していたHTMLUtilitiesクラスの基本実装
"""

import html
import re
from typing import Dict, List, Optional


class HTMLUtilities:
    """HTML処理ユーティリティクラス - 基本実装"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        HTMLUtilities初期化

        Args:
            config: 設定オプション辞書
        """
        self.config = config or {}
        self._heading_counter = 0

    def escape_html(self, text: str) -> str:
        """HTML文字列のエスケープ"""
        return html.escape(text)

    def heading_counter(self, value: Optional[int] = None) -> int:
        """
        見出しカウンター管理

        Args:
            value: 設定する値（Noneの場合は現在値を返す）

        Returns:
            現在のカウンター値
        """
        if value is not None:
            self._heading_counter = value
        return self._heading_counter

    def generate_heading_id(self, title: str) -> str:
        """
        見出しIDを生成

        Args:
            title: 見出しテキスト

        Returns:
            生成されたID
        """
        # 基本的なID生成（英数字とハイフンのみ）
        clean_title = re.sub(r"[^\w\s-]", "", title.lower())
        clean_title = re.sub(r"[\s_-]+", "-", clean_title)
        clean_title = clean_title.strip("-")

        if not clean_title:
            clean_title = "heading"

        self._heading_counter += 1
        return f"{clean_title}-{self._heading_counter}"

    def generate_toc_from_headings(self, headings: List[Dict[str, Any]]) -> str:
        """
        見出しリストから目次HTMLを生成

        Args:
            headings: 見出し情報のリスト

        Returns:
            目次HTML
        """
        if not headings:
            return ""

        toc_parts = ['<div class="table-of-contents">', "<ul>"]

        for heading in headings:
            level = heading.get("level", 1)
            title = heading.get("title", "")
            heading_id = heading.get("id", self.generate_heading_id(title))

            # レベルに応じたクラス追加
            class_attr = f' class="toc-level-{level}"' if level > 1 else ""
            toc_parts.append(
                f'<li{class_attr}><a href="#{heading_id}">{self.escape_html(title)}</a></li>'
            )

        toc_parts.extend(["</ul>", "</div>"])
        return "\n".join(toc_parts)

    def get_utility_info(self) -> Dict[str, Any]:
        """ユーティリティ情報を取得"""
        return {
            "name": "HTMLUtilities",
            "version": "1.0.0",
            "heading_counter": self._heading_counter,
            "config": self.config,
        }

    def sanitize_html_attributes(self, attributes: Dict[str, str]) -> Dict[str, str]:
        """
        HTML属性の無害化

        Args:
            attributes: 属性辞書

        Returns:
            無害化された属性辞書
        """
        safe_attributes = {}

        for key, value in attributes.items():
            # 基本的な無害化（危険なスクリプト系属性を除外）
            if not key.lower().startswith(("on", "javascript:")):
                safe_key = re.sub(r"[^a-zA-Z0-9-_]", "", key)
                safe_value = self.escape_html(str(value))
                if safe_key:
                    safe_attributes[safe_key] = safe_value

        return safe_attributes

    def build_html_tag(
        self,
        tag_name: str,
        content: str = "",
        attributes: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        HTMLタグを構築

        Args:
            tag_name: タグ名
            content: コンテンツ
            attributes: 属性辞書

        Returns:
            構築されたHTMLタグ
        """
        safe_tag = re.sub(r"[^a-zA-Z0-9]", "", tag_name.lower())
        if not safe_tag:
            return self.escape_html(content)

        # 属性処理
        attr_str = ""
        if attributes:
            safe_attrs = self.sanitize_html_attributes(attributes)
            attr_parts = []
            for key, value in safe_attrs.items():
                attr_parts.append(f'{key}="{value}"')
            if attr_parts:
                attr_str = " " + " ".join(attr_parts)

        # 自己閉じタグの判定
        void_elements = {"br", "hr", "img", "input", "meta", "link"}
        if safe_tag in void_elements:
            return f"<{safe_tag}{attr_str}>"
        else:
            return f"<{safe_tag}{attr_str}>{content}</{safe_tag}>"
