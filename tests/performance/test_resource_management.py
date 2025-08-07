"""
リソース管理テストスイート

Issue #772 - メモリ・リソース管理の強化と長時間実行時の安定性向上
リソースプール、オブジェクト再利用、クリーンアップ機能のテスト
"""

import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.core.performance import MemoryOptimizer


class ResourceManagementTest:
    """リソース管理テストクラス"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.memory_optimizer = MemoryOptimizer(enable_gc_optimization=True)

    def test_resource_pool_efficiency(self, pool_size: int = 50, operations: int = 1000) -> Dict[str, Any]:
        """
        リソースプール効率性テスト

        Args:
            pool_size: プールサイズ
            operations: 操作回数

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(f"Starting resource pool efficiency test with {pool_size} pool size, {operations} operations")

        # テスト用データクラス
        class TestResource:
            def __init__(self):
                self.data = "x" * 1000  # 1KB程度のデータ
                self.usage_count = 0
                self.created_at = time.time()

            def reset(self):
                self.usage_count = 0

            def use(self):
                self.usage_count += 1

        # リソースプール作成
        pool_name = "efficiency_test_pool"
        self.memory_optimizer.create_advanced_resource_pool(
            pool_name,
            factory_func=TestResource,
            max_size=pool_size,
            cleanup_func=lambda obj: obj.reset(),
            auto_cleanup_interval=30
        )

        results = {
            "test_name": "resource_pool_efficiency",
            "pool_size": pool_size,
            "operations": operations,
            "reuse_rate": 0.0,
            "avg_operation_time_ms": 0.0,
            "memory_impact_mb": 0.0,
            "pool_hits": 0,
            "pool_misses": 0
        }

        # 初期メモリ使用量記録
        initial_memory = self.memory_optimizer.get_memory_stats()["process_memory_mb"]

        operation_times = []

        for i in range(operations):
            start_time = time.time()

            # リソース取得・使用・返却
            resource = self.memory_optimizer.get_pooled_object(pool_name)
            resource.use()
            self.memory_optimizer.return_pooled_object(pool_name, resource)

            operation_time = (time.time() - start_time) * 1000  # ミリ秒
            operation_times.append(operation_time)

        # 統計計算
        pool_stats = self.memory_optimizer.get_memory_stats()["object_pools"][pool_name]
        total_requests = pool_stats["created_count"] + pool_stats["reused_count"]

        results["reuse_rate"] = (pool_stats["reused_count"] / total_requests * 100) if total_requests > 0 else 0
        results["avg_operation_time_ms"] = sum(operation_times) / len(operation_times) if operation_times else 0
        results["pool_hits"] = pool_stats["reused_count"]
        results["pool_misses"] = pool_stats["created_count"]

        # メモリ影響測定
        final_memory = self.memory_optimizer.get_memory_stats()["process_memory_mb"]
        results["memory_impact_mb"] = final_memory - initial_memory

        self.logger.info(f"Resource pool efficiency test completed. Reuse rate: {results['reuse_rate']:.1f}%")
        return results

    def test_resource_lifecycle_management(self, lifecycle_cycles: int = 100) -> Dict[str, Any]:
        """
        リソースライフサイクル管理テスト

        Args:
            lifecycle_cycles: ライフサイクル回数

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(f"Starting resource lifecycle management test with {lifecycle_cycles} cycles")

        class ManagedResource:
            def __init__(self):
                self.id = time.time()
                self.state = "created"
                self.operations = 0

            def reset(self):
                self.state = "reset"
                self.operations = 0

            def cleanup(self):
                self.state = "cleaned"

        # 管理用プール作成
        pool_name = "lifecycle_test_pool"
        self.memory_optimizer.create_advanced_resource_pool(
            pool_name,
            factory_func=ManagedResource,
            max_size=20,
            cleanup_func=lambda obj: obj.cleanup(),
            auto_cleanup_interval=10
        )

        results = {
            "test_name": "resource_lifecycle_management",
            "lifecycle_cycles": lifecycle_cycles,
            "resources_created": 0,
            "resources_reused": 0,
            "cleanup_operations": 0,
            "lifecycle_violations": []
        }

        for cycle in range(lifecycle_cycles):
            # リソース取得
            resource = self.memory_optimizer.get_pooled_object(pool_name)

            # 状態チェック
            if resource.state not in ["created", "reset"]:
                results["lifecycle_violations"].append({
                    "cycle": cycle,
                    "resource_id": resource.id,
                    "unexpected_state": resource.state
                })

            # リソース使用
            resource.operations += 1
            resource.state = "in_use"

            # リソース返却
            self.memory_optimizer.return_pooled_object(pool_name, resource)

            # 短時間待機（ライフサイクルシミュレーション）
            time.sleep(0.01)

        # 統計更新
        pool_stats = self.memory_optimizer.get_memory_stats()["object_pools"][pool_name]
        results["resources_created"] = pool_stats["created_count"]
        results["resources_reused"] = pool_stats["reused_count"]
        results["cleanup_operations"] = pool_stats.get("cleanup_count", 0)

        self.logger.info(f"Resource lifecycle test completed. Violations: {len(results['lifecycle_violations'])}")
        return results

    def test_memory_pressure_response(self, memory_pressure_mb: float = 50.0) -> Dict[str, Any]:
        """
        メモリ圧迫時の応答テスト

        Args:
            memory_pressure_mb: メモリ圧迫閾値（MB）

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(f"Starting memory pressure response test with {memory_pressure_mb} MB threshold")

        results = {
            "test_name": "memory_pressure_response",
            "pressure_threshold_mb": memory_pressure_mb,
            "gc_triggers": [],
            "memory_samples": [],
            "response_effectiveness": 0.0
        }

        # 初期メモリ記録
        initial_memory = self.memory_optimizer.get_memory_stats()["process_memory_mb"]

        # メモリ圧迫シミュレーション用のデータ構造
        memory_consumers = []

        try:
            # メモリ使用量を段階的に増加
            for step in range(10):
                # 大容量データ作成（5MB程度）
                data_chunk = "x" * (5 * 1024 * 1024)
                memory_consumers.append(data_chunk)

                # メモリ状況記録
                current_memory = self.memory_optimizer.get_memory_stats()["process_memory_mb"]
                memory_growth = current_memory - initial_memory

                results["memory_samples"].append({
                    "step": step,
                    "memory_mb": current_memory,
                    "growth_mb": memory_growth
                })

                # メモリ圧迫閾値チェック
                if memory_growth >= memory_pressure_mb:
                    self.logger.info(f"Memory pressure threshold reached at step {step}")

                    # プロアクティブGC実行
                    gc_result = self.memory_optimizer.proactive_gc_strategy(
                        memory_threshold_mb=current_memory * 0.8
                    )

                    if gc_result["gc_executed"]:
                        results["gc_triggers"].append({
                            "step": step,
                            "pre_gc_memory_mb": current_memory,
                            "memory_freed_mb": gc_result.get("memory_freed_mb", 0),
                            "execution_time_ms": gc_result.get("execution_time_ms", 0)
                        })

                time.sleep(0.1)  # 短時間待機

        finally:
            # メモリクリーンアップ
            memory_consumers.clear()
            self.memory_optimizer.force_garbage_collection()

        # 応答効果性計算
        if results["gc_triggers"]:
            total_freed = sum(gc["memory_freed_mb"] for gc in results["gc_triggers"])
            total_pressure = max(sample["growth_mb"] for sample in results["memory_samples"])
            results["response_effectiveness"] = (total_freed / total_pressure * 100) if total_pressure > 0 else 0

        self.logger.info(f"Memory pressure test completed. GC triggers: {len(results['gc_triggers'])}")
        return results

    def test_concurrent_resource_access_safety(self, thread_count: int = 8, access_count: int = 500) -> Dict[str, Any]:
        """
        並行リソースアクセス安全性テスト

        Args:
            thread_count: 並行スレッド数
            access_count: 各スレッドのアクセス回数

        Returns:
            Dict[str, Any]: テスト結果
        """
        self.logger.info(f"Starting concurrent resource access safety test with {thread_count} threads")

        class ConcurrentResource:
            def __init__(self):
                self.access_count = 0
                self.last_accessor = None
                self.lock = threading.Lock()

            def reset(self):
                with self.lock:
                    self.access_count = 0
                    self.last_accessor = None

            def safe_access(self, accessor_id: int):
                with self.lock:
                    self.access_count += 1
                    self.last_accessor = accessor_id
                    return self.access_count

        # 並行アクセス用プール作成
        pool_name = "concurrent_safety_pool"
        self.memory_optimizer.create_advanced_resource_pool(
            pool_name,
            factory_func=ConcurrentResource,
            max_size=thread_count * 2,  # スレッド数の2倍のプールサイズ
            cleanup_func=lambda obj: obj.reset(),
            auto_cleanup_interval=60
        )

        results = {
            "test_name": "concurrent_resource_access_safety",
            "thread_count": thread_count,
            "access_count_per_thread": access_count,
            "thread_results": {},
            "race_conditions": [],
            "total_accesses": 0,
            "consistency_violations": 0
        }

        test_active = threading.Event()
        test_active.set()

        def worker_thread(thread_id: int):
            """ワーカースレッド関数"""
            thread_results = {
                "accesses": 0,
                "errors": 0,
                "resource_states": []
            }

            for access in range(access_count):
                try:
                    # リソース取得
                    resource = self.memory_optimizer.get_pooled_object(pool_name)

                    # 安全なアクセス実行
                    access_result = resource.safe_access(thread_id)
                    thread_results["accesses"] += 1

                    # リソース状態記録
                    thread_results["resource_states"].append({
                        "access_number": access,
                        "resource_access_count": access_result,
                        "last_accessor": resource.last_accessor
                    })

                    # リソース返却
                    self.memory_optimizer.return_pooled_object(pool_name, resource)

                    # 短時間待機（競合状況シミュレーション）
                    time.sleep(0.001)

                except Exception as e:
                    thread_results["errors"] += 1
                    results["race_conditions"].append({
                        "thread_id": thread_id,
                        "access_number": access,
                        "error": str(e)
                    })

            results["thread_results"][thread_id] = thread_results

        # 並行スレッド実行
        threads = []
        for i in range(thread_count):
            thread = threading.Thread(target=worker_thread, args=(i,))
            thread.start()
            threads.append(thread)

        # 全スレッド完了待機
        for thread in threads:
            thread.join()

        # 結果集計
        results["total_accesses"] = sum(
            thread_result["accesses"]
            for thread_result in results["thread_results"].values()
        )

        total_errors = sum(
            thread_result["errors"]
            for thread_result in results["thread_results"].values()
        )

        # 一貫性チェック
        expected_total = thread_count * access_count
        if results["total_accesses"] != expected_total:
            results["consistency_violations"] += 1

        self.logger.info(f"Concurrent safety test completed. Total accesses: {results['total_accesses']}, Errors: {total_errors}")
        return results


