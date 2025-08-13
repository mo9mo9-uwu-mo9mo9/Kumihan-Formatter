#!/usr/bin/env python3
"""
Efficiency Tracking System
効率性メトリクス追跡システム - タスクキュー処理効率の定量的監視
"""

import json
import datetime
import os
import statistics
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class EfficiencyLevel(Enum):
    """効率レベル"""
    EXCELLENT = "excellent"     # 優秀（90%以上）
    GOOD = "good"              # 良好（70-89%）
    ACCEPTABLE = "acceptable"   # 許容（50-69%）
    POOR = "poor"              # 不良（30-49%）
    CRITICAL = "critical"       # 重大（30%未満）


@dataclass
class TaskExecutionMetrics:
    """タスク実行メトリクス"""
    task_id: str
    execution_timestamp: str
    execution_time_seconds: float
    errors_before: int
    errors_after: int
    errors_fixed: int
    success_rate: float
    quality_score: float
    token_usage: int
    cost_estimate: float
    ai_agent: str  # claude, gemini
    task_type: str
    file_count: int


@dataclass
class QueueEfficiencySnapshot:
    """キュー効率性スナップショット"""
    timestamp: str
    queue_size: int
    pending_tasks: int
    processing_rate: float  # タスク/時間
    error_fix_rate: float   # 修正成功率
    duplicate_rate: float   # 重複タスク率
    avg_processing_time: float  # 平均処理時間（秒）
    quality_approval_rate: float    # 品質承認率
    token_efficiency: float # トークン効率（修正件数/Token数）
    cost_efficiency: float  # コスト効率（修正件数/コスト）


