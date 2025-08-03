"""Block parsing utilities for Kumihan-Formatter

This module handles the parsing of basic block-level elements.
新記法 #キーワード# 対応 - Issue #665
"""

import bisect
import os
import re
from functools import lru_cache
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

        # Issue #755対応: 正規表現のプリコンパイルとキャッシュ

        # よく使用される正規表現パターンをプリコンパイル
        self._list_pattern = re.compile(r"^[-・*+]\s|^\d+\.\s")
        self._empty_line_pattern = re.compile(r"^\s*$")

        # マーカー判定キャッシュ（LRU）
        self._is_marker_cache = lru_cache(maxsize=10000)(self._is_marker_internal)
        self._is_list_cache = lru_cache(maxsize=10000)(self._is_list_internal)

        self.logger.debug("BlockParser initialized with performance optimizations")

    def _is_marker_internal(self, line: str) -> bool:
        """内部用マーカー判定（キャッシュされる）"""
        return self.keyword_parser.marker_parser.is_new_marker_format(line)

    def _is_list_internal(self, line: str) -> bool:
        """内部用リスト判定（キャッシュされる）"""
        return bool(self._list_pattern.match(line))

    def set_parser_reference(self, parser) -> None:
        """
        Issue #700対応: graceful error handlingのためのパーサー参照を設定

        Args:
            parser: メインパーサーのインスタンス（循環参照回避のため型ヒントなし）
        """
        self.parser_ref = parser
        self.logger.debug("Parser reference set for graceful error handling")

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

        # Issue #755対応: 前処理行数制限を環境変数で設定可能に（デフォルト500,000行）
        max_preprocess_lines = int(
            os.environ.get("KUMIHAN_MAX_PREPROCESS_LINES", "500000")
        )

        # ブロック終了マーカーの位置を事前計算（O(n)で一回のみ）
        try:
            for i, line in enumerate(lines):
                if i >= max_preprocess_lines:  # 安全弁: 大規模ファイル対応
                    self.logger.info(
                        f"Reached preprocessing limit at line {i} (max: {max_preprocess_lines})"
                    )
                    break

                stripped = line.strip()
                if self.keyword_parser.marker_parser.is_block_end_marker(stripped):
                    self._block_end_indices.append(i)
            self.logger.debug(
                f"Preprocessed {min(len(lines), max_preprocess_lines)} lines, "
                f"found {len(self._block_end_indices)} block end markers"
            )
        except Exception as e:
            self.logger.error(f"Error during preprocessing: {e}")
            self._block_end_indices.clear()
            self._lines_cache = []

    def _find_next_block_end(self, start_index: int) -> int | None:
        """
        最適化された次のブロック終了マーカー検索（Issue #713対応改善版）

        Args:
            start_index: 検索開始位置

        Returns:
            次のブロック終了インデックス、見つからない場合はNone

        Notes:
            Issue #713対応: エンドマーカー検出の信頼性向上
            - 前処理キャッシュに依存しない動的検索
            - 複雑記法パターンでの見落としを防止
            - リアルタイム検証機能を追加
        """
        if not self._lines_cache:
            return None

        # Issue #713修正: 前処理キャッシュとリアルタイム検索のハイブリッド方式
        # キャッシュがある場合はそれを使用し、ない場合は動的に検索

        # 方式1: 前処理キャッシュを使用した高速検索（O(log n)）
        if self._block_end_indices:

            if start_index < 0 or start_index >= len(self._lines_cache):
                return None

            # 二分探索でstart_indexより大きい最初のインデックスを検索
            pos = bisect.bisect_right(self._block_end_indices, start_index)

            if pos < len(self._block_end_indices):
                cached_result = self._block_end_indices[pos]

                # Issue #713新機能: キャッシュ結果の検証
                # キャッシュが古い場合やエラーがある場合の安全装置
                if cached_result < len(self._lines_cache):
                    line = self._lines_cache[cached_result].strip()
                    if self.keyword_parser.marker_parser.is_block_end_marker(line):
                        return cached_result

        # 方式2: 動的検索（キャッシュが無効な場合のフォールバック）
        # Issue #713対応: 確実性を重視した線形検索
        for i in range(start_index + 1, len(self._lines_cache)):
            line = self._lines_cache[i].strip()
            if self.keyword_parser.marker_parser.is_block_end_marker(line):
                # Issue #713新機能: リアルタイムキャッシュ更新
                # 見つかったエンドマーカーをキャッシュに追加
                if i not in self._block_end_indices:
                    self._block_end_indices.append(i)
                    self._block_end_indices.sort()  # ソート状態を維持

                return i

        # Issue #713新機能: エンドマーカーが見つからない場合のログ出力
        self.logger.warning(
            f"Block end marker not found after line {start_index + 1}. "
            f"This may indicate an unclosed block marker."
        )

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
        新記法 # キーワード # 形式のマーカーを解析（α-dev: ブロック記法のみ）

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
            if (
                hasattr(self, "parser_ref")
                and self.parser_ref
                and self.parser_ref.graceful_errors
            ):
                self.parser_ref._record_graceful_error(
                    start_index + 1,  # 1-based line number
                    1,  # column
                    "invalid_marker_format",
                    "error",
                    "不正なマーカー記法: 終了マーカー # が見つかりません",
                    opening_line,
                    "正しい記法: # キーワード #\n内容\n##",
                )
            return None, start_index

        keywords, attributes, parse_errors = parse_result

        if parse_errors:
            self.logger.error(f"Parse errors in new format keywords: {parse_errors}")
            return error_node("; ".join(parse_errors), start_index + 1), start_index + 1

        # α-dev: インライン内容の確認 - 単一行記法使用時はエラー
        inline_content = self.keyword_parser.marker_parser.extract_inline_content(
            opening_line
        )

        if inline_content:
            # Issue #751対応: インライン記法をサポート
            return self._parse_inline_format(
                keywords, attributes, inline_content, start_index
            )
        else:
            # ブロック記法: # キーワード # \n 内容 \n ##
            return self._parse_new_format_block(
                lines, start_index, keywords, attributes
            )

    def _parse_inline_format(
        self, keywords: list[str], attributes: dict, content: str, start_index: int
    ) -> tuple[Node | None, int]:
        """
        Issue #751対応: インライン記法を処理

        Args:
            keywords: 抽出されたキーワードリスト
            attributes: 抽出された属性辞書
            content: インライン内容
            start_index: 開始インデックス

        Returns:
            tuple: (parsed_node, next_index)
        """
        if not keywords or not content:
            return None, start_index + 1

        # 最初のキーワードを使用してノードを作成
        primary_keyword = keywords[0]

        # ファクトリ関数をインポート
        from kumihan_formatter.core.ast_nodes import NodeBuilder
        from kumihan_formatter.core.ast_nodes.factories import (
            emphasis,
            heading,
            highlight,
            strong,
        )

        # キーワードに基づいてノードタイプを決定
        if primary_keyword in ["太字", "bold"]:
            node = strong(content)
        elif primary_keyword in ["イタリック", "italic", "斜体"]:
            node = emphasis(content)
        elif primary_keyword in ["見出し1", "h1"]:
            node = heading(1, content)
        elif primary_keyword in ["見出し2", "h2"]:
            node = heading(2, content)
        elif primary_keyword in ["見出し3", "h3"]:
            node = heading(3, content)
        elif primary_keyword in ["見出し4", "h4"]:
            node = heading(4, content)
        elif primary_keyword in ["見出し5", "h5"]:
            node = heading(5, content)
        elif primary_keyword in ["ハイライト", "highlight", "mark"]:
            node = highlight(content)
        elif primary_keyword in ["下線", "underline"]:
            node = NodeBuilder("u").content(content).build()
        elif primary_keyword in ["コード", "code"]:
            node = NodeBuilder("code").content(content).build()
        else:
            # 未知のキーワードの場合、そのまま表示
            node = NodeBuilder("span").content(f"{primary_keyword}: {content}").build()

        # 属性があれば適用
        if attributes:
            for key, value in attributes.items():
                if key == "color":
                    if hasattr(node, "attributes"):
                        node.attributes = node.attributes or {}
                        node.attributes["style"] = f"color: {value};"
                    else:
                        setattr(node, "attributes", {"style": f"color: {value};"})

        self.logger.debug(f"Inline format parsed: {primary_keyword} -> {content}")
        return paragraph(node), start_index + 1

    def _parse_new_format_block(
        self,
        lines: list[str],
        start_index: int,
        keywords: list[str],
        attributes: dict[str, Any],
    ) -> tuple[Node | None, int]:
        """
        新記法のブロック形式を解析（Issue #713対応最適化版）

        Args:
            lines: All lines in the document
            start_index: Index of the opening marker
            keywords: Parsed keywords
            attributes: Parsed attributes

        Returns:
            tuple: (parsed_node, next_index)

        Raises:
            ValueError: パラメータが不正な場合

        Notes:
            Issue #713対応: エンドマーカー検出の信頼性向上とエラー回復機能を強化
        """
        if not keywords:
            raise ValueError("Keywords list cannot be empty")

        self.logger.debug(f"Parsing new format block at line {start_index + 1}")

        # 前処理が未実行または古い場合は実行
        if not self._lines_cache or self._lines_cache != lines:
            self.logger.debug("Preprocessing lines for block parsing")
            self._preprocess_lines(lines)

        # Issue #713修正: より堅牢なエンドマーカー検索
        end_index = self._find_next_block_end(start_index)

        if end_index is None:
            # Issue #713対応: エンドマーカーが見つからない場合の改善されたエラーハンドリング
            self.logger.error(f"Block end marker not found for line {start_index + 1}")

            # Graceful error handling対応
            if (
                hasattr(self, "parser_ref")
                and self.parser_ref
                and self.parser_ref.graceful_errors
            ):
                # Issue #713新機能: より詳細なエラー情報とサジェスチョン
                opening_line = lines[start_index].strip()
                suggested_fix = self._generate_block_fix_suggestions(
                    opening_line, keywords
                )

                self.parser_ref._record_graceful_error(
                    start_index + 1,  # 1-based line number
                    1,  # column
                    "incomplete_block_marker",
                    "error",
                    "未完了のマーカー: 終了マーカー ## が見つかりません",
                    opening_line,
                    suggested_fix,
                )

                # Issue #713新機能: 部分的な回復を試行
                # ファイル終端まで検索して、可能な限りコンテンツを回復
                recovered_content = self._attempt_content_recovery(lines, start_index)
                if recovered_content:
                    self.logger.info(
                        f"Recovered {len(recovered_content)} lines of content"
                    )
                    # 回復したコンテンツでノードを作成
                    if len(keywords) == 1:
                        node = self.keyword_parser.create_single_block(
                            keywords[0], recovered_content, attributes
                        )
                    else:
                        node = self.keyword_parser.create_compound_block(
                            keywords, recovered_content, attributes
                        )
                    return node, len(lines)  # ファイル終端まで処理済み

            # 従来のエラーノード作成
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

        # 新リスト記法の処理
        if "リスト" in keywords:
            self.logger.info("Found list block in new format")
            return self._parse_list_block(lines, start_index, keywords, attributes)

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

    def _generate_block_fix_suggestions(
        self, opening_line: str, keywords: list[str]
    ) -> str:
        """
        Issue #713新機能: ブロックマーカーエラーに対する修正提案を生成

        Args:
            opening_line: 開始マーカー行
            keywords: パースされたキーワード

        Returns:
            str: 修正提案メッセージ
        """
        suggestions = []

        # 基本的な修正提案
        suggestions.append("ブロック記法を確認し、終了マーカー ## を追加してください")

        # キーワード固有の提案
        if len(keywords) == 1:
            suggestions.append(f"例: {opening_line}\\n内容\\n##")
        else:
            suggestions.append(
                f"複合キーワード ({'+'.join(keywords)}) の場合も ## で終了してください"
            )

        # よくある間違いの指摘
        if "color=" in opening_line:
            suggestions.append(
                "color属性がある場合も、必ず ## で終了する必要があります"
            )

        return " | ".join(suggestions)

    def _attempt_content_recovery(self, lines: list[str], start_index: int) -> str:
        """
        Issue #713新機能: エンドマーカーが見つからない場合のコンテンツ回復を試行

        Args:
            lines: 全行データ
            start_index: ブロック開始位置

        Returns:
            str: 回復されたコンテンツ（空の場合もある）
        """
        if start_index + 1 >= len(lines):
            return ""

        recovery_lines = []
        max_recovery_lines = 50  # 回復する最大行数（無制限な回復を防止）

        for i in range(
            start_index + 1, min(len(lines), start_index + 1 + max_recovery_lines)
        ):
            line = lines[i].strip()

            # 明らかに新しいブロックが始まっている場合は停止
            if self.keyword_parser.marker_parser.is_new_marker_format(line):
                break

            # リスト項目の場合も停止
            if line.startswith(("- ", "* ", "+ ")) or re.match(r"^\d+\.\s", line):
                break

            recovery_lines.append(lines[i])  # 元の行（stripしない）

        return "\n".join(recovery_lines).strip()

    def _parse_list_block(
        self,
        lines: list[str],
        start_index: int,
        keywords: list[str],
        attributes: dict[str, Any],
    ) -> tuple[Node | None, int]:
        """
        新リスト記法 # リスト # ブロックの解析

        Args:
            lines: 全行データ
            start_index: 開始インデックス
            keywords: パースされたキーワード
            attributes: パースされた属性

        Returns:
            tuple: (list_node, next_index)
        """
        from kumihan_formatter.core.list_parser_core import ListParserCore

        self.logger.debug(f"Parsing list block at line {start_index + 1}")

        # ListParserCoreを使用して新リスト記法を処理
        list_parser = ListParserCore(self.keyword_parser)
        list_node, next_index = list_parser.parse_list_block(lines, start_index)

        self.logger.debug(f"List block parsed, next index: {next_index}")
        return list_node, next_index

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

            # リスト項目で停止（Issue #755: キャッシュで高速化）
            if self._is_list_cache(line):
                break

            # ブロックマーカーで停止（Issue #755: キャッシュで高速化）
            if self._is_marker_cache(line):
                break

            paragraph_lines.append(line)
            current_index += 1

        if not paragraph_lines:
            return None, start_index

        # 行を改行タグで結合（テキストファイル上の改行を保持）
        content = "<br>\n".join(paragraph_lines)

        # インライン記法を処理
        processed_content = self.keyword_parser._process_inline_keywords(content)

        # 処理結果が配列の場合は、段落ノードに適切に設定
        if isinstance(processed_content, list):
            # 配列の場合は、段落の内容として配列をそのまま渡す
            paragraph_node = paragraph(processed_content)
        else:
            # 単一要素の場合は従来通り
            paragraph_node = paragraph(processed_content)

        self.logger.debug(
            f"Paragraph parsed: {len(content)} characters, {len(paragraph_lines)} lines"
        )

        return paragraph_node, current_index

    def is_block_marker_line(self, line: str) -> bool:
        """Check if a line is a block marker (new format only)

        Args:
            line: 判定対象の行

        Returns:
            ブロックマーカーの場合True
        """
        line = line.strip()
        # Issue #755対応: キャッシュで高速化
        return self._is_marker_cache(
            line
        ) or self.keyword_parser.marker_parser.is_block_end_marker(line)

    def is_opening_marker(self, line: str) -> bool:
        """Check if a line is an opening block marker (new format only)

        Args:
            line: 判定対象の行

        Returns:
            開始マーカーの場合True
        """
        line = line.strip()
        # Issue #755対応: キャッシュを使用して高速化
        return self._is_marker_cache(line)

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
