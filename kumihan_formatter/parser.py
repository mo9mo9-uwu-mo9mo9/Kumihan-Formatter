"""Base parser module - Refactored and modularized parser for Kumihan-Formatter

This is the main parser implementation that integrates specialized handlers.
Issue #813: Split monolithic parser.py into modular components.
"""

import time
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional

if TYPE_CHECKING:
    from .core.common.error_base import GracefulSyntaxError

# Import specialized handlers
from .block_handler import BlockHandler
from .core.ast_nodes import Node, error_node
from .core.keyword_parser import KeywordParser
from .core.list_parser import ListParser
from .core.parsing.block import BlockParser
from .core.utilities.logger import get_logger
from .inline_handler import InlineHandler
from .parallel_processor import ParallelProcessorHandler
from .streaming_parser import StreamingParser


# Issue #759対応: カスタム例外クラス定義
class ParallelProcessingError(Exception):
    """並列処理固有のエラー"""

    pass


class ChunkProcessingError(Exception):
    """チャンク処理でのエラー"""

    pass


class MemoryMonitoringError(Exception):
    """メモリ監視でのエラー"""

    pass


# Issue #759対応: 並列処理設定クラス
class ParallelProcessingConfig:
    """並列処理の設定管理"""

    def __init__(self) -> None:
        # 並列処理しきい値設定
        self.parallel_threshold_lines = 10000  # 10K行以上で並列化
        self.parallel_threshold_size = 10 * 1024 * 1024  # 10MB以上で並列化

        # チャンク設定
        self.min_chunk_size = 50
        self.max_chunk_size = 2000
        self.target_chunks_per_core = 2  # CPUコアあたりのチャンク数

        # メモリ監視設定
        self.memory_warning_threshold_mb = 150
        self.memory_critical_threshold_mb = 250
        self.memory_check_interval = 10  # チャンク数

        # タイムアウト設定
        self.processing_timeout_seconds = 300  # 5分
        self.chunk_timeout_seconds = 30  # 30秒

        # パフォーマンス設定
        self.enable_progress_callbacks = True
        self.progress_update_interval = 100  # 行数
        self.enable_memory_monitoring = True
        self.enable_gc_optimization = True

    @classmethod
    def from_environment(cls) -> "ParallelProcessingConfig":
        """環境変数から設定を読み込み"""
        import os

        config = cls()

        # 環境変数からの設定上書き
        if threshold_lines := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_LINES"):
            try:
                config.parallel_threshold_lines = int(threshold_lines)
            except ValueError:
                pass

        if threshold_size := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_SIZE"):
            try:
                config.parallel_threshold_size = int(threshold_size)
            except ValueError:
                pass

        if memory_limit := os.getenv("KUMIHAN_MEMORY_LIMIT_MB"):
            try:
                memory_limit_int = int(memory_limit)
                config.memory_critical_threshold_mb = memory_limit_int
                config.memory_warning_threshold_mb = int(memory_limit_int * 0.6)
            except ValueError:
                pass

        if timeout := os.getenv("KUMIHAN_PROCESSING_TIMEOUT"):
            try:
                config.processing_timeout_seconds = int(timeout)
            except ValueError:
                pass

        return config

    def validate(self) -> bool:
        """設定値の検証"""
        try:
            assert self.parallel_threshold_lines > 0
            assert self.parallel_threshold_size > 0
            assert self.min_chunk_size > 0
            assert self.max_chunk_size > self.min_chunk_size
            assert self.memory_warning_threshold_mb > 0
            assert self.memory_critical_threshold_mb > self.memory_warning_threshold_mb
            assert self.processing_timeout_seconds > 0
            return True
        except AssertionError:
            return False


