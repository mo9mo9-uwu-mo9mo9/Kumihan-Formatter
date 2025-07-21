"""メモリガGC最適化機能。

ガベージコレクションの強制実行と設定最適化を行う専用モジュール。
"""

import gc
import time
from typing import Any

from ..utilities.logger import get_logger
from .memory_types import GC_OPTIMIZATION_THRESHOLDS


class MemoryGCOptimizer:
    """メモリガベージコレクション最適化機能"""

    def __init__(self) -> None:
        """最適化器を初期化"""
        self.logger = get_logger(__name__)
        self.stats = {
            "total_gc_forced": 0,
            "memory_optimizations": 0,
        }

    def force_garbage_collection(self) -> dict[str, Any]:
        """ガベージコレクションを強制実行

        Returns:
            dict: GC実行結果
        """
        start_time = time.time()
        start_objects = len(gc.get_objects())

        # 全世代のGCを実行
        collected_counts = []
        for generation in range(3):
            collected = gc.collect(generation)
            collected_counts.append(collected)
            self.logger.debug(f"Generation {generation}: {collected} objects collected")

        end_time = time.time()
        end_objects = len(gc.get_objects())
        execution_time = end_time - start_time

        total_collected = sum(collected_counts)
        objects_freed = start_objects - end_objects

        result = {
            "execution_time_ms": execution_time * 1000,
            "objects_before": start_objects,
            "objects_after": end_objects,
            "objects_freed": objects_freed,
            "total_collected": total_collected,
            "collected_by_generation": {
                f"generation_{i}": count for i, count in enumerate(collected_counts)
            },
            "gc_stats": gc.get_stats(),
            "timestamp": start_time,
        }

        self.stats["total_gc_forced"] += 1

        if total_collected > 0:
            self.logger.info(
                f"GC強制実行完了: {total_collected}オブジェクト解放, "
                f"{execution_time * 1000:.1f}ms"
            )
        else:
            self.logger.debug("GC強制実行: 解放対象なし")

        # メモリ効率性の評価
        efficiency = (objects_freed / start_objects * 100) if start_objects > 0 else 0
        result["efficiency_percent"] = efficiency

        if efficiency < 5:  # 5%未満の効率
            result["warning"] = "GC効率が低いです。メモリリークの可能性あり"

        return result

    def optimize_memory_settings(self) -> dict[str, Any]:
        """メモリ設定を最適化

        Returns:
            dict: 最適化結果
        """
        current_thresholds = gc.get_threshold()
        current_objects = len(gc.get_objects())

        # オブジェクト数に基づいて闾値を調整
        if current_objects > GC_OPTIMIZATION_THRESHOLDS["high_object_count"]:
            # オブジェクト数が多い場合は、より頻繁にGCを実行
            new_thresholds = (500, 10, 10)
            optimization_type = "frequent_gc"
        elif current_objects < GC_OPTIMIZATION_THRESHOLDS["low_object_count"]:
            # オブジェクト数が少ない場合は、GC頻度を下げる
            new_thresholds = (1500, 20, 20)
            optimization_type = "infrequent_gc"
        else:
            # 標準的な設定
            new_thresholds = (700, 10, 10)
            optimization_type = "standard"

        # 闾値を適用
        gc.set_threshold(*new_thresholds)
        self.stats["memory_optimizations"] += 1

        result = {
            "previous_thresholds": current_thresholds,
            "new_thresholds": new_thresholds,
            "current_objects": current_objects,
            "optimization_type": optimization_type,
            "timestamp": time.time(),
        }

        self.logger.info(
            f"メモリ設定最適化: {optimization_type}, "
            f"闾値 {current_thresholds} -> {new_thresholds}"
        )

        # 最適化の有効性をチェック
        recommendations = []
        if current_objects > GC_OPTIMIZATION_THRESHOLDS["memory_leak_threshold"]:
            recommendations.append(
                "オブジェクト数が異常に多いです。メモリリークの調査を推奨します"
            )

        if optimization_type == "frequent_gc":
            recommendations.append("頻繁なGCでパフォーマンスに影響する可能性があります")

        if recommendations:
            result["recommendations"] = recommendations

        return result

    def get_gc_statistics(self) -> dict[str, Any]:
        """ガGC統計情報を取得

        Returns:
            dict: GC統計情報
        """
        return {
            "current_thresholds": gc.get_threshold(),
            "current_objects": len(gc.get_objects()),
            "gc_stats": gc.get_stats(),
            "gc_enabled": gc.isenabled(),
            "unreachable_objects": gc.collect(),  # 同時にクリーンアップ
            "optimizer_stats": self.stats.copy(),
        }

    def reset_stats(self) -> None:
        """統計情報をリセット"""
        self.stats = {
            "total_gc_forced": 0,
            "memory_optimizations": 0,
        }
        self.logger.debug("メモリ最適化器の統計情報をリセット")
