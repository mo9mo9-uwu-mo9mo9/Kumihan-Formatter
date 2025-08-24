"""ガベージコレクション効率分析"""

from __future__ import annotations

from typing import Any, Dict, List

from kumihan_formatter.core.utilities.logger import get_logger
from ..snapshot import MemorySnapshot

logger = get_logger(__name__)


class MemoryGCAnalyzer:
    """
    メモリガベージコレクション分析クラス

    GC効率と最適化のための詳細分析を実行します。
    """

    def __init__(self) -> None:
        """GC分析器を初期化します。"""
        try:
            logger.info("MemoryGCAnalyzer初期化完了")

        except Exception as e:
            logger.error(f"MemoryGCAnalyzer初期化エラー: {str(e)}")
            raise

    def analyze_gc_efficiency(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """GC効率分析"""
        try:
            if len(snapshots) < 2:
                return {}

            valid_snapshots = [s for s in snapshots if s.gc_stats]
            if len(valid_snapshots) < 2:
                return {}

            # GC統計の変化を分析
            first_gc = valid_snapshots[0].gc_stats
            last_gc = valid_snapshots[-1].gc_stats

            if len(first_gc) != len(last_gc):
                return {}

            gc_collections = []
            gc_collected = []

            for i in range(len(first_gc)):
                if isinstance(first_gc[i], dict) and isinstance(last_gc[i], dict):
                    collections_diff = last_gc[i].get("collections", 0) - first_gc[
                        i
                    ].get("collections", 0)
                    collected_diff = last_gc[i].get("collected", 0) - first_gc[i].get(
                        "collected", 0
                    )

                    gc_collections.append(collections_diff)
                    gc_collected.append(collected_diff)

            total_collections = sum(gc_collections)
            total_collected = sum(gc_collected)
            time_span = valid_snapshots[-1].timestamp - valid_snapshots[0].timestamp

            # GC効率スコア計算
            efficiency_score = self._calculate_gc_efficiency_score(valid_snapshots)

            # GCプレッシャー分析
            pressure_analysis = self._analyze_gc_pressure(valid_snapshots)

            return {
                "total_gc_collections": total_collections,
                "total_objects_collected": total_collected,
                "gc_frequency_per_second": (
                    total_collections / time_span if time_span > 0 else 0
                ),
                "gc_collections_by_generation": gc_collections,
                "gc_collected_by_generation": gc_collected,
                "gc_efficiency_score": efficiency_score,
                "gc_pressure_analysis": pressure_analysis,
                "gc_performance_level": self._get_gc_performance_level(
                    efficiency_score
                ),
                "collection_effectiveness": (
                    total_collected / total_collections if total_collections > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"GC効率分析エラー: {str(e)}")
            return {}

    def analyze_gc_patterns(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """GCパターン分析"""
        try:
            if len(snapshots) < 5:
                return {}

            valid_snapshots = [s for s in snapshots if s.gc_stats]
            if len(valid_snapshots) < 5:
                return {}

            patterns = {
                "frequent_minor_gc": self._detect_frequent_minor_gc(valid_snapshots),
                "major_gc_frequency": self._analyze_major_gc_frequency(valid_snapshots),
                "gc_pause_estimation": self._estimate_gc_pauses(valid_snapshots),
                "memory_gc_correlation": self._analyze_memory_gc_correlation(
                    valid_snapshots
                ),
            }

            return patterns

        except Exception as e:
            logger.error(f"GCパターン分析エラー: {str(e)}")
            return {}

    def generate_gc_recommendations(self, snapshots: List[MemorySnapshot]) -> List[str]:
        """GC最適化推奨事項を生成します"""
        try:
            recommendations: List[str] = []

            if len(snapshots) < 2:
                return recommendations

            gc_analysis = self.analyze_gc_efficiency(snapshots)

            # GC頻度チェック
            gc_frequency = gc_analysis.get("gc_frequency_per_second", 0)
            if gc_frequency > 10:  # 10回/秒以上
                recommendations.append(
                    f"GC頻度が高すぎます（{gc_frequency:.1f}回/秒）。"
                    "オブジェクト生成を削減するか、メモリプールを検討してください。"
                )

            # GC効率チェック
            efficiency_score = gc_analysis.get("gc_efficiency_score", 0)
            if efficiency_score < 0.5:
                recommendations.append(
                    f"GC効率が低下しています（スコア: {efficiency_score:.2f}）。"
                    "長生きするオブジェクトの参照を確認してください。"
                )

            # 世代別GC分析
            gc_collections = gc_analysis.get("gc_collections_by_generation", [])
            if len(gc_collections) >= 3 and gc_collections[2] > gc_collections[0] * 0.1:
                recommendations.append(
                    "Major GCが頻繁に発生しています。"
                    "長期間保持されるオブジェクトを削減してください。"
                )

            # コレクション効果チェック
            effectiveness = gc_analysis.get("collection_effectiveness", 0)
            if effectiveness < 10:  # 1回のGCで平均10個未満の回収
                recommendations.append(
                    "GCの回収効率が低下しています。"
                    "不要な参照の保持を確認してください。"
                )

            return recommendations

        except Exception as e:
            logger.error(f"GC推奨事項生成エラー: {str(e)}")
            return []

    def _calculate_gc_efficiency_score(self, snapshots: List[MemorySnapshot]) -> float:
        """GC効率スコアを計算します（0-1）"""
        try:
            if len(snapshots) < 2:
                return 0.0

            memory_values = [s.process_memory_mb for s in snapshots]
            gc_stats_list = [s.gc_stats for s in snapshots if s.gc_stats]

            if len(gc_stats_list) < 2:
                return 0.0

            # メモリ安定性（GCがメモリを効果的に管理しているか）
            memory_stability = self._calculate_memory_stability(memory_values)

            # GC頻度の適切性（頻繁すぎず、少なすぎない）
            gc_frequency_score = self._calculate_gc_frequency_score(
                gc_stats_list, snapshots
            )

            # 総合効率スコア
            efficiency_score = (memory_stability * 0.6) + (gc_frequency_score * 0.4)

            return min(max(efficiency_score, 0.0), 1.0)

        except Exception as e:
            logger.error(f"GC効率スコア計算エラー: {str(e)}")
            return 0.0

    def _analyze_gc_pressure(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """GCプレッシャー分析"""
        try:
            if len(snapshots) < 3:
                return {}

            # メモリ使用量の変動とGC発生の関係を分析
            memory_changes = []
            gc_events = []

            for i in range(1, len(snapshots)):
                memory_diff = (
                    snapshots[i].process_memory_mb - snapshots[i - 1].process_memory_mb
                )
                memory_changes.append(memory_diff)

                # GCイベント数の変化（簡易計算）
                if snapshots[i].gc_stats and snapshots[i - 1].gc_stats:
                    current_collections = sum(
                        stat.get("collections", 0)
                        for stat in snapshots[i].gc_stats
                        if isinstance(stat, dict)
                    )
                    prev_collections = sum(
                        stat.get("collections", 0)
                        for stat in snapshots[i - 1].gc_stats
                        if isinstance(stat, dict)
                    )
                    gc_events.append(current_collections - prev_collections)

            if not gc_events:
                return {}

            # プレッシャー指標
            avg_memory_change = sum(memory_changes) / len(memory_changes)
            avg_gc_events = sum(gc_events) / len(gc_events)

            # プレッシャーレベル判定
            pressure_level = "low"
            if avg_gc_events > 5 or avg_memory_change > 50:  # 50MB以上の変動
                pressure_level = "high"
            elif avg_gc_events > 2 or avg_memory_change > 20:
                pressure_level = "medium"

            return {
                "average_memory_change_mb": avg_memory_change,
                "average_gc_events_per_interval": avg_gc_events,
                "pressure_level": pressure_level,
            }

        except Exception as e:
            logger.error(f"GCプレッシャー分析エラー: {str(e)}")
            return {}

    def _calculate_memory_stability(self, memory_values: List[float]) -> float:
        """メモリ安定性を計算します"""
        try:
            if len(memory_values) < 2:
                return 0.0

            mean_memory = sum(memory_values) / len(memory_values)
            variance = sum((v - mean_memory) ** 2 for v in memory_values) / len(
                memory_values
            )
            cv = (variance**0.5) / mean_memory if mean_memory > 0 else 1.0

            # 変動係数が小さいほど安定
            stability = max(0.0, 1.0 - cv)
            return min(stability, 1.0)

        except Exception as e:
            logger.error(f"メモリ安定性計算エラー: {str(e)}")
            return 0.0

    def _calculate_gc_frequency_score(
        self, gc_stats_list: List[List[Any]], snapshots: List[MemorySnapshot]
    ) -> float:
        """GC頻度スコアを計算します"""
        try:
            if len(gc_stats_list) < 2 or len(snapshots) < 2:
                return 0.0

            time_span = snapshots[-1].timestamp - snapshots[0].timestamp

            # 総GC回数計算
            total_collections = 0
            for gc_stats in gc_stats_list:
                for stat in gc_stats:
                    if isinstance(stat, dict):
                        total_collections += stat.get("collections", 0)

            gc_per_second = total_collections / time_span if time_span > 0 else 0

            # 適切な頻度範囲（1-5回/秒）でスコア計算
            if 1 <= gc_per_second <= 5:
                return 1.0
            elif 0.5 <= gc_per_second < 1 or 5 < gc_per_second <= 10:
                return 0.7
            elif gc_per_second < 0.5 or gc_per_second > 20:
                return 0.2
            else:
                return 0.5

        except Exception as e:
            logger.error(f"GC頻度スコア計算エラー: {str(e)}")
            return 0.0

    def _get_gc_performance_level(self, efficiency_score: float) -> str:
        """GC性能レベルを取得します"""
        try:
            if efficiency_score >= 0.8:
                return "excellent"
            elif efficiency_score >= 0.6:
                return "good"
            elif efficiency_score >= 0.4:
                return "fair"
            elif efficiency_score >= 0.2:
                return "poor"
            else:
                return "critical"

        except Exception as e:
            logger.error(f"GC性能レベル取得エラー: {str(e)}")
            return "unknown"

    def _detect_frequent_minor_gc(self, snapshots: List[MemorySnapshot]) -> bool:
        """頻繁なMinor GCを検出します"""
        try:
            if len(snapshots) < 3:
                return False

            # Generation 0のGC頻度を確認
            gen0_collections = []
            for snapshot in snapshots:
                if snapshot.gc_stats and len(snapshot.gc_stats) > 0:
                    if isinstance(snapshot.gc_stats[0], dict):
                        gen0_collections.append(
                            snapshot.gc_stats[0].get("collections", 0)
                        )

            if len(gen0_collections) < 2:
                return False

            total_gen0_gc = gen0_collections[-1] - gen0_collections[0]
            time_span = snapshots[-1].timestamp - snapshots[0].timestamp

            gc_frequency = total_gen0_gc / time_span if time_span > 0 else 0

            return gc_frequency > 20  # 20回/秒以上

        except Exception as e:
            logger.error(f"頻繁Minor GC検出エラー: {str(e)}")
            return False

    def _analyze_major_gc_frequency(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """Major GC頻度分析"""
        try:
            if len(snapshots) < 2:
                return {}

            # Generation 2のGC統計を確認
            gen2_collections = []
            for snapshot in snapshots:
                if snapshot.gc_stats and len(snapshot.gc_stats) > 2:
                    if isinstance(snapshot.gc_stats[2], dict):
                        gen2_collections.append(
                            snapshot.gc_stats[2].get("collections", 0)
                        )

            if len(gen2_collections) < 2:
                return {}

            total_major_gc = gen2_collections[-1] - gen2_collections[0]
            time_span = snapshots[-1].timestamp - snapshots[0].timestamp

            major_gc_frequency = total_major_gc / time_span if time_span > 0 else 0

            return {
                "major_gc_frequency_per_second": major_gc_frequency,
                "total_major_gc": total_major_gc,
                "is_frequent": major_gc_frequency > 0.1,  # 0.1回/秒以上
            }

        except Exception as e:
            logger.error(f"Major GC頻度分析エラー: {str(e)}")
            return {}

    def _estimate_gc_pauses(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """GC一時停止時間推定"""
        try:
            # 実際のGC一時停止時間は測定が困難なため、
            # GC頻度とメモリ変動から推定値を算出

            if len(snapshots) < 3:
                return {}

            memory_values = [s.process_memory_mb for s in snapshots]
            memory_volatility = self._calculate_memory_stability(memory_values)

            # 推定一時停止時間（実際の値ではなく相対的指標）
            estimated_pause_impact = (1.0 - memory_volatility) * 100  # ms単位での推定

            return {
                "estimated_pause_impact_ms": estimated_pause_impact,
                "pause_severity": (
                    "high"
                    if estimated_pause_impact > 50
                    else "medium" if estimated_pause_impact > 20 else "low"
                ),
            }

        except Exception as e:
            logger.error(f"GC一時停止推定エラー: {str(e)}")
            return {}

    def _analyze_memory_gc_correlation(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """メモリ使用量とGC発生の相関分析"""
        try:
            if len(snapshots) < 5:
                return {}

            memory_values = [s.process_memory_mb for s in snapshots]
            gc_events = []

            for i in range(1, len(snapshots)):
                if snapshots[i].gc_stats and snapshots[i - 1].gc_stats:
                    current_total = sum(
                        stat.get("collections", 0)
                        for stat in snapshots[i].gc_stats
                        if isinstance(stat, dict)
                    )
                    prev_total = sum(
                        stat.get("collections", 0)
                        for stat in snapshots[i - 1].gc_stats
                        if isinstance(stat, dict)
                    )
                    gc_events.append(current_total - prev_total)

            if len(gc_events) != len(memory_values) - 1:
                return {}

            # 簡単な相関係数計算
            memory_changes = [
                memory_values[i + 1] - memory_values[i]
                for i in range(len(memory_values) - 1)
            ]

            correlation = self._calculate_correlation(memory_changes, gc_events)

            return {
                "memory_gc_correlation": float(correlation),
                "correlation_strength": str(
                    "strong"
                    if abs(correlation) > 0.7
                    else "moderate" if abs(correlation) > 0.3 else "weak"
                ),
            }

        except Exception as e:
            logger.error(f"メモリGC相関分析エラー: {str(e)}")
            return {}

    def _calculate_correlation(
        self, x_values: List[float], y_values: List[float]
    ) -> float:
        """相関係数を計算します"""
        try:
            if len(x_values) != len(y_values) or len(x_values) < 2:
                return 0.0

            n = len(x_values)
            x_mean = sum(x_values) / n
            y_mean = sum(y_values) / n

            numerator = sum(
                (x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n)
            )
            x_variance = sum((x - x_mean) ** 2 for x in x_values)
            y_variance = sum((y - y_mean) ** 2 for y in y_values)

            if x_variance == 0 or y_variance == 0:
                return 0.0

            correlation = numerator / (x_variance * y_variance) ** 0.5
            return float(correlation)

        except Exception as e:
            logger.error(f"相関係数計算エラー: {str(e)}")
            return 0.0