class Parser:
    """
    Kumihan記法のメインパーサー（モジュラー設計版）

    Issue #813対応: 巨大なparser.pyを5つのモジュールに分割
    - base_parser.py: メイン統合クラス（このファイル）
    - block_handler.py: ブロック記法処理
    - inline_handler.py: インライン記法処理
    - parallel_processor.py: 並列処理ロジック
    - streaming_parser.py: ストリーミングパーサー

    設計原則:
    - 単一責任原則: 各ハンドラーは特定の責任を持つ
    - 依存性注入: ハンドラーにParserインスタンスを注入
    - 後方互換性: 既存APIを完全に維持
    """

    def __init__(
        self,
        config: Any = None,
        graceful_errors: bool = False,
        parallel_config: ParallelProcessingConfig | None = None,
    ) -> None:
        """Initialize parser with specialized handlers

        Args:
            config: Parser configuration (ignored for simplification)
            graceful_errors: Enable graceful error handling (Issue #700)
            parallel_config: 並列処理設定（Issue #759コードレビュー対応）
        """
        # 基本設定
        self.config = None
        self.lines: list[str] = []
        self.current = 0
        self.errors: list[Any] = []
        self.logger = get_logger(__name__)

        # Issue #700: graceful error handling
        self.graceful_errors = graceful_errors
        self.graceful_syntax_errors: list["GracefulSyntaxError"] = []

        # Issue #759: 並列処理設定の外部化対応
        self.parallel_config = (
            parallel_config or ParallelProcessingConfig.from_environment()
        )

        # 設定値検証
        if not self.parallel_config.validate():
            self.logger.warning(
                "Invalid parallel processing configuration, using defaults"
            )
            self.parallel_config = ParallelProcessingConfig()

        # 修正提案エンジン
        if graceful_errors:
            from .core.error_handling.analysis.correction_engine import CorrectionEngine

            self.correction_engine = CorrectionEngine()
            self.logger.info(
                "Correction engine initialized for graceful error handling"
            )

        # Initialize specialized parsers
        self.keyword_parser = KeywordParser()
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)

        # Issue #700: graceful error handling対応
        if graceful_errors:
            self.block_parser.set_parser_reference(self)

        # Issue #759: 並列処理統合
        from .core.utilities.parallel_processor import ParallelChunkProcessor

        self.parallel_processor = ParallelChunkProcessor()

        # 並列処理のしきい値設定
        self.parallel_threshold_lines = self.parallel_config.parallel_threshold_lines
        self.parallel_threshold_size = self.parallel_config.parallel_threshold_size

        # Issue #813: 特化ハンドラーの初期化（依存性注入）
        self.block_handler = BlockHandler(self)
        self.inline_handler = InlineHandler(self)
        self.parallel_handler = ParallelProcessorHandler(self)

        # ストリーミング処理用状態
        self._cancelled = False

        # スレッドローカルストレージ
        import threading

        self._thread_local = threading.local()

        self.logger.debug(
            f"Modular Parser initialized with specialized handlers "
            f"(graceful_errors={graceful_errors}, "
            f"parallel_threshold={self.parallel_threshold_lines} lines, "
            f"memory_limit={self.parallel_config.memory_critical_threshold_mb}MB)"
        )

    @property
    def _thread_local_storage(self) -> Any:
        """スレッドローカルストレージへの統一アクセス"""
        return self._thread_local

    def parse(self, text: str) -> list[Node]:
        """Parse text into AST nodes"""
        self.lines = text.split("\n")
        self.current = 0
        self.errors = []
        nodes = []

        self.logger.info(f"Starting parse of {len(self.lines)} lines")
        self.logger.debug(f"Input text length: {len(text)} characters")

        # 無限ループ防止のための安全装置
        max_iterations = len(self.lines) * 2
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
                self.logger.warning(
                    f"Parser stuck at line {self.current}, forcing advance"
                )
                self.current += 1

            iteration_count += 1

        if iteration_count >= max_iterations:
            self.logger.error(
                f"Parser hit maximum iteration limit ({max_iterations}), stopping"
            )
            self.add_error(f"Parser exceeded maximum iterations at line {self.current}")

        self.logger.info(
            f"Parse complete: {len(nodes)} nodes created, {len(self.errors)} errors"
        )
        return nodes

    def parse_optimized(self, text: str) -> list[Node]:
        """最適化されたパース処理（Issue #727 パフォーマンス最適化対応）"""
        self.logger.info(f"Starting optimized parse of {len(text)} characters")

        # 最適化: 行分割を効率化
        self.lines = self._split_lines_optimized(text)
        self.current = 0
        self.errors = []
        nodes = []

        # パフォーマンス監視開始

        # パフォーマンス監視機能は削除されました
        # パターンキャッシュ初期化
        pattern_cache: dict[str, Any] = {}
        line_type_cache: dict[str, str] = {}

        # 最適化: 事前にラインタイプを一括解析
        line_types = self.block_handler.analyze_line_types_batch(self.lines)

        # メインパースループ（最適化版）
        while self.current < len(self.lines):
            previous_current = self.current

            # 最適化されたライン解析（ハンドラー委譲）
            node = self.block_handler.parse_line_optimized(
                line_types, pattern_cache, line_type_cache, self.current
            )

            if node:
                nodes.append(node)

            # 進捗チェック（最適化）
            if self.current == previous_current:
                self.logger.warning(
                    f"Parser stuck at line {self.current}, forcing advance"
                )
                self.current += 1

        self.logger.info(
            f"Optimized parse complete: {len(nodes)} nodes, {len(self.errors)} errors"
        )

        return nodes

    def _split_lines_optimized(self, text: str) -> list[str]:
        """Issue #757対応: 行分割の最適化実装"""
        # 大容量ファイル用の最適化された行分割
        if len(text) > 1000000:  # 1MB以上
            # メモリ効率を重視した分割
            return text.splitlines()

        # 通常サイズの場合
        return text.splitlines()

    def parse_streaming_from_text(
        self,
        text: str,
        progress_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> Iterator[Node]:
        """Issue #757対応: ストリーミングパース（ハンドラー委譲）"""

        self.logger.info(
            f"Starting streaming parse: {len(text)} chars, "
            f"progress_callback={'enabled' if progress_callback else 'disabled'}"
        )

        lines = text.split("\n")
        total_lines = len(lines)
        current_line = 0
        start_time = time.time()

        # ストリーミング処理状態
        self._cancelled = False
        processed_nodes = 0

        try:
            # チャンクサイズを動的に決定
            chunk_size = self.parallel_handler.calculate_optimal_chunk_size(total_lines)

            self.logger.info(
                f"Streaming configuration: {total_lines} lines, "
                f"chunk_size={chunk_size}"
            )

            # チャンク単位での処理
            while current_line < total_lines and not self._cancelled:
                # チャンク範囲決定
                chunk_end = min(current_line + chunk_size, total_lines)
                chunk_lines = lines[current_line:chunk_end]

                # プログレス更新
                progress_percent = (current_line / total_lines) * 100
                elapsed = time.time() - start_time
                eta_seconds = (
                    int((elapsed / max(current_line, 1)) * (total_lines - current_line))
                    if current_line > 0
                    else 0
                )

                if progress_callback:
                    progress_info = {
                        "current_line": current_line,
                        "total_lines": total_lines,
                        "progress_percent": progress_percent,
                        "eta_seconds": eta_seconds,
                        "processing_rate": current_line / elapsed if elapsed > 0 else 0,
                        "chunk_id": current_line // chunk_size,
                    }
                    progress_callback(progress_info)

                # チャンク内容を解析
                chunk_text = "\n".join(chunk_lines)
                if chunk_text.strip():  # 空チャンクスキップ
                    try:
                        # チャンク解析（最適化されたパーサー使用）
                        chunk_nodes = self.parallel_handler.parse_chunk_optimized(
                            chunk_text, current_line, chunk_end
                        )

                        # ストリーミング出力
                        for node in chunk_nodes:
                            if self._cancelled:
                                break
                            yield node
                            processed_nodes += 1

                    except Exception as e:
                        self.logger.warning(
                            f"Error parsing chunk {current_line}-{chunk_end}: {e}"
                        )

                current_line = chunk_end

                # 定期的なメモリ解放
                if processed_nodes % 1000 == 0:
                    import gc

                    gc.collect()

            # 最終プログレス更新
            if progress_callback and not self._cancelled:
                final_progress = {
                    "current_line": total_lines,
                    "total_lines": total_lines,
                    "progress_percent": 100.0,
                    "eta_seconds": 0,
                    "processing_rate": total_lines / (time.time() - start_time),
                    "completed": True,
                }
                progress_callback(final_progress)

            elapsed_total = time.time() - start_time
            self.logger.info(
                f"Streaming parse completed: {processed_nodes} nodes in {elapsed_total:.2f}s "
                f"({total_lines / elapsed_total:.0f} lines/sec)"
            )

        except Exception as e:
            self.logger.error(f"Streaming parse failed: {e}")
            # フォールバック: 従来の解析方式
            self.logger.info("Falling back to optimized parse")
            yield from self.parse_optimized(text)
        finally:
            # クリーンアップ
            self._cancelled = False

    def parse_parallel_streaming(
        self,
        text: str,
        progress_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> Iterator[Node]:
        """並列ストリーミング処理（ハンドラー委譲）"""
        yield from self.parallel_handler.parse_parallel_streaming(
            text, progress_callback
        )

    def cancel_parsing(self) -> None:
        """ストリーミング解析の安全なキャンセル"""
        self.logger.info("Cancelling streaming parse...")
        self._cancelled = True

    def get_performance_statistics(self) -> dict[str, Any]:
        """パフォーマンス統計を取得"""
        return {
            "total_lines": len(self.lines) if hasattr(self, "lines") else 0,
            "current_position": self.current,
            "errors_count": len(self.errors),
            "graceful_errors_count": (
                len(self.graceful_syntax_errors)
                if hasattr(self, "graceful_syntax_errors")
                else 0
            ),
            "heading_count": getattr(self.block_parser, "heading_counter", 0),
        }

    def get_parallel_processing_metrics(self) -> dict[str, Any]:
        """並列処理メトリクスを取得（ハンドラー委譲）"""
        return self.parallel_handler.get_parallel_processing_metrics()

    def log_performance_summary(
        self, processing_time: float, total_lines: int, total_nodes: int
    ) -> None:
        """パフォーマンスサマリーをログ出力（ハンドラー委譲）"""
        self.parallel_handler.log_performance_summary(
            processing_time, total_lines, total_nodes
        )

    def _parse_line(self) -> Node | None:
        """Parse a single line or block starting from current position"""
        if self.current >= len(self.lines):
            return None

        # Issue #880修正: graceful error handlingの設定に応じて適切な処理を選択
        if self.graceful_errors:
            return self._parse_line_with_graceful_errors()
        else:
            return self._parse_line_traditional()

    def _parse_line_traditional(self) -> Node | None:
        """従来のパース処理（エラー時に例外をスロー）"""
        line = self.lines[self.current].strip()

        # Parse block markers first
        if self.block_parser.is_opening_marker(line):
            self.logger.debug(f"Found block marker at line {self.current}")
            node, next_index = self.block_parser.parse_block_marker(
                self.lines, self.current
            )
            self.current = next_index
            return node

        # Issue #880修正: 通常テキストの処理を追加（フォールバック方式）
        if hasattr(self, "block_handler") and self.block_handler:
            result, next_index = self.block_handler.parse_line_fallback(
                self.lines, self.current
            )
            if result:
                self.current = next_index
                return result

        # フォールバック: インライン記法処理を含むテキストノード作成
        if line:
            # Issue #880修正: キーワード記法の処理を追加
            if hasattr(self, "keyword_parser") and self.keyword_parser:
                # キーワード記法（脚注等）の解析を試行
                try:
                    keywords, metadata, patterns = (
                        self.keyword_parser.parse_marker_keywords(line)
                    )
                    if keywords or metadata:
                        from .core.ast_nodes import Node

                        content_node = Node(
                            type="keyword", content=line, attributes=metadata
                        )
                        self.current += 1
                        return content_node
                except Exception:
                    # パース失敗時は通常のテキスト処理に続行
                    pass

            # 基本的なテキストノード作成
            from .core.ast_nodes import Node

            text_node = Node(type="text", content=line)
            self.current += 1
            return text_node

        # 空行の場合は次に進む
        self.current += 1
        return None

    def _parse_line_with_graceful_errors(self) -> Node | None:
        """graceful error handling対応のパース処理"""
        # エラー回復位置追跡の実装
        original_position = self.current
        original_line = (
            self.lines[self.current] if self.current < len(self.lines) else ""
        )
        line = original_line.strip()

        try:
            # Parse block markers first
            if self.block_parser.is_opening_marker(line):
                self.logger.debug(f"Found block marker at line {self.current}")
                node, next_index = self.block_parser.parse_block_marker(
                    self.lines, self.current
                )
                self.current = next_index
                return node

            # Issue #880修正: 通常テキストの処理を追加（フォールバック方式）
            if hasattr(self, "block_handler") and self.block_handler:
                result, next_index = self.block_handler.parse_line_fallback(
                    self.lines, self.current
                )
                if result:
                    self.current = next_index
                    return result

            # フォールバック: インライン記法処理を含むテキストノード作成
            if line:
                # Issue #880修正: キーワード記法の処理を追加
                if hasattr(self, "keyword_parser") and self.keyword_parser:
                    # キーワード記法（脚注等）の解析を試行
                    try:
                        keywords, metadata, patterns = (
                            self.keyword_parser.parse_marker_keywords(line)
                        )
                        if keywords or metadata:
                            from .core.ast_nodes import Node

                            content_node = Node(
                                type="keyword", content=line, attributes=metadata
                            )
                            self.current += 1
                            return content_node
                    except Exception:
                        # パース失敗時は通常のテキスト処理に続行
                        pass

                # 基本的なテキストノード作成
                from .core.ast_nodes import Node

                text_node = Node(type="text", content=line)
                self.current += 1
                return text_node

            # 空行の場合は次に進む
            self.current += 1
            return None

        except Exception as e:
            # エラー回復位置追跡情報を含むログ
            self.logger.debug(
                f"Error recovery info: pos={original_position}->{self.current}, "
                f"line='{original_line.strip()}', error={type(e).__name__}: {e}"
            )

            self.logger.warning(
                f"Parsing error at line {original_position}: {e} "
                f"(original: '{original_line.strip()}')"
            )

            # エラー位置を回復（元の位置+1に進む）
            self.current = original_position + 1

            return self._create_error_node(original_line.strip(), str(e))

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

        # 修正提案エンジンで拡張
        if hasattr(self, "correction_engine"):
            graceful_error = self.correction_engine.enhance_error_with_suggestions(
                graceful_error
            )
            self.logger.info(
                f"Enhanced error with "
                f"{len(graceful_error.correction_suggestions or [])} suggestions"
            )

        self.graceful_syntax_errors.append(graceful_error)
        self.logger.info(f"Graceful error recorded: {message} at line {line_number}")

    def _create_error_node(self, line: str, error_message: str) -> Node:
        """エラー発生箇所にエラー情報を含むノードを作成"""
        error_content = f"❌ 解析エラー: {error_message} (original_line: {line})"
        return error_node(error_content)

    def get_graceful_errors(self) -> list["GracefulSyntaxError"]:
        """Issue #700: graceful error handlingで収集したエラーを取得"""
        return self.graceful_syntax_errors

    def has_graceful_errors(self) -> bool:
        """graceful error handlingでエラーが記録されているかチェック"""
        return len(self.graceful_syntax_errors) > 0

    def get_graceful_error_summary(self) -> dict[str, Any]:
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

    def get_statistics(self) -> dict[str, Any]:
        """Get parsing statistics"""
        return {
            "total_lines": len(self.lines),
            "errors_count": len(self.errors),
            "heading_count": self.block_parser.heading_counter,
        }


def parse(text: str, config: Any = None) -> list[Node]:
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


def parse_with_error_config(
    text: str, config: Any = None, use_streaming: bool | None = None
) -> list[Node]:
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
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        use_streaming = size_mb > 1.0

    if use_streaming:
        streaming_parser = StreamingParser(config=config)
        nodes = list(streaming_parser.parse_streaming_from_text(text))
        return nodes
    else:
        parser: Parser = Parser(config=config)
        return parser.parse(text)
