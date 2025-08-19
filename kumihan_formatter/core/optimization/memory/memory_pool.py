"""
メモリプール管理

オブジェクトプールによる効率的なメモリ使用量削減システム
"""

import gc
import os
import threading
import time
import weakref
from collections import defaultdict, deque
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class MemoryPool(Generic[T]):
    """汎用オブジェクトプールクラス"""

    def __init__(
        self,
        factory: Callable[[], T],
        reset_func: Optional[Callable[[T], None]] = None,
        max_size: int = 100,
        ttl_seconds: Optional[int] = None,
    ):
        self.factory = factory
        self.reset_func = reset_func
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        self._pool: deque = deque()
        self._in_use: Set[int] = set()
        self._creation_times: Dict[int, float] = {}
        self._lock = threading.Lock()

        # 統計情報
        self.stats = {
            "created": 0,
            "reused": 0,
            "returned": 0,
            "expired": 0,
            "max_pool_size": 0,
        }

    def acquire(self) -> T:
        """オブジェクト取得"""
        with self._lock:
            # 期限切れオブジェクトのクリーンアップ
            self._cleanup_expired()

            obj = None

            # プールから再利用可能オブジェクト取得
            while self._pool and obj is None:
                candidate = self._pool.popleft()
                obj_id = id(candidate)

                # 期限チェック
                if self.ttl_seconds and obj_id in self._creation_times:
                    age = time.time() - self._creation_times[obj_id]
                    if age > self.ttl_seconds:
                        del self._creation_times[obj_id]
                        self.stats["expired"] += 1
                        continue

                obj = candidate
                self.stats["reused"] += 1
                logger.debug(f"Reused object from pool (pool size: {len(self._pool)})")

            # プールが空の場合は新規作成
            if obj is None:
                obj = self.factory()
                self.stats["created"] += 1
                logger.debug(
                    f"Created new object (total created: {self.stats['created']})"
                )

            # 使用中として記録
            obj_id = id(obj)
            self._in_use.add(obj_id)
            if obj_id not in self._creation_times:
                self._creation_times[obj_id] = time.time()

            return obj

    def release(self, obj: T) -> None:
        """オブジェクト返却"""
        with self._lock:
            obj_id = id(obj)

            if obj_id not in self._in_use:
                logger.warning("Attempted to release object not acquired from pool")
                return

            self._in_use.remove(obj_id)

            # リセット処理
            if self.reset_func:
                try:
                    self.reset_func(obj)
                except Exception as e:
                    logger.error(f"Failed to reset object: {e}")
                    if obj_id in self._creation_times:
                        del self._creation_times[obj_id]
                    return

            # プールサイズ確認
            if len(self._pool) < self.max_size:
                self._pool.append(obj)
                self.stats["returned"] += 1
                self.stats["max_pool_size"] = max(
                    self.stats["max_pool_size"], len(self._pool)
                )
                logger.debug(f"Returned object to pool (pool size: {len(self._pool)})")
            else:
                # プールが満杯の場合は破棄
                if obj_id in self._creation_times:
                    del self._creation_times[obj_id]
                logger.debug("Pool full, discarding object")

    def _cleanup_expired(self) -> None:
        """期限切れオブジェクトのクリーンアップ"""
        if not self.ttl_seconds:
            return

        current_time = time.time()
        expired_objects = []

        # 期限切れオブジェクト特定
        for i, obj in enumerate(self._pool):
            obj_id = id(obj)
            if obj_id in self._creation_times:
                age = current_time - self._creation_times[obj_id]
                if age > self.ttl_seconds:
                    expired_objects.append(i)

        # 期限切れオブジェクト削除（逆順で削除）
        for i in reversed(expired_objects):
            obj = self._pool[i]
            del self._pool[i]
            obj_id = id(obj)
            if obj_id in self._creation_times:
                del self._creation_times[obj_id]
            self.stats["expired"] += 1

    def clear(self) -> None:
        """プールクリア"""
        with self._lock:
            self._pool.clear()
            self._creation_times.clear()
            logger.info("Memory pool cleared")

    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        with self._lock:
            return {
                **self.stats,
                "current_pool_size": len(self._pool),
                "objects_in_use": len(self._in_use),
                "total_objects": len(self._creation_times),
                "efficiency": (
                    self.stats["reused"]
                    / (self.stats["created"] + self.stats["reused"])
                    if (self.stats["created"] + self.stats["reused"]) > 0
                    else 0
                ),
            }


