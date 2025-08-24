"""非同期パーサー処理システム

Issue #1170: パーサーの非同期処理調査・実装
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Union

from ..utilities.logger import get_logger
from .parser_events import ParserEvent, ParserEventType, get_parser_event_bus
from .event_driven_parser import EventDrivenParserMixin

logger = get_logger(__name__)


class AsyncParserMixin(EventDrivenParserMixin):
    """非同期パーサーミックスイン"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_enabled = True
        self._max_concurrent_tasks = 5
        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_concurrent_tasks)

    async def parse_async(self, content: Union[str, List[str]], **kwargs) -> Any:
        """非同期パース処理"""
        start_time = time.time()

        try:
            # 解析開始通知
            self.notify_parse_started(content, async_mode=True, **kwargs)

            # 非同期処理として実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._thread_pool, self._parse_sync_wrapper, content, kwargs
            )

            # 解析完了通知
            processing_time = time.time() - start_time
            self.notify_parse_completed(
                processing_time,
                {
                    "result_type": type(result).__name__,
                    "async_mode": True,
                    "success": True,
                },
            )

            return result

        except Exception as e:
            # エラー通知
            processing_time = time.time() - start_time
            is_critical = isinstance(e, (MemoryError, SystemError))

            self.notify_parse_error(
                e, is_critical, processing_time=processing_time, async_mode=True
            )
            raise

    def _parse_sync_wrapper(
        self, content: Union[str, List[str]], kwargs: Dict[str, Any]
    ) -> Any:
        """同期処理ラッパー（ThreadPoolExecutor用）"""
        return self.parse(content, **kwargs)

    async def parse_batch_async(
        self, contents: List[Union[str, List[str]]], **kwargs
    ) -> List[Any]:
        """バッチ非同期パース処理"""
        start_time = time.time()

        try:
            # バッチ処理開始通知
            event = ParserEvent(
                event_type=ParserEventType.PARSE_STARTED,
                data=self._create_event_data(
                    metadata={
                        "batch_size": len(contents),
                        "async_mode": True,
                        "batch_processing": True,
                    }
                ),
            )
            self._publish_event(event)

            # 並行処理
            tasks = []
            for i, content in enumerate(contents):
                task = asyncio.create_task(
                    self.parse_async(content, batch_index=i, **kwargs),
                    name=f"{self._parser_name}_batch_{i}",
                )
                tasks.append(task)

            # 全タスク完了待ち
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 結果とエラーの分離
            successful_results = []
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append((i, result))
                else:
                    successful_results.append(result)

            # バッチ処理完了通知
            processing_time = time.time() - start_time
            event = ParserEvent(
                event_type=ParserEventType.PARSE_COMPLETED,
                data=self._create_event_data(
                    processing_time=processing_time,
                    metadata={
                        "batch_size": len(contents),
                        "successful_count": len(successful_results),
                        "error_count": len(errors),
                        "async_mode": True,
                        "batch_processing": True,
                    },
                ),
            )
            self._publish_event(event)

            # エラーがある場合は通知
            if errors:
                for index, error in errors:
                    self.notify_parse_error(
                        error, False, batch_index=index, batch_processing=True
                    )

            return results

        except Exception as e:
            processing_time = time.time() - start_time
            self.notify_parse_error(
                e, True, processing_time=processing_time, batch_processing=True
            )
            raise

    def set_max_concurrent_tasks(self, max_tasks: int) -> None:
        """最大同時実行タスク数設定"""
        self._max_concurrent_tasks = max_tasks
        # ThreadPoolExecutorを再作成
        self._thread_pool.shutdown(wait=False)
        self._thread_pool = ThreadPoolExecutor(max_workers=max_tasks)

    def enable_async_mode(self) -> None:
        """非同期モード有効化"""
        self._async_enabled = True

    def disable_async_mode(self) -> None:
        """非同期モード無効化"""
        self._async_enabled = False


