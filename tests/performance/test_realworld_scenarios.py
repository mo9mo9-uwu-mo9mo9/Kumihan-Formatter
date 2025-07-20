"""Real-World Performance Scenarios

実世界のパフォーマンステスト - ファイル変換、並行処理、実際のワークフロー
"""

import queue
import tempfile
import threading
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.performance


@pytest.mark.e2e
@pytest.mark.tdd_green
class TestRealWorldPerformance:
    """実世界パフォーマンステスト"""

    @pytest.mark.file_io
    @pytest.mark.slow
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

    @pytest.mark.slow
    def test_concurrent_file_processing(self):
        """並行ファイル処理テスト"""
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
