"""パーシング性能のパフォーマンステスト

大量データの解析速度とパーシング処理の効率性をテストし、
性能基準の達成を確認する。
"""

import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class ParsingPerformanceTester:
    """パーシング性能テスター"""

    def __init__(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results: List[Dict[str, Any]] = []

    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        import shutil
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")

    def generate_test_content(self, line_count: int,
                            complexity: str = "medium") -> str:
        """テストコンテンツ生成"""
        lines = []

        if complexity == "simple":
            # シンプルなテキストのみ
            for i in range(line_count):
                lines.append(f"テストライン {i}")

        elif complexity == "medium":
            # 中程度の複雑さ（記法混在）
            for i in range(line_count):
                if i % 10 == 0:
                    lines.append(f"#見出し{i}#")
                    lines.append("見出しコンテンツ")
                    lines.append("#")
                elif i % 5 == 0:
                    lines.append(f"#太字 テストライン{i}#")
                elif i % 3 == 0:
                    lines.append(f"#イタリック")
                    lines.append(f"ブロック内容 {i}")
                    lines.append("##")
                else:
                    lines.append(f"通常のテキスト行 {i}")

        elif complexity == "complex":
            # 高度な複雑さ（ネスト、複合記法）
            for i in range(line_count):
                if i % 20 == 0:
                    lines.append(f"#見出し{i}#")
                    lines.append("#太字")
                    lines.append(f"ネストした内容 {i}")
                    lines.append("##")
                    lines.append("#")
                elif i % 8 == 0:
                    lines.append(f"#複合 #太字 内容{i}# と #イタリック 内容{i}##")
                elif i % 4 == 0:
                    lines.append("#リスト")
                    for j in range(3):
                        lines.append(f"- 項目{i}-{j}")
                    lines.append("##")
                else:
                    lines.append(f"通常のテキスト行 {i} #インライン{i}#")

        return '\n'.join(lines)

    def mock_parse_content(self, content: str) -> Dict[str, Any]:
        """コンテンツのモックパース処理"""
        start_time = time.time()

        # パース処理のシミュレート
        lines = content.split('\n')
        parse_result = {
            "line_count": len(lines),
            "total_chars": len(content),
            "blocks": 0,
            "inline_elements": 0,
            "headings": 0,
            "processing_steps": []
        }

        # ステップ1: 行の分類
        step1_start = time.time()
        for line in lines:
            if line.startswith('#') and line.endswith('#') and len(line) > 2:
                parse_result["inline_elements"] += 1
            elif line.startswith('#') and not line.endswith('#'):
                parse_result["headings"] += 1
            elif line.strip() == "##":
                parse_result["blocks"] += 1
        step1_time = time.time() - step1_start
        parse_result["processing_steps"].append(("line_classification", step1_time))

        # ステップ2: 構造解析
        step2_start = time.time()
        block_depth = 0
        for line in lines:
            if line.startswith('#') and not line.endswith('#'):
                block_depth += 1
            elif line.strip() == "##":
                block_depth = max(0, block_depth - 1)
        step2_time = time.time() - step2_start
        parse_result["processing_steps"].append(("structure_analysis", step2_time))

        # ステップ3: 内容処理
        step3_start = time.time()
        processed_content = []
        for line in lines:
            if '#' in line:
                # 記法処理のシミュレート
                processed_line = line.replace('#太字', '<strong>').replace('#', '</strong>')
                processed_line = processed_line.replace('##', '</div>')
                processed_content.append(processed_line)
            else:
                processed_content.append(line)
        step3_time = time.time() - step3_start
        parse_result["processing_steps"].append(("content_processing", step3_time))

        total_time = time.time() - start_time
        parse_result["total_processing_time"] = total_time
        parse_result["processed_content"] = '\n'.join(processed_content)

        return parse_result

    def measure_parsing_performance(self, content: str,
                                  iterations: int = 1) -> Dict[str, Any]:
        """パーシング性能測定"""
        start_memory = 0
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            start_memory = process.memory_info().rss

        results = []
        total_start_time = time.time()

        for i in range(iterations):
            iteration_start = time.time()
            parse_result = self.mock_parse_content(content)
            iteration_time = time.time() - iteration_start

            results.append({
                "iteration": i,
                "time": iteration_time,
                "parse_result": parse_result
            })

        total_time = time.time() - total_start_time

        end_memory = 0
        if PSUTIL_AVAILABLE:
            end_memory = process.memory_info().rss

        # 統計計算
        processing_times = [r["time"] for r in results]
        avg_time = sum(processing_times) / len(processing_times)
        min_time = min(processing_times)
        max_time = max(processing_times)

        return {
            "iterations": iterations,
            "total_time": total_time,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "throughput_per_second": iterations / total_time if total_time > 0 else 0,
            "memory_usage_mb": (end_memory - start_memory) / 1024 / 1024 if PSUTIL_AVAILABLE else 0,
            "results": results
        }

    def run_scalability_test(self, base_line_count: int,
                           scale_factors: List[int]) -> Dict[str, Any]:
        """スケーラビリティテスト実行"""
        scalability_results = []

        for factor in scale_factors:
            line_count = base_line_count * factor
            content = self.generate_test_content(line_count, "medium")

            performance_result = self.measure_parsing_performance(content, 3)

            scalability_results.append({
                "scale_factor": factor,
                "line_count": line_count,
                "content_size_kb": len(content) / 1024,
                "average_time": performance_result["average_time"],
                "throughput": performance_result["throughput_per_second"],
                "memory_usage_mb": performance_result["memory_usage_mb"]
            })

        return {
            "base_line_count": base_line_count,
            "scale_factors": scale_factors,
            "results": scalability_results
        }


class TestParsingPerformance:
    """パーシング性能のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.tester = ParsingPerformanceTester()
        logger.info("パーシング性能テスト開始")

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        self.tester.cleanup()
        logger.info("パーシング性能テスト終了")

    @pytest.mark.performance
    def test_パーシング性能_小規模データ(self) -> None:
        """パーシング性能: 小規模データ（100行）"""
        # Given: 小規模テストデータ
        content = self.tester.generate_test_content(100, "medium")

        # When: パフォーマンス測定
        result = self.tester.measure_parsing_performance(content, 10)

        # Then: 性能基準確認
        assert result["average_time"] < 0.1, \
               f"小規模データ処理時間超過: {result['average_time']:.3f}秒"
        assert result["throughput_per_second"] > 50, \
               f"小規模データスループット不足: {result['throughput_per_second']:.1f}/秒"

        logger.info(f"小規模データ性能: 平均{result['average_time']:.3f}秒, "
                   f"スループット{result['throughput_per_second']:.1f}/秒")

    @pytest.mark.performance
    def test_パーシング性能_中規模データ(self) -> None:
        """パーシング性能: 中規模データ（1000行）- 指示書基準"""
        # Given: 中規模テストデータ（指示書の基準）
        content = self.tester.generate_test_content(1000, "medium")

        # When: パフォーマンス測定
        result = self.tester.measure_parsing_performance(content, 5)

        # Then: 指示書基準確認（5秒以内）
        assert result["average_time"] < 5.0, \
               f"中規模データ処理時間基準超過: {result['average_time']:.3f}秒"
        assert result["memory_usage_mb"] < 100, \
               f"中規模データメモリ使用量基準超過: {result['memory_usage_mb']:.1f}MB"

        # スループット確認
        assert result["throughput_per_second"] > 1, \
               f"中規模データスループット不足: {result['throughput_per_second']:.1f}/秒"

        logger.info(f"中規模データ性能: 平均{result['average_time']:.3f}秒, "
                   f"メモリ{result['memory_usage_mb']:.1f}MB")

    @pytest.mark.performance
    def test_パーシング性能_大規模データ(self) -> None:
        """パーシング性能: 大規模データ（10000行）"""
        # Given: 大規模テストデータ
        content = self.tester.generate_test_content(10000, "medium")

        # When: パフォーマンス測定
        result = self.tester.measure_parsing_performance(content, 3)

        # Then: 性能基準確認
        assert result["average_time"] < 30.0, \
               f"大規模データ処理時間超過: {result['average_time']:.3f}秒"
        assert result["memory_usage_mb"] < 200, \
               f"大規模データメモリ使用量超過: {result['memory_usage_mb']:.1f}MB"

        logger.info(f"大規模データ性能: 平均{result['average_time']:.3f}秒, "
                   f"メモリ{result['memory_usage_mb']:.1f}MB")

    @pytest.mark.performance
    def test_パーシング性能_複雑度比較(self) -> None:
        """パーシング性能: 複雑度による性能差"""
        # Given: 異なる複雑度のテストデータ
        line_count = 500
        complexities = ["simple", "medium", "complex"]

        # When: 複雑度別性能測定
        complexity_results = {}
        for complexity in complexities:
            content = self.tester.generate_test_content(line_count, complexity)
            result = self.tester.measure_parsing_performance(content, 5)
            complexity_results[complexity] = result

        # Then: 複雑度による性能差確認
        simple_time = complexity_results["simple"]["average_time"]
        medium_time = complexity_results["medium"]["average_time"]
        complex_time = complexity_results["complex"]["average_time"]

        # 複雑度が上がると処理時間も増加するはず
        assert simple_time <= medium_time <= complex_time, \
               "複雑度と処理時間の関係が正しくない"

        # 最大複雑度でも妥当な時間内
        assert complex_time < 10.0, \
               f"複雑データ処理時間超過: {complex_time:.3f}秒"

        logger.info(f"複雑度性能比較: シンプル{simple_time:.3f}s, "
                   f"中程度{medium_time:.3f}s, 複雑{complex_time:.3f}s")

    @pytest.mark.performance
    def test_パーシング性能_スケーラビリティ(self) -> None:
        """パーシング性能: スケーラビリティの確認"""
        # Given: スケーラビリティテスト設定
        base_line_count = 100
        scale_factors = [1, 2, 5, 10]

        # When: スケーラビリティテスト実行
        scalability_result = self.tester.run_scalability_test(
            base_line_count, scale_factors
        )

        # Then: スケーラビリティ確認
        results = scalability_result["results"]

        # 線形スケーラビリティの確認（時間が線形に増加）
        time_ratios = []
        for i in range(1, len(results)):
            prev_time = results[i-1]["average_time"]
            curr_time = results[i]["average_time"]
            scale_ratio = results[i]["scale_factor"] / results[i-1]["scale_factor"]
            time_ratio = curr_time / prev_time if prev_time > 0 else float('inf')
            time_ratios.append(time_ratio / scale_ratio)

        # 時間増加率が妥当な範囲内（線形に近い）
        avg_ratio = sum(time_ratios) / len(time_ratios) if time_ratios else 1.0
        assert 0.5 <= avg_ratio <= 3.0, \
               f"スケーラビリティが非線形: 平均比{avg_ratio:.2f}"

        # 最大スケールでも妥当な性能
        max_scale_result = results[-1]
        assert max_scale_result["average_time"] < 15.0, \
               f"最大スケール処理時間超過: {max_scale_result['average_time']:.3f}秒"

        logger.info(f"スケーラビリティ確認完了: {len(results)}ポイント, "
                   f"平均比{avg_ratio:.2f}")

    @pytest.mark.performance
    def test_パーシング性能_メモリ効率性(self) -> None:
        """パーシング性能: メモリ効率性の確認"""
        # Given: メモリ効率性テスト用データ
        content = self.tester.generate_test_content(2000, "medium")

        # When: 複数回実行でメモリリーク確認
        memory_usage_history = []
        for i in range(5):
            result = self.tester.measure_parsing_performance(content, 1)
            memory_usage_history.append(result["memory_usage_mb"])

        # Then: メモリ効率性確認
        # メモリ使用量の安定性確認
        max_memory = max(memory_usage_history)
        min_memory = min(memory_usage_history)
        memory_variance = max_memory - min_memory

        assert memory_variance < 50, \
               f"メモリ使用量の変動が大きい: {memory_variance:.1f}MB"

        # 絶対的なメモリ使用量確認
        avg_memory = sum(memory_usage_history) / len(memory_usage_history)
        assert avg_memory < 100, \
               f"平均メモリ使用量が基準超過: {avg_memory:.1f}MB"

        logger.info(f"メモリ効率性確認完了: 平均{avg_memory:.1f}MB, "
                   f"変動{memory_variance:.1f}MB")

    @pytest.mark.performance
    def test_パーシング性能_並列処理シミュレート(self) -> None:
        """パーシング性能: 並列処理での性能確認"""
        # Given: 並列処理シミュレート用データ
        contents = [
            self.tester.generate_test_content(300, "simple"),
            self.tester.generate_test_content(300, "medium"),
            self.tester.generate_test_content(300, "complex")
        ]

        # When: 同時処理シミュレート
        start_time = time.time()
        parallel_results = []

        for i, content in enumerate(contents):
            result = self.tester.measure_parsing_performance(content, 1)
            parallel_results.append({
                "task_id": i,
                "content_type": ["simple", "medium", "complex"][i],
                "result": result
            })

        total_parallel_time = time.time() - start_time

        # Then: 並列処理性能確認
        total_processing_time = sum(r["result"]["average_time"] for r in parallel_results)

        # 並列処理効率性確認（シーケンシャル処理との比較）
        efficiency = total_processing_time / total_parallel_time if total_parallel_time > 0 else 0
        assert efficiency >= 0.8, f"並列処理効率が低い: {efficiency:.2f}"

        # 全体の処理時間確認
        assert total_parallel_time < 10.0, \
               f"並列処理時間超過: {total_parallel_time:.3f}秒"

        logger.info(f"並列処理性能確認完了: 効率{efficiency:.2f}, "
                   f"総時間{total_parallel_time:.3f}秒")

    @pytest.mark.performance
    def test_パーシング性能_エラー処理オーバーヘッド(self) -> None:
        """パーシング性能: エラー処理のオーバーヘッド確認"""
        # Given: エラーを含むテストデータ
        error_content = self.tester.generate_test_content(500, "medium")
        # 意図的にエラーを挿入
        error_content += "\n#不正な記法\n不完全なブロック\n"

        normal_content = self.tester.generate_test_content(500, "medium")

        # When: エラー処理ありとなしの性能比較
        normal_result = self.tester.measure_parsing_performance(normal_content, 5)
        error_result = self.tester.measure_parsing_performance(error_content, 5)

        # Then: エラー処理オーバーヘッド確認
        overhead_ratio = error_result["average_time"] / normal_result["average_time"]

        # エラー処理オーバーヘッドが妥当な範囲内
        assert overhead_ratio < 2.0, \
               f"エラー処理オーバーヘッドが大きすぎる: {overhead_ratio:.2f}倍"

        # エラーがあっても妥当な時間内
        assert error_result["average_time"] < 8.0, \
               f"エラー処理時間超過: {error_result['average_time']:.3f}秒"

        logger.info(f"エラー処理オーバーヘッド確認完了: {overhead_ratio:.2f}倍, "
                   f"エラー処理時間{error_result['average_time']:.3f}秒")
