"""
オブジェクトリサイクルシステム

大型オブジェクトの効率的な再利用による
メモリ使用量削減とパフォーマンス向上
"""

import gc
import os
import sys
import threading
import time
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ObjectRecycler:
    """オブジェクトリサイクル管理クラス"""

    def __init__(self, max_objects_per_type: int = 50):
        self.max_objects_per_type = max_objects_per_type
        self._recycled_objects: Dict[Type, deque] = defaultdict(deque)
        self._in_use_objects: Dict[Type, Set[int]] = defaultdict(set)
        self._object_metadata: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        # 統計情報
        self.stats = {
            "objects_recycled": 0,
            "objects_reused": 0,
            "objects_created": 0,
            "memory_saved_bytes": 0,
            "recycling_efficiency": 0.0,
        }

        # 型別設定
        self._type_configs: Dict[Type, Dict[str, Any]] = {}

    def register_type(
        self,
        obj_type: Type[T],
        reset_function: Optional[Callable[[T], None]] = None,
        size_calculator: Optional[Callable[[T], int]] = None,
        max_objects: Optional[int] = None,
    ) -> None:
        """オブジェクト型の登録"""

        self._type_configs[obj_type] = {
            "reset_function": reset_function,
            "size_calculator": size_calculator or sys.getsizeof,
            "max_objects": max_objects or self.max_objects_per_type,
            "creation_time": time.time(),
        }

        logger.info(f"Registered type for recycling: {obj_type.__name__}")

    def acquire_object(
        self, obj_type: Type[T], factory: Optional[Callable[[], T]] = None
    ) -> T:
        """オブジェクト取得（リサイクル優先）"""

        with self._lock:
            # リサイクルプールから取得試行
            if obj_type in self._recycled_objects and self._recycled_objects[obj_type]:
                obj = self._recycled_objects[obj_type].popleft()
                obj_id = id(obj)

                # 使用中として記録
                self._in_use_objects[obj_type].add(obj_id)

                # メタデータ更新
                if obj_id in self._object_metadata:
                    self._object_metadata[obj_id]["reused_count"] += 1
                    self._object_metadata[obj_id]["last_reuse"] = time.time()

                self.stats["objects_reused"] += 1
                logger.debug(f"Reused {obj_type.__name__} object (ID: {obj_id})")

                return obj

            # 新規作成
            if factory:
                obj = factory()
            else:
                obj = obj_type()

            obj_id = id(obj)

            # 使用中として記録
            self._in_use_objects[obj_type].add(obj_id)

            # メタデータ記録
            self._object_metadata[obj_id] = {
                "type": obj_type,
                "created_time": time.time(),
                "reused_count": 0,
                "last_reuse": None,
                "size_bytes": self._calculate_object_size(obj, obj_type),
            }

            self.stats["objects_created"] += 1
            logger.debug(f"Created new {obj_type.__name__} object (ID: {obj_id})")

            return obj

    def release_object(self, obj: T) -> None:
        """オブジェクト返却（リサイクル登録）"""

        with self._lock:
            obj_type = type(obj)
            obj_id = id(obj)

            # 使用中リストから削除
            if obj_type in self._in_use_objects:
                self._in_use_objects[obj_type].discard(obj_id)

            # 未登録型は無視
            if obj_type not in self._type_configs:
                logger.debug(f"Unregistered type {obj_type.__name__}, object discarded")
                return

            config = self._type_configs[obj_type]

            # リセット処理
            reset_func = config["reset_function"]
            if reset_func:
                try:
                    reset_func(obj)
                except Exception as e:
                    logger.error(f"Failed to reset {obj_type.__name__} object: {e}")
                    self._cleanup_object_metadata(obj_id)
                    return

            # プール容量チェック
            current_pool_size = len(self._recycled_objects[obj_type])
            max_objects = config["max_objects"]

            if current_pool_size < max_objects:
                # リサイクルプールに追加
                self._recycled_objects[obj_type].append(obj)
                self.stats["objects_recycled"] += 1

                # メモリ節約量計算
                if obj_id in self._object_metadata:
                    obj_size = self._object_metadata[obj_id]["size_bytes"]
                    self.stats["memory_saved_bytes"] += obj_size

                logger.debug(
                    f"Recycled {obj_type.__name__} object (pool size: {current_pool_size + 1})"
                )
            else:
                # プール満杯時は破棄
                self._cleanup_object_metadata(obj_id)
                logger.debug(f"Pool full for {obj_type.__name__}, object discarded")

    def _calculate_object_size(self, obj: Any, obj_type: Type) -> int:
        """オブジェクトサイズ計算"""
        if obj_type in self._type_configs:
            size_calc = self._type_configs[obj_type]["size_calculator"]
            try:
                return size_calc(obj)
            except Exception as e:
                logger.warning(f"Size calculation failed for {obj_type.__name__}: {e}")

        return sys.getsizeof(obj)

    def _cleanup_object_metadata(self, obj_id: int) -> None:
        """オブジェクトメタデータクリーンアップ"""
        if obj_id in self._object_metadata:
            del self._object_metadata[obj_id]

    def clear_type_pool(self, obj_type: Type) -> int:
        """特定型のプールクリア"""
        with self._lock:
            if obj_type in self._recycled_objects:
                cleared_count = len(self._recycled_objects[obj_type])

                # メタデータクリーンアップ
                for obj in self._recycled_objects[obj_type]:
                    self._cleanup_object_metadata(id(obj))

                self._recycled_objects[obj_type].clear()
                logger.info(f"Cleared {cleared_count} {obj_type.__name__} objects")
                return cleared_count

            return 0

    def clear_all_pools(self) -> Dict[Type, int]:
        """全プールクリア"""
        with self._lock:
            cleared_counts = {}

            for obj_type in list(self._recycled_objects.keys()):
                cleared_counts[obj_type] = self.clear_type_pool(obj_type)

            self._object_metadata.clear()
            logger.info("Cleared all recycling pools")

            return cleared_counts

    def get_pool_statistics(self) -> Dict[str, Any]:
        """プール統計取得"""
        with self._lock:
            type_stats = {}

            for obj_type, pool in self._recycled_objects.items():
                in_use_count = len(self._in_use_objects.get(obj_type, set()))

                type_stats[obj_type.__name__] = {
                    "pooled_objects": len(pool),
                    "in_use_objects": in_use_count,
                    "total_objects": len(pool) + in_use_count,
                    "max_pool_size": self._type_configs.get(obj_type, {}).get(
                        "max_objects", 0
                    ),
                }

            # 効率計算
            total_accessed = (
                self.stats["objects_created"] + self.stats["objects_reused"]
            )
            self.stats["recycling_efficiency"] = (
                self.stats["objects_reused"] / total_accessed
                if total_accessed > 0
                else 0.0
            )

            return {
                "overall_stats": self.stats.copy(),
                "type_breakdown": type_stats,
                "registered_types": list(self._type_configs.keys()),
                "memory_usage": {
                    "total_metadata_entries": len(self._object_metadata),
                    "estimated_memory_saved_mb": self.stats["memory_saved_bytes"]
                    / (1024 * 1024),
                },
            }

    def force_cleanup(self) -> Dict[str, Any]:
        """強制クリーンアップ（ガベージコレクション付き）"""
        with self._lock:
            initial_objects = len(gc.get_objects())

            # 全プールクリア
            cleared_counts = self.clear_all_pools()

            # ガベージコレクション
            collected = gc.collect()

            final_objects = len(gc.get_objects())

            result = {
                "initial_objects": initial_objects,
                "final_objects": final_objects,
                "objects_freed": initial_objects - final_objects,
                "gc_collected": collected,
                "cleared_pools": cleared_counts,
            }

            logger.info(f"Force cleanup completed: {result}")
            return result


