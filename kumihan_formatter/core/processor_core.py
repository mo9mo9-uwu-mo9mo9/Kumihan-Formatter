"""
並列チャンク処理コア - 軽量化版
分離されたモジュールを統合する軽量なファサードクラス
"""

import concurrent.futures
import logging
import threading
from typing import Any, Callable, Dict, Iterator, List, Optional

from .chunk_manager import ChunkInfo, ChunkManager
from .processing_optimized import ProcessingOptimized


class ParallelChunkProcessor:
    """並列チャンク処理クラス - 軽量版（委譲パターン）"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        chunk_size: int = 1000,
    ):
        """並列チャンク処理初期化"""
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.chunk_size = chunk_size

        # 基本的なスレッド管理
        self._lock = threading.RLock()
        self._results_lock = threading.RLock()

        # 分離されたモジュールの初期化
        self.chunk_manager = ChunkManager(chunk_size=chunk_size)
        self.processing_optimized = ProcessingOptimized(max_workers=max_workers)

    # ===== 基本的な並列処理メソッド =====

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

    # ===== 最適化処理へのデリゲーション =====

    def process_chunks_parallel_optimized(
        self,
        chunks: List[ChunkInfo],
        processing_func: Callable[[ChunkInfo], Iterator[Any]],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Iterator[Any]:
        """最適化並列処理（委譲）"""
        return self.processing_optimized.process_chunks_parallel_optimized(
            chunks, processing_func, progress_callback
        )

    def get_parallel_metrics(self) -> Dict[str, Any]:
        """並列処理メトリクス取得（委譲）"""
        base_metrics = self.processing_optimized.get_parallel_metrics()
        base_metrics.update(
            {"chunk_size": self.chunk_size, "chunk_manager_status": "active"}
        )
        return base_metrics

    # ===== チャンク管理へのデリゲーション =====

    def create_chunks_from_lines(
        self, lines: List[str], chunk_size: int = None
    ) -> List[ChunkInfo]:
        """行リストからチャンク作成（委譲）"""
        return self.chunk_manager.create_chunks_from_lines(lines, chunk_size)

    def create_chunks_adaptive(
        self, lines: List[str], target_chunk_count: int = None
    ) -> List[ChunkInfo]:
        """適応的チャンク作成（委譲）"""
        return self.chunk_manager.create_chunks_adaptive(lines, target_chunk_count)

    def create_chunks_from_file(
        self, file_path, encoding: str = "utf-8"
    ) -> List[ChunkInfo]:
        """ファイルからチャンク作成（委譲）"""
        return self.chunk_manager.create_chunks_from_file(file_path, encoding)

    def merge_chunks(self, chunks: List[ChunkInfo]) -> List[str]:
        """チャンクマージ（委譲）"""
        return self.chunk_manager.merge_chunks(chunks)

    def get_chunk_info(self, chunks: List[ChunkInfo]) -> dict:
        """チャンク情報取得（委譲）"""
        return self.chunk_manager.get_chunk_info(chunks)

    def validate_chunks(self, chunks: List[ChunkInfo]) -> List[str]:
        """チャンク検証（委譲）"""
        return self.chunk_manager.validate_chunks(chunks)

    # ===== 互換性メソッド =====

    def _get_cpu_count(self) -> int:
        """CPU数取得（互換性のため残存）"""
        return self.chunk_manager._get_cpu_count()

    def _calculate_optimal_workers(self, chunk_count: int) -> int:
        """最適ワーカー数計算（委譲）"""
        return self.processing_optimized.calculate_optimal_workers(chunk_count)

    def _create_progress_info_optimized(
        self, completed: int, total: int, current_chunk: ChunkInfo
    ) -> Dict[str, Any]:
        """進捗情報作成（委譲）"""
        return self.processing_optimized.create_progress_info_optimized(
            completed, total, current_chunk
        )

    def _process_single_chunk_optimized(
        self,
        chunk: ChunkInfo,
        processing_func: Callable[[ChunkInfo], Iterator[Any]],
        perf_monitor: Any,
    ) -> List[Any]:
        """最適化処理（委譲）"""
        return self.processing_optimized.process_single_chunk_optimized(
            chunk, processing_func, perf_monitor
        )

    # ===== システム情報 =====

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            "processor_status": "active",
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "modules": {"chunk_manager": "loaded", "processing_optimized": "loaded"},
            "thread_count": threading.active_count(),
            "lock_status": "active",
        }

    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        self.logger.info("Cleaning up ParallelChunkProcessor resources")
        # 必要に応じてリソース解放処理を実装
