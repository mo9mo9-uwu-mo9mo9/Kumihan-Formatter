"""
メモリレポート生成器 - メモリ分析レポート機能の独立クラス

MemoryAnalyzerから抽出されたレポート生成機能を専門的に扱う
Issue #476対応 - 300行制限による技術的負債削減
"""

import time
from typing import Any, Optional

from ..utilities.logger import get_logger
from .memory_types import MemoryLeak, MemorySnapshot


class MemoryReportGenerator:
    """メモリレポート生成専用クラス

    機能:
    - 包括的なメモリレポート生成
    - トレンド分析統合
    - メモリリーク分析
    - 推奨アクション生成
    """

    def __init__(self) -> None:
        """メモリレポート生成器を初期化"""
        self.logger = get_logger(__name__)

        # 統計
        self.stats = {
            "total_reports_generated": 0,
        }

        self.logger.info("メモリレポート生成器初期化完了")

    def generate_memory_report(
        self,
        snapshots: list[MemorySnapshot],
        leaks: Optional[list[MemoryLeak]] = None,
        include_trend: bool = True,
        trend_window_minutes: int = 30,
        trend_analysis: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """包括的なメモリレポートを生成

        Args:
            snapshots: メモリスナップショットリスト
            leaks: 検出されたメモリリーク（オプション）
            include_trend: トレンド分析を含めるか
            trend_window_minutes: トレンド分析のウィンドウ（分）
            trend_analysis: 事前計算されたトレンド分析結果（オプション）

        Returns:
            dict: メモリレポート
        """
        if not snapshots:
            return {"error": "No snapshots available for report"}

        current_snapshot = snapshots[-1]

        # 基本情報
        report = {
            "report_timestamp": time.time(),
            "report_time_human": time.strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot_count": len(snapshots),
            "monitoring_duration_hours": (
                ((snapshots[-1].timestamp - snapshots[0].timestamp) / 3600)
                if len(snapshots) > 1
                else 0
            ),
            # 現在の状況
            "current_memory": {
                "process_memory_mb": current_snapshot.memory_mb,
                "available_memory_mb": current_snapshot.available_mb,
                "memory_usage_ratio": current_snapshot.memory_usage_ratio,
                "gc_objects": current_snapshot.gc_objects,
                "gc_collections": current_snapshot.gc_collections,
                "custom_objects": current_snapshot.custom_objects,
                "is_warning": current_snapshot.is_memory_warning,
                "is_critical": current_snapshot.is_memory_critical,
            },
        }

        # トレンド分析（オプション）
        if include_trend and trend_analysis:
            report["trend_analysis"] = trend_analysis

        # メモリリーク情報（オプション）
        if leaks:
            leak_summary = self._generate_leak_summary(leaks)
            report["memory_leaks"] = leak_summary

        # 推奨アクション
        recommendations = self._generate_recommendations(
            current_snapshot, leaks, report
        )
        report["recommendations"] = recommendations

        # 統計更新
        self.stats["total_reports_generated"] += 1

        self.logger.info(
            f"メモリレポート生成完了 snapshot_count={len(snapshots)}, "
            f"current_memory_mb={current_snapshot.memory_mb:.1f}, "
            f"leak_count={len(leaks) if leaks else 0}"
        )

        return report

    def _generate_leak_summary(self, leaks: list[MemoryLeak]) -> dict[str, Any]:
        """メモリリーク情報のサマリーを生成

        Args:
            leaks: 検出されたメモリリークリスト

        Returns:
            dict: リーク情報サマリー
        """
        leaks_by_severity: dict[str, int] = {}
        top_leaks: list[dict[str, Any]] = []

        leak_summary = {
            "total_leaks": len(leaks),
            "critical_leaks": len([leak for leak in leaks if leak.is_critical_leak()]),
            "leaks_by_severity": leaks_by_severity,
            "top_leaks": top_leaks,
        }

        # 深刻度別分類
        for leak in leaks:
            severity = leak.severity
            if severity not in leaks_by_severity:
                leaks_by_severity[severity] = 0
            leaks_by_severity[severity] += 1

        # トップリーク（上位5つ）
        sorted_leaks = sorted(leaks, key=lambda x: x.count_increase, reverse=True)[:5]
        for leak in sorted_leaks:
            top_leaks.append(
                {
                    "object_type": leak.object_type,
                    "count_increase": leak.count_increase,
                    "size_estimate_mb": leak.size_estimate_mb,
                    "severity": leak.severity,
                    "age_hours": leak.age_seconds / 3600,
                }
            )

        return leak_summary

    def _generate_recommendations(
        self,
        current_snapshot: MemorySnapshot,
        leaks: Optional[list[MemoryLeak]],
        report: dict[str, Any],
    ) -> list[str]:
        """推奨アクションを生成

        Args:
            current_snapshot: 現在のメモリスナップショット
            leaks: 検出されたメモリリーク（オプション）
            report: 生成中のレポート

        Returns:
            list[str]: 推奨アクションリスト
        """
        recommendations = []

        # メモリ使用量チェック
        if current_snapshot.is_memory_critical:
            recommendations.append(
                "Critical: メモリ使用量が危険なレベルです。即座にガベージコレクションを実行してください。"
            )
        elif current_snapshot.is_memory_warning:
            recommendations.append(
                "Warning: メモリ使用量が警告レベルです。監視を強化してください。"
            )

        # メモリリークチェック
        if leaks and len([leak for leak in leaks if leak.is_critical_leak()]) > 0:
            recommendations.append(
                "Critical: クリティカルなメモリリークが検出されています。アプリケーションの再起動を検討してください。"
            )

        # トレンド分析チェック
        if "trend_analysis" in report:
            trend_data = report["trend_analysis"]
            if isinstance(trend_data, dict):
                memory_trend = trend_data.get("memory_trend", {})
                if isinstance(memory_trend, dict):
                    change_percent = memory_trend.get("change_percent", 0)
                    if isinstance(change_percent, (int, float)) and change_percent > 10:
                        recommendations.append(
                            "Warning: メモリ使用量が急速に増加しています。"
                        )

        return recommendations

    def get_stats(self) -> dict[str, Any]:
        """統計情報を取得

        Returns:
            dict: 統計情報
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """統計情報をリセット"""
        old_stats = self.stats.copy()
        self.stats = {
            "total_reports_generated": 0,
        }

        self.logger.info(f"レポート生成器統計情報をリセット old_stats={old_stats}")
