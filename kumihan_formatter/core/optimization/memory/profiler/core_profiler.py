"""メモリプロファイラーコアクラス"""

from __future__ import annotations

import gc
import json
import os
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

import psutil

from kumihan_formatter.core.utilities.logger import get_logger

from .config import ProfilerConfig
from .snapshot import MemorySnapshot

logger = get_logger(__name__)


class MemoryProfiler:
    """
    メモリプロファイラーメインクラス

    新しい分割されたコンポーネントを統合して、既存APIの互換性を保持します。
    """

    def __init__(self, config: Optional[ProfilerConfig] = None) -> None:
        """
        メモリプロファイラーを初期化します。

        Args:
            config: プロファイラー設定
        """
        try:
            from .core import MemoryProfilerBase

            # 新しいコンポーネントベースのプロファイラーを使用
            self._profiler_base = MemoryProfilerBase(config)

            # 旧APIとの互換性のため、内部コンポーネントへの参照を保持
            self._config = self._profiler_base.config
            self._monitor = self._profiler_base._monitor
            self._leak_detector = self._profiler_base._leak_detector
            self._report_generator = self._profiler_base._report_generator

            # 旧API互換プロパティ
            self._snapshots = self._monitor.snapshots
            self._lock = self._monitor._lock
            self._is_profiling = False

            logger.info("MemoryProfiler（新版）初期化完了")

        except Exception as e:
            logger.error(f"MemoryProfiler初期化エラー: {str(e)}")
            raise

    def start_profiling(self) -> None:
        """メモリプロファイリングを開始します。"""
        try:
            self._profiler_base.start_profiling()
            self._is_profiling = self._monitor.is_profiling

        except Exception as e:
            logger.error(f"プロファイリング開始エラー: {str(e)}")
            raise

    def stop_profiling(self) -> None:
        """メモリプロファイリングを停止します。"""
        try:
            self._profiler_base.stop_profiling()
            self._is_profiling = self._monitor.is_profiling

        except Exception as e:
            logger.error(f"プロファイリング停止エラー: {str(e)}")

    def _profiling_loop(self) -> None:
        """プロファイリングループ処理（旧API互換）"""
        # 新バージョンでは内部的に処理されるため、ここでは何もしない
        pass

    def _take_memory_snapshot(self) -> Optional[Any]:
        """メモリスナップショットを取得します（旧API互換）。"""
        try:
            return self._monitor.take_memory_snapshot()

        except Exception as e:
            logger.error(f"スナップショット取得エラー: {str(e)}")
            return None

    def _get_object_counts(self) -> Dict[str, int]:
        """オブジェクト数統計を取得します（旧API互換）。"""
        try:
            snapshot = self._monitor.take_memory_snapshot()
            return snapshot.object_counts if snapshot else {}

        except Exception as e:
            logger.error(f"オブジェクト数統計取得エラー: {str(e)}")
            return {}

    def _get_top_objects(self, limit: int = 20) -> List[Any]:
        """メモリ使用量上位オブジェクトを取得します（旧API互換）。"""
        try:
            snapshot = self._monitor.take_memory_snapshot()
            return snapshot.top_objects[:limit] if snapshot else []

        except Exception as e:
            logger.error(f"上位オブジェクト取得エラー: {str(e)}")
            return []

    def _calculate_fragmentation_ratio(self) -> float:
        """メモリ断片化率を計算します（旧API互換）。"""
        try:
            snapshot = self._monitor.take_memory_snapshot()
            return snapshot.fragmentation_ratio if snapshot else 0.0

        except Exception as e:
            logger.error(f"断片化率計算エラー: {str(e)}")
            return 0.0

    def _detect_memory_leaks(self) -> None:
        """メモリリーク検出処理（旧API互換）"""
        try:
            snapshots = list(self._monitor.snapshots)
            if snapshots:
                self._leak_detector.detect_memory_leaks_simple(snapshots)

        except Exception as e:
            logger.error(f"メモリリーク検出エラー: {str(e)}")

    def _is_growing_pattern(self, values: List[int], threshold: float = 0.1) -> bool:
        """継続的な増加パターンかチェックします（旧API互換）。"""
        try:
            return self._leak_detector._is_growing_pattern(values, threshold)

        except Exception as e:
            logger.debug(f"増加パターン判定エラー: {str(e)}")
            return False

    def _calculate_leak_rate(self, obj_type: str) -> float:
        """リーク率を計算します（旧API互換）。"""
        try:
            return self._leak_detector._calculate_leak_rate_simple(obj_type)

        except Exception as e:
            logger.error(f"リーク率計算エラー: {str(e)}")
            return 0.0

    def _generate_profiling_report(self) -> None:
        """プロファイリングレポートを生成します（旧API互換）。"""
        try:
            self._profiler_base.generate_report()

        except Exception as e:
            logger.error(f"プロファイリングレポート生成エラー: {str(e)}")

    def _generate_optimization_recommendations(self) -> List[str]:
        """最適化推奨事項を生成します（旧API互換）。"""
        try:
            snapshots = list(self._monitor.snapshots)

            if not snapshots:
                return []

            from .new_usage_analyzer import MemoryUsageAnalyzerNew

            analyzer = MemoryUsageAnalyzerNew()
            return analyzer._identify_optimization_opportunities(snapshots)

        except Exception as e:
            logger.error(f"最適化推奨事項生成エラー: {str(e)}")
            return []

    def get_current_stats(self) -> Dict[str, Any]:
        """現在のメモリ統計を取得します。"""
        try:
            base_stats = self._profiler_base.get_current_stats()

            # 旧API互換のため、追加フィールドを含める
            base_stats.update(
                {
                    "potential_leaks": len(self._leak_detector.leak_history),
                    "is_profiling": self._monitor.is_profiling,
                }
            )

            return base_stats

        except Exception as e:
            logger.error(f"現在統計取得エラー: {str(e)}")
            return {}

    def force_garbage_collection(self) -> Dict[str, int]:
        """強制ガベージコレクションを実行します。"""
        try:
            return self._profiler_base.force_garbage_collection()

        except Exception as e:
            logger.error(f"強制GC実行エラー: {str(e)}")
            return {}

    # プロパティ（旧API互換）
    @property
    def _snapshots(self) -> Any:
        """スナップショット履歴（互換性プロパティ）"""
        return self._monitor.snapshots

    @_snapshots.setter
    def _snapshots(self, value: Any) -> None:
        """スナップショット設定（互換性のため何もしない）"""
        pass

    @property
    def _leak_history(self) -> Any:
        """リーク履歴（互換性プロパティ）"""
        return self._leak_detector.leak_history
