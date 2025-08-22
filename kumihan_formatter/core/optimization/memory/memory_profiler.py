"""
メモリプロファイラーシステム

メモリ使用量の詳細計測とメモリリーク検出機能を提供します。
プロセスメモリ推移、オブジェクト別メモリ使用量、ガベージコレクション統計、
メモリ断片化率の計測とレポート生成を行います。

Classes:
    MemoryProfiler: メモリプロファイラーメインクラス
    MemoryLeakDetector: メモリリーク検出器クラス
    MemoryUsageAnalyzer: メモリ使用パターン分析クラス
    OptimizationEffectReporter: 最適化効果レポーターク���ス
"""

import gc
import os
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock, RLock
from typing import Any, Dict, List, Optional, Tuple, cast

import psutil

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemorySnapshot:
    """メモリスナップショット"""

    timestamp: float
    process_memory_mb: float
    virtual_memory_mb: float
    memory_percent: float
    gc_stats: List[Dict[str, Any]]
    object_counts: Dict[str, int]
    top_objects: List[Tuple[str, int, int]]  # (type, count, size)
    fragmentation_ratio: float


@dataclass
class MemoryLeakInfo:
    """メモリリーク情報"""

    object_type: str
    leak_rate_mb_per_sec: float
    total_leaked_mb: float
    detection_time: float
    confidence_score: float
    growth_pattern: List[float]


@dataclass
class ProfilerConfig:
    """プロファイラー設定"""

    snapshot_interval: int = 30  # スナップショット間隔（秒）
    leak_detection_window: int = 300  # リーク検出ウィンドウ（秒）
    memory_threshold_mb: float = 1000.0  # メモリ閾値（MB）
    fragmentation_threshold: float = 0.3  # 断片化閾値（30%）
    enable_tracemalloc: bool = True
    tracemalloc_limit: int = 100


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

            import json

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


class MemoryLeakDetector:
    """
    メモリリーク検出器クラス

    より高度なメモリリーク検出とパターン分析を提供します。
    """

    def __init__(self, profiler: MemoryProfiler) -> None:
        """
        メモリリーク検出器を初期化します。

        Args:
            profiler: メモリプロファイラー
        """
        try:
            self._profiler = profiler
            self._detected_leaks: Dict[str, MemoryLeakInfo] = {}
            self._lock = Lock()

            logger.info("MemoryLeakDetector初期化完了")

        except Exception as e:
            logger.error(f"MemoryLeakDetector初期化エラー: {str(e)}")
            raise

    def detect_leaks(self, confidence_threshold: float = 0.7) -> List[MemoryLeakInfo]:
        """
        高度なメモリリーク検出を実行します。

        Args:
            confidence_threshold: 信頼度閾値

        Returns:
            検出されたメモリリーク情報
        """
        try:
            with self._lock:
                snapshots = list(self._profiler._snapshots)

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


