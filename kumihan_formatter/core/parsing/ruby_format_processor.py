"""Ruby Format Processor - ルビ記法処理専用モジュール

core_marker_parser.py分割により抽出 (Phase3最適化)
ルビ記法処理関連の機能をすべて統合
"""

import re
from typing import Any, Dict, List, Optional, Union

import logging


class RubyFormatProcessor:
    """ルビ記法処理専用クラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()

    def _initialize_patterns(self):
        """ルビ記法パターンを初期化"""
        # 基本ルビパターン: 漢字(ひらがな)
        self.ruby_pattern = re.compile(r"([^\s\(\)]+)\(([^\)]+)\)", re.UNICODE)

        # 複雑なルビパターン: |漢字《ひらがな》
        self.complex_ruby_pattern = re.compile(r"\|([^《]+)《([^》]+)》", re.UNICODE)

        # 英語ルビパターン: word(pronunciation)
        self.english_ruby_pattern = re.compile(
            r"([a-zA-Z]+)\(([a-zA-Z\s\/\-\.]+)\)", re.IGNORECASE
        )

        # HTMLルビパターン: <ruby>漢字<rt>ひらがな</rt></ruby>
        self.html_ruby_pattern = re.compile(
            r"<ruby>([^<]+)<rt>([^<]+)</rt></ruby>", re.IGNORECASE
        )

    def parse_ruby_content(self, content: str) -> Optional[Dict[str, Any]]:
        """ルビコンテンツを解析

        Args:
            content: 解析対象コンテンツ

        Returns:
            ルビ情報辞書またはNone
        """
        if not content or not content.strip():
            return None

        ruby_info = {
            "base_text": content,
            "ruby_annotations": [],
            "format_type": None,
            "processed_text": content,
        }

        # 各パターンでルビを検索
        found_ruby = False

        # 1. 複雑なルビパターン（優先度高）
        if self._process_complex_ruby(content, ruby_info):
            found_ruby = True

        # 2. 基本ルビパターン
        elif self._process_basic_ruby(content, ruby_info):
            found_ruby = True

        # 3. 英語ルビパターン
        elif self._process_english_ruby(content, ruby_info):
            found_ruby = True

        # 4. HTMLルビパターン
        elif self._process_html_ruby(content, ruby_info):
            found_ruby = True

        return ruby_info if found_ruby else None

    def _process_complex_ruby(self, content: str, ruby_info: Dict[str, Any]) -> bool:
        """複雑なルビパターンを処理"""
        matches = list(self.complex_ruby_pattern.finditer(content))
        if not matches:
            return False

        ruby_info["format_type"] = "complex"
        processed_text = content

        # 後ろから処理（位置ずれを防ぐため）
        for match in reversed(matches):
            base = match.group(1).strip()
            ruby = match.group(2).strip()

            ruby_info["ruby_annotations"].append(
                {"base": base, "ruby": ruby, "start": match.start(), "end": match.end()}
            )

            # HTMLルビタグに変換
            html_ruby = f"<ruby>{base}<rt>{ruby}</rt></ruby>"
            processed_text = (
                processed_text[: match.start()]
                + html_ruby
                + processed_text[match.end() :]
            )

        ruby_info["processed_text"] = processed_text
        ruby_info["ruby_annotations"].reverse()  # 元の順序に戻す
        return True

    def _process_basic_ruby(self, content: str, ruby_info: Dict[str, Any]) -> bool:
        """基本ルビパターンを処理"""
        matches = list(self.ruby_pattern.finditer(content))
        if not matches:
            return False

        # 日本語ルビかどうか判定
        is_japanese = any(
            self._is_japanese_text(match.group(1))
            or self._is_japanese_text(match.group(2))
            for match in matches
        )

        if not is_japanese:
            return False

        ruby_info["format_type"] = "basic"
        processed_text = content

        # 後ろから処理
        for match in reversed(matches):
            base = match.group(1).strip()
            ruby = match.group(2).strip()

            ruby_info["ruby_annotations"].append(
                {"base": base, "ruby": ruby, "start": match.start(), "end": match.end()}
            )

            # HTMLルビタグに変換
            html_ruby = f"<ruby>{base}<rt>{ruby}</rt></ruby>"
            processed_text = (
                processed_text[: match.start()]
                + html_ruby
                + processed_text[match.end() :]
            )

        ruby_info["processed_text"] = processed_text
        ruby_info["ruby_annotations"].reverse()
        return True

    def _process_english_ruby(self, content: str, ruby_info: Dict[str, Any]) -> bool:
        """英語ルビパターンを処理"""
        matches = list(self.english_ruby_pattern.finditer(content))
        if not matches:
            return False

        ruby_info["format_type"] = "english"
        processed_text = content

        for match in reversed(matches):
            base = match.group(1).strip()
            pronunciation = match.group(2).strip()

            ruby_info["ruby_annotations"].append(
                {
                    "base": base,
                    "ruby": pronunciation,
                    "type": "pronunciation",
                    "start": match.start(),
                    "end": match.end(),
                }
            )

            # HTMLルビタグに変換
            html_ruby = f"<ruby>{base}<rt>{pronunciation}</rt></ruby>"
            processed_text = (
                processed_text[: match.start()]
                + html_ruby
                + processed_text[match.end() :]
            )

        ruby_info["processed_text"] = processed_text
        ruby_info["ruby_annotations"].reverse()
        return True

    def _process_html_ruby(self, content: str, ruby_info: Dict[str, Any]) -> bool:
        """HTMLルビパターンを処理"""
        matches = list(self.html_ruby_pattern.finditer(content))
        if not matches:
            return False

        ruby_info["format_type"] = "html"
        ruby_info["processed_text"] = content  # 既にHTMLなのでそのまま

        for match in matches:
            base = match.group(1).strip()
            ruby = match.group(2).strip()

            ruby_info["ruby_annotations"].append(
                {"base": base, "ruby": ruby, "start": match.start(), "end": match.end()}
            )

        return True

    def _is_japanese_text(self, text: str) -> bool:
        """テキストが日本語かどうか判定"""
        if not text:
            return False

        # ひらがな、カタカナ、漢字の範囲
        japanese_pattern = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]")
        return bool(japanese_pattern.search(text))

    def convert_to_html_ruby(self, content: str) -> str:
        """コンテンツをHTMLルビ形式に変換

        Args:
            content: 元のコンテンツ

        Returns:
            HTMLルビ形式に変換されたコンテンツ
        """
        ruby_info = self.parse_ruby_content(content)
        return ruby_info["processed_text"] if ruby_info else content

    def extract_ruby_annotations(self, content: str) -> List[Dict[str, Any]]:
        """コンテンツからルビ注釈を抽出

        Args:
            content: 解析対象コンテンツ

        Returns:
            ルビ注釈のリスト
        """
        ruby_info = self.parse_ruby_content(content)
        return ruby_info["ruby_annotations"] if ruby_info else []

    def has_ruby_content(self, content: str) -> bool:
        """コンテンツにルビが含まれているか判定

        Args:
            content: 判定対象コンテンツ

        Returns:
            ルビが含まれているかどうか
        """
        return self.parse_ruby_content(content) is not None

    def get_ruby_statistics(self, content: str) -> Dict[str, Any]:
        """ルビ統計情報を取得

        Args:
            content: 解析対象コンテンツ

        Returns:
            ルビ統計情報
        """
        ruby_info = self.parse_ruby_content(content)

        if not ruby_info:
            return {"has_ruby": False, "ruby_count": 0, "format_type": None}

        annotations = ruby_info["ruby_annotations"]

        return {
            "has_ruby": True,
            "ruby_count": len(annotations),
            "format_type": ruby_info["format_type"],
            "base_characters": sum(len(ann["base"]) for ann in annotations),
            "ruby_characters": sum(len(ann["ruby"]) for ann in annotations),
            "unique_bases": len(set(ann["base"] for ann in annotations)),
            "unique_rubies": len(set(ann["ruby"] for ann in annotations)),
        }
