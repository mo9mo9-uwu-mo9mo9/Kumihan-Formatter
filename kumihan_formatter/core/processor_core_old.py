"""
並列チャンク処理システム - Issue #694 Phase 3対応
大容量ファイルの並列チャンク処理による更なる高速化
"""

import concurrent.futures
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

from .logger import get_logger


@dataclass
class ChunkInfo:
    """処理チャンク情報"""

    chunk_id: int
    start_line: int
    end_line: int
    lines: List[str]
    file_position: int = 0


class ParallelChunkProcessor:
    """
    並列チャンク処理システム

    特徴:
    - ThreadPoolExecutorによる並列処理
    - チャンク間の依存関係を考慮した安全な並列化
    - メモリ効率を維持した並列実行
    - プログレス追跡統合
    """

    def __init__(
        self, max_workers: Optional[int] = None, chunk_size: int = 100
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers or min(4, (threading.active_count() or 1) + 2)
        self.chunk_size = chunk_size

        # スレッドセーフティ
        self._lock = threading.Lock()
        self._results_lock = threading.Lock()

        self.logger.info(
            f"ParallelChunkProcessor initialized: {self.max_workers} workers, "
            f"chunk_size={chunk_size}"
        )

    def process_chunks_parallel(
        self,
        chunks: List[ChunkInfo],
        processing_func: Callable[[ChunkInfo], Iterator[Any]],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Iterator[Any]:
        """
        チャンクリストを並列処理

        Args:
            chunks: 処理対象チャンクリスト
            processing_func: チャンク処理関数
            progress_callback: プログレス更新コールバック

        Yields:
            Any: 処理結果
        """
        self.logger.info(f"Starting parallel processing of {len(chunks)} chunks")

        # 並列処理実行
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 全チャンクを並列で開始
            future_to_chunk = {
                executor.submit(
                    self._process_single_chunk, chunk, processing_func
                ): chunk
                for chunk in chunks
            }

            completed_chunks = 0

            # 完了順に結果を取得
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk = future_to_chunk[future]

                try:
                    results = future.result()

                    # 結果をyield（順序は保証されない）
                    for result in results:
                        yield result

                    completed_chunks += 1

                    # プログレス更新
                    if progress_callback:
                        progress_info = {
                            "completed_chunks": completed_chunks,
                            "total_chunks": len(chunks),
                            "chunk_id": chunk.chunk_id,
                            "progress_percent": (completed_chunks / len(chunks)) * 100,
                        }
                        progress_callback(progress_info)

                except Exception as e:
                    self.logger.error(f"Chunk {chunk.chunk_id} processing failed: {e}")
                    # エラーチャンクはスキップして継続
                    continue

        self.logger.info(
            f"Parallel processing completed: {completed_chunks}/{len(chunks)} chunks"
        )

    def process_chunks_parallel_optimized(
        self,
        chunks: List[ChunkInfo],
        processing_func: Callable[[ChunkInfo], Iterator[Any]],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Iterator[Any]:
        """
        最適化されたチャンクリスト並列処理（Issue #727 パフォーマンス最適化対応）

        改善点:
        - CPU効率最大化: ワーカー数動的調整
        - メモリ効率向上: 結果ストリーミング
        - 順序保証: チャンクIDベース結果ソート
        - エラー耐性強化: 個別チャンクエラーでも継続

        Args:
            chunks: 処理対象チャンクリスト
            processing_func: チャンク処理関数
            progress_callback: プログレス更新コールバック

        Yields:
            Any: 処理結果（順序保証付き）
        """
        self.logger.info(
            f"Starting optimized parallel processing: {len(chunks)} chunks"
        )

        if not chunks:
            return

        # 動的ワーカー数計算（CPU効率最大化）
        optimal_workers = self._calculate_optimal_workers(len(chunks))

        # 結果収集用の順序保証辞書
        results_dict = {}
        errors_dict = {}

        # パフォーマンス監視（簡易版）
        # performance_metricsモジュールが存在しないため、基本的なモニタリング実装を使用
        class SimplePerformanceMonitor:
            def __init__(self, name: str) -> None:
                self.name = name
                self.items_processed = 0

            def record_item_processed(self) -> None:
                self.items_processed += 1

            def __enter__(self) -> "SimplePerformanceMonitor":
                return self

            def __exit__(
                self,
                exc_type: Optional[type],
                exc_val: Optional[BaseException],
                exc_tb: Optional[Any],
            ) -> None:
                pass

        with SimplePerformanceMonitor("parallel_chunk_processing") as perf_monitor:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=optimal_workers
            ) as executor:

                # 全チャンクを並列で開始（最適化されたsubmit）
                future_to_chunk = {}
                for chunk in chunks:
                    future = executor.submit(
                        self._process_single_chunk_optimized,
                        chunk,
                        processing_func,
                        perf_monitor,
                    )
                    future_to_chunk[future] = chunk

                completed_chunks = 0

                # 完了順に結果を収集
                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk = future_to_chunk[future]

                    try:
                        results = future.result()
                        results_dict[chunk.chunk_id] = results

                        completed_chunks += 1

                        # プログレス更新（最適化）
                        if (
                            progress_callback and completed_chunks % 5 == 0
                        ):  # 更新頻度調整
                            progress_info = self._create_progress_info_optimized(
                                completed_chunks, len(chunks), chunk
                            )
                            progress_callback(progress_info)

                    except Exception as e:
                        error_msg = f"Chunk {chunk.chunk_id} processing failed: {e}"
                        self.logger.error(error_msg)
                        errors_dict[chunk.chunk_id] = error_msg
                        # エラーでも処理継続

                # 順序保証付き結果出力
                for chunk_id in sorted(results_dict.keys()):
                    for result in results_dict[chunk_id]:
                        yield result

        # 最終レポート
        success_count = len(results_dict)
        error_count = len(errors_dict)
        self.logger.info(
            f"Optimized parallel processing completed: "
            f"{success_count} success, {error_count} errors, "
            f"efficiency: {(success_count/(success_count+error_count)*100):.1f}%"
        )

    def _process_single_chunk_optimized(
        self,
        chunk: ChunkInfo,
        processing_func: Callable[[ChunkInfo], Iterator[Any]],
        perf_monitor: Any,
    ) -> List[Any]:
        """単一チャンクの最適化処理（効率向上版）"""

        try:
            # スレッドローカル情報でデバッグ改善
            thread_id = threading.get_ident()

            self.logger.debug(
                f"Thread {thread_id}: Processing chunk {chunk.chunk_id} "
                f"(lines {chunk.start_line}-{chunk.end_line})"
            )

            # 処理実行（結果を即座にリスト化してメモリ効率向上）
            results = []
            for result in processing_func(chunk):
                if result:  # None結果のフィルタリング
                    results.append(result)
                    # パフォーマンス監視にアイテム処理を記録
                    perf_monitor.record_item_processed()

            self.logger.debug(
                f"Thread {thread_id}: Chunk {chunk.chunk_id} completed "
                f"with {len(results)} results"
            )

            return results
        except Exception as e:
            self.logger.error(
                f"Thread {threading.get_ident()}: Error in chunk {chunk.chunk_id}: {e}",
                exc_info=True,
            )
            raise

    def _calculate_optimal_workers(self, chunk_count: int) -> int:
        """最適ワーカー数の動的計算"""

        # CPU コア数ベースの計算
        cpu_count = os.cpu_count() or 1

        # チャンク数に応じた調整
        if chunk_count <= 2:
            optimal = 1  # 少数チャンクは並列化不要
        elif chunk_count <= cpu_count:
            optimal = chunk_count  # チャンク数 ≤ CPU数
        else:
            # CPU集約的処理のため、CPU数+2を上限とする
            optimal = min(cpu_count + 2, self.max_workers or cpu_count + 2)

        # メモリ使用量も考慮（簡易版）
        try:
            import psutil

            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 80:  # メモリ使用率が高い場合は並列度を下げる
                optimal = max(1, optimal // 2)
        except ImportError:
            pass  # psutil未利用環境では無視

        self.logger.info(
            f"Calculated optimal workers: {optimal} "
            f"(chunks: {chunk_count}, CPU: {cpu_count})"
        )
        return optimal

    def _create_progress_info_optimized(
        self, completed: int, total: int, current_chunk: ChunkInfo
    ) -> dict[str, Any]:
        """最適化されたプログレス情報作成"""

        progress_percent = (completed / total) * 100 if total > 0 else 100

        return {
            "completed_chunks": completed,
            "total_chunks": total,
            "chunk_id": current_chunk.chunk_id,
            "progress_percent": progress_percent,
            "current_lines": f"{current_chunk.start_line}-{current_chunk.end_line}",
            "efficiency": "high" if progress_percent > 0 else "starting",
        }

    def create_chunks_adaptive(
        self, lines: List[str], target_chunk_count: Optional[int] = None
    ) -> List[ChunkInfo]:
        """
        適応的チャンク作成（処理量に応じてサイズ調整）

        Args:
            lines: 対象行リスト
            target_chunk_count: 目標チャンク数（Noneなら自動計算）

        Returns:
            List[ChunkInfo]: 最適化されたチャンクリスト
        """

        total_lines = len(lines)
        if total_lines == 0:
            return []

        # チャンクサイズの決定
        cpu_count = self._get_cpu_count()
        if total_lines <= 100:
            target_chunk_count = 1
        elif total_lines <= 1000:
            target_chunk_count = min(4, cpu_count)
        else:
            target_chunk_count = min(cpu_count * 2, 16)  # 最大16チャンク

        # 適応的チャンクサイズ計算
        adaptive_chunk_size = max(1, total_lines // target_chunk_count)

        self.logger.info(
            f"Adaptive chunking: {total_lines} lines → {target_chunk_count} chunks "
            f"(size: ~{adaptive_chunk_size})"
        )

        return self.create_chunks_from_lines(lines, adaptive_chunk_size)

    def get_parallel_metrics(self) -> dict[str, Any]:
        """並列処理メトリクスを取得"""
        return {
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "cpu_count": os.cpu_count(),
            "active_threads": threading.active_count(),
        }

    def _process_single_chunk(
        self, chunk: ChunkInfo, processing_func: Callable[[ChunkInfo], Iterator[Any]]
    ) -> List[Any]:
        """単一チャンクを処理（スレッドセーフ）"""
        try:
            with self._lock:
                self.logger.debug(
                    f"Processing chunk {chunk.chunk_id}: "
                    f"lines {chunk.start_line}-{chunk.end_line}"
                )

            results = list(processing_func(chunk))

            with self._lock:
                self.logger.debug(
                    f"Chunk {chunk.chunk_id} completed: {len(results)} results"
                )

            return results
        except Exception as e:
            self.logger.error(f"Error in chunk {chunk.chunk_id}: {e}")
            raise

    def create_chunks_from_lines(
        self, lines: List[str], chunk_size: Optional[int] = None
    ) -> List[ChunkInfo]:
        """行リストからチャンクを作成"""
        effective_chunk_size = chunk_size or self.chunk_size
        chunks: list[ChunkInfo] = []

        for i in range(0, len(lines), effective_chunk_size):
            chunk_lines = lines[i : i + effective_chunk_size]
            chunk = ChunkInfo(
                chunk_id=len(chunks),
                start_line=i,
                end_line=min(i + effective_chunk_size - 1, len(lines) - 1),
                lines=chunk_lines,
            )
            chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} chunks from {len(lines)} lines")
        return chunks

    def _get_cpu_count(self) -> int:
        """
        CPUコア数を取得

        Returns:
            int: CPUコア数
        """
        import os

        try:
            return os.cpu_count() or 4  # フォールバックとして 4
        except Exception:
            return 4

    def create_chunks_from_file(
        self, file_path: Path, chunk_size: Optional[int] = None
    ) -> List[ChunkInfo]:
        """ファイルからチャンクを作成（メモリ効率版）"""
        effective_chunk_size = chunk_size or self.chunk_size
        chunks: list[ChunkInfo] = []

        with open(file_path, "r", encoding="utf-8") as file:
            current_chunk_lines = []
            current_start_line = 0
            line_number = 0

            for line in file:
                current_chunk_lines.append(line.rstrip("\n"))
                line_number += 1

                if len(current_chunk_lines) >= effective_chunk_size:
                    # チャンク作成
                    chunk = ChunkInfo(
                        chunk_id=len(chunks),
                        start_line=current_start_line,
                        end_line=line_number - 1,
                        lines=current_chunk_lines.copy(),
                    )
                    chunks.append(chunk)

                    # 次のチャンク準備
                    current_chunk_lines.clear()
                    current_start_line = line_number

            # 残りの行でチャンク作成
            if current_chunk_lines:
                chunk = ChunkInfo(
                    chunk_id=len(chunks),
                    start_line=current_start_line,
                    end_line=line_number - 1,
                    lines=current_chunk_lines,
                )
                chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} chunks from file: {file_path}")
        return chunks