class TypeBasedRecycler:
    """型別リサイクル戦略"""

    def __init__(self):
        self.recycler = ObjectRecycler()
        self._setup_common_types()

    def _setup_common_types(self) -> None:
        """共通型の設定"""

        # リスト型
        self.recycler.register_type(
            list,
            reset_function=lambda x: x.clear(),
            size_calculator=lambda x: sys.getsizeof(x)
            + sum(sys.getsizeof(item) for item in x),
            max_objects=100,
        )

        # 辞書型
        self.recycler.register_type(
            dict,
            reset_function=lambda x: x.clear(),
            size_calculator=lambda x: sys.getsizeof(x)
            + sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in x.items()),
            max_objects=50,
        )

        # セット型
        self.recycler.register_type(
            set,
            reset_function=lambda x: x.clear(),
            size_calculator=lambda x: sys.getsizeof(x)
            + sum(sys.getsizeof(item) for item in x),
            max_objects=30,
        )

        logger.info("Common types registered for recycling")

    def get_list(self) -> List:
        """リスト取得"""
        return self.recycler.acquire_object(list, factory=list)

    def return_list(self, lst: List) -> None:
        """リスト返却"""
        self.recycler.release_object(lst)

    def get_dict(self) -> Dict:
        """辞書取得"""
        return self.recycler.acquire_object(dict, factory=dict)

    def return_dict(self, dct: Dict) -> None:
        """辞書返却"""
        self.recycler.release_object(dct)

    def get_set(self) -> Set:
        """セット取得"""
        return self.recycler.acquire_object(set, factory=set)

    def return_set(self, st: Set) -> None:
        """セット返却"""
        self.recycler.release_object(st)