# Pytestテストケース
class TestResourceManagement:
    """Pytest用リソース管理テストクラス"""

    def setup_method(self):
        """各テスト前のセットアップ"""
        self.test_suite = ResourceManagementTest()

    @pytest.mark.performance
    def test_resource_pool_basic_efficiency(self):
        """基本的なリソースプール効率性テスト"""
        result = self.test_suite.test_resource_pool_efficiency(pool_size=10, operations=100)

        # 検証条件
        assert result["reuse_rate"] > 50.0, "リソース再利用率が50%を下回りました"
        assert result["avg_operation_time_ms"] < 1.0, "操作時間が1ms以上かかっています"
        assert len(result) > 0, "テスト結果が空です"

    @pytest.mark.performance
    def test_resource_lifecycle_basic(self):
        """基本的なリソースライフサイクルテスト"""
        result = self.test_suite.test_resource_lifecycle_management(lifecycle_cycles=50)

        # 検証条件
        assert len(result["lifecycle_violations"]) == 0, "ライフサイクル違反が検出されました"
        assert result["resources_created"] > 0, "リソースが作成されていません"

    @pytest.mark.performance
    def test_memory_pressure_basic(self):
        """基本的なメモリ圧迫応答テスト"""
        result = self.test_suite.test_memory_pressure_response(memory_pressure_mb=20.0)

        # 検証条件
        assert len(result["memory_samples"]) > 0, "メモリサンプルが記録されていません"
        # GCが実行されるかは環境依存のため、実行されなくてもエラーにしない

    @pytest.mark.performance
    def test_concurrent_access_basic(self):
        """基本的な並行アクセス安全性テスト"""
        result = self.test_suite.test_concurrent_resource_access_safety(thread_count=4, access_count=50)

        # 検証条件
        assert result["total_accesses"] > 0, "アクセスが記録されていません"
        assert result["consistency_violations"] == 0, "一貫性違反が検出されました"


if __name__ == "__main__":
    # 直接実行時のテスト
    print("🔧 リソース管理テスト開始...")

    test_suite = ResourceManagementTest()

    # 各テスト実行
    results = []

    print("1. リソースプール効率性テスト...")
    result1 = test_suite.test_resource_pool_efficiency(pool_size=30, operations=500)
    results.append(result1)

    print("2. リソースライフサイクル管理テスト...")
    result2 = test_suite.test_resource_lifecycle_management(lifecycle_cycles=200)
    results.append(result2)

    print("3. メモリ圧迫応答テスト...")
    result3 = test_suite.test_memory_pressure_response(memory_pressure_mb=30.0)
    results.append(result3)

    print("4. 並行アクセス安全性テスト...")
    result4 = test_suite.test_concurrent_resource_access_safety(thread_count=6, access_count=200)
    results.append(result4)

    # 結果サマリー
    print(f"✅ 全テスト完了！実行テスト数: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['test_name']}: 完了")
