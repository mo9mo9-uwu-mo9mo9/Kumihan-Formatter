"""Block parsing utilities for Kumihan-Formatter

This module handles the parsing of basic block-level elements.
新記法 #キーワード# 対応 - Issue #665
"""

import re
from typing import Any

from ..ast_nodes import Node, error_node, paragraph, toc_marker
from ..keyword_parser import KeywordParser
from ..utilities.logger import get_logger


class BlockParser:
    """Parser for block-level elements"""

    def __init__(self, keyword_parser: KeywordParser) -> None:
        self.logger = get_logger(__name__)
        self.keyword_parser = keyword_parser
        self.heading_counter = 0

        # パフォーマンス最適化: キャッシュとインデックス
        self._block_end_indices: list[int] = []
        self._lines_cache: list[str] = []

        self.logger.debug("BlockParser initialized with performance optimizations")


    def _preprocess_lines(self, lines: list[str]) -> None:
        """行データの前処理でパフォーマンス最適化

        Args:
            lines: 処理対象の行データリスト
        """
        if not lines:
            self.logger.warning("Empty lines list provided to _preprocess_lines")
            self._block_end_indices.clear()
            self._lines_cache = []
            return

        # キャッシュリセット
        self._block_end_indices.clear()
        self._lines_cache = lines.copy()  # 安全なコピーを作成

        # ブロック終了マーカーの位置を事前計算（O(n)で一回のみ）
        try:
            for i, line in enumerate(lines):
                if i >= 10000:  # 安全弁: 極端に大きなファイルの処理防止
                    self.logger.warning(
                        f"File too large, stopping preprocessing at line {i}"
                    )
                    break

                stripped = line.strip()
                if self.keyword_parser.marker_parser.is_block_end_marker(stripped):
                    self._block_end_indices.append(i)
            self.logger.debug(
                f"Preprocessed {len(lines)} lines, "
                f"found {len(self._block_end_indices)} block end markers"
            )
        except Exception as e:
            self.logger.error(f"Error during preprocessing: {e}")
            self._block_end_indices.clear()
            self._lines_cache = []

    def _find_next_block_end(self, start_index: int) -> int | None:
        """最適化された次のブロック終了マーカー検索（O(log n)二分探索）

        Args:
            start_index: 検索開始位置

        Returns:
            次のブロック終了インデックス、見つからない場合はNone
        """
        import bisect

        # 安全性チェック: キャッシュが初期化されているか確認
        if not self._block_end_indices:
            self.logger.warning(
                f"Block end indices cache is empty at start_index {start_index}"
            )
            return None

        # 範囲チェック: start_indexが有効範囲内か確認
        if start_index < 0 or (
            self._lines_cache and start_index >= len(self._lines_cache)
        ):
            self.logger.warning(
                f"Invalid start_index {start_index}, lines count: {len(self._lines_cache) if self._lines_cache else 0}"
            )
            return None

        # 二分探索でstart_indexより大きい最初のインデックスを検索
        pos = bisect.bisect_right(self._block_end_indices, start_index)

        if pos < len(self._block_end_indices):
            result = self._block_end_indices[pos]
            self.logger.debug(
                f"Found block end at index {result} for start_index {start_index}"
            )
            return result

        self.logger.debug(f"No block end found after start_index {start_index}")
        return None

    @staticmethod
    def _is_block_marker_cached(line: str, keyword_parser: KeywordParser) -> bool:
        """キャッシュを使用した高速ブロックマーカー判定（LRUキャッシュ対応）

        Args:
            line: 判定対象の行
            keyword_parser: キーワードパーサーインスタンス

        Returns:
            ブロックマーカーの場合True
        """
        from functools import lru_cache

        @lru_cache(maxsize=512)  # メモリ上限設定
        def _cached_marker_check(stripped_line: str) -> bool:
            """内部キャッシュ関数"""
            return keyword_parser.marker_parser.is_new_marker_format(
                stripped_line
            ) or keyword_parser.marker_parser.is_block_end_marker(stripped_line)

        return _cached_marker_check(line)

    def parse_new_format_marker(
        self, lines: list[str], start_index: int
    ) -> tuple[Node | None, int]:
        """
        新記法 # キーワード # 形式のマーカーを解析（最適化版）

        Args:
            lines: All lines in the document
            start_index: Index of the marker line

        Returns:
            tuple: (parsed_node, next_index)

        Raises:
            ValueError: start_indexが範囲外の場合
        """
        if start_index < 0 or start_index >= len(lines):
            raise ValueError(
                f"start_index {start_index} is out of range [0, {len(lines)})"
            )

        self.logger.debug(f"Parsing new format marker at line {start_index + 1}")

        # 前処理が未実行の場合は実行
        if not self._lines_cache or self._lines_cache != lines:
            self._preprocess_lines(lines)

        opening_line = lines[start_index].strip()
        self.logger.debug(f"Opening line: {opening_line}")

        # 新記法のマーカーパース
        parse_result = self.keyword_parser.marker_parser.parse_new_marker_format(
            opening_line
        )
        if parse_result is None:
            # Issue #700: graceful error handling対応 - 不正な記法をgraceful errorとして記録
            if hasattr(self, 'parser_ref') and self.parser_ref and self.parser_ref.graceful_errors:
                self.parser_ref._record_graceful_error(
                    start_index + 1,  # 1-based line number
                    1,  # column
                    "invalid_marker_format",
                    "error",
                    "不正なマーカー記法: 終了マーカー # が見つかりません",
                    opening_line,
                    "正しい記法: # キーワード # 内容 または # キーワード #\n内容\n##",
                )
            return None, start_index

        keywords, attributes, parse_errors = parse_result

        if parse_errors:
            self.logger.error(f"Parse errors in new format keywords: {parse_errors}")
            return error_node("; ".join(parse_errors), start_index + 1), start_index + 1

        # インライン内容を抽出
        inline_content = self.keyword_parser.marker_parser.extract_inline_content(
            opening_line
        )

        if inline_content:
            # インライン記法: # キーワード # 内容
            self.logger.debug(f"Processing inline content: {inline_content}")
            if len(keywords) == 1:
                node = self.keyword_parser.create_single_block(
                    keywords[0], inline_content, attributes
                )
            else:
                node = self.keyword_parser.create_compound_block(
                    keywords, inline_content, attributes
                )
            return node, start_index + 1
        else:
            # ブロック記法: # キーワード # \n 内容 \n ##
            return self._parse_new_format_block(
                lines, start_index, keywords, attributes
            )

    def _parse_new_format_block(
        self,
        lines: list[str],
        start_index: int,
        keywords: list[str],
        attributes: dict[str, Any],
    ) -> tuple[Node | None, int]:
        """
        新記法のブロック形式を解析（最適化版）

        Args:
            lines: All lines in the document
            start_index: Index of the opening marker
            keywords: Parsed keywords
            attributes: Parsed attributes

        Returns:
            tuple: (parsed_node, next_index)

        Raises:
            ValueError: パラメータが不正な場合
        """
        if not keywords:
            raise ValueError("Keywords list cannot be empty")

        self.logger.debug(f"Parsing new format block at line {start_index + 1}")

        # 前処理が未実行またはキャッシュが古い場合は実行
        if not self._lines_cache or self._lines_cache != lines:
            self.logger.debug("Preprocessing lines for block parsing")
            self._preprocess_lines(lines)

        # 最適化された終了マーカー検索（O(log n)二分探索）
        end_index = self._find_next_block_end(start_index)

        if end_index is None:
            self.logger.error(f"Block end marker not found for line {start_index + 1}")
            
            # Issue #700: graceful error handling対応
            if hasattr(self, 'parser_ref') and self.parser_ref and self.parser_ref.graceful_errors:
                self.parser_ref._record_graceful_error(
                    start_index + 1,  # 1-based line number
                    1,  # column
                    "incomplete_block_marker",
                    "error",
                    "未完了のマーカー: 終了マーカー # が見つかりません",
                    lines[start_index].strip(),
                    "ブロック記法を確認し、終了マーカー # を追加してください",
                )
            
            return (
                error_node(
                    "ブロックの終了マーカー ## が見つかりません", start_index + 1
                ),
                start_index + 1,
            )

        # コンテンツを抽出
        content_lines = lines[start_index + 1 : end_index]
        content = "\n".join(content_lines).strip()
        self.logger.debug(f"Block content: {len(content)} characters")

        # 特殊キーワードの処理
        if "目次" in keywords:
            self.logger.info("Found TOC marker in new format")
            return toc_marker(), end_index + 1

        # ブロックノードを作成
        if len(keywords) == 1:
            self.logger.debug(f"Creating single block with keyword: {keywords[0]}")
            node = self.keyword_parser.create_single_block(
                keywords[0], content, attributes
            )
        else:
            self.logger.debug(f"Creating compound block with keywords: {keywords}")
            node = self.keyword_parser.create_compound_block(
                keywords, content, attributes
            )

        # 見出しIDの追加
        if any(keyword.startswith("見出し") for keyword in keywords):
            self.heading_counter += 1
            if hasattr(node, "add_attribute"):
                node.add_attribute("id", f"heading-{self.heading_counter}")
            self.logger.debug(f"Added heading ID: heading-{self.heading_counter}")

        self.logger.debug(
            f"New format block parsed successfully, next index: {end_index + 1}"
        )
        return node, end_index + 1

    def parse_block_marker(
        self, lines: list[str], start_index: int
    ) -> tuple[Node | None, int]:
        """
        Parse a block marker starting from the given index (new format only)

        Args:
            lines: All lines in the document
            start_index: Index of the opening marker

        Returns:
            tuple: (parsed_node, next_index)
        """
        # 新記法専用パーサーに委譲
        return self.parse_new_format_marker(lines, start_index)

    def _is_simple_image_marker(self, line: str) -> bool:
        """
        Check if a line is a simple image marker (# 画像 # filename.ext)

        Args:
            line: 判定対象の行

        Returns:
            画像マーカーの場合True
        """
        line = line.strip()

        # 新記法での画像マーカーチェック
        parse_result = self.keyword_parser.marker_parser.parse_new_marker_format(line)
        if parse_result is None:
            return False

        keywords, _, _ = parse_result

        # 画像キーワードが含まれているかチェック
        if "画像" not in keywords:
            return False

        # インライン内容があるかチェック（ファイル名）
        inline_content = self.keyword_parser.marker_parser.extract_inline_content(line)
        if not inline_content:
            return False

        # 画像拡張子チェック
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]
        return any(inline_content.lower().endswith(ext) for ext in image_extensions)

    def parse_paragraph(
        self, lines: list[str], start_index: int
    ) -> tuple[Node | None, int]:
        """
        Parse a paragraph starting from the given index（最適化版）

        Args:
            lines: All lines in the document
            start_index: Index where paragraph starts

        Returns:
            tuple: (paragraph_node, next_index)

        Raises:
            ValueError: start_indexが範囲外の場合
        """
        if start_index < 0 or start_index >= len(lines):
            raise ValueError(
                f"start_index {start_index} is out of range [0, {len(lines)})"
            )

        self.logger.debug(f"Parsing paragraph at line {start_index + 1}")

        # 前処理が未実行の場合は実行
        if not self._lines_cache or self._lines_cache != lines:
            self._preprocess_lines(lines)

        paragraph_lines: list[str] = []
        current_index = start_index

        # 高速化された連続行収集
        while current_index < len(lines):
            line = lines[current_index].strip()

            # 空行で停止
            if not line:
                break

            # リスト項目で停止（高速チェック）
            if line.startswith(("- ", "* ", "+ ")) or re.match(r"^\d+\.\s", line):
                break

            # ブロックマーカーで停止（LRUキャッシュ使用）
            if self._is_block_marker_cached(line, self.keyword_parser):
                break

            paragraph_lines.append(line)
            current_index += 1

        if not paragraph_lines:
            return None, start_index

        # 行を改行タグで結合（テキストファイル上の改行を保持）
        content = "<br>
