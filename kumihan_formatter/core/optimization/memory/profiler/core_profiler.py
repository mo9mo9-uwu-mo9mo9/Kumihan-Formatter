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

    システム全体のメモリ使用量を詳細に計測し、パフォーマンス問題を特定します。
    """

    def __init__(self, config: Optional[ProfilerConfig] = None) -> None:
        """
        メモリプロファイラーを初期化します。

        Args:
            config: プロファイラー設定
        """
        try:
            self._config = config or ProfilerConfig()
            self._process = psutil.Process()

            # プロファイリングデータ
            self._snapshots: deque[MemorySnapshot] = deque(maxlen=1000)
            self._leak_history: Dict[str, List[float]] = defaultdict(list)
            self._lock = RLock()

            # 監視スレッド
            self._monitoring_thread: Optional[threading.Thread] = None
            self._stop_monitoring = threading.Event()
            self._is_profiling = False

            # tracemalloc初期化
            if self._config.enable_tracemalloc and not tracemalloc.is_tracing():
                tracemalloc.start(self._config.tracemalloc_limit)

            logger.info("MemoryProfiler初期化完了")

        except Exception as e:
            logger.error(f"MemoryProfiler初期化エラー: {str(e)}")
            raise

    def start_profiling(self) -> None:
        """メモリプロファイリングを開始します。"""
        try:
            if self._is_profiling:
                logger.warning("プロファイリングは既に開始されています")
                return

            self._is_profiling = True
            self._stop_monitoring.clear()

            self._monitoring_thread = threading.Thread(
                target=self._profiling_loop, daemon=True
            )
            self._monitoring_thread.start()

            logger.info("メモリプロファイリング開始")

        except Exception as e:
            logger.error(f"プロファイリング開始エラー: {str(e)}")
            raise

    def stop_profiling(self) -> None:
        """メモリプロファイリングを停止します。"""
        try:
            if not self._is_profiling:
                return

            self._is_profiling = False
            self._stop_monitoring.set()

            if self._monitoring_thread:
                self._monitoring_thread.join(timeout=10.0)

            logger.info("メモリプロファイリング停止")

        except Exception as e:
            logger.error(f"プロファイリング停止エラー: {str(e)}")

    def _profiling_loop(self) -> None:
        """プロファイリングループ処理"""
        try:
            while not self._stop_monitoring.wait(self._config.snapshot_interval):
                snapshot = self._take_memory_snapshot()

                with self._lock:
                    self._snapshots.append(snapshot)

                # リーク検出
                self._detect_memory_leaks()

                # レポート生成（定期的）
                if len(self._snapshots) % 10 == 0:  # 10回に1回
                    self._generate_profiling_report()

        except Exception as e:
            logger.error(f"プロファイリングループエラー: {str(e)}")

    def _take_memory_snapshot(self) -> MemorySnapshot:
        """メモリスナップショットを取得します。"""
        try:
            # プロセス情報取得
            memory_info = self._process.memory_info()
            virtual_memory = psutil.virtual_memory()

            # GC統計
            gc_stats = gc.get_stats()

            # オブジェクト統計
            object_counts = self._get_object_counts()
            top_objects = self._get_top_objects()

            # メモリ断片化率計算
            fragmentation_ratio = self._calculate_fragmentation_ratio()

            snapshot = MemorySnapshot(
                timestamp=time.time(),
                process_memory_mb=memory_info.rss / (1024 * 1024),
                virtual_memory_mb=virtual_memory.total / (1024 * 1024),
                memory_percent=virtual_memory.percent,
                gc_stats=gc_stats,
                object_counts=object_counts,
                top_objects=top_objects,
                fragmentation_ratio=fragmentation_ratio,
            )

            logger.debug(
                f"メモリスナップショット取得: {snapshot.process_memory_mb:.1f}MB"
            )
            return snapshot

        except Exception as e:
            logger.error(f"スナップショット取得エラー: {str(e)}")
            # エラー時はダミーデータ
            return MemorySnapshot(
                timestamp=time.time(),
                process_memory_mb=0.0,
                virtual_memory_mb=0.0,
                memory_percent=0.0,
                gc_stats=[],
                object_counts={},
                top_objects=[],
                fragmentation_ratio=0.0,
            )

    def _get_object_counts(self) -> Dict[str, int]:
        """オブジェクト数統計を取得します。"""
        try:
            object_counts: Dict[str, int] = defaultdict(int)

            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                object_counts[obj_type] += 1

            return dict(object_counts)

        except Exception as e:
            logger.error(f"オブジェクト数統計取得エラー: {str(e)}")
            return {}

    def _get_top_objects(self, limit: int = 20) -> List[Tuple[str, int, int]]:
        """メモリ使用量上位オブジェクトを取得します。"""
        try:
            if not tracemalloc.is_tracing():
                return []

            # tracemalloc統計取得
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("filename")

            top_objects = []
            for stat in top_stats[:limit]:
                filename = stat.traceback.format()[0] if stat.traceback else "unknown"
                size_mb = stat.size / (1024 * 1024)
                top_objects.append((filename, stat.count, int(size_mb * 1024)))

            return top_objects

        except Exception as e:
            logger.error(f"上位オブジェクト取得エラー: {str(e)}")
            return []

    def _calculate_fragmentation_ratio(self) -> float:
        """メモリ断片化率を計算します。"""
        try:
            # 簡易断片化率計算（実際の実装では詳細な断片化分析が必要）
            virtual_memory = psutil.virtual_memory()
            available_ratio = virtual_memory.available / virtual_memory.total

            # 利用可能メモリが少ないほど断片化していると仮定
            fragmentation_ratio = 1.0 - available_ratio

            return min(fragmentation_ratio, 1.0)

        except Exception as e:
            logger.error(f"断片化率計算エラー: {str(e)}")
            return 0.0

    def _detect_memory_leaks(self) -> None:
        """メモリリーク検出処理"""
        try:
            if len(self._snapshots) < 3:
                return

            # 最近のスナップショットから成長パターンを分析
            recent_snapshots = list(self._snapshots)[-10:]

            for obj_type in set().union(
                *[s.object_counts.keys() for s in recent_snapshots]
            ):
                counts = [s.object_counts.get(obj_type, 0) for s in recent_snapshots]

                # 継続的な増加パターンをチェック
                if self._is_growing_pattern(counts):
                    self._leak_history[obj_type].extend(counts)

                    # リーク率計算
                    leak_rate = self._calculate_leak_rate(obj_type)
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

    def _calculate_leak_rate(self, obj_type: str) -> float:
        """リーク率を計算します（MB/秒）。"""
        try:
            history = self._leak_history[obj_type]
            if len(history) < 2:
                return 0.0

            # 簡易計算：オブジェクト数増加 × 推定サイズ
            count_increase = history[-1] - history[0]
            time_span = len(history) * self._config.snapshot_interval

            # 推定オブジェクトサイズ（1KB仮定）
            estimated_size_mb = count_increase * 0.001

            return estimated_size_mb / time_span

        except Exception as e:
            logger.error(f"リーク率計算エラー: {str(e)}")
            return 0.0

    def _generate_profiling_report(self) -> None:
        """プロファイリングレポートを生成します。"""
        try:
            os.makedirs("tmp", exist_ok=True)

            with self._lock:
                if not self._snapshots:
                    return

                # レポートデータ作成
                latest_snapshot = self._snapshots[-1]
                report_data = {
                    "profiling_summary": {
                        "total_snapshots": len(self._snapshots),
                        "profiling_duration_seconds": (
                            latest_snapshot.timestamp - self._snapshots[0].timestamp
                            if len(self._snapshots) > 1
                            else 0
                        ),
                        "current_memory_mb": latest_snapshot.process_memory_mb,
                        "peak_memory_mb": max(
                            s.process_memory_mb for s in self._snapshots
                        ),
                        "avg_memory_mb": sum(
                            s.process_memory_mb for s in self._snapshots
                        )
                        / len(self._snapshots),
                        "current_fragmentation": latest_snapshot.fragmentation_ratio,
                    },
                    "memory_trend": [
                        {
                            "timestamp": s.timestamp,
                            "memory_mb": s.process_memory_mb,
                            "fragmentation": s.fragmentation_ratio,
                        }
                        for s in list(self._snapshots)[-50:]  # 最新50件
                    ],
                    "top_objects": latest_snapshot.top_objects,
                    "object_counts": latest_snapshot.object_counts,
                    "gc_statistics": latest_snapshot.gc_stats,
                    "leak_detection": {
                        obj_type: {
                            "leak_rate_mb_per_sec": self._calculate_leak_rate(obj_type),
                            "history_length": len(history),
                        }
                        for obj_type, history in self._leak_history.items()
                    },
                    "optimization_recommendations": (
                        self._generate_optimization_recommendations()
                    ),
                }

            # レポート出力
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_path = f"tmp/memory_profiling_report_{timestamp}.json"

            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            logger.info(f"メモリプロファイリングレポート生成: {report_path}")

        except Exception as e:
            logger.error(f"プロファイリングレポート生成エラー: {str(e)}")

    def _generate_optimization_recommendations(self) -> List[str]:
        """最適化推奨事項を生成します。"""
        try:
            recommendations: List[str] = []

            if not self._snapshots:
                return recommendations

            latest = self._snapshots[-1]

            # メモリ使用量チェック
            if latest.process_memory_mb > self._config.memory_threshold_mb:
                recommendations.append(
                    f"メモリ使用量が閾値を超過しています "
                    f"({latest.process_memory_mb:.1f}MB > "
                    f"{self._config.memory_threshold_mb}MB)"
                )

            # 断片化チェック
            if latest.fragmentation_ratio > self._config.fragmentation_threshold:
                ratio = latest.fragmentation_ratio
                threshold = self._config.fragmentation_threshold
                recommendations.append(
                    f"メモリ断片化が深刻です ({ratio:.1%} > {threshold:.1%})"
                )

            # リークチェック
            high_leak_types = [
                obj_type
                for obj_type in self._leak_history.keys()
                if self._calculate_leak_rate(obj_type) > 0.1
            ]
            if high_leak_types:
                recommendations.append(
                    f"メモリリークの可能性: {', '.join(high_leak_types)}"
                )

            # オブジェクト数チェック
            large_object_types = [
                obj_type
                for obj_type, count in latest.object_counts.items()
                if count > 10000
            ]
            if large_object_types:
                recommendations.append(
                    f"大量のオブジェクトが検出されました: {', '.join(large_object_types)}"
                )

            return recommendations

        except Exception as e:
            logger.error(f"最適化推奨事項生成エラー: {str(e)}")
            return []

    def get_current_stats(self) -> Dict[str, Any]:
        """現在のメモリ統計を取得します。"""
        try:
            with self._lock:
                if not self._snapshots:
                    return {}

                latest = self._snapshots[-1]

                return {
                    "current_memory_mb": latest.process_memory_mb,
                    "virtual_memory_mb": latest.virtual_memory_mb,
                    "memory_percent": latest.memory_percent,
                    "fragmentation_ratio": latest.fragmentation_ratio,
                    "object_count_total": sum(latest.object_counts.values()),
                    "top_object_types": sorted(
                        latest.object_counts.items(), key=lambda x: x[1], reverse=True
                    )[:10],
                    "snapshots_taken": len(self._snapshots),
                    "potential_leaks": len(self._leak_history),
                    "is_profiling": self._is_profiling,
                }

        except Exception as e:
            logger.error(f"現在統計取得エラー: {str(e)}")
            return {}

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