class ObjectPool:
    """特定オブジェクト用プール"""

    def __init__(self, obj_type: type, max_size: int = 50):
        self.obj_type = obj_type
        self.max_size = max_size
        self._pools: Dict[str, MemoryPool] = {}
        self._lock = threading.Lock()

    def get_pool(self, pool_key: str = "default") -> MemoryPool:
        """プール取得（遅延作成）"""
        with self._lock:
            if pool_key not in self._pools:
                self._pools[pool_key] = MemoryPool(
                    factory=lambda: self.obj_type(),
                    max_size=self.max_size,
                    ttl_seconds=600,  # 10分
                )
                logger.info(f"Created new pool for {self.obj_type.__name__}:{pool_key}")

            return self._pools[pool_key]

    def acquire(self, pool_key: str = "default") -> Any:
        """オブジェクト取得"""
        return self.get_pool(pool_key).acquire()

    def release(self, obj: Any, pool_key: str = "default") -> None:
        """オブジェクト返却"""
        self.get_pool(pool_key).release(obj)

    def clear_all(self) -> None:
        """全プールクリア"""
        with self._lock:
            for pool in self._pools.values():
                pool.clear()
            self._pools.clear()
            logger.info(f"Cleared all pools for {self.obj_type.__name__}")


class PoolManager:
    """複数プール統合管理"""

    def __init__(self):
        self._object_pools: Dict[type, ObjectPool] = {}
        self._string_pool: Optional[MemoryPool] = None
        self._list_pool: Optional[MemoryPool] = None
        self._dict_pool: Optional[MemoryPool] = None
        self._lock = threading.Lock()

        # 自動初期化
        self._initialize_common_pools()

    def _initialize_common_pools(self) -> None:
        """共通プールの初期化"""
        # 文字列プール（小さなバッファ用）
        self._string_pool = MemoryPool(
            factory=lambda: [],
            reset_func=lambda x: x.clear(),
            max_size=200,
            ttl_seconds=300,
        )

        # リストプール
        self._list_pool = MemoryPool(
            factory=lambda: [],
            reset_func=lambda x: x.clear(),
            max_size=100,
            ttl_seconds=300,
        )

        # 辞書プール
        self._dict_pool = MemoryPool(
            factory=lambda: {},
            reset_func=lambda x: x.clear(),
            max_size=100,
            ttl_seconds=300,
        )

        logger.info("Common pools initialized")

    def get_object_pool(self, obj_type: type, max_size: int = 50) -> ObjectPool:
        """オブジェクトプール取得"""
        with self._lock:
            if obj_type not in self._object_pools:
                self._object_pools[obj_type] = ObjectPool(obj_type, max_size)
                logger.info(f"Created object pool for {obj_type.__name__}")

            return self._object_pools[obj_type]

    def acquire_list(self) -> List:
        """リスト取得"""
        return self._list_pool.acquire()

    def release_list(self, lst: List) -> None:
        """リスト返却"""
        self._list_pool.release(lst)

    def acquire_dict(self) -> Dict:
        """辞書取得"""
        return self._dict_pool.acquire()

    def release_dict(self, dct: Dict) -> None:
        """辞書返却"""
        self._dict_pool.release(dct)

    def acquire_string_buffer(self) -> List:
        """文字列バッファ取得"""
        return self._string_pool.acquire()

    def release_string_buffer(self, buffer: List) -> None:
        """文字列バッファ返却"""
        self._string_pool.release(buffer)

    def get_all_stats(self) -> Dict[str, Any]:
        """全プール統計取得"""
        stats = {
            "common_pools": {
                "string_pool": self._string_pool.get_stats(),
                "list_pool": self._list_pool.get_stats(),
                "dict_pool": self._dict_pool.get_stats(),
            },
            "object_pools": {},
        }

        for obj_type, pool in self._object_pools.items():
            pool_stats = {}
            for key, memory_pool in pool._pools.items():
                pool_stats[key] = memory_pool.get_stats()
            stats["object_pools"][obj_type.__name__] = pool_stats

        return stats

    def clear_all(self) -> None:
        """全プールクリア"""
        with self._lock:
            self._string_pool.clear()
            self._list_pool.clear()
            self._dict_pool.clear()

            for pool in self._object_pools.values():
                pool.clear_all()

            logger.info("All pools cleared")

    def force_gc(self) -> Dict[str, int]:
        """強制ガベージコレクション"""
        before_objects = len(gc.get_objects())
        before_collections = gc.get_stats()

        # 全プールクリア
        self.clear_all()

        # ガベージコレクション実行
        collected = gc.collect()

        after_objects = len(gc.get_objects())
        after_collections = gc.get_stats()

        result = {
            "objects_before": before_objects,
            "objects_after": after_objects,
            "objects_collected": collected,
            "objects_freed": before_objects - after_objects,
        }

        logger.info(f"Forced GC completed: {result}")
        return result


