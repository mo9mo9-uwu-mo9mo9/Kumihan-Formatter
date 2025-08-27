"""メモリプロファイラー基底クラス"""

from __future__ import annotations

import gc
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger
from ..config import ProfilerConfig
from .memory_monitor import MemoryMonitor
from .report_generator import MemoryReportGenerator
from ..leak_detector import MemoryLeakDetector

logger = get_logger(__name__)


class MemoryProfilerBase:
    """
    メモリプロファイラー基底クラス

    各コンポーネントを統合し、基本的なプロファイリング機能を提供します。
    """

    def __init__(self, config: Optional[ProfilerConfig] = None) -> None:
        """
        メモリプロファイラーを初期化します。

        Args:
            config: プロファイラー設定
        """
        try:
            self._config = config or ProfilerConfig()

            # コンポーネント初期化
            self._monitor = MemoryMonitor(self._config)
            self._leak_detector = MemoryLeakDetector(self._monitor)
            self._report_generator = MemoryReportGenerator(self._config)

            logger.info("MemoryProfilerBase初期化完了")

        except Exception as e:
            logger.error(f"MemoryProfilerBase初期化エラー: {str(e)}")
            raise

    def start_profiling(self) -> None:
        """メモリプロファイリングを開始します。"""
        try:
            self._monitor.start_profiling()

        except Exception as e:
            logger.error(f"プロファイリング開始エラー: {str(e)}")
            raise

    def stop_profiling(self) -> None:
        """メモリプロファイリングを停止します。"""
        try:
            self._monitor.stop_profiling()

        except Exception as e:
            logger.error(f"プロファイリング停止エラー: {str(e)}")

    def get_current_stats(self) -> Dict[str, Any]:
        """現在のメモリ統計を取得します。"""
        try:
            snapshots = list(self._monitor.snapshots)

            if not snapshots:
                return {
                    "current_memory_mb": 0.0,
                    "is_profiling": self._monitor.is_profiling,
                    "snapshots_taken": 0,
                }

            return self._report_generator.generate_summary_report(snapshots)

        except Exception as e:
            logger.error(f"現在統計取得エラー: {str(e)}")
            return {}

    def generate_report(self, output_path: Optional[str] = None) -> Optional[str]:
        """プロファイリングレポートを生成します。"""
        try:
            snapshots = list(self._monitor.snapshots)
            leak_history = self._leak_detector.leak_history

            return self._report_generator.generate_profiling_report(
                snapshots, leak_history, output_path
            )

        except Exception as e:
            logger.error(f"レポート生成エラー: {str(e)}")
            return None

    def detect_leaks(self, confidence_threshold: float = 0.7) -> List[Any]:
        """メモリリーク検出を実行します。"""
        try:
            return self._leak_detector.detect_leaks(confidence_threshold)

        except Exception as e:
            logger.error(f"リーク検出エラー: {str(e)}")
            return []

    def force_garbage_collection(self) -> Dict[str, int]:
        """強制ガベージコレクションを実行します。"""
        try:
            before_counts = gc.get_count()
            collected = gc.collect()
            after_counts = gc.get_count()

            result = {
                "objects_collected": collected,
                "before_gen0": before_counts[0] if before_counts else 0,
                "before_gen1": before_counts[1] if len(before_counts) > 1 else 0,
                "before_gen2": before_counts[2] if len(before_counts) > 2 else 0,
                "after_gen0": after_counts[0] if after_counts else 0,
                "after_gen1": after_counts[1] if len(after_counts) > 1 else 0,
                "after_gen2": after_counts[2] if len(after_counts) > 2 else 0,
            }

            logger.info(f"強制GC実行: {collected}オブジェクト回収")
            return result

        except Exception as e:
            logger.error(f"強制GC実行エラー: {str(e)}")
            return {}

    def take_snapshot(self) -> Optional[Any]:
        """手動でスナップショットを取得します。"""
        try:
            return self._monitor.take_memory_snapshot()

        except Exception as e:
            logger.error(f"スナップショット取得エラー: {str(e)}")
            return None

    @property
    def is_profiling(self) -> bool:
        """プロファイリング状態"""
        return self._monitor.is_profiling

    @property
    def snapshot_count(self) -> int:
        """取得済みスナップショット数"""
        return len(self._monitor.snapshots)

    @property
    def config(self) -> ProfilerConfig:
        """プロファイラー設定"""
        return self._config
