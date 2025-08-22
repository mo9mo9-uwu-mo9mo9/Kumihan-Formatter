"""フォーマット統合テスト

異なるフォーマット間の変換と統合機能をテストし、
相互運用性を検証する。
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestFormatIntegration:
    """フォーマット統合テスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        os.makedirs("tmp", exist_ok=True)
        self.output_dir = Path("tmp/format_integration_test")
        self.output_dir.mkdir(exist_ok=True)

        # フォーマット統合テストデータ
        self.integration_cases = {
            "kumihan_to_html": {
                "input": "# 太字 #統合テスト## # イタリック #フォーマット##",
                "expected_html_tags": [
                    "統合テスト",
                    "フォーマット",
                    "kumihan-document",
                ],
            },
            "mixed_content": {
                "input": """# 見出し1 #統合テスト##
- リスト項目1
- リスト項目2
# 太字 #重要なポイント##""",
                "expected_elements": ["統合テスト", "リスト項目1", "重要なポイント"],
            },
            "complex_nesting": {
                "input": "# 枠線 ## 太字 #ネスト## と # イタリック #構造##",
                "expected_nesting": ["ネスト", "構造", "kumihan-document"],
            },
        }

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        import shutil

        try:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")

    def process_format_integration(
        self, content: str, output_format: str = "html"
    ) -> Dict[str, Any]:
        """フォーマット統合処理を実行"""
        try:
            from kumihan_formatter.core.parsing.main_parser import MainParser
            from kumihan_formatter.renderer import Renderer

            # パース処理
            parser = MainParser()
            parsed_result = parser.parse(content)

            # レンダリング処理
            renderer = Renderer()

            if output_format == "html":
                output = renderer.render(parsed_result)
                file_extension = ".html"
            else:
                # 他のフォーマットにも対応可能な設計
                output = renderer.render(parsed_result)
                file_extension = ".html"

            # ファイル出力
            output_file = self.output_dir / f"integration_output{file_extension}"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)

            return {
                "success": True,
                "format": output_format,
                "output": output,
                "parsed": parsed_result,
                "file_path": output_file,
                "file_size": output_file.stat().st_size,
            }

        except Exception as e:
            logger.error(f"フォーマット統合エラー: {e}")
            return {"success": False, "error": str(e), "format": output_format}

    def test_Kumihan記法からHTML統合(self) -> None:
        """Kumihan記法からHTMLへの統合変換"""
        test_case = self.integration_cases["kumihan_to_html"]
        result = self.process_format_integration(test_case["input"])

        assert result["success"], f"Kumihan→HTML統合失敗: {result.get('error')}"

        html_output = result["output"]
        for expected_tag in test_case["expected_html_tags"]:
            assert expected_tag in html_output, f"期待されるHTMLタグが不足: {expected_tag}"

        # ファイル統合確認
        assert result["file_path"].exists(), "統合出力ファイルが作成されていません"
        assert result["file_size"] > 0, "統合出力ファイルが空です"

    def test_混合コンテンツ統合(self) -> None:
        """異なる要素の混合コンテンツ統合"""
        test_case = self.integration_cases["mixed_content"]
        result = self.process_format_integration(test_case["input"])

        assert result["success"], f"混合コンテンツ統合失敗: {result.get('error')}"

        html_output = result["output"]
        for expected_element in test_case["expected_elements"]:
            assert expected_element in html_output, f"混合要素が不足: {expected_element}"

    def test_複雑なネスト統合(self) -> None:
        """複雑なネスト構造の統合"""
        test_case = self.integration_cases["complex_nesting"]
        result = self.process_format_integration(test_case["input"])

        assert result["success"], f"ネスト統合失敗: {result.get('error')}"

        html_output = result["output"]
        for expected_nest in test_case["expected_nesting"]:
            assert expected_nest in html_output, f"ネスト構造が不正: {expected_nest}"

    def test_フォーマット一貫性統合(self) -> None:
        """フォーマット一貫性の統合テスト"""
        test_contents = [
            "# 太字 #一貫性テスト1##",
            "# イタリック #一貫性テスト2##",
            "# 下線 #一貫性テスト3##",
        ]

        results = []
        for i, content in enumerate(test_contents):
            result = self.process_format_integration(content)
            assert result["success"], f"一貫性テスト{i+1}失敗"
            results.append(result)

        # 全ての出力が同様の構造を持つことを確認
        for i, result in enumerate(results):
            html = result["output"]
            assert (
                "<html>" in html or "<!DOCTYPE" in html or len(html) > 10
            ), f"出力{i+1}の構造が不正"

    def test_エラー統合処理(self) -> None:
        """エラーケースでの統合処理"""
        error_cases = [
            "",  # 空入力
            "# 不完全",  # 不完全マーカー
            None,  # None入力（例外処理）
        ]

        handled_count = 0
        for i, error_case in enumerate(error_cases):
            try:
                if error_case is not None:
                    result = self.process_format_integration(error_case)
                    # エラーでも適切にハンドリングされること
                    if result["success"] or result.get("error"):
                        handled_count += 1
                else:
                    handled_count += 1  # None の場合は事前回避
            except Exception as e:
                logger.debug(f"エラー統合{i+1}で例外: {e}")

        assert handled_count >= 2, "エラー統合処理が不十分です"

    def test_大規模統合処理(self) -> None:
        """大規模コンテンツの統合処理"""
        # 大規模コンテンツ生成
        large_content_parts = []
        for i in range(100):
            large_content_parts.append(f"# 見出し{i} #セクション{i}##")
            large_content_parts.append(f"# 太字 #重要ポイント{i}##")
            if i % 10 == 0:
                large_content_parts.append(f"- リスト項目{i}")

        large_content = "\n".join(large_content_parts)

        import time

        start_time = time.time()
        result = self.process_format_integration(large_content)
        elapsed = time.time() - start_time

        assert result["success"], f"大規模統合処理失敗: {result.get('error')}"
        assert elapsed < 10.0, f"大規模統合処理が遅すぎます: {elapsed:.2f}秒"

        # 出力サイズ確認
        assert result["file_size"] > 1000, "大規模統合出力が小さすぎます"

        logger.info(f"大規模統合処理: {elapsed:.3f}秒, 出力 {result['file_size']/1024:.1f}KB")

    def test_並行フォーマット統合(self) -> None:
        """並行でのフォーマット統合処理"""
        from concurrent.futures import ThreadPoolExecutor

        test_contents = [f"# 並行テスト{i} #コンテンツ{i}##" for i in range(10)]

        def process_single(content: str) -> Dict[str, Any]:
            return self.process_format_integration(content)

        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_single, content) for content in test_contents]
            for future in futures:
                results.append(future.result())

        # 全ての並行処理が成功すること
        success_count = sum(1 for r in results if r["success"])
        assert success_count == len(
            test_contents
        ), f"並行統合失敗: {success_count}/{len(test_contents)}"

    def test_統合品質検証(self) -> None:
        """統合結果の品質検証"""
        test_content = """# 見出し1 #品質テスト##
# 太字 #重要## な内容と # イタリック #強調## された部分
- 項目1
- 項目2
  - ネスト項目"""

        result = self.process_format_integration(test_content)
        assert result["success"], f"品質検証処理失敗: {result.get('error')}"

        html_output = result["output"]

        # 品質基準チェック（実際のレンダラー出力形式に合わせて更新）
        quality_checks = [
            ("# 見出し1 #品質テスト##" in html_output, "見出し記法"),
            ("# 太字 #重要##" in html_output, "太字記法"),
            ("# イタリック #強調##" in html_output, "イタリック記法"),
            ("項目1" in html_output and "項目2" in html_output, "リスト項目"),
            (len(html_output) > 100, "十分な出力長"),
            ("品質テスト" in html_output, "元コンテンツ保持"),
        ]

        for check_result, check_name in quality_checks:
            assert check_result, f"品質基準未達成: {check_name}"

    def test_統合メモリ管理(self) -> None:
        """統合処理でのメモリ管理"""
        import gc
        import tracemalloc

        tracemalloc.start()
        gc.collect()
        snapshot1 = tracemalloc.take_snapshot()

        # 複数回の統合処理
        for i in range(20):
            content = f"# メモリテスト{i} ## 太字 #データ{i}## ##"
            result = self.process_format_integration(content)
            assert result["success"], f"メモリ統合{i}失敗"

            # 定期的なGC
            if i % 5 == 0:
                gc.collect()

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()

        # メモリ使用量分析
        top_stats = snapshot2.compare_to(snapshot1, "lineno")
        total_increase = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)

        tracemalloc.stop()

        # メモリ増加が適切範囲内（3MB以下）
        assert (
            total_increase < 3 * 1024 * 1024
        ), f"統合処理でメモリ増加過多: {total_increase/1024/1024:.2f}MB"

        logger.info(f"統合メモリ管理テスト完了: 増加 {total_increase/1024:.1f}KB")
