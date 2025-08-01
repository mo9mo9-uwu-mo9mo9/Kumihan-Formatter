"""
マーカー構文解析 - Issue #476, #665対応

新記法 #キーワード# 対応およびマーカーコンテンツの正規化、キーワード・属性の抽出。
"""

import re
from dataclasses import dataclass, field
from typing import Any

from .definitions import KeywordDefinitions


@dataclass
class ParseResult:
    """テスト互換性のためのパース結果オブジェクト"""

    markers: list[str]
    content: str
    keywords: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class MarkerParser:
    """マーカー構文解析クラス"""

    # プリコンパイルされた正規表現パターン（性能改善）
    _NEW_FORMAT_PATTERN = re.compile(r"^([#＃])\s*(.+)\s*([#＃])\s*(.*)")
    _INLINE_CONTENT_PATTERN = re.compile(r"^[#＃]\s*.+?\s*[#＃]\s*(.*)")
    _FORMAT_CHECK_PATTERN = re.compile(r"^[#＃]\s*.+\s*[#＃]")
    _COLOR_ATTRIBUTE_PATTERN = re.compile(r"\s*color=(#?[a-fA-F0-9]{3,6}|[a-zA-Z]+)")
    # _ALT_ATTRIBUTE_PATTERN = re.compile(r"alt=([^;]+)")  # alt属性は削除されました（Phase 1）
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

    def parse(self, text: str) -> ParseResult | None:
        """
        テキストを解析してマーカー情報を抽出（新記法のみ対応）

        Args:
            text: 解析対象のテキスト

        Returns:
            ParseResult: 解析結果、解析対象がない場合はNone
        """
        text = text.strip()
        if not text:
            return None

        # テキストから#記法#パターンを抽出
        import re

        all_keywords = []
        all_content = []
        all_attributes = {}

        # 改良されたマーカー検出アルゴリズム
        # 複数のマーカーペアを正しく検出する
        i = 0
        while i < len(text):
            if text[i] in "#＃":
                start_pos = i
                start_marker = text[i]
                i += 1

                # 有効なマーカーペアを探す
                # 戦略: バランスの取れたマーカーペアを見つける
                end_pos = self._find_matching_marker(text, start_pos, start_marker)

                if end_pos > start_pos:
                    # マーカー内容を抽出
                    full_content = text[start_pos + 1 : end_pos].strip()

                    if full_content:
                        # キーワードとコンテンツを分離
                        parts = full_content.split(None, 1)  # 最初の空白で分割

                        if parts:
                            keyword = parts[0]
                            content = parts[1] if len(parts) > 1 else ""

                            # 属性解析（color=, alt= など）
                            if "color=" in keyword:
                                # color属性の処理は既存メソッドを利用
                                _, attrs, _ = self.parse_marker_keywords(full_content)
                                all_attributes.update(attrs)
                                # color属性を除いたキーワードを抽出
                                keyword = self._COLOR_ATTRIBUTE_PATTERN.sub("", keyword).strip()

                            all_keywords.append(keyword)
                            if content:
                                all_content.append(content.strip())

                    # 処理した部分をスキップ
                    i = end_pos + 1
                else:
                    # 対応する終了マーカーがない場合は次の文字へ
                    pass
            else:
                i += 1

        # ブロック形式もチェック（インライン形式が見つからない場合）
        if not all_keywords:
            block_pattern = r"^[#＃]([^#＃]+?)$"
            block_match = re.match(block_pattern, text)
            if block_match:
                keyword_part = block_match.group(1).strip()
                keyword = keyword_part.split()[0] if keyword_part.split() else ""
                return ParseResult(
                    markers=[keyword] if keyword else [],
                    content="",
                    keywords=[keyword] if keyword else [],
                    attributes={},
                    errors=[],
                )
            return None

        # コンテンツを結合
        combined_content = " ".join(all_content) if all_content else ""

        if all_keywords:
            return ParseResult(
                markers=all_keywords,
                content=combined_content,
                keywords=all_keywords,
                attributes=all_attributes,
                errors=[],
            )

        return None

    def _find_matching_marker(
        self, text: str, start_pos: int, start_marker: str
    ) -> int:
        """
        開始マーカーに対応する終了マーカーを見つける（特殊文字と複数マーカー両対応）

        Args:
            text: 検索対象のテキスト
            start_pos: 開始マーカーの位置
            start_marker: 開始マーカー文字（# または ＃）

        Returns:
            int: 終了マーカーの位置、見つからない場合は-1
        """
        # 戦略: コンテキストに応じて最適なマッチング戦略を選択

        # 1. 後続にさらにマーカーがあるかチェック
        remaining_text = text[start_pos + 1 :]
        marker_positions = []

        for i, char in enumerate(remaining_text):
            if char == start_marker:
                abs_pos = start_pos + 1 + i
                marker_positions.append(abs_pos)

        if not marker_positions:
            return -1

        # 2. 最適な終了マーカーを決定
        # 複数マーカー検出ヒューリスティック：
        # - 文中に「と」「に」「が」などの接続詞がある場合は複数マーカーの可能性が高い
        # - 特殊文字（!@#$%^&*()など）が多い場合は単一マーカーの可能性が高い

        connection_words = ["と", "に", "が", "で", "を", "は", "の"]
        special_chars = ["!", "@", "$", "%", "^", "&", "*", "(", ")", "_", "=", "+", "#"]

        content_to_first = text[start_pos + 1 : marker_positions[0]]

        connection_count = sum(
            1 for word in connection_words if word in content_to_first
        )
        special_count = sum(1 for char in special_chars if char in content_to_first)

        # 複数マーカーの可能性が高い場合：最初のマーカーを選択
        if connection_count > 0 and len(marker_positions) > 1:
            # さらに検証：最初のマーカーまでの内容に有効なキーワード+コンテンツがあるか
            if self._looks_like_complete_marker(content_to_first):
                return marker_positions[0]

        # color属性を持つ場合の特別な処理
        if "color=" in content_to_first and len(marker_positions) > 1:
            # 次の位置が16進数カラーコードかチェック
            first_marker_pos = marker_positions[0]
            if first_marker_pos + 1 < len(text):
                # color=#xxx の # は終了マーカーではないので、最後のマーカーを選択
                return marker_positions[-1]

        # 特殊文字が多い場合または複数マーカーでない場合：最後のマーカーを選択
        if special_count >= 2 or len(marker_positions) == 1:
            return marker_positions[-1]

        # デフォルト：最初のマーカーを選択（より保守的）
        return marker_positions[0]

    def _looks_like_complete_marker(self, content: str) -> bool:
        """
        コンテンツが完全なマーカー内容に見えるかチェック

        Args:
            content: チェックするコンテンツ

        Returns:
            bool: 完全なマーカーに見える場合True
        """
        content = content.strip()
        if not content:
            return False

        # キーワード + スペース + コンテンツ の形式かチェック
        parts = content.split(None, 1)
        if not parts:
            return False

        keyword = parts[0]

        # 有効なキーワードかチェック（簡易版）
        valid_keywords = [
            "太字",
            "下線",
            "斜体",
            "見出し1",
            "見出し2",
            "見出し3",
            "見出し4",
            "見出し5",
            "イタリック",
            "ハイライト",
            "リスト",
        ]

        # キーワードが有効で、適度な長さのコンテンツがある場合
        if keyword in valid_keywords:
            if len(parts) == 1:  # キーワードのみ（空のコンテンツ）
                return True
            elif len(parts) == 2 and len(parts[1]) > 0:  # キーワード + コンテンツ
                return True

        return False

    def _is_valid_marker_pair(
        self, text: str, start: int, end: int, marker: str
    ) -> bool:
        """
        マーカーペアが有効かどうかを判定

        Args:
            text: テキスト
            start: 開始位置
            end: 終了位置
            marker: マーカー文字

        Returns:
            bool: 有効なペアの場合True
        """
        # 基本的な検証
        if end <= start:
            return False

        # 中間にコンテンツがあることを確認
        content = text[start + 1 : end].strip()
        if not content:
            return False

        # より高度な検証は必要に応じて追加
        # 現在は基本的な構造チェックのみ
        return True

    def _parse_new_format(self, text: str) -> ParseResult:
        """新記法の解析処理"""
        # インライン内容を抽出
        inline_content = self.extract_inline_content(text)

        # マーカー解析
        result = self.parse_new_marker_format(text)
        if result:
            keywords, attributes, errors = result
            return ParseResult(
                markers=keywords,
                content=inline_content or "",
                keywords=keywords,
                attributes=attributes,
                errors=errors,
            )

        return ParseResult(
            markers=[],
            content=inline_content or "",
            keywords=[],
            attributes={},
            errors=["新記法の解析に失敗しました"],
        )

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

        # alt= の前にスペースがない場合は追加（alt属性は削除されました - Phase 1）
        # normalized = re.sub(r"([^\s])alt=", r"\1 alt=", normalized)

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
            marker_content: # マーカー間のコンテンツ（新記法）

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
            color_value = self._sanitize_color_attribute(color_match.group(1))
            attributes["color"] = color_value
            marker_content = re.sub(self._COLOR_ATTRIBUTE_PATTERN, "", marker_content)

        # alt 属性を抽出（画像用、プリコンパイルパターン使用）- alt属性は削除されました（Phase 1）
        # alt_match = self._ALT_ATTRIBUTE_PATTERN.search(marker_content)
        # if alt_match:
        #     alt_value = self._sanitize_alt_attribute(alt_match.group(1).strip())
        #     attributes["alt"] = alt_value
        #     marker_content = re.sub(r"\s*alt=[^;]+", "", marker_content)

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

    # def extract_alt_attribute(self, marker_content: str) -> tuple[str | None, str]:
    #     """マーカーコンテンツからalt属性を抽出 - alt属性は削除されました（Phase 1）
    #
    #     Args:
    #         marker_content: マーカーコンテンツ
    #
    #     Returns:
    #         tuple: (alt値, alt属性を除去したコンテンツ)
    #     """
    #     alt_match = re.search(r"alt=([^;]+)", marker_content)
    #     if alt_match:
    #         alt = alt_match.group(1).strip()
    #         cleaned_content = re.sub(r"\s*alt=[^;]+", "", marker_content)
    #         return alt, cleaned_content
    #     return None, marker_content

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

        # 手動で最後の#マーカーを探す（color属性対応）
        if not (line.startswith('#') or line.startswith('＃')):
            return None
            
        start_marker = line[0]
        
        # ##または＃＃で終わる場合は取り除く
        working_line = line
        if working_line.endswith('##') or working_line.endswith('＃＃'):
            working_line = working_line[:-2].rstrip()
        
        # 最後の#または＃を探す
        last_hash_pos = -1
        for i in range(len(working_line) - 1, 0, -1):
            if working_line[i] in ['#', '＃']:
                last_hash_pos = i
                break
        
        if last_hash_pos == -1 or last_hash_pos == 0:
            return None
            
        end_marker = working_line[last_hash_pos]
        keyword_part = working_line[1:last_hash_pos].strip()
        content = working_line[last_hash_pos + 1:].strip()

        # マーカーの整合性チェック（混在も許可）
        if start_marker not in self.HASH_MARKERS or end_marker not in self.HASH_MARKERS:
            return (
                [],
                {},
                [
                    f"無効なマーカー文字: {start_marker}{keyword_part}{end_marker}。"
                    "正しい形式: # キーワード # または ＃キーワード＃"
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
        
        # リスト項目の場合は除外（リスト内のインライン記法は別途処理）
        if (line.startswith("- ") or line.startswith("・") or 
            line.startswith("* ") or line.startswith("+ ") or
            re.match(r"^\d+\.\s", line)):
            return False
            
        # インライン形式 #キーワード# または ブロック形式 #キーワード を検出
        inline_pattern = r"[#\uff03][^#\uff03]+[#\uff03]"
        block_pattern = r"^[#\uff03][^#\uff03]+$"

        return bool(re.search(inline_pattern, line)) or bool(
            re.match(block_pattern, line)
        )

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

    def _sanitize_color_attribute(self, color_value: str) -> str:
        """
        color属性値をサニタイゼーション

        Args:
            color_value: 生のcolor値

        Returns:
            str: サニタイゼーション済みのcolor値
        """
        # 基本的なサニタイゼーション
        sanitized = color_value.strip()

        # HTMLエンティティエスケープ
        sanitized = sanitized.replace("&", "&amp;")
        sanitized = sanitized.replace("<", "&lt;")
        sanitized = sanitized.replace(">", "&gt;")
        sanitized = sanitized.replace('"', "&quot;")
        sanitized = sanitized.replace("'", "&#x27;")

        # JavaScriptプロトコルの除去
        if sanitized.lower().startswith(("javascript:", "data:", "vbscript:")):
            return "#000000"  # デフォルトの黒色

        # 長さ制限（最大20文字）
        if len(sanitized) > 20:
            sanitized = sanitized[:20]

        return sanitized

    # def _sanitize_alt_attribute(self, alt_value: str) -> str:
    #     """
    #     alt属性値をサニタイゼーション - alt属性は削除されました（Phase 1）
    #
    #     Args:
    #         alt_value: 生のalt値
    #
    #     Returns:
    #         str: サニタイゼーション済みのalt値
    #     """
    #     # 基本的なサニタイゼーション
    #     sanitized = alt_value.strip()
    #
    #     # HTMLエンティティエスケープ
    #     sanitized = sanitized.replace("&", "&amp;")
    #     sanitized = sanitized.replace("<", "&lt;")
    #     sanitized = sanitized.replace(">", "&gt;")
    #     sanitized = sanitized.replace('"', "&quot;")
    #     sanitized = sanitized.replace("'", "&#x27;")
    #
    #     # 改行文字を削除
    #     sanitized = sanitized.replace("\n", " ").replace("\r", " ")
    #
    #     # 連続スペースを単一スペースに
    #     sanitized = re.sub(r"\s+", " ", sanitized)
    #
    #     # 長さ制限（最大100文字）
    #     if len(sanitized) > 100:
    #         sanitized = sanitized[:97] + "..."
    #
    #     return sanitized
