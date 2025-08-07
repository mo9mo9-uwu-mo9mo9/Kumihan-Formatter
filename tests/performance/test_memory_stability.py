"""
長時間実行メモリ安定性テストスイート

Issue #772 - メモリ・リソース管理の強化と長時間実行時の安定性向上
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.core.performance import MemoryOptimizer


class LongRunningMemoryTest:
    """長時間実行メモリ安定性テストクラス"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.memory_optimizer = MemoryOptimizer(enable_gc_optimization=True)
        self.test_results: List[Dict[str, Any]] = []

    def test_memory_stability_continuous(self, duration_minutes: int = 30) -> Dict[str, Any]:
        """
        継続的メモリ安定性テスト

        Args:
            duration_minutes: テスト実行時間（分）

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(f"Starting continuous memory stability test for {duration_minutes} minutes")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        results = {
            "test_name": "continuous_memory_stability",
            "duration_minutes": duration_minutes,
            "samples": [],
            "leak_detections": [],
            "gc_runs": [],
            "max_memory_mb": 0.0,
            "avg_memory_mb": 0.0,
            "memory_growth_mb": 0.0,
            "stability_score": 0.0
        }

        sample_interval = 30  # 30秒間隔でサンプリング
        last_sample_time = start_time

        while time.time() < end_time:
            current_time = time.time()

            if current_time - last_sample_time >= sample_interval:
                # メモリ状態をサンプリング
                memory_stats = self.memory_optimizer.get_memory_stats()
                sample = {
                    "timestamp": current_time,
                    "elapsed_minutes": (current_time - start_time) / 60,
                    "memory_mb": memory_stats["process_memory_mb"],
                    "virtual_memory_mb": memory_stats["virtual_memory_mb"]
                }
                results["samples"].append(sample)

                # 最大メモリ使用量更新
                if sample["memory_mb"] > results["max_memory_mb"]:
                    results["max_memory_mb"] = sample["memory_mb"]

                # メモリリーク検出実行
                leak_info = self.memory_optimizer.detect_memory_leaks(
                    threshold_mb=5.0,
                    sample_interval=3
                )
                if leak_info["leak_detected"]:
                    results["leak_detections"].append({
                        "timestamp": current_time,
                        "elapsed_minutes": sample["elapsed_minutes"],
                        "leak_info": leak_info
                    })
                    self.logger.warning(f"Memory leak detected at {sample['elapsed_minutes']:.1f} minutes")

                # プロアクティブGC実行
                gc_result = self.memory_optimizer.proactive_gc_strategy(
                    memory_threshold_mb=80.0
                )
                if gc_result["gc_executed"]:
                    results["gc_runs"].append({
                        "timestamp": current_time,
                        "elapsed_minutes": sample["elapsed_minutes"],
                        "gc_result": gc_result
                    })

                last_sample_time = current_time

            # CPU使用率を下げるため少し待機
            time.sleep(1)

        # 結果分析
        if results["samples"]:
            memory_values = [s["memory_mb"] for s in results["samples"]]
            results["avg_memory_mb"] = sum(memory_values) / len(memory_values)
            results["memory_growth_mb"] = results["samples"][-1]["memory_mb"] - results["samples"][0]["memory_mb"]

            # 安定性スコア計算（メモリ使用量の変動が少ないほど高スコア）
            if len(memory_values) > 1:
                memory_variance = sum((x - results["avg_memory_mb"]) ** 2 for x in memory_values) / len(memory_values)
                results["stability_score"] = max(0, 100 - (memory_variance / results["avg_memory_mb"] * 100))
            else:
                results["stability_score"] = 100

        self.logger.info(f"Continuous memory test completed. Stability score: {results['stability_score']:.1f}")
        return results

    def test_cyclic_processing_stability(self, cycles: int = 1000) -> Dict[str, Any]:
        """
        繰り返し処理メモリ安定性テスト

        Args:
            cycles: 実行サイクル数

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(f"Starting cyclic processing stability test for {cycles} cycles")

        results = {
            "test_name": "cyclic_processing_stability",
            "cycles": cycles,
            "cycle_results": [],
            "memory_leak_detected": False,
            "max_memory_growth_mb": 0.0,
            "avg_cycle_time_ms": 0.0
        }

        initial_memory = self.memory_optimizer.get_memory_stats()["process_memory_mb"]
        cycle_times = []

        # オブジェクトプール作成
        self.memory_optimizer.create_advanced_resource_pool(
            "test_objects",
            factory_func=lambda: {"data": "x" * 1000, "counter": 0},
            max_size=50,
            cleanup_func=lambda obj: obj.clear(),
            auto_cleanup_interval=60
        )

        for cycle in range(cycles):
            cycle_start = time.time()

            # テストデータ処理シミュレーション
            test_objects = []
            for i in range(10):
                obj = self.memory_optimizer.get_pooled_object("test_objects")
                obj["counter"] = cycle * 10 + i
                test_objects.append(obj)

            # オブジェクトをプールに返却
            for obj in test_objects:
                self.memory_optimizer.return_pooled_object("test_objects", obj)

            cycle_time = (time.time() - cycle_start) * 1000  # ミリ秒
            cycle_times.append(cycle_time)

            # 定期的なメモリチェック（100サイクルごと）
            if cycle % 100 == 0:
                current_memory = self.memory_optimizer.get_memory_stats()["process_memory_mb"]
                memory_growth = current_memory - initial_memory

                cycle_result = {
                    "cycle": cycle,
                    "memory_mb": current_memory,
                    "memory_growth_mb": memory_growth,
                    "cycle_time_ms": cycle_time
                }
                results["cycle_results"].append(cycle_result)

                if memory_growth > results["max_memory_growth_mb"]:
                    results["max_memory_growth_mb"] = memory_growth

                # メモリリーク検出
                if memory_growth > 10.0:  # 10MB以上の増加
                    leak_info = self.memory_optimizer.detect_memory_leaks(threshold_mb=5.0)
                    if leak_info["leak_detected"]:
                        results["memory_leak_detected"] = True
                        self.logger.warning(f"Memory leak detected at cycle {cycle}")

                self.logger.debug(f"Cycle {cycle}: Memory {current_memory:.2f} MB (+{memory_growth:.2f} MB)")

        # 平均サイクル時間計算
        results["avg_cycle_time_ms"] = sum(cycle_times) / len(cycle_times) if cycle_times else 0

        self.logger.info(f"Cyclic processing test completed. Max memory growth: {results['max_memory_growth_mb']:.2f} MB")
        return results

    def test_concurrent_memory_access(self, thread_count: int = 4, duration_minutes: int = 10) -> Dict[str, Any]:
        """
        並行メモリアクセス安定性テスト

        Args:
            thread_count: 並行スレッド数
            duration_minutes: テスト実行時間（分）

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(f"Starting concurrent memory access test with {thread_count} threads for {duration_minutes} minutes")

        results = {
            "test_name": "concurrent_memory_access",
            "thread_count": thread_count,
            "duration_minutes": duration_minutes,
            "thread_results": [],
            "memory_samples": [],
            "errors": []
        }

        # 共有リソースプール作成
        for i in range(thread_count):
            pool_name = f"concurrent_pool_{i}"
            self.memory_optimizer.create_advanced_resource_pool(
                pool_name,
                factory_func=lambda: {"thread_data": "x" * 500, "operations": 0},
                max_size=20,
                cleanup_func=lambda obj: obj.clear(),
                auto_cleanup_interval=120
            )

        test_active = threading.Event()
        test_active.set()
        thread_results = {}

        def worker_thread(thread_id: int):
            """ワーカースレッド関数"""
            pool_name = f"concurrent_pool_{thread_id}"
            operations = 0
            errors = 0

            while test_active.is_set():
                try:
                    # オブジェクト取得・操作・返却
                    obj = self.memory_optimizer.get_pooled_object(pool_name)
                    obj["operations"] += 1
                    operations += 1

                    # 軽微な処理シミュレーション
                    time.sleep(0.001)

                    self.memory_optimizer.return_pooled_object(pool_name, obj)

                except Exception as e:
                    errors += 1
                    results["errors"].append({
                        "thread_id": thread_id,
                        "error": str(e),
                        "timestamp": time.time()
                    })

            thread_results[thread_id] = {
                "operations": operations,
                "errors": errors
            }

        # スレッド開始
        threads = []
        start_time = time.time()

        for i in range(thread_count):
            thread = threading.Thread(target=worker_thread, args=(i,))
            thread.start()
            threads.append(thread)

        # メモリ監視
        monitoring_active = True
        def memory_monitor():
            while monitoring_active and test_active.is_set():
                memory_stats = self.memory_optimizer.get_memory_stats()
                results["memory_samples"].append({
                    "timestamp": time.time(),
                    "elapsed_minutes": (time.time() - start_time) / 60,
                    "memory_mb": memory_stats["process_memory_mb"],
                    "pool_stats": memory_stats["object_pools"]
                })
                time.sleep(5)  # 5秒間隔でサンプリング

        monitor_thread = threading.Thread(target=memory_monitor)
        monitor_thread.start()

        # テスト実行
        time.sleep(duration_minutes * 60)

        # 終了処理
        test_active.clear()
        monitoring_active = False

        for thread in threads:
            thread.join(timeout=5)

        monitor_thread.join(timeout=2)

        results["thread_results"] = thread_results

        # 結果サマリー
        total_operations = sum(r["operations"] for r in thread_results.values())
        total_errors = sum(r["errors"] for r in thread_results.values())

        self.logger.info(f"Concurrent test completed. Operations: {total_operations}, Errors: {total_errors}")

        return results

    def generate_test_report(self, test_results: List[Dict[str, Any]]) -> str:
        """テスト結果レポート生成"""
        from datetime import datetime

        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_report = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>長時間実行メモリ安定性テストレポート</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; color: #2c3e50; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ background-color: #d4edda; border-color: #c3e6cb; }}
        .fail {{ background-color: #f8d7da; border-color: #f5c6cb; }}
        .warning {{ background-color: #fff3cd; border-color: #ffeaa7; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 長時間実行メモリ安定性テストレポート</h1>
        <p>Issue #772 - メモリ・リソース管理強化システム</p>
        <p>生成日時: {report_time}</p>
    </div>
    '''

        for test_result in test_results:
            test_name = test_result.get("test_name", "Unknown Test")

            # テスト結果の成功/失敗判定
            if test_name == "continuous_memory_stability":
                status_class = "pass" if test_result.get("stability_score", 0) > 70 else "warning"
                status_text = f"安定性スコア: {test_result.get('stability_score', 0):.1f}"
            elif test_name == "cyclic_processing_stability":
                status_class = "pass" if not test_result.get("memory_leak_detected", False) else "fail"
                status_text = "メモリリーク検出なし" if not test_result.get("memory_leak_detected", False) else "メモリリーク検出"
            elif test_name == "concurrent_memory_access":
                error_count = len(test_result.get("errors", []))
                status_class = "pass" if error_count == 0 else "warning"
                status_text = f"エラー数: {error_count}"
            else:
                status_class = "pass"
                status_text = "完了"

            html_report += f'''
    <div class="test-section {status_class}">
        <h2>📋 {test_name}</h2>
        <p><strong>ステータス:</strong> {status_text}</p>
        '''

            # テスト固有の詳細情報
            if test_name == "continuous_memory_stability":
                html_report += f'''
        <p><strong>実行時間:</strong> {test_result.get('duration_minutes', 0)} 分</p>
        <p><strong>最大メモリ使用量:</strong> {test_result.get('max_memory_mb', 0):.2f} MB</p>
        <p><strong>平均メモリ使用量:</strong> {test_result.get('avg_memory_mb', 0):.2f} MB</p>
        <p><strong>メモリ増加量:</strong> {test_result.get('memory_growth_mb', 0):.2f} MB</p>
        <p><strong>リーク検出回数:</strong> {len(test_result.get('leak_detections', []))}</p>
        '''

            elif test_name == "cyclic_processing_stability":
                html_report += f'''
        <p><strong>実行サイクル数:</strong> {test_result.get('cycles', 0):,}</p>
        <p><strong>最大メモリ増加:</strong> {test_result.get('max_memory_growth_mb', 0):.2f} MB</p>
        <p><strong>平均サイクル時間:</strong> {test_result.get('avg_cycle_time_ms', 0):.2f} ms</p>
        '''

            elif test_name == "concurrent_memory_access":
                html_report += f'''
        <p><strong>並行スレッド数:</strong> {test_result.get('thread_count', 0)}</p>
        <p><strong>実行時間:</strong> {test_result.get('duration_minutes', 0)} 分</p>
        <p><strong>総操作数:</strong> {sum(r.get('operations', 0) for r in test_result.get('thread_results', {}).values()):,}</p>
        '''

            html_report += '</div>'

        html_report += '''
</body>
</html>
        '''

        return html_report.strip()


# テスト実行用のヘルパー関数
def run_comprehensive_memory_tests(quick_mode: bool = False) -> Dict[str, Any]:
    """包括的メモリテスト実行"""
    test_suite = LongRunningMemoryTest()

    if quick_mode:
        # クイックテスト（短時間）
        duration_minutes = 2
        cycles = 100
        thread_duration = 1
    else:
        # フルテスト
        duration_minutes = 30
        cycles = 1000
        thread_duration = 10

    results = []

    # 継続的メモリ安定性テスト
    result1 = test_suite.test_memory_stability_continuous(duration_minutes)
    results.append(result1)

    # 繰り返し処理安定性テスト
    result2 = test_suite.test_cyclic_processing_stability(cycles)
    results.append(result2)

    # 並行メモリアクセステスト
    result3 = test_suite.test_concurrent_memory_access(thread_count=4, duration_minutes=thread_duration)
    results.append(result3)

    # レポート生成
    report_html = test_suite.generate_test_report(results)

    return {
        "test_results": results,
        "report_html": report_html,
        "summary": {
            "total_tests": len(results),
            "completed_tests": len([r for r in results if r]),
            "quick_mode": quick_mode
        }
    }


if __name__ == "__main__":
    # 直接実行時のテスト
    print("🧪 長時間実行メモリ安定性テスト開始...")

    # クイックモードでテスト実行
    comprehensive_results = run_comprehensive_memory_tests(quick_mode=True)

    # 結果保存
    import tempfile
    report_path = tempfile.mktemp(suffix=".html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(comprehensive_results["report_html"])

    print(f"✅ テスト完了！レポート: {report_path}")
    print(f"📊 完了テスト数: {comprehensive_results['summary']['completed_tests']}")
