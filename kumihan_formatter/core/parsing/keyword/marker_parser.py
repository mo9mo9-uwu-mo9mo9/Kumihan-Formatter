"""
マーカー構文解析 - Issue #476, #665対応

新記法 #キーワード# 対応およびマーカーコンテンツの正規化、キーワード・属性の抽出。
"""

import re
from typing import Any, List

# Import from new location for backward compatibility
from .parse_result import ParseResult


class MarkerParser:
    """マーカー構文解析クラス - 軽量化版（分割されたパーサー統合）"""

    def __init__(self, definitions: Any) -> None:
        """マーカーパーサーを初期化

        Args:
            definitions: キーワード定義
        """
        self.definitions = definitions
        from kumihan_formatter.core.utilities.logger import get_logger

        self.logger = get_logger(__name__)

        # Initialize component parsers
        from .attribute_parser import AttributeParser
        from .content_parser import ContentParser
        from .keyword_parser import KeywordParser

        self.keyword_parser = KeywordParser(definitions)
        self.attribute_parser = AttributeParser()
        self.content_parser = ContentParser()

        # Legacy patterns for backward compatibility
        self._NEW_FORMAT_PATTERN = re.compile(r"^([#＃])\s*(.+)\s*([#＃])\s*(.*)")
        self._INLINE_CONTENT_PATTERN = re.compile(r"^([#＃])\s*(.+?)\s*([#＃])\s*(.*)")
        self._FORMAT_CHECK_PATTERN = re.compile(r"^[#＃]\s*.+\s*[#＃]")
        self._COLOR_ATTRIBUTE_PATTERN = re.compile(
            r"\s*color=(#?[a-fA-F0-9]{3,6}|[a-zA-Z]+)"
        )
        self._KEYWORD_SPLIT_PATTERN = re.compile(r"[+＋]")

        # 新記法対応: マーカー文字の定義
        self.HASH_MARKERS = ["#", "＃"]  # 半角・全角両対応
        self.BLOCK_END_MARKERS = ["##", "＃＃"]  # ブロック終了マーカー

        # Issue #751対応: パフォーマンス改善のため正規表現を事前コンパイル
        self._inline_pattern_1 = re.compile(r"^[#＃]\s*([^#＃]+)\s*[#＃]\s+(.+)$")
        self._inline_pattern_2 = re.compile(r"^[#＃]\s*([^#＃]+)\s+([^#＃]+)\s*[#＃]$")
        self._inline_pattern_3 = re.compile(
            r"^[#＃]\s+([^#＃]+)\s+[#＃]([^#＃]+)[#＃][#＃]$"
        )

        # ブロック記法パターン
        self._basic_pattern = re.compile(r"^[#＃]\s*[^#＃]+\s*[#＃]$")
        self._attribute_pattern = re.compile(r"^[#＃]\s*[^#＃]+\s+[^#＃]+=\S+\s*[#＃]$")
        self._compound_pattern = re.compile(r"^[#＃]\s*[^#＃]+[+＋][^#＃]+\s*[#＃]$")

        # リストアイテムパターン
        self._list_item_pattern = re.compile(r"^\d+\.\s")

    def parse_footnotes(self, text: str) -> list[dict[str, Any]]:
        """廃止済み脚注パーサー - 新記法ブロック形式に移行"""
        self.logger.warning(
            "parse_footnotes() is deprecated. "
            "Use new block format '# 脚注 #内容##' instead."
        )
        return []

    def extract_footnotes_from_text(
        self, text: str
    ) -> tuple[str, list[dict[str, Any]]]:
        """廃止済み脚注抽出機能 - 新記法ブロック形式に移行"""
        self.logger.warning(
            "extract_footnotes_from_text() is deprecated. "
            "Use new block format '# 脚注 #内容##' instead."
        )
        return text, []

    def parse(self, text: str) -> ParseResult | None:
        """テキストを解析してマーカー情報を抽出（新記法のみ対応）

        Args:
            text: 解析対象のテキスト

        Returns:
            ParseResult: 解析結果、解析対象がない場合はNone
        """
        text = text.strip()
        if not text:
            return None

        # インライン形式の解析
        all_keywords = []
        all_content = []
        all_attributes = {}
        i = 0

        while i < len(text):
            if text[i] in self.HASH_MARKERS:
                start_pos = i
                start_marker = text[i]
                i += 1

                # 有効なマーカーペアを探す
                end_pos = self._find_matching_marker(text, start_pos, start_marker)

                if end_pos > start_pos:
                    # マーカー内容を抽出
                    full_content = text[start_pos + 1 : end_pos].strip()

                    if full_content:
                        # キーワードとコンテンツを分離
                        parts = full_content.split(None, 1)

                        if parts:
                            keyword = parts[0]
                            content = parts[1] if len(parts) > 1 else ""

                            # ルビ記法の特殊処理
                            ruby_result = None
                            if keyword == "ルビ":
                                ruby_result = self._parse_ruby_content(content)
                            if ruby_result:
                                all_attributes.update(ruby_result)
                                all_keywords.append(keyword)
                                if content:
                                    all_content.append(content.strip())
                                continue

                        # 属性解析（color=, alt= など）
                        if "color=" in keyword:
                            # color属性の処理
                            _, attrs, _ = self.parse_marker_keywords(full_content)
                            all_attributes.update(attrs)
                            # color属性を除いたキーワードを抽出
                            keyword = self._COLOR_ATTRIBUTE_PATTERN.sub(
                                "", keyword
                            ).strip()

                        all_keywords.append(keyword)
                        if content:
                            all_content.append(content.strip())

                    # 処理した部分をスキップ
                    i = end_pos + 1
                else:
                    # 対応する終了マーカーがない場合は次の文字へ
                    i += 1
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
                    markers=[(0, len(keyword), keyword)] if keyword else [],
                    content="",
                    keywords=[keyword] if keyword else [],
                    attributes={},
                    errors=[],
                )
            return None

        # 結果をまとめる
        if all_keywords:
            combined_content = " ".join(all_content) if all_content else ""
            return ParseResult(
                markers=[(i, len(kw), kw) for i, kw in enumerate(all_keywords)],
                content=combined_content,
                keywords=all_keywords,
                attributes=all_attributes,
                errors=[],
            )

        return None

    def _find_matching_marker(
        self, text: str, start_pos: int, start_marker: str
    ) -> int:
        """開始マーカーに対応する終了マーカーを見つける"""
        remaining_text = text[start_pos + 1 :]
        marker_positions = []

        # すべてのマーカー位置を収集
        for i, char in enumerate(remaining_text):
            if char == start_marker:
                abs_pos = start_pos + 1 + i
                marker_positions.append(abs_pos)

        if not marker_positions:
            return -1

        # 最も近い有効なマーカーを探す
        for pos in marker_positions:
            content_to_pos = text[start_pos + 1 : pos]
            if self._is_valid_marker_content(content_to_pos):
                return pos

        return -1

    def _contains_color_attribute(self, content: str) -> bool:
        """コンテンツにcolor属性が含まれているかをチェック"""
        return bool(self._COLOR_ATTRIBUTE_PATTERN.search(content))

    def _is_valid_marker_content(self, content: str) -> bool:
        """マーカー内容が有効かどうかをチェック（簡素化版）"""
        content = content.strip()
        if not content:
            return False
        return True

    def parse_marker_keywords(
        self, marker_content: str
    ) -> tuple[list[str], dict[str, Any], list[str]]:
        """マーカーコンテンツからキーワードと属性を解析"""
        return self.keyword_parser.parse_marker_keywords(marker_content)

    def extract_color_attribute(self, marker_content: str) -> tuple[str, str]:
        """マーカーコンテンツからcolor属性を抽出"""
        return self.attribute_parser.extract_color_attribute(marker_content)

    def split_compound_keywords(self, keyword_content: str) -> list[str]:
        """複合キーワードを分割"""
        return self.keyword_parser.split_compound_keywords(keyword_content)

    def normalize_marker_syntax(self, marker_content: str) -> str:
        """マーカー構文正規化"""
        return self.content_parser.normalize_marker_syntax(marker_content)

    def is_new_marker_format(self, line: str) -> bool:
        """行が新記法 # キーワード # 形式かどうかを判定"""
        return self.content_parser.is_new_marker_format(line)

    def is_block_end_marker(self, line: str) -> bool:
        """行がブロック終了マーカー ## または ＃＃ かどうかを判定"""
        return self.content_parser.is_block_end_marker(line)

    def extract_inline_content(self, line: str) -> str | None:
        """インライン記法からコンテンツを抽出"""
        return self.content_parser.extract_inline_content(line)

    def parse_new_marker_format(
        self, line: str
    ) -> tuple[list[str], dict[str, Any], list[str]] | None:
        """新記法 # キーワード # 形式のマーカーを解析"""
        line = line.strip()

        # 手動で最後の#マーカーを探す（color属性対応）
        if not (line.startswith("#") or line.startswith("＃")):
            return None

        last_hash_pos = -1
        for i in range(len(line) - 1, 0, -1):
            if line[i] in ("#", "＃"):
                last_hash_pos = i
                break

        if last_hash_pos == -1 or last_hash_pos == 0:
            return None

        start_marker = line[0]
        keyword_part = line[1:last_hash_pos]
        end_marker = line[last_hash_pos]

        if not keyword_part.strip():
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
        """新記法固有の構文検証"""
        errors: List[str] = []

        # 空のキーワード部分チェック
        if not keyword_part.strip():
            errors.append(
                "キーワードが指定されていません。例: # 太字 # または # 見出し1 #"
            )

        # キーワード長さチェック
        if len(keyword_part.strip()) > 50:
            errors.append(
                f"キーワードが長すぎます（50文字以内）: '{keyword_part[:20]}...'"
            )

        # 不正文字チェック
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

        # 空白のみの複合キーワードチェック
        if "+" in keyword_part or "＋" in keyword_part:
            parts = self._KEYWORD_SPLIT_PATTERN.split(keyword_part)
            empty_parts = [i for i, part in enumerate(parts) if not part.strip()]
            if empty_parts:
                errors.append(
                    f"複合キーワードに空の部分があります（位置: {empty_parts}）"
                )

        return errors

    def _parse_ruby_content(self, content: str) -> dict[str, Any] | None:
        """ルビ記法のコンテンツを解析"""
        if not content:
            return None

        # 簡略化されたルビ解析
        ruby_pattern = r"([^()（）]+)[()（]([^()（）]+)[)）]"
        match = re.search(ruby_pattern, content)

        if match:
            base_text = match.group(1).strip()
            ruby_text = match.group(2).strip()

            # 混在チェック
            if "(" in content and "（" in content:
                return None  # 混在は無効

            return {"ruby_base": base_text, "ruby_text": ruby_text}

        return None

    def _contains_malicious_content(self, content: str) -> bool:
        """脚注内容に悪意のあるコンテンツが含まれているかチェック"""
        if not content:
            return False

        malicious_patterns = ["<script", "javascript:", "data:", "vbscript:"]
        content_lower = content.lower()
        for pattern in malicious_patterns:
            if pattern in content_lower:
                return True
        return False

    def _sanitize_footnote_content(self, content: str) -> str:
        """脚注内容のサニタイゼーション"""
        if not content:
            return ""
        return content.strip()

    def _validate_footnote_structure(self, footnotes: list[Any]) -> list[str]:
        """脚注構造の妥当性検証"""
        errors: list[str] = []
        if not footnotes:
            return errors
        return errors

    def _sanitize_color_attribute(self, color_value: str) -> str:
        """color属性値をサニタイゼーション"""
        sanitized = color_value.strip()
        sanitized = sanitized.replace("&", "&amp;")
        sanitized = sanitized.replace("<", "&lt;")
        sanitized = sanitized.replace(">", "&gt;")
        sanitized = sanitized.replace('"', "&quot;")
        sanitized = sanitized.replace("'", "&#x27;")
        if sanitized.lower().startswith(("javascript:", "data:", "vbscript:")):
            return "#000000"
        return sanitized
