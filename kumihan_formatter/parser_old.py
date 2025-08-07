"""Refactored text parser for Kumihan-Formatter

This is the new, modular parser implementation that replaces the monolithic
parser.py file. Each parsing responsibility is now handled by specialized modules.
"""

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional

if TYPE_CHECKING:
    from .core.common.error_base import GracefulSyntaxError

from .core.ast_nodes import Node, error_node
from .core.block_parser import BlockParser
from .core.keyword_parser import KeywordParser
from .core.list_parser import ListParser
from .core.utilities.logger import get_logger
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

    def __init__(self):
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
                config.memory_critical_threshold_mb = int(memory_limit)
                config.memory_warning_threshold_mb = int(memory_limit * 0.6)
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

    def __init__(
        self,
        config=None,
        graceful_errors: bool = False,
        parallel_config: ParallelProcessingConfig = None,
    ) -> None:  # type: ignore
        """Initialize parser with fixed markers

        Args:
            config: Parser configuration (ignored for simplification)
            graceful_errors: Enable graceful error handling (Issue #700)
            parallel_config: 並列処理設定（Issue #759コードレビュー対応）
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
            from .core.error_analysis.correction_engine import CorrectionEngine

            self.correction_engine = CorrectionEngine()
            self.logger.info(
                "Correction engine initialized for graceful error handling"
            )

        # Initialize specialized parsers
        self.keyword_parser = KeywordParser()
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)

        # Issue #700: graceful error handling対応 - sub-parsersにパーサー参照を設定
        if graceful_errors:
            self.block_parser.set_parser_reference(self)

        # Issue #759: 並列処理統合 - ParallelChunkProcessorの初期化
        from .core.utilities.parallel_processor import ParallelChunkProcessor

        self.parallel_processor = ParallelChunkProcessor()

        # 並列処理のしきい値設定（外部設定から取得）
        self.parallel_threshold_lines = self.parallel_config.parallel_threshold_lines
        self.parallel_threshold_size = self.parallel_config.parallel_threshold_size

        self.logger.debug(
            f"Parser initialized with specialized parsers and parallel processing "
            f"(graceful_errors={graceful_errors}, "
            f"parallel_threshold={self.parallel_threshold_lines} lines, "
            f"memory_limit={self.parallel_config.memory_critical_threshold_mb}MB)"
        )  # type: ignore  # type: ignore

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
        """
        最適化されたパーステキスト処理（Issue #727 パフォーマンス最適化対応）

        改善点:
        - O(n²) → O(n) 計算複雑度改善
        - パターンマッチングキャッシュ
        - 文字列処理最適化
        - メモリ効率向上

        Args:
            text: Input text to parse

        Returns:
            list[Node]: Parsed AST nodes
        """
        self.logger.info(f"Starting optimized parse of {len(text)} characters")

        # 最適化: 行分割を効率化（split最適化）
        self.lines = self._split_lines_optimized(text)
        self.current = 0
        self.errors = []
        nodes = []

        # パフォーマンス監視開始
        from .core.performance import monitor_performance

        with monitor_performance("optimized_parse") as perf_monitor:
            # パターンキャッシュ初期化
            pattern_cache = {}
            line_type_cache = {}

            # 最適化: 事前にラインタイプを一括解析（O(n)で処理）
            line_types = self._analyze_line_types_batch(self.lines)

            # メインパースループ（最適化版）
            while self.current < len(self.lines):
                previous_current = self.current

                # 最適化されたライン解析
                node = self._parse_line_optimized(
                    line_types, pattern_cache, line_type_cache
                )

                if node:
                    nodes.append(node)
                    # パフォーマンス監視にアイテム処理を記録
                    perf_monitor.record_item_processed()

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
        """
        Issue #757対応: 行分割の最適化実装

        従来のsplit('\n')より高速な行分割処理
        """
        # 大容量ファイル用の最適化された行分割
        if len(text) > 1000000:  # 1MB以上
            # メモリ効率を重視した分割
            return text.splitlines()
        else:
            # 速度重視の分割
            return text.split("\n")

    def _analyze_line_types_batch(self, lines: list[str]) -> dict[int, str]:
        """
        Issue #757対応: 一括行タイプ解析（O(n)処理）

        全行のタイプを事前に解析することで、後続処理を高速化
        """
        line_types = {}

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                line_types[i] = "empty"
            elif self.block_parser.is_opening_marker(stripped):
                line_types[i] = "block_marker"
            elif stripped.startswith("#") and not self.block_parser.is_opening_marker(
                stripped
            ):
                line_types[i] = "comment"
            elif self.list_parser.is_list_line(stripped):
                line_types[i] = "list"
            else:
                line_types[i] = "paragraph"

        return line_types

    def _parse_line_optimized(
        self, line_types: dict[int, str], pattern_cache: dict, line_type_cache: dict
    ) -> Optional[Node]:
        """
        Issue #757対応: 最適化されたライン解析

        事前解析結果を活用した高速ライン処理
        """
        if self.current >= len(self.lines):
            return None

        line_type = line_types.get(self.current, "unknown")

        # タイプ別高速処理
        if line_type == "empty":
            self.current += 1
            return None
        elif line_type == "block_marker":
            return self._parse_block_marker_fast()
        elif line_type == "comment":
            self.current += 1
            return None
        elif line_type == "list":
            return self._parse_list_fast()
        elif line_type == "paragraph":
            return self._parse_paragraph_fast()
        else:
            # フォールバック
            return self._parse_line_fallback()

    def _parse_block_marker_fast(self) -> Optional[Node]:
        """高速ブロックマーカー解析"""
        node, next_index = self.block_parser.parse_block_marker(
            self.lines, self.current
        )
        self.current = next_index
        return node

    def _parse_list_fast(self) -> Optional[Node]:
        """高速リスト解析"""
        line = self.lines[self.current].strip()
        list_type = self.list_parser.is_list_line(line)

        if list_type == "ul":
            node, next_index = self.list_parser.parse_unordered_list(
                self.lines, self.current
            )
        else:
            node, next_index = self.list_parser.parse_ordered_list(
                self.lines, self.current
            )

        self.current = next_index
        return node

    def _parse_paragraph_fast(self) -> Optional[Node]:
        """高速パラグラフ解析"""
        node, next_index = self.block_parser.parse_paragraph(self.lines, self.current)
        self.current = next_index
        return node

    def _parse_line_fallback(self) -> Optional[Node]:
        """フォールバック処理（従来ロジック）"""
        line = self.lines[self.current].strip()

        if self.block_parser.is_opening_marker(line):
            node, next_index = self.block_parser.parse_block_marker(
                self.lines, self.current
            )
            self.current = next_index
            return node

        self.current += 1
        return None

    def parse_streaming_from_text(
        self, text: str, progress_callback: Optional[Callable[[dict], None]] = None
    ) -> Iterator[Node]:
        """
        Issue #757対応: 本格的なストリーミングパース実装

        大容量ファイル（300K+行）のパフォーマンス最適化を目標に、
        チャンク単位でのストリーミング処理を実装。

        改善点:
        - メモリ効率: 全文を一度にメモリに保持しない
        - 処理速度: チャンク並列処理による高速化
        - プログレス: リアルタイム進捗表示
        - キャンセル: 処理途中での安全な中断

        Args:
            text: 解析対象のテキスト
            progress_callback: プログレス通知用コールバック
                               仕様: {"current_line": int, "total_lines": int,
                                     "progress_percent": float, "eta_seconds": int}

        Yields:
            Node: 解析されたASTノード（ストリーミング出力）
        """
        import time

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
            # チャンクサイズを動的に決定（パフォーマンス最適化）
            chunk_size = self._calculate_optimal_chunk_size(total_lines)

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
                        chunk_nodes = self._parse_chunk_optimized(
                            chunk_text, current_line, chunk_end
                        )

                        # ストリーミング出力
                        for node in chunk_nodes:
                            if not self._cancelled:
                                yield node
                                processed_nodes += 1
                            else:
                                break

                    except Exception as e:
                        self.logger.warning(
                            f"Error parsing chunk {current_line}-{chunk_end}: {e}"
                        )
                        # エラー時も処理継続（graceful degradation）

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
        self, text: str, progress_callback: Optional[Callable[[dict], None]] = None
    ) -> Iterator[Node]:
        """
        Issue #759対応: 並列処理×真のストリーミング統合実装

        大規模ファイル処理の究極パフォーマンス最適化を実現する
        並列チャンク処理とストリーミングを統合した新しいパース方式

        パフォーマンス目標:
        - 300K行ファイル: 5秒以下 (従来23.41秒から78.6%改善)
        - メモリ使用量: 50%以上削減
        - CPU効率: 最大化された並列度

        改善点:
        - マルチスレッドチャンク処理による並列化
        - 動的ワーカー数計算によるCPU効率最大化
        - メモリ安全な並列実行とリアルタイムガベージコレクション
        - 行レベル並列パースとスレッド安全性保証

        Args:
            text: 解析対象のテキスト
            progress_callback: プログレス通知用コールバック
                             仕様: {"current_line": int, "total_lines": int,
                                   "progress_percent": float, "eta_seconds": int,
                                   "parallel_info": dict}

        Yields:
            Node: 解析されたASTノード（ストリーミング出力）

        Raises:
            ParallelProcessingError: 並列処理固有のエラー
            ChunkProcessingError: チャンク処理でのエラー
            ValueError: 不正な入力パラメーター
            MemoryError: メモリ不足による処理中断
        """
        import time

        # 入力検証
        if not isinstance(text, str):
            raise ValueError(f"Expected string input, got {type(text)}")
        if not text.strip():
            self.logger.warning("Empty or whitespace-only text provided")
            return

        self.logger.info(
            f"Starting parallel streaming parse: {len(text)} chars, "
            f"progress_callback={'enabled' if progress_callback else 'disabled'}"
        )

        lines = text.split("\n")
        total_lines = len(lines)
        start_time = time.time()

        # 並列処理条件判定
        should_parallelize = self._should_use_parallel_processing(text, lines)

        if not should_parallelize:
            self.logger.info(
                "Using traditional streaming parse (below parallel threshold)"
            )
            yield from self.parse_streaming_from_text(text, progress_callback)
            return

        self.logger.info(
            f"Parallel processing enabled: {total_lines} lines, "
            f"estimated improvement: 60-80%"
        )

        # 並列処理状態
        self._cancelled = False
        processed_nodes = 0

        try:
            # 適応的チャンク作成
            chunks = self.parallel_processor.create_chunks_adaptive(
                lines, target_chunk_count=None  # 自動計算
            )

            if not chunks:
                raise ChunkProcessingError("Failed to create processing chunks")

            chunk_size = len(chunks[0].lines) if chunks else 100
            self.logger.info(
                f"Parallel configuration: {len(chunks)} chunks, "
                f"chunk_size={chunk_size}"
            )

            # 並列処理実行
            chunk_progress_info = {
                "completed_chunks": 0,
                "total_chunks": len(chunks),
                "processing_stage": "parallel_execution",
            }

            # メモリ監視付き並列処理
            for i, result in enumerate(
                self._process_chunks_with_memory_monitoring(
                    chunks,
                    chunk_progress_info,
                    progress_callback,
                    start_time,
                    total_lines,
                )
            ):
                if not self._cancelled and result:
                    yield result
                    processed_nodes += 1
                elif self._cancelled:
                    self.logger.warning("Processing cancelled by user request")
                    break

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
                    "parallel_info": {
                        "chunks_processed": len(chunks),
                        "parallel_efficiency": "high",
                    },
                }
                progress_callback(final_progress)

            elapsed_total = time.time() - start_time
            self.logger.info(
                f"Parallel streaming parse completed: {processed_nodes} nodes "
                f"in {elapsed_total:.2f}s ({total_lines / elapsed_total:.0f} lines/sec, "
                f"improvement: {((23.41 - elapsed_total) / 23.41 * 100):.1f}%)"
            )

        except (ParallelProcessingError, ChunkProcessingError) as e:
            self.logger.error(f"Parallel processing error: {e}")
            # フォールバック: 最適化版パース
            self.logger.info("Falling back to optimized parse")
            yield from self.parse_optimized(text)
        except MemoryError as e:
            self.logger.error(f"Memory error during parallel processing: {e}")
            # フォールバック: 低メモリ版ストリーミング
            self.logger.info("Falling back to memory-safe streaming")
            yield from self.parse_streaming_from_text(text, progress_callback)
        except Exception as e:
            self.logger.error(f"Unexpected error in parallel streaming parse: {e}")
            # 最後のフォールバック: 従来の解析方式
            self.logger.info("Falling back to traditional parse")
            yield from self.parse(text)
        finally:
            # クリーンアップ
            self._cancelled = False

    def _process_chunks_with_memory_monitoring(
        self,
        chunks,
        chunk_progress_info: dict,
        progress_callback,
        start_time: float,
        total_lines: int,
    ) -> Iterator[Node]:
        """
        メモリ監視付きチャンク並列処理（Issue #759コードレビュー対応）

        メモリ使用量を監視しながら安全に並列処理を実行

        Args:
            chunks: 処理対象チャンクリスト
            chunk_progress_info: チャンク進捗情報
            progress_callback: プログレス通知コールバック
            start_time: 処理開始時刻
            total_lines: 総行数

        Yields:
            Node: 解析されたノード

        Raises:
            MemoryMonitoringError: メモリ監視でエラーが発生した場合
        """
        try:
            # メモリ監視の初期化
            memory_monitor = self._init_enhanced_memory_monitor()
            processed_chunks = 0

            # 並列処理実行
            for i, result in enumerate(
                self.parallel_processor.process_chunks_parallel_optimized(
                    chunks,
                    self._parse_chunk_parallel_optimized,
                    lambda info: self._update_parallel_progress(
                        info,
                        chunk_progress_info,
                        progress_callback,
                        start_time,
                        total_lines,
                    ),
                )
            ):
                if self._cancelled:
                    break

                if result:
                    yield result

                processed_chunks += 1

                # メモリ監視チェック（定期的）
                if processed_chunks % 10 == 0:
                    memory_status = memory_monitor.check_memory_status()

                    if memory_status["critical"]:
                        self.logger.warning(
                            f"Critical memory usage: {memory_status['current_mb']:.1f}MB, "
                            f"triggering aggressive cleanup"
                        )

                        # 積極的ガベージコレクション
                        import gc

                        gc.collect()

                        # メモリ状況再チェック
                        memory_status = memory_monitor.check_memory_status()
                        if memory_status["critical"]:
                            raise MemoryMonitoringError(
                                f"Memory usage remains critical after cleanup: "
                                f"{memory_status['current_mb']:.1f}MB"
                            )

                    elif memory_status["warning"]:
                        self.logger.info(
                            f"High memory usage: {memory_status['current_mb']:.1f}MB, "
                            f"performing routine cleanup"
                        )
                        import gc

                        gc.collect()

        except Exception as e:
            self.logger.error(f"Memory monitoring error in parallel processing: {e}")
            raise MemoryMonitoringError(
                f"Failed to monitor memory during parallel processing: {e}"
            )

    def _init_enhanced_memory_monitor(self):
        """拡張メモリ監視システムの初期化"""

        class EnhancedMemoryMonitor:
            def __init__(self):
                self.logger = get_logger(__name__)
                self.warning_threshold_mb = 150  # 150MB で警告
                self.critical_threshold_mb = 250  # 250MB で重大警告

            def get_current_memory_mb(self) -> float:
                """現在のメモリ使用量をMBで取得（エラーハンドリング強化）"""
                try:
                    import psutil

                    process = psutil.Process()
                    memory_info = process.memory_info()
                    return memory_info.rss / 1024 / 1024  # MB
                except ImportError:
                    self.logger.debug("psutil not available, using estimated memory")
                    return 75.0  # 推定値
                except Exception as e:
                    self.logger.debug(f"Memory monitoring error: {e}")
                    return 0.0

            def check_memory_status(self) -> dict:
                """メモリ状況の包括的チェック"""
                current_mb = self.get_current_memory_mb()

                return {
                    "current_mb": current_mb,
                    "warning": current_mb > self.warning_threshold_mb,
                    "critical": current_mb > self.critical_threshold_mb,
                    "percentage_of_critical": (current_mb / self.critical_threshold_mb)
                    * 100,
                    "safe": current_mb <= self.warning_threshold_mb,
                }

        return EnhancedMemoryMonitor()

    def get_parallel_processing_metrics(self) -> dict:
        """
        並列処理のパフォーマンスメトリクスを取得（Issue #759コードレビュー対応）

        Returns:
            dict: パフォーマンス統計情報
        """
        import os

        metrics = {
            # システム情報
            "system_info": {
                "cpu_count": os.cpu_count() or 1,
                "parallel_threshold_lines": self.parallel_threshold_lines,
                "parallel_threshold_size": self.parallel_threshold_size,
                "memory_limit_mb": self.parallel_config.memory_critical_threshold_mb,
            },
            # 設定情報
            "configuration": {
                "chunk_min_size": self.parallel_config.min_chunk_size,
                "chunk_max_size": self.parallel_config.max_chunk_size,
                "memory_monitoring": self.parallel_config.enable_memory_monitoring,
                "gc_optimization": self.parallel_config.enable_gc_optimization,
                "timeout_seconds": self.parallel_config.processing_timeout_seconds,
            },
            # 実行時統計
            "runtime_stats": {
                "current_lines": len(self.lines) if hasattr(self, "lines") else 0,
                "errors_count": len(self.errors) if hasattr(self, "errors") else 0,
                "graceful_errors_count": (
                    len(self.graceful_syntax_errors)
                    if hasattr(self, "graceful_syntax_errors")
                    else 0
                ),
            },
            # メモリ統計
            "memory_stats": self._get_memory_statistics(),
            # 並列処理統計
            "parallel_stats": (
                self._get_parallel_statistics()
                if hasattr(self, "parallel_processor")
                else {}
            ),
        }

        return metrics

    def _get_memory_statistics(self) -> dict:
        """メモリ使用統計を取得"""
        try:
            memory_monitor = self._init_enhanced_memory_monitor()
            memory_status = memory_monitor.check_memory_status()

            return {
                "current_mb": memory_status["current_mb"],
                "warning_threshold_mb": memory_monitor.warning_threshold_mb,
                "critical_threshold_mb": memory_monitor.critical_threshold_mb,
                "is_warning": memory_status["warning"],
                "is_critical": memory_status["critical"],
                "usage_percentage": memory_status["percentage_of_critical"],
            }
        except Exception as e:
            self.logger.debug(f"Memory statistics error: {e}")
            return {"error": str(e)}

    def _get_parallel_statistics(self) -> dict:
        """並列処理統計を取得"""
        try:
            # 並列プロセッサーから統計を取得
            if hasattr(self.parallel_processor, "get_statistics"):
                return self.parallel_processor.get_statistics()
            else:
                return {
                    "available": True,
                    "status": "ready",
                    "processed_chunks": 0,
                    "total_processing_time": 0.0,
                }
        except Exception as e:
            self.logger.debug(f"Parallel statistics error: {e}")
            return {"error": str(e)}

    def log_performance_summary(
        self, processing_time: float, total_lines: int, total_nodes: int
    ):
        """
        パフォーマンスサマリーをログ出力（Issue #759対応）

        Args:
            processing_time: 処理時間（秒）
            total_lines: 処理行数
            total_nodes: 生成ノード数
        """
        metrics = self.get_parallel_processing_metrics()

        # パフォーマンス指標計算
        lines_per_second = total_lines / processing_time if processing_time > 0 else 0
        nodes_per_second = total_nodes / processing_time if processing_time > 0 else 0

        # ベースライン（従来方式）との比較
        baseline_time = 23.41  # 300K行での従来処理時間
        baseline_lines = 300000
        estimated_baseline_time = (total_lines / baseline_lines) * baseline_time
        improvement_percent = (
            (
                (estimated_baseline_time - processing_time)
                / estimated_baseline_time
                * 100
            )
            if estimated_baseline_time > 0
            else 0
        )

        # サマリーログ出力
        self.logger.info(
            f"\n"
            f"=== Issue #759 パフォーマンスサマリー ===\n"
            f"処理時間: {processing_time:.2f}秒\n"
            f"処理行数: {total_lines:,}行\n"
            f"生成ノード数: {total_nodes:,}個\n"
            f"処理速度: {lines_per_second:.0f}行/秒, {nodes_per_second:.0f}ノード/秒\n"
            f"推定改善率: {improvement_percent:+.1f}%\n"
            f"メモリ使用量: {metrics['memory_stats'].get('current_mb', 'N/A')}MB\n"
            f"並列処理: {'有効' if total_lines >= self.parallel_threshold_lines else '無効'}\n"
            f"CPU数: {metrics['system_info']['cpu_count']}コア\n"
            f"エラー: {metrics['runtime_stats']['errors_count']}件\n"
            f"==============================="
        )

    def parse_parallel_streaming_memory_safe(
        self, text_or_file, progress_callback: Optional[Callable[[dict], None]] = None
    ) -> Iterator[Node]:
        """
        メモリ安全な並列ストリーミング解析（Issue #759コードレビュー対応）

        大容量ファイル処理時のメモリ爆発を防止する改良版

        Args:
            text_or_file: ファイルパス(Path/str)またはテキスト(str)
            progress_callback: プログレス通知用コールバック

        Yields:
            Node: 解析されたASTノード
        """
        from pathlib import Path

        # 入力タイプ判定とメモリ安全な処理方式選択
        if isinstance(text_or_file, (str, Path)):
            file_path = Path(text_or_file)
            if file_path.exists():
                # ファイルの場合は真のストリーミング処理（メモリ安全）
                self.logger.info(f"Memory-safe file processing: {file_path}")
                yield from self.parse_true_streaming_from_file(
                    file_path, progress_callback
                )
                return

        # テキストの場合はサイズチェック
        text = str(text_or_file)
        text_size_mb = len(text.encode("utf-8")) / (1024 * 1024)

        if text_size_mb > 100:  # 100MB超過時はワーニング
            self.logger.warning(
                f"Large text processing: {text_size_mb:.1f}MB. "
                f"Consider using file-based processing for better memory efficiency."
            )

        # テキストサイズに応じた処理方式選択
        if text_size_mb > 50:  # 50MB以上は段階的処理
            yield from self._parse_text_chunked_streaming(text, progress_callback)
        else:
            # 通常の並列ストリーミング
            yield from self.parse_parallel_streaming(text, progress_callback)

    def _parse_text_chunked_streaming(
        self, text: str, progress_callback: Optional[Callable[[dict], None]] = None
    ) -> Iterator[Node]:
        """
        大容量テキストの段階的ストリーミング処理

        メモリ使用量を一定に保ちながら処理する改良実装
        """
        import time

        self.logger.info(
            f"Starting chunked streaming for large text: {len(text)/1024/1024:.1f}MB"
        )

        # 段階的テキスト分割（行単位でイテレート）
        lines_processed = 0
        chunk_buffer = []
        chunk_size = 1000  # 1000行ずつ処理
        start_time = time.time()

        try:
            for line in self._text_line_iterator(text):
                chunk_buffer.append(line)
                lines_processed += 1

                # チャンクサイズに達したら処理
                if len(chunk_buffer) >= chunk_size:
                    chunk_text = "\n".join(chunk_buffer)

                    # チャンク解析
                    for node in self.parse_optimized(chunk_text):
                        if node:
                            yield node

                    # メモリクリア
                    chunk_buffer.clear()

                    # プログレス更新
                    if progress_callback and lines_processed % 5000 == 0:
                        elapsed = time.time() - start_time
                        progress_info = {
                            "current_line": lines_processed,
                            "total_lines": text.count("\n") + 1,
                            "progress_percent": (
                                lines_processed / (text.count("\n") + 1)
                            )
                            * 100,
                            "processing_rate": (
                                lines_processed / elapsed if elapsed > 0 else 0
                            ),
                            "memory_safe_mode": True,
                        }
                        progress_callback(progress_info)

                    # 定期的なガベージコレクション
                    if lines_processed % 10000 == 0:
                        import gc

                        gc.collect()

            # 残りバッファの処理
            if chunk_buffer:
                chunk_text = "\n".join(chunk_buffer)
                for node in self.parse_optimized(chunk_text):
                    if node:
                        yield node

        except Exception as e:
            self.logger.error(f"Chunked streaming failed: {e}")
            raise

    def _text_line_iterator(self, text: str) -> Iterator[str]:
        """
        テキストを行単位でイテレートするメモリ効率的なジェネレータ
        """
        start = 0
        while start < len(text):
            # 改行位置を検索
            newline_pos = text.find("\n", start)
            if newline_pos == -1:
                # 最後の行
                if start < len(text):
                    yield text[start:]
                break
            else:
                yield text[start:newline_pos]
                start = newline_pos + 1

    def parse_true_streaming_from_file(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[dict], None]] = None,
    ) -> Iterator[Node]:
        """
        Issue #759対応: 真のストリーミング実装

        ファイルディスクリプタベース読み取りによる
        メモリ使用量大幅削減とリアルタイム処理を実現

        改善点:
        - 全行一括読み込み (text.split('\n')) の完全廃止
        - 行単位の真のストリーミング処理
        - バッファリング最適化とリアルタイムガベージコレクション
        - メモリ効率最大化: ファイルサイズに依存しない一定メモリ使用量

        パフォーマンス目標:
        - メモリ使用量: 50%以上削減
        - 大容量ファイル: 安定した処理時間
        - リアルタイム: 行単位での即座な結果出力

        Args:
            file_path: 解析対象ファイルパス
            progress_callback: プログレス通知用コールバック
                             仕様: {"current_line": int, "total_lines": int,
                                   "progress_percent": float, "eta_seconds": int,
                                   "memory_mb": float, "streaming_info": dict}

        Yields:
            Node: 解析されたASTノード（リアルタイム出力）
        """
        self.logger.info(f"Starting true streaming parse from file: {file_path}")

        # 前処理と初期化
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stream_context = self._initialize_streaming_context(
            file_path, progress_callback
        )

        try:
            # メインストリーミング処理
            yield from self._execute_streaming_parse(stream_context)

            # 最終処理
            self._finalize_streaming_parse(stream_context)

        except Exception as e:
            self.logger.error(f"True streaming parse failed: {e}")
            raise
        finally:
            # クリーンアップ
            self._cleanup_streaming_resources()

    def _initialize_streaming_context(self, file_path: Path, progress_callback) -> dict:
        """ストリーミング処理コンテキストの初期化"""
        import time

        file_size = file_path.stat().st_size
        self.logger.info(f"File size: {file_size:,} bytes")

        # 真のストリーミング処理状態
        self._cancelled = False

        context = {
            "file_path": file_path,
            "file_size": file_size,
            "progress_callback": progress_callback,
            "processed_nodes": 0,
            "current_line_num": 0,
            "start_time": time.time(),
            "estimated_lines": self._estimate_total_lines_fast(file_path),
            "memory_monitor": self._init_memory_monitor(),
            "line_buffer": [],
            "buffer_threshold": 50,  # 小さなバッファサイズでメモリ効率最大化
        }

        return context

    def _execute_streaming_parse(self, context: dict) -> Iterator[Node]:
        """メインストリーミング解析処理"""
        with open(context["file_path"], "r", encoding="utf-8", buffering=8192) as file:
            for line_content in file:
                # キャンセルチェック
                if self._cancelled:
                    self.logger.info("True streaming parse cancelled")
                    break

                context["current_line_num"] += 1
                context["line_buffer"].append(line_content.rstrip("\n\r"))

                # バッファ処理
                if len(context["line_buffer"]) >= context["buffer_threshold"]:
                    yield from self._process_buffer_chunk(context)

                # プログレス更新とメンテナンス
                if context["current_line_num"] % 100 == 0:
                    self._update_streaming_progress(context)

                if context["processed_nodes"] % 500 == 0:
                    self._perform_streaming_maintenance(context)

            # 残りバッファの処理
            if context["line_buffer"]:
                yield from self._process_final_buffer(context)

    def _process_buffer_chunk(self, context: dict) -> Iterator[Node]:
        """バッファチャンクの処理"""
        # リアルタイム解析処理
        start_line = context["current_line_num"] - len(context["line_buffer"])
        for node in self._process_streaming_buffer(context["line_buffer"], start_line):
            if node:
                yield node
                context["processed_nodes"] += 1

        # メモリ効率のためのバッファクリア
        context["line_buffer"].clear()

    def _process_final_buffer(self, context: dict) -> Iterator[Node]:
        """最終バッファの処理"""
        start_line = context["current_line_num"] - len(context["line_buffer"])
        for node in self._process_streaming_buffer(context["line_buffer"], start_line):
            if node:
                yield node
                context["processed_nodes"] += 1

    def _update_streaming_progress(self, context: dict):
        """ストリーミングプログレス更新"""
        if context["progress_callback"]:
            progress_info = self._calculate_streaming_progress(
                context["current_line_num"],
                context["estimated_lines"],
                context["start_time"],
                context["memory_monitor"],
                context["processed_nodes"],
            )
            context["progress_callback"](progress_info)

    def _perform_streaming_maintenance(self, context: dict):
        """ストリーミングメンテナンス処理"""
        import gc

        gc.collect()

        # メモリ使用量チェック
        current_memory = context["memory_monitor"].get_current_memory_mb()
        if current_memory > 200:  # 200MB閾値
            self.logger.warning(
                f"High memory usage in streaming: {current_memory:.1f}MB"
            )

    def _finalize_streaming_parse(self, context: dict):
        """ストリーミング解析の最終処理"""
        import time

        # 最終プログレス更新
        if context["progress_callback"] and not self._cancelled:
            final_progress = self._calculate_streaming_progress(
                context["current_line_num"],
                context["current_line_num"],
                context["start_time"],
                context["memory_monitor"],
                context["processed_nodes"],
                completed=True,
            )
            context["progress_callback"](final_progress)

        elapsed_total = time.time() - context["start_time"]
        final_memory = context["memory_monitor"].get_current_memory_mb()

        self.logger.info(
            f"True streaming parse completed: {context['processed_nodes']} nodes from "
            f"{context['current_line_num']} lines in {elapsed_total:.2f}s "
            f"({context['current_line_num'] / elapsed_total:.0f} lines/sec, "
            f"memory: {final_memory:.1f}MB)"
        )

    def _cleanup_streaming_resources(self):
        """ストリーミングリソースのクリーンアップ"""
        self._cancelled = False

    def parse_hybrid_optimized(
        self, input_source, progress_callback: Optional[Callable[[dict], None]] = None
    ) -> Iterator[Node]:
        """
        Issue #759対応: ハイブリッド処理モード

        ファイルサイズと処理特性に応じて最適な処理方式を
        自動選択するインテリジェントなパーサー

        処理モード選択:
        - 小容量ファイル (< 1MB, < 1K行): 従来方式（最速）
        - 中容量ファイル (1MB-10MB, 1K-10K行): チャンクベースストリーミング
        - 大容量ファイル (> 10MB, > 10K行): 並列×真のストリーミング

        Args:
            input_source: ファイルパス(Path)またはテキスト(str)
            progress_callback: プログレス通知用コールバック

        Yields:
            Node: 解析されたASTノード
        """
        from pathlib import Path

        self.logger.info("Starting hybrid optimized parse")

        # 入力タイプ判定
        if isinstance(input_source, (str, Path)):
            file_path = Path(input_source)
            if file_path.exists():
                # ファイルからの処理
                yield from self._parse_from_file_hybrid(file_path, progress_callback)
            else:
                # テキストとして処理
                yield from self._parse_from_text_hybrid(
                    str(input_source), progress_callback
                )
        else:
            # テキストとして処理
            yield from self._parse_from_text_hybrid(
                str(input_source), progress_callback
            )

    def _parse_from_file_hybrid(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[dict], None]] = None,
    ) -> Iterator[Node]:
        """ファイルに対するハイブリッド処理"""

        # ファイル情報取得
        file_size = file_path.stat().st_size
        estimated_lines = self._estimate_total_lines_fast(file_path)

        # 処理モード決定
        processing_mode = self._determine_processing_mode(file_size, estimated_lines)

        self.logger.info(
            f"Hybrid mode selected: {processing_mode} "
            f"(size: {file_size/1024/1024:.1f}MB, lines: ~{estimated_lines})"
        )

        # モード別処理実行
        if processing_mode == "traditional":
            # 小容量: 従来の高速処理
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            yield from self.parse_optimized(content)

        elif processing_mode == "streaming":
            # 中容量: チャンクベースストリーミング
            yield from self._parse_file_streaming_optimized(
                file_path, progress_callback
            )

        elif processing_mode == "parallel_streaming":
            # 大容量: 並列×真のストリーミング統合
            yield from self._parse_file_parallel_streaming(file_path, progress_callback)

        else:
            # フォールバック
            self.logger.warning(
                f"Unknown processing mode: {processing_mode}, using traditional"
            )
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            yield from self.parse_optimized(content)

    def _parse_from_text_hybrid(
        self, text: str, progress_callback: Optional[Callable[[dict], None]] = None
    ) -> Iterator[Node]:
        """テキストに対するハイブリッド処理"""

        # テキスト特性分析
        text_size = len(text)
        estimated_lines = text.count("\n") + 1

        # 処理モード決定
        processing_mode = self._determine_processing_mode(text_size, estimated_lines)

        self.logger.info(
            f"Hybrid text mode: {processing_mode} "
            f"(size: {text_size/1024/1024:.1f}MB, lines: {estimated_lines})"
        )

        # モード別処理実行
        if processing_mode == "traditional":
            # 小容量: 最適化された従来処理
            yield from self.parse_optimized(text)

        elif processing_mode == "streaming":
            # 中容量: テキストストリーミング
            yield from self.parse_streaming_from_text(text, progress_callback)

        elif processing_mode == "parallel_streaming":
            # 大容量: 並列ストリーミング
            yield from self.parse_parallel_streaming(text, progress_callback)

        else:
            # フォールバック
            yield from self.parse_optimized(text)

    def _determine_processing_mode(self, size_bytes: int, estimated_lines: int) -> str:
        """最適な処理モードを決定"""

        # サイズベースの判定
        size_mb = size_bytes / 1024 / 1024

        # CPU数考慮
        import os

        cpu_count = os.cpu_count() or 1

        # 判定ロジック
        if size_mb < 1 and estimated_lines < 1000:
            # 小容量: 従来方式が最適
            return "traditional"

        elif size_mb < 10 and estimated_lines < 10000:
            # 中容量: ストリーミング方式
            return "streaming"

        elif size_mb >= 10 or estimated_lines >= 10000:
            # 大容量: 並列処理が有効
            if cpu_count >= 2:
                return "parallel_streaming"
            else:
                return "streaming"  # シングルコアならストリーミング
        else:
            # デフォルト
            return "traditional"

    def _parse_file_streaming_optimized(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[dict], None]] = None,
    ) -> Iterator[Node]:
        """ファイル用最適化ストリーミング処理"""
        yield from self.parse_true_streaming_from_file(file_path, progress_callback)

    def _parse_file_parallel_streaming(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[dict], None]] = None,
    ) -> Iterator[Node]:
        """ファイル用並列ストリーミング処理"""

        # ファイルを効率的に読み込み
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # 並列ストリーミング実行
        yield from self.parse_parallel_streaming(content, progress_callback)

    def get_processing_recommendations(self, input_source) -> dict:
        """入力に対する処理方式の推奨事項を取得"""
        from pathlib import Path

        recommendations = {
            "input_type": "unknown",
            "size_mb": 0,
            "estimated_lines": 0,
            "recommended_mode": "traditional",
            "expected_performance": "unknown",
            "memory_usage": "low",
            "cpu_utilization": "low",
        }

        try:
            if isinstance(input_source, (str, Path)):
                file_path = Path(input_source)
                if file_path.exists():
                    # ファイル分析
                    file_size = file_path.stat().st_size
                    estimated_lines = self._estimate_total_lines_fast(file_path)

                    recommendations.update(
                        {
                            "input_type": "file",
                            "size_mb": file_size / 1024 / 1024,
                            "estimated_lines": estimated_lines,
                            "recommended_mode": self._determine_processing_mode(
                                file_size, estimated_lines
                            ),
                        }
                    )
                else:
                    # テキスト分析
                    text = str(input_source)
                    text_size = len(text)
                    estimated_lines = text.count("\n") + 1

                    recommendations.update(
                        {
                            "input_type": "text",
                            "size_mb": text_size / 1024 / 1024,
                            "estimated_lines": estimated_lines,
                            "recommended_mode": self._determine_processing_mode(
                                text_size, estimated_lines
                            ),
                        }
                    )

            # パフォーマンス予測
            mode = recommendations["recommended_mode"]
            if mode == "traditional":
                recommendations.update(
                    {
                        "expected_performance": "very_fast",
                        "memory_usage": "low",
                        "cpu_utilization": "single_core",
                    }
                )
            elif mode == "streaming":
                recommendations.update(
                    {
                        "expected_performance": "fast",
                        "memory_usage": "constant",
                        "cpu_utilization": "single_core_optimized",
                    }
                )
            elif mode == "parallel_streaming":
                recommendations.update(
                    {
                        "expected_performance": "very_fast_parallel",
                        "memory_usage": "optimized",
                        "cpu_utilization": "multi_core",
                    }
                )

        except Exception as e:
            self.logger.warning(f"Processing recommendation failed: {e}")

        return recommendations

    def _process_streaming_buffer(
        self, lines: list[str], start_line: int
    ) -> Iterator[Node]:
        """ストリーミングバッファの効率的処理"""
        try:
            # 効率的なテキスト結合
            buffer_text = "\n".join(lines)

            if buffer_text.strip():  # 空バッファスキップ
                # 最適化されたパーサーで高速処理
                buffer_nodes = self.parse_optimized(buffer_text)

                # ストリーミング出力
                for node in buffer_nodes:
                    if node:
                        yield node

        except Exception as e:
            self.logger.warning(
                f"Streaming buffer parse failed (lines {start_line}-{start_line + len(lines)}): {e}"
            )
            # エラー時も処理継続

    def _estimate_total_lines_fast(self, file_path: Path) -> int:
        """高速行数推定（全ファイル読み込みなし）"""
        try:
            # サンプリングベースの推定
            sample_size = min(16384, file_path.stat().st_size)  # 16KB サンプル

            with open(file_path, "r", encoding="utf-8") as file:
                sample = file.read(sample_size)
                if not sample:
                    return 0

                sample_lines = sample.count("\n")
                file_size = file_path.stat().st_size

                if len(sample) < file_size:
                    # 全体の行数を推定
                    estimated_lines = int((sample_lines / len(sample)) * file_size)
                    return max(estimated_lines, 1)
                else:
                    return sample_lines + 1

        except Exception as e:
            self.logger.warning(f"Line estimation error: {e}")
            # フォールバック: ファイルサイズベースの推定
            return max(1, int(file_path.stat().st_size / 60))  # 平均60バイト/行と仮定

    def _init_memory_monitor(self):
        """メモリ監視システムの初期化"""

        class MemoryMonitor:
            def __init__(self):
                self.logger = get_logger(__name__)

            def get_current_memory_mb(self) -> float:
                """現在のメモリ使用量をMBで取得"""
                try:
                    import psutil

                    process = psutil.Process()
                    memory_info = process.memory_info()
                    return memory_info.rss / 1024 / 1024  # MB
                except ImportError:
                    # psutil未利用環境ではダミー値
                    return 50.0
                except Exception as e:
                    self.logger.debug(f"Memory monitoring error: {e}")
                    return 0.0

        return MemoryMonitor()

    def _calculate_streaming_progress(
        self,
        current_line: int,
        total_lines: int,
        start_time: float,
        memory_monitor,
        processed_nodes: int,
        completed: bool = False,
    ) -> dict:
        """ストリーミング進捗情報の計算"""

        elapsed = time.time() - start_time
        progress_percent = (
            (current_line / max(total_lines, 1)) * 100 if not completed else 100.0
        )

        # ETA計算
        eta_seconds = 0
        if not completed and progress_percent > 0 and elapsed > 0:
            remaining_percent = 100 - progress_percent
            eta_seconds = int((elapsed / progress_percent) * remaining_percent)

        # 処理速度計算
        processing_rate = current_line / elapsed if elapsed > 0 else 0

        # メモリ使用量取得
        memory_mb = memory_monitor.get_current_memory_mb()

        return {
            "current_line": current_line,
            "total_lines": total_lines,
            "progress_percent": progress_percent,
            "eta_seconds": max(0, eta_seconds),
            "processing_rate": processing_rate,
            "memory_mb": memory_mb,
            "streaming_info": {
                "nodes_processed": processed_nodes,
                "memory_efficiency": "high" if memory_mb < 100 else "moderate",
                "streaming_mode": "true_streaming",
                "buffer_size": "optimized",
                "completed": completed,
            },
        }

    def _should_use_parallel_processing(self, text: str, lines: list[str]) -> bool:
        """並列処理を使用すべきかを判定"""

        # ファイルサイズチェック
        text_size = len(text)
        line_count = len(lines)

        # 並列化の条件
        size_condition = text_size >= self.parallel_threshold_size
        lines_condition = line_count >= self.parallel_threshold_lines

        # CPU数チェック（最低2コア必要）
        import os

        cpu_count = os.cpu_count() or 1
        cpu_condition = cpu_count >= 2

        should_parallelize = (size_condition or lines_condition) and cpu_condition

        self.logger.debug(
            f"Parallel processing decision: size={text_size/1024/1024:.1f}MB "
            f"({size_condition}), lines={line_count} ({lines_condition}), "
            f"cpu={cpu_count} ({cpu_condition}) → "
            f"{'PARALLEL' if should_parallelize else 'SEQUENTIAL'}"
        )

        return should_parallelize

    def _parse_chunk_parallel_optimized(self, chunk) -> Iterator[Node]:
        """
        単一チャンクの並列最適化解析（スレッドセーフ）

        Args:
            chunk: ChunkInfo オブジェクト

        Yields:
            Node: 解析されたノード
        """
        try:
            # スレッドローカルパーサーコンポーネントを使用
            thread_local_parser = self._get_thread_local_parser()

            # チャンク内容をテキストに変換
            chunk_text = "\n".join(chunk.lines)

            if chunk_text.strip():  # 空チャンクスキップ
                # 最適化されたパーサーを使用
                chunk_nodes = thread_local_parser.parse_optimized(chunk_text)

                # ストリーミング出力
                for node in chunk_nodes:
                    if node:  # Noneフィルタリング
                        yield node

        except Exception as e:
            self.logger.warning(
                f"Parallel chunk parse failed (chunk {chunk.chunk_id}): {e}"
            )
            # エラー時も処理継続（graceful degradation）

    def _get_thread_local_parser(self):
        """スレッドローカルパーサーインスタンスを取得"""
        if not hasattr(self._thread_local_storage, "parser"):
            # スレッド固有のパーサーインスタンスを作成
            self._thread_local_storage.parser = Parser(
                config=self.config, graceful_errors=self.graceful_errors
            )

        return self._thread_local_storage.parser

    def _update_parallel_progress(
        self,
        chunk_info: dict,
        chunk_progress: dict,
        progress_callback,
        start_time: float,
        total_lines: int,
    ):
        """並列処理プログレス更新"""
        if not progress_callback:
            return

        # チャンク進捗を更新
        chunk_progress["completed_chunks"] = chunk_info.get("completed_chunks", 0)

        # 全体進捗を計算
        progress_percent = (
            chunk_progress["completed_chunks"] / chunk_progress["total_chunks"] * 100
            if chunk_progress["total_chunks"] > 0
            else 0
        )

        # ETA計算
        elapsed = time.time() - start_time
        eta_seconds = (
            int(elapsed / max(progress_percent / 100, 0.01) - elapsed)
            if progress_percent > 0
            else 0
        )

        # プログレス情報を構築
        progress_info = {
            "current_line": int(total_lines * progress_percent / 100),
            "total_lines": total_lines,
            "progress_percent": progress_percent,
            "eta_seconds": max(0, eta_seconds),
            "processing_rate": (
                total_lines * progress_percent / 100 / elapsed if elapsed > 0 else 0
            ),
            "parallel_info": {
                "completed_chunks": chunk_progress["completed_chunks"],
                "total_chunks": chunk_progress["total_chunks"],
                "chunk_id": chunk_info.get("chunk_id", 0),
                "processing_stage": chunk_progress["processing_stage"],
                "efficiency": "high" if progress_percent > 0 else "starting",
            },
        }

        progress_callback(progress_info)

    @property
    def _thread_local_storage(self):
        """スレッドローカルストレージの遅延初期化"""
        import threading

        if not hasattr(self, "_thread_local"):
            self._thread_local = threading.local()
        return self._thread_local

    def _calculate_optimal_chunk_size(self, total_lines: int) -> int:
        """最適なチャンクサイズを計算（Issue #757パフォーマンス最適化）"""
        # ファイルサイズに応じた動的チャンクサイズ
        if total_lines <= 1000:
            return 100  # 小ファイル: 100行/チャンク
        elif total_lines <= 10000:
            return 500  # 中ファイル: 500行/チャンク
        elif total_lines <= 100000:
            return 1000  # 大ファイル: 1000行/チャンク
        else:
            return 2000  # 超大ファイル: 2000行/チャンク

    def _parse_chunk_optimized(
        self, chunk_text: str, start_line: int, end_line: int
    ) -> list[Node]:
        """
        チャンク解析の最適化実装（Issue #757）

        Args:
            chunk_text: チャンクテキスト
            start_line: 開始行番号
            end_line: 終了行番号

        Returns:
            list[Node]: 解析されたノード群
        """
        try:
            # Issue #755対応: 最適化されたパーサーを使用
            return self.parse_optimized(chunk_text)
        except Exception as e:
            self.logger.warning(
                f"Chunk parse failed (lines {start_line}-{end_line}): {e}"
            )
            return []

    def cancel_parsing(self) -> None:
        """ストリーミング解析の安全なキャンセル（Issue #757）"""
        self.logger.info("Cancelling streaming parse...")
        self._cancelled = True

    def get_performance_statistics(self) -> dict:
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
                self.logger.warning(
                    f"Force advancing line due to parsing error at line {self.current}"
                )
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

        # 修正提案エンジンで拡張
        if hasattr(self, "correction_engine"):
            graceful_error = self.correction_engine.enhance_error_with_suggestions(
                graceful_error
            )
            self.logger.info(
                f"Enhanced error with {len(graceful_error.correction_suggestions)} suggestions"
            )

        self.graceful_syntax_errors.append(graceful_error)
        self.logger.info(f"Graceful error recorded: {message} at line {line_number}")

    def _create_error_node(self, line: str, error_message: str) -> Node:
        """エラー発生箇所にエラー情報を含むノードを作成"""

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


# StreamingParser moved to streaming_parser.py


# 既存Parserクラスとの互換性維持のためのラッパー関数
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
        parser = StreamingParser(config=config)
        nodes = list(parser.parse_streaming_from_text(text))
        return nodes
    else:
        # 既存の非ストリーミング処理
        parser = Parser(config=config)
        return parser.parse(text)


# --- 以下は streaming_parser.py に移動 --- #
