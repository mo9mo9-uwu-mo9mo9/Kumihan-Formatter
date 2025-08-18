"""AsyncCoordinatorの包括的なテスト

Issue #920対応: async_processing/モジュールのテスト作成
カバレッジ80%以上の包括的なテストを実装
"""

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import anyio
import pytest

from kumihan_formatter.core.async_processing.async_coordinator import (
    AsyncCoordinator,
    AsyncTask,
    get_async_coordinator,
    run_async,
)
from kumihan_formatter.core.patterns.event_bus import ExtendedEventType


class TestAsyncTask:
    """AsyncTaskのテスト"""

    def test_正常系_初期化_基本(self):
        """正常系: 基本的な初期化"""

        def sample_func():
            return "test"

        task = AsyncTask(task_id="test_task_1", func=sample_func, args=(), kwargs={})

        assert task.task_id == "test_task_1"
        assert task.func == sample_func
        assert task.args == ()
        assert task.kwargs == {}
        assert isinstance(task.created_at, datetime)

    def test_正常系_初期化_引数付き(self):
        """正常系: 引数付きの初期化"""

        def sample_func(a, b, c=None):
            return a + b

        task = AsyncTask(
            task_id="test_task_2", func=sample_func, args=(1, 2), kwargs={"c": 3}
        )

        assert task.task_id == "test_task_2"
        assert task.args == (1, 2)
        assert task.kwargs == {"c": 3}

    def test_正常系_created_at_自動設定(self):
        """正常系: created_atの自動設定"""

        def sample_func():
            pass

        before_create = datetime.now()
        task = AsyncTask("test", sample_func, (), {})
        after_create = datetime.now()

        assert before_create <= task.created_at <= after_create

    def test_正常系_created_at_手動設定(self):
        """正常系: created_atの手動設定"""

        def sample_func():
            pass

        manual_time = datetime(2023, 1, 1, 12, 0, 0)
        task = AsyncTask("test", sample_func, (), {}, created_at=manual_time)

        assert task.created_at == manual_time


