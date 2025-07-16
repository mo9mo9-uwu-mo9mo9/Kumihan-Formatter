"""
メモリ分析器 - 高度な分析とレポート機能

メモリ使用量の分析、トレンド解析、レポート生成を行う専用モジュール
Issue #402対応 - パフォーマンス最適化
"""

import gc
import time
from typing import Dict, List, Optional, Any, Callable

from .memory_types import MemorySnapshot, MemoryLeak, MEMORY_ALERT_THRESHOLDS, GC_OPTIMIZATION_THRESHOLDS
from ..utilities.logger import get_logger


class MemoryAnalyzer:
    """メモリ分析とレポート生成機能
    
    機能:
    - メモリトレンド分析
    - 包括的レポート生成
    - ガベージコレクション最適化
    - メモリアラート管理
    """

    def __init__(self):
        """メモリ分析器を初期化"""
        self.logger = get_logger(__name__)
        
        # アラート管理
        self.alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.last_alert_time: Dict[str, float] = {}
        self.alert_cooldown = 300.0  # 5分間のクールダウン
        
        # 統計
        self.stats = {
            "total_reports_generated": 0,
            "total_gc_forced": 0,
            "total_alerts_triggered": 0,
            "memory_optimizations": 0,
        }
        
        self.logger.info("メモリ分析器初期化完了")

    def register_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """アラートコールバックを登録

        Args:
            callback: アラート発生時に呼び出される関数
        """
        self.alert_callbacks.append(callback)
        self.logger.debug("アラートコールバック登録完了")

    def get_memory_trend(
        self, snapshots: List[MemorySnapshot], window_minutes: int = 30
    ) -> Dict[str, Any]:
        """メモリ使用量のトレンドを分析

        Args:
            snapshots: 分析対象のスナップショットリスト
            window_minutes: 分析ウィンドウ（分）

        Returns:
            Dict: トレンド分析結果
        """
        if not snapshots:
            return {"error": "No snapshots available"}

        current_time = time.time()
        window_seconds = window_minutes * 60
        cutoff_time = current_time - window_seconds

        # ウィンドウ内のスナップショットを抽出
        window_snapshots = [
            s for s in snapshots if s.timestamp >= cutoff_time
        ]

        if len(window_snapshots) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # トレンド計算
        memory_values = [s.memory_mb for s in window_snapshots]
        gc_object_values = [s.gc_objects for s in window_snapshots]
        
        start_memory = memory_values[0]
        end_memory = memory_values[-1]
        memory_change = end_memory - start_memory
        memory_change_percent = (memory_change / start_memory * 100) if start_memory > 0 else 0

        start_gc = gc_object_values[0]
        end_gc = gc_object_values[-1]
        gc_change = end_gc - start_gc

        # 統計
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        min_memory = min(memory_values)

        # 変化率の計算
        memory_slope = self._calculate_slope([s.timestamp for s in window_snapshots], memory_values)
        gc_slope = self._calculate_slope([s.timestamp for s in window_snapshots], gc_object_values)

        return {
            "window_minutes": window_minutes,
            "data_points": len(window_snapshots),
            "memory_trend": {
                "start_mb": start_memory,
                "end_mb": end_memory,
                "change_mb": memory_change,
                "change_percent": memory_change_percent,
                "slope_mb_per_hour": memory_slope * 3600,
                "average_mb": avg_memory,
                "max_mb": max_memory,
                "min_mb": min_memory,
            },
            "gc_objects_trend": {
                "start_count": start_gc,
                "end_count": end_gc,
                "change": gc_change,
                "slope_per_hour": gc_slope * 3600,
            },
            "is_increasing": memory_slope > 0,
            "growth_rate": "rapid" if abs(memory_change_percent) > 10 else "moderate" if abs(memory_change_percent) > 2 else "stable",
        }

    def _calculate_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """最小二乗法で傾きを計算

        Args:
            x_values: X軸の値（通常は時間）
            y_values: Y軸の値（メモリ使用量など）

        Returns:
            float: 傾き
        """
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def generate_memory_report(
        self, 
        snapshots: List[MemorySnapshot], 
        leaks: Optional[List[MemoryLeak]] = None,
        include_trend: bool = True,
        trend_window_minutes: int = 30
    ) -> Dict[str, Any]:
        """包括的なメモリレポートを生成

        Args:
            snapshots: メモリスナップショットリスト
            leaks: 検出されたメモリリーク（オプション）
            include_trend: トレンド分析を含めるか
            trend_window_minutes: トレンド分析のウィンドウ（分）

        Returns:
            Dict: メモリレポート
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
                (snapshots[-1].timestamp - snapshots[0].timestamp) / 3600
            ) if len(snapshots) > 1 else 0,
            
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
        if include_trend and len(snapshots) > 1:
            trend = self.get_memory_trend(snapshots, trend_window_minutes)
            report["trend_analysis"] = trend

        # メモリリーク情報（オプション）
        if leaks:
            leak_summary = {
                "total_leaks": len(leaks),
                "critical_leaks": len([l for l in leaks if l.is_critical_leak()]),
                "leaks_by_severity": {},
                "top_leaks": [],
            }
            
            # 深刻度別分類
            for leak in leaks:
                severity = leak.severity
                if severity not in leak_summary["leaks_by_severity"]:
                    leak_summary["leaks_by_severity"][severity] = 0
                leak_summary["leaks_by_severity"][severity] += 1
            
            # トップリーク（上位5つ）
            sorted_leaks = sorted(leaks, key=lambda x: x.count_increase, reverse=True)[:5]
            for leak in sorted_leaks:
                leak_summary["top_leaks"].append({
                    "object_type": leak.object_type,
                    "count_increase": leak.count_increase,
                    "size_estimate_mb": leak.size_estimate_mb,
                    "severity": leak.severity,
                    "age_hours": leak.age_seconds / 3600,
                })
            
            report["memory_leaks"] = leak_summary

        # 推奨アクション
        recommendations = []
        if current_snapshot.is_memory_critical:
            recommendations.append("Critical: メモリ使用量が危険なレベルです。即座にガベージコレクションを実行してください。")
        elif current_snapshot.is_memory_warning:
            recommendations.append("Warning: メモリ使用量が警告レベルです。監視を強化してください。")
        
        if leaks and len([l for l in leaks if l.is_critical_leak()]) > 0:
            recommendations.append("Critical: クリティカルなメモリリークが検出されています。アプリケーションの再起動を検討してください。")
        
        if include_trend and "trend_analysis" in report:
            trend_data = report["trend_analysis"]
            if trend_data.get("memory_trend", {}).get("change_percent", 0) > 10:
                recommendations.append("Warning: メモリ使用量が急速に増加しています。")

        report["recommendations"] = recommendations
        
        # 統計更新
        self.stats["total_reports_generated"] += 1
        
        self.logger.info(
            f"メモリレポート生成完了 snapshot_count={len(snapshots)}, "
            f"current_memory_mb={current_snapshot.memory_mb:.1f}, "
            f"leak_count={len(leaks) if leaks else 0}"
        )

        return report

    def force_garbage_collection(self) -> Dict[str, Any]:
        """ガベージコレクションを強制実行

        Returns:
            Dict: GC実行結果
        """
        start_time = time.time()
        
        # 実行前の状態
        before_objects = len(gc.get_objects())
        before_collections = gc.get_count()
        
        # GC実行
        collected_counts = []
        for generation in range(3):
            collected = gc.collect(generation)
            collected_counts.append(collected)
        
        # 実行後の状態
        after_objects = len(gc.get_objects())
        after_collections = gc.get_count()
        
        duration = time.time() - start_time
        
        result = {
            "duration_ms": duration * 1000,
            "before": {
                "objects": before_objects,
                "collections": before_collections,
            },
            "after": {
                "objects": after_objects,
                "collections": after_collections,
            },
            "collected_by_generation": collected_counts,
            "objects_freed": before_objects - after_objects,
            "total_collected": sum(collected_counts),
        }
        
        self.stats["total_gc_forced"] += 1
        
        self.logger.info(
            f"強制GC実行完了 duration_ms={result['duration_ms']:.2f}, "
            f"objects_freed={result['objects_freed']}, "
            f"total_collected={result['total_collected']}"
        )
        
        return result

    def optimize_memory_settings(self) -> Dict[str, Any]:
        """メモリ設定を最適化

        Returns:
            Dict: 最適化結果
        """
        old_thresholds = gc.get_threshold()
        
        # 最適化された閾値を設定
        new_thresholds = (
            GC_OPTIMIZATION_THRESHOLDS["generation_0"],
            GC_OPTIMIZATION_THRESHOLDS["generation_1"], 
            GC_OPTIMIZATION_THRESHOLDS["generation_2"],
        )
        
        gc.set_threshold(*new_thresholds)
        
        # 設定確認
        current_thresholds = gc.get_threshold()
        
        result = {
            "old_thresholds": old_thresholds,
            "new_thresholds": current_thresholds,
            "optimization_applied": current_thresholds == new_thresholds,
        }
        
        self.stats["memory_optimizations"] += 1
        
        self.logger.info(
            f"メモリ設定最適化完了 old_thresholds={old_thresholds}, "
            f"new_thresholds={current_thresholds}"
        )
        
        return result

    def check_memory_alerts(self, snapshot: MemorySnapshot) -> None:
        """メモリアラートをチェック

        Args:
            snapshot: チェック対象のスナップショット
        """
        current_time = time.time()
        
        # 警告レベルチェック
        if snapshot.is_memory_warning:
            alert_type = "memory_warning"
            if self._can_trigger_alert(alert_type, current_time):
                self._trigger_alert(
                    alert_type,
                    {
                        "memory_usage_ratio": snapshot.memory_usage_ratio,
                        "memory_mb": snapshot.memory_mb,
                        "available_mb": snapshot.available_mb,
                        "threshold": MEMORY_ALERT_THRESHOLDS["warning"],
                    }
                )
        
        # クリティカルレベルチェック
        if snapshot.is_memory_critical:
            alert_type = "memory_critical"
            if self._can_trigger_alert(alert_type, current_time):
                self._trigger_alert(
                    alert_type,
                    {
                        "memory_usage_ratio": snapshot.memory_usage_ratio,
                        "memory_mb": snapshot.memory_mb,
                        "available_mb": snapshot.available_mb,
                        "threshold": MEMORY_ALERT_THRESHOLDS["critical"],
                    }
                )

    def check_memory_alerts_batch(self, snapshots: List[MemorySnapshot]) -> None:
        """複数のスナップショットに対してアラートをチェック

        Args:
            snapshots: チェック対象のスナップショットリスト
        """
        for snapshot in snapshots:
            self.check_memory_alerts(snapshot)

    def _can_trigger_alert(self, alert_type: str, current_time: float) -> bool:
        """アラートを発火できるかチェック（クールダウン考慮）

        Args:
            alert_type: アラートタイプ
            current_time: 現在時刻

        Returns:
            bool: アラート発火可能かどうか
        """
        last_time = self.last_alert_time.get(alert_type, 0)
        return current_time - last_time >= self.alert_cooldown

    def _trigger_alert(self, alert_type: str, context: Dict[str, Any]) -> None:
        """アラートを発火

        Args:
            alert_type: アラートタイプ
            context: アラートコンテキスト
        """
        current_time = time.time()
        self.last_alert_time[alert_type] = current_time
        
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self.logger.warning(
            f"メモリアラート発火: {alert_type} {context_str}"
        )
        
        # 登録されたコールバックを実行
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, context)
            except Exception as e:
                self.logger.error(f"アラートコールバック実行エラー: {e}")
        
        self.stats["total_alerts_triggered"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得

        Returns:
            Dict: 統計情報
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """統計情報をリセット"""
        old_stats = self.stats.copy()
        self.stats = {
            "total_reports_generated": 0,
            "total_gc_forced": 0,
            "total_alerts_triggered": 0,
            "memory_optimizations": 0,
        }
        
        self.logger.info(f"統計情報をリセット old_stats={old_stats}")