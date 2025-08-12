#!/usr/bin/env python3
"""
Success Rate Monitoring System
Issue #844: ハイブリッド実装フロー - 成功率監視・測定システム

Issue #844で要求される成功基準の継続的監視・測定システム
- 新規実装成功率: 70%以上
- Token節約率: 90%以上維持
- 実装品質スコア: 0.80以上
- 統合成功率: 95%以上
"""

import json
import os
import datetime
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue

class SuccessMetricType(Enum):
    """成功メトリクスタイプ"""
    IMPLEMENTATION_SUCCESS = "implementation_success"
    TOKEN_SAVINGS = "token_savings"
    QUALITY_SCORE = "quality_score"
    INTEGRATION_SUCCESS = "integration_success"

class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class SuccessMetric:
    """成功メトリクス"""
    metric_type: SuccessMetricType
    value: float
    target_value: float
    timestamp: str
    implementation_id: str
    phase: str
    details: Dict[str, Any]

@dataclass
class Alert:
    """アラート"""
    alert_id: str
    level: AlertLevel
    metric_type: SuccessMetricType
    message: str
    current_value: float
    target_value: float
    timestamp: str
    implementation_id: str
    resolved: bool

class SuccessRateMonitor:
    """Issue #844 成功率監視・測定システム"""

    def __init__(self):
        # 成功基準 (Issue #844)
        self.success_targets = {
            SuccessMetricType.IMPLEMENTATION_SUCCESS: 0.70,  # 70%以上
            SuccessMetricType.TOKEN_SAVINGS: 0.90,          # 90%以上維持
            SuccessMetricType.QUALITY_SCORE: 0.80,          # 0.80以上
            SuccessMetricType.INTEGRATION_SUCCESS: 0.95     # 95%以上
        }

        # 監視データ
        self.metrics_history: List[SuccessMetric] = []
        self.alerts: List[Alert] = []
        self.running_averages: Dict[SuccessMetricType, float] = {}
        self.trend_analysis: Dict[SuccessMetricType, Dict[str, Any]] = {}

        # 監視設定
        self.monitoring_active = False
        self.alert_subscribers: List[callable] = []
        self.monitoring_thread: Optional[threading.Thread] = None
        self.metrics_queue = queue.Queue()

        # データ保存
        self.data_dir = Path("postbox/monitoring/success_metrics")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        print("📊 Success Rate Monitor 初期化完了")
        print(f"🎯 監視目標: 実装≥70%, Token≥90%, 品質≥80%, 統合≥95%")

        # 過去データ読み込み
        self._load_historical_data()

    def record_implementation_success(self, implementation_id: str, phase: str,
                                    success: bool, details: Dict[str, Any] = None) -> None:
        """実装成功率記録"""

        metric = SuccessMetric(
            metric_type=SuccessMetricType.IMPLEMENTATION_SUCCESS,
            value=1.0 if success else 0.0,
            target_value=self.success_targets[SuccessMetricType.IMPLEMENTATION_SUCCESS],
            timestamp=datetime.datetime.now().isoformat(),
            implementation_id=implementation_id,
            phase=phase,
            details=details or {}
        )

        self._record_metric(metric)
        print(f"📊 実装成功率記録: {implementation_id} = {'成功' if success else '失敗'}")

    def record_token_savings(self, implementation_id: str, phase: str,
                           tokens_used: int, baseline_tokens: int,
                           details: Dict[str, Any] = None) -> None:
        """Token節約率記録"""

        if baseline_tokens > 0:
            savings_rate = 1.0 - (tokens_used / baseline_tokens)
        else:
            savings_rate = 0.0

        metric = SuccessMetric(
            metric_type=SuccessMetricType.TOKEN_SAVINGS,
            value=savings_rate,
            target_value=self.success_targets[SuccessMetricType.TOKEN_SAVINGS],
            timestamp=datetime.datetime.now().isoformat(),
            implementation_id=implementation_id,
            phase=phase,
            details={
                "tokens_used": tokens_used,
                "baseline_tokens": baseline_tokens,
                "savings_absolute": baseline_tokens - tokens_used,
                **(details or {})
            }
        )

        self._record_metric(metric)
        print(f"📊 Token節約率記録: {implementation_id} = {savings_rate:.1%}")

    def record_quality_score(self, implementation_id: str, phase: str,
                           quality_score: float, details: Dict[str, Any] = None) -> None:
        """品質スコア記録"""

        metric = SuccessMetric(
            metric_type=SuccessMetricType.QUALITY_SCORE,
            value=quality_score,
            target_value=self.success_targets[SuccessMetricType.QUALITY_SCORE],
            timestamp=datetime.datetime.now().isoformat(),
            implementation_id=implementation_id,
            phase=phase,
            details=details or {}
        )

        self._record_metric(metric)
        print(f"📊 品質スコア記録: {implementation_id} = {quality_score:.2f}")

    def record_integration_success(self, implementation_id: str, phase: str,
                                 integration_success_rate: float,
                                 details: Dict[str, Any] = None) -> None:
        """統合成功率記録"""

        metric = SuccessMetric(
            metric_type=SuccessMetricType.INTEGRATION_SUCCESS,
            value=integration_success_rate,
            target_value=self.success_targets[SuccessMetricType.INTEGRATION_SUCCESS],
            timestamp=datetime.datetime.now().isoformat(),
            implementation_id=implementation_id,
            phase=phase,
            details=details or {}
        )

        self._record_metric(metric)
        print(f"📊 統合成功率記録: {implementation_id} = {integration_success_rate:.1%}")

    def get_current_success_rates(self) -> Dict[str, Any]:
        """現在の成功率取得"""

        current_rates = {}

        for metric_type in SuccessMetricType:
            recent_metrics = self._get_recent_metrics(metric_type, hours=24)

            if recent_metrics:
                if metric_type == SuccessMetricType.IMPLEMENTATION_SUCCESS:
                    # 実装成功率は平均値
                    current_rate = sum(m.value for m in recent_metrics) / len(recent_metrics)
                else:
                    # その他は加重平均または最新値
                    current_rate = sum(m.value for m in recent_metrics) / len(recent_metrics)

                target = self.success_targets[metric_type]
                meets_target = current_rate >= target

                current_rates[metric_type.value] = {
                    "current_rate": current_rate,
                    "target_rate": target,
                    "meets_target": meets_target,
                    "sample_count": len(recent_metrics),
                    "last_updated": recent_metrics[-1].timestamp if recent_metrics else None
                }
            else:
                current_rates[metric_type.value] = {
                    "current_rate": 0.0,
                    "target_rate": self.success_targets[metric_type],
                    "meets_target": False,
                    "sample_count": 0,
                    "last_updated": None
                }

        # Issue #844全体の成功基準達成状況
        overall_success = all(
            rate_data["meets_target"] for rate_data in current_rates.values()
        )

        return {
            "individual_metrics": current_rates,
            "overall_success": overall_success,
            "issue_844_criteria_met": overall_success,
            "summary": {
                "implementation_success": current_rates[SuccessMetricType.IMPLEMENTATION_SUCCESS.value]["current_rate"],
                "token_savings": current_rates[SuccessMetricType.TOKEN_SAVINGS.value]["current_rate"],
                "quality_score": current_rates[SuccessMetricType.QUALITY_SCORE.value]["current_rate"],
                "integration_success": current_rates[SuccessMetricType.INTEGRATION_SUCCESS.value]["current_rate"]
            }
        }

    def generate_success_report(self, time_period_hours: int = 24) -> Dict[str, Any]:
        """成功率レポート生成"""

        print(f"📊 成功率レポート生成中 (過去{time_period_hours}時間)")

        report_data = {
            "report_timestamp": datetime.datetime.now().isoformat(),
            "time_period_hours": time_period_hours,
            "success_metrics": {},
            "trend_analysis": {},
            "alerts_summary": {},
            "recommendations": [],
            "issue_844_status": {}
        }

        for metric_type in SuccessMetricType:
            metrics = self._get_recent_metrics(metric_type, time_period_hours)

            if metrics:
                values = [m.value for m in metrics]
                current_rate = sum(values) / len(values)
                target = self.success_targets[metric_type]

                trend = self._calculate_trend(metrics)

                metric_report = {
                    "current_rate": current_rate,
                    "target_rate": target,
                    "meets_target": current_rate >= target,
                    "sample_count": len(metrics),
                    "min_value": min(values),
                    "max_value": max(values),
                    "trend": trend,
                    "recent_implementations": [
                        {
                            "id": m.implementation_id,
                            "phase": m.phase,
                            "value": m.value,
                            "timestamp": m.timestamp
                        } for m in metrics[-5:]  # 最新5件
                    ]
                }

                report_data["success_metrics"][metric_type.value] = metric_report

                # トレンド分析
                report_data["trend_analysis"][metric_type.value] = {
                    "direction": trend,
                    "stability": self._assess_stability(values),
                    "volatility": self._calculate_volatility(values)
                }

                # 改善推奨
                if current_rate < target:
                    improvement_needed = target - current_rate
                    report_data["recommendations"].append({
                        "metric": metric_type.value,
                        "current": current_rate,
                        "target": target,
                        "improvement_needed": improvement_needed,
                        "recommendations": self._generate_improvement_recommendations(
                            metric_type, current_rate, target
                        )
                    })

        # アラートサマリー
        recent_alerts = [
            alert for alert in self.alerts
            if self._is_recent_timestamp(alert.timestamp, time_period_hours)
        ]

        report_data["alerts_summary"] = {
            "total_alerts": len(recent_alerts),
            "critical_alerts": len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
            "unresolved_alerts": len([a for a in recent_alerts if not a.resolved])
        }

        # Issue #844 ステータス
        current_rates = self.get_current_success_rates()
        report_data["issue_844_status"] = {
            "overall_criteria_met": current_rates["overall_success"],
            "individual_targets": {
                metric_type.value: current_rates["individual_metrics"][metric_type.value]["meets_target"]
                for metric_type in SuccessMetricType
            },
            "completion_percentage": sum(
                1 for metric_type in SuccessMetricType
                if current_rates["individual_metrics"][metric_type.value]["meets_target"]
            ) / len(SuccessMetricType) * 100
        }

        print(f"✅ 成功率レポート生成完了")
        return report_data

    def start_monitoring(self, check_interval_seconds: int = 300) -> None:
        """リアルタイム監視開始"""

        if self.monitoring_active:
            print("⚠️ 監視は既に開始されています")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()

        print(f"📊 リアルタイム監視開始 (間隔: {check_interval_seconds}秒)")

    def stop_monitoring(self) -> None:
        """監視停止"""

        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)

        print("📊 監視停止")

    def subscribe_to_alerts(self, callback: callable) -> None:
        """アラート通知購読"""

        self.alert_subscribers.append(callback)
        print(f"🔔 アラート通知購読追加: {len(self.alert_subscribers)}件")

    def get_metrics_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボード用データ取得"""

        dashboard_data = {
            "current_rates": self.get_current_success_rates(),
            "recent_trends": {},
            "active_alerts": [
                self._alert_to_dict(alert) for alert in self.alerts if not alert.resolved
            ],
            "recent_activity": [],
            "performance_summary": {}
        }

        # トレンドデータ
        for metric_type in SuccessMetricType:
            recent_metrics = self._get_recent_metrics(metric_type, hours=24)
            if recent_metrics:
                dashboard_data["recent_trends"][metric_type.value] = [
                    {"timestamp": m.timestamp, "value": m.value}
                    for m in recent_metrics[-20:]  # 最新20件
                ]

        # 最近のアクティビティ
        recent_metrics = sorted(
            self.metrics_history[-50:], key=lambda m: m.timestamp, reverse=True
        )
        dashboard_data["recent_activity"] = [
            {
                "timestamp": m.timestamp,
                "type": m.metric_type.value,
                "implementation_id": m.implementation_id,
                "phase": m.phase,
                "value": m.value,
                "meets_target": m.value >= m.target_value
            } for m in recent_metrics[:20]
        ]

        # パフォーマンスサマリー
        dashboard_data["performance_summary"] = {
            "total_implementations": len(set(m.implementation_id for m in self.metrics_history)),
            "success_trend": self._calculate_overall_trend(),
            "average_quality": self._calculate_average_quality(),
            "token_efficiency": self._calculate_token_efficiency()
        }

        return dashboard_data

    # === プライベートメソッド ===

    def _record_metric(self, metric: SuccessMetric) -> None:
        """メトリクス記録"""

        self.metrics_history.append(metric)
        self.metrics_queue.put(metric)

        # 目標未達成時のアラート生成
        if metric.value < metric.target_value:
            self._generate_alert(metric)

        # データ保存
        self._save_metric(metric)

        # 実行平均更新
        self._update_running_average(metric.metric_type)

    def _generate_alert(self, metric: SuccessMetric) -> None:
        """アラート生成"""

        # アラートレベル決定
        deficit = metric.target_value - metric.value
        if deficit >= 0.2:
            level = AlertLevel.CRITICAL
        elif deficit >= 0.1:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.INFO

        alert = Alert(
            alert_id=f"alert_{metric.implementation_id}_{int(time.time())}",
            level=level,
            metric_type=metric.metric_type,
            message=self._generate_alert_message(metric, deficit),
            current_value=metric.value,
            target_value=metric.target_value,
            timestamp=datetime.datetime.now().isoformat(),
            implementation_id=metric.implementation_id,
            resolved=False
        )

        self.alerts.append(alert)

        # 通知配信
        for callback in self.alert_subscribers:
            try:
                callback(alert)
            except Exception as e:
                print(f"⚠️ アラート通知エラー: {e}")

    def _generate_alert_message(self, metric: SuccessMetric, deficit: float) -> str:
        """アラートメッセージ生成"""

        metric_names = {
            SuccessMetricType.IMPLEMENTATION_SUCCESS: "実装成功率",
            SuccessMetricType.TOKEN_SAVINGS: "Token節約率",
            SuccessMetricType.QUALITY_SCORE: "品質スコア",
            SuccessMetricType.INTEGRATION_SUCCESS: "統合成功率"
        }

        metric_name = metric_names.get(metric.metric_type, "メトリクス")

        if metric.metric_type == SuccessMetricType.TOKEN_SAVINGS:
            return f"{metric_name}が目標を下回っています: {metric.value:.1%} (目標: {metric.target_value:.1%})"
        else:
            return f"{metric_name}が目標を下回っています: {metric.value:.2f} (目標: {metric.target_value:.2f})"

    def _monitoring_loop(self, check_interval: int) -> None:
        """監視ループ"""

        while self.monitoring_active:
            try:
                # メトリクス処理
                while not self.metrics_queue.empty():
                    try:
                        metric = self.metrics_queue.get_nowait()
                        # 追加の監視処理があればここで実行
                    except queue.Empty:
                        break

                # 定期チェック
                self._perform_periodic_checks()

                time.sleep(check_interval)

            except Exception as e:
                print(f"⚠️ 監視ループエラー: {e}")
                time.sleep(check_interval)

    def _perform_periodic_checks(self) -> None:
        """定期チェック"""

        # トレンド分析更新
        for metric_type in SuccessMetricType:
            recent_metrics = self._get_recent_metrics(metric_type, hours=4)
            if len(recent_metrics) >= 3:
                trend = self._calculate_trend(recent_metrics)

                # 悪化トレンドの場合はアラート
                if trend == "declining" and len(recent_metrics) >= 5:
                    latest_metric = recent_metrics[-1]
                    if latest_metric.value < latest_metric.target_value:
                        # 既にアラートがあるかチェック
                        recent_alerts = [
                            a for a in self.alerts
                            if a.metric_type == metric_type and
                            not a.resolved and
                            self._is_recent_timestamp(a.timestamp, hours=1)
                        ]

                        if not recent_alerts:
                            self._generate_trend_alert(metric_type, trend, recent_metrics)

    def _generate_trend_alert(self, metric_type: SuccessMetricType, trend: str,
                             recent_metrics: List[SuccessMetric]) -> None:
        """トレンドアラート生成"""

        latest_metric = recent_metrics[-1]

        alert = Alert(
            alert_id=f"trend_alert_{metric_type.value}_{int(time.time())}",
            level=AlertLevel.WARNING,
            metric_type=metric_type,
            message=f"{metric_type.value} に悪化トレンドを検出: {trend}",
            current_value=latest_metric.value,
            target_value=latest_metric.target_value,
            timestamp=datetime.datetime.now().isoformat(),
            implementation_id="trend_analysis",
            resolved=False
        )

        self.alerts.append(alert)

    def _get_recent_metrics(self, metric_type: SuccessMetricType, hours: int) -> List[SuccessMetric]:
        """最近のメトリクス取得"""

        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)

        return [
            metric for metric in self.metrics_history
            if metric.metric_type == metric_type and
            datetime.datetime.fromisoformat(metric.timestamp) > cutoff_time
        ]

    def _calculate_trend(self, metrics: List[SuccessMetric]) -> str:
        """トレンド計算"""

        if len(metrics) < 3:
            return "insufficient_data"

        values = [m.value for m in metrics]

        # 簡易的な線形回帰
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"

    def _assess_stability(self, values: List[float]) -> str:
        """安定性評価"""

        if len(values) < 3:
            return "unknown"

        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5

        if std_dev / mean_val < 0.1:
            return "stable"
        elif std_dev / mean_val < 0.2:
            return "moderate"
        else:
            return "volatile"

    def _calculate_volatility(self, values: List[float]) -> float:
        """ボラティリティ計算"""

        if len(values) < 2:
            return 0.0

        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)

        return variance ** 0.5

    def _generate_improvement_recommendations(self, metric_type: SuccessMetricType,
                                           current_rate: float, target: float) -> List[str]:
        """改善推奨生成"""

        recommendations = {
            SuccessMetricType.IMPLEMENTATION_SUCCESS: [
                "Phase Aの設計品質を向上させる",
                "Gemini指示の具体性を高める",
                "エラー処理パターンの標準化",
                "品質チェックポイントの強化"
            ],
            SuccessMetricType.TOKEN_SAVINGS: [
                "タスク分割の最適化",
                "テンプレートの効率化",
                "Gemini実行の効率改善",
                "重複処理の除去"
            ],
            SuccessMetricType.QUALITY_SCORE: [
                "コードレビュープロセス強化",
                "自動品質チェックの拡充",
                "テスト・ドキュメント品質向上",
                "リファクタリング基準の厳格化"
            ],
            SuccessMetricType.INTEGRATION_SUCCESS: [
                "統合テストの充実",
                "依存関係管理の改善",
                "インターフェース設計の標準化",
                "エラー復旧機能の強化"
            ]
        }

        return recommendations.get(metric_type, ["一般的な品質改善施策を実施"])

    def _save_metric(self, metric: SuccessMetric) -> None:
        """メトリクス保存"""

        date_str = datetime.datetime.now().strftime("%Y%m%d")
        metric_file = self.data_dir / f"metrics_{metric.metric_type.value}_{date_str}.json"

        # 既存データ読み込み
        if metric_file.exists():
            with open(metric_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"metrics": []}

        # 新しいメトリクス追加（Enumを文字列に変換）
        metric_dict = asdict(metric)
        if 'metric_type' in metric_dict and hasattr(metric_dict['metric_type'], 'value'):
            metric_dict['metric_type'] = metric_dict['metric_type'].value
        data["metrics"].append(metric_dict)

        # 保存
        with open(metric_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_historical_data(self) -> None:
        """過去データ読み込み"""

        print("📊 過去データ読み込み中...")

        loaded_count = 0

        for metric_file in self.data_dir.glob("metrics_*.json"):
            try:
                with open(metric_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for metric_data in data.get("metrics", []):
                    # metric_typeを文字列からEnumに変換
                    if 'metric_type' in metric_data and isinstance(metric_data['metric_type'], str):
                        try:
                            metric_data['metric_type'] = SuccessMetricType(metric_data['metric_type'])
                        except ValueError:
                            # 旧形式の互換性のため、値から変換を試みる
                            for metric_type in SuccessMetricType:
                                if metric_type.value == metric_data['metric_type']:
                                    metric_data['metric_type'] = metric_type
                                    break

                    metric = SuccessMetric(**metric_data)
                    self.metrics_history.append(metric)
                    loaded_count += 1

            except Exception as e:
                print(f"⚠️ データ読み込みエラー {metric_file}: {e}")

        # 時系列ソート
        self.metrics_history.sort(key=lambda m: m.timestamp)

        print(f"✅ 過去データ読み込み完了: {loaded_count}件")

    def _update_running_average(self, metric_type: SuccessMetricType) -> None:
        """実行平均更新"""

        recent_metrics = self._get_recent_metrics(metric_type, hours=24)
        if recent_metrics:
            self.running_averages[metric_type] = sum(m.value for m in recent_metrics) / len(recent_metrics)

    def _is_recent_timestamp(self, timestamp: str, hours: int) -> bool:
        """タイムスタンプが最近のものかチェック"""

        try:
            ts = datetime.datetime.fromisoformat(timestamp)
            cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
            return ts > cutoff
        except:
            return False

    def _calculate_overall_trend(self) -> str:
        """全体トレンド計算"""

        trends = []
        for metric_type in SuccessMetricType:
            recent_metrics = self._get_recent_metrics(metric_type, hours=24)
            if len(recent_metrics) >= 3:
                trend = self._calculate_trend(recent_metrics)
                trends.append(trend)

        if not trends:
            return "insufficient_data"

        improving = trends.count("improving")
        declining = trends.count("declining")

        if improving > declining:
            return "improving"
        elif declining > improving:
            return "declining"
        else:
            return "stable"

    def _calculate_average_quality(self) -> float:
        """平均品質計算"""

        recent_quality_metrics = self._get_recent_metrics(SuccessMetricType.QUALITY_SCORE, hours=24)
        if recent_quality_metrics:
            return sum(m.value for m in recent_quality_metrics) / len(recent_quality_metrics)
        return 0.0

    def _calculate_token_efficiency(self) -> float:
        """Token効率計算"""

        recent_token_metrics = self._get_recent_metrics(SuccessMetricType.TOKEN_SAVINGS, hours=24)
        if recent_token_metrics:
            return sum(m.value for m in recent_token_metrics) / len(recent_token_metrics)
        return 0.0

    def _alert_to_dict(self, alert: Alert) -> Dict[str, Any]:
        """アラートオブジェクトを辞書に変換（Enum処理含む）"""
        alert_dict = asdict(alert)

        # Enumフィールドを文字列に変換
        if 'level' in alert_dict and hasattr(alert_dict['level'], 'value'):
            alert_dict['level'] = alert_dict['level'].value

        if 'metric_type' in alert_dict and hasattr(alert_dict['metric_type'], 'value'):
            alert_dict['metric_type'] = alert_dict['metric_type'].value

        return alert_dict

def main():
    """テスト実行"""

    monitor = SuccessRateMonitor()

    # テストデータ記録
    print("📊 テストデータ記録開始")

    # 実装成功率テスト
    monitor.record_implementation_success("test_001", "phase_a", True, {"complexity": "medium"})
    monitor.record_implementation_success("test_002", "phase_b", True, {"quality": 0.85})
    monitor.record_implementation_success("test_003", "phase_c", False, {"issue": "integration_failure"})

    # Token節約率テスト
    monitor.record_token_savings("test_001", "phase_b", 800, 1000, {"optimization": "gemini_flash"})
    monitor.record_token_savings("test_002", "phase_b", 750, 1000, {"optimization": "template_reuse"})

    # 品質スコアテスト
    monitor.record_quality_score("test_001", "phase_c", 0.87, {"components": 3})
    monitor.record_quality_score("test_002", "phase_c", 0.82, {"components": 2})
    monitor.record_quality_score("test_003", "phase_c", 0.75, {"components": 4})

    # 統合成功率テスト
    monitor.record_integration_success("test_001", "phase_c", 0.95, {"tests_passed": 19, "tests_total": 20})
    monitor.record_integration_success("test_002", "phase_c", 0.98, {"tests_passed": 49, "tests_total": 50})

    # 現在の成功率確認
    print("\n📊 現在の成功率:")
    current_rates = monitor.get_current_success_rates()
    for metric, data in current_rates["individual_metrics"].items():
        print(f"  {metric}: {data['current_rate']:.1%} (目標: {data['target_rate']:.1%}) {'✅' if data['meets_target'] else '❌'}")

    # Issue #844基準達成状況
    print(f"\n🎯 Issue #844基準達成: {'✅' if current_rates['overall_success'] else '❌'}")

    # レポート生成
    print("\n📊 成功率レポート生成")
    report = monitor.generate_success_report(time_period_hours=1)
    print(f"  完了率: {report['issue_844_status']['completion_percentage']:.1f}%")
    print(f"  アラート: {report['alerts_summary']['total_alerts']}件")

    # ダッシュボードデータ
    print("\n📊 ダッシュボードデータ")
    dashboard = monitor.get_metrics_dashboard_data()
    print(f"  総実装数: {dashboard['performance_summary']['total_implementations']}")
    print(f"  全体トレンド: {dashboard['performance_summary']['success_trend']}")
    print(f"  アクティブアラート: {len(dashboard['active_alerts'])}件")

    print("\n🎉 Success Rate Monitor テスト完了")

if __name__ == "__main__":
    main()