# グローバルプールマネージャー
_global_pool_manager = PoolManager()


def get_pool_manager() -> PoolManager:
    """グローバルプールマネージャー取得"""
    return _global_pool_manager


def benchmark_pool_performance(iterations: int = 1000) -> Dict[str, Any]:
    """プールパフォーマンスベンチマーク"""
    manager = get_pool_manager()

    # ベンチマーク: 通常の生成 vs プール使用
    start_time = time.time()

    # 通常の生成
    normal_objects = []
    for _ in range(iterations):
        obj = []
        obj.append("test")
        normal_objects.append(obj)

    normal_time = time.time() - start_time

    # プール使用
    start_time = time.time()
    pool_objects = []

    for _ in range(iterations):
        obj = manager.acquire_list()
        obj.append("test")
        pool_objects.append(obj)

    # 返却
    for obj in pool_objects:
        manager.release_list(obj)

    pool_time = time.time() - start_time

    # 統計
    pool_stats = manager.get_all_stats()

    return {
        "iterations": iterations,
        "normal_creation_time": normal_time,
        "pool_usage_time": pool_time,
        "improvement_ratio": normal_time / pool_time if pool_time > 0 else 0,
        "pool_efficiency": pool_stats["common_pools"]["list_pool"]["efficiency"],
        "objects_reused": pool_stats["common_pools"]["list_pool"]["reused"],
        "objects_created": pool_stats["common_pools"]["list_pool"]["created"],
    }


def main():
    """CLI エントリーポイント"""
    import argparse
    import json

    os.makedirs("tmp", exist_ok=True)

    parser = argparse.ArgumentParser(description="Memory pool manager")
    parser.add_argument(
        "--benchmark", action="store_true", help="Run pool performance benchmark"
    )
    parser.add_argument("--stats", action="store_true", help="Show pool statistics")
    parser.add_argument("--clear", action="store_true", help="Clear all pools")
    parser.add_argument("--gc", action="store_true", help="Force garbage collection")
    parser.add_argument(
        "--iterations", type=int, default=1000, help="Benchmark iterations"
    )

    args = parser.parse_args()

    manager = get_pool_manager()

    if args.benchmark:
        print("Running pool performance benchmark...")
        results = benchmark_pool_performance(args.iterations)

        benchmark_path = "tmp/memory_pool_benchmark.json"
        with open(benchmark_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Benchmark completed:")
        print(f"  Normal creation time: {results['normal_creation_time']:.4f}s")
        print(f"  Pool usage time: {results['pool_usage_time']:.4f}s")
        print(f"  Improvement ratio: {results['improvement_ratio']:.2f}x")
        print(f"  Pool efficiency: {results['pool_efficiency']:.1%}")
        print(f"Results saved: {benchmark_path}")

    elif args.stats:
        print("Pool statistics:")
        stats = manager.get_all_stats()

        stats_path = "tmp/memory_pool_stats.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)

        print(json.dumps(stats, indent=2))
        print(f"Stats saved: {stats_path}")

    elif args.clear:
        print("Clearing all pools...")
        manager.clear_all()
        print("All pools cleared")

    elif args.gc:
        print("Forcing garbage collection...")
        gc_results = manager.force_gc()

        gc_path = "tmp/gc_results.json"
        with open(gc_path, "w") as f:
            json.dump(gc_results, f, indent=2)

        print(f"GC completed:")
        print(f"  Objects freed: {gc_results['objects_freed']}")
        print(f"  Objects collected: {gc_results['objects_collected']}")
        print(f"Results saved: {gc_path}")

    else:
        print("No action specified. Use --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
