"""メモリプロファイリングレポート生成"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger
from ..config import ProfilerConfig
from ..snapshot import MemorySnapshot

logger = get_logger(__name__)


class MemoryReportGenerator:
    """
    メモリプロファイリングレポート生成クラス

    プロファイリング結果から詳細なレポートを生成します。
    """

    def __init__(self, config: Optional[ProfilerConfig] = None) -> None:
        """
        レポート生成器を初期化します。

        Args:
            config: プロファイラー設定
        """
        try:
            self._config = config or ProfilerConfig()
            logger.info("MemoryReportGenerator初期化完了")

        except Exception as e:
            logger.error(f"MemoryReportGenerator初期化エラー: {str(e)}")
            raise

    def generate_profiling_report(
        self,
        snapshots: List[MemorySnapshot],
        leak_history: Optional[Dict[str, List[float]]] = None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        プロファイリングレポートを生成します。

        Args:
            snapshots: メモリスナップショットリスト
            leak_history: リーク履歴データ
            output_path: 出力パス（オプション）

        Returns:
            生成されたレポートファイルパス
        """
        try:
            os.makedirs("tmp", exist_ok=True)

            if not snapshots:
                logger.warning("スナップショットが存在しません")
                return None

            # レポートデータ作成
            latest_snapshot = snapshots[-1]
            report_data = {
                "profiling_summary": self._create_summary(snapshots),
                "memory_trend": self._create_trend_data(snapshots),
                "top_objects": latest_snapshot.top_objects,
                "object_counts": latest_snapshot.object_counts,
                "gc_statistics": latest_snapshot.gc_stats,
                "leak_detection": self._create_leak_data(leak_history or {}),
                "optimization_recommendations": self._generate_optimization_recommendations(
                    snapshots
                ),
            }

            # レポート出力
            if output_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_path = f"tmp/memory_profiling_report_{timestamp}.json"

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            logger.info(f"メモリプロファイリングレポート生成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"プロファイリングレポート生成エラー: {str(e)}")
            return None

    def _create_summary(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """プロファイリングサマリーを作成します。"""
        try:
            if not snapshots:
                return {}

            latest = snapshots[-1]
            memory_values = [s.process_memory_mb for s in snapshots]

            return {
                "total_snapshots": len(snapshots),
                "profiling_duration_seconds": (
                    latest.timestamp - snapshots[0].timestamp
                    if len(snapshots) > 1
                    else 0
                ),
                "current_memory_mb": latest.process_memory_mb,
                "peak_memory_mb": max(memory_values),
                "min_memory_mb": min(memory_values),
                "avg_memory_mb": sum(memory_values) / len(memory_values),
                "current_fragmentation": latest.fragmentation_ratio,
                "avg_fragmentation": sum(s.fragmentation_ratio for s in snapshots)
                / len(snapshots),
            }

        except Exception as e:
            logger.error(f"サマリー作成エラー: {str(e)}")
            return {}

    def _create_trend_data(
        self, snapshots: List[MemorySnapshot], limit: int = 50
    ) -> List[Dict[str, Any]]:
        """メモリトレンドデータを作成します。"""
        try:
            recent_snapshots = (
                snapshots[-limit:] if len(snapshots) > limit else snapshots
            )

            return [
                {
                    "timestamp": s.timestamp,
                    "memory_mb": s.process_memory_mb,
                    "virtual_memory_mb": s.virtual_memory_mb,
                    "memory_percent": s.memory_percent,
                    "fragmentation": s.fragmentation_ratio,
                    "object_count_total": (
                        sum(s.object_counts.values()) if s.object_counts else 0
                    ),
                }
                for s in recent_snapshots
            ]

        except Exception as e:
            logger.error(f"トレンドデータ作成エラー: {str(e)}")
            return []

    def _create_leak_data(self, leak_history: Dict[str, List[float]]) -> Dict[str, Any]:
        """リーク検出データを作成します。"""
        try:
            if not leak_history:
                return {}

            return {
                obj_type: {
                    "leak_rate_mb_per_sec": self._calculate_simple_leak_rate(history),
                    "history_length": len(history),
                    "total_growth": history[-1] - history[0] if len(history) > 1 else 0,
                    "max_count": max(history) if history else 0,
                }
                for obj_type, history in leak_history.items()
            }

        except Exception as e:
            logger.error(f"リークデータ作成エラー: {str(e)}")
            return {}

    def _calculate_simple_leak_rate(
        self, history: List[float], snapshot_interval: float = 1.0
    ) -> float:
        """シンプルなリーク率計算"""
        try:
            if len(history) < 2:
                return 0.0

            count_increase = history[-1] - history[0]
            time_span = len(history) * snapshot_interval
            estimated_size_mb = count_increase * 0.001  # 1KB仮定

            return estimated_size_mb / time_span

        except Exception as e:
            logger.error(f"リーク率計算エラー: {str(e)}")
            return 0.0

    def _generate_optimization_recommendations(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """最適化推奨事項を生成します。"""
        try:
            recommendations: List[str] = []

            if not snapshots:
                return recommendations

            latest = snapshots[-1]

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

            # メモリ使用量の傾向分析
            if len(snapshots) > 10:
                memory_values = [s.process_memory_mb for s in snapshots[-10:]]
                trend = self._analyze_memory_trend(memory_values)

                if trend == "increasing":
                    recommendations.append("メモリ使用量が継続的に増加しています")
                elif trend == "volatile":
                    recommendations.append("メモリ使用量が不安定です")

            # オブジェクト数チェック
            if latest.object_counts:
                large_object_types = [
                    obj_type
                    for obj_type, count in latest.object_counts.items()
                    if count > 10000
                ]
                if large_object_types:
                    recommendations.append(
                        f"大量のオブジェクトが検出されました: {', '.join(large_object_types)}"
                    )

            # GC効率チェック
            if latest.gc_stats and len(latest.gc_stats) > 0:
                total_collections = sum(
                    stat.get("collections", 0)
                    for stat in latest.gc_stats
                    if isinstance(stat, dict)
                )
                if total_collections > 1000:
                    recommendations.append(
                        "ガベージコレクションが頻繁に実行されています"
                    )

            return recommendations

        except Exception as e:
            logger.error(f"最適化推奨事項生成エラー: {str(e)}")
            return []

    def _analyze_memory_trend(self, values: List[float]) -> str:
        """メモリ使用量の傾向を分析します。"""
        try:
            if len(values) < 3:
                return "insufficient_data"

            # 線形回帰で傾向を判定
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n

            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return "stable"

            slope = numerator / denominator

            # 変動性チェック
            variance = sum((v - y_mean) ** 2 for v in values) / n
            cv = (variance**0.5) / y_mean if y_mean > 0 else 0

            if abs(slope) < 0.1 and cv < 0.1:
                return "stable"
            elif slope > 0.1:
                return "increasing"
            elif slope < -0.1:
                return "decreasing"
            elif cv > 0.2:
                return "volatile"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"傾向分析エラー: {str(e)}")
            return "unknown"

    def generate_summary_report(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """簡易サマリーレポートを生成します。"""
        try:
            if not snapshots:
                return {}

            latest = snapshots[-1]
            return {
                "current_memory_mb": latest.process_memory_mb,
                "virtual_memory_mb": latest.virtual_memory_mb,
                "memory_percent": latest.memory_percent,
                "fragmentation_ratio": latest.fragmentation_ratio,
                "object_count_total": (
                    sum(latest.object_counts.values()) if latest.object_counts else 0
                ),
                "top_object_types": (
                    sorted(
                        latest.object_counts.items(), key=lambda x: x[1], reverse=True
                    )[:10]
                    if latest.object_counts
                    else []
                ),
                "snapshots_taken": len(snapshots),
                "profiling_duration": (
                    latest.timestamp - snapshots[0].timestamp
                    if len(snapshots) > 1
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"サマリーレポート生成エラー: {str(e)}")
            return {}
