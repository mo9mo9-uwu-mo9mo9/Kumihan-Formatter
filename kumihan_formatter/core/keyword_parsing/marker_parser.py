"""
マーカー構文解析 - Issue #476, #665対応

新記法 #キーワード# 対応およびマーカーコンテンツの正規化、キーワード・属性の抽出。
"""

import re
from typing import Any, TypedDict

from .definitions import KeywordDefinitions


class ParseResult(TypedDict):
    """新記法パース結果の型定義"""

    keywords: list[str]
    attributes: dict[str, Any]
    errors: list[str]


class MarkerParser:
    """マーカー構文解析クラス"""

    # プリコンパイルされた正規表現パターン（性能改善）
    _NEW_FORMAT_PATTERN = re.compile(r"^([#＃])\s*(\S.+?)\s*([#＃])\s*(.*)")
    _INLINE_CONTENT_PATTERN = re.compile(r"^[#＃]\s*.+?\s*[#＃]\s*(.*)")
    _FORMAT_CHECK_PATTERN = re.compile(r"^[#＃]\s*.+\s*[#＃]")
    _COLOR_ATTRIBUTE_PATTERN = re.compile(r"color=([#\w]+)")
    _ALT_ATTRIBUTE_PATTERN = re.compile(r"alt=([^;]+)")
    _KEYWORD_SPLIT_PATTERN = re.compile(r"[+＋]")

    def __init__(self, definitions: KeywordDefinitions) -> None:
        """マーカーパーサーを初期化

        Args:
            definitions: キーワード定義
        """
        self.definitions = definitions

        # 新記法対応: マーカー文字の定義
        self.HASH_MARKERS = ["#", "＃"]  # 半角・全角両対応
        self.BLOCK_END_MARKERS = ["##", "＃＃"]  # ブロック終了マーカー

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

        # color 属性を抽出（プリコンパイルパターン使用）
        color_match = self._COLOR_ATTRIBUTE_PATTERN.search(marker_content)
        if color_match:
            attributes["color"] = color_match.group(1)
            marker_content = re.sub(r"\s*color=[#\w]+", "", marker_content)

        # alt 属性を抽出（画像用、プリコンパイルパターン使用）
        alt_match = self._ALT_ATTRIBUTE_PATTERN.search(marker_content)
        if alt_match:
            attributes["alt"] = alt_match.group(1).strip()
            marker_content = re.sub(r"\s*alt=[^;]+", "", marker_content)

        # キーワードを + または ＋ で分割（プリコンパイルパターン使用）
        if "+" in marker_content or "＋" in marker_content:
            # 複合キーワード
            parts = self._KEYWORD_SPLIT_PATTERN.split(marker_content)
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

    def parse_new_marker_format(
        self, line: str
    ) -> tuple[list[str], dict[str, Any], list[str]] | None:
        """
        新記法 # キーワード # 形式のマーカーを解析

        対応形式:
        - # 太字 # 内容
        - ＃太字＃ 内容
        - # 太字 color=#ff0000 # 内容
        - ＃見出し1＋太字＃ 内容

        Args:
            line: 解析対象の行

        Returns:
            tuple: (キーワード, 属性, エラー) または None（非対応形式の場合）
        """
        line = line.strip()

        # 新記法のパターンマッチング（境界条件修正済み）
        # # キーワード # 形式の検出 (半角・全角・混在対応)
        # \S.+? で非空白文字必須、空白のみキーワードを防止
        match = self._NEW_FORMAT_PATTERN.match(line)

        if not match:
            return None

        start_marker, keyword_part, end_marker, content = match.groups()

        # マーカーの整合性チェック（混在も許可）
        if start_marker not in self.HASH_MARKERS or end_marker not in self.HASH_MARKERS:
            return (
                [],
                {},
                [
                    f"無効なマーカー文字: {start_marker}{keyword_part}{end_marker}。正しい形式: # キーワード # または ＃キーワード＃"
                ],
            )

        # キーワード部分と属性を解析
        keywords, attributes, errors = self.parse_marker_keywords(keyword_part)

        # 新記法固有の検証
        additional_errors = self._validate_new_format_syntax(
            start_marker, end_marker, keyword_part
        )
        errors.extend(additional_errors)

        return keywords, attributes, errors

    def _validate_new_format_syntax(
        self, start_marker: str, end_marker: str, keyword_part: str
    ) -> list[str]:
        """
        新記法固有の構文検証

        Args:
            start_marker: 開始マーカー
            end_marker: 終了マーカー
            keyword_part: キーワード部分

        Returns:
            list[str]: エラーメッセージリスト
        """
        errors = []

        # 空のキーワード部分チェック
        if not keyword_part.strip():
            errors.append(
                "キーワードが指定されていません。例: # 太字 # または # 見出し1 #"
            )

        # キーワード長さチェック（追加）
        if len(keyword_part.strip()) > 50:
            errors.append(
                f"キーワードが長すぎます（50文字以内）: '{keyword_part[:20]}...'"
            )

        # 不正文字チェック（追加）
        invalid_chars = set(keyword_part) & {"<", ">", '"', "'", "&"}
        if invalid_chars:
            errors.append(f"無効な文字が含まれています: {', '.join(invalid_chars)}")

        # Markdownとの競合チェック
        if keyword_part.strip().isdigit():
            errors.append(
                f"数字のみのキーワード '{keyword_part}' はMarkdown見出しと競合します"
            )

        # 予約語チェック
        reserved_words = ["#", "##", "###", "javascript:", "data:", "vbscript:"]
        if keyword_part.strip().lower() in [w.lower() for w in reserved_words]:
            errors.append(f"予約語 '{keyword_part}' は使用できません")

        # 空白のみの複合キーワードチェック（追加）
        if "+" in keyword_part or "＋" in keyword_part:
            parts = self._KEYWORD_SPLIT_PATTERN.split(keyword_part)
            empty_parts = [i for i, part in enumerate(parts) if not part.strip()]
            if empty_parts:
                errors.append(
                    f"複合キーワードに空の部分があります（位置: {empty_parts}）"
                )

        return errors

    def is_new_marker_format(self, line: str) -> bool:
        """
        行が新記法 # キーワード # 形式かどうかを判定

        Args:
            line: 判定対象の行

        Returns:
            bool: 新記法の場合True
        """
        line = line.strip()
        return bool(self._FORMAT_CHECK_PATTERN.match(line))

    def is_block_end_marker(self, line: str) -> bool:
        """
        行がブロック終了マーカー ## または ＃＃ かどうかを判定（厳密化）

        Args:
            line: 判定対象の行

        Returns:
            bool: ブロック終了マーカーの場合True
        """
        line = line.strip()

        # 厳密な完全一致チェック（"## コメント" などを除外）
        if line not in self.BLOCK_END_MARKERS:
            return False

        # 追加の安全チェック: 空白で分割した最初の要素が終了マーカーと一致
        first_token = line.split()[0] if line.split() else ""
        return first_token in self.BLOCK_END_MARKERS and first_token == line

    def extract_inline_content(self, line: str) -> str | None:
        """
        新記法からインライン内容を抽出

        例: "# 太字 # これが内容" → "これが内容"

        Args:
            line: 解析対象の行

        Returns:
            str: インライン内容、ブロック記法の場合はNone
        """
        line = line.strip()
        match = self._INLINE_CONTENT_PATTERN.match(line)

        if match:
            content = match.group(1).strip()
            return content if content else None
        return None
