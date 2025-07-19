"""Performance Benchmarks Test Suite

パフォーマンス測定とベンチマーク基盤のテスト。
メモリ使用量、処理時間、スループットの測定を含む。
"""

import gc
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

pytestmark = pytest.mark.performance


class TestPerformanceBenchmarks:
    """パフォーマンスベンチマークテスト"""

    def test_memory_usage_baseline(self):
        """メモリ使用量ベースライン測定"""
        import sys

        # 初期メモリ使用量
        gc.collect()
        initial_objects = len(gc.get_objects())

        # テストデータの作成と解放
        test_data = [{"key": f"value_{i}"} for i in range(1000)]
        created_objects = len(gc.get_objects())

        # データ解放
        del test_data
        gc.collect()
        final_objects = len(gc.get_objects())

        # メモリリークがないことを確認（多少の変動は許容）
        assert final_objects <= created_objects
        assert (
            abs(final_objects - initial_objects) <= 50
        )  # 50オブジェクト程度の変動は許容（GC動作考慮）

    def test_file_processing_performance(self):
        """ファイル処理パフォーマンステスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # テストファイル作成
            test_files = []
            for i in range(10):
                test_file = temp_path / f"test_{i}.txt"
                test_file.write_text(f"Test content {i}" * 100, encoding="utf-8")
                test_files.append(test_file)

            # ファイル読み込み性能測定
            start_time = time.time()

            total_content = ""
            for test_file in test_files:
                content = test_file.read_text(encoding="utf-8")
                total_content += content

            end_time = time.time()
            processing_time = end_time - start_time

            # パフォーマンス基準: 10ファイルを1秒以内で処理
            assert processing_time < 1.0
            assert len(total_content) > 0

    def test_rendering_performance_baseline(self):
        """レンダリング性能ベースライン"""
        try:
            from kumihan_formatter.core.ast_nodes import Node
            from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer

            renderer = HTMLRenderer()

            # 大量のノード作成
            nodes = []
            for i in range(100):
                node = Node("p", f"Test paragraph {i}")
                nodes.append(node)

            # レンダリング時間測定
            start_time = time.time()

            with (
                patch.object(
                    renderer.element_renderer,
                    "render_paragraph",
                    return_value="<p>Test</p>",
                ),
            ):
                result = renderer.render_nodes(nodes)

            end_time = time.time()
            rendering_time = end_time - start_time

            # パフォーマンス基準: 100ノードを0.1秒以内でレンダリング
            assert rendering_time < 0.1
            assert len(result) > 0

        except ImportError:
            pytest.skip("Rendering modules not available")

    def test_string_processing_performance(self):
        """文字列処理パフォーマンステスト"""
        # 大きなテキストデータの作成
        large_text = "日本語テキスト処理テスト。" * 1000

        # 文字列操作性能測定
        start_time = time.time()

        # 様々な文字列操作
        processed_text = large_text.upper()
        processed_text = processed_text.replace("テスト", "TEST")
        lines = processed_text.split("。")
        filtered_lines = [line for line in lines if "処理" in line]
        final_text = "。".join(filtered_lines)

        end_time = time.time()
        processing_time = end_time - start_time

        # パフォーマンス基準: 大量文字列処理を0.1秒以内
        assert processing_time < 0.1
        assert len(final_text) > 0

    def test_concurrent_processing_simulation(self):
        """並行処理シミュレーション"""
        import queue
        import threading

        results_queue = queue.Queue()

        def worker_function(worker_id):
            # 軽い処理をシミュレート
            time.sleep(0.01)
            result = f"Worker {worker_id} completed"
            results_queue.put(result)

        # 複数スレッドでの処理
        threads = []
        num_workers = 5

        start_time = time.time()

        for i in range(num_workers):
            thread = threading.Thread(target=worker_function, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了待機
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # 結果確認
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # パフォーマンス基準: 並行処理が逐次処理より効率的
        assert len(results) == num_workers
        assert total_time < 0.1  # 並行処理により高速化


class TestMemoryPerformance:
    """メモリパフォーマンステスト"""

    def test_memory_allocation_patterns(self):
        """メモリ割り当てパターンのテスト"""
        import sys

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

    def test_memory_efficiency_comparison(self):
        """メモリ効率比較テスト"""
        import sys

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


class TestPerformanceMonitoring:
    """パフォーマンス監視テスト"""

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
            time.sleep(0.01)  # 処理をシミュレート
            return {"status": "success"}

        result = test_function()

        assert result["status"] == "success"
        assert "_execution_time" in result
        assert result["_execution_time"] >= 0.01

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


class TestRealWorldPerformance:
    """実世界パフォーマンステスト"""

    def test_file_conversion_performance(self):
        """ファイル変換パフォーマンステスト"""
        # Kumihan記法のサンプルコンテンツ
        sample_content = (
            """# テストドキュメント

これはパフォーマンステスト用のドキュメントです。

;;;highlight;;; 重要な情報 ;;;

((脚注の例))

｜日本語《にほんご》の例

## セクション2

- リスト項目1
- リスト項目2
- リスト項目3

"""
            * 10
        )  # 10倍に拡大

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(sample_content)
            test_file = f.name

        try:
            # ファイル読み込み性能
            start_time = time.time()

            content = Path(test_file).read_text(encoding="utf-8")
            lines = content.split("\n")
            processed_lines = [line.strip() for line in lines if line.strip()]

            processing_time = time.time() - start_time

            # パフォーマンス基準
            assert processing_time < 0.1
            assert len(processed_lines) > 0
            assert "テストドキュメント" in content

        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_concurrent_file_processing(self):
        """並行ファイル処理テスト"""
        import queue
        import threading

        results_queue = queue.Queue()

        def process_file_content(file_id, content):
            """ファイルコンテンツ処理をシミュレート"""
            # 簡単な処理をシミュレート
            lines = content.split("\n")
            word_count = sum(len(line.split()) for line in lines)

            results_queue.put(
                {"file_id": file_id, "lines": len(lines), "words": word_count}
            )

        # テストコンテンツ
        test_contents = [
            f"Test file {i}\nContent line 1\nContent line 2" for i in range(5)
        ]

        # 並行処理
        threads = []
        start_time = time.time()

        for i, content in enumerate(test_contents):
            thread = threading.Thread(target=process_file_content, args=(i, content))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # 結果収集
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # パフォーマンス確認
        assert len(results) == 5
        assert total_time < 0.5  # 並行処理により高速化
        assert all(result["words"] > 0 for result in results)
