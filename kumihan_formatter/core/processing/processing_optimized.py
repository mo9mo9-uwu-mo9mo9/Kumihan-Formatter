"""
並列処理最適化機能
processor_core.py分割版 - 高度なパフォーマンス最適化専用モジュール
"""

import concurrent.futures
import logging
import os
import threading
from typing import Any, Callable, Dict, Iterator, List, Optional

from ..types import ChunkInfo


class ProcessingOptimized:
    """並列処理最適化クラス"""

    def __init__(self, max_workers: Optional[int] = None):
        """並列処理最適化初期化"""
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self._lock = threading.RLock()
        self._results_lock = threading.RLock()

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
        optimal_workers = self.calculate_optimal_workers(len(chunks))

        # 結果収集用の順序保証辞書
        results_dict = {}
        errors_dict = {}

        # パフォーマンス監視（簡易版）
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
                        self.process_single_chunk_optimized,
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
                            progress_info = self.create_progress_info_optimized(
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

    def process_single_chunk_optimized(
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

    def calculate_optimal_workers(self, chunk_count: int) -> int:
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

    def create_progress_info_optimized(
        self, completed: int, total: int, current_chunk: ChunkInfo
    ) -> Dict[str, Any]:
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

    def get_parallel_metrics(self) -> Dict[str, Any]:
        """並列処理メトリクス取得"""
        return {
            "max_workers": self.max_workers,
            "cpu_count": os.cpu_count(),
            "memory_info": self._get_memory_info(),
            "thread_count": threading.active_count(),
        }

    def _get_memory_info(self) -> Dict[str, Any]:
        """メモリ情報取得"""
        try:

            memory = psutil.virtual_memory()
            return {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
            }
        except ImportError:
            return {"status": "psutil_not_available"}

    def _get_cpu_count(self) -> int:
        """CPU数取得（フォールバック付き）"""
        try:
            return os.cpu_count() or 1
        except Exception:
            return 1
