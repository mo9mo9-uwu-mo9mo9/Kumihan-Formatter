"""
メモリアクセスパターン最適化システム
Issue #813対応 - performance_metrics.pyから分離
"""

import os
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

import psutil

# from ...utilities.logger import get_logger  # Removed: unused import


class MemoryOptimizer:
    """
    メモリアクセスパターン最適化システム

    特徴:
    - メモリ効率的なデータ構造選択
    - ガベージコレクション最適化
    - メモリプールとオブジェクト再利用
    - 大容量ファイル処理のメモリ管理
    """

    def __init__(self, enable_gc_optimization: bool = True):
        from kumihan_formatter.core.utilities.logger import get_logger

        self.logger = get_logger(__name__)
        self.enable_gc_optimization = enable_gc_optimization
        self._object_pools: Dict[str, Dict[str, Any]] = {}  # mypy型修正
        self._memory_stats = {"allocations": 0, "deallocations": 0, "pool_hits": 0}

        if enable_gc_optimization:
            self._configure_gc_optimization()

        self.logger.info("MemoryOptimizer initialized")

    def _configure_gc_optimization(self) -> None:
        """ガベージコレクション最適化設定"""
        import gc

        # GC閾値を調整（大容量処理向け）
        original_thresholds = gc.get_threshold()
        # より高い閾値でGC頻度を下げ、バッチ処理効率を向上
        new_thresholds = (
            original_thresholds[0] * 2,  # 世代0
            original_thresholds[1] * 2,  # 世代1
            original_thresholds[2] * 2,  # 世代2
        )
        gc.set_threshold(*new_thresholds)

        self.logger.info(
            f"GC thresholds adjusted: {original_thresholds} -> {new_thresholds}"
        )

    def create_object_pool(
        self, pool_name: str, factory_func: Callable[[], Any], max_size: int = 100
    ) -> None:
        """
        オブジェクトプール作成

        Args:
            pool_name: プール名
            factory_func: オブジェクト生成関数
            max_size: プール最大サイズ
        """
        self._object_pools[pool_name] = {
            "pool": deque(maxlen=max_size),
            "factory": factory_func,
            "max_size": max_size,
            "created_count": 0,
            "reused_count": 0,
        }

        self.logger.info(f"Object pool '{pool_name}' created with max size: {max_size}")

    def get_pooled_object(self, pool_name: str) -> None:
        """プールからオブジェクトを取得"""
        if pool_name not in self._object_pools:
            raise ValueError(f"Object pool '{pool_name}' not found")

        pool_info = self._object_pools[pool_name]
        pool = pool_info["pool"]

        if pool:
            # プールから再利用
            obj = pool.popleft()
            pool_info["reused_count"] += 1
            self._memory_stats["pool_hits"] += 1
            return obj
        else:
            # 新規作成
            obj = pool_info["factory"]()
            pool_info["created_count"] += 1
            self._memory_stats["allocations"] += 1
            return obj

    def return_pooled_object(self, pool_name: str, obj: Any) -> None:
        """オブジェクトをプールに返却"""
        if pool_name not in self._object_pools:
            return

        pool_info = self._object_pools[pool_name]
        pool = pool_info["pool"]

        # オブジェクトをリセット（可能であれば）
        if hasattr(obj, "reset"):
            obj.reset()
        elif hasattr(obj, "clear"):
            obj.clear()

        # プールに返却
        if len(pool) < pool_info["max_size"]:
            pool.append(obj)
        else:
            # プールが満杯の場合は破棄
            self._memory_stats["deallocations"] += 1

    def memory_efficient_file_reader(
        self,
        file_path: Union[str, Path],
        chunk_size: int = 64 * 1024,
        use_mmap: bool = False,
    ) -> Iterator[str]:
        """
        メモリ効率的なファイル読み込み

        Args:
            file_path: ファイルパス
            chunk_size: チャンクサイズ
            use_mmap: メモリマップドファイル使用フラグ

        Yields:
            str: ファイルチャンク
        """
        if use_mmap:
            try:
                import mmap

                with open(file_path, "r", encoding="utf-8") as f:
                    with mmap.mmap(
                        f.fileno(), 0, access=mmap.ACCESS_READ
                    ) as mmapped_file:
                        for i in range(0, len(mmapped_file), chunk_size):
                            chunk = mmapped_file[i : i + chunk_size].decode(
                                "utf-8", errors="ignore"
                            )
                            yield chunk
                return
            except Exception as e:
                self.logger.warning(f"mmap failed, falling back to regular read: {e}")

        # 通常のファイル読み込み
        with open(file_path, "r", encoding="utf-8") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def optimize_list_operations(self, data: List[Any], operation: str) -> Any:
        """
        リスト操作の最適化

        Args:
            data: 操作対象データ
            operation: 操作種別（'sort', 'unique', 'filter_empty'）

        Returns:
            Any: 最適化された結果
        """
        if operation == "sort":
            # 大容量データの場合はTimsortアルゴリズムを活用
            return sorted(data, key=str if isinstance(data[0], str) else None)

        elif operation == "unique":
            # 高速unique処理
            if len(data) < 1000:
                return list(set(data))
            else:
                # メモリ効率重視の重複削除
                seen = set()
                result = []
                for item in data:
                    if item not in seen:
                        seen.add(item)
                        result.append(item)
                return result

        elif operation == "filter_empty":
            # 空要素フィルタリング
            return [item for item in data if item]

        else:
            # その他の操作はそのまま返す
            return data

    def batch_process_with_memory_limit(
        self,
        data_generator: Iterator[Any],
        processing_func: Callable,
        memory_limit_mb: int = 100,
    ) -> Iterator[Any]:
        """
        メモリ制限付きバッチ処理

        Args:
            data_generator: データジェネレータ
            processing_func: 処理関数
            memory_limit_mb: メモリ制限（MB）

        Yields:
            Any: 処理結果
        """
        import sys

        batch = []
        batch_size_bytes = 0
        memory_limit_bytes = memory_limit_mb * 1024 * 1024

        for item in data_generator:
            batch.append(item)
            # 概算のメモリサイズを計算
            batch_size_bytes += sys.getsizeof(item)

            if batch_size_bytes >= memory_limit_bytes:
                # バッチ処理実行
                for result in processing_func(batch):
                    yield result

                # バッチクリア
                batch.clear()
                batch_size_bytes = 0

        # 残りのバッチを処理
        if batch:
            for result in processing_func(batch):
                yield result

    def force_garbage_collection(self) -> None:
        """強制ガベージコレクション実行"""
        import gc

        collected_objects = gc.collect()
        self.logger.debug(f"Garbage collection: {collected_objects} objects collected")
        return collected_objects

    def get_memory_stats(self) -> Dict[str, Any]:
        """メモリ使用統計を取得"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        pool_stats = {}
        for name, pool_info in self._object_pools.items():
            pool_stats[name] = {
                "current_size": len(pool_info["pool"]),
                "max_size": pool_info["max_size"],
                "created_count": pool_info["created_count"],
                "reused_count": pool_info["reused_count"],
                "efficiency_percent": (
                    pool_info["reused_count"]
                    / (pool_info["created_count"] + pool_info["reused_count"])
                    * 100
                    if (pool_info["created_count"] + pool_info["reused_count"]) > 0
                    else 0
                ),
            }

        return {
            "process_memory_mb": memory_info.rss / 1024 / 1024,
            "virtual_memory_mb": memory_info.vms / 1024 / 1024,
            "object_pools": pool_stats,
            "memory_operations": self._memory_stats,
        }

    def detect_memory_leaks(
        self, threshold_mb: float = 10.0, sample_interval: int = 5
    ) -> Dict[str, Any]:
        """
        高度なメモリリーク検出機構

        Args:
            threshold_mb: メモリ増加の検出閾値（MB）
            sample_interval: サンプル間隔（秒）

        Returns:
            Dict[str, Any]: リーク検出結果
        """
        import gc

        process = psutil.Process(os.getpid())
        samples: List[Tuple[float, float]] = []  # (timestamp, memory_mb)

        # 初期メモリ使用量記録
        initial_memory = process.memory_info().rss / 1024 / 1024
        samples.append((time.time(), initial_memory))

        self.logger.info(
            f"Memory leak detection started. Initial memory: {initial_memory:.2f} MB"
        )

        # 複数回サンプリング
        for i in range(sample_interval):
            time.sleep(1)
            current_memory = process.memory_info().rss / 1024 / 1024
            samples.append((time.time(), current_memory))

        # リーク分析
        memory_growth = samples[-1][1] - samples[0][1]
        growth_rate = memory_growth / (samples[-1][0] - samples[0][0])  # MB/秒

        # ガベージコレクション実行後のメモリ確認
        gc.collect()
        time.sleep(0.5)
        post_gc_memory = process.memory_info().rss / 1024 / 1024
        gc_effect = samples[-1][1] - post_gc_memory

        # リーク判定
        is_leak_detected = (
            memory_growth > threshold_mb
            and gc_effect < memory_growth * 0.5  # GCで半分以上回収されない場合
        )

        leak_info = {
            "leak_detected": is_leak_detected,
            "memory_growth_mb": memory_growth,
            "growth_rate_mb_per_sec": growth_rate,
            "gc_effect_mb": gc_effect,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": samples[-1][1],
            "post_gc_memory_mb": post_gc_memory,
            "samples": samples,
            "recommendation": self._generate_leak_recommendation(
                is_leak_detected, memory_growth, gc_effect
            ),
        }

        if is_leak_detected:
            self.logger.warning(
                f"Memory leak detected! Growth: {memory_growth:.2f} MB, "
                f"Rate: {growth_rate:.4f} MB/s"
            )
        else:
            self.logger.info(
                f"No significant memory leak detected. Growth: {memory_growth:.2f} MB"
            )

        return leak_info

    def proactive_gc_strategy(
        self, memory_threshold_mb: float = 100.0, enable_generational: bool = True
    ) -> Dict[str, Any]:
        """
        プロアクティブなガベージコレクション戦略

        Args:
            memory_threshold_mb: GC実行メモリ閾値（MB）
            enable_generational: 世代別GC最適化有効フラグ

        Returns:
            Dict[str, Any]: GC実行結果
        """
        import gc

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        self.logger.info(
            f"Proactive GC strategy triggered. Current memory: {initial_memory:.2f} MB"
        )

        results = {
            "initial_memory_mb": initial_memory,
            "gc_executed": False,
            "collections_performed": [],
            "memory_freed_mb": 0.0,
            "execution_time_ms": 0.0,
        }

        start_time = time.time()

        # メモリ閾値チェック
        if initial_memory >= memory_threshold_mb:
            self.logger.info(
                f"Memory threshold ({memory_threshold_mb} MB) exceeded. Executing proactive GC..."
            )

            if enable_generational:
                # 世代別最適化GC実行
                for generation in range(3):  # Python GCの3世代
                    collected = gc.collect(generation)
                    results["collections_performed"].append(
                        {"generation": generation, "objects_collected": collected}
                    )
                    self.logger.debug(
                        f"Generation {generation} GC: {collected} objects collected"
                    )
            else:
                # 標準GC実行
                collected = gc.collect()
                results["collections_performed"].append(
                    {"generation": "all", "objects_collected": collected}
                )

            # GC後メモリ確認
            time.sleep(0.1)  # GC完了を待機
            post_gc_memory = process.memory_info().rss / 1024 / 1024
            results["memory_freed_mb"] = initial_memory - post_gc_memory
            results["final_memory_mb"] = post_gc_memory
            results["gc_executed"] = True

            self.logger.info(
                f"Proactive GC completed. Memory freed: {results['memory_freed_mb']:.2f} MB"
            )
        else:
            self.logger.debug(
                f"Memory usage ({initial_memory:.2f} MB) below threshold. GC not needed."
            )

        results["execution_time_ms"] = (time.time() - start_time) * 1000
        return results

    def create_advanced_resource_pool(
        self,
        pool_name: str,
        factory_func: Callable,
        max_size: int = 100,
        cleanup_func: Optional[Callable] = None,
        auto_cleanup_interval: int = 300,
    ) -> None:
        """
        高度なリソースプール管理システム

        Args:
            pool_name: プール名
            factory_func: オブジェクト生成関数
            max_size: プール最大サイズ
            cleanup_func: クリーンアップ関数
            auto_cleanup_interval: 自動クリーンアップ間隔（秒）
        """
        pool_info = {
            "pool": deque(maxlen=max_size),
            "factory": factory_func,
            "cleanup": cleanup_func,
            "max_size": max_size,
            "created_count": 0,
            "reused_count": 0,
            "cleanup_count": 0,
            "last_cleanup": time.time(),
            "auto_cleanup_interval": auto_cleanup_interval,
            "lock": threading.RLock(),  # リエントラントロック
        }

        self._object_pools[pool_name] = pool_info

        # 自動クリーンアップタイマー設定
        def auto_cleanup() -> None:
            while pool_name in self._object_pools:
                time.sleep(auto_cleanup_interval)
                self._cleanup_resource_pool(pool_name)

        cleanup_thread = threading.Thread(target=auto_cleanup, daemon=True)
        cleanup_thread.start()

        self.logger.info(
            f"Advanced resource pool '{pool_name}' created with auto-cleanup "
            f"every {auto_cleanup_interval}s"
        )

    def _cleanup_resource_pool(self, pool_name: str) -> int:
        """リソースプールのクリーンアップ実行"""
        if pool_name not in self._object_pools:
            return 0

        pool_info = self._object_pools[pool_name]
        cleanup_count = 0

        with pool_info["lock"]:
            cleanup_func = pool_info.get("cleanup")
            if cleanup_func:
                # プール内の全オブジェクトをクリーンアップ
                temp_objects = []
                while pool_info["pool"]:
                    obj = pool_info["pool"].popleft()
                    try:
                        cleanup_func(obj)
                        temp_objects.append(obj)
                        cleanup_count += 1
                    except Exception as e:
                        self.logger.warning(
                            f"Cleanup failed for object in pool '{pool_name}': {e}"
                        )

                # クリーンアップされたオブジェクトを戻す
                for obj in temp_objects:
                    pool_info["pool"].append(obj)

            pool_info["cleanup_count"] += cleanup_count
            pool_info["last_cleanup"] = time.time()

            if cleanup_count > 0:
                self.logger.info(
                    f"Resource pool '{pool_name}' cleanup: {cleanup_count} objects processed"
                )

        return cleanup_count

    def generate_memory_report(self, include_detailed_stats: bool = True) -> str:
        """
        メモリ使用量の詳細レポート生成（可視化機能）

        Args:
            include_detailed_stats: 詳細統計情報を含むか

        Returns:
            str: HTMLフォーマットのメモリレポート
        """
        # tmp/配下にレポート保存
        from pathlib import Path

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        # 基本情報収集
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memory_mb = memory_info.rss / 1024 / 1024
        _ = memory_info.vms / 1024 / 1024  # Virtual memory (unused)

        # システム情報
        system_memory = psutil.virtual_memory()
        _ = system_memory.total / 1024 / 1024 / 1024  # System total (unused)
        _ = system_memory.available / 1024 / 1024 / 1024  # System available (unused)
        system_usage_percent = system_memory.percent

        # HTML レポート生成
        html_report = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Kumihan-Formatter メモリレポート</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; margin: 10px; border-radius: 6px; }}
        .memory-bar {{ width: 100%; height: 20px; background-color: #ecf0f1; border-radius: 10px; }}
        .memory-fill {{
            height: 100%;
            background: linear-gradient(90deg, #27ae60, #f39c12, #e74c3c);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Kumihan-Formatter メモリレポート</h1>
        <div class="stat-card">
            <h3>プロセスメモリ使用量: {memory_mb:.2f} MB</h3>
            <div class="memory-bar">
                <div class="memory-fill" style="width: {min(memory_mb/100*10, 100)}%;"></div>
            </div>
        </div>
        <div class="stat-card">
            <h3>システムメモリ使用率: {system_usage_percent:.1f}%</h3>
            <div class="memory-bar">
                <div class="memory-fill" style="width: {system_usage_percent}%;"></div>
            </div>
        </div>
        <p>レポート生成時刻: {current_time}</p>
    </div>
</body>
</html>"""

        # tmp/配下に保存
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)
        report_path = (
            tmp_dir / f"memory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_report)

        self.logger.info(f"Memory report generated and saved to {report_path}")
        return str(report_path)

    def _generate_leak_recommendation(
        self, is_leak: bool, growth_mb: float, gc_effect_mb: float
    ) -> str:
        """メモリリーク検出結果に基づく推奨アクション生成"""
        if not is_leak:
            return "正常なメモリ使用パターンです。定期的な監視を継続してください。"

        recommendations = []

        if gc_effect_mb < growth_mb * 0.3:
            recommendations.append(
                "ガベージコレクションの効果が低いため、強い参照の解除を確認してください。"
            )

        if growth_mb > 50:
            recommendations.append(
                "大幅なメモリ増加が検出されました。大容量データの処理方法を見直してください。"
            )

        if not recommendations:
            recommendations.append(
                "メモリリークが検出されました。オブジェクトのライフサイクルを確認してください。"
            )

        return " ".join(recommendations)
