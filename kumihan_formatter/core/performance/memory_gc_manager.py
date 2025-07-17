"""
ガベージコレクション管理器 - GC機能の独立クラス

MemoryAnalyzerから抽出されたGC管理機能を専門的に扱う
Issue #476対応 - 300行制限による技術的負債削減
"""

import gc
import time
from typing import Any

from ..utilities.logger import get_logger
from .memory_types import GC_OPTIMIZATION_THRESHOLDS


class MemoryGCManager:
    """ガベージコレクション管理専用クラス

    機能:
    - 強制ガベージコレクション実行
    - メモリ設定最適化
    - GC統計情報管理
    """

    def __init__(self) -> None:
        """ガベージコレクション管理器を初期化"""
        self.logger = get_logger(__name__)

        # 統計
        self.stats = {
            "total_gc_forced": 0,
            "memory_optimizations": 0,
        }

        self.logger.info("ガベージコレクション管理器初期化完了")

    def force_garbage_collection(self) -> dict[str, Any]:
        """ガベージコレクションを強制実行

        Returns:
            dict: GC実行結果
        """
        start_time = time.time()

        # 実行前の状態
        before_objects = len(gc.get_objects())
        before_collections = gc.get_count()

        # GC実行
        collected_counts = []
        for generation in range(3):
            collected = gc.collect(generation)
            collected_counts.append(collected)

        # 実行後の状態
        after_objects = len(gc.get_objects())
        after_collections = gc.get_count()

        duration = time.time() - start_time

        result = {
            "duration_ms": duration * 1000,
            "before": {
                "objects": before_objects,
                "collections": before_collections,
            },
            "after": {
                "objects": after_objects,
                "collections": after_collections,
            },
            "collected_by_generation": collected_counts,
            "objects_freed": before_objects - after_objects,
            "total_collected": sum(collected_counts),
        }

        self.stats["total_gc_forced"] += 1

        self.logger.info(
            f"強制GC実行完了 duration_ms={result['duration_ms']:.2f}, "
            f"objects_freed={result['objects_freed']}, "
            f"total_collected={result['total_collected']}"
        )

        return result

    def optimize_memory_settings(self) -> dict[str, Any]:
        """メモリ設定を最適化

        Returns:
            dict: 最適化結果
        """
        old_thresholds = gc.get_threshold()

        # 最適化された閾値を設定
        new_thresholds = (
            GC_OPTIMIZATION_THRESHOLDS["generation_0"],
            GC_OPTIMIZATION_THRESHOLDS["generation_1"],
            GC_OPTIMIZATION_THRESHOLDS["generation_2"],
        )

        gc.set_threshold(*new_thresholds)

        # 設定確認
        current_thresholds = gc.get_threshold()

        result = {
            "old_thresholds": old_thresholds,
            "new_thresholds": current_thresholds,
            "optimization_applied": current_thresholds == new_thresholds,
        }

        self.stats["memory_optimizations"] += 1

        self.logger.info(
            f"メモリ設定最適化完了 old_thresholds={old_thresholds}, "
            f"new_thresholds={current_thresholds}"
        )

        return result

    def get_stats(self) -> dict[str, Any]:
        """統計情報を取得

        Returns:
            dict: 統計情報
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """統計情報をリセット"""
        old_stats = self.stats.copy()
        self.stats = {
            "total_gc_forced": 0,
            "memory_optimizations": 0,
        }

        self.logger.info(f"GC管理器統計情報をリセット old_stats={old_stats}")
