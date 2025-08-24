"""オブジェクト分布・断片化分析"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from kumihan_formatter.core.utilities.logger import get_logger
from ..snapshot import MemorySnapshot

logger = get_logger(__name__)


class MemoryObjectAnalyzer:
    """
    メモリオブジェクト分析クラス

    オブジェクト分布とメモリ断片化の詳細分析を実行します。
    """

    def __init__(self) -> None:
        """オブジェクト分析器を初期化します。"""
        try:
            logger.info("MemoryObjectAnalyzer初期化完了")

        except Exception as e:
            logger.error(f"MemoryObjectAnalyzer初期化エラー: {str(e)}")
            raise

    def analyze_fragmentation(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """断片化分析"""
        try:
            if not snapshots:
                return {}

            fragmentation_values = [s.fragmentation_ratio for s in snapshots]

            avg_fragmentation = sum(fragmentation_values) / len(fragmentation_values)
            max_fragmentation = max(fragmentation_values)
            min_fragmentation = min(fragmentation_values)

            # 断片化の悪化傾向
            recent_fragmentation = sum(fragmentation_values[-5:]) / min(
                5, len(fragmentation_values)
            )
            early_fragmentation = sum(fragmentation_values[:5]) / min(
                5, len(fragmentation_values)
            )

            fragmentation_trend = recent_fragmentation - early_fragmentation

            # 断片化変動分析
            fragmentation_volatility = self._calculate_volatility(fragmentation_values)

            return {
                "average_fragmentation": avg_fragmentation,
                "max_fragmentation": max_fragmentation,
                "min_fragmentation": min_fragmentation,
                "fragmentation_range": max_fragmentation - min_fragmentation,
                "fragmentation_trend": fragmentation_trend,
                "fragmentation_volatility": fragmentation_volatility,
                "fragmentation_severity": self._get_fragmentation_severity(
                    avg_fragmentation
                ),
                "trend_direction": (
                    "worsening"
                    if fragmentation_trend > 0.05
                    else "improving" if fragmentation_trend < -0.05 else "stable"
                ),
            }

        except Exception as e:
            logger.error(f"断片化分析エラー: {str(e)}")
            return {}

    def analyze_object_distribution(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """オブジェクト分布分析"""
        try:
            if not snapshots:
                return {}

            # 最新スナップショットのオブジェクト分布
            latest = snapshots[-1]
            total_objects = (
                sum(latest.object_counts.values()) if latest.object_counts else 0
            )

            if total_objects == 0:
                return {}

            # 上位オブジェクトタイプ
            sorted_objects = sorted(
                latest.object_counts.items(), key=lambda x: x[1], reverse=True
            )

            # 集中度分析（上位10%のオブジェクトタイプが全体の何%を占めるか）
            top_10_percent_count = max(1, len(sorted_objects) // 10)
            top_objects_sum = sum(
                count for _, count in sorted_objects[:top_10_percent_count]
            )
            concentration_ratio = top_objects_sum / total_objects

            # オブジェクト成長分析
            growth_analysis = self._analyze_object_growth(snapshots)

            # オブジェクトダイバーシティ分析
            diversity_score = self._calculate_diversity_score(latest.object_counts)

            return {
                "total_object_count": total_objects,
                "object_type_diversity": len(latest.object_counts),
                "top_object_types": sorted_objects[:10],
                "concentration_ratio": concentration_ratio,
                "diversity_score": diversity_score,
                "distribution_balance": self._get_distribution_balance(
                    concentration_ratio
                ),
                "object_growth_analysis": growth_analysis,
            }

        except Exception as e:
            logger.error(f"オブジェクト分布分析エラー: {str(e)}")
            return {}

    def analyze_memory_patterns(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """メモリパターン分析"""
        try:
            if len(snapshots) < 5:
                return {}

            # メモリ使用パターンの識別
            memory_values = [s.process_memory_mb for s in snapshots]

            patterns = {
                "steady_growth": self._detect_steady_growth(memory_values),
                "periodic_spikes": self._detect_periodic_spikes(memory_values),
                "memory_leaks": self._detect_potential_leaks(snapshots),
                "gc_effectiveness": self._analyze_gc_effectiveness(snapshots),
            }

            return patterns

        except Exception as e:
            logger.error(f"メモリパターン分析エラー: {str(e)}")
            return {}

    def _calculate_volatility(self, values: List[float]) -> float:
        """変動性を計算します"""
        try:
            if len(values) < 2:
                return 0.0

            mean_value = sum(values) / len(values)
            variance = sum((v - mean_value) ** 2 for v in values) / len(values)
            volatility = (variance**0.5) / mean_value if mean_value > 0 else 0

            return volatility

        except Exception as e:
            logger.error(f"変動性計算エラー: {str(e)}")
            return 0.0

    def _get_fragmentation_severity(self, avg_fragmentation: float) -> str:
        """断片化深刻度を取得します"""
        try:
            if avg_fragmentation > 0.7:
                return "critical"
            elif avg_fragmentation > 0.5:
                return "high"
            elif avg_fragmentation > 0.3:
                return "moderate"
            elif avg_fragmentation > 0.1:
                return "low"
            else:
                return "minimal"

        except Exception as e:
            logger.error(f"断片化深刻度取得エラー: {str(e)}")
            return "unknown"

    def _analyze_object_growth(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """オブジェクト成長分析"""
        try:
            if len(snapshots) < 2:
                return {}

            first_snapshot = snapshots[0]
            last_snapshot = snapshots[-1]

            growing_types = []
            shrinking_types = []

            # 共通オブジェクトタイプの成長を分析
            common_types = set(first_snapshot.object_counts.keys()) & set(
                last_snapshot.object_counts.keys()
            )

            for obj_type in common_types:
                initial_count = first_snapshot.object_counts[obj_type]
                final_count = last_snapshot.object_counts[obj_type]

                if initial_count > 0:
                    growth_rate = (final_count - initial_count) / initial_count

                    if growth_rate > 0.1:  # 10%以上の増加
                        growing_types.append((obj_type, growth_rate))
                    elif growth_rate < -0.1:  # 10%以上の減少
                        shrinking_types.append((obj_type, growth_rate))

            return {
                "growing_object_types": sorted(
                    growing_types, key=lambda x: x[1], reverse=True
                )[:5],
                "shrinking_object_types": sorted(shrinking_types, key=lambda x: x[1])[
                    :5
                ],
                "net_growth_types": len(growing_types) - len(shrinking_types),
            }

        except Exception as e:
            logger.error(f"オブジェクト成長分析エラー: {str(e)}")
            return {}

    def _calculate_diversity_score(self, object_counts: Dict[str, int]) -> float:
        """オブジェクトダイバーシティスコアを計算します（Shannon entropy）"""
        try:
            if not object_counts:
                return 0.0

            total_objects = sum(object_counts.values())
            if total_objects == 0:
                return 0.0

            # Shannon entropy計算
            entropy = 0.0
            for count in object_counts.values():
                if count > 0:
                    probability = count / total_objects
                    entropy -= probability * (probability**0.5).bit_length()

            # 正規化（0-1スケール）
            max_entropy = (
                (len(object_counts) ** 0.5).bit_length() if object_counts else 0
            )
            diversity_score = entropy / max_entropy if max_entropy > 0 else 0

            return min(diversity_score, 1.0)

        except Exception as e:
            logger.error(f"ダイバーシティスコア計算エラー: {str(e)}")
            return 0.0

    def _get_distribution_balance(self, concentration_ratio: float) -> str:
        """分布バランスを取得します"""
        try:
            if concentration_ratio > 0.8:
                return "highly_concentrated"
            elif concentration_ratio > 0.6:
                return "concentrated"
            elif concentration_ratio > 0.4:
                return "balanced"
            elif concentration_ratio > 0.2:
                return "distributed"
            else:
                return "highly_distributed"

        except Exception as e:
            logger.error(f"分布バランス取得エラー: {str(e)}")
            return "unknown"

    def _detect_steady_growth(self, memory_values: List[float]) -> bool:
        """継続的な成長パターンを検出します"""
        try:
            if len(memory_values) < 5:
                return False

            # 最近の値が初期の値より継続的に大きいかチェック
            recent_avg = sum(memory_values[-3:]) / 3
            initial_avg = sum(memory_values[:3]) / 3

            growth_ratio = (
                (recent_avg - initial_avg) / initial_avg if initial_avg > 0 else 0
            )

            return growth_ratio > 0.1  # 10%以上の成長

        except Exception as e:
            logger.error(f"継続成長検出エラー: {str(e)}")
            return False

    def _detect_periodic_spikes(self, memory_values: List[float]) -> bool:
        """周期的なスパイクを検出します"""
        try:
            if len(memory_values) < 10:
                return False

            # 簡単なピーク検出
            peaks = 0
            for i in range(1, len(memory_values) - 1):
                if (
                    memory_values[i] > memory_values[i - 1]
                    and memory_values[i] > memory_values[i + 1]
                ):
                    peaks += 1

            # ピーク頻度が高いか判定
            peak_frequency = peaks / len(memory_values)
            return peak_frequency > 0.1  # 10%以上の頻度でピーク

        except Exception as e:
            logger.error(f"周期的スパイク検出エラー: {str(e)}")
            return False

    def _detect_potential_leaks(self, snapshots: List[MemorySnapshot]) -> List[str]:
        """潜在的リークを検出します"""
        try:
            potential_leaks: List[str] = []

            if len(snapshots) < 5:
                return potential_leaks

            # 一貫して増加しているオブジェクトタイプを探す
            for obj_type in set().union(*[s.object_counts.keys() for s in snapshots]):
                counts = [s.object_counts.get(obj_type, 0) for s in snapshots]

                if len(counts) >= 5:
                    # 単調増加パターンをチェック
                    increasing_trend = all(
                        counts[i] <= counts[i + 1] for i in range(len(counts) - 1)
                    )

                    if (
                        increasing_trend and counts[-1] > counts[0] * 1.5
                    ):  # 50%以上の増加
                        potential_leaks.append(obj_type)

            return potential_leaks[:10]  # 上位10個

        except Exception as e:
            logger.error(f"潜在的リーク検出エラー: {str(e)}")
            return []

    def _analyze_gc_effectiveness(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """ガベージコレクション効果分析"""
        try:
            if not snapshots:
                return {}

            # GC統計の分析
            gc_collections = []
            for snapshot in snapshots:
                if snapshot.gc_stats:
                    total_collections = sum(
                        stat.get("collections", 0)
                        for stat in snapshot.gc_stats
                        if isinstance(stat, dict)
                    )
                    gc_collections.append(total_collections)

            if len(gc_collections) < 2:
                return {}

            gc_frequency = (gc_collections[-1] - gc_collections[0]) / len(
                gc_collections
            )

            return {
                "gc_frequency": gc_frequency,
                "total_collections": gc_collections[-1] if gc_collections else 0,
                "gc_effectiveness": "high" if gc_frequency < 10 else "low",
            }

        except Exception as e:
            logger.error(f"GC効果分析エラー: {str(e)}")
            return {}