".join(paragraph_lines)
        self.logger.debug(
            f"Paragraph parsed: {len(content)} characters, {len(paragraph_lines)} lines"
        )

        return paragraph(content), current_index

    def is_block_marker_line(self, line: str) -> bool:
        """Check if a line is a block marker (new format only)

        Args:
            line: 判定対象の行

        Returns:
            ブロックマーカーの場合True
        """
        line = line.strip()
        return self._is_block_marker_cached(line, self.keyword_parser)

    def is_opening_marker(self, line: str) -> bool:
        """Check if a line is an opening block marker (new format only)

        Args:
            line: 判定対象の行

        Returns:
            開始マーカーの場合True
        """
        line = line.strip()
        # 新記法: # キーワード # 形式（インライン・ブロック両対応）
        return self.keyword_parser.marker_parser.is_new_marker_format(line)

    def is_closing_marker(self, line: str) -> bool:
        """Check if a line is a closing block marker (new format only)

        Args:
            line: 判定対象の行

        Returns:
            終了マーカーの場合True
        """
        return self.keyword_parser.marker_parser.is_block_end_marker(line)

    def skip_empty_lines(self, lines: list[str], start_index: int) -> int:
        """Skip empty lines and return the next non-empty line index

        Args:
            lines: 全行データ
            start_index: 開始インデックス

        Returns:
            次の非空行のインデックス
        """
        index = start_index
        while index < len(lines) and not lines[index].strip():
            index += 1
        return index

    def find_next_significant_line(
        self, lines: list[str], start_index: int
    ) -> int | None:
        """Find the next line that contains significant content

        Args:
            lines: 全行データ
            start_index: 開始インデックス

        Returns:
            有意な内容を含む次の行のインデックス、見つからない場合はNone
        """
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if line and not self._is_comment_line(line):
                return i
        return None

    def _is_comment_line(self, line: str) -> bool:
        """Check if a line is a comment (starts with #)

        Args:
            line: 判定対象の行

        Returns:
            コメント行の場合True
        """
        return line.strip().startswith("#")
