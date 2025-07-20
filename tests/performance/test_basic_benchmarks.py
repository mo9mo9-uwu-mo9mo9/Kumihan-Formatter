"""Basic Performance Benchmarks

基本的なパフォーマンステスト - メモリ使用量、ファイル処理、レンダリング、文字列処理
"""

import gc
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

pytestmark = pytest.mark.performance


@pytest.mark.tdd_green
class TestPerformanceBenchmarks:
    """パフォーマンスベンチマークテスト"""

    @pytest.mark.unit
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

    @pytest.mark.file_io
    @pytest.mark.slow
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

    @pytest.mark.mock_heavy
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

    @pytest.mark.unit
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

    @pytest.mark.slow
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
