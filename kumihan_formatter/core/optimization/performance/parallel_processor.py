"""
並列処理最適化システム - Issue #922 Phase 4-6対応
複数コア活用による高速並列処理システム
"""

import asyncio
import multiprocessing as mp
import os
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from kumihan_formatter.core.utilities.logger import get_logger

T = TypeVar("T")
R = TypeVar("R")


class TaskType(Enum):
    """タスクの種類を定義"""

    CPU_BOUND = auto()  # CPUバウンドタスク
    IO_BOUND = auto()  # IOバウンドタスク
    HYBRID = auto()  # ハイブリッドタスク


@dataclass
class TaskInfo:
    """タスク情報"""

    task_id: str
    task_type: TaskType
    priority: int = 0
    estimated_time: float = 0.0
    memory_requirement: int = 0  # MB
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkerStats:
    """ワーカー統計情報"""

    worker_id: str
    tasks_completed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    error_count: int = 0
    last_active: float = 0.0


class ParallelOptimizedProcessor:
    """
    並列処理最適化プロセッサー

    機能:
    - マルチコア活用によるCPUバウンドタスク最適化
    - スレッドプール/プロセスプールの動的切り替え
    - タスク負荷分散とワークスティーリング
    - メモリ効率的な並列処理
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        enable_process_pool: bool = True,
        enable_thread_pool: bool = True,
        memory_limit_mb: int = 1024,
    ) -> None:
        """
        並列処理プロセッサーの初期化

        Args:
            max_workers: 最大ワーカー数（None: CPU数と同じ）
            enable_process_pool: プロセスプール使用フラグ
            enable_thread_pool: スレッドプール使用フラグ
            memory_limit_mb: メモリ制限（MB）
        """
        self.logger = get_logger(__name__)

        # ワーカー数の決定
        self.cpu_count = os.cpu_count() or 4
        self.max_workers = max_workers or self.cpu_count
        self.memory_limit_mb = memory_limit_mb

        # プール設定
        self.enable_process_pool = enable_process_pool
        self.enable_thread_pool = enable_thread_pool

        # プールインスタンス
        self._process_pool: Optional[ProcessPoolExecutor] = None
        self._thread_pool: Optional[ThreadPoolExecutor] = None

        # 統計情報
        self._worker_stats: Dict[str, WorkerStats] = {}
        self._task_queue: List[TaskInfo] = []
        self._completed_tasks: List[str] = []

        # 同期プリミティブ
        self._stats_lock = threading.Lock()
        self._queue_lock = threading.Lock()

        self.logger.info(
            f"Parallel processor initialized: {self.max_workers} workers, "
            f"CPU count: {self.cpu_count}, Memory limit: {self.memory_limit_mb}MB"
        )

    def _get_process_pool(self) -> Optional[ProcessPoolExecutor]:
        """プロセスプールを取得（遅延初期化）"""
        if self._process_pool is None and self.enable_process_pool:
            self._process_pool = ProcessPoolExecutor(
                max_workers=self.max_workers,
                mp_context=mp.get_context("spawn"),  # macOS対応
            )
            self.logger.debug(f"Process pool created with {self.max_workers} workers")
        return self._process_pool

    def _get_thread_pool(self) -> Optional[ThreadPoolExecutor]:
        """スレッドプールを取得（遅延初期化）"""
        if self._thread_pool is None and self.enable_thread_pool:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
            self.logger.debug(f"Thread pool created with {self.max_workers} workers")
        return self._thread_pool

    def determine_optimal_strategy(
        self, task_info: TaskInfo, data_size: int
    ) -> Tuple[TaskType, str]:
        """
        タスクに最適な並列化戦略を決定

        Args:
            task_info: タスク情報
            data_size: データサイズ（バイト）

        Returns:
            Tuple[TaskType, str]: タスクタイプと推奨戦略
        """
        # メモリ使用量チェック
        memory_usage_mb = data_size / (1024 * 1024)

        # CPUバウンドタスクの判定条件
        if task_info.task_type == TaskType.CPU_BOUND:
            if memory_usage_mb > self.memory_limit_mb / self.max_workers:
                return TaskType.CPU_BOUND, "process_pool_sequential"
            else:
                return TaskType.CPU_BOUND, "process_pool_parallel"

        # IOバウンドタスクの判定条件
        elif task_info.task_type == TaskType.IO_BOUND:
            return TaskType.IO_BOUND, "thread_pool_parallel"

        # ハイブリッドタスクの判定
        else:
            if memory_usage_mb > self.memory_limit_mb / 2:
                return TaskType.HYBRID, "mixed_strategy_sequential"
            else:
                return TaskType.HYBRID, "mixed_strategy_parallel"

    def process_parallel(
        self,
        data_chunks: List[T],
        processing_func: Callable[[T], R],
        task_info: Optional[TaskInfo] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[R]:
        """
        データを並列処理

        Args:
            data_chunks: 処理対象データチャンク
            processing_func: 処理関数
            task_info: タスク情報
            progress_callback: プログレス更新コールバック

        Returns:
            List[R]: 処理結果リスト
        """
        if not data_chunks:
            return []

        task_info = task_info or TaskInfo(
            task_id=f"parallel_task_{int(time.time())}", task_type=TaskType.CPU_BOUND
        )

        start_time = time.time()
        total_chunks = len(data_chunks)

        # 最適戦略決定
        data_size = sum(len(str(chunk)) for chunk in data_chunks)
        task_type, strategy = self.determine_optimal_strategy(task_info, data_size)

        self.logger.info(f"Processing {total_chunks} chunks using strategy: {strategy}")

        try:
            if "process_pool" in strategy:
                results = self._process_with_process_pool(
                    data_chunks, processing_func, progress_callback
                )
            elif "thread_pool" in strategy:
                results = self._process_with_thread_pool(
                    data_chunks, processing_func, progress_callback
                )
            else:  # mixed strategy
                results = self._process_with_mixed_strategy(
                    data_chunks, processing_func, progress_callback
                )

            # 統計情報更新
            processing_time = time.time() - start_time
            self._update_task_stats(task_info.task_id, processing_time, len(results))

            self.logger.info(
                f"Parallel processing completed: {len(results)} results in "
                f"{processing_time:.2f}s using {strategy}"
            )

            return results

        except Exception as e:
            self.logger.error(f"Parallel processing failed: {e}")
            self._update_task_stats(
                task_info.task_id, time.time() - start_time, 0, error=True
            )
            raise

    def _process_with_process_pool(
        self,
        data_chunks: List[T],
        processing_func: Callable[[T], R],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[R]:
        """プロセスプールでの並列処理"""
        pool = self._get_process_pool()
        if pool is None:
            raise RuntimeError("Process pool not available")

        results: List[R] = []
        completed = 0
        total = len(data_chunks)

        # Future提出
        future_to_index = {
            pool.submit(processing_func, chunk): i
            for i, chunk in enumerate(data_chunks)
        }

        # 結果収集
        results = [None] * total  # type: ignore

        for future in as_completed(future_to_index):
            try:
                index = future_to_index[future]
                results[index] = future.result()
                completed += 1

                if progress_callback:
                    progress_callback(completed / total)

            except Exception as e:
                self.logger.warning(f"Process task failed: {e}")
                completed += 1

                if progress_callback:
                    progress_callback(completed / total)

        return [r for r in results if r is not None]

    def _process_with_thread_pool(
        self,
        data_chunks: List[T],
        processing_func: Callable[[T], R],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[R]:
        """スレッドプールでの並列処理"""
        pool = self._get_thread_pool()
        if pool is None:
            raise RuntimeError("Thread pool not available")

        results: List[R] = []
        completed = 0
        total = len(data_chunks)

        # Future提出
        future_to_index = {
            pool.submit(processing_func, chunk): i
            for i, chunk in enumerate(data_chunks)
        }

        # 結果収集
        results = [None] * total  # type: ignore

        for future in as_completed(future_to_index):
            try:
                index = future_to_index[future]
                results[index] = future.result()
                completed += 1

                if progress_callback:
                    progress_callback(completed / total)

            except Exception as e:
                self.logger.warning(f"Thread task failed: {e}")
                completed += 1

                if progress_callback:
                    progress_callback(completed / total)

        return [r for r in results if r is not None]

    def _process_with_mixed_strategy(
        self,
        data_chunks: List[T],
        processing_func: Callable[[T], R],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[R]:
        """混合戦略での並列処理"""
        # データサイズに基づいて分割
        chunk_size = len(data_chunks) // 2
        cpu_chunks = data_chunks[:chunk_size]
        io_chunks = data_chunks[chunk_size:]

        results: List[R] = []

        # CPUバウンドタスクをプロセスプールで処理
        if cpu_chunks and self.enable_process_pool:
            cpu_results = self._process_with_process_pool(
                cpu_chunks, processing_func, None
            )
            results.extend(cpu_results)

        # IOバウンドタスクをスレッドプールで処理
        if io_chunks and self.enable_thread_pool:
            io_results = self._process_with_thread_pool(
                io_chunks, processing_func, None
            )
            results.extend(io_results)

        if progress_callback:
            progress_callback(1.0)

        return results

    async def process_async(
        self,
        data_chunks: List[T],
        async_processing_func: Callable[[T], Any],
        task_info: Optional[TaskInfo] = None,
    ) -> List[R]:
        """
        非同期並列処理

        Args:
            data_chunks: 処理対象データチャンク
            async_processing_func: 非同期処理関数
            task_info: タスク情報

        Returns:
            List[R]: 処理結果リスト
        """
        if not data_chunks:
            return []

        task_info = task_info or TaskInfo(
            task_id=f"async_task_{int(time.time())}", task_type=TaskType.IO_BOUND
        )

        start_time = time.time()

        try:
            # 非同期タスク作成
            tasks = [async_processing_func(chunk) for chunk in data_chunks]

            # 非同期実行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # エラーハンドリング
            valid_results: List[R] = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Async task {i} failed: {result}")
                elif result is not None:
                    valid_results.append(result)  # type: ignore[arg-type]

            processing_time = time.time() - start_time
            self._update_task_stats(
                task_info.task_id, processing_time, len(valid_results)
            )

            self.logger.info(
                f"Async processing completed: {len(valid_results)} results in "
                f"{processing_time:.2f}s"
            )

            return valid_results

        except Exception as e:
            self.logger.error(f"Async processing failed: {e}")
            self._update_task_stats(
                task_info.task_id, time.time() - start_time, 0, error=True
            )
            raise

    def process_large_file(
        self,
        file_path: Path,
        chunk_processor: Callable[[str], R],
        chunk_size: int = 1024 * 1024,  # 1MB
        task_info: Optional[TaskInfo] = None,
    ) -> List[R]:
        """
        大型ファイルの並列処理

        Args:
            file_path: ファイルパス
            chunk_processor: チャンク処理関数
            chunk_size: チャンクサイズ（バイト）
            task_info: タスク情報

        Returns:
            List[R]: 処理結果リスト
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        task_info = task_info or TaskInfo(
            task_id=f"file_task_{file_path.name}_{int(time.time())}",
            task_type=TaskType.HYBRID,
        )

        self.logger.info(
            f"Processing large file: {file_path} (chunk size: {chunk_size})"
        )

        # ファイルをチャンクに分割
        chunks: List[str] = []
        with open(file_path, "r", encoding="utf-8") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)

        # 並列処理実行
        return self.process_parallel(chunks, chunk_processor, task_info)

    def _update_task_stats(
        self,
        task_id: str,
        processing_time: float,
        result_count: int,
        error: bool = False,
    ) -> None:
        """タスク統計情報を更新"""
        with self._stats_lock:
            if task_id not in self._worker_stats:
                self._worker_stats[task_id] = WorkerStats(worker_id=task_id)

            stats = self._worker_stats[task_id]
            stats.tasks_completed += 1
            stats.total_processing_time += processing_time
            stats.average_processing_time = (
                stats.total_processing_time / stats.tasks_completed
            )
            stats.last_active = time.time()

            if error:
                stats.error_count += 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        パフォーマンス統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        with self._stats_lock:
            total_tasks = sum(
                stats.tasks_completed for stats in self._worker_stats.values()
            )
            total_errors = sum(
                stats.error_count for stats in self._worker_stats.values()
            )
            avg_processing_time = (
                sum(
                    stats.average_processing_time
                    for stats in self._worker_stats.values()
                )
                / len(self._worker_stats)
                if self._worker_stats
                else 0.0
            )

            return {
                "cpu_count": self.cpu_count,
                "max_workers": self.max_workers,
                "memory_limit_mb": self.memory_limit_mb,
                "total_tasks_completed": total_tasks,
                "total_errors": total_errors,
                "error_rate": total_errors / total_tasks if total_tasks > 0 else 0.0,
                "average_processing_time": avg_processing_time,
                "worker_stats": {
                    worker_id: {
                        "tasks_completed": stats.tasks_completed,
                        "total_processing_time": stats.total_processing_time,
                        "average_processing_time": stats.average_processing_time,
                        "error_count": stats.error_count,
                        "last_active": stats.last_active,
                    }
                    for worker_id, stats in self._worker_stats.items()
                },
                "pool_status": {
                    "process_pool_enabled": self.enable_process_pool,
                    "thread_pool_enabled": self.enable_thread_pool,
                    "process_pool_active": self._process_pool is not None,
                    "thread_pool_active": self._thread_pool is not None,
                },
            }

    def shutdown(self, wait: bool = True) -> None:
        """
        プロセッサーのシャットダウン

        Args:
            wait: 実行中タスクの完了を待機するかどうか
        """
        self.logger.info("Shutting down parallel processor")

        # プロセスプール終了
        if self._process_pool is not None:
            self._process_pool.shutdown(wait=wait)
            self._process_pool = None
            self.logger.debug("Process pool shutdown completed")

        # スレッドプール終了
        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=wait)
            self._thread_pool = None
            self.logger.debug("Thread pool shutdown completed")

        self.logger.info("Parallel processor shutdown completed")

    def __enter__(self) -> "ParallelOptimizedProcessor":
        """コンテキストマネージャー対応"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """コンテキストマネージャー対応"""
        self.shutdown(wait=True)

    def __del__(self) -> None:
        """デストラクタでリソース解放を保証"""
        try:
            self.shutdown(wait=False)
        except Exception:
            pass  # デストラクタでの例外は無視