@dataclass
class EfficiencyTrend:
    """効率性トレンド"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str    # improving, degrading, stable
    trend_strength: str     # strong, moderate, weak


@dataclass
class EfficiencyReport:
    """効率性レポート"""
    report_timestamp: str
    monitoring_period_hours: float
    current_snapshot: QueueEfficiencySnapshot
    efficiency_trends: List[EfficiencyTrend]
    performance_goals: Dict[str, Any]
    achievement_status: Dict[str, bool]
    recommendations: List[str]
    alert_level: EfficiencyLevel


class EfficiencyTracker:
    """効率性メトリクス追跡システム"""

    def __init__(self) -> None:
        # データ保存パス
        self.metrics_history_path = Path("postbox/monitoring/efficiency_metrics.json")
        self.snapshots_path = Path("postbox/monitoring/efficiency_snapshots.json")
        self.reports_path = Path("postbox/monitoring/efficiency_reports.json")

        # ディレクトリ作成
        for path in [self.metrics_history_path, self.snapshots_path, self.reports_path]:
            path.parent.mkdir(parents=True, exist_ok=True)

        # パフォーマンス目標（Issue #858要件）
        self.performance_goals = {
            "error_fix_rate": 0.60,      # 60%以上
            "queue_size_target": 10,      # 10件以下
            "processing_time_target": 2.0,   # 2秒以下
            "quality_approval_rate": 0.70,   # 70%以上
            "duplicate_rate_max": 0.20,       # 20%以下
            "token_efficiency_min": 0.01,     # 0.01以上（修正/Token）
            "cost_efficiency_min": 10.0       # 10以上（修正/ドル）
        }

        # メトリクス履歴ロード
        self.metrics_history = self._load_metrics_history()
        self.snapshots_history = self._load_snapshots_history()

        # アラート設定
        self.alert_settings = {
            "queue_size_alert_threshold": 20,      # キューサイズ警告閾値
            "error_fix_rate_alert_threshold": 0.3,  # エラー修正率警告閾値
            "processing_time_alert_threshold": 5.0, # 処理時間警告閾値（秒）
            "alert_enabled": True                   # アラート有効フラグ
        }

        print("📊 EfficiencyTracker 初期化完了")

    def record_task_execution(self, task_metrics: TaskExecutionMetrics) -> None:
        """タスク実行メトリクスを記録"""

        print(f"📝 タスクメトリクス記録: {task_metrics.task_id}")

        # メトリクス履歴に追加
        self.metrics_history.append(asdict(task_metrics))

        # 履歴保存
        self._save_metrics_history()

        # リアルタイム分析（必要に応じて）
        self._update_realtime_metrics(task_metrics)

    def capture_queue_snapshot(self, queue_tasks: List[Dict[str, Any]]) -> QueueEfficiencySnapshot:
        """キュー状態スナップショット取得"""

        print(f"📸 キュースナップショット取得: {len(queue_tasks)}タスク")

        # 基本統計計算
        queue_size = len(queue_tasks)
        pending_tasks = sum(1 for task in queue_tasks if task.get("status", "pending") == "pending")

        # 最近の実行データから効率性指標を計算
        recent_metrics = self._get_recent_metrics(hours=24)

        # 処理レート計算（タスク/時間）
        processing_rate = self._calculate_processing_rate(recent_metrics)

        # エラー修正率計算
        error_fix_rate = self._calculate_error_fix_rate(recent_metrics)

        # 重複率計算（キューから）
        duplicate_rate = self._calculate_duplicate_rate(queue_tasks)

        # 平均処理時間計算
        avg_processing_time = self._calculate_avg_processing_time(recent_metrics)

        # 品質承認率計算
        quality_approval_rate = self._calculate_quality_approval_rate(recent_metrics)

        # Token・コスト効率計算
        token_efficiency = self._calculate_token_efficiency(recent_metrics)
        cost_efficiency = self._calculate_cost_efficiency(recent_metrics)

        snapshot = QueueEfficiencySnapshot(
            timestamp=datetime.datetime.now().isoformat(),
            queue_size=queue_size,
            pending_tasks=pending_tasks,
            processing_rate=processing_rate,
            error_fix_rate=error_fix_rate,
            duplicate_rate=duplicate_rate,
            avg_processing_time=avg_processing_time,
            quality_approval_rate=quality_approval_rate,
            token_efficiency=token_efficiency,
            cost_efficiency=cost_efficiency
        )

        # スナップショット履歴に追加
        self.snapshots_history.append(asdict(snapshot))
        self._save_snapshots_history()

        # アラートチェック
        alerts = self.check_and_send_alerts(snapshot)
        if alerts:
            print(f"🚨 {len(alerts)}件のアラートが発生しました")

        return snapshot

    def analyze_efficiency_trends(self, analysis_period_hours: float = 168) -> List[EfficiencyTrend]:
        """効率性トレンド分析（デフォルト1週間）"""

        print(f"📈 効率性トレンド分析: {analysis_period_hours}時間")

        # 分析対象期間のスナップショット取得
        current_time = datetime.datetime.now()
        cutoff_time = current_time - datetime.timedelta(hours=analysis_period_hours)

        relevant_snapshots = [
            snap for snap in self.snapshots_history
            if datetime.datetime.fromisoformat(snap["timestamp"]) >= cutoff_time
        ]

        if len(relevant_snapshots) < 2:
            print("⚠️ 分析に必要な履歴データが不足")
            return []

        # トレンド分析対象メトリクス
        metrics_to_analyze = [
            "error_fix_rate",
            "processing_rate",
            "duplicate_rate",
            "avg_processing_time",
            "quality_approval_rate",
            "token_efficiency",
            "cost_efficiency"
        ]

        trends = []

        for metric_name in metrics_to_analyze:
            trend = self._analyze_metric_trend(relevant_snapshots, metric_name)
            if trend:
                trends.append(trend)

        return trends

    def generate_efficiency_report(self, queue_tasks: List[Dict[str, Any]],
                                 monitoring_period_hours: float = 24) -> EfficiencyReport:
        """効率性レポート生成"""

        print(f"📋 効率性レポート生成: {monitoring_period_hours}時間分析")

        # 現在のキュースナップショット
        current_snapshot = self.capture_queue_snapshot(queue_tasks)

        # トレンド分析
        efficiency_trends = self.analyze_efficiency_trends(monitoring_period_hours)

        # 目標達成状況
        achievement_status = self._evaluate_goal_achievement(current_snapshot)

        # 推奨事項生成
        recommendations = self._generate_recommendations(current_snapshot, efficiency_trends, achievement_status)

        # アラートレベル決定
        alert_level = self._determine_alert_level(current_snapshot, achievement_status)

        report = EfficiencyReport(
            report_timestamp=datetime.datetime.now().isoformat(),
            monitoring_period_hours=monitoring_period_hours,
            current_snapshot=current_snapshot,
            efficiency_trends=efficiency_trends,
            performance_goals=self.performance_goals,
            achievement_status=achievement_status,
            recommendations=recommendations,
            alert_level=alert_level
        )

        # レポート保存
        self._save_efficiency_report(report)

        return report

    def _get_recent_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """指定時間内の最近のメトリクス取得"""

        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)

        recent_metrics = []
        for metric in self.metrics_history:
            try:
                metric_time = datetime.datetime.fromisoformat(metric["execution_timestamp"])
                if metric_time >= cutoff_time:
                    recent_metrics.append(metric)
            except (ValueError, KeyError):
                continue

        return recent_metrics

    def _calculate_processing_rate(self, metrics: List[Dict[str, Any]]) -> float:
        """処理レート計算（タスク/時間）"""

        if not metrics:
            return 0.0

        # 時間範囲計算
        timestamps = [datetime.datetime.fromisoformat(m["execution_timestamp"]) for m in metrics]
        if len(timestamps) < 2:
            return len(metrics)  # 1時間以内として扱う

        time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600
        if time_span_hours == 0:
            return len(metrics)

        return len(metrics) / time_span_hours

    def _calculate_error_fix_rate(self, metrics: List[Dict[str, Any]]) -> float:
        """エラー修正率計算"""

        if not metrics:
            return 0.0

        total_tasks = len(metrics)
        successful_fixes = sum(1 for m in metrics if m.get("errors_fixed", 0) > 0)

        return successful_fixes / total_tasks if total_tasks > 0 else 0.0

    def _calculate_duplicate_rate(self, queue_tasks: List[Dict[str, Any]]) -> float:
        """重複率計算（簡易版）"""

        if len(queue_tasks) < 2:
            return 0.0

        # ファイル・エラータイプの組み合わせで重複判定
        task_signatures = set()
        duplicates = 0

        for task in queue_tasks:
            target_files = tuple(sorted(task.get("target_files", [])))
            error_type = task.get("requirements", {}).get("error_type", "")
            signature = (target_files, error_type)

            if signature in task_signatures:
                duplicates += 1
            else:
                task_signatures.add(signature)

        return duplicates / len(queue_tasks) if queue_tasks else 0.0

    def _calculate_avg_processing_time(self, metrics: List[Dict[str, Any]]) -> float:
        """平均処理時間計算"""

        if not metrics:
            return 0.0

        processing_times = [m.get("execution_time_seconds", 0.0) for m in metrics]
        return statistics.mean(processing_times) if processing_times else 0.0

    def _calculate_quality_approval_rate(self, metrics: List[Dict[str, Any]]) -> float:
        """品質承認率計算"""

        if not metrics:
            return 0.0

        quality_scores = [m.get("quality_score", 0.0) for m in metrics]
        approved = sum(1 for score in quality_scores if score >= 0.7)  # 70%以上を承認と判定

        return approved / len(quality_scores) if quality_scores else 0.0

    def _calculate_token_efficiency(self, metrics: List[Dict[str, Any]]) -> float:
        """Token効率計算（修正件数/Token数）"""

        if not metrics:
            return 0.0

        total_fixes = sum(m.get("errors_fixed", 0) for m in metrics)
        total_tokens = sum(m.get("token_usage", 0) for m in metrics)

        return total_fixes / total_tokens if total_tokens > 0 else 0.0

    def _calculate_cost_efficiency(self, metrics: List[Dict[str, Any]]) -> float:
        """コスト効率計算（修正件数/コスト）"""

        if not metrics:
            return 0.0

        total_fixes = sum(m.get("errors_fixed", 0) for m in metrics)
        total_cost = sum(m.get("cost_estimate", 0.0) for m in metrics)

        return total_fixes / total_cost if total_cost > 0 else 0.0

    def _analyze_metric_trend(self, snapshots: List[Dict[str, Any]], metric_name: str) -> Optional[EfficiencyTrend]:
        """メトリクストレンド分析"""

        values = [snap.get(metric_name, 0) for snap in snapshots]

        if len(values) < 2:
            return None

        # 直近と初期の値を比較
        current_value = values[-1]
        previous_value = values[0]

        if previous_value == 0:
            change_percentage = 100.0 if current_value > 0 else 0.0
        else:
            change_percentage = ((current_value - previous_value) / previous_value) * 100

        # トレンド方向決定
        if abs(change_percentage) < 5:
            trend_direction = "stable"
        elif change_percentage > 0:
            # メトリクスによって改善/悪化の判定が逆転
            if metric_name in ["duplicate_rate", "avg_processing_time"]:
                trend_direction = "degrading"  # これらは下がる方が良い
            else:
                trend_direction = "improving"  # これらは上がる方が良い
        else:
            if metric_name in ["duplicate_rate", "avg_processing_time"]:
                trend_direction = "improving"
            else:
                trend_direction = "degrading"

        # トレンド強度
        abs_change = abs(change_percentage)
        if abs_change > 20:
            trend_strength = "strong"
        elif abs_change > 10:
            trend_strength = "moderate"
        else:
            trend_strength = "weak"

        return EfficiencyTrend(
            metric_name=metric_name,
            current_value=current_value,
            previous_value=previous_value,
            change_percentage=change_percentage,
            trend_direction=trend_direction,
            trend_strength=trend_strength
        )

    def _evaluate_goal_achievement(self, snapshot: QueueEfficiencySnapshot) -> Dict[str, bool]:
        """目標達成状況評価"""

        achievement_status = {}

        # 各目標の達成状況確認
        achievement_status["error_fix_rate"] = snapshot.error_fix_rate >= self.performance_goals["error_fix_rate"]
        achievement_status["queue_size"] = snapshot.queue_size <= self.performance_goals["queue_size_target"]
        achievement_status["processing_time"] = snapshot.avg_processing_time <= self.performance_goals["processing_time_target"]
        achievement_status["quality_approval_rate"] = snapshot.quality_approval_rate >= self.performance_goals["quality_approval_rate"]
        achievement_status["duplicate_rate"] = snapshot.duplicate_rate <= self.performance_goals["duplicate_rate_max"]
        achievement_status["token_efficiency"] = snapshot.token_efficiency >= self.performance_goals["token_efficiency_min"]
        achievement_status["cost_efficiency"] = snapshot.cost_efficiency >= self.performance_goals["cost_efficiency_min"]

        return achievement_status

    def _generate_recommendations(self, snapshot: QueueEfficiencySnapshot,
                                trends: List[EfficiencyTrend],
                                achievement_status: Dict[str, bool]) -> List[str]:
        """推奨事項生成"""

        recommendations = []

        # 目標未達成項目への対応
        if not achievement_status.get("error_fix_rate", True):
            recommendations.append(f"エラー修正率が目標未達成（現在: {snapshot.error_fix_rate:.1%}、目標: {self.performance_goals['error_fix_rate']:.1%}）")
            recommendations.append("- タスク事前検証システムの導入を検討")
            recommendations.append("- 修正困難なタスクの手動対応への移行")

        if not achievement_status.get("queue_size", True):
            recommendations.append(f"キューサイズが目標を超過（現在: {snapshot.queue_size}件、目標: {self.performance_goals['queue_size_target']}件）")
            recommendations.append("- 重複タスク排除の実施")
            recommendations.append("- タスク優先度の再評価")

        if not achievement_status.get("duplicate_rate", True):
            recommendations.append(f"重複率が高い（現在: {snapshot.duplicate_rate:.1%}、上限: {self.performance_goals['duplicate_rate_max']:.1%}）")
            recommendations.append("- TaskDeduplicatorの活用")

        if not achievement_status.get("quality_approval_rate", True):
            recommendations.append(f"品質承認率が低い（現在: {snapshot.quality_approval_rate:.1%}、目標: {self.performance_goals['quality_approval_rate']:.1%}）")
            recommendations.append("- 品質チェック基準の見直し")
            recommendations.append("- AI修正精度の向上策検討")

        # トレンドに基づく推奨事項
        for trend in trends:
            if trend.trend_direction == "degrading" and trend.trend_strength in ["strong", "moderate"]:
                recommendations.append(f"{trend.metric_name}が悪化傾向（{trend.change_percentage:.1f}%変化）")

        # 全般的な推奨事項
        if len([status for status in achievement_status.values() if not status]) >= 3:
            recommendations.append("複数指標で目標未達成 - システム全体の見直しが必要")

        return recommendations

    def _determine_alert_level(self, snapshot: QueueEfficiencySnapshot,
                             achievement_status: Dict[str, bool]) -> EfficiencyLevel:
        """アラートレベル決定"""

        # 達成している目標の数
        achieved_goals = sum(achievement_status.values())
        total_goals = len(achievement_status)
        achievement_rate = achieved_goals / total_goals

        # アラートレベル決定
        if achievement_rate >= 0.90:
            return EfficiencyLevel.EXCELLENT
        elif achievement_rate >= 0.70:
            return EfficiencyLevel.GOOD
        elif achievement_rate >= 0.50:
            return EfficiencyLevel.ACCEPTABLE
        elif achievement_rate >= 0.30:
            return EfficiencyLevel.POOR
        else:
            return EfficiencyLevel.CRITICAL

    def _update_realtime_metrics(self, metrics: TaskExecutionMetrics) -> None:
        """リアルタイムメトリクス更新"""

        # リアルタイム統計ファイルの更新
        realtime_path = Path("postbox/monitoring/realtime_efficiency.json")

        realtime_data = {
            "last_update": datetime.datetime.now().isoformat(),
            "recent_task": {
                "task_id": metrics.task_id,
                "success": metrics.errors_fixed > 0,
                "processing_time": metrics.execution_time_seconds,
                "quality_score": metrics.quality_score,
                "ai_agent": metrics.ai_agent
            }
        }

        with open(realtime_path, 'w', encoding='utf-8') as f:
            json.dump(realtime_data, f, indent=2, ensure_ascii=False)

    def _load_metrics_history(self) -> List[Dict[str, Any]]:
        """メトリクス履歴ロード"""

        if self.metrics_history_path.exists():
            try:
                with open(self.metrics_history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ メトリクス履歴読み込みエラー: {e}")
                return []
        return []

    def _load_snapshots_history(self) -> List[Dict[str, Any]]:
        """スナップショット履歴ロード"""

        if self.snapshots_path.exists():
            try:
                with open(self.snapshots_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ スナップショット履歴読み込みエラー: {e}")
                return []
        return []

    def _save_metrics_history(self) -> None:
        """メトリクス履歴保存"""

        # 過去30日分のみ保持
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=30)

        filtered_history = []
        for metric in self.metrics_history:
            try:
                metric_time = datetime.datetime.fromisoformat(metric["execution_timestamp"])
                if metric_time >= cutoff_time:
                    filtered_history.append(metric)
            except (ValueError, KeyError):
                continue

        self.metrics_history = filtered_history

        with open(self.metrics_history_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics_history, f, indent=2, ensure_ascii=False)

    def _save_snapshots_history(self) -> None:
        """スナップショット履歴保存"""

        # 過去30日分のみ保持
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=30)

        filtered_history = []
        for snapshot in self.snapshots_history:
            try:
                snapshot_time = datetime.datetime.fromisoformat(snapshot["timestamp"])
                if snapshot_time >= cutoff_time:
                    filtered_history.append(snapshot)
            except (ValueError, KeyError):
                continue

        self.snapshots_history = filtered_history

        with open(self.snapshots_path, 'w', encoding='utf-8') as f:
            json.dump(self.snapshots_history, f, indent=2, ensure_ascii=False)

    def _save_efficiency_report(self, report: EfficiencyReport) -> None:
        """効率性レポート保存"""

        # 既存レポート読み込み
        reports = []
        if self.reports_path.exists():
            try:
                with open(self.reports_path, 'r', encoding='utf-8') as f:
                    reports = json.load(f)
            except Exception:
                reports = []

        # 新しいレポート追加（Enumを文字列に変換）
        report_dict = asdict(report)
        self._convert_enums_to_strings(report_dict)
        reports.append(report_dict)

        # 過去30件のみ保持
        reports = reports[-30:]

        with open(self.reports_path, 'w', encoding='utf-8') as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)

    def _convert_enums_to_strings(self, data: Any) -> None:
        """EnumをJSON用に文字列に変換"""
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(value, 'value'):  # Enumの場合
                    data[key] = value.value
                elif isinstance(value, (dict, list)):
                    self._convert_enums_to_strings(value)
        elif isinstance(data, list):
            for item in data:
                self._convert_enums_to_strings(item)

    def create_efficiency_dashboard_data(self) -> Dict[str, Any]:
        """効率性ダッシュボード用データ生成"""

        # 最新の統計
        recent_metrics = self._get_recent_metrics(24)
        recent_snapshots = self.snapshots_history[-10:] if self.snapshots_history else []

        dashboard_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_tasks_processed": len(self.metrics_history),
                "recent_tasks_24h": len(recent_metrics),
                "current_queue_size": recent_snapshots[-1]["queue_size"] if recent_snapshots else 0,
                "avg_error_fix_rate": self._calculate_error_fix_rate(recent_metrics),
                "avg_quality_score": statistics.mean([m.get("quality_score", 0) for m in recent_metrics]) if recent_metrics else 0
            },
            "charts": {
                "error_fix_rate_trend": [snap.get("error_fix_rate", 0) for snap in recent_snapshots],
                "queue_size_trend": [snap.get("queue_size", 0) for snap in recent_snapshots],
                "processing_time_trend": [snap.get("avg_processing_time", 0) for snap in recent_snapshots],
                "quality_approval_trend": [snap.get("quality_approval_rate", 0) for snap in recent_snapshots]
            },
            "performance_goals": self.performance_goals
        }

        return dashboard_data

    def save_dashboard_data(self, output_path: str = "tmp/efficiency_dashboard.json") -> str:
        """ダッシュボードデータ保存"""

        # 出力ディレクトリ作成
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        dashboard_data = self.create_efficiency_dashboard_data()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

        print(f"📊 ダッシュボードデータ保存: {output_path}")
        return output_path

    def check_and_send_alerts(self, snapshot: QueueEfficiencySnapshot) -> List[str]:
        """アラートチェック・通知送信"""

        if not self.alert_settings["alert_enabled"]:
            return []

        alerts = []

        # キューサイズアラート
        if snapshot.queue_size > self.alert_settings["queue_size_alert_threshold"]:
            alert_msg = f"🚨 キューサイズ警告: {snapshot.queue_size}件 (閾値: {self.alert_settings['queue_size_alert_threshold']}件)"
            alerts.append(alert_msg)
            self._send_alert_notification(alert_msg, "queue_size")

        # エラー修正率アラート
        if snapshot.error_fix_rate < self.alert_settings["error_fix_rate_alert_threshold"]:
            alert_msg = f"🚨 エラー修正率警告: {snapshot.error_fix_rate:.1%} (閾値: {self.alert_settings['error_fix_rate_alert_threshold']:.1%})"
            alerts.append(alert_msg)
            self._send_alert_notification(alert_msg, "error_fix_rate")

        # 処理時間アラート
        if snapshot.avg_processing_time > self.alert_settings["processing_time_alert_threshold"]:
            alert_msg = f"🚨 処理時間警告: {snapshot.avg_processing_time:.1f}秒 (閾値: {self.alert_settings['processing_time_alert_threshold']}秒)"
            alerts.append(alert_msg)
            self._send_alert_notification(alert_msg, "processing_time")

        # 重複率アラート
        if snapshot.duplicate_rate > 0.3:  # 30%以上で警告
            alert_msg = f"🚨 重複率警告: {snapshot.duplicate_rate:.1%} - 重複排除システムの実行を推奨"
            alerts.append(alert_msg)
            self._send_alert_notification(alert_msg, "duplicate_rate")

        return alerts

    def _send_alert_notification(self, message: str, alert_type: str) -> None:
        """アラート通知送信"""

        # アラート履歴ファイルに記録
        alert_file = Path("postbox/monitoring/alerts.json")
        alert_file.parent.mkdir(parents=True, exist_ok=True)

        alert_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "alert_type": alert_type,
            "message": message,
            "severity": "warning"
        }

        alerts_history = []
        if alert_file.exists():
            try:
                with open(alert_file, 'r', encoding='utf-8') as f:
                    alerts_history = json.load(f)
            except Exception:
                alerts_history = []

        alerts_history.append(alert_record)

        # 過去100件のみ保持
        alerts_history = alerts_history[-100:]

        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alerts_history, f, indent=2, ensure_ascii=False)

        # コンソール出力
        print(f"⚠️ {message}")

        # 将来的にはSlack、メール等の通知も可能


def main() -> None:
    """テスト実行"""

    print("🧪 EfficiencyTracker テスト実行")

    tracker = EfficiencyTracker()

    # テスト用タスク実行メトリクス作成
    test_metrics = [
        TaskExecutionMetrics(
            task_id="test_001",
            execution_timestamp=datetime.datetime.now().isoformat(),
            execution_time_seconds=3.5,
            errors_before=5,
            errors_after=0,
            errors_fixed=5,
            success_rate=1.0,
            quality_score=0.85,
            token_usage=1200,
            cost_estimate=0.0036,
            ai_agent="gemini",
            task_type="file_code_modification",
            file_count=1
        ),
        TaskExecutionMetrics(
            task_id="test_002",
            execution_timestamp=(datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat(),
            execution_time_seconds=5.2,
            errors_before=3,
            errors_after=2,
            errors_fixed=1,
            success_rate=0.33,
            quality_score=0.6,
            token_usage=1800,
            cost_estimate=0.0054,
            ai_agent="claude",
            task_type="file_code_modification",
            file_count=2
        )
    ]

    # メトリクス記録
    for metrics in test_metrics:
        tracker.record_task_execution(metrics)

    # テスト用キュータスク
    test_queue = [
        {"task_id": "queue_001", "target_files": ["file_a.py"], "requirements": {"error_type": "no-untyped-def"}},
        {"task_id": "queue_002", "target_files": ["file_a.py"], "requirements": {"error_type": "no-untyped-def"}},  # 重複
        {"task_id": "queue_003", "target_files": ["file_b.py"], "requirements": {"error_type": "call-arg"}},
        {"task_id": "queue_004", "target_files": ["file_c.py"], "requirements": {"error_type": "type-arg"}}
    ]

    # 効率性レポート生成
    print("\n📋 効率性レポート生成:")
    report = tracker.generate_efficiency_report(test_queue, monitoring_period_hours=1)

    print(f"現在のキューサイズ: {report.current_snapshot.queue_size}")
    print(f"エラー修正率: {report.current_snapshot.error_fix_rate:.1%}")
    print(f"重複率: {report.current_snapshot.duplicate_rate:.1%}")
    print(f"品質承認率: {report.current_snapshot.quality_approval_rate:.1%}")
    print(f"アラートレベル: {report.alert_level.value}")

    # 目標達成状況
    print(f"\n🎯 目標達成状況:")
    for goal, achieved in report.achievement_status.items():
        status = "✅" if achieved else "❌"
        print(f"  {status} {goal}")

    # 推奨事項
    print(f"\n💡 推奨事項: {len(report.recommendations)}件")
    for i, rec in enumerate(report.recommendations[:3], 1):
        print(f"  {i}. {rec}")

    # ダッシュボードデータ生成
    print("\n📊 ダッシュボードデータ生成:")
    dashboard_path = tracker.save_dashboard_data()

    print("\n✅ EfficiencyTracker テスト完了")


if __name__ == "__main__":
    main()
