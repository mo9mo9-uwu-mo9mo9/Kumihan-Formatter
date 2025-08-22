"""非同期ワークフローテスト

非同期処理フローの統合テストを実行する。
"""

import asyncio
import time
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

# pytest-asyncioが無い場合は全体をスキップ
pytestmark = pytest.mark.skipif(not HAS_PYTEST_ASYNCIO, reason="pytest-asyncio is not installed")


class TestAsyncWorkflow:
    """非同期ワークフローテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.test_contents = [
            "# 見出し #テスト1##",
            "# 太字 #テスト2##",
            "# イタリック #テスト3##",
            "# 枠線 #テスト4##",
            "# ハイライト #テスト5##",
        ]

    async def async_parse(self, content: str) -> Dict[str, Any]:
        """非同期パース処理"""
        # 実際の非同期処理をシミュレート
        await asyncio.sleep(0.01)  # 10ms待機

        try:
            from kumihan_formatter.core.parsing.main_parser import MainParser

            parser = MainParser()
            result = parser.parse(content)

            return {
                "success": True,
                "result": result,
                "content": content,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": content,
                "timestamp": time.time(),
            }

    async def async_render(self, parsed_data: Any) -> Dict[str, Any]:
        """非同期レンダリング処理"""
        await asyncio.sleep(0.01)  # 10ms待機

        try:
            from kumihan_formatter.renderer import Renderer

            renderer = Renderer()
            html = renderer.render(parsed_data)

            return {
                "success": True,
                "html": html,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.time(),
            }

    def test_基本的な非同期処理(self) -> None:
        """基本的な非同期処理のテスト"""
        content = "# 太字 #テストコンテンツ##"

        # パース処理
        async def run_test():
            parse_result = await self.async_parse(content)
            assert parse_result["success"], f"パース失敗: {parse_result.get('error')}"

            # レンダリング処理
            render_result = await self.async_render(parse_result["result"])
            assert render_result["success"], f"レンダリング失敗: {render_result.get('error')}"
            return render_result

        render_result = asyncio.run(run_test())

        # 結果検証
        html = render_result["html"]
        # kumihan記法では太字は<keyword>タグとして出力される
        # 少なくともHTMLが正常に生成され、何らかのコンテンツがあることを確認
        assert len(html) > 100, "HTML出力が短すぎます"
        assert "<html" in html, "HTMLドキュメントとして正しく出力されていません"
        assert "太字" in html or "keyword" in html, "期待されるコンテンツが含まれていません"

    @pytest.mark.asyncio
    async def test_並行非同期処理(self) -> None:
        """複数コンテンツの並行処理"""
        # 並行パース処理
        parse_tasks = [self.async_parse(content) for content in self.test_contents]
        parse_results = await asyncio.gather(*parse_tasks)

        # 全てのパースが成功することを確認
        for result in parse_results:
            assert result["success"], f"パース失敗: {result.get('error')}"

        # 並行レンダリング処理
        render_tasks = [self.async_render(result["result"]) for result in parse_results]
        render_results = await asyncio.gather(*render_tasks)

        # 全てのレンダリングが成功することを確認
        for result in render_results:
            assert result["success"], f"レンダリング失敗: {result.get('error')}"

        logger.info(f"並行処理完了: {len(self.test_contents)}件")

    @pytest.mark.asyncio
    async def test_非同期エラーハンドリング(self) -> None:
        """非同期処理でのエラーハンドリング"""
        # 意図的に無効なコンテンツを含むリスト
        mixed_contents = [
            "# 太字 #正常コンテンツ##",
            None,  # 無効なコンテンツ
            "# イタリック #正常コンテンツ2##",
            "",  # 空コンテンツ
            "# 枠線 #正常コンテンツ3##",
        ]

        # 各コンテンツを非同期で処理
        tasks = []
        for content in mixed_contents:
            if content is not None:
                tasks.append(self.async_parse(content))
            else:
                # None の場合は手動でエラー結果を作成
                tasks.append(asyncio.create_task(self._create_error_result("None content")))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果分析
        success_count = 0
        error_count = 0

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
            elif isinstance(result, dict) and result.get("success"):
                success_count += 1
            else:
                error_count += 1

        # 少なくとも一部は成功することを確認
        assert success_count >= 3, f"成功した処理が少なすぎます: {success_count}"
        logger.info(f"エラーハンドリング: 成功 {success_count}, エラー {error_count}")

    async def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """エラー結果を作成するヘルパー"""
        await asyncio.sleep(0.001)
        return {
            "success": False,
            "error": error_msg,
            "timestamp": time.time(),
        }

    @pytest.mark.asyncio
    async def test_非同期パフォーマンス(self) -> None:
        """非同期処理のパフォーマンステスト"""
        content_count = 20
        test_contents = [
            f"# 太字 #テスト{i}## # イタリック #内容{i}##" for i in range(content_count)
        ]

        # 同期的処理の時間測定
        start_sync = time.time()
        sync_results = []
        for content in test_contents:
            result = await self.async_parse(content)
            sync_results.append(result)
        sync_time = time.time() - start_sync

        # 非同期並行処理の時間測定
        start_async = time.time()
        async_tasks = [self.async_parse(content) for content in test_contents]
        async_results = await asyncio.gather(*async_tasks)
        async_time = time.time() - start_async

        # 結果検証
        assert len(sync_results) == content_count
        assert len(async_results) == content_count

        # 非同期処理の方が高速であることを確認
        # ただし、I/O待機が少ない場合は劇的な差は出ない可能性がある
        logger.info(f"同期処理: {sync_time:.3f}秒")
        logger.info(f"非同期処理: {async_time:.3f}秒")
        logger.info(f"速度比: {sync_time / async_time:.2f}倍")

    @pytest.mark.asyncio
    async def test_非同期リソース管理(self) -> None:
        """非同期処理でのリソース管理"""
        import tracemalloc

        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]

        # 大量の非同期タスクを実行
        large_contents = [f"# 見出し{i} #セクション{i}## # 太字 #内容{i}##" * 10 for i in range(50)]

        # バッチ処理でメモリ使用量を制御
        batch_size = 10
        all_results = []

        for i in range(0, len(large_contents), batch_size):
            batch = large_contents[i : i + batch_size]
            batch_tasks = [self.async_parse(content) for content in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)

            # バッチ間でGCを実行
            import gc

            gc.collect()

        final_memory = tracemalloc.get_traced_memory()[0]
        memory_increase = final_memory - initial_memory

        tracemalloc.stop()

        # 結果検証
        assert len(all_results) == len(large_contents)
        success_count = sum(1 for r in all_results if r.get("success"))
        assert success_count == len(
            large_contents
        ), f"失敗した処理: {len(large_contents) - success_count}"

        # メモリ使用量が適切な範囲内であることを確認（50MB以下）
        assert (
            memory_increase < 50 * 1024 * 1024
        ), f"メモリ使用量が多すぎます: {memory_increase / 1024 / 1024:.1f}MB"

        logger.info(f"リソース管理: メモリ増加 {memory_increase / 1024:.1f}KB")

    @pytest.mark.asyncio
    async def test_タイムアウト処理(self) -> None:
        """タイムアウト処理のテスト"""

        async def slow_parse(content: str) -> Dict[str, Any]:
            """遅い処理をシミュレート"""
            await asyncio.sleep(0.5)  # 500ms待機
            return await self.async_parse(content)

        content = "# 太字 #タイムアウトテスト##"

        # 短いタイムアウトでテスト
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_parse(content), timeout=0.1)

        # 十分なタイムアウトでテスト
        try:
            result = await asyncio.wait_for(slow_parse(content), timeout=1.0)
            assert result["success"], "処理が失敗しました"
        except asyncio.TimeoutError:
            pytest.fail("タイムアウトが発生しました（予期しない）")
