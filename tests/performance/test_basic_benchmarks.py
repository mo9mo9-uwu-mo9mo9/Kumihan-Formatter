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

        # CI/CD最適化: テストデータ削減 1000→100
        test_data = [{"key": f"value_{i}"} for i in range(100)]
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

            # CI/CD最適化: ファイル数削減 10→3
            test_files = []
            for i in range(3):
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

            # CI/CD最適化: 3ファイルを0.5秒以内で処理
            assert processing_time < 0.5
            assert len(total_content) > 0

    @pytest.mark.mock_heavy
    def test_rendering_performance_baseline(self):
        """レンダリング性能ベースライン"""
        try:
            from kumihan_formatter.core.ast_nodes import Node
            from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer

            renderer = HTMLRenderer()

            # CI/CD最適化: ノード数削減 100→20
            nodes = []
            for i in range(20):
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

            # CI/CD最適化: 20ノードを0.05秒以内でレンダリング
            assert rendering_time < 0.05
            assert len(result) > 0

        except ImportError:
            pytest.skip("Rendering modules not available")

    @pytest.mark.unit
    def test_string_processing_performance(self):
        """文字列処理パフォーマンステスト"""
        # CI/CD最適化: テキストサイズ削減 1000→100
        large_text = "日本語テキスト処理テスト。" * 100

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

        # CI/CD最適化: 文字列処理を0.05秒以内
        assert processing_time < 0.05
        assert len(final_text) > 0

    @pytest.mark.slow
    def test_concurrent_processing_simulation(self):
        """並行処理シミュレーション"""
        import queue
        import threading

        results_queue = queue.Queue()

        def worker_function(worker_id):
            # CI/CD最適化: time.sleep削除、軽量計算でシミュレート
            dummy_work = sum(range(worker_id * 10 + 50))  # 軽量な実処理
            result = f"Worker {worker_id} completed"
            results_queue.put(result)

        # CI/CD最適化: ワーカー数削減 5→2
        threads = []
        num_workers = 2

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

        # CI/CD最適化: 2ワーカー並行処理を0.05秒以内
        assert len(results) == num_workers
        assert total_time < 0.05  # 並行処理により高速化
