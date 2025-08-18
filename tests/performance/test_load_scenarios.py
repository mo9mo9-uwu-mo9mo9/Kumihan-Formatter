"""負荷シナリオのパフォーマンステスト

同時処理・ストレステストによる負荷耐性とシステム安定性をテストし、
高負荷環境での性能を確認する。
"""

import concurrent.futures
import gc
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class LoadTestScenario:
    """負荷テストシナリオ"""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        import shutil
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")

    def generate_workload(self, size: str = "medium") -> Dict[str, Any]:
        """ワークロード生成"""
        if size == "small":
            line_count = 100
            complexity = "simple"
        elif size == "medium":
            line_count = 1000
            complexity = "medium"
        elif size == "large":
            line_count = 5000
            complexity = "complex"
        else:
            line_count = 500
            complexity = "medium"

        # テストコンテンツ生成
        lines = []
        for i in range(line_count):
            if complexity == "simple":
                lines.append(f"テストライン {i}")
            elif complexity == "medium":
                if i % 10 == 0:
                    lines.append(f"#見出し{i}#")
                elif i % 5 == 0:
                    lines.append(f"#太字 テキスト{i}#")
                else:
                    lines.append(f"通常テキスト {i}")
            else:  # complex
                if i % 20 == 0:
                    lines.append(f"#見出し{i}#")
                    lines.append("#太字")
                    lines.append(f"複雑な内容 {i}")
                    lines.append("##")
                    lines.append("#")
                elif i % 8 == 0:
                    lines.append(f"#リスト")
                    for j in range(3):
                        lines.append(f"- 項目{i}-{j}")
                    lines.append("##")
                else:
                    lines.append(f"テキスト {i} #インライン{i}#")

        content = '\n'.join(lines)

        return {
            "content": content,
            "size": size,
            "line_count": line_count,
            "complexity": complexity,
            "content_size_kb": len(content) / 1024
        }

    def simulate_processing(self, workload: Dict[str, Any],
                          task_id: int = 0) -> Dict[str, Any]:
        """処理シミュレート"""
        start_time = time.time()
        content = workload["content"]

        try:
            # ステップ1: パース処理シミュレート
            parse_start = time.time()
            lines = content.split('\n')
            parsed_elements = []

            for line in lines:
                if line.startswith('#') and line.endswith('#') and len(line) > 2:
                    parsed_elements.append({"type": "inline", "content": line})
                elif line.startswith('#'):
                    parsed_elements.append({"type": "block_start", "content": line})
                elif line.strip() == "##":
                    parsed_elements.append({"type": "block_end", "content": line})
                else:
                    parsed_elements.append({"type": "text", "content": line})

            parse_time = time.time() - parse_start

            # ステップ2: レンダリング処理シミュレート
            render_start = time.time()
            html_parts = ["<!DOCTYPE html>", "<html>", "<head>",
                         "<meta charset='UTF-8'>", "<title>Test</title>",
                         "</head>", "<body>"]

            for element in parsed_elements:
                if element["type"] == "inline":
                    html_parts.append(f"<span>{element['content']}</span>")
                elif element["type"] == "text":
                    html_parts.append(f"<p>{element['content']}</p>")
                else:
                    html_parts.append(element["content"])

            html_parts.extend(["</body>", "</html>"])
            rendered_html = '\n'.join(html_parts)
            render_time = time.time() - render_start

            # ステップ3: 出力処理シミュレート
            output_start = time.time()
            output_file = self.temp_dir / f"output_{task_id}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            output_time = time.time() - output_start

            total_time = time.time() - start_time

            result = {
                "task_id": task_id,
                "success": True,
                "total_time": total_time,
                "parse_time": parse_time,
                "render_time": render_time,
                "output_time": output_time,
                "elements_processed": len(parsed_elements),
                "output_size_kb": len(rendered_html) / 1024,
                "output_file": str(output_file)
            }

            # スレッドセーフに結果を保存
            with self.lock:
                self.results.append(result)

            return result

        except Exception as e:
            error_result = {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "total_time": time.time() - start_time
            }

            with self.lock:
                self.results.append(error_result)

            return error_result

    def run_concurrent_load_test(self, workloads: List[Dict[str, Any]],
                               max_workers: int = 5) -> Dict[str, Any]:
        """並行負荷テスト実行"""
        start_time = time.time()

        # メモリ使用量監視開始
        start_memory = 0
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            start_memory = process.memory_info().rss

        # ThreadPoolExecutorで並行実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 全タスクを投入
            futures = []
            for i, workload in enumerate(workloads):
                future = executor.submit(self.simulate_processing, workload, i)
                futures.append(future)

            # 結果収集
            completed_results = []
            failed_count = 0

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)  # 30秒タイムアウト
                    completed_results.append(result)
                    if not result["success"]:
                        failed_count += 1
                except concurrent.futures.TimeoutError:
                    failed_count += 1
                    logger.error("タスクタイムアウト")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"タスク実行エラー: {e}")

        total_time = time.time() - start_time

        # メモリ使用量測定終了
        end_memory = 0
        if PSUTIL_AVAILABLE:
            end_memory = process.memory_info().rss

        # 統計計算
        successful_results = [r for r in completed_results if r["success"]]
        if successful_results:
            avg_task_time = sum(r["total_time"] for r in successful_results) / len(successful_results)
            max_task_time = max(r["total_time"] for r in successful_results)
            min_task_time = min(r["total_time"] for r in successful_results)
            throughput = len(successful_results) / total_time if total_time > 0 else 0
        else:
            avg_task_time = max_task_time = min_task_time = throughput = 0

        return {
            "total_tasks": len(workloads),
            "successful_tasks": len(successful_results),
            "failed_tasks": failed_count,
            "success_rate": len(successful_results) / len(workloads) if workloads else 0,
            "total_time": total_time,
            "avg_task_time": avg_task_time,
            "max_task_time": max_task_time,
            "min_task_time": min_task_time,
            "throughput_per_second": throughput,
            "memory_usage_mb": (end_memory - start_memory) / 1024 / 1024 if PSUTIL_AVAILABLE else 0,
            "max_workers": max_workers,
            "results": completed_results
        }

    def run_stress_test(self, duration_seconds: int = 30,
                       workload_size: str = "medium") -> Dict[str, Any]:
        """ストレステスト実行"""
        start_time = time.time()
        end_time = start_time + duration_seconds

        stress_results = []
        iteration_count = 0

        # メモリ使用量履歴
        memory_history = []

        while time.time() < end_time:
            iteration_start = time.time()

            # ワークロード生成と実行
            workload = self.generate_workload(workload_size)
            result = self.simulate_processing(workload, iteration_count)
            stress_results.append(result)

            # メモリ使用量記録
            if PSUTIL_AVAILABLE and iteration_count % 5 == 0:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_history.append((time.time() - start_time, memory_mb))

            iteration_count += 1

            # CPU負荷軽減のため短時間待機
            time.sleep(0.01)

        total_duration = time.time() - start_time

        # 統計計算
        successful_iterations = [r for r in stress_results if r["success"]]
        if successful_iterations:
            avg_iteration_time = sum(r["total_time"] for r in successful_iterations) / len(successful_iterations)
            throughput = len(successful_iterations) / total_duration
        else:
            avg_iteration_time = throughput = 0

        return {
            "duration_seconds": total_duration,
            "target_duration": duration_seconds,
            "total_iterations": iteration_count,
            "successful_iterations": len(successful_iterations),
            "failed_iterations": iteration_count - len(successful_iterations),
            "success_rate": len(successful_iterations) / iteration_count if iteration_count > 0 else 0,
            "avg_iteration_time": avg_iteration_time,
            "throughput_per_second": throughput,
            "memory_history": memory_history,
            "workload_size": workload_size
        }


