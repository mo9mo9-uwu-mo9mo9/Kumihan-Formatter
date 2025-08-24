"""メモリ使用パターン分析器"""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, List, TYPE_CHECKING

from kumihan_formatter.core.utilities.logger import get_logger

from .snapshot import MemorySnapshot

if TYPE_CHECKING:
    from .core_profiler import MemoryProfiler

logger = get_logger(__name__)


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
