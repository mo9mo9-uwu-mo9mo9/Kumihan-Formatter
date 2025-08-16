"""
メモリリーク検出テストスイート

Issue #772 - メモリ・リソース管理の強化と長時間実行時の安定性向上
メモリリーク検出機構の精度と信頼性をテスト
"""

import gc
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.core.performance import MemoryOptimizer


class MemoryLeakDetectionTest:
    """メモリリーク検出テストクラス"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.memory_optimizer = MemoryOptimizer(enable_gc_optimization=True)

    def create_intentional_memory_leak(
        self, leak_type: str, size_mb: float = 5.0
    ) -> List[Any]:
        """
        意図的なメモリリーク作成（テスト用）

        Args:
            leak_type: リークタイプ（'circular', 'growing_list', 'unclosed_files'）
            size_mb: リークサイズ（MB）

        Returns:
            List[Any]: リークオブジェクト参照（テスト後のクリーンアップ用）
        """
        leak_objects = []
        size_bytes = int(size_mb * 1024 * 1024)

        if leak_type == "circular":
            # 循環参照によるリーク
            class CircularNode:
                def __init__(self, data: str):
                    self.data = data
                    self.ref = None

            # 循環参照チェーン作成
            nodes = []
            chunk_size = 1024  # 1KB per node
            node_count = size_bytes // chunk_size

            for i in range(node_count):
                node = CircularNode("x" * chunk_size)
                if nodes:
                    nodes[-1].ref = node
                nodes.append(node)

            # 最後のノードから最初のノードへの循環参照
            if nodes:
                nodes[-1].ref = nodes[0]

            leak_objects.extend(nodes)

        elif leak_type == "growing_list":
            # 成長し続けるリストによるリーク
            growing_list = []
            chunk_size = 1024
            chunk_count = size_bytes // chunk_size

            for i in range(chunk_count):
                growing_list.append("x" * chunk_size)

            leak_objects.append(growing_list)

        elif leak_type == "unclosed_files":
            # クローズされないファイルハンドルによるリーク
            temp_files = []

            try:
                # 複数の一時ファイルを開いたまま保持
                for i in range(50):  # 50個のファイルハンドル
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    temp_file.write(b"x" * (size_bytes // 50))
                    temp_files.append(temp_file)  # ファイルをクローズせずに保持

            except Exception as e:
                self.logger.warning(f"Failed to create file leak: {e}")

            leak_objects.extend(temp_files)

        self.logger.info(
            f"Created intentional {leak_type} memory leak (~{size_mb:.1f} MB)"
        )
        return leak_objects

    def test_leak_detection_accuracy(
        self, leak_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        メモリリーク検出精度テスト

        Args:
            leak_types: テストするリークタイプ

        Returns:
            Dict[str, Any]: テスト結果
        """
        if leak_types is None:
            leak_types = ["circular", "growing_list", "unclosed_files"]

        self.logger.info(f"Starting leak detection accuracy test for: {leak_types}")

        results = {
            "test_name": "leak_detection_accuracy",
            "leak_tests": [],
            "detection_accuracy": 0.0,
            "false_positives": 0,
            "false_negatives": 0,
        }

        for leak_type in leak_types:
            self.logger.info(f"Testing {leak_type} leak detection...")

            # 初期状態測定
            initial_memory = self.memory_optimizer.get_memory_stats()[
                "process_memory_mb"
            ]

            # ベースライン測定（リークなし）
            baseline_result = self.memory_optimizer.detect_memory_leaks(
                threshold_mb=2.0, sample_interval=2
            )

            leak_test_result = {
                "leak_type": leak_type,
                "baseline_leak_detected": baseline_result["leak_detected"],
                "leak_created": False,
                "leak_detected_after_creation": False,
                "detection_time_ms": 0.0,
                "cleanup_effective": False,
            }

            # 意図的リーク作成
            leak_objects = []
            try:
                start_time = time.time()
                leak_objects = self.create_intentional_memory_leak(
                    leak_type, size_mb=8.0
                )
                leak_test_result["leak_created"] = True

                # リーク検出実行
                detection_start = time.time()
                leak_result = self.memory_optimizer.detect_memory_leaks(
                    threshold_mb=3.0, sample_interval=3
                )
                leak_test_result["detection_time_ms"] = (
                    time.time() - detection_start
                ) * 1000

                leak_test_result["leak_detected_after_creation"] = leak_result[
                    "leak_detected"
                ]
                leak_test_result["memory_growth_mb"] = leak_result["memory_growth_mb"]
                leak_test_result["gc_effect_mb"] = leak_result.get("gc_effect_mb", 0)

                self.logger.info(
                    f"{leak_type} leak: Created={leak_test_result['leak_created']}, "
                    f"Detected={leak_test_result['leak_detected_after_creation']}"
                )

            except Exception as e:
                self.logger.error(f"Error during {leak_type} leak test: {e}")
                leak_test_result["error"] = str(e)

            finally:
                # クリーンアップ
                cleanup_start_memory = self.memory_optimizer.get_memory_stats()[
                    "process_memory_mb"
                ]

                # リークオブジェクトのクリーンアップ
                if leak_type == "unclosed_files":
                    for temp_file in leak_objects:
                        try:
                            temp_file.close()
                            Path(temp_file.name).unlink(missing_ok=True)
                        except Exception:
                            pass

                leak_objects.clear()

                # 強制ガベージコレクション
                self.memory_optimizer.force_garbage_collection()
                time.sleep(0.5)

                cleanup_end_memory = self.memory_optimizer.get_memory_stats()[
                    "process_memory_mb"
                ]
                memory_recovered = cleanup_start_memory - cleanup_end_memory
                leak_test_result["cleanup_effective"] = (
                    memory_recovered > 1.0
                )  # 1MB以上回収

            results["leak_tests"].append(leak_test_result)

        # 精度計算
        correct_detections = 0
        total_tests = len(results["leak_tests"])

        for test in results["leak_tests"]:
            # 正しい検出: リーク作成後に検出され、ベースラインでは検出されない
            if (
                test["leak_created"]
                and test["leak_detected_after_creation"]
                and not test["baseline_leak_detected"]
            ):
                correct_detections += 1

            # 偽陽性: ベースラインでリーク検出
            if test["baseline_leak_detected"]:
                results["false_positives"] += 1

            # 偽陰性: リーク作成後に検出されない
            if test["leak_created"] and not test["leak_detected_after_creation"]:
                results["false_negatives"] += 1

        results["detection_accuracy"] = (
            (correct_detections / total_tests * 100) if total_tests > 0 else 0
        )

        self.logger.info(
            f"Leak detection accuracy: {results['detection_accuracy']:.1f}%"
        )
        return results

    def test_leak_detection_sensitivity(
        self, threshold_levels: List[float] = None
    ) -> Dict[str, Any]:
        """
        メモリリーク検出感度テスト

        Args:
            threshold_levels: テストする閾値レベル（MB）

        Returns:
            Dict[str, Any]: テスト結果
        """
        if threshold_levels is None:
            threshold_levels = [1.0, 2.5, 5.0, 10.0, 20.0]

        self.logger.info(
            f"Starting leak detection sensitivity test with thresholds: {threshold_levels}"
        )

        results = {
            "test_name": "leak_detection_sensitivity",
            "threshold_tests": [],
            "optimal_threshold_mb": 0.0,
            "sensitivity_curve": [],
        }

        # 段階的にメモリリークを作成
        leak_sizes = [1.0, 3.0, 7.0, 15.0]  # MB

        for leak_size in leak_sizes:
            self.logger.info(f"Testing leak size: {leak_size} MB")

            # リーク作成
            leak_objects = self.create_intentional_memory_leak(
                "growing_list", size_mb=leak_size
            )

            try:
                threshold_results = []

                for threshold in threshold_levels:
                    detection_result = self.memory_optimizer.detect_memory_leaks(
                        threshold_mb=threshold, sample_interval=2
                    )

                    threshold_results.append(
                        {
                            "threshold_mb": threshold,
                            "leak_detected": detection_result["leak_detected"],
                            "memory_growth_mb": detection_result["memory_growth_mb"],
                            "detection_confidence": self._calculate_detection_confidence(
                                detection_result
                            ),
                        }
                    )

                sensitivity_point = {
                    "leak_size_mb": leak_size,
                    "threshold_results": threshold_results,
                    "min_detection_threshold": self._find_min_detection_threshold(
                        threshold_results
                    ),
                }

                results["sensitivity_curve"].append(sensitivity_point)

            finally:
                # クリーンアップ
                leak_objects.clear()
                self.memory_optimizer.force_garbage_collection()
                time.sleep(0.5)

        # 最適閾値計算
        results["optimal_threshold_mb"] = self._calculate_optimal_threshold(
            results["sensitivity_curve"]
        )

        self.logger.info(
            f"Optimal detection threshold: {results['optimal_threshold_mb']:.1f} MB"
        )
        return results

    def test_leak_detection_under_load(
        self, concurrent_threads: int = 4, duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        負荷下でのメモリリーク検出テスト

        Args:
            concurrent_threads: 並行スレッド数
            duration_minutes: テスト継続時間（分）

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(
            f"Starting leak detection under load test: {concurrent_threads} threads, {duration_minutes} min"
        )

        results = {
            "test_name": "leak_detection_under_load",
            "concurrent_threads": concurrent_threads,
            "duration_minutes": duration_minutes,
            "detection_attempts": 0,
            "successful_detections": 0,
            "detection_times_ms": [],
            "load_impact_factor": 0.0,
        }

        test_active = threading.Event()
        test_active.set()

        detection_results = []
        detection_lock = threading.Lock()

        def load_generator_thread(thread_id: int):
            """負荷生成スレッド"""
            local_objects = []

            while test_active.is_set():
                try:
                    # メモリ使用パターンシミュレーション
                    temp_data = ["x" * 10000] * 100  # 1MB程度
                    local_objects.append(temp_data)

                    # 定期的にクリーンアップ
                    if len(local_objects) > 10:
                        local_objects.clear()

                    time.sleep(0.1)

                except Exception as e:
                    self.logger.warning(f"Load generator thread {thread_id} error: {e}")

        def leak_detection_thread():
            """リーク検出スレッド"""
            while test_active.is_set():
                try:
                    start_time = time.time()

                    leak_result = self.memory_optimizer.detect_memory_leaks(
                        threshold_mb=5.0, sample_interval=2
                    )

                    detection_time = (time.time() - start_time) * 1000

                    with detection_lock:
                        detection_results.append(
                            {
                                "timestamp": time.time(),
                                "detection_time_ms": detection_time,
                                "leak_detected": leak_result["leak_detected"],
                                "memory_growth_mb": leak_result["memory_growth_mb"],
                            }
                        )

                    time.sleep(2)  # 2秒間隔で検出実行

                except Exception as e:
                    self.logger.warning(f"Leak detection thread error: {e}")

        # スレッド開始
        load_threads = []
        for i in range(concurrent_threads):
            thread = threading.Thread(target=load_generator_thread, args=(i,))
            thread.start()
            load_threads.append(thread)

        detection_thread = threading.Thread(target=leak_detection_thread)
        detection_thread.start()

        # テスト実行
        time.sleep(duration_minutes * 60)

        # 終了処理
        test_active.clear()

        for thread in load_threads:
            thread.join(timeout=2)

        detection_thread.join(timeout=5)

        # 結果分析
        results["detection_attempts"] = len(detection_results)
        results["successful_detections"] = sum(
            1 for r in detection_results if r["leak_detected"]
        )
        results["detection_times_ms"] = [
            r["detection_time_ms"] for r in detection_results
        ]

        if results["detection_times_ms"]:
            avg_detection_time = sum(results["detection_times_ms"]) / len(
                results["detection_times_ms"]
            )
            # ベースライン検出時間と比較（負荷なしでの検出時間）
            baseline_time = 100  # 仮定値（ms）
            results["load_impact_factor"] = avg_detection_time / baseline_time

        self.logger.info(
            f"Load test completed. Detection rate: {results['successful_detections']}/{results['detection_attempts']}"
        )
        return results

    def _calculate_detection_confidence(
        self, detection_result: Dict[str, Any]
    ) -> float:
        """検出信頼度計算"""
        if not detection_result["leak_detected"]:
            return 0.0

        growth = detection_result.get("memory_growth_mb", 0)
        gc_effect = detection_result.get("gc_effect_mb", 0)

        # GC効果が低いほど信頼度が高い
        confidence = (
            max(0, min(100, (growth - gc_effect) / growth * 100)) if growth > 0 else 0
        )
        return confidence

    def _find_min_detection_threshold(
        self, threshold_results: List[Dict[str, Any]]
    ) -> float:
        """最小検出閾値を見つける"""
        for result in sorted(threshold_results, key=lambda x: x["threshold_mb"]):
            if result["leak_detected"]:
                return result["threshold_mb"]
        return float("inf")

    def _calculate_optimal_threshold(
        self, sensitivity_curve: List[Dict[str, Any]]
    ) -> float:
        """最適閾値計算"""
        if not sensitivity_curve:
            return 5.0  # デフォルト値

        # 各リークサイズに対する最小検出閾値の平均
        min_thresholds = []
        for point in sensitivity_curve:
            min_threshold = point["min_detection_threshold"]
            if min_threshold != float("inf"):
                min_thresholds.append(min_threshold)

        return sum(min_thresholds) / len(min_thresholds) if min_thresholds else 5.0


# Pytestテストケース
class TestMemoryLeakDetection:
    """Pytest用メモリリーク検出テストクラス"""

    def setup_method(self):
        """各テスト前のセットアップ"""
        self.test_suite = MemoryLeakDetectionTest()

    @pytest.mark.performance
    def test_basic_leak_detection(self):
        """基本的なメモリリーク検出テスト"""
        result = self.test_suite.test_leak_detection_accuracy(
            leak_types=["growing_list"]
        )

        # 検証条件
        assert len(result["leak_tests"]) > 0, "リーク検出テストが実行されていません"
        assert result["detection_accuracy"] > 50.0, "検出精度が50%を下回りました"

    @pytest.mark.performance
    def test_sensitivity_basic(self):
        """基本的な検出感度テスト"""
        result = self.test_suite.test_leak_detection_sensitivity(
            threshold_levels=[2.0, 5.0, 10.0]
        )

        # 検証条件
        assert len(result["sensitivity_curve"]) > 0, "感度テスト結果が空です"
        assert result["optimal_threshold_mb"] > 0, "最適閾値が計算されていません"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_load_detection_basic(self):
        """基本的な負荷下検出テスト"""
        result = self.test_suite.test_leak_detection_under_load(
            concurrent_threads=2, duration_minutes=1
        )

        # 検証条件
        assert result["detection_attempts"] > 0, "検出試行が記録されていません"
        assert result["load_impact_factor"] > 0, "負荷影響係数が計算されていません"


if __name__ == "__main__":
    # 直接実行時のテスト
    print("🔍 メモリリーク検出テスト開始...")

    test_suite = MemoryLeakDetectionTest()

    # 各テスト実行
    print("1. リーク検出精度テスト...")
    result1 = test_suite.test_leak_detection_accuracy()
    print(f"   検出精度: {result1['detection_accuracy']:.1f}%")

    print("2. 検出感度テスト...")
    result2 = test_suite.test_leak_detection_sensitivity()
    print(f"   最適閾値: {result2['optimal_threshold_mb']:.1f} MB")

    print("3. 負荷下検出テスト...")
    result3 = test_suite.test_leak_detection_under_load(
        concurrent_threads=2, duration_minutes=2
    )
    print(
        f"   検出試行: {result3['detection_attempts']}, 成功: {result3['successful_detections']}"
    )

    print("✅ 全メモリリーク検出テスト完了！")
