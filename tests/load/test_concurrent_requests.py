"""並行リクエストの負荷テスト

高負荷環境でのシステムの安定性を検証する。
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestConcurrentRequests:
    """並行リクエストテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.test_input = "# 見出し #これはテストです##"
        self.max_workers = 10
        self.request_count = 50

    def process_request(self, request_id: int) -> tuple[int, float, bool]:
        """単一リクエストを処理"""
        start_time = time.time()
        try:
            from kumihan_formatter.core.parsing.main_parser import MainParser

            parser = MainParser()
            result = parser.parse(self.test_input)
            elapsed = time.time() - start_time
            return request_id, elapsed, result is not None
        except Exception as e:
            logger.error(f"リクエスト {request_id} 処理エラー: {e}")
            elapsed = time.time() - start_time
            return request_id, elapsed, False

    def test_並行リクエスト_基本(self) -> None:
        """基本的な並行リクエスト処理"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.process_request, i)
                for i in range(self.request_count)
            ]
            
            results = []
            for future in futures:
                results.append(future.result())
        
        # 検証
        success_count = sum(1 for _, _, success in results if success)
        assert success_count == self.request_count, f"失敗したリクエスト: {self.request_count - success_count}"
        
        # パフォーマンス統計
        times = [elapsed for _, elapsed, _ in results]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        logger.info(f"平均処理時間: {avg_time:.3f}秒")
        logger.info(f"最大処理時間: {max_time:.3f}秒")
        
        # 許容範囲のチェック
        assert avg_time < 0.1, f"平均処理時間が遅すぎます: {avg_time:.3f}秒"
        assert max_time < 1.0, f"最大処理時間が遅すぎます: {max_time:.3f}秒"

    def test_並行リクエスト_メモリリーク確認(self) -> None:
        """並行処理時のメモリリーク確認"""
        import gc
        import tracemalloc
        
        tracemalloc.start()
        gc.collect()
        
        # ベースラインメモリ使用量
        snapshot1 = tracemalloc.take_snapshot()
        
        # 負荷テスト実行
        with ThreadPoolExecutor(max_workers=5) as executor:
            for batch in range(3):
                futures = [
                    executor.submit(self.process_request, i)
                    for i in range(20)
                ]
                for future in futures:
                    future.result()
                gc.collect()
        
        # 最終メモリ使用量
        snapshot2 = tracemalloc.take_snapshot()
        
        # メモリ差分確認
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_diff = sum(stat.size_diff for stat in top_stats)
        
        # 許容範囲内か確認（10MB以下）
        assert total_diff < 10 * 1024 * 1024, f"メモリリークの可能性: {total_diff / 1024 / 1024:.2f}MB"
        
        tracemalloc.stop()

    def test_非同期並行リクエスト(self) -> None:
        """非同期での並行リクエスト処理"""
        async def async_process(request_id: int) -> tuple[int, float, bool]:
            """非同期処理"""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.process_request, request_id)
        
        # 非同期タスク作成と実行
        async def run_async_tasks():
            tasks = [async_process(i) for i in range(30)]
            return await asyncio.gather(*tasks)
        
        results = asyncio.run(run_async_tasks())
        
        # 検証
        success_count = sum(1 for _, _, success in results if success)
        assert success_count == 30, f"失敗したリクエスト: {30 - success_count}"

    def test_段階的負荷増加(self) -> None:
        """段階的に負荷を増加させるテスト"""
        worker_counts = [1, 5, 10, 20]
        results_by_workers: List[List[float]] = []
        
        for workers in worker_counts:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(self.process_request, i)
                    for i in range(20)
                ]
                
                times = []
                for future in futures:
                    _, elapsed, _ = future.result()
                    times.append(elapsed)
                
                avg_time = sum(times) / len(times)
                results_by_workers.append(times)
                logger.info(f"ワーカー数 {workers}: 平均 {avg_time:.3f}秒")
        
        # スケーラビリティの検証
        # ワーカー数が増えても極端にパフォーマンスが劣化しないこと
        for i in range(1, len(worker_counts)):
            prev_avg = sum(results_by_workers[i-1]) / len(results_by_workers[i-1])
            curr_avg = sum(results_by_workers[i]) / len(results_by_workers[i])
            
            # 2倍以上遅くならないこと
            assert curr_avg < prev_avg * 2, (
                f"ワーカー数増加でパフォーマンス劣化: "
                f"{worker_counts[i-1]}→{worker_counts[i]}: "
                f"{prev_avg:.3f}秒→{curr_avg:.3f}秒"
            )