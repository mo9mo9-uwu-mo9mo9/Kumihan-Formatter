"""Memory Performance Tests

メモリ使用量とメモリ効率のパフォーマンステスト
"""

import gc
import sys
import time

import pytest

pytestmark = pytest.mark.performance


@pytest.mark.tdd_green
class TestMemoryPerformance:
    """メモリパフォーマンステスト"""

    @pytest.mark.unit
    def test_memory_allocation_patterns(self):
        """メモリ割り当てパターンのテスト"""
        # 小さなオブジェクトの大量作成
        start_time = time.time()
        small_objects = [{"id": i} for i in range(10000)]
        allocation_time = time.time() - start_time

        # メモリ使用量確認
        memory_usage = sys.getsizeof(small_objects)

        # クリーンアップ
        del small_objects
        gc.collect()

        # パフォーマンス基準
        assert allocation_time < 0.5  # 10000オブジェクトを0.5秒以内で作成
        assert memory_usage > 0

    @pytest.mark.slow
    def test_large_data_processing(self):
        """大データ処理テスト"""
        # 大きなデータ構造の作成
        large_data = {
            f"key_{i}": {"value": f"data_{i}", "metadata": {"index": i, "type": "test"}}
            for i in range(1000)
        }

        start_time = time.time()

        # データ処理
        processed_data = {}
        for key, value in large_data.items():
            if value["metadata"]["index"] % 2 == 0:
                processed_data[key] = value

        processing_time = time.time() - start_time

        # 結果確認
        assert len(processed_data) == 500  # 偶数インデックスのみ
        assert processing_time < 0.1  # 高速処理

    @pytest.mark.unit
    def test_memory_efficiency_comparison(self):
        """メモリ効率比較テスト"""
        # リスト vs ジェネレータの比較
        # リスト作成
        start_time = time.time()
        list_data = [i * 2 for i in range(10000)]
        list_time = time.time() - start_time
        list_memory = sys.getsizeof(list_data)

        # ジェネレータ作成
        start_time = time.time()
        gen_data = (i * 2 for i in range(10000))
        gen_time = time.time() - start_time
        gen_memory = sys.getsizeof(gen_data)

        # メモリ効率確認
        assert gen_memory < list_memory  # ジェネレータの方がメモリ効率が良い
        assert gen_time < list_time  # ジェネレータの方が作成が高速