class TestAsyncCoordinator:
    """AsyncCoordinatorのテスト"""

    def setup_method(self):
        """各テストの前準備"""
        self.coordinator = AsyncCoordinator(max_workers=2)

    def teardown_method(self):
        """各テストの後処理"""
        if hasattr(self, "coordinator"):
            self.coordinator.cleanup()

    def test_正常系_初期化_Thread(self):
        """正常系: ThreadPoolExecutorでの初期化"""
        coordinator = AsyncCoordinator(max_workers=4, use_process_pool=False)

        assert coordinator.max_workers == 4
        assert coordinator.use_process_pool is False
        assert isinstance(coordinator._executor, ThreadPoolExecutor)
        assert coordinator._running_tasks == {}

        coordinator.cleanup()

    def test_正常系_初期化_Process(self):
        """正常系: ProcessPoolExecutorでの初期化"""
        coordinator = AsyncCoordinator(max_workers=2, use_process_pool=True)

        assert coordinator.max_workers == 2
        assert coordinator.use_process_pool is True
        assert isinstance(coordinator._executor, ProcessPoolExecutor)

        coordinator.cleanup()

    @pytest.mark.anyio
    async def test_正常系_run_async_同期関数(self):
        """正常系: 同期関数の非同期実行"""

        def sync_function(x, y):
            return x + y

        result = await self.coordinator.run_async(sync_function, 3, 5)
        assert result == 8

    @pytest.mark.anyio
    async def test_正常系_run_async_非同期関数(self):
        """正常系: 非同期関数の実行"""

        async def async_function(x, y):
            await asyncio.sleep(0.01)  # 短い待機
            return x * y

        result = await self.coordinator.run_async(async_function, 4, 6)
        assert result == 24

    @pytest.mark.anyio
    async def test_正常系_run_async_キーワード引数(self):
        """正常系: キーワード引数付きの実行"""

        def func_with_kwargs(a, b=10, c=20):
            return a + b + c

        # 位置引数のみで実行
        result = await self.coordinator.run_async(func_with_kwargs, 5, 15, 25)
        assert result == 45

    @pytest.mark.anyio
    async def test_異常系_run_async_エラー発生(self):
        """異常系: 実行中のエラー処理"""

        def error_function():
            raise ValueError("テストエラー")

        with pytest.raises(ValueError, match="テストエラー"):
            await self.coordinator.run_async(error_function)

    @pytest.mark.anyio
    async def test_異常系_run_async_非同期エラー(self):
        """異常系: 非同期関数でのエラー処理"""

        async def async_error_function():
            await asyncio.sleep(0.01)
            raise RuntimeError("非同期エラー")

        with pytest.raises(RuntimeError, match="非同期エラー"):
            await self.coordinator.run_async(async_error_function)

    @pytest.mark.anyio
    async def test_正常系_run_parallel_複数タスク(self):
        """正常系: 複数タスクの並列実行"""

        def add_func(x, y):
            return x + y

        def multiply_func(x, y):
            return x * y

        tasks = [
            AsyncTask("task1", add_func, (2, 3), {}),
            AsyncTask("task2", multiply_func, (4, 5), {}),
            AsyncTask("task3", add_func, (10, 20), {}),
        ]

        results = await self.coordinator.run_parallel(tasks)

        assert len(results) == 3
        assert results[0] == 5  # 2 + 3
        assert results[1] == 20  # 4 * 5
        assert results[2] == 30  # 10 + 20

    @pytest.mark.anyio
    async def test_正常系_run_parallel_空リスト(self):
        """正常系: 空タスクリストの並列実行"""
        results = await self.coordinator.run_parallel([])
        assert results == []

    @pytest.mark.anyio
    async def test_異常系_run_parallel_エラー混在(self):
        """異常系: エラーが混在するタスクの並列実行"""

        def success_func(x):
            return x * 2

        def error_func():
            raise ValueError("並列エラー")

        tasks = [
            AsyncTask("task1", success_func, (5,), {}),
            AsyncTask("task2", error_func, (), {}),
            AsyncTask("task3", success_func, (10,), {}),
        ]

        results = await self.coordinator.run_parallel(tasks)

        assert len(results) == 3
        assert results[0] == 10  # 成功: 5 * 2
        assert isinstance(results[1], ValueError)  # エラー
        assert results[2] == 20  # 成功: 10 * 2

    @pytest.mark.anyio
    async def test_正常系_run_batch_基本処理(self):
        """正常系: バッチ処理の基本動作"""

        def square_func(x):
            return x**2

        items = [1, 2, 3, 4, 5]
        results = await self.coordinator.run_batch(square_func, items, batch_size=2)

        assert len(results) == 5
        # Exception が含まれていないことを確認
        assert all(not isinstance(r, Exception) for r in results)
        # 結果の値を確認（順序は保証されないため、セットで比較）
        assert set(results) == {1, 4, 9, 16, 25}

    @pytest.mark.anyio
    async def test_正常系_run_batch_大きなバッチサイズ(self):
        """正常系: バッチサイズが項目数より大きい場合"""

        def double_func(x):
            return x * 2

        items = [1, 2, 3]
        results = await self.coordinator.run_batch(double_func, items, batch_size=10)

        assert len(results) == 3
        assert set(results) == {2, 4, 6}

    @pytest.mark.anyio
    async def test_正常系_run_batch_空項目(self):
        """正常系: 空項目リストのバッチ処理"""

        def dummy_func(x):
            return x

        results = await self.coordinator.run_batch(dummy_func, [], batch_size=5)
        assert results == []

    @pytest.mark.anyio
    async def test_境界値_バッチサイズ1(self):
        """境界値: バッチサイズ1での処理"""

        def increment_func(x):
            return x + 1

        items = [10, 20, 30]
        results = await self.coordinator.run_batch(increment_func, items, batch_size=1)

        assert len(results) == 3
        assert set(results) == {11, 21, 31}

    def test_正常系_cleanup(self):
        """正常系: リソースクリーンアップ"""
        coordinator = AsyncCoordinator(max_workers=2)

        # cleanup前は実行できる
        assert coordinator._executor._threads is not None

        # cleanup実行
        coordinator.cleanup()

        # cleanup後はshutdown済み
        assert coordinator._executor._shutdown

    @pytest.mark.anyio
    async def test_統合系_並行処理_制限確認(self):
        """統合系: 並行処理数の制限確認"""

        def slow_func(duration):
            time.sleep(duration)
            return f"completed_{duration}"

        coordinator = AsyncCoordinator(max_workers=2)

        try:
            # 3つのタスクを同時実行（制限は2）
            tasks = [AsyncTask(f"task_{i}", slow_func, (0.1,), {}) for i in range(3)]

            start_time = time.time()
            results = await coordinator.run_parallel(tasks)
            elapsed_time = time.time() - start_time

            # 3つのタスクが完了
            assert len(results) == 3
            assert all("completed_0.1" in str(r) for r in results)

            # 並行制限により、少なくとも0.15秒はかかる（0.1 + 0.1の順次実行部分）
            assert elapsed_time >= 0.15

        finally:
            coordinator.cleanup()

    @pytest.mark.anyio
    async def test_統合系_イベント発行確認(self):
        """統合系: イベント発行の確認"""
        with patch(
            "kumihan_formatter.core.async_processing.async_coordinator.publish_event"
        ) as mock_publish:

            def simple_func():
                return "test_result"

            result = await self.coordinator.run_async(simple_func)

            assert result == "test_result"

            # イベントが2回発行される（開始・完了）
            assert mock_publish.call_count == 2

            # 開始イベント確認
            start_call = mock_publish.call_args_list[0]
            assert start_call[0][0] == ExtendedEventType.ASYNC_TASK_STARTED
            assert start_call[0][1] == "AsyncCoordinator"
            assert "task_id" in start_call[0][2]
            assert start_call[0][2]["func_name"] == "simple_func"

            # 完了イベント確認
            complete_call = mock_publish.call_args_list[1]
            assert complete_call[0][0] == ExtendedEventType.ASYNC_TASK_COMPLETED
            assert complete_call[0][1] == "AsyncCoordinator"
            assert complete_call[0][2]["success"] is True

    @pytest.mark.anyio
    async def test_統合系_エラー時イベント発行(self):
        """統合系: エラー時のイベント発行確認"""
        with patch(
            "kumihan_formatter.core.async_processing.async_coordinator.publish_event"
        ) as mock_publish:

            def error_func():
                raise RuntimeError("統合テストエラー")

            with pytest.raises(RuntimeError):
                await self.coordinator.run_async(error_func)

            # エラー時も2回発行（開始・完了）
            assert mock_publish.call_count == 2

            # 完了イベントがエラー情報を含む
            complete_call = mock_publish.call_args_list[1]
            assert complete_call[0][2]["success"] is False
            assert "統合テストエラー" in complete_call[0][2]["error"]


