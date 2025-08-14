#!/usr/bin/env python3
"""
EnhancedCollaborationDashboard - Issue #860対応
協業ダッシュボード強化システム

包括的可視化・リアルタイムアラート・トレンド分析により
協業状況の透明性向上と問題の早期発見を実現
"""

import json
import datetime
import statistics
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class DashboardSection(Enum):
    """ダッシュボードセクション"""
    OVERVIEW = "overview"
    COLLABORATION_METRICS = "collaboration_metrics"
    PERFORMANCE_TRENDS = "performance_trends"
    QUALITY_INDICATORS = "quality_indicators"
    ALERTS_NOTIFICATIONS = "alerts_notifications"
    OPTIMIZATION_INSIGHTS = "optimization_insights"
    HISTORICAL_ANALYSIS = "historical_analysis"


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TrendDirection(Enum):
    """トレンド方向"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


@dataclass
class DashboardAlert:
    """ダッシュボードアラート"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: str
    section: DashboardSection
    action_required: bool
    auto_resolve: bool
    resolution_status: str  # "active", "acknowledged", "resolved"


@dataclass
class MetricTrend:
    """メトリクストレンド"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: TrendDirection
    confidence_level: float  # 0.0-1.0
    data_points: List[float]
    time_period: str


@dataclass
class CollaborationInsight:
    """協業インサイト"""
    insight_id: str
    category: str
    title: str
    description: str
    impact_level: str  # "low", "medium", "high", "critical"
    recommended_actions: List[str]
    estimated_benefit: str
    implementation_difficulty: str


@dataclass
class DashboardData:
    """ダッシュボードデータ"""
    timestamp: str
    overview_metrics: Dict[str, Any]
    collaboration_metrics: Dict[str, Any]
    performance_trends: List[MetricTrend]
    quality_indicators: Dict[str, Any]
    active_alerts: List[DashboardAlert]
    optimization_insights: List[CollaborationInsight]
    historical_summary: Dict[str, Any]


class EnhancedCollaborationDashboard:
    """強化協業ダッシュボードシステム

    Gemini×Claude協業の包括的可視化と分析により、
    協業効率の透明性向上と最適化機会の特定を実現
    """

    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.collaboration_dir = self.postbox_dir / "collaboration"
        self.monitoring_dir = self.postbox_dir / "monitoring"
        self.dashboard_dir = self.collaboration_dir / "dashboard"

        # ディレクトリ作成
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)

        self.dashboard_data_file = self.dashboard_dir / "dashboard_data.json"
        self.alerts_file = self.dashboard_dir / "alerts.json"
        self.insights_file = self.dashboard_dir / "insights.json"
        self.trends_cache_file = self.dashboard_dir / "trends_cache.json"

        # アラート管理
        self.active_alerts = self._load_alerts()

        # インサイト履歴
        self.insights_history = self._load_insights_history()

        # トレンドキャッシュ
        self.trends_cache = self._load_trends_cache()

        logger.info("📊 EnhancedCollaborationDashboard 初期化完了")

    def generate_dashboard_data(self) -> DashboardData:
        """ダッシュボードデータ生成

        Returns:
            DashboardData: 完全なダッシュボードデータ
        """

        logger.info("📊 ダッシュボードデータ生成開始")

        try:
            timestamp = datetime.datetime.now().isoformat()

            # 各セクションのデータ生成
            overview = self._generate_overview_metrics()
            collaboration = self._generate_collaboration_metrics()
            trends = self._generate_performance_trends()
            quality = self._generate_quality_indicators()
            alerts = self._update_and_get_active_alerts()
            insights = self._generate_optimization_insights()
            historical = self._generate_historical_summary()

            dashboard_data = DashboardData(
                timestamp=timestamp,
                overview_metrics=overview,
                collaboration_metrics=collaboration,
                performance_trends=trends,
                quality_indicators=quality,
                active_alerts=alerts,
                optimization_insights=insights,
                historical_summary=historical
            )

            # ダッシュボードデータ保存
            self._save_dashboard_data(dashboard_data)

            logger.info("✅ ダッシュボードデータ生成完了")

            return dashboard_data

        except Exception as e:
            logger.error(f"❌ ダッシュボードデータ生成エラー: {e}")
            return self._create_fallback_dashboard_data()

    def _generate_overview_metrics(self) -> Dict[str, Any]:
        """概要メトリクス生成"""

        overview = {
            "collaboration_safety_score": 0.0,
            "current_safety_level": "unknown",
            "target_achievement": {
                "safety_score_progress": 0.0,
                "target_value": 75.0,
                "current_value": 40.0,
                "completion_percentage": 0.0
            },
            "system_status": {
                "operational": True,
                "last_update": datetime.datetime.now().isoformat(),
                "active_sessions": 1,
                "error_rate": 0.0
            },
            "quick_stats": {
                "total_tasks_today": 0,
                "success_rate_today": 0.0,
                "avg_processing_time": 0.0,
                "token_efficiency": 0.99
            }
        }

        try:
            # 効率監視データから現在の安全性スコア取得
            efficiency_file = self.collaboration_dir / "efficiency_metrics.json"
            if efficiency_file.exists():
                with open(efficiency_file, 'r', encoding='utf-8') as f:
                    efficiency_data = json.load(f)

                if efficiency_data:
                    latest_metric = efficiency_data[-1]
                    current_score = latest_metric.get("overall_safety_score", 40.0)
                    safety_level = latest_metric.get("safety_level", "low")

                    overview["collaboration_safety_score"] = current_score
                    overview["current_safety_level"] = safety_level
                    overview["target_achievement"]["current_value"] = current_score
                    overview["target_achievement"]["completion_percentage"] = (current_score / 75.0) * 100

            # 3層検証データから今日の統計
            verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"
            if verification_file.exists():
                with open(verification_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)

                # 今日のデータフィルタリング
                today = datetime.datetime.now().date()
                today_data = []

                for entry in verification_data:
                    try:
                        entry_date = datetime.datetime.fromisoformat(entry["timestamp"]).date()
                        if entry_date == today:
                            today_data.append(entry)
                    except Exception:
                        continue

                if today_data:
                    overview["quick_stats"]["total_tasks_today"] = len(today_data)

                    success_rates = [d["success_rates"]["overall_success_rate"] for d in today_data]
                    overview["quick_stats"]["success_rate_today"] = statistics.mean(success_rates)

                    exec_times = [d["execution_time"] for d in today_data]
                    overview["quick_stats"]["avg_processing_time"] = statistics.mean(exec_times)

        except Exception as e:
            logger.warning(f"⚠️ 概要メトリクス生成エラー: {e}")

        return overview

    def _generate_collaboration_metrics(self) -> Dict[str, Any]:
        """協業メトリクス生成"""

        collaboration = {
            "agent_performance": {
                "gemini_efficiency": 0.85,
                "claude_effectiveness": 0.80,
                "collaboration_synergy": 0.75
            },
            "task_distribution": {
                "gemini_tasks": 0,
                "claude_tasks": 0,
                "hybrid_tasks": 0,
                "auto_routed_tasks": 0
            },
            "layer_performance": {
                "layer1_success_rate": 0.0,
                "layer2_success_rate": 0.0,
                "layer3_approval_rate": 0.0,
                "integration_success_rate": 0.0
            },
            "failsafe_metrics": {
                "current_usage_rate": 0.0,
                "target_usage_rate": 0.20,
                "reduction_progress": 0.0,
                "prevention_effectiveness": 0.0
            },
            "routing_accuracy": {
                "correct_routing_rate": 0.0,
                "optimization_efficiency": 0.0,
                "decision_confidence": 0.0
            }
        }

        try:
            # 3層検証データから層別パフォーマンス
            verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"
            if verification_file.exists():
                with open(verification_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)

                if verification_data:
                    recent_data = verification_data[-10:]  # 最新10件

                    layer1_rates = [d["success_rates"]["layer1_success_rate"] for d in recent_data]
                    layer2_rates = [d["success_rates"]["layer2_success_rate"] for d in recent_data]
                    layer3_rates = [d["success_rates"]["layer3_approval_rate"] for d in recent_data]
                    integration_rates = [d["success_rates"]["integration_success_rate"] for d in recent_data]

                    collaboration["layer_performance"] = {
                        "layer1_success_rate": statistics.mean(layer1_rates) if layer1_rates else 0.0,
                        "layer2_success_rate": statistics.mean(layer2_rates) if layer2_rates else 0.0,
                        "layer3_approval_rate": statistics.mean(layer3_rates) if layer3_rates else 0.0,
                        "integration_success_rate": statistics.mean(integration_rates) if integration_rates else 0.0
                    }

            # フェイルセーフメトリクス
            failsafe_file = self.monitoring_dir / "failsafe_usage.json"
            if failsafe_file.exists():
                with open(failsafe_file, 'r', encoding='utf-8') as f:
                    failsafe_data = json.load(f)

                if failsafe_data:
                    recent_failsafe = failsafe_data[-5:]

                    total_failsafe = sum(entry["failsafe_count"] for entry in recent_failsafe)
                    total_files = sum(entry["total_files"] for entry in recent_failsafe)

                    if total_files > 0:
                        current_rate = total_failsafe / total_files
                        target_rate = 0.20

                        collaboration["failsafe_metrics"] = {
                            "current_usage_rate": current_rate,
                            "target_usage_rate": target_rate,
                            "reduction_progress": max(0, (0.5 - current_rate) / (0.5 - target_rate)),
                            "prevention_effectiveness": max(0, 1.0 - current_rate / 0.5)
                        }

            # ルーティング精度（フロー最適化データから）
            routing_file = self.collaboration_dir / "routing_decisions.json"
            if routing_file.exists():
                with open(routing_file, 'r', encoding='utf-8') as f:
                    routing_data = json.load(f)

                if routing_data:
                    recent_decisions = routing_data[-20:]  # 最新20件

                    confidence_scores = [d["confidence_score"] for d in recent_decisions]

                    collaboration["routing_accuracy"] = {
                        "correct_routing_rate": 0.85,  # 推定値
                        "optimization_efficiency": 0.80,  # 推定値
                        "decision_confidence": statistics.mean(confidence_scores) if confidence_scores else 0.0
                    }

        except Exception as e:
            logger.warning(f"⚠️ 協業メトリクス生成エラー: {e}")

        return collaboration

    def _generate_performance_trends(self) -> List[MetricTrend]:
        """パフォーマンストレンド生成"""

        trends = []

        try:
            # 効率メトリクストレンド
            efficiency_file = self.collaboration_dir / "efficiency_metrics.json"
            if efficiency_file.exists():
                with open(efficiency_file, 'r', encoding='utf-8') as f:
                    efficiency_data = json.load(f)

                if len(efficiency_data) >= 2:
                    # 安全性スコアトレンド
                    safety_scores = [d["overall_safety_score"] for d in efficiency_data[-10:]]
                    if len(safety_scores) >= 2:
                        trend = self._create_metric_trend(
                            "collaboration_safety_score",
                            safety_scores,
                            "7d"
                        )
                        trends.append(trend)

                    # 成功率トレンド
                    success_rates = [d["task_success_rate"] for d in efficiency_data[-10:]]
                    if len(success_rates) >= 2:
                        trend = self._create_metric_trend(
                            "task_success_rate",
                            success_rates,
                            "7d"
                        )
                        trends.append(trend)

            # フェイルセーフ使用率トレンド
            failsafe_file = self.monitoring_dir / "failsafe_usage.json"
            if failsafe_file.exists():
                with open(failsafe_file, 'r', encoding='utf-8') as f:
                    failsafe_data = json.load(f)

                if len(failsafe_data) >= 5:
                    # フェイルセーフ率を時系列で計算
                    failsafe_rates = []
                    for entry in failsafe_data[-10:]:
                        if entry["total_files"] > 0:
                            rate = entry["failsafe_count"] / entry["total_files"]
                            failsafe_rates.append(rate)

                    if len(failsafe_rates) >= 2:
                        trend = self._create_metric_trend(
                            "failsafe_usage_rate",
                            failsafe_rates,
                            "7d"
                        )
                        trends.append(trend)

            # 処理時間トレンド
            verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"
            if verification_file.exists():
                with open(verification_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)

                if len(verification_data) >= 5:
                    exec_times = [d["execution_time"] for d in verification_data[-10:]]
                    if len(exec_times) >= 2:
                        trend = self._create_metric_trend(
                            "processing_time",
                            exec_times,
                            "7d"
                        )
                        trends.append(trend)

        except Exception as e:
            logger.warning(f"⚠️ パフォーマンストレンド生成エラー: {e}")

        return trends

    def _create_metric_trend(self, metric_name: str, data_points: List[float],
                           time_period: str) -> MetricTrend:
        """メトリクストレンド作成"""

        if len(data_points) < 2:
            return MetricTrend(
                metric_name=metric_name,
                current_value=data_points[0] if data_points else 0.0,
                previous_value=0.0,
                change_percentage=0.0,
                trend_direction=TrendDirection.STABLE,
                confidence_level=0.0,
                data_points=data_points,
                time_period=time_period
            )

        current_value = data_points[-1]
        previous_value = data_points[-2]

        # 変化率計算
        if previous_value != 0:
            change_percentage = ((current_value - previous_value) / previous_value) * 100
        else:
            change_percentage = 0.0

        # トレンド方向判定
        if abs(change_percentage) < 5:
            trend_direction = TrendDirection.STABLE
        elif change_percentage > 5:
            trend_direction = TrendDirection.IMPROVING
        else:
            trend_direction = TrendDirection.DECLINING

        # ボラティリティチェック
        if len(data_points) >= 3:
            volatility = statistics.stdev(data_points[-5:]) if len(data_points) >= 5 else statistics.stdev(data_points)
            if volatility > statistics.mean(data_points) * 0.2:  # 20%以上の変動
                trend_direction = TrendDirection.VOLATILE

        # 信頼度計算
        confidence_level = min(len(data_points) / 10.0, 1.0)  # データ点数に基づく

        return MetricTrend(
            metric_name=metric_name,
            current_value=current_value,
            previous_value=previous_value,
            change_percentage=change_percentage,
            trend_direction=trend_direction,
            confidence_level=confidence_level,
            data_points=data_points,
            time_period=time_period
        )

    def _generate_quality_indicators(self) -> Dict[str, Any]:
        """品質指標生成"""

        quality = {
            "code_quality_score": 0.0,
            "type_safety_coverage": 0.0,
            "test_coverage_estimate": 0.0,
            "documentation_completeness": 0.0,
            "security_compliance": 0.0,
            "performance_efficiency": 0.0,
            "quality_trend": "stable",
            "improvement_areas": [],
            "quality_gates": {
                "syntax_validation": {"status": "unknown", "score": 0.0},
                "type_checking": {"status": "unknown", "score": 0.0},
                "integration_tests": {"status": "unknown", "score": 0.0},
                "claude_approval": {"status": "unknown", "score": 0.0}
            }
        }

        try:
            # 予防的品質チェック結果から品質指標取得
            preventive_dir = self.postbox_dir / "quality" / "preventive_checks"
            if preventive_dir.exists():
                check_files = list(preventive_dir.glob("check_*.json"))

                if check_files:
                    # 最新のチェック結果
                    latest_files = sorted(check_files)[-5:]

                    quality_scores = []
                    risk_counts = []

                    for check_file in latest_files:
                        try:
                            with open(check_file, 'r', encoding='utf-8') as f:
                                check_data = json.load(f)

                            quality_scores.append(check_data.get("overall_quality_score", 0.0))
                            risk_counts.append(len(check_data.get("detected_risks", [])))

                        except Exception:
                            continue

                    if quality_scores:
                        quality["code_quality_score"] = statistics.mean(quality_scores)

                        # 改善エリア特定
                        if statistics.mean(risk_counts) > 3:
                            quality["improvement_areas"].append("多数の品質リスク検出")

                        if quality["code_quality_score"] < 0.7:
                            quality["improvement_areas"].append("全体的な品質向上が必要")

            # 3層検証から品質ゲート状況
            verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"
            if verification_file.exists():
                with open(verification_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)

                if verification_data:
                    latest_verification = verification_data[-1]
                    success_rates = latest_verification["success_rates"]

                    quality["quality_gates"] = {
                        "syntax_validation": {
                            "status": "pass" if success_rates["layer1_success_rate"] > 0.8 else "fail",
                            "score": success_rates["layer1_success_rate"]
                        },
                        "type_checking": {
                            "status": "pass" if success_rates["layer2_success_rate"] > 0.9 else "fail",
                            "score": success_rates["layer2_success_rate"]
                        },
                        "integration_tests": {
                            "status": "pass" if success_rates["integration_success_rate"] > 0.8 else "fail",
                            "score": success_rates["integration_success_rate"]
                        },
                        "claude_approval": {
                            "status": "pass" if success_rates["layer3_approval_rate"] > 0.7 else "fail",
                            "score": success_rates["layer3_approval_rate"]
                        }
                    }

        except Exception as e:
            logger.warning(f"⚠️ 品質指標生成エラー: {e}")

        return quality

    def _update_and_get_active_alerts(self) -> List[DashboardAlert]:
        """アクティブアラート更新・取得"""

        current_alerts = []

        try:
            # 既存アラートをチェック・更新
            self._update_existing_alerts()

            # 新しいアラートを生成
            new_alerts = self._generate_new_alerts()
            current_alerts.extend(new_alerts)

            # アクティブアラートのみフィルタリング
            active_alerts = [alert for alert in self.active_alerts + current_alerts
                           if alert.resolution_status == "active"]

            # 重複除去
            unique_alerts = {}
            for alert in active_alerts:
                unique_alerts[alert.alert_id] = alert

            final_alerts = list(unique_alerts.values())

            # アラート保存
            self._save_alerts(final_alerts)

            return final_alerts[:10]  # 最大10件

        except Exception as e:
            logger.warning(f"⚠️ アラート更新エラー: {e}")
            return []

    def _update_existing_alerts(self) -> None:
        """既存アラート更新"""

        for alert in self.active_alerts:
            # 自動解決アラートのチェック
            if alert.auto_resolve and alert.resolution_status == "active":
                if self._check_alert_auto_resolution(alert):
                    alert.resolution_status = "resolved"

    def _check_alert_auto_resolution(self, alert: DashboardAlert) -> bool:
        """アラート自動解決チェック"""

        # 基本的な自動解決ロジック
        if "failsafe" in alert.title.lower():
            # フェイルセーフ関連アラートは使用率改善で解決
            try:
                current_rate = self._get_current_failsafe_rate()
                if current_rate < 0.3:  # 30%未満で解決
                    return True
            except Exception:
                pass

        elif "success rate" in alert.title.lower():
            # 成功率関連アラートは成功率改善で解決
            try:
                current_rate = self._get_current_success_rate()
                if current_rate > 0.7:  # 70%以上で解決
                    return True
            except Exception:
                pass

        return False

    def _generate_new_alerts(self) -> List[DashboardAlert]:
        """新しいアラート生成"""

        new_alerts = []

        try:
            # 協業安全性スコアアラート
            safety_score = self._get_current_safety_score()
            if safety_score < 60:
                alert = DashboardAlert(
                    alert_id=f"safety_score_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}",
                    level=AlertLevel.CRITICAL if safety_score < 40 else AlertLevel.WARNING,
                    title="協業安全性スコア低下",
                    message=f"現在の安全性スコア: {safety_score:.1f}/100 (目標: 75+)",
                    timestamp=datetime.datetime.now().isoformat(),
                    section=DashboardSection.COLLABORATION_METRICS,
                    action_required=True,
                    auto_resolve=True,
                    resolution_status="active"
                )
                new_alerts.append(alert)

            # フェイルセーフ過使用アラート
            failsafe_rate = self._get_current_failsafe_rate()
            if failsafe_rate > 0.4:
                alert = DashboardAlert(
                    alert_id=f"failsafe_overuse_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}",
                    level=AlertLevel.WARNING,
                    title="フェイルセーフ過使用検出",
                    message=f"フェイルセーフ使用率: {failsafe_rate:.1%} (目標: 20%以下)",
                    timestamp=datetime.datetime.now().isoformat(),
                    section=DashboardSection.PERFORMANCE_TRENDS,
                    action_required=True,
                    auto_resolve=True,
                    resolution_status="active"
                )
                new_alerts.append(alert)

            # Layer1成功率アラート
            layer1_rate = self._get_layer1_success_rate()
            if layer1_rate < 0.6:
                alert = DashboardAlert(
                    alert_id=f"layer1_failure_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}",
                    level=AlertLevel.ERROR,
                    title="Layer1構文検証失敗率高",
                    message=f"Layer1成功率: {layer1_rate:.1%} (目標: 80%以上)",
                    timestamp=datetime.datetime.now().isoformat(),
                    section=DashboardSection.QUALITY_INDICATORS,
                    action_required=True,
                    auto_resolve=True,
                    resolution_status="active"
                )
                new_alerts.append(alert)

        except Exception as e:
            logger.warning(f"⚠️ 新アラート生成エラー: {e}")

        return new_alerts

    def _generate_optimization_insights(self) -> List[CollaborationInsight]:
        """最適化インサイト生成"""

        insights = []

        try:
            # パフォーマンス分析からインサイト生成
            safety_score = self._get_current_safety_score()
            failsafe_rate = self._get_current_failsafe_rate()

            # 安全性スコア改善インサイト
            if safety_score < 75:
                gap = 75 - safety_score
                if gap > 20:
                    impact_level = "critical"
                    benefit = "協業安全性の大幅向上"
                elif gap > 10:
                    impact_level = "high"
                    benefit = "協業安全性の顕著な向上"
                else:
                    impact_level = "medium"
                    benefit = "協業安全性の改善"

                insight = CollaborationInsight(
                    insight_id=f"safety_improvement_{datetime.datetime.now().strftime('%Y%m%d')}",
                    category="safety_optimization",
                    title="協業安全性スコア向上機会",
                    description=f"現在{safety_score:.1f}点の安全性スコアを目標の75点に向上させる機会があります",
                    impact_level=impact_level,
                    recommended_actions=[
                        "Layer1構文検証の強化",
                        "予防的品質チェックの導入",
                        "フェイルセーフ使用率の削減"
                    ],
                    estimated_benefit=benefit,
                    implementation_difficulty="medium"
                )
                insights.append(insight)

            # フェイルセーフ削減インサイト
            if failsafe_rate > 0.25:
                insight = CollaborationInsight(
                    insight_id=f"failsafe_reduction_{datetime.datetime.now().strftime('%Y%m%d')}",
                    category="efficiency_optimization",
                    title="フェイルセーフ使用率削減機会",
                    description=f"現在{failsafe_rate:.1%}のフェイルセーフ使用率を20%以下に削減可能",
                    impact_level="high",
                    recommended_actions=[
                        "事前バリデーション強化",
                        "型注釈カバレッジ向上",
                        "自動修正機能活用"
                    ],
                    estimated_benefit="処理効率20-30%向上",
                    implementation_difficulty="low"
                )
                insights.append(insight)

            # 協業ルーティング最適化インサイト
            routing_accuracy = self._get_routing_accuracy()
            if routing_accuracy < 0.9:
                insight = CollaborationInsight(
                    insight_id=f"routing_optimization_{datetime.datetime.now().strftime('%Y%m%d')}",
                    category="workflow_optimization",
                    title="タスクルーティング精度向上機会",
                    description=f"ルーティング精度{routing_accuracy:.1%}を90%以上に向上可能",
                    impact_level="medium",
                    recommended_actions=[
                        "ルーティングルールの最適化",
                        "機械学習による精度向上",
                        "フィードバックループの強化"
                    ],
                    estimated_benefit="タスク処理効率10-15%向上",
                    implementation_difficulty="medium"
                )
                insights.append(insight)

        except Exception as e:
            logger.warning(f"⚠️ 最適化インサイト生成エラー: {e}")

        return insights

    def _generate_historical_summary(self) -> Dict[str, Any]:
        """履歴サマリー生成"""

        summary = {
            "timeframe": "30d",
            "total_tasks_processed": 0,
            "average_safety_score": 0.0,
            "improvement_rate": 0.0,
            "major_milestones": [],
            "performance_comparison": {
                "last_30d": {"safety_score": 0.0, "success_rate": 0.0},
                "previous_30d": {"safety_score": 0.0, "success_rate": 0.0}
            },
            "optimization_impact": {
                "total_optimizations": 0,
                "estimated_efficiency_gain": 0.0,
                "cost_savings": 0.0
            }
        }

        try:
            # 効率メトリクス履歴分析
            efficiency_file = self.collaboration_dir / "efficiency_metrics.json"
            if efficiency_file.exists():
                with open(efficiency_file, 'r', encoding='utf-8') as f:
                    efficiency_data = json.load(f)

                if efficiency_data:
                    # 過去30日間のデータ
                    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)
                    recent_data = []

                    for entry in efficiency_data:
                        try:
                            entry_date = datetime.datetime.fromisoformat(entry["timestamp"])
                            if entry_date >= cutoff_date:
                                recent_data.append(entry)
                        except Exception:
                            continue

                    if recent_data:
                        summary["total_tasks_processed"] = len(recent_data)

                        safety_scores = [d["overall_safety_score"] for d in recent_data]
                        summary["average_safety_score"] = statistics.mean(safety_scores)

                        # 改善率計算
                        if len(safety_scores) >= 2:
                            first_half = safety_scores[:len(safety_scores)//2]
                            second_half = safety_scores[len(safety_scores)//2:]

                            if first_half and second_half:
                                improvement = statistics.mean(second_half) - statistics.mean(first_half)
                                summary["improvement_rate"] = improvement

            # マイルストーン検出
            if summary["average_safety_score"] >= 70:
                summary["major_milestones"].append("協業安全性スコア70点突破")

            if summary["improvement_rate"] > 5:
                summary["major_milestones"].append("顕著な品質向上トレンド")

        except Exception as e:
            logger.warning(f"⚠️ 履歴サマリー生成エラー: {e}")

        return summary

    def _get_current_safety_score(self) -> float:
        """現在の安全性スコア取得"""

        try:
            efficiency_file = self.collaboration_dir / "efficiency_metrics.json"
            if efficiency_file.exists():
                with open(efficiency_file, 'r', encoding='utf-8') as f:
                    efficiency_data = json.load(f)

                if efficiency_data:
                    return efficiency_data[-1]["overall_safety_score"]
        except Exception:
            pass

        return 40.0  # デフォルト値

    def _get_current_failsafe_rate(self) -> float:
        """現在のフェイルセーフ使用率取得"""

        try:
            failsafe_file = self.monitoring_dir / "failsafe_usage.json"
            if failsafe_file.exists():
                with open(failsafe_file, 'r', encoding='utf-8') as f:
                    failsafe_data = json.load(f)

                if failsafe_data:
                    recent_data = failsafe_data[-3:]
                    total_failsafe = sum(entry["failsafe_count"] for entry in recent_data)
                    total_files = sum(entry["total_files"] for entry in recent_data)

                    if total_files > 0:
                        return total_failsafe / total_files
        except Exception:
            pass

        return 0.5  # デフォルト値

    def _get_current_success_rate(self) -> float:
        """現在の成功率取得"""

        try:
            verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"
            if verification_file.exists():
                with open(verification_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)

                if verification_data:
                    return verification_data[-1]["success_rates"]["overall_success_rate"]
        except Exception:
            pass

        return 0.5  # デフォルト値

    def _get_layer1_success_rate(self) -> float:
        """Layer1成功率取得"""

        try:
            verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"
            if verification_file.exists():
                with open(verification_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)

                if verification_data:
                    return verification_data[-1]["success_rates"]["layer1_success_rate"]
        except Exception:
            pass

        return 0.5  # デフォルト値

    def _get_routing_accuracy(self) -> float:
        """ルーティング精度取得"""

        try:
            routing_file = self.collaboration_dir / "routing_decisions.json"
            if routing_file.exists():
                with open(routing_file, 'r', encoding='utf-8') as f:
                    routing_data = json.load(f)

                if routing_data:
                    recent_decisions = routing_data[-10:]
                    confidence_scores = [d["confidence_score"] for d in recent_decisions]

                    if confidence_scores:
                        return statistics.mean(confidence_scores)
        except Exception:
            pass

        return 0.8  # デフォルト値

    def _save_dashboard_data(self, dashboard_data: DashboardData) -> None:
        """ダッシュボードデータ保存"""

        try:
            with open(self.dashboard_data_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(dashboard_data), f, indent=2, ensure_ascii=False, default=str)

            logger.debug("✅ ダッシュボードデータ保存完了")

        except Exception as e:
            logger.error(f"❌ ダッシュボードデータ保存エラー: {e}")

    def _save_alerts(self, alerts: List[DashboardAlert]) -> None:
        """アラート保存"""

        try:
            alerts_data = [asdict(alert) for alert in alerts]

            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alerts_data, f, indent=2, ensure_ascii=False, default=str)

            self.active_alerts = alerts

        except Exception as e:
            logger.error(f"❌ アラート保存エラー: {e}")

    def _load_alerts(self) -> List[DashboardAlert]:
        """アラート読み込み"""

        if not self.alerts_file.exists():
            return []

        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)

            alerts = []
            for data in alerts_data:
                alert = DashboardAlert(**data)
                alerts.append(alert)

            return alerts

        except Exception as e:
            logger.warning(f"⚠️ アラート読み込みエラー: {e}")
            return []

    def _load_insights_history(self) -> List[CollaborationInsight]:
        """インサイト履歴読み込み"""

        if not self.insights_file.exists():
            return []

        try:
            with open(self.insights_file, 'r', encoding='utf-8') as f:
                insights_data = json.load(f)

            insights = []
            for data in insights_data:
                insight = CollaborationInsight(**data)
                insights.append(insight)

            return insights[-20:]  # 最新20件

        except Exception as e:
            logger.warning(f"⚠️ インサイト履歴読み込みエラー: {e}")
            return []

    def _load_trends_cache(self) -> Dict[str, Any]:
        """トレンドキャッシュ読み込み"""

        if not self.trends_cache_file.exists():
            return {}

        try:
            with open(self.trends_cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ トレンドキャッシュ読み込みエラー: {e}")
            return {}

    def _create_fallback_dashboard_data(self) -> DashboardData:
        """フォールバックダッシュボードデータ"""

        return DashboardData(
            timestamp=datetime.datetime.now().isoformat(),
            overview_metrics={
                "collaboration_safety_score": 40.0,
                "current_safety_level": "low",
                "system_status": {"operational": True, "error_rate": 0.0}
            },
            collaboration_metrics={
                "layer_performance": {"layer1_success_rate": 0.5},
                "failsafe_metrics": {"current_usage_rate": 0.5}
            },
            performance_trends=[],
            quality_indicators={"code_quality_score": 0.5},
            active_alerts=[],
            optimization_insights=[],
            historical_summary={"total_tasks_processed": 0}
        )

    def export_dashboard_report(self, format_type: str = "json") -> str:
        """ダッシュボードレポート出力

        Args:
            format_type: 出力形式 ("json", "html", "csv")

        Returns:
            str: 出力ファイルパス
        """

        logger.info(f"📄 ダッシュボードレポート出力開始: {format_type}")

        try:
            # 最新ダッシュボードデータ生成
            dashboard_data = self.generate_dashboard_data()

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

            if format_type == "json":
                output_file = self.dashboard_dir / f"dashboard_report_{timestamp}.json"

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(dashboard_data), f, indent=2, ensure_ascii=False, default=str)

            elif format_type == "html":
                output_file = self.dashboard_dir / f"dashboard_report_{timestamp}.html"
                html_content = self._generate_html_report(dashboard_data)

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)

            else:
                raise ValueError(f"未対応の出力形式: {format_type}")

            logger.info(f"✅ ダッシュボードレポート出力完了: {output_file}")

            return str(output_file)

        except Exception as e:
            logger.error(f"❌ ダッシュボードレポート出力エラー: {e}")
            return ""

    def _generate_html_report(self, dashboard_data: DashboardData) -> str:
        """HTMLレポート生成"""

        html_template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>協業ダッシュボードレポート</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #333; }}
        .metric-card {{ background-color: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #007bff; }}
        .alert-critical {{ border-left-color: #dc3545; }}
        .alert-warning {{ border-left-color: #ffc107; }}
        .alert-info {{ border-left-color: #17a2b8; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .trend-improving {{ color: #28a745; }}
        .trend-declining {{ color: #dc3545; }}
        .trend-stable {{ color: #6c757d; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .progress-bar {{ width: 100%; background-color: #e9ecef; border-radius: 4px; height: 20px; }}
        .progress-fill {{ height: 100%; background-color: #007bff; border-radius: 4px; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Gemini×Claude 協業ダッシュボードレポート</h1>
        <p><strong>生成日時:</strong> {dashboard_data.timestamp}</p>

        <h2>📊 概要メトリクス</h2>
        <div class="metric-card">
            <h3>協業安全性スコア</h3>
            <div class="metric-value">{dashboard_data.overview_metrics.get('collaboration_safety_score', 0):.1f}/100</div>
            <p>目標: 75.0以上 | 現在レベル: {dashboard_data.overview_metrics.get('current_safety_level', 'unknown')}</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {min(dashboard_data.overview_metrics.get('collaboration_safety_score', 0), 100)}%"></div>
            </div>
        </div>

        <h2>🎯 協業パフォーマンス</h2>
        <table>
            <tr>
                <th>指標</th>
                <th>現在値</th>
                <th>目標値</th>
                <th>状態</th>
            </tr>
            <tr>
                <td>Layer1成功率</td>
                <td>{dashboard_data.collaboration_metrics.get('layer_performance', {}).get('layer1_success_rate', 0):.1%}</td>
                <td>80%以上</td>
                <td>{'✅' if dashboard_data.collaboration_metrics.get('layer_performance', {}).get('layer1_success_rate', 0) >= 0.8 else '⚠️'}</td>
            </tr>
            <tr>
                <td>フェイルセーフ使用率</td>
                <td>{dashboard_data.collaboration_metrics.get('failsafe_metrics', {}).get('current_usage_rate', 0):.1%}</td>
                <td>20%以下</td>
                <td>{'✅' if dashboard_data.collaboration_metrics.get('failsafe_metrics', {}).get('current_usage_rate', 0) <= 0.2 else '⚠️'}</td>
            </tr>
        </table>

        <h2>📈 パフォーマンストレンド</h2>
        {self._generate_trends_html(dashboard_data.performance_trends)}

        <h2>🚨 アクティブアラート</h2>
        {self._generate_alerts_html(dashboard_data.active_alerts)}

        <h2>💡 最適化インサイト</h2>
        {self._generate_insights_html(dashboard_data.optimization_insights)}

        <p style="text-align: center; margin-top: 40px; color: #6c757d;">
            <em>このレポートはEnhancedCollaborationDashboardシステムにより自動生成されました</em>
        </p>
    </div>
</body>
</html>
"""
        return html_template

    def _generate_trends_html(self, trends: List[MetricTrend]) -> str:
        """トレンドHTML生成"""

        if not trends:
            return "<p>トレンドデータがありません</p>"

        html = "<div>"
        for trend in trends:
            trend_class = f"trend-{trend.trend_direction.value}"
            direction_icon = {
                TrendDirection.IMPROVING: "📈",
                TrendDirection.DECLINING: "📉",
                TrendDirection.STABLE: "➡️",
                TrendDirection.VOLATILE: "📊"
            }.get(trend.trend_direction, "➡️")

            html += f"""
            <div class="metric-card">
                <h4>{direction_icon} {trend.metric_name}</h4>
                <p class="{trend_class}">
                    現在値: {trend.current_value:.3f} |
                    変化率: {trend.change_percentage:+.1f}% |
                    信頼度: {trend.confidence_level:.1%}
                </p>
            </div>
            """

        html += "</div>"
        return html

    def _generate_alerts_html(self, alerts: List[DashboardAlert]) -> str:
        """アラートHTML生成"""

        if not alerts:
            return "<p>アクティブなアラートはありません ✅</p>"

        html = "<div>"
        for alert in alerts:
            alert_class = f"alert-{alert.level.value}"
            level_icon = {
                AlertLevel.CRITICAL: "🚨",
                AlertLevel.ERROR: "❌",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.INFO: "ℹ️"
            }.get(alert.level, "ℹ️")

            html += f"""
            <div class="metric-card {alert_class}">
                <h4>{level_icon} {alert.title}</h4>
                <p>{alert.message}</p>
                <small>セクション: {alert.section.value} | 時刻: {alert.timestamp}</small>
            </div>
            """

        html += "</div>"
        return html

    def _generate_insights_html(self, insights: List[CollaborationInsight]) -> str:
        """インサイトHTML生成"""

        if not insights:
            return "<p>最適化インサイトがありません</p>"

        html = "<div>"
        for insight in insights:
            impact_icon = {
                "critical": "🚨",
                "high": "🔥",
                "medium": "⚡",
                "low": "💡"
            }.get(insight.impact_level, "💡")

            html += f"""
            <div class="metric-card">
                <h4>{impact_icon} {insight.title}</h4>
                <p>{insight.description}</p>
                <p><strong>期待効果:</strong> {insight.estimated_benefit}</p>
                <p><strong>推奨アクション:</strong></p>
                <ul>
            """

            for action in insight.recommended_actions:
                html += f"<li>{action}</li>"

            html += f"""
                </ul>
                <small>実装難易度: {insight.implementation_difficulty}</small>
            </div>
            """

        html += "</div>"
        return html


def main() -> None:
    """テスト実行"""
    dashboard = EnhancedCollaborationDashboard()

    # ダッシュボードデータ生成
    data = dashboard.generate_dashboard_data()
    print(f"協業安全性スコア: {data.overview_metrics['collaboration_safety_score']:.1f}")
    print(f"アクティブアラート: {len(data.active_alerts)}件")
    print(f"最適化インサイト: {len(data.optimization_insights)}件")

    # HTMLレポート出力
    report_file = dashboard.export_dashboard_report("html")
    if report_file:
        print(f"HTMLレポート生成: {report_file}")


if __name__ == "__main__":
    main()
