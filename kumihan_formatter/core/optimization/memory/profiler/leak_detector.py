"""メモリリーク検出器"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from kumihan_formatter.core.utilities.logger import get_logger

from .snapshot import MemoryLeakInfo, MemorySnapshot

if TYPE_CHECKING:
    from .core_profiler import MemoryProfiler

logger = get_logger(__name__)


class MemoryLeakDetector:
    """
    メモリリーク検出器クラス

    より高度なメモリリーク検出とパターン分析を提供します。
    """

    def __init__(self, memory_monitor: Optional[Any] = None) -> None:
        """
        メモリリーク検出器を初期化します。

        Args:
            memory_monitor: メモリ監視インスタンス（オプション）
        """
        try:
            self._memory_monitor = memory_monitor
            self._detected_leaks: Dict[str, MemoryLeakInfo] = {}
            self._leak_history: Dict[str, List[float]] = defaultdict(list)
            self._lock = Lock()

            logger.info("MemoryLeakDetector初期化完了")

        except Exception as e:
            logger.error(f"MemoryLeakDetector初期化エラー: {str(e)}")
            raise

    def detect_leaks_from_snapshots(
        self, snapshots: List[MemorySnapshot], confidence_threshold: float = 0.7
    ) -> List[MemoryLeakInfo]:
        """
        スナップショットリストからリーク検出を実行します。

        Args:
            snapshots: メモリスナップショットのリスト
            confidence_threshold: 信頼度閾値

        Returns:
            検出されたメモリリーク情報
        """
        try:
            with self._lock:
                if len(snapshots) < 5:
                    return []

                detected_leaks = []

                # オブジェクトタイプ別分析
                for obj_type in set().union(
                    *[s.object_counts.keys() for s in snapshots]
                ):
                    leak_info = self._analyze_object_type(obj_type, snapshots)

                    if leak_info and leak_info.confidence_score >= confidence_threshold:
                        detected_leaks.append(leak_info)
                        self._detected_leaks[obj_type] = leak_info

                return detected_leaks

        except Exception as e:
            logger.error(f"メモリリーク検出エラー: {str(e)}")
            return []

    def detect_leaks(self, confidence_threshold: float = 0.7) -> List[MemoryLeakInfo]:
        """
        高度なメモリリーク検出を実行します。

        Args:
            confidence_threshold: 信頼度閾値

        Returns:
            検出されたメモリリーク情報
        """
        try:
            if self._memory_monitor:
                snapshots = list(self._memory_monitor.snapshots)
                return self.detect_leaks_from_snapshots(snapshots, confidence_threshold)
            else:
                logger.warning("メモリ監視インスタンスが設定されていません")
                return []

        except Exception as e:
            logger.error(f"メモリリーク検出エラー: {str(e)}")
            return []

    def detect_memory_leaks_simple(self, snapshots: List[MemorySnapshot]) -> None:
        """
        シンプルなメモリリーク検出処理（旧コアプロファイラーから移植）
        """
        try:
            if len(snapshots) < 3:
                return

            # 最近のスナップショットから成長パターンを分析
            recent_snapshots = snapshots[-10:]

            for obj_type in set().union(
                *[s.object_counts.keys() for s in recent_snapshots]
            ):
                counts = [s.object_counts.get(obj_type, 0) for s in recent_snapshots]

                # 継続的な増加パターンをチェック
                if self._is_growing_pattern(counts):
                    self._leak_history[obj_type].extend(counts)

                    # リーク率計算
                    leak_rate = self._calculate_leak_rate_simple(obj_type)
                    if leak_rate > 0.1:  # 0.1MB/秒以上の増加
                        logger.warning(
                            f"メモリリーク検出: {obj_type} - {leak_rate:.3f}MB/秒"
                        )

        except Exception as e:
            logger.error(f"メモリリーク検出エラー: {str(e)}")

    def _is_growing_pattern(self, values: List[int], threshold: float = 0.1) -> bool:
        """継続的な増加パターンかチェックします。"""
        try:
            if len(values) < 3:
                return False

            # 線形回帰による傾き計算
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n

            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return False

            slope = numerator / denominator
            return slope > threshold

        except Exception as e:
            logger.debug(f"増加パターン判定エラー: {str(e)}")
            return False

    def _calculate_leak_rate_simple(
        self, obj_type: str, snapshot_interval: float = 1.0
    ) -> float:
        """シンプルなリーク率を計算します（MB/秒）。"""
        try:
            history = self._leak_history[obj_type]
            if len(history) < 2:
                return 0.0

            # 簡易計算：オブジェクト数増加 × 推定サイズ
            count_increase = history[-1] - history[0]
            time_span = len(history) * snapshot_interval

            # 推定オブジェクトサイズ（1KB仮定）
            estimated_size_mb = count_increase * 0.001

            return estimated_size_mb / time_span

        except Exception as e:
            logger.error(f"リーク率計算エラー: {str(e)}")
            return 0.0

    def _analyze_object_type(
        self, obj_type: str, snapshots: List[MemorySnapshot]
    ) -> Optional[MemoryLeakInfo]:
        """オブジェクトタイプ別リーク分析"""
        try:
            counts = [s.object_counts.get(obj_type, 0) for s in snapshots]
            timestamps = [s.timestamp for s in snapshots]

            if len(counts) < 3:
                return None

            # 成長パターン分析
            growth_pattern = self._calculate_growth_pattern(counts)
            confidence = self._calculate_confidence(growth_pattern)

            if confidence < 0.5:  # 最低信頼度
                return None

            # リーク率計算
            time_span = timestamps[-1] - timestamps[0]
            count_increase = counts[-1] - counts[0]

            if time_span <= 0 or count_increase <= 0:
                return None

            # 推定メモリサイズ（オブジェクトタイプ別）
            estimated_size_kb = self._estimate_object_size(obj_type)
            leak_rate_mb_per_sec = (
                count_increase * estimated_size_kb / 1024
            ) / time_span
            total_leaked_mb = count_increase * estimated_size_kb / 1024

            return MemoryLeakInfo(
                object_type=obj_type,
                leak_rate_mb_per_sec=leak_rate_mb_per_sec,
                total_leaked_mb=total_leaked_mb,
                detection_time=time.time(),
                confidence_score=confidence,
                growth_pattern=growth_pattern,
            )

        except Exception as e:
            logger.error(f"オブジェクト分析エラー: {str(e)}")
            return None

    def _calculate_growth_pattern(self, values: List[int]) -> List[float]:
        """成長パターンを計算します。"""
        try:
            if len(values) < 2:
                return []

            growth_rates = []
            for i in range(1, len(values)):
                if values[i - 1] > 0:
                    rate = (values[i] - values[i - 1]) / values[i - 1]
                    growth_rates.append(rate)
                else:
                    growth_rates.append(0.0)

            return growth_rates

        except Exception as e:
            logger.error(f"成長パターン計算エラー: {str(e)}")
            return []

    def _calculate_confidence(self, growth_pattern: List[float]) -> float:
        """リーク検出の信頼度を計算します。"""
        try:
            if not growth_pattern:
                return 0.0

            # 正の成長率の割合
            positive_growth_ratio = sum(1 for rate in growth_pattern if rate > 0) / len(
                growth_pattern
            )

            # 成長の一貫性
            avg_growth = sum(growth_pattern) / len(growth_pattern)
            consistency = 1.0 - (
                sum(abs(rate - avg_growth) for rate in growth_pattern)
                / len(growth_pattern)
            )

            # 総合信頼度
            confidence = positive_growth_ratio * 0.6 + max(0, consistency) * 0.4

            return min(confidence, 1.0)

        except Exception as e:
            logger.error(f"信頼度計算エラー: {str(e)}")
            return 0.0

    def _estimate_object_size(self, obj_type: str) -> float:
        """オブジェクトタイプ別推定サイズ（KB）"""
        try:
            # オブジェクトタイプ別の推定サイズ
            size_estimates = {
                "str": 0.1,
                "list": 0.5,
                "dict": 1.0,
                "tuple": 0.3,
                "set": 0.8,
                "bytes": 0.1,
                "function": 2.0,
                "type": 5.0,
                "module": 50.0,
            }

            return size_estimates.get(obj_type, 1.0)  # デフォルト1KB

        except Exception as e:
            logger.error(f"オブジェクトサイズ推定エラー: {str(e)}")
            return 1.0

    def get_leak_summary(self) -> Dict[str, Any]:
        """リーク検出サマリーを取得します。"""
        try:
            with self._lock:
                return {
                    "total_leaks_detected": len(self._detected_leaks),
                    "high_confidence_leaks": len(
                        [
                            leak
                            for leak in self._detected_leaks.values()
                            if leak.confidence_score > 0.8
                        ]
                    ),
                    "total_leaked_mb": sum(
                        leak.total_leaked_mb for leak in self._detected_leaks.values()
                    ),
                    "avg_leak_rate_mb_per_sec": (
                        sum(
                            leak.leak_rate_mb_per_sec
                            for leak in self._detected_leaks.values()
                        )
                        / len(self._detected_leaks)
                        if self._detected_leaks
                        else 0.0
                    ),
                    "leak_details": {
                        obj_type: {
                            "leak_rate_mb_per_sec": leak.leak_rate_mb_per_sec,
                            "total_leaked_mb": leak.total_leaked_mb,
                            "confidence_score": leak.confidence_score,
                        }
                        for obj_type, leak in self._detected_leaks.items()
                    },
                }

        except Exception as e:
            logger.error(f"リークサマリー取得エラー: {str(e)}")
            return {}

    @property
    def leak_history(self) -> Dict[str, List[float]]:
        """リーク履歴データ"""
        with self._lock:
            return self._leak_history.copy()
