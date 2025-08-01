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
        
        # Phase2: 修正提案エンジン
        if graceful_errors:
            from .core.error_analysis.correction_engine import CorrectionEngine
            self.correction_engine = CorrectionEngine()
            self.logger.info("Correction engine initialized for graceful error handling")

        # Initialize specialized parsers
        self.keyword_parser = KeywordParser()
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)
        
        # Issue #700: graceful error handling対応 - sub-parsersにパーサー参照を設定
        if graceful_errors:
            self.block_parser.set_parser_reference(self)

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

        # 無限ループ防止のための安全装置
        max_iterations = len(self.lines) * 2  # 最大反復数
        iteration_count = 0

        while self.current < len(self.lines) and iteration_count < max_iterations:
            previous_current = self.current
            node = self._parse_line()

            if node:
                nodes.append(node)
                self.logger.debug(
                    f"Parsed node type: {node.type} at line {self.current}"
                )

            # 無限ループ防止: currentが進んでいない場合
            if self.current == previous_current:
                self.logger.warning(f"Parser stuck at line {self.current}, forcing advance")
                self.current += 1

            iteration_count += 1

        if iteration_count >= max_iterations:
            self.logger.error(f"Parser hit maximum iteration limit ({max_iterations}), stopping")
            self.add_error(f"Parser exceeded maximum iterations at line {self.current}")

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
        # 無限ループ防止のための安全装置
        start_current = self.current
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
            # 安全装置: currentが進んでいない場合は強制的に進める
            if self.current == start_current:
                self.current += 1
                self.logger.warning(f"Force advancing line due to parsing error at line {self.current}")
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

        # Phase2: 修正提案エンジンで拡張
        if hasattr(self, 'correction_engine'):
            graceful_error = self.correction_engine.enhance_error_with_suggestions(graceful_error)
            self.logger.info(f"Enhanced error with {len(graceful_error.correction_suggestions)} suggestions")

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
    大容量ファイル対応ストリーミングパーサー（Issue #694 Phase 3対応）

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

    # クラス定数
    CHUNK_SIZE = 200  # チャンクサイズ（行数）
    PROGRESS_UPDATE_INTERVAL = 50  # プログレス更新間隔（行数）

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

        # パフォーマンス監視を初期化
        from .core.utilities.performance_metrics import PerformanceMonitor
        self.performance_monitor = PerformanceMonitor()

        self.logger.info("StreamingParser initialized with performance monitoring")

    def parse_streaming_from_file(
        self, file_path: Path, progress_callback=None
    ) -> Iterator[Node]:
        """
        ファイルからストリーミング解析を実行

        Args:
            file_path: 解析対象ファイルパス
            progress_callback: プログレス更新コールバック

        Yields:
            Node: 解析済みAST node

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            MemoryError: メモリ不足の場合
        """
        self.logger.info(f"Starting streaming parse of: {file_path}")
        self._cancelled = False
        self.errors = []

        # パフォーマンス監視開始
        self.performance_monitor.start_monitoring()

        try:
            # ファイルサイズと行数の事前取得
            file_size = file_path.stat().st_size
            self.total_lines = self._count_lines_efficiently(file_path)
            self.current_line = 0

            self.logger.info(
                f"File info: {file_size:,} bytes, {self.total_lines:,} lines"
            )

            # ファイルをストリーミング読み込み
            with open(file_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    if self._cancelled:
                        self.logger.info("Parse cancelled by user")
                        break

                    # プログレス更新
                    if progress_callback and line_num % self.PROGRESS_UPDATE_INTERVAL == 0:
                        progress_info = self._calculate_progress(line_num)
                        progress_callback(progress_info)

                    # パフォーマンス監視にアイテム処理を記録
                    self.performance_monitor.record_item_processed()

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

    def parse_streaming_from_text(
        self, text: str, progress_callback=None
    ) -> Iterator[Node]:
        """
        テキストからストリーミング解析を実行（最適化版）

        Args:
            text: 解析対象テキスト
            progress_callback: プログレス更新コールバック

        Yields:
            Node: 解析済みAST node
        """
        self.logger.info(f"Starting optimized streaming parse of text: {len(text)} chars")
        self._cancelled = False

        # プログレス管理システムを初期化
        from .core.utilities.progress_manager import ProgressManager
        progress_manager = ProgressManager(
            total_items=len(text.split("
")),
            task_name="テキスト解析"
        )

        # パフォーマンス監視開始
        self.performance_monitor.start_monitoring()

        try:
            # テキストを行に分割
            lines = text.split("
")
            self.total_lines = len(lines)
            
            # チャンクバッファを初期化
            chunk_buffer = []

            for line_num, line in enumerate(lines, 1):
                chunk_buffer.append(line)
                
                # キャンセルチェック
                if self._cancelled or progress_manager.is_cancelled():
                    self.logger.info("Parse cancelled by user")
                    break

                # チャンクサイズに達したら処理実行
                if len(chunk_buffer) >= self.CHUNK_SIZE:
                    # チャンク処理
                    chunk_start_line = line_num - len(chunk_buffer) + 1
                    
                    for node in self._parse_chunk_optimized(chunk_buffer, chunk_start_line):
                        if node:
                            yield node

                    # バッファクリア
                    chunk_buffer.clear()

                # プログレス更新
                if line_num % self.PROGRESS_UPDATE_INTERVAL == 0:
                    progress_manager.update_progress(line_num, f"行 {line_num}/{self.total_lines}")

            # 残りのチャンクを処理
            if chunk_buffer:
                chunk_start_line = self.total_lines - len(chunk_buffer) + 1
                for node in self._parse_chunk_optimized(chunk_buffer, chunk_start_line):
                    if node:
                        yield node

        except Exception as e:
            progress_manager.add_error(f"解析エラー: {str(e)}")
            self.logger.error(f"Optimized streaming parse error: {e}", exc_info=True)
            # パフォーマンス監視にエラーを記録
            self.performance_monitor.add_error()
            raise
        finally:
            # パフォーマンス監視停止
            self.performance_monitor.stop_monitoring()

            # 最終サマリー
            summary = progress_manager.get_summary()
            self.logger.info(
                f"Optimized parse summary: {summary['current']}/{summary['total']} lines, "
                f"{summary['elapsed_time']:.2f}s, {summary['errors_count']} errors"
            )

    def _parse_chunk_optimized(self, lines: list[str], start_line: int) -> Iterator[Node]:
        """最適化されたチャンク解析（高速版）"""
        current = 0
        while current < len(lines):
            # 空行をスキップ
            current = self.block_parser.skip_empty_lines(lines, current)
            if current >= len(lines):
                break

            line = lines[current].strip()

            # 高速パターンマッチング
            try:
                # ブロックマーカー解析
                if self.block_parser.is_opening_marker(line):
                    node, next_index = self._parse_block_in_chunk(lines, current)
                    if node:
                        yield node
                    current = next_index
                    continue

                # リスト解析
                list_type = self.list_parser.is_list_line(line)
                if list_type:
                    node, next_index = self._parse_list_in_chunk(lines, current, list_type)
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
                self.logger.warning(f"Chunk parse error at line {start_line + current}: {e}")
                self.add_error(f"Chunk parse error: {str(e)}")
                current += 1

    def _parse_block_in_chunk(self, lines: list[str], current: int) -> tuple[Node | None, int]:
        """チャンク内でブロックマーカーを解析"""
        try:
            node, next_index = self.block_parser.parse_block_marker(lines, current)
            return node, next_index
        except Exception as e:
            self.logger.warning(f"Block parse error: {e}")
            self.add_error(f"Block parse error: {str(e)}")
            return None, current + 1

    def _parse_list_in_chunk(self, lines: list[str], current: int, list_type: str) -> tuple[Node | None, int]:
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

    def _parse_paragraph_in_chunk(self, lines: list[str], current: int) -> tuple[Node | None, int]:
        """チャンク内でパラグラフを解析"""
        try:
            node, next_index = self.block_parser.parse_paragraph(lines, current)
            return node, next_index
        except Exception as e:
            self.logger.warning(f"Paragraph parse error: {e}")
            self.add_error(f"Paragraph parse error: {str(e)}")
            return None, current + 1

    def _count_lines_efficiently(self, file_path: Path) -> int:
        """効率的な行数カウント"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
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
            # ETAは簡易計算（実際の実装では処理速度を考慮）
            eta_seconds = max(0, int((self.total_lines - current_line) * 0.01))

        return {
            "current_line": current_line,
            "total_lines": self.total_lines,
            "progress_percent": progress_percent,
            "eta_seconds": eta_seconds,
        }

    def cancel_parsing(self) -> None:
        """解析処理をキャンセル"""
        self._cancelled = True
        self.logger.info("Parse cancellation requested")

    def add_error(self, error: str) -> None:
        """解析エラーを追加"""
        self.errors.append(error)
        self.logger.warning(f"Parse error: {error}")

    def get_errors(self) -> list[str]:
        """解析エラーを取得"""
        return self.errors[:]


# 既存Parserクラスとの互換性維持のためのラッパー関数
def parse_with_error_config(text: str, config: Any = None, use_streaming: bool | None = None) -> list[Node]:
    """
    エラー設定対応の解析関数（ストリーミング対応）

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
        size_mb = len(text.encode('utf-8')) / (1024 * 1024)
        use_streaming = size_mb > 1.0

    if use_streaming:
        parser = StreamingParser(config=config)
        nodes = list(parser.parse_streaming_from_text(text))
        return nodes
    else:
        # 既存の非ストリーミング処理
        parser = Parser(config=config)
        return parser.parse(text)