class AsyncParserOrchestrator:
    """非同期パーサーオーケストレーター"""

    def __init__(self):
        self._registered_parsers: Dict[str, Any] = {}
        self._event_bus = get_parser_event_bus()
        self._processing_queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []
        self._running = False

    def register_parser(self, name: str, parser: Any) -> None:
        """パーサー登録"""
        self._registered_parsers[name] = parser
        logger.debug(f"Async parser registered: {name}")

    async def start_workers(self, num_workers: int = 3) -> None:
        """ワーカー開始"""
        if self._running:
            return

        self._running = True

        for i in range(num_workers):
            task = asyncio.create_task(
                self._worker_loop(f"worker_{i}"), name=f"async_parser_worker_{i}"
            )
            self._worker_tasks.append(task)

        logger.info(f"Started {num_workers} async parser workers")

    async def stop_workers(self) -> None:
        """ワーカー停止"""
        self._running = False

        # 全ワーカータスクをキャンセル
        for task in self._worker_tasks:
            task.cancel()

        # タスク完了待ち
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        self._worker_tasks.clear()
        logger.info("Async parser workers stopped")

    async def _worker_loop(self, worker_name: str) -> None:
        """ワーカーループ"""
        logger.debug(f"Async parser worker started: {worker_name}")

        while self._running:
            try:
                # キューからタスク取得（タイムアウト付き）
                task_data = await asyncio.wait_for(
                    self._processing_queue.get(), timeout=1.0
                )

                parser_name = task_data["parser_name"]
                content = task_data["content"]
                kwargs = task_data.get("kwargs", {})
                future = task_data["future"]

                # パーサー実行
                try:
                    parser = self._registered_parsers.get(parser_name)
                    if not parser:
                        raise ValueError(f"Parser not found: {parser_name}")

                    if hasattr(parser, "parse_async"):
                        result = await parser.parse_async(content, **kwargs)
                    else:
                        # 同期パーサーを非同期で実行
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None, parser.parse, content, **kwargs
                        )

                    future.set_result(result)

                except Exception as e:
                    future.set_exception(e)

                finally:
                    self._processing_queue.task_done()

            except asyncio.TimeoutError:
                # キューが空の場合は継続
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")

        logger.debug(f"Async parser worker stopped: {worker_name}")

    async def parse_async(
        self, parser_name: str, content: Union[str, List[str]], **kwargs
    ) -> Any:
        """非同期パース要求"""
        if not self._running:
            raise RuntimeError("Async parser orchestrator not running")

        future = asyncio.Future()
        task_data = {
            "parser_name": parser_name,
            "content": content,
            "kwargs": kwargs,
            "future": future,
        }

        await self._processing_queue.put(task_data)
        return await future

    async def parse_with_multiple_parsers(
        self, parser_configs: List[Dict[str, Any]], content: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """複数パーサーによる並行処理"""
        start_time = time.time()

        # 並行タスク作成
        tasks = {}
        for config in parser_configs:
            parser_name = config["parser_name"]
            parser_kwargs = config.get("kwargs", {})

            task = asyncio.create_task(
                self.parse_async(parser_name, content, **parser_kwargs),
                name=f"multi_parser_{parser_name}",
            )
            tasks[parser_name] = task

        # 全タスク完了待ち
        results = {}
        errors = {}

        for parser_name, task in tasks.items():
            try:
                result = await task
                results[parser_name] = result
            except Exception as e:
                errors[parser_name] = str(e)

        processing_time = time.time() - start_time

        # 結果イベント発行
        event = ParserEvent(
            event_type=ParserEventType.PARSE_COMPLETED,
            data={
                "parser_name": "orchestrator",
                "parser_type": "multi_parser",
                "processing_time": processing_time,
                "metadata": {
                    "parsers_used": list(parser_configs),
                    "successful_parsers": list(results.keys()),
                    "failed_parsers": list(errors.keys()),
                    "multi_parser_mode": True,
                },
            },
        )
        self._event_bus.publish(event)

        return {
            "results": results,
            "errors": errors,
            "processing_time": processing_time,
            "success_count": len(results),
            "error_count": len(errors),
        }

    def get_queue_status(self) -> Dict[str, Any]:
        """キュー状態取得"""
        return {
            "queue_size": self._processing_queue.qsize(),
            "running": self._running,
            "active_workers": len(self._worker_tasks),
            "registered_parsers": list(self._registered_parsers.keys()),
        }


# グローバルオーケストレーター
_global_async_orchestrator: Optional[AsyncParserOrchestrator] = None


def get_async_orchestrator() -> AsyncParserOrchestrator:
    """グローバル非同期オーケストレーター取得"""
    global _global_async_orchestrator
    if _global_async_orchestrator is None:
        _global_async_orchestrator = AsyncParserOrchestrator()
    return _global_async_orchestrator


async def initialize_async_parsing(num_workers: int = 3) -> None:
    """非同期パーシング初期化"""
    orchestrator = get_async_orchestrator()
    await orchestrator.start_workers(num_workers)
    logger.info(f"Async parsing initialized with {num_workers} workers")
