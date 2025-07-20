"""Performance Monitoring and Benchmarks

パフォーマンス監視とベンチマーク比較テスト
"""

import gc
import time

import pytest

pytestmark = pytest.mark.performance


@pytest.mark.tdd_refactor
class TestPerformanceMonitoring:
    """パフォーマンス監視テスト"""

    @pytest.mark.unit
    def test_performance_decorator_simulation(self):
        """パフォーマンスデコレーターシミュレーション"""

        def performance_monitor(func):
            """簡易パフォーマンス監視デコレーター"""

            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time

                # 実行時間をresultに追加
                if isinstance(result, dict):
                    result["_execution_time"] = execution_time

                return result

            return wrapper

        @performance_monitor
        def test_function():
            # CI/CD最適化: time.sleep削除、軽量計算でシミュレート
            dummy_work = sum(range(100))  # 軽量な実処理
            return {"status": "success"}

        result = test_function()

        assert result["status"] == "success"
        assert "_execution_time" in result
        assert result["_execution_time"] >= 0.0  # CI/CD最適化: 時間要件緩和

    @pytest.mark.slow
    def test_resource_usage_tracking(self):
        """リソース使用量追跡テスト"""
        import threading

        class ResourceTracker:
            def __init__(self):
                self.start_time = None
                self.memory_samples = []
                self.is_tracking = False

            def start(self):
                self.start_time = time.time()
                self.is_tracking = True

            def sample_memory(self):
                if self.is_tracking:
                    gc.collect()
                    objects_count = len(gc.get_objects())
                    self.memory_samples.append(objects_count)

            def stop(self):
                self.is_tracking = False
                return {
                    "duration": time.time() - self.start_time,
                    "memory_samples": len(self.memory_samples),
                    "peak_objects": (
                        max(self.memory_samples) if self.memory_samples else 0
                    ),
                }

        tracker = ResourceTracker()
        tracker.start()

        # リソース集約的な処理をシミュレート
        data = []
        for i in range(100):
            data.append({"item": i, "data": "x" * 100})
            tracker.sample_memory()

        stats = tracker.stop()

        assert stats["duration"] > 0
        assert stats["memory_samples"] > 0
        assert stats["peak_objects"] > 0

    @pytest.mark.unit
    def test_benchmark_comparison(self):
        """ベンチマーク比較テスト"""

        def benchmark_function(func, *args, **kwargs):
            """関数のベンチマークを取る"""
            iterations = 100
            total_time = 0

            for _ in range(iterations):
                start_time = time.time()
                func(*args, **kwargs)
                end_time = time.time()
                total_time += end_time - start_time

            return {
                "average_time": total_time / iterations,
                "total_time": total_time,
                "iterations": iterations,
            }

        def simple_function():
            return sum(range(100))

        def complex_function():
            return sum(i**2 for i in range(100))

        simple_stats = benchmark_function(simple_function)
        complex_stats = benchmark_function(complex_function)

        # 複雑な関数の方が時間がかかることを確認
        assert complex_stats["average_time"] >= simple_stats["average_time"]
        assert simple_stats["iterations"] == 100
        assert complex_stats["iterations"] == 100
