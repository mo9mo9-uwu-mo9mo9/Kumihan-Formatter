"""Refactored text parser for Kumihan-Formatter

This is the new, modular parser implementation that replaces the monolithic
parser.py file. Each parsing responsibility is now handled by specialized modules.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from .core.common.error_base import GracefulSyntaxError

from .core.ast_nodes import Node
from .core.block_parser import BlockParser
from .core.keyword_parser import KeywordParser
from .core.list_parser import ListParser
from .core.utilities.logger import get_logger


class Parser:
    """
    Kumihan記法のメインパーサー（各特化パーサーを統括）

    設計ドキュメント:
    - 記法仕様: /SPEC.md
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - KeywordParser: キーワード解析を委譲
    - ListParser: リスト解析を委譲（KeywordParser使用）
    - BlockParser: ブロック解析を委譲（KeywordParser使用）
    - Node: 生成するASTノード

    責務:
    - テキスト全体の解析フロー制御
    - 行タイプ判定と適切なパーサーへの委譲
    - AST構造の構築統括
    """

    def __init__(self, config=None, graceful_errors: bool = False) -> None:  # type: ignore
        """Initialize parser with fixed markers

        Args:
            config: Parser configuration (ignored for simplification)
            graceful_errors: Enable graceful error handling (Issue #700)
        """
        # 簡素化: configは無視して固定マーカーのみ使用
        self.config = None
        self.lines = []  # type: ignore
        self.current = 0
        self.errors = []  # type: ignore
        self.logger = get_logger(__name__)

        # Issue #700: graceful error handling
        self.graceful_errors = graceful_errors
        self.graceful_syntax_errors: list["GracefulSyntaxError"] = []

        # Initialize specialized parsers
        self.keyword_parser = KeywordParser()
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)

        self.logger.debug(
            f"Parser initialized with specialized parsers (graceful_errors={graceful_errors})"
        )

    def parse(self, text: str) -> list[Node]:
        """
        Parse text into AST nodes

        Args:
            text: Input text to parse

        Returns:
            list[Node]: Parsed AST nodes
        """
        self.lines = text.split("\n")
        self.current = 0
        self.errors = []
        nodes = []

        self.logger.info(f"Starting parse of {len(self.lines)} lines")
        self.logger.debug(f"Input text length: {len(text)} characters")

        while self.current < len(self.lines):
            node = self._parse_line()

            if node:
                nodes.append(node)
                self.logger.debug(
                    f"Parsed node type: {node.type} at line {self.current}"
                )

        self.logger.info(
            f"Parse complete: {len(nodes)} nodes created, {len(self.errors)} errors"
        )
        return nodes

    def _parse_line(self) -> Node | None:
        """Parse a single line or block starting from current position"""
        if self.current >= len(self.lines):
            return None

        # Skip empty lines
        self.current = self.block_parser.skip_empty_lines(self.lines, self.current)

        if self.current >= len(self.lines):
            return None

        line = self.lines[self.current].strip()
        self.logger.debug(
            f"Processing line {self.current}: {line[:50]}..."
            if len(line) > 50
            else f"Processing line {self.current}: {line}"
        )

        # Issue #700: graceful error handlingモードでのエラー処理
        if self.graceful_errors:
            return self._parse_line_with_graceful_errors()

        # 従来のエラー処理（エラー時に例外をスロー）
        return self._parse_line_traditional()

    def _parse_line_traditional(self) -> Node | None:
        """従来のパース処理（エラー時に例外をスロー）"""
        line = self.lines[self.current].strip()

        # Parse block markers first (to handle new notation #keyword#)
        if self.block_parser.is_opening_marker(line):
            self.logger.debug(f"Found block marker at line {self.current}")
            node, next_index = self.block_parser.parse_block_marker(
                self.lines, self.current
            )
            self.current = next_index
            return node

        # Skip comment lines (lines starting with # but not new notation)
        # This check is now after block marker check to avoid conflict
        if line.startswith("#") and not self.block_parser.is_opening_marker(line):
            self.current += 1
            return None

        # Parse lists
        list_type = self.list_parser.is_list_line(line)
        if list_type:
            self.logger.debug(f"Found {list_type} list at line {self.current}")
            if list_type == "ul":
                node, next_index = self.list_parser.parse_unordered_list(
                    self.lines, self.current
                )
            else:  # 'ol'
                node, next_index = self.list_parser.parse_ordered_list(
                    self.lines, self.current
                )

            self.current = next_index
            return node

        # Parse paragraph
        node, next_index = self.block_parser.parse_paragraph(self.lines, self.current)
        self.current = next_index
        return node

    def _parse_line_with_graceful_errors(self) -> Node | None:
        """graceful error handling対応のパース処理"""
        line = self.lines[self.current].strip()

        try:
            # Parse block markers first (to handle new notation #keyword#)
            if self.block_parser.is_opening_marker(line):
                self.logger.debug(f"Found block marker at line {self.current}")
                node, next_index = self.block_parser.parse_block_marker(
                    self.lines, self.current
                )
                self.current = next_index
                return node

        except Exception as e:
            # ブロックマーカーエラーを記録して継続
            self._record_graceful_error(
                self.current + 1,  # 1-based line number
                1,  # column
                "block_marker_error",
                "error",
                f"ブロックマーカー解析エラー: {str(e)}",
                line,
                "マーカーの記法を確認してください",
            )
            self.current += 1
            return self._create_error_node(line, str(e))

        try:
            # Skip comment lines (lines starting with # but not new notation)
            if line.startswith("#") and not self.block_parser.is_opening_marker(line):
                self.current += 1
                return None

            # Parse lists
            list_type = self.list_parser.is_list_line(line)
            if list_type:
                self.logger.debug(f"Found {list_type} list at line {self.current}")
                if list_type == "ul":
                    node, next_index = self.list_parser.parse_unordered_list(
                        self.lines, self.current
                    )
                else:  # 'ol'
                    node, next_index = self.list_parser.parse_ordered_list(
                        self.lines, self.current
                    )

                self.current = next_index
                return node

        except Exception as e:
            # リスト解析エラーを記録して継続
            self._record_graceful_error(
                self.current + 1,
                1,
                "list_parse_error",
                "error",
                f"リスト解析エラー: {str(e)}",
                line,
                "リスト記法を確認してください",
            )
            self.current += 1
            return self._create_error_node(line, str(e))

        try:
            # Parse paragraph
            node, next_index = self.block_parser.parse_paragraph(
                self.lines, self.current
            )
            self.current = next_index
            return node

        except Exception as e:
            # パラグラフ解析エラーを記録して継続
            self._record_graceful_error(
                self.current + 1,
                1,
                "paragraph_parse_error",
                "warning",  # パラグラフエラーは警告レベル
                f"パラグラフ解析エラー: {str(e)}",
                line,
                "テキスト内容を確認してください",
            )
            self.current += 1
            return self._create_error_node(line, str(e))

    def get_errors(self) -> list[str]:
        """Get parsing errors"""
        return self.errors

    def add_error(self, error: str) -> None:
        """Add a parsing error"""
        self.errors.append(error)
        self.logger.warning(f"Parse error: {error}")

    def _record_graceful_error(
        self,
        line_number: int,
        column: int,
        error_type: str,
        severity: str,
        message: str,
        context: str,
        suggestion: str = "",
    ) -> None:
        """Issue #700: graceful error handlingでエラーを記録"""
        from .core.common.error_base import GracefulSyntaxError

        graceful_error = GracefulSyntaxError(
            line_number=line_number,
            column=column,
            error_type=error_type,
            severity=severity,
            message=message,
            context=context,
            suggestion=suggestion,
            file_path="",  # ファイルパスは後で設定
        )

        self.graceful_syntax_errors.append(graceful_error)
        self.logger.info(f"Graceful error recorded: {message} at line {line_number}")

    def _create_error_node(self, line: str, error_message: str) -> Node:
        """エラー発生箇所にエラー情報を含むノードを作成"""
        from .core.ast_nodes.factories import error_node

        error_content = f"❌ 解析エラー: {error_message}"
        return error_node(
            error_content, {"original_line": line, "error_type": "parse_error"}
        )

    def get_graceful_errors(self) -> list["GracefulSyntaxError"]:
        """Issue #700: graceful error handlingで収集したエラーを取得"""
        return self.graceful_syntax_errors

    def has_graceful_errors(self) -> bool:
        """graceful error handlingでエラーが記録されているかチェック"""
        return len(self.graceful_syntax_errors) > 0

    def get_graceful_error_summary(self) -> dict:
        """graceful error handlingのエラーサマリーを取得"""
        errors_by_severity = {"error": 0, "warning": 0, "info": 0}

        for error in self.graceful_syntax_errors:
            if error.severity in errors_by_severity:
                errors_by_severity[error.severity] += 1

        return {
            "total_errors": len(self.graceful_syntax_errors),
            "by_severity": errors_by_severity,
            "has_critical_errors": errors_by_severity["error"] > 0,
        }

    def get_statistics(self) -> dict:  # type: ignore
        """Get parsing statistics"""
        return {
            "total_lines": len(self.lines),
            "errors_count": len(self.errors),
            "heading_count": self.block_parser.heading_counter,
        }


def parse(text: str, config=None) -> list[Node]:  # type: ignore
    """
    Main parsing function (compatibility with existing API)

    Args:
        text: Input text to parse
        config: Optional configuration

    Returns:
        list[Node]: Parsed AST nodes
    """
    parser = Parser(config)
    return parser.parse(text)


class StreamingParser:
    """
    大容量ファイル対応のストリーミングパーサー

    特徴:
    - ジェネレーターベース：メモリ使用量を最小化
    - チャンク処理：ファイルを分割して段階的処理
    - プログレス追跡：リアルタイムの進捗表示とETA算出
    - キャンセル対応：処理中断機能

    パフォーマンス目標:
    - 1000行ファイル: 10秒以内
    - メモリ使用量: 一定（ファイルサイズに依存しない）
    - 10MBファイル対応
    """

    CHUNK_SIZE = 50  # 一度に処理する行数
    PROGRESS_UPDATE_INTERVAL = 50  # プログレス更新間隔

    def __init__(self, config=None) -> None:
        self.config = config
        self.logger = get_logger(__name__)
        self.errors = []  # type: ignore
        self.current_line = 0
        self.total_lines = 0
        self._cancelled = False

        # Initialize specialized parsers
        self.keyword_parser = KeywordParser()
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)

        # Initialize advanced error recovery system
        from .core.utilities.error_recovery import AdvancedErrorRecoverySystem

        self.error_recovery = AdvancedErrorRecoverySystem()

        # Initialize performance monitoring system
        from .core.utilities.performance_metrics import PerformanceMonitor

        self.performance_monitor = PerformanceMonitor(
            monitoring_interval=0.5,  # 0.5秒間隔で監視
            history_size=500,  # 500サンプルまで保持
        )

        self.logger.debug(
            "StreamingParser initialized for large file processing with error recovery and performance monitoring"
        )

    def parse_streaming(
        self, file_path: Path, progress_callback=None
    ) -> Iterator[Node]:
        """
        ファイルをストリーミング形式で解析

        Args:
            file_path: 解析対象ファイルパス
            progress_callback: プログレス通知用コールバック関数

        Yields:
            Node: 解析済みAST nodes（リアルタイム生成）

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            MemoryError: メモリ不足の場合
        """
        self.logger.info(f"Starting streaming parse of: {file_path}")
        self._cancelled = False
        self.errors = []

        try:
            # ファイルサイズと行数の事前取得
            file_size = file_path.stat().st_size
            self.total_lines = self._count_lines_efficiently(file_path)
            self.current_line = 0

            self.logger.info(
                f"File analysis: {file_size} bytes, {self.total_lines} lines"
            )

            # パフォーマンス監視開始
            self.performance_monitor.start_monitoring(
                self.total_lines, f"ファイル解析: {file_path.name}"
            )

            # パフォーマンスアラートコールバック設定
            def performance_alert_callback(alert_type: str, alert_data: dict):
                self.logger.warning(
                    f"Performance alert [{alert_type}]: {alert_data['message']}"
                )

            self.performance_monitor.add_alert_callback(performance_alert_callback)

            # チャンク単位でファイルを処理
            with open(file_path, "r", encoding="utf-8", buffering=8192) as file:
                chunk_buffer = []

                for line_num, line in enumerate(file, 1):
                    if self._cancelled:
                        self.logger.info("Parse cancelled by user")
                        break

                    chunk_buffer.append(line.rstrip("\n"))
                    self.current_line = line_num

                    # チャンクサイズに達したら処理実行
                    if len(chunk_buffer) >= self.CHUNK_SIZE:
                        yield from self._process_chunk(
                            chunk_buffer, line_num - len(chunk_buffer) + 1
                        )
                        chunk_buffer.clear()

                        # プログレス更新
                        if line_num % self.PROGRESS_UPDATE_INTERVAL == 0:
                            # パフォーマンス統計更新
                            self.performance_monitor.update_progress(
                                line_num,
                                f"チャンク処理中 ({line_num}/{self.total_lines}行)",
                            )

                            if progress_callback:
                                progress_info = self._calculate_progress(line_num)
                                progress_callback(progress_info)

                # 残りのチャンクを処理
                if chunk_buffer and not self._cancelled:
                    yield from self._process_chunk(
                        chunk_buffer, self.current_line - len(chunk_buffer) + 1
                    )

                    # 最終プログレス更新
                    if progress_callback:
                        final_progress = self._calculate_progress(self.total_lines)
                        progress_callback(final_progress)

        except Exception as e:
            self.logger.error(f"Streaming parse error: {e}", exc_info=True)
            self.add_error(f"Streaming parse failed: {str(e)}")
            # パフォーマンス監視にエラーを記録
            self.performance_monitor.add_error()
            raise
        finally:
            # パフォーマンス監視停止
            self.performance_monitor.stop_monitoring()

            # パフォーマンスレポート生成
            performance_report = self.performance_monitor.generate_performance_report()
            self.logger.info(f"Performance Report:\n{performance_report}")

        self.logger.info(
            f"Streaming parse complete: {self.current_line} lines processed, {len(self.errors)} errors"
        )

    def parse_streaming_from_text(
        self, text: str, progress_callback=None
    ) -> Iterator[Node]:
        """
        テキストをストリーミング形式で解析（真のメモリ効率版）

        Args:
            text: 解析対象テキスト
            progress_callback: プログレス通知用コールバック関数

        Yields:
            Node: 解析済みAST nodes
        """
        from io import StringIO

        from .core.utilities.progress_manager import ProgressManager

        self.logger.info(
            f"Starting optimized streaming parse of text: {len(text)} characters"
        )
        self._cancelled = False
        self.errors = []

        # プログレス管理システム初期化
        progress_manager = ProgressManager("最適化テキスト解析")

        # テキストサイズから行数を推定（メモリ効率のため）
        estimated_lines = text.count("\n") + 1
        self.total_lines = estimated_lines
        self.current_line = 0

        # パフォーマンス監視開始
        self.performance_monitor.start_monitoring(
            estimated_lines, "テキスト解析（ストリーミング）"
        )

        # パフォーマンスアラートコールバック設定
        def performance_alert_callback(alert_type: str, alert_data: dict):
            self.logger.warning(
                f"Performance alert [{alert_type}]: {alert_data['message']}"
            )

        self.performance_monitor.add_alert_callback(performance_alert_callback)

        # プログレス追跡開始
        progress_manager.start(estimated_lines, "最適化ストリーミング解析")

        # プログレス更新コールバック設定
        if progress_callback:

            def enhanced_progress_callback(state):
                progress_info = {
                    "current_line": state.current,
                    "total_lines": state.total,
                    "progress_percent": state.progress_percent,
                    "eta_seconds": state.eta_seconds,
                    "errors_count": len(self.errors),
                    "processing_rate": state.processing_rate,
                    "stage": state.stage,
                    "substage": state.substage,
                }
                progress_callback(progress_info)

            progress_manager.set_progress_callback(enhanced_progress_callback)

        # キャンセル機能設定
        progress_manager.set_cancellation_callback(self.cancel_parsing)

        chunk_buffer = []

        try:
            # StringIOを使用してメモリ効率的な行単位読み込み
            text_stream = StringIO(text)

            for line_num, line in enumerate(text_stream, 1):
                # キャンセルチェック
                if self._cancelled or progress_manager.is_cancelled():
                    self.logger.info("Parse cancelled by user")
                    break

                # 行末の改行文字を除去
                line = line.rstrip("\n\r")
                chunk_buffer.append(line)
                self.current_line = line_num

                # チャンクサイズに達したら処理実行
                if len(chunk_buffer) >= self.CHUNK_SIZE:
                    # チャンク処理
                    chunk_start_line = line_num - len(chunk_buffer) + 1
                    progress_manager.update(
                        line_num, f"チャンク{chunk_start_line}-{line_num}行処理中"
                    )

                    # メモリ効率的なチャンク処理
                    for node in self._process_chunk_optimized(
                        chunk_buffer, chunk_start_line
                    ):
                        yield node

                    # チャンクバッファを即座にクリア（メモリ解放）
                    chunk_buffer.clear()

                # プログレス更新（定期的）
                if line_num % self.PROGRESS_UPDATE_INTERVAL == 0:
                    # パフォーマンス統計更新
                    self.performance_monitor.update_progress(
                        line_num, f"テキスト解析中 ({line_num}/{estimated_lines}行)"
                    )

                    if not progress_manager.update(
                        line_num, f"{line_num}/{estimated_lines}行解析完了"
                    ):
                        break  # キャンセルされた場合

            # 残りのチャンクを処理
            if chunk_buffer and not (
                self._cancelled or progress_manager.is_cancelled()
            ):
                progress_manager.set_stage("最終処理", "残りチャンクを処理中")
                chunk_start_line = self.current_line - len(chunk_buffer) + 1

                for node in self._process_chunk_optimized(
                    chunk_buffer, chunk_start_line
                ):
                    yield node

                # 最終クリーンアップ
                chunk_buffer.clear()

            # 完了処理
            if not (self._cancelled or progress_manager.is_cancelled()):
                progress_manager.finish("解析完了")

        except Exception as e:
            progress_manager.add_error(f"解析エラー: {str(e)}")
            self.logger.error(f"Optimized streaming parse error: {e}", exc_info=True)
            # パフォーマンス監視にエラーを記録
            self.performance_monitor.add_error()
            raise
        finally:
            # パフォーマンス監視停止
            self.performance_monitor.stop_monitoring()

            # パフォーマンスレポート生成
            performance_report = self.performance_monitor.generate_performance_report()
            self.logger.info(f"Performance Report:\n{performance_report}")

            # メモリ解放の確実な実行
            chunk_buffer.clear()
            text_stream.close()

            # 最終サマリー
            summary = progress_manager.get_summary()
            self.logger.info(
                f"Optimized parse summary: {summary['current']}/{summary['total']} lines, "
                f"{summary['elapsed_time']:.2f}s, {summary['errors_count']} errors"
            )

    def _process_chunk(self, lines: list[str], start_line_num: int) -> Iterator[Node]:
        """
        チャンク（行のまとまり）を処理してノードを生成

        Args:
            lines: 処理対象の行リスト
            start_line_num: チャンク開始行番号

        Yields:
            Node: 解析済みノード
        """
        self.logger.debug(
            f"Processing chunk: lines {start_line_num}-{start_line_num + len(lines) - 1}"
        )

        current = 0
        while current < len(lines):
            # 空行をスキップ
            current = self.block_parser.skip_empty_lines(lines, current)
            if current >= len(lines):
                break

            line = lines[current].strip()

            try:
                # ブロックマーカーの解析
                if self.block_parser.is_opening_marker(line):
                    node, next_index = self._parse_block_in_chunk(
                        lines, current, start_line_num
                    )
                    if node:
                        yield node
                    current = next_index
                    continue

                # コメント行をスキップ
                if line.startswith("#") and not self.block_parser.is_opening_marker(
                    line
                ):
                    current += 1
                    continue

                # リスト解析
                list_type = self.list_parser.is_list_line(line)
                if list_type:
                    node, next_index = self._parse_list_in_chunk(
                        lines, current, list_type
                    )
                    if node:
                        yield node
                    current = next_index
                    continue

                # パラグラフ解析
                node, next_index = self._parse_paragraph_in_chunk(lines, current)
                if node:
                    yield node
                current = next_index

            except Exception as e:
                self.logger.warning(
                    f"Error processing line {start_line_num + current}: {e}"
                )
                self.add_error(f"Line {start_line_num + current}: {str(e)}")
                # パフォーマンス監視に警告記録
                if hasattr(self, "performance_monitor"):
                    self.performance_monitor.add_warning()
                current += 1  # エラー時は次の行へ

    def _parse_block_in_chunk(
        self, lines: list[str], current: int, start_line_num: int
    ) -> tuple[Node | None, int]:
        """チャンク内でブロックマーカーを解析"""
        try:
            node, next_index = self.block_parser.parse_block_marker(lines, current)
            return node, next_index
        except Exception as e:
            self.logger.warning(
                f"Block parse error at line {start_line_num + current}: {e}"
            )
            self.add_error(f"Block parse error: {str(e)}")
            return None, current + 1

    def _parse_list_in_chunk(
        self, lines: list[str], current: int, list_type: str
    ) -> tuple[Node | None, int]:
        """チャンク内でリストを解析"""
        try:
            if list_type == "ul":
                node, next_index = self.list_parser.parse_unordered_list(lines, current)
            else:  # 'ol'
                node, next_index = self.list_parser.parse_ordered_list(lines, current)
            return node, next_index
        except Exception as e:
            self.logger.warning(f"List parse error: {e}")
            self.add_error(f"List parse error: {str(e)}")
            return None, current + 1

    def _parse_paragraph_in_chunk(
        self, lines: list[str], current: int
    ) -> tuple[Node | None, int]:
        """チャンク内でパラグラフを解析"""
        try:
            node, next_index = self.block_parser.parse_paragraph(lines, current)
            return node, next_index
        except Exception as e:
            self.logger.warning(f"Paragraph parse error: {e}")
            self.add_error(f"Paragraph parse error: {str(e)}")
            return None, current + 1

    def _process_chunk_optimized(
        self, lines: list[str], start_line_num: int
    ) -> Iterator[Node]:
        """
        メモリ効率最適化されたチャンク処理

        Args:
            lines: 処理対象の行リスト
            start_line_num: チャンク開始行番号

        Yields:
            Node: 解析済みノード
        """
        self.logger.debug(
            f"Processing optimized chunk: lines {start_line_num}-{start_line_num + len(lines) - 1}"
        )

        current = 0
        processed_nodes = 0

        while current < len(lines):
            # 空行をスキップ
            current = self.block_parser.skip_empty_lines(lines, current)
            if current >= len(lines):
                break

            line = lines[current].strip()

            try:
                # ブロックマーカーの解析
                if self.block_parser.is_opening_marker(line):
                    node, next_index = self._parse_block_in_chunk_safe(
                        lines, current, start_line_num
                    )
                    if node:
                        yield node
                        processed_nodes += 1
                    current = next_index
                    continue

                # コメント行をスキップ
                if line.startswith("#") and not self.block_parser.is_opening_marker(
                    line
                ):
                    current += 1
                    continue

                # リスト解析
                list_type = self.list_parser.is_list_line(line)
                if list_type:
                    node, next_index = self._parse_list_in_chunk_safe(
                        lines, current, list_type
                    )
                    if node:
                        yield node
                        processed_nodes += 1
                    current = next_index
                    continue

                # パラグラフ解析
                node, next_index = self._parse_paragraph_in_chunk_safe(lines, current)
                if node:
                    yield node
                    processed_nodes += 1
                current = next_index

            except Exception as e:
                self.logger.warning(
                    f"Error processing line {start_line_num + current}: {e}"
                )
                self.add_error(f"Line {start_line_num + current}: {str(e)}")
                # パフォーマンス監視に警告記録
                if hasattr(self, "performance_monitor"):
                    self.performance_monitor.add_warning()
                current += 1  # エラー時は次の行へ

        self.logger.debug(
            f"Optimized chunk completed: {processed_nodes} nodes processed"
        )

    def _parse_block_in_chunk_safe(
        self, lines: list[str], current: int, start_line_num: int
    ) -> tuple[Node | None, int]:
        """高度なエラー回復機能付きブロック解析"""
        try:
            node, next_index = self.block_parser.parse_block_marker(lines, current)
            return node, next_index
        except Exception as e:
            # エラーコンテキストを作成
            from .core.utilities.error_recovery import ErrorType

            context_info = {
                "line_number": start_line_num + current,
                "content_snippet": lines[current] if current < len(lines) else "",
                "parsing_context": "block_marker",
            }

            error_context = self.error_recovery.classify_error(e, context_info)

            # エラー種別に応じた処理
            if error_context.error_type == ErrorType.BLOCK_STRUCTURE_ERROR:
                # 高度な回復を試行
                recovery_result = self.error_recovery.recover_from_error(
                    error_context, lines
                )

                if recovery_result.success:
                    self.logger.info(
                        f"Block error recovery: {recovery_result.recovery_message}"
                    )

                    # 警告をエラーリストに追加
                    for warning in recovery_result.warnings:
                        self.add_error(f"Warning: {warning}")

                    return None, recovery_result.skip_to_line

            # フォールバック: 従来の回復処理
            recovery_index = self._find_block_end_marker(lines, current)
            if recovery_index > current:
                self.logger.info(
                    f"Block error recovered at line {start_line_num + recovery_index}"
                )
                return None, recovery_index

            self.logger.warning(
                f"Block parse error at line {start_line_num + current}: {e}"
            )
            self.add_error(f"Block parse error: {str(e)}")
            return None, current + 1

    def _parse_list_in_chunk_safe(
        self, lines: list[str], current: int, list_type: str
    ) -> tuple[Node | None, int]:
        """安全なリスト解析（エラー回復機能付き）"""
        try:
            if list_type == "ul":
                node, next_index = self.list_parser.parse_unordered_list(lines, current)
            else:  # 'ol'
                node, next_index = self.list_parser.parse_ordered_list(lines, current)
            return node, next_index
        except Exception as e:
            # エラー回復: リスト終了を検出
            recovery_index = self._find_list_end(lines, current, list_type)
            if recovery_index > current:
                self.logger.info(f"List error recovered at line {recovery_index}")
                return None, recovery_index

            self.logger.warning(f"List parse error: {e}")
            self.add_error(f"List parse error: {str(e)}")
            return None, current + 1

    def _parse_paragraph_in_chunk_safe(
        self, lines: list[str], current: int
    ) -> tuple[Node | None, int]:
        """安全なパラグラフ解析（エラー回復機能付き）"""
        try:
            node, next_index = self.block_parser.parse_paragraph(lines, current)
            return node, next_index
        except Exception as e:
            # エラー回復: 次の空行まで進む
            recovery_index = self._find_next_empty_line(lines, current)
            if recovery_index > current:
                self.logger.info(f"Paragraph error recovered at line {recovery_index}")
                return None, recovery_index

            self.logger.warning(f"Paragraph parse error: {e}")
            self.add_error(f"Paragraph parse error: {str(e)}")
            return None, current + 1

    def _find_block_end_marker(self, lines: list[str], start: int) -> int:
        """ブロック終了マーカーを検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if line == "##" or (
                line.startswith("#") and self.block_parser.is_opening_marker(line)
            ):
                return i
        return start + 1  # 見つからない場合は次の行

    def _find_list_end(self, lines: list[str], start: int, list_type: str) -> int:
        """リスト終了位置を検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if not line:  # 空行でリスト終了
                return i
            if not self.list_parser.is_list_line(line):  # リスト以外の行
                return i
        return start + 1

    def _find_next_empty_line(self, lines: list[str], start: int) -> int:
        """次の空行を検索"""
        for i in range(start + 1, len(lines)):
            if not lines[i].strip():
                return i
        return start + 1

    def _count_lines_efficiently(self, file_path: Path) -> int:
        """効率的な行数カウント"""
        try:
            with open(file_path, "rb") as file:
                line_count = sum(1 for _ in file)
            return line_count
        except Exception:
            # フォールバック: 概算値を返す
            file_size = file_path.stat().st_size
            # 平均行長を60文字と仮定
            return max(1, int(file_size / 60))

    def _calculate_progress(self, current_line: int) -> dict:
        """プログレス情報を計算"""
        if self.total_lines == 0:
            progress_percent = 100.0
            eta_seconds = 0
        else:
            progress_percent = min(100.0, (current_line / self.total_lines) * 100)

            # ETA算出（簡易版）
            if current_line > 0 and progress_percent > 0:
                # 現在の処理速度から残り時間を推定
                elapsed_estimate = (
                    current_line / max(1, self.PROGRESS_UPDATE_INTERVAL) * 0.1
                )  # 概算
                remaining_percent = 100.0 - progress_percent
                eta_seconds = (elapsed_estimate * remaining_percent) / max(
                    0.1, progress_percent
                )
            else:
                eta_seconds = 0

        return {
            "current_line": current_line,
            "total_lines": self.total_lines,
            "progress_percent": progress_percent,
            "eta_seconds": int(eta_seconds),
            "errors_count": len(self.errors),
        }

    def cancel_parsing(self) -> None:
        """解析処理をキャンセル"""
        self._cancelled = True
        self.logger.info("Parse cancellation requested")

    def get_errors(self) -> list[str]:
        """解析エラーを取得"""
        return self.errors

    def add_error(self, error: str) -> None:
        """解析エラーを追加"""
        self.errors.append(error)
        self.logger.warning(f"Parse error: {error}")


# 既存Parserクラスとの互換性維持のためのラッパー関数
def parse_with_streaming(
    text: str, config=None, use_streaming: bool = None
) -> list[Node]:
    """
    ストリーミングパーサーを使用した解析（互換性維持）

    Args:
        text: 解析対象テキスト
        config: 設定オブジェクト（現在未使用）
        use_streaming: ストリーミング使用フラグ（Noneの場合は自動判定）

    Returns:
        list[Node]: 解析済みAST nodes
    """
    # ストリーミング使用判定
    if use_streaming is None:
        # テキストサイズが大きい場合はストリーミングを使用
        text_size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        use_streaming = text_size_mb > 1.0 or len(text.split("\n")) > 200

    if use_streaming:
        parser = StreamingParser(config=config)
        nodes = list(parser.parse_streaming_from_text(text))
        return nodes
    else:
        # 既存の非ストリーミング処理
        parser = Parser(config=config)
        return parser.parse(text)
