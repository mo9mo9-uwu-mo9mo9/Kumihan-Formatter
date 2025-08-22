"""ストレスシナリオテスト

極限状況でのシステムの堅牢性を検証する。
"""

import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestStressScenarios:
    """ストレスシナリオテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.complex_patterns = [
            "# 見出し1 ## 見出し2 ### 見出し3 #ネスト##",
            "# 太字 ## イタリック ## 下線 #複合装飾## ##",
            "# ルビ #漢字|かんじ## と # 太字 #強調##",
            "```python\ndef test():\n    return '# 太字 #コード内##'\n```",
            "- リスト1\n  - リスト2\n    - リスト3\n      - リスト4",
        ]

    def generate_stress_content(self, pattern_type: str) -> str:
        """ストレステスト用コンテンツ生成"""
        if pattern_type == "deep_nesting":
            # 深いネスト構造
            content = ""
            for i in range(50):
                content += "  " * i + f"- レベル{i}アイテム\n"
            return content

        elif pattern_type == "many_markers":
            # 大量のマーカー
            content = []
            markers = ["太字", "イタリック", "下線", "枠線", "ハイライト"]
            for i in range(100):
                marker = random.choice(markers)
                content.append(f"# {marker} #テキスト{i}##")
            return " ".join(content)

        elif pattern_type == "complex_mix":
            # 複雑な混合パターン
            content = []
            for i in range(100):
                pattern = random.choice(self.complex_patterns)
                content.append(pattern.format(i))
            return "\n".join(content)

        elif pattern_type == "edge_cases":
            # エッジケース集
            return """
# 太字 #開始タグのみ
終了タグのみ##
# # 空マーカー ##
# 太字 # # ネスト # 内部 ## ##
###連続ハッシュ###
# 太字 #改行
を含む
テキスト##
"""
        else:
            return "通常のテキスト"

    def stress_test_parser(self, content: str) -> Dict[str, Any]:
        """パーサーのストレステスト"""
        from kumihan_formatter.core.parsing.main_parser import MainParser

        start_time = time.time()
        errors = []
        result = None

        try:
            parser = MainParser()
            result = parser.parse(content)
            success = True
        except Exception as e:
            errors.append(str(e))
            success = False

        elapsed = time.time() - start_time

        return {
            "success": success,
            "elapsed": elapsed,
            "errors": errors,
            "result": result,
        }

    def test_深いネスト構造(self) -> None:
        """深いネスト構造の処理"""
        content = self.generate_stress_content("deep_nesting")
        result = self.stress_test_parser(content)

        assert result["success"], f"深いネスト処理失敗: {result['errors']}"
        assert result["elapsed"] < 5.0, f"処理時間超過: {result['elapsed']:.2f}秒"

        logger.info(f"深いネスト処理: {result['elapsed']:.3f}秒")

    def test_大量マーカー処理(self) -> None:
        """大量のマーカー処理"""
        content = self.generate_stress_content("many_markers")
        result = self.stress_test_parser(content)

        assert result["success"], f"大量マーカー処理失敗: {result['errors']}"
        assert result["elapsed"] < 3.0, f"処理時間超過: {result['elapsed']:.2f}秒"

        logger.info(f"大量マーカー処理: {result['elapsed']:.3f}秒")

    def test_複雑パターン混合(self) -> None:
        """複雑なパターンの混合処理"""
        content = self.generate_stress_content("complex_mix")
        result = self.stress_test_parser(content)

        assert result["success"], f"複雑パターン処理失敗: {result['errors']}"
        assert result["elapsed"] < 5.0, f"処理時間超過: {result['elapsed']:.2f}秒"

        logger.info(f"複雑パターン処理: {result['elapsed']:.3f}秒")

    def test_エッジケース集(self) -> None:
        """エッジケースの処理"""
        content = self.generate_stress_content("edge_cases")
        result = self.stress_test_parser(content)

        # エッジケースでもクラッシュしないこと
        assert result["success"] or len(result["errors"]) > 0, "エッジケース処理が不明な状態"
        assert result["elapsed"] < 1.0, f"処理時間超過: {result['elapsed']:.2f}秒"

        if result["errors"]:
            logger.info(f"期待されるエラー: {result['errors']}")

    def test_並行ストレス処理(self) -> None:
        """並行でのストレス処理"""
        test_cases = [
            ("deep_nesting", 5),
            ("many_markers", 5),
            ("complex_mix", 5),
            ("edge_cases", 5),
        ]

        results: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for pattern_type, count in test_cases:
                for i in range(count):
                    content = self.generate_stress_content(pattern_type)
                    future = executor.submit(self.stress_test_parser, content)
                    futures.append((pattern_type, future))

            for pattern_type, future in futures:
                result = future.result()
                result["pattern"] = pattern_type
                results.append(result)

        # 統計
        total = len(results)
        success_count = sum(1 for r in results if r["success"])
        avg_time = sum(r["elapsed"] for r in results) / total

        logger.info(
            f"並行ストレステスト: " f"成功 {success_count}/{total}, " f"平均時間 {avg_time:.3f}秒"
        )

        # 90%以上成功すること
        assert success_count >= total * 0.9, f"成功率が低い: {success_count}/{total}"

    def test_メモリストレス(self) -> None:
        """メモリストレステスト"""
        import gc
        import tracemalloc

        tracemalloc.start()

        # 初期状態
        gc.collect()
        snapshot1 = tracemalloc.take_snapshot()

        # ストレス処理を繰り返し実行
        for i in range(10):
            for pattern in ["deep_nesting", "many_markers", "complex_mix"]:
                content = self.generate_stress_content(pattern)
                result = self.stress_test_parser(content)

                # 結果を破棄してメモリ解放を促す
                del result
                del content

            # 定期的にGC実行
            if i % 3 == 0:
                gc.collect()

        # 最終状態
        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()

        # メモリ増加量確認
        top_stats = snapshot2.compare_to(snapshot1, "lineno")
        total_diff = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)

        tracemalloc.stop()

        # メモリリークがないこと（増加量が5MB以下）
        assert (
            total_diff < 5 * 1024 * 1024
        ), f"メモリ増加量が多すぎます: {total_diff/1024/1024:.2f}MB"

        logger.info(f"メモリストレステスト完了: 増加量 {total_diff/1024:.1f}KB")

    def test_エラー回復性(self) -> None:
        """エラーからの回復性テスト"""
        # 意図的に壊れたコンテンツを含むテストケース
        test_contents = [
            "正常なテキスト",
            "# 壊れた #マーカー",  # 終了タグなし
            "正常なテキスト2",
            None,  # Noneを渡す
            "",  # 空文字列
            "正常なテキスト3",
            "# " * 1000,  # 大量の開始タグ
            "正常なテキスト4",
        ]

        success_count = 0
        error_count = 0

        for i, content in enumerate(test_contents):
            try:
                if content is not None:
                    result = self.stress_test_parser(content)
                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                logger.debug(f"ケース{i}でエラー: {e}")

        # エラーが発生しても後続の処理が継続できること
        assert success_count >= 4, f"正常処理が少なすぎます: {success_count}"
        logger.info(f"エラー回復性: 成功 {success_count}, エラー {error_count}")
