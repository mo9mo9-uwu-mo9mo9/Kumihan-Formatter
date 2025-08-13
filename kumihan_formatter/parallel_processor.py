"""Parallel processing logic for Kumihan parser - Issue #813 refactoring

This module contains parallel processing and streaming logic extracted from the
monolithic parser.py.
Handles chunked processing, memory monitoring, and performance optimization.
"""

import gc
import os
import time
from typing import Any, Callable, Iterator, Optional, cast

from .core.ast_nodes import Node
from .core.utilities.logger import get_logger


class ParallelProcessorHandler:
    """
    並列処理の特化ハンドラー

    担当範囲：
    - 並列ストリーミング処理
    - チャンク処理とメモリ監視
    - パフォーマンス最適化
    - ハイブリッド処理モード
    """

    def __init__(self, parser_instance: Any) -> None:
        """
        Args:
            parser_instance: メインParserインスタンス（依存注入）
        """
        self.parser = parser_instance
        self.logger = get_logger(__name__)

    def parse_parallel_streaming(
        self,
        text: str,
        progress_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> Iterator[Node]:
        """
        Issue #759対応: 並列処理×真のストリーミング統合実装
        """
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
            yield from self.parser.parse_streaming_from_text(text, progress_callback)
            return

        self.logger.info(
            f"Parallel processing enabled: {total_lines} lines, "
            f"estimated improvement: 60-80%"
        )

        # 並列処理状態
        self.parser._cancelled = False
        processed_nodes = 0

        try:
            # 適応的チャンク作成
            chunks = self.parser.parallel_processor.create_chunks_adaptive(
                lines, target_chunk_count=None  # 自動計算
            )

            if not chunks:
                raise Exception("Failed to create processing chunks")

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
                if not self.parser._cancelled and result:
                    yield result
                    processed_nodes += 1
                elif self.parser._cancelled:
                    self.logger.warning("Processing cancelled by user request")
                    break

                # 定期的なメモリ解放
                if processed_nodes % 1000 == 0:
                    gc.collect()

            # 最終プログレス更新
            if progress_callback and not self.parser._cancelled:
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
                f"in {elapsed_total:.2f}s ({total_lines / elapsed_total:.0f} lines/sec)"
            )

        except Exception as e:
            self.logger.error(f"Parallel processing error: {e}")
            # フォールバック: 最適化版パース
            self.logger.info("Falling back to optimized parse")
            yield from self.parser.parse_optimized(text)
        finally:
            # クリーンアップ
            self.parser._cancelled = False

    def _process_chunks_with_memory_monitoring(
        self,
        chunks: Any,
        chunk_progress_info: dict[str, Any],
        progress_callback: Any,
        start_time: float,
        total_lines: int,
    ) -> Iterator[Node]:
        """メモリ監視付きチャンク並列処理"""
        try:
            # メモリ監視の初期化
            memory_monitor = self._init_enhanced_memory_monitor()
            processed_chunks = 0

            # 並列処理実行
            for i, result in enumerate(
                self.parser.parallel_processor.process_chunks_parallel_optimized(
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
                if self.parser._cancelled:
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
                        gc.collect()

                        # メモリ状況再チェック
                        memory_status = memory_monitor.check_memory_status()
                        if memory_status["critical"]:
                            raise Exception(
                                f"Memory usage remains critical after cleanup: "
                                f"{memory_status['current_mb']:.1f}MB"
                            )

                    elif memory_status["warning"]:
                        self.logger.info(
                            f"High memory usage: {memory_status['current_mb']:.1f}MB, "
                            f"performing routine cleanup"
                        )
                        gc.collect()

        except Exception as e:
            self.logger.error(f"Memory monitoring error in parallel processing: {e}")
            raise Exception(f"Failed to monitor memory during parallel processing: {e}")

    def _init_enhanced_memory_monitor(self) -> Any:
        """拡張メモリ監視システムの初期化"""

        class EnhancedMemoryMonitor:
            def __init__(self) -> None:
                self.logger = get_logger(__name__)
                self.warning_threshold_mb = 150  # 150MB で警告
                self.critical_threshold_mb = 250  # 250MB で重大警告

            def get_current_memory_mb(self) -> float:
                """現在のメモリ使用量をMBで取得（エラーハンドリング強化）"""
                try:
                    import psutil

                    process = psutil.Process()
                    memory_info = process.memory_info()
                    return cast(float, memory_info.rss / 1024 / 1024)  # MB
                except Exception:
                    return 0.0  # フォールバック

            def check_memory_status(self) -> dict[str, Any]:
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

    def _parse_chunk_parallel_optimized(self, chunk: Any) -> Iterator[Node]:
        """単一チャンクの並列最適化解析（スレッドセーフ）"""
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

    def _get_thread_local_parser(self) -> Any:
        """スレッドローカルパーサーインスタンスを取得"""
        if not hasattr(self.parser._thread_local_storage, "parser"):
            # スレッド固有のパーサーインスタンスを作成
            from .parser import Parser  # 循環インポート回避

            self.parser._thread_local_storage.parser = Parser(
                config=self.parser.config, graceful_errors=self.parser.graceful_errors
            )

        return self.parser._thread_local_storage.parser

    def _should_use_parallel_processing(self, text: str, lines: list[str]) -> bool:
        """並列処理を使用すべきかを判定"""

        # ファイルサイズチェック
        text_size = len(text)
        line_count = len(lines)

        # 並列化の条件
        size_condition = text_size >= self.parser.parallel_threshold_size
        lines_condition = line_count >= self.parser.parallel_threshold_lines

        # CPU数チェック（最低2コア必要）
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

    def _update_parallel_progress(
        self,
        chunk_info: dict[str, Any],
        chunk_progress: dict[str, Any],
        progress_callback: Any,
        start_time: float,
        total_lines: int,
    ) -> None:
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

    def calculate_optimal_chunk_size(self, total_lines: int) -> int:
        """最適なチャンクサイズを計算（Issue #757パフォーマンス最適化）"""
        # ファイルサイズに応じた動的チャンクサイズ
        if total_lines <= 1000:
            return 100  # 小ファイル: 100行/チャンク
        elif total_lines <= 10000:
            return 500  # 中ファイル: 500行/チャンク
        else:
            return 1000  # 大ファイル: 1000行/チャンク

    def parse_chunk_optimized(
        self, chunk_text: str, start_line: int, end_line: int
    ) -> list[Node]:
        """チャンク解析の最適化実装（Issue #757）"""
        try:
            # Issue #755対応: 最適化されたパーサーを使用
            return cast(list[Node], self.parser.parse_optimized(chunk_text))
        except Exception as e:
            self.logger.error(f"Chunk parsing failed: {e}")
            return []

    def get_parallel_processing_metrics(self) -> dict[str, Any]:
        """並列処理のパフォーマンスメトリクスを取得（Issue #759コードレビュー対応）"""
        metrics = {
            # システム情報
            "system_info": {
                "cpu_count": os.cpu_count() or 1,
                "parallel_threshold_lines": self.parser.parallel_threshold_lines,
                "parallel_threshold_size": self.parser.parallel_threshold_size,
                "memory_limit_mb": self.parser.parallel_config.memory_critical_threshold_mb,
            },
            # 設定情報
            "configuration": {
                "chunk_min_size": self.parser.parallel_config.min_chunk_size,
                "chunk_max_size": self.parser.parallel_config.max_chunk_size,
                "memory_monitoring": self.parser.parallel_config.enable_memory_monitoring,
                "gc_optimization": self.parser.parallel_config.enable_gc_optimization,
                "timeout_seconds": self.parser.parallel_config.processing_timeout_seconds,
            },
            # 実行時統計
            "runtime_stats": {
                "current_lines": (
                    len(self.parser.lines) if hasattr(self.parser, "lines") else 0
                ),
                "errors_count": (
                    len(self.parser.errors) if hasattr(self.parser, "errors") else 0
                ),
                "graceful_errors_count": (
                    len(self.parser.graceful_syntax_errors)
                    if hasattr(self.parser, "graceful_syntax_errors")
                    else 0
                ),
            },
            # メモリ統計
            "memory_stats": self._get_memory_statistics(),
            # 並列処理統計
            "parallel_stats": (
                self._get_parallel_statistics()
                if hasattr(self.parser, "parallel_processor")
                else {}
            ),
        }

        return metrics

    def _get_memory_statistics(self) -> dict[str, Any]:
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

    def _get_parallel_statistics(self) -> dict[str, Any]:
        """並列処理統計を取得"""
        try:
            # 並列プロセッサーから統計を取得
            if hasattr(self.parser.parallel_processor, "get_statistics"):
                return cast(
                    dict[Any, Any], self.parser.parallel_processor.get_statistics()
                )

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
    ) -> None:
        """パフォーマンスサマリーをログ出力（Issue #759対応）"""
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
            f"並列処理: {'有効' if total_lines >= self.parser.parallel_threshold_lines else '無効'}\n"
            f"CPU数: {metrics['system_info']['cpu_count']}コア\n"
            f"エラー: {metrics['runtime_stats']['errors_count']}件\n"
            f"==============================="
        )
