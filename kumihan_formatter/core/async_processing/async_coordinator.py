"""非同期処理コーディネーター

Issue #914 Phase 3: 非同期・並列処理基盤
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from ..patterns.event_bus import ExtendedEventType, get_event_bus, publish_event
from ..utilities.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


@dataclass
class AsyncTask:
    """非同期タスク"""

    task_id: str
    func: Callable[..., Any]
    args: tuple
    kwargs: dict
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()


class AsyncCoordinator:
    """非同期処理コーディネーター"""

    def __init__(self, max_workers: int = 4, use_process_pool: bool = False) -> None:
        self.event_bus = get_event_bus()
        self.max_workers = max_workers
        self.use_process_pool = use_process_pool

        if use_process_pool:
            self._executor: Union[ProcessPoolExecutor, ThreadPoolExecutor] = (
                ProcessPoolExecutor(max_workers=max_workers)
            )
        else:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)

        self._running_tasks: Dict[str, asyncio.Task[Any]] = {}

    async def run_async(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """関数を非同期実行"""
        task_id = f"task_{datetime.now().timestamp()}"

        # 開始イベント
        publish_event(
            ExtendedEventType.ASYNC_TASK_STARTED,
            "AsyncCoordinator",
            {"task_id": task_id, "func_name": func.__name__},
        )

        try:
            # asyncio.create_task でイベントループで実行
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # 同期関数は別スレッドで実行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor, func, *args, **kwargs
                )

            # 完了イベント
            publish_event(
                ExtendedEventType.ASYNC_TASK_COMPLETED,
                "AsyncCoordinator",
                {"task_id": task_id, "success": True},
            )

            return cast(T, result)

        except Exception as e:
            # エラーイベント
            publish_event(
                ExtendedEventType.ASYNC_TASK_COMPLETED,
                "AsyncCoordinator",
                {"task_id": task_id, "success": False, "error": str(e)},
            )
            raise

    async def run_parallel(self, tasks: List[AsyncTask]) -> List[Any]:
        """複数タスクの並列実行"""
        async_tasks = []

        for task in tasks:
            async_task = self.run_async(task.func, *task.args, **task.kwargs)
            async_tasks.append(async_task)

        return await asyncio.gather(*async_tasks, return_exceptions=True)

    async def run_batch(
        self, func: Callable[[Any], Any], items: List[Any], batch_size: int = 10
    ) -> List[Any]:
        """バッチ処理実行"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_tasks = [
                AsyncTask(f"batch_{i}_{j}", func, (item,), {})
                for j, item in enumerate(batch)
            ]

            batch_results = await self.run_parallel(batch_tasks)
            results.extend(batch_results)

        return results

    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        try:
            self._executor.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Executor shutdown error: {e}")


# グローバル非同期コーディネーター
_global_async_coordinator = AsyncCoordinator()


def get_async_coordinator() -> AsyncCoordinator:
    """グローバル非同期コーディネーター取得"""
    return _global_async_coordinator


async def run_async(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """便利な非同期実行関数"""
    return await _global_async_coordinator.run_async(func, *args, **kwargs)