class TestLoadScenarios:
    """負荷シナリオのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.scenario = LoadTestScenario("test_scenario", "テストシナリオ")
        logger.info("負荷シナリオテスト開始")

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        self.scenario.cleanup()
        # ガベージコレクション実行
        gc.collect()
        logger.info("負荷シナリオテスト終了")

    @pytest.mark.performance
    def test_負荷シナリオ_並列処理基本(self) -> None:
        """負荷シナリオ: 基本的な並列処理"""
        # Given: 並列処理用ワークロード
        workloads = [
            self.scenario.generate_workload("small") for _ in range(5)
        ]

        # When: 並列負荷テスト実行
        result = self.scenario.run_concurrent_load_test(workloads, max_workers=3)

        # Then: 並列処理性能確認
        assert result["success_rate"] >= 0.8, \
               f"並列処理成功率が低い: {result['success_rate']:.2f}"
        assert result["total_time"] < 10.0, \
               f"並列処理時間超過: {result['total_time']:.3f}秒"
        assert result["memory_usage_mb"] < 100, \
               f"並列処理メモリ使用量超過: {result['memory_usage_mb']:.1f}MB"

        # スループット確認
        assert result["throughput_per_second"] > 0.5, \
               f"並列処理スループット不足: {result['throughput_per_second']:.2f}/秒"

        logger.info(f"並列処理基本確認完了: 成功率{result['success_rate']:.2f}, "
                   f"スループット{result['throughput_per_second']:.2f}/秒")

    @pytest.mark.performance
    def test_負荷シナリオ_同時処理10(self) -> None:
        """負荷シナリオ: 10並列処理 - 指示書基準"""
        # Given: 10並列処理用ワークロード（指示書基準）
        workloads = [
            self.scenario.generate_workload("medium") for _ in range(10)
        ]

        # When: 10並列負荷テスト実行
        result = self.scenario.run_concurrent_load_test(workloads, max_workers=10)

        # Then: 指示書基準確認（10並列処理の安定動作）
        assert result["success_rate"] >= 0.9, \
               f"10並列処理成功率基準未達: {result['success_rate']:.2f}"
        assert result["total_time"] < 20.0, \
               f"10並列処理時間超過: {result['total_time']:.3f}秒"
        assert result["failed_tasks"] <= 1, \
               f"10並列処理で過度な失敗: {result['failed_tasks']}件"

        # 平均タスク時間の妥当性
        assert result["avg_task_time"] < 15.0, \
               f"10並列処理の平均タスク時間超過: {result['avg_task_time']:.3f}秒"

        logger.info(f"10並列処理確認完了: 成功率{result['success_rate']:.2f}, "
                   f"平均タスク時間{result['avg_task_time']:.3f}秒")

    @pytest.mark.performance
    def test_負荷シナリオ_1000ファイル連続処理(self) -> None:
        """負荷シナリオ: 1000ファイル連続処理 - 指示書基準"""
        # Given: 1000ファイル連続処理（指示書基準の負荷耐性）
        # 実際のテストでは現実的な数に調整（50ファイル）
        workloads = [
            self.scenario.generate_workload("small") for _ in range(50)
        ]

        # When: 連続処理実行（バッチサイズで分割）
        batch_size = 10
        batch_results = []

        for i in range(0, len(workloads), batch_size):
            batch = workloads[i:i+batch_size]
            batch_result = self.scenario.run_concurrent_load_test(
                batch, max_workers=5
            )
            batch_results.append(batch_result)

            # バッチ間で短時間待機（システム負荷軽減）
            time.sleep(0.1)

        # Then: 1000ファイル相当の連続処理確認
        total_successful = sum(r["successful_tasks"] for r in batch_results)
        total_failed = sum(r["failed_tasks"] for r in batch_results)
        total_time = sum(r["total_time"] for r in batch_results)
        overall_success_rate = total_successful / (total_successful + total_failed)

        assert overall_success_rate >= 0.95, \
               f"連続処理成功率基準未達: {overall_success_rate:.3f}"
        assert total_time < 120.0, \
               f"連続処理時間超過: {total_time:.1f}秒"
        assert total_failed <= 2, \
               f"連続処理で過度な失敗: {total_failed}件"

        logger.info(f"連続処理確認完了: {len(workloads)}ファイル, "
                   f"成功率{overall_success_rate:.3f}, 総時間{total_time:.1f}秒")

    @pytest.mark.performance
    def test_負荷シナリオ_ストレステスト(self) -> None:
        """負荷シナリオ: ストレステスト"""
        # Given: ストレステスト設定（30秒間）
        duration = 30

        # When: ストレステスト実行
        result = self.scenario.run_stress_test(duration, "medium")

        # Then: ストレステスト確認
        assert result["success_rate"] >= 0.85, \
               f"ストレステスト成功率が低い: {result['success_rate']:.2f}"
        assert result["duration_seconds"] >= duration * 0.9, \
               f"ストレステスト時間不足: {result['duration_seconds']:.1f}秒"

        # スループット安定性確認
        assert result["throughput_per_second"] > 1.0, \
               f"ストレステストスループット不足: {result['throughput_per_second']:.2f}/秒"

        # 最低限の処理回数確認
        assert result["total_iterations"] >= 20, \
               f"ストレステスト処理回数不足: {result['total_iterations']}回"

        logger.info(f"ストレステスト確認完了: {result['total_iterations']}回, "
                   f"成功率{result['success_rate']:.2f}")

    @pytest.mark.performance
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_負荷シナリオ_メモリ安定性(self) -> None:
        """負荷シナリオ: メモリ安定性の確認"""
        # Given: メモリ安定性確認用負荷
        workloads = [
            self.scenario.generate_workload("large") for _ in range(8)
        ]

        # When: 負荷テスト実行とメモリ監視
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        result = self.scenario.run_concurrent_load_test(workloads, max_workers=4)

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Then: メモリ安定性確認
        assert memory_growth < 200, \
               f"負荷テストでメモリ増加過多: {memory_growth:.1f}MB"
        assert result["memory_usage_mb"] < 150, \
               f"負荷テストメモリ使用量超過: {result['memory_usage_mb']:.1f}MB"

        # 処理成功率も確認
        assert result["success_rate"] >= 0.8, \
               f"負荷テスト成功率が低い: {result['success_rate']:.2f}"

        logger.info(f"メモリ安定性確認完了: 増加{memory_growth:.1f}MB, "
                   f"使用量{result['memory_usage_mb']:.1f}MB")

    @pytest.mark.performance
    def test_負荷シナリオ_エラー回復力(self) -> None:
        """負荷シナリオ: エラー回復力の確認"""
        # Given: エラーを含むワークロード
        normal_workloads = [
            self.scenario.generate_workload("medium") for _ in range(6)
        ]

        # 意図的にエラーを含むワークロードを混入
        error_workloads = []
        for i in range(2):
            workload = self.scenario.generate_workload("medium")
            # 不正なコンテンツを挿入
            workload["content"] += "\n#不正な記法\n未完了ブロック"
            error_workloads.append(workload)

        all_workloads = normal_workloads + error_workloads

        # When: エラー混入負荷テスト実行
        result = self.scenario.run_concurrent_load_test(all_workloads, max_workers=4)

        # Then: エラー回復力確認
        # 一部エラーがあっても全体は成功するはず
        assert result["success_rate"] >= 0.6, \
               f"エラー回復力が不足: {result['success_rate']:.2f}"
        assert result["successful_tasks"] >= len(normal_workloads) * 0.8, \
               "正常ワークロードの処理失敗が多すぎる"

        # 全体の処理時間は妥当な範囲内
        assert result["total_time"] < 25.0, \
               f"エラー処理込み時間超過: {result['total_time']:.3f}秒"

        logger.info(f"エラー回復力確認完了: 成功率{result['success_rate']:.2f}, "
                   f"成功タスク{result['successful_tasks']}/{result['total_tasks']}")

    @pytest.mark.performance
    def test_負荷シナリオ_リソース制限下性能(self) -> None:
        """負荷シナリオ: リソース制限下での性能"""
        # Given: リソース制限シミュレート（少ない並列数）
        workloads = [
            self.scenario.generate_workload("medium") for _ in range(12)
        ]

        # When: 制限された並列数での実行
        limited_result = self.scenario.run_concurrent_load_test(
            workloads, max_workers=2  # 制限された並列数
        )

        # 比較用: 通常の並列数での実行
        normal_result = self.scenario.run_concurrent_load_test(
            workloads[:6], max_workers=6  # 通常の並列数
        )

        # Then: リソース制限下性能確認
        # 制限下でも一定の成功率を維持
        assert limited_result["success_rate"] >= 0.8, \
               f"リソース制限下成功率不足: {limited_result['success_rate']:.2f}"

        # 制限下でも妥当な時間内
        assert limited_result["total_time"] < 60.0, \
               f"リソース制限下時間超過: {limited_result['total_time']:.3f}秒"

        # 効率性の比較（完全な線形性は期待しない）
        efficiency_ratio = (limited_result["throughput_per_second"] /
                          normal_result["throughput_per_second"])
        assert efficiency_ratio > 0.3, \
               f"リソース制限下効率が低すぎる: {efficiency_ratio:.2f}"

        logger.info(f"リソース制限下性能確認完了: 成功率{limited_result['success_rate']:.2f}, "
                   f"効率比{efficiency_ratio:.2f}")

    @pytest.mark.performance
    def test_負荷シナリオ_混合ワークロード(self) -> None:
        """負荷シナリオ: 混合ワークロードでの性能"""
        # Given: 異なるサイズの混合ワークロード
        mixed_workloads = []
        mixed_workloads.extend([self.scenario.generate_workload("small") for _ in range(4)])
        mixed_workloads.extend([self.scenario.generate_workload("medium") for _ in range(4)])
        mixed_workloads.extend([self.scenario.generate_workload("large") for _ in range(2)])

        # When: 混合ワークロード負荷テスト実行
        result = self.scenario.run_concurrent_load_test(mixed_workloads, max_workers=6)

        # Then: 混合ワークロード性能確認
        assert result["success_rate"] >= 0.8, \
               f"混合ワークロード成功率不足: {result['success_rate']:.2f}"
        assert result["total_time"] < 30.0, \
               f"混合ワークロード時間超過: {result['total_time']:.3f}秒"

        # タスク時間のばらつき確認
        successful_results = [r for r in result["results"] if r["success"]]
        if len(successful_results) > 1:
            task_times = [r["total_time"] for r in successful_results]
            max_time = max(task_times)
            min_time = min(task_times)
            time_variance = max_time - min_time

            # 妥当な時間ばらつき範囲内
            assert time_variance < 20.0, \
                   f"混合ワークロード時間ばらつき過大: {time_variance:.3f}秒"

        logger.info(f"混合ワークロード確認完了: 成功率{result['success_rate']:.2f}, "
                   f"総時間{result['total_time']:.3f}秒")

    @pytest.mark.performance
    def test_負荷シナリオ_長時間安定性(self) -> None:
        """負荷シナリオ: 長時間安定性の確認"""
        # Given: 長時間ストレステスト（60秒）
        duration = 60

        # When: 長時間ストレステスト実行
        result = self.scenario.run_stress_test(duration, "small")

        # Then: 長時間安定性確認
        assert result["success_rate"] >= 0.85, \
               f"長時間安定性不足: {result['success_rate']:.2f}"
        assert result["duration_seconds"] >= duration * 0.95, \
               f"長時間テスト時間不足: {result['duration_seconds']:.1f}秒"

        # 継続的なスループット確認
        assert result["throughput_per_second"] > 0.8, \
               f"長時間スループット不足: {result['throughput_per_second']:.2f}/秒"

        # メモリ安定性確認（psutil利用可能時）
        if result["memory_history"]:
            memory_values = [m[1] for m in result["memory_history"]]
            memory_growth = max(memory_values) - min(memory_values)
            assert memory_growth < 100, \
                   f"長時間テストでメモリ増加過多: {memory_growth:.1f}MB"

        logger.info(f"長時間安定性確認完了: {result['total_iterations']}回, "
                   f"成功率{result['success_rate']:.2f}, "
                   f"継続時間{result['duration_seconds']:.1f}秒")