class RecycleEffectMeasurer:
    """リサイクル効果測定"""

    def __init__(self, recycler: ObjectRecycler):
        self.recycler = recycler
        self.baseline_measurements = {}

    def measure_baseline(
        self, obj_type: Type, operations: int = 1000
    ) -> Dict[str, Any]:
        """ベースライン測定（リサイクルなし）"""

        start_time = time.time()
        start_memory = self._get_memory_usage()

        objects = []
        for _ in range(operations):
            obj = obj_type()
            # 簡単な操作
            if hasattr(obj, "append") and callable(obj.append):
                obj.append("test")
            elif hasattr(obj, "update") and callable(obj.update):
                obj.update({"test": "value"})
            objects.append(obj)

        # オブジェクト破棄
        del objects
        gc.collect()

        end_time = time.time()
        end_memory = self._get_memory_usage()

        baseline = {
            "operations": operations,
            "creation_time": end_time - start_time,
            "peak_memory_mb": (end_memory - start_memory) / (1024 * 1024),
            "objects_per_second": operations / (end_time - start_time),
        }

        self.baseline_measurements[obj_type] = baseline
        logger.info(f"Baseline measured for {obj_type.__name__}: {baseline}")

        return baseline

    def measure_recycling(
        self, obj_type: Type, operations: int = 1000
    ) -> Dict[str, Any]:
        """リサイクル効果測定"""

        start_time = time.time()
        start_memory = self._get_memory_usage()

        objects = []
        for _ in range(operations):
            obj = self.recycler.acquire_object(obj_type)
            # 簡単な操作
            if hasattr(obj, "append") and callable(obj.append):
                obj.append("test")
            elif hasattr(obj, "update") and callable(obj.update):
                obj.update({"test": "value"})
            objects.append(obj)

        # オブジェクト返却
        for obj in objects:
            self.recycler.release_object(obj)

        end_time = time.time()
        end_memory = self._get_memory_usage()

        recycling_result = {
            "operations": operations,
            "recycling_time": end_time - start_time,
            "peak_memory_mb": (end_memory - start_memory) / (1024 * 1024),
            "objects_per_second": operations / (end_time - start_time),
        }

        # ベースラインとの比較
        if obj_type in self.baseline_measurements:
            baseline = self.baseline_measurements[obj_type]
            recycling_result["improvement"] = {
                "time_improvement": baseline["creation_time"]
                / recycling_result["recycling_time"],
                "memory_improvement": baseline["peak_memory_mb"]
                / recycling_result["peak_memory_mb"],
                "throughput_improvement": recycling_result["objects_per_second"]
                / baseline["objects_per_second"],
            }

        logger.info(f"Recycling measured for {obj_type.__name__}: {recycling_result}")
        return recycling_result

    def _get_memory_usage(self) -> float:
        """メモリ使用量取得"""
        try:
            import psutil

            return psutil.Process().memory_info().rss
        except ImportError:
            return 0.0


