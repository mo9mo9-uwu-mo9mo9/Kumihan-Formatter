"""並行処理テスト

並行処理環境での統合テストを実行する。
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import pytest

# pytest-asyncio が無い環境でテストをスキップ
try:
    import pytest_asyncio

    HAS_PYTEST_ASYNCIO = True
except ImportError:
    HAS_PYTEST_ASYNCIO = False

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestConcurrentProcessing:
    """並行処理テスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.test_data = {
            "simple": [
                "# 太字 #シンプル{}##",
                "# イタリック #テキスト{}##",
                "通常のテキスト{}",
            ],
            "complex": [
                "# 見出し{} ## 太字 #内容{}## ##",
                "# ルビ #漢字{}|かんじ## # 下線 #テキスト{}##",
                "- リスト{}\n  - ネスト{}",
            ],
            "edge_cases": [
                "# 太字 #",  # 不完全なタグ
                "##",  # 終了タグのみ
                "",  # 空文字列
            ],
        }

    def process_content_sync(self, content: str, worker_id: int) -> Dict[str, Any]:
        """同期的なコンテンツ処理"""
        start_time = time.time()
        thread_id = threading.current_thread().ident

        try:
            from kumihan_formatter.core.parsing.main_parser import MainParser
            from kumihan_formatter.renderer import MainRenderer

            # パース処理
            parser = MainParser()
            parsed = parser.parse(content)

            # レンダリング処理
            renderer = MainRenderer()
            html = renderer.render(parsed)

            elapsed = time.time() - start_time

            return {
                "success": True,
                "worker_id": worker_id,
                "thread_id": thread_id,
                "content": content,
                "html": html,
                "elapsed": elapsed,
                "timestamp": time.time(),
            }

        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "worker_id": worker_id,
                "thread_id": thread_id,
                "content": content,
                "error": str(e),
                "elapsed": elapsed,
                "timestamp": time.time(),
            }

    def test_スレッドプール並行処理(self) -> None:
        """ThreadPoolExecutorを使用した並行処理"""
        contents = []
        for category, patterns in self.test_data.items():
            for i, pattern in enumerate(patterns):
                if "{}" in pattern:
                    contents.append(pattern.format(i))
                else:
                    contents.append(pattern)

        max_workers = 4
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # タスクを提出
            futures = [
                executor.submit(self.process_content_sync, content, i)
                for i, content in enumerate(contents)
            ]

            # 結果を収集
            for future in futures:
                results.append(future.result())

        # 結果検証
        assert len(results) == len(contents)

        success_count = sum(1 for r in results if r["success"])
        error_count = len(results) - success_count

        # 統計情報
        thread_ids = set(r["thread_id"] for r in results)
        avg_time = sum(r["elapsed"] for r in results) / len(results)

        logger.info(f"並行処理結果: 成功 {success_count}, エラー {error_count}")
        logger.info(f"使用スレッド数: {len(thread_ids)}")
        logger.info(f"平均処理時間: {avg_time:.3f}秒")

        # 検証
        assert (
            success_count >= len(contents) * 0.8
        ), f"成功率が低い: {success_count}/{len(contents)}"
        assert len(thread_ids) <= max_workers, f"スレッド数が制限を超過: {len(thread_ids)}"

    @pytest.mark.skipif(not HAS_PYTEST_ASYNCIO, reason="pytest-asyncio is not installed")
    @pytest.mark.asyncio
    async def test_非同期並行処理(self) -> None:
        """asyncioを使用した非同期並行処理"""

        async def async_process(content: str, worker_id: int) -> Dict[str, Any]:
            """非同期処理ラッパー"""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.process_content_sync, content, worker_id)

        # テストデータ準備
        contents = []
        for patterns in self.test_data.values():
            for i, pattern in enumerate(patterns):
                if "{}" in pattern:
                    contents.append(pattern.format(i))
                else:
                    contents.append(pattern)

        # 非同期タスク作成
        tasks = [async_process(content, i) for i, content in enumerate(contents)]

        # 並行実行
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # 結果分析
        success_results = []
        error_results = []

        for result in results:
            if isinstance(result, Exception):
                error_results.append(str(result))
            elif isinstance(result, dict) and result.get("success"):
                success_results.append(result)
            else:
                error_results.append(result)

        logger.info(f"非同期並行処理: 成功 {len(success_results)}, エラー {len(error_results)}")
        logger.info(f"総処理時間: {total_time:.3f}秒")

        # 検証
        assert len(success_results) >= len(contents) * 0.8

    def test_スレッド安全性(self) -> None:
        """スレッド安全性のテスト"""
        import threading

        shared_data = {"counter": 0, "results": []}
        lock = threading.Lock()

        def worker_with_shared_data(content: str, worker_id: int):
            """共有データを使用するワーカー"""
            result = self.process_content_sync(content, worker_id)

            with lock:
                shared_data["counter"] += 1
                shared_data["results"].append(result)

            return result

        # 同じコンテンツを複数スレッドで処理
        content = "# 太字 #スレッド安全性テスト##"
        worker_count = 10

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(worker_with_shared_data, content, i) for i in range(worker_count)
            ]

            for future in futures:
                future.result()

        # 検証
        assert shared_data["counter"] == worker_count, "カウンターが正しくない"
        assert len(shared_data["results"]) == worker_count, "結果数が正しくない"

        # 全て成功していることを確認
        success_count = sum(1 for r in shared_data["results"] if r["success"])
        assert success_count == worker_count, f"失敗した処理: {worker_count - success_count}"

    def test_リソース競合回避(self) -> None:
        """リソース競合の回避テスト"""
        import os
        import tempfile
        from pathlib import Path

        # 一時ディレクトリ作成
        temp_dir = Path(tempfile.mkdtemp())

        def worker_with_file_io(content: str, worker_id: int):
            """ファイルI/Oを含むワーカー"""
            # 個別のファイルを使用してリソース競合を回避
            temp_file = temp_dir / f"worker_{worker_id}.tmp"

            try:
                # ファイルに書き込み
                temp_file.write_text(content, encoding="utf-8")

                # ファイルから読み込み
                read_content = temp_file.read_text(encoding="utf-8")

                # 処理実行
                result = self.process_content_sync(read_content, worker_id)

                # ファイル削除
                temp_file.unlink()

                return result

            except Exception as e:
                return {
                    "success": False,
                    "worker_id": worker_id,
                    "error": str(e),
                }

        # 並行実行
        contents = [f"# 太字 #ワーカー{i}##" for i in range(8)]

        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(worker_with_file_io, content, i)
                    for i, content in enumerate(contents)
                ]

                results = [future.result() for future in futures]

            # 結果検証
            success_count = sum(1 for r in results if r.get("success"))
            assert success_count == len(
                contents
            ), f"リソース競合で失敗: {len(contents) - success_count}"

        finally:
            # クリーンアップ
            import shutil

            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def test_デッドロック回避(self) -> None:
        """デッドロック回避のテスト"""
        import random
        import threading

        # 複数のロックを使用
        lock1 = threading.Lock()
        lock2 = threading.Lock()
        results = []

        def worker_with_multiple_locks(content: str, worker_id: int):
            """複数のロックを使用するワーカー（デッドロック回避のため順序固定）"""
            # デッドロック回避: 常に同じ順序でロックを取得
            locks = [lock1, lock2]

            try:
                # 短い待機でロック取得の順序をランダム化
                time.sleep(random.uniform(0.001, 0.01))

                with locks[0]:
                    with locks[1]:
                        # 処理実行
                        result = self.process_content_sync(content, worker_id)
                        results.append(result)

                        # クリティカルセクション内での処理時間をシミュレート
                        time.sleep(0.01)

                        return result

            except Exception as e:
                error_result = {
                    "success": False,
                    "worker_id": worker_id,
                    "error": str(e),
                }
                results.append(error_result)
                return error_result

        # 並行実行
        content = "# 太字 #デッドロックテスト##"
        worker_count = 6

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(worker_with_multiple_locks, content, i) for i in range(worker_count)
            ]

            # タイムアウト付きで結果を取得（デッドロックしないことを確認）
            completed_results = []
            for future in futures:
                try:
                    result = future.result(timeout=5.0)  # 5秒でタイムアウト
                    completed_results.append(result)
                except Exception as e:
                    completed_results.append(
                        {
                            "success": False,
                            "error": f"タイムアウトまたはエラー: {e}",
                        }
                    )

        # 検証
        assert len(completed_results) == worker_count, "タイムアウトでデッドロックが疑われます"
        assert len(results) == worker_count, "結果数が正しくない"

        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"デッドロック回避テスト: 成功 {success_count}/{worker_count}")

        # 少なくとも80%は成功することを期待
        assert success_count >= worker_count * 0.8
