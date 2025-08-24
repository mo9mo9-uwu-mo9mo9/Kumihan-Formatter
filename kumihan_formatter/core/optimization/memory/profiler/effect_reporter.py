"""最適化効果レポーター"""

from __future__ import annotations

import json
import os
import time
from threading import Lock
from typing import Any, Dict, List, Optional, TYPE_CHECKING, cast

from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from .core_profiler import MemoryProfiler

logger = get_logger(__name__)


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