# グローバル型別リサイクラー
_global_type_recycler = TypeBasedRecycler()


def get_type_recycler() -> TypeBasedRecycler:
    """グローバル型別リサイクラー取得"""
    return _global_type_recycler


def benchmark_recycling_performance(iterations: int = 5000) -> Dict[str, Any]:
    """リサイクルパフォーマンスベンチマーク"""

    recycler = get_type_recycler()
    measurer = RecycleEffectMeasurer(recycler.recycler)

    results = {}

    # 測定対象型
    test_types = [list, dict, set]

    for obj_type in test_types:
        logger.info(f"Benchmarking {obj_type.__name__}...")

        # ベースライン測定
        baseline = measurer.measure_baseline(obj_type, iterations)

        # リサイクル測定
        recycling = measurer.measure_recycling(obj_type, iterations)

        results[obj_type.__name__] = {
            "baseline": baseline,
            "recycling": recycling,
        }

    # 統計取得
    pool_stats = recycler.recycler.get_pool_statistics()
    results["pool_statistics"] = pool_stats

    return results


def main():
    """CLI エントリーポイント"""
    import argparse
    import json

    os.makedirs("tmp", exist_ok=True)

    parser = argparse.ArgumentParser(description="Object recycler")
    parser.add_argument(
        "--benchmark", action="store_true", help="Run recycling benchmark"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show recycling statistics"
    )
    parser.add_argument("--cleanup", action="store_true", help="Force cleanup")
    parser.add_argument(
        "--iterations", type=int, default=5000, help="Benchmark iterations"
    )

    args = parser.parse_args()

    recycler = get_type_recycler()

    if args.benchmark:
        print("Running recycling benchmark...")
        results = benchmark_recycling_performance(args.iterations)

        benchmark_path = "tmp/recycling_benchmark.json"
        with open(benchmark_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("Benchmark Results:")
        for obj_type, data in results.items():
            if obj_type != "pool_statistics":
                improvement = data["recycling"].get("improvement", {})
                print(f"\n{obj_type}:")
                print(
                    f"  Time improvement: {improvement.get('time_improvement', 0):.2f}x"
                )
                print(
                    f"  Memory improvement: {improvement.get('memory_improvement', 0):.2f}x"
                )
                print(
                    f"  Throughput improvement: {improvement.get('throughput_improvement', 0):.2f}x"
                )

        print(f"\nResults saved: {benchmark_path}")

    elif args.stats:
        print("Recycling statistics:")
        stats = recycler.recycler.get_pool_statistics()

        stats_path = "tmp/recycling_stats.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2, default=str)

        print(json.dumps(stats, indent=2, default=str))
        print(f"Stats saved: {stats_path}")

    elif args.cleanup:
        print("Performing force cleanup...")
        cleanup_results = recycler.recycler.force_cleanup()

        cleanup_path = "tmp/cleanup_results.json"
        with open(cleanup_path, "w") as f:
            json.dump(cleanup_results, f, indent=2)

        print("Cleanup completed:")
        print(f"  Objects freed: {cleanup_results['objects_freed']}")
        print(f"  GC collected: {cleanup_results['gc_collected']}")
        print(f"Results saved: {cleanup_path}")

    else:
        print("No action specified. Use --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