class MemoryUsageAnalyzer:
    """
    メモリ使用パターン分析クラス

    メモリ使用パターンを分析し、最適化ポイントを特定します。
    """

    def __init__(self, profiler: MemoryProfiler) -> None:
        """
        メモリ使用分析器を初期化します。

        Args:
            profiler: メモリプロファイラー
        """
        try:
            self._profiler = profiler
            self._analysis_cache: Dict[str, Any] = {}
            self._lock = Lock()

            logger.info("MemoryUsageAnalyzer初期化完了")

        except Exception as e:
            logger.error(f"MemoryUsageAnalyzer初期化エラー: {str(e)}")
            raise

    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """メモリ使用パターンを分析します。"""
        try:
            with self._lock:
                snapshots = list(self._profiler._snapshots)

                if len(snapshots) < 3:
                    return {}

                analysis = {
                    "memory_trend": self._analyze_memory_trend(snapshots),
                    "peak_analysis": self._analyze_peaks(snapshots),
                    "fragmentation_analysis": self._analyze_fragmentation(snapshots),
                    "object_distribution": self._analyze_object_distribution(snapshots),
                    "gc_efficiency": self._analyze_gc_efficiency(snapshots),
                    "optimization_opportunities": (
                        self._identify_optimization_opportunities(snapshots)
                    ),
                }

                self._analysis_cache["latest_analysis"] = analysis
                return analysis

        except Exception as e:
            logger.error(f"使用パターン分析エラー: {str(e)}")
            return {}

    def _analyze_memory_trend(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """メモリトレンド分析"""
        try:
            memory_values = [s.process_memory_mb for s in snapshots]

            # 線形回帰による傾向分析
            n = len(memory_values)
            x_mean = (n - 1) / 2
            y_mean = sum(memory_values) / n

            numerator = sum(
                (i - x_mean) * (memory_values[i] - y_mean) for i in range(n)
            )
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0

            # 変動係数
            std_dev = (sum((v - y_mean) ** 2 for v in memory_values) / n) ** 0.5
            cv = std_dev / y_mean if y_mean > 0 else 0

            return {
                "trend_slope_mb_per_snapshot": slope,
                "average_memory_mb": y_mean,
                "memory_volatility": cv,
                "trend_direction": (
                    "increasing"
                    if slope > 0.1
                    else "decreasing" if slope < -0.1 else "stable"
                ),
                "min_memory_mb": min(memory_values),
                "max_memory_mb": max(memory_values),
            }

        except Exception as e:
            logger.error(f"メモリトレンド分析エラー: {str(e)}")
            return {}

    def _analyze_peaks(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """ピーク分析"""
        try:
            memory_values = [s.process_memory_mb for s in snapshots]
            timestamps = [s.timestamp for s in snapshots]

            # ピーク検出
            peaks = []
            for i in range(1, len(memory_values) - 1):
                if (
                    memory_values[i] > memory_values[i - 1]
                    and memory_values[i] > memory_values[i + 1]
                ):
                    peaks.append(
                        {
                            "timestamp": timestamps[i],
                            "memory_mb": memory_values[i],
                            "index": i,
                        }
                    )

            # 平均からの乖離分析
            avg_memory = sum(memory_values) / len(memory_values)
            significant_peaks = [p for p in peaks if p["memory_mb"] > avg_memory * 1.2]

            return {
                "total_peaks": len(peaks),
                "significant_peaks": len(significant_peaks),
                "peak_frequency": len(peaks) / len(snapshots) if snapshots else 0,
                "avg_peak_height_mb": (
                    sum(p["memory_mb"] for p in peaks) / len(peaks) if peaks else 0
                ),
                "max_peak_mb": max((p["memory_mb"] for p in peaks), default=0),
            }

        except Exception as e:
            logger.error(f"ピーク分析エラー: {str(e)}")
            return {}

    def _analyze_fragmentation(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """断片化分析"""
        try:
            fragmentation_values = [s.fragmentation_ratio for s in snapshots]

            avg_fragmentation = sum(fragmentation_values) / len(fragmentation_values)
            max_fragmentation = max(fragmentation_values)

            # 断片化の悪化傾向
            recent_fragmentation = sum(fragmentation_values[-5:]) / min(
                5, len(fragmentation_values)
            )
            early_fragmentation = sum(fragmentation_values[:5]) / min(
                5, len(fragmentation_values)
            )

            fragmentation_trend = recent_fragmentation - early_fragmentation

            return {
                "average_fragmentation": avg_fragmentation,
                "max_fragmentation": max_fragmentation,
                "fragmentation_trend": fragmentation_trend,
                "fragmentation_severity": (
                    "critical"
                    if avg_fragmentation > 0.5
                    else (
                        "high"
                        if avg_fragmentation > 0.3
                        else "moderate" if avg_fragmentation > 0.1 else "low"
                    )
                ),
            }

        except Exception as e:
            logger.error(f"断片化分析エラー: {str(e)}")
            return {}

    def _analyze_object_distribution(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """オブジェクト分布分析"""
        try:
            # 最新スナップショットのオブジェクト分布
            latest = snapshots[-1]
            total_objects = sum(latest.object_counts.values())

            # 上位オブジェクトタイプ
            sorted_objects = sorted(
                latest.object_counts.items(), key=lambda x: x[1], reverse=True
            )

            # 集中度分析（上位10%のオブジェクトタイプが全体の何%を占めるか）
            top_10_percent_count = max(1, len(sorted_objects) // 10)
            top_objects_sum = sum(
                count for _, count in sorted_objects[:top_10_percent_count]
            )
            concentration_ratio = (
                top_objects_sum / total_objects if total_objects > 0 else 0
            )

            return {
                "total_object_count": total_objects,
                "object_type_diversity": len(latest.object_counts),
                "top_object_types": sorted_objects[:10],
                "concentration_ratio": concentration_ratio,
                "distribution_balance": (
                    "concentrated"
                    if concentration_ratio > 0.8
                    else "balanced" if concentration_ratio > 0.4 else "distributed"
                ),
            }

        except Exception as e:
            logger.error(f"オブジェクト分布分析エラー: {str(e)}")
            return {}

    def _analyze_gc_efficiency(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """GC効率分析"""
        try:
            if not snapshots or not snapshots[0].gc_stats:
                return {}

            # GC統計の変化を分析
            first_gc = snapshots[0].gc_stats
            last_gc = snapshots[-1].gc_stats

            if len(first_gc) != len(last_gc):
                return {}

            gc_collections = []
            for i in range(len(first_gc)):
                collections_diff = last_gc[i].get("collections", 0) - first_gc[i].get(
                    "collections", 0
                )
                gc_collections.append(collections_diff)

            total_collections = sum(gc_collections)
            time_span = snapshots[-1].timestamp - snapshots[0].timestamp

            return {
                "total_gc_collections": total_collections,
                "gc_frequency_per_second": (
                    total_collections / time_span if time_span > 0 else 0
                ),
                "gc_collections_by_generation": gc_collections,
                "gc_efficiency_score": self._calculate_gc_efficiency_score(snapshots),
            }

        except Exception as e:
            logger.error(f"GC効率分析エラー: {str(e)}")
            return {}

    def _calculate_gc_efficiency_score(self, snapshots: List[MemorySnapshot]) -> float:
        """GC効率スコアを計算"""
        try:
            memory_values = [s.process_memory_mb for s in snapshots]

            # メモリ使用量の変動とGC頻度の関係から効率性を評価
            memory_variance = sum(
                (m - sum(memory_values) / len(memory_values)) ** 2
                for m in memory_values
            ) / len(memory_values)

            # 正規化（0-1の範囲）
            normalized_variance = min(memory_variance / 100, 1.0)  # 100MB^2を基準

            # 効率スコア（低い変動 = 高い効率）
            return 1.0 - normalized_variance

        except Exception as e:
            logger.error(f"GC効率スコア計算エラー: {str(e)}")
            return 0.0

    def _identify_optimization_opportunities(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """最適化機会を特定"""
        try:
            opportunities: List[str] = []

            if not snapshots:
                return opportunities

            # メモリトレンド分析結果に基づく推奨
            trend_analysis = self._analyze_memory_trend(snapshots)
            if trend_analysis.get("trend_slope_mb_per_snapshot", 0) > 1.0:
                opportunities.append(
                    "継続的なメモリ増加が検出されました。メモリリークの調査を推奨します。"
                )

            # 断片化分析結果に基づく推奨
            frag_analysis = self._analyze_fragmentation(snapshots)
            if frag_analysis.get("fragmentation_severity") in ["high", "critical"]:
                opportunities.append(
                    "メモリ断片化が深刻です。オブジェクトプールやメモリプールの導入を推奨します。"
                )

            # オブジェクト分布分析結果に基づく推奨
            obj_analysis = self._analyze_object_distribution(snapshots)
            if obj_analysis.get("concentration_ratio", 0) > 0.8:
                opportunities.append(
                    "特定のオブジェクトタイプに偏っています。オブジェクトリサイクルを検討してください。"
                )

            # GC効率分析結果に基づく推奨
            gc_analysis = self._analyze_gc_efficiency(snapshots)
            if gc_analysis.get("gc_efficiency_score", 1.0) < 0.5:
                opportunities.append(
                    "ガベージコレクションの効率が低下しています。弱参照の活用を推奨します。"
                )

            return opportunities

        except Exception as e:
            logger.error(f"最適化機会特定エラー: {str(e)}")
            return []


class OptimizationEffectReporter:
    """
    最適化効果レポータークラス

    メモリ最適化の効果を定量的に評価・レポートします。
    """

    def __init__(self) -> None:
        """最適化効果レポーターを初期化します。"""
        try:
            self._baseline_stats: Optional[Dict[str, Any]] = None
            self._optimization_points: List[Dict[str, Any]] = []
            self._lock = Lock()

            logger.info("OptimizationEffectReporter初期化完了")

        except Exception as e:
            logger.error(f"OptimizationEffectReporter初期化エラー: {str(e)}")
            raise

    def set_baseline(self, profiler: MemoryProfiler) -> None:
        """
        ベースライン統計を設定します。

        Args:
            profiler: メモリプロファイラー
        """
        try:
            with self._lock:
                self._baseline_stats = profiler.get_current_stats()
                self._baseline_stats["timestamp"] = time.time()
                logger.info("最適化ベースライン設定完了")

        except Exception as e:
            logger.error(f"ベースライン設定エラー: {str(e)}")
            raise

    def record_optimization_point(
        self, profiler: MemoryProfiler, optimization_name: str, description: str = ""
    ) -> None:
        """
        最適化ポイントを記録します。

        Args:
            profiler: メモリプロファイラー
            optimization_name: 最適化名
            description: 説明
        """
        try:
            with self._lock:
                current_stats = profiler.get_current_stats()
                current_stats["timestamp"] = time.time()

                optimization_point = {
                    "name": optimization_name,
                    "description": description,
                    "stats": current_stats,
                    "improvement": (
                        self._calculate_improvement(current_stats)
                        if self._baseline_stats
                        else {}
                    ),
                }

                self._optimization_points.append(optimization_point)
                logger.info(f"最適化ポイント記録: {optimization_name}")

        except Exception as e:
            logger.error(f"最適化ポイント記録エラー: {str(e)}")

    def _calculate_improvement(self, current_stats: Dict[str, Any]) -> Dict[str, Any]:
        """最適化効果を計算します。"""
        try:
            if not self._baseline_stats:
                return {}

            baseline_memory = self._baseline_stats.get("current_memory_mb", 0)
            current_memory = current_stats.get("current_memory_mb", 0)

            memory_reduction_mb = baseline_memory - current_memory
            memory_reduction_percent = (
                (memory_reduction_mb / baseline_memory * 100)
                if baseline_memory > 0
                else 0
            )

            baseline_fragmentation = self._baseline_stats.get("fragmentation_ratio", 0)
            current_fragmentation = current_stats.get("fragmentation_ratio", 0)

            fragmentation_improvement = baseline_fragmentation - current_fragmentation

            return {
                "memory_reduction_mb": memory_reduction_mb,
                "memory_reduction_percent": memory_reduction_percent,
                "fragmentation_improvement": fragmentation_improvement,
                "object_count_change": (
                    current_stats.get("object_count_total", 0)
                    - self._baseline_stats.get("object_count_total", 0)
                ),
            }

        except Exception as e:
            logger.error(f"改善効果計算エラー: {str(e)}")
            return {}

    def generate_effect_report(self) -> Dict[str, Any]:
        """最適化効果レポートを生成します。"""
        try:
            with self._lock:
                if not self._baseline_stats or not self._optimization_points:
                    return {}

                # 最新の最適化ポイント
                latest_point = self._optimization_points[-1]

                # 総合効果計算
                total_improvement = self._calculate_improvement(latest_point["stats"])

                # 最適化履歴
                optimization_history = [
                    {
                        "name": point["name"],
                        "description": point["description"],
                        "memory_mb": point["stats"].get("current_memory_mb", 0),
                        "improvement": point["improvement"],
                    }
                    for point in self._optimization_points
                ]

                report = {
                    "summary": {
                        "baseline_memory_mb": self._baseline_stats.get(
                            "current_memory_mb", 0
                        ),
                        "current_memory_mb": latest_point["stats"].get(
                            "current_memory_mb", 0
                        ),
                        "total_memory_reduction_mb": total_improvement.get(
                            "memory_reduction_mb", 0
                        ),
                        "total_memory_reduction_percent": total_improvement.get(
                            "memory_reduction_percent", 0
                        ),
                        "fragmentation_improvement": total_improvement.get(
                            "fragmentation_improvement", 0
                        ),
                        "optimization_count": len(self._optimization_points),
                    },
                    "optimization_history": optimization_history,
                    "effectiveness_score": self._calculate_effectiveness_score(
                        total_improvement
                    ),
                    "recommendations": self._generate_future_recommendations(
                        total_improvement
                    ),
                }

                # レポートファイル出力
                os.makedirs("tmp", exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                report_path = f"tmp/optimization_effect_report_{timestamp}.json"

                import json

                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                logger.info(f"最適化効果レポート生成: {report_path}")
                return report

        except Exception as e:
            logger.error(f"効果レポート生成エラー: {str(e)}")
            return {}

    def _calculate_effectiveness_score(self, improvement: Dict[str, Any]) -> float:
        """効果スコアを計算します（0-1の範囲）。"""
        try:
            # メモリ削減効果
            memory_score = min(
                improvement.get("memory_reduction_percent", 0) / 30, 1.0
            )  # 30%削減で満点

            # 断片化改善効果
            frag_score = min(
                improvement.get("fragmentation_improvement", 0) / 0.3, 1.0
            )  # 30%改善で満点

            # 総合スコア
            total_score = memory_score * 0.7 + frag_score * 0.3

            return cast(float, max(0.0, min(total_score, 1.0)))

        except Exception as e:
            logger.error(f"効果スコア計算エラー: {str(e)}")
            return 0.0

    def _generate_future_recommendations(
        self, improvement: Dict[str, Any]
    ) -> List[str]:
        """今後の推奨事項を生成します。"""
        try:
            recommendations = []

            memory_reduction = improvement.get("memory_reduction_percent", 0)
            if memory_reduction < 10:
                recommendations.append(
                    "メモリ削減効果が限定的です。追加の最適化手法を検討してください。"
                )
            elif memory_reduction > 30:
                recommendations.append(
                    "優秀なメモリ削減効果です。現在の最適化設定を維持してください。"
                )

            frag_improvement = improvement.get("fragmentation_improvement", 0)
            if frag_improvement < 0.1:
                recommendations.append(
                    "メモリ断片化の改善余地があります。オブジェクトプールの調整を検討してください。"
                )

            if not recommendations:
                recommendations.append(
                    "現在の最適化は適切に機能しています。定期的な監視を継続してください。"
                )

            return recommendations

        except Exception as e:
            logger.error(f"推奨事項生成エラー: {str(e)}")
            return []


# グローバルインスタンス
_global_profiler = MemoryProfiler()
_global_leak_detector = MemoryLeakDetector(_global_profiler)
_global_usage_analyzer = MemoryUsageAnalyzer(_global_profiler)
_global_effect_reporter = OptimizationEffectReporter()


def get_memory_profiler() -> MemoryProfiler:
    """グローバルメモリプロファイラーを取得します。"""
    return _global_profiler


def get_leak_detector() -> MemoryLeakDetector:
    """グローバルメモリリーク検出器を取得します。"""
    return _global_leak_detector


def get_usage_analyzer() -> MemoryUsageAnalyzer:
    """グローバルメモリ使用分析器を取得します。"""
    return _global_usage_analyzer


def get_effect_reporter() -> OptimizationEffectReporter:
    """グローバル最適化効果レポーターを取得します。"""
    return _global_effect_reporter


if __name__ == "__main__":
    """メモリプロファイラーシステムのテスト実行"""

    def test_memory_profiler() -> None:
        """メモリプロファイラーテスト"""
        logger.info("=== メモリプロファイラーテスト開始 ===")

        profiler = get_memory_profiler()

        # プロファイリング開始
        profiler.start_profiling()

        # メモリ使用量変動をシミュレート
        test_objects = []
        for i in range(1000):
            test_objects.append(list(range(100)))

        import time

        time.sleep(2)  # スナップショット取得待ち

        # 現在統計確認
        stats = profiler.get_current_stats()
        logger.info(f"現在のメモリ統計: {stats}")

        # オブジェクト削除
        del test_objects

        # 強制GC
        gc_result = profiler.force_garbage_collection()
        logger.info(f"GC結果: {gc_result}")

        # プロファイリング停止
        profiler.stop_profiling()

    def test_leak_detection() -> None:
        """メモリリーク検出テスト"""
        logger.info("=== メモリリーク検出テスト開始 ===")

        profiler = get_memory_profiler()
        leak_detector = get_leak_detector()

        # プロファイリング開始
        profiler.start_profiling()

        # リークシミュレート
        leak_objects = []
        for i in range(500):
            leak_objects.append({f"key_{j}": f"value_{j}" for j in range(50)})
            if i % 100 == 0:
                import time

                time.sleep(0.5)

        # リーク検出実行
        detected_leaks = leak_detector.detect_leaks()
        logger.info(f"検出されたリーク: {len(detected_leaks)}")

        # リークサマリー
        leak_summary = leak_detector.get_leak_summary()
        logger.info(f"リークサマリー: {leak_summary}")

        # プロファイリング停止
        profiler.stop_profiling()

    def test_usage_analysis() -> None:
        """メモリ使用パターン分析テスト"""
        logger.info("=== メモリ使用パターン分析テスト開始 ===")

        profiler = get_memory_profiler()
        analyzer = get_usage_analyzer()

        # プロファイリング開始
        profiler.start_profiling()

        # 使用パターン生成
        import time

        for cycle in range(3):
            # メモリ使用量増加
            temp_objects = [list(range(200)) for _ in range(300)]  # noqa: F841
            time.sleep(1)

            # メモリ解放
            del temp_objects
            gc.collect()
            time.sleep(1)

        # パターン分析実行
        analysis = analyzer.analyze_usage_patterns()
        logger.info(f"使用パターン分析: {analysis}")

        # プロファイリング停止
        profiler.stop_profiling()

    def test_optimization_effect_reporting() -> None:
        """最適化効果レポートテスト"""
        logger.info("=== 最適化効果レポートテスト開始 ===")

        profiler = get_memory_profiler()
        reporter = get_effect_reporter()

        # プロファイリング開始
        profiler.start_profiling()

        import time

        time.sleep(1)

        # ベースライン設定
        reporter.set_baseline(profiler)

        # 最適化シミュレート（メモリプール使用）
        memory_pool = []
        for i in range(100):
            memory_pool.append(list(range(50)))

        time.sleep(1)
        reporter.record_optimization_point(
            profiler, "memory_pool_introduction", "メモリプール導入"
        )

        # さらなる最適化（オブジェクト削除）
        del memory_pool[:50]
        gc.collect()

        time.sleep(1)
        reporter.record_optimization_point(
            profiler, "object_cleanup", "オブジェクトクリーンアップ"
        )

        # 効果レポート生成
        effect_report = reporter.generate_effect_report()
        logger.info(f"最適化効果レポート: {effect_report}")

        # プロファイリング停止
        profiler.stop_profiling()

    try:
        # テスト実行
        test_memory_profiler()
        test_leak_detection()
        test_usage_analysis()
        test_optimization_effect_reporting()

        logger.info("=== メモリプロファイラーシステムテスト完了 ===")

    except Exception as e:
        logger.error(f"テスト実行エラー: {str(e)}")
        raise
    finally:
        # 全プロファイラー停止
        get_memory_profiler().stop_profiling()

        # 最終レポート生成
        try:
            get_memory_profiler()._generate_profiling_report()
        except Exception:
            pass