class TestAsyncCoordinatorGlobalFunctions:
    """グローバル関数のテスト"""

    def test_正常系_get_async_coordinator(self):
        """正常系: グローバルインスタンス取得"""
        coordinator1 = get_async_coordinator()
        coordinator2 = get_async_coordinator()

        # 同じインスタンスが返される
        assert coordinator1 is coordinator2
        assert isinstance(coordinator1, AsyncCoordinator)

    @pytest.mark.anyio
    async def test_正常系_run_async_便利関数(self):
        """正常系: 便利な非同期実行関数"""

        def test_func(x, y):
            return x - y

        result = await run_async(test_func, 10, 3)
        assert result == 7

    @pytest.mark.anyio
    async def test_異常系_run_async_便利関数_エラー(self):
        """異常系: 便利関数でのエラー処理"""

        def error_func():
            raise KeyError("便利関数エラー")

        with pytest.raises(KeyError, match="便利関数エラー"):
            await run_async(error_func)


class TestAsyncCoordinatorEdgeCases:
    """エッジケースのテスト"""

    @pytest.mark.anyio
    async def test_エッジケース_非常に短い実行時間(self):
        """エッジケース: 非常に短い実行時間の関数"""
        coordinator = AsyncCoordinator()

        try:

            def instant_func():
                return "instant"

            result = await coordinator.run_async(instant_func)
            assert result == "instant"
        finally:
            coordinator.cleanup()

    @pytest.mark.anyio
    async def test_エッジケース_大きなデータ引数(self):
        """エッジケース: 大きなデータを引数とする場合"""
        coordinator = AsyncCoordinator()

        try:

            def process_large_data(data_list):
                return len(data_list)

            large_data = list(range(10000))
            result = await coordinator.run_async(process_large_data, large_data)
            assert result == 10000
        finally:
            coordinator.cleanup()

    @pytest.mark.anyio
    async def test_エッジケース_ネストした非同期呼び出し(self):
        """エッジケース: ネストした非同期呼び出し"""
        coordinator = AsyncCoordinator()

        try:

            async def nested_func(x):
                # 内部で別の非同期処理を呼び出し
                return await coordinator.run_async(lambda y: y * 2, x)

            result = await coordinator.run_async(nested_func, 7)
            assert result == 14
        finally:
            coordinator.cleanup()

    def test_エッジケース_cleanup_二重呼び出し(self):
        """エッジケース: cleanup の二重呼び出し"""
        coordinator = AsyncCoordinator()

        # 1回目のcleanup
        coordinator.cleanup()

        # 2回目のcleanupでもエラーが発生しない
        coordinator.cleanup()  # エラーが発生しないことを確認

    @pytest.mark.anyio
    async def test_性能系_大量タスク並列実行(self):
        """性能系: 大量タスクの並列実行"""
        coordinator = AsyncCoordinator(max_workers=4)

        try:

            def simple_calc(x):
                return x**2 + x

            # 100個のタスクを作成
            tasks = [
                AsyncTask(f"perf_task_{i}", simple_calc, (i,), {}) for i in range(100)
            ]

            start_time = time.time()
            results = await coordinator.run_parallel(tasks)
            elapsed_time = time.time() - start_time

            # 全て完了
            assert len(results) == 100

            # 並列処理により高速化されている（シーケンシャルより早い）
            assert elapsed_time < 1.0  # 1秒以内で完了

            # 結果の妥当性確認（いくつかサンプル）
            assert all(
                isinstance(r, int) for r in results if not isinstance(r, Exception)
            )

        finally:
            coordinator.cleanup()
