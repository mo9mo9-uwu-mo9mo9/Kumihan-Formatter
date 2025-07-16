"""
マーカー構文解析 - Issue #476対応

マーカーコンテンツの正規化、キーワード・属性の抽出。
"""

import re
from typing import Any

from .definitions import KeywordDefinitions


class MarkerParser:
    """マーカー構文解析クラス"""

    def __init__(self, definitions: KeywordDefinitions) -> None:
        """マーカーパーサーを初期化
        
        Args:
            definitions: キーワード定義
        """
        self.definitions = definitions

    def normalize_marker_syntax(self, marker_content: str) -> str:
        """
        ユーザーフレンドリーな入力のためのマーカー構文正規化

        受け入れる形式:
        - 全角スペース（　） -> 半角スペース( )
        - 属性前のスペースなし -> スペースを追加
        - 複数スペース -> 単一スペース

        Args:
            marker_content: 生のマーカーコンテンツ

        Returns:
            str: 正規化されたマーカーコンテンツ
        """
        # 全角スペースを半角スペースに置換
        normalized = marker_content.replace("　", " ")

        # color= の前にスペースがない場合は追加
        normalized = re.sub(r"([^\s])color=", r"\1 color=", normalized)

        # alt= の前にスペースがない場合は追加
        normalized = re.sub(r"([^\s])alt=", r"\1 alt=", normalized)

        # 複数スペースを単一スペースに正規化
        normalized = re.sub(r"\s+", " ", normalized)

        # 先頭・末尾のスペースをクリーンアップ
        normalized = normalized.strip()

        return normalized

    def parse_marker_keywords(
        self, marker_content: str
    ) -> tuple[list[str], dict[str, Any], list[str]]:
        """
        マーカーコンテンツからキーワードと属性を解析

        Args:
            marker_content: ;;; マーカー間のコンテンツ

        Returns:
            tuple: (キーワード, 属性, エラー)
        """
        # ユーザーフレンドリーな入力のためにマーカーコンテンツを正規化
        marker_content = self.normalize_marker_syntax(marker_content)

        keywords = []
        attributes = {}
        errors: list[str] = []

        # color 属性を抽出
        color_match = re.search(r"color=([#\w]+)", marker_content)
        if color_match:
            attributes["color"] = color_match.group(1)
            marker_content = re.sub(r"\s*color=[#\w]+", "", marker_content)

        # alt 属性を抽出（画像用）
        alt_match = re.search(r"alt=([^;]+)", marker_content)
        if alt_match:
            attributes["alt"] = alt_match.group(1).strip()
            marker_content = re.sub(r"\s*alt=[^;]+", "", marker_content)

        # キーワードを + または ＋ で分割
        if "+" in marker_content or "＋" in marker_content:
            # 複合キーワード
            parts = re.split(r"[+＋]", marker_content)
            for part in parts:
                part = part.strip()
                if part:
                    keywords.append(part)
        else:
            # 単一キーワード
            keyword = marker_content.strip()
            if keyword:
                keywords.append(keyword)

        return keywords, attributes, errors

    def extract_color_attribute(self, marker_content: str) -> tuple[str | None, str]:
        """マーカーコンテンツからcolor属性を抽出
        
        Args:
            marker_content: マーカーコンテンツ
            
        Returns:
            tuple: (color値, color属性を除去したコンテンツ)
        """
        color_match = re.search(r"color=([#\w]+)", marker_content)
        if color_match:
            color = color_match.group(1)
            cleaned_content = re.sub(r"\s*color=[#\w]+", "", marker_content)
            return color, cleaned_content
        return None, marker_content

    def extract_alt_attribute(self, marker_content: str) -> tuple[str | None, str]:
        """マーカーコンテンツからalt属性を抽出
        
        Args:
            marker_content: マーカーコンテンツ
            
        Returns:
            tuple: (alt値, alt属性を除去したコンテンツ)
        """
        alt_match = re.search(r"alt=([^;]+)", marker_content)
        if alt_match:
            alt = alt_match.group(1).strip()
            cleaned_content = re.sub(r"\s*alt=[^;]+", "", marker_content)
            return alt, cleaned_content
        return None, marker_content

    def split_compound_keywords(self, keyword_content: str) -> list[str]:
        """複合キーワードを分割
        
        Args:
            keyword_content: キーワード部分のコンテンツ
            
        Returns:
            キーワードのリスト
        """
        keywords = []
        
        if "+" in keyword_content or "＋" in keyword_content:
            # 複合キーワード
            parts = re.split(r"[+＋]", keyword_content)
            for part in parts:
                part = part.strip()
                if part:
                    keywords.append(part)
        else:
            # 単一キーワード
            keyword = keyword_content.strip()
            if keyword:
                keywords.append(keyword)
        
        return keywords
