#!/usr/bin/env python3
"""
CollaborationEfficiencyMonitor - Issue #860対応
Gemini×Claude協業効率の包括的監視・分析システム

協業安全性を40/100から75-80/100に向上させるための
リアルタイム監視・ボトルネック検出・最適化推奨システム
"""

import json
import datetime
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import os

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class CollaborationSafetyLevel(Enum):
    """協業安全性レベル"""
    CRITICAL = "critical"      # 0-30: 緊急対応必要
    LOW = "low"               # 31-50: 改善必要
    MODERATE = "moderate"     # 51-70: 改善推奨
    GOOD = "good"             # 71-85: 良好
    EXCELLENT = "excellent"   # 86-100: 優秀


class BottleneckType(Enum):
    """ボトルネックタイプ"""
    LAYER1_SYNTAX = "layer1_syntax_validation"
    LAYER2_QUALITY = "layer2_quality_check"
    LAYER3_APPROVAL = "layer3_claude_approval"
    INTEGRATION = "integration_test"
    TASK_ROUTING = "task_routing_decision"
    FAILSAFE_OVERUSE = "failsafe_mechanism_overuse"
    PROCESSING_TIME = "processing_time_exceeded"
    TOKEN_EFFICIENCY = "token_efficiency_degraded"


@dataclass
class CollaborationMetrics:
    """協業メトリクス"""
    timestamp: str
    overall_safety_score: float  # 0-100
    safety_level: CollaborationSafetyLevel
    task_success_rate: float  # 0.0-1.0
    layer_success_rates: Dict[str, float]
    failsafe_usage_rate: float  # 0.0-1.0
    average_processing_time: float  # seconds
    token_efficiency: float  # 0.0-1.0
    total_tasks_processed: int
    detected_bottlenecks: List[BottleneckType]
    recommendations: List[str]


@dataclass
class EfficiencyTrend:
    """効率トレンド分析"""
    timeframe: str  # "1h", "24h", "7d", "30d"
    safety_score_trend: float  # positive=改善, negative=悪化
    success_rate_trend: float
    processing_time_trend: float
    failsafe_usage_trend: float
    critical_issues: List[str]
    improvement_opportunities: List[str]


class CollaborationEfficiencyMonitor:
    """協業効率監視システム

    Gemini×Claude協業の包括的監視・分析・最適化推奨を行う
    Issue #860: 協業安全性40/100 → 75-80/100達成のため
    """

    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.monitoring_dir = self.postbox_dir / "monitoring"
        self.collaboration_dir = self.postbox_dir / "collaboration"

        # 監視データディレクトリ作成
        self.collaboration_dir.mkdir(exist_ok=True)

        self.metrics_file = self.collaboration_dir / "efficiency_metrics.json"
        self.trends_file = self.collaboration_dir / "efficiency_trends.json"
        self.alerts_file = self.collaboration_dir / "efficiency_alerts.json"

        # 目標値設定 (Issue #860要件)
        self.TARGET_SAFETY_SCORE = 75.0  # 最小目標
        self.TARGET_SUCCESS_RATE = 0.70  # 70%以上
        self.TARGET_PROCESSING_TIME = 2.0  # 2秒以内
        self.TARGET_FAILSAFE_RATE = 0.30  # 30%以下
        self.TARGET_TOKEN_EFFICIENCY = 0.99  # 99%以上

        logger.info("🔍 CollaborationEfficiencyMonitor 初期化完了")

    def collect_current_metrics(self) -> CollaborationMetrics:
        """現在の協業メトリクス収集"""

        logger.info("📊 協業メトリクス収集開始")

        try:
            # 3層検証データ収集
            verification_data = self._load_verification_metrics()

            # フェイルセーフデータ収集
            failsafe_data = self._load_failsafe_metrics()

            # コスト・トークンデータ収集
            cost_data = self._load_cost_metrics()

            # メトリクス計算
            metrics = self._calculate_comprehensive_metrics(
                verification_data, failsafe_data, cost_data
            )

            # ボトルネック検出
            bottlenecks = self._detect_bottlenecks(metrics)
            metrics.detected_bottlenecks = bottlenecks

            # 推奨事項生成
            recommendations = self._generate_recommendations(metrics)
            metrics.recommendations = recommendations

            # メトリクス保存
            self._save_metrics(metrics)

            logger.info(f"✅ 協業メトリクス収集完了: 安全性スコア {metrics.overall_safety_score:.1f}/100")

            return metrics

        except Exception as e:
            logger.error(f"❌ 協業メトリクス収集エラー: {e}")
            # フォールバック: 基本メトリクス
            return self._create_fallback_metrics()

    def _load_verification_metrics(self) -> Dict[str, Any]:
        """3層検証メトリクス読み込み"""

        verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"

        if not verification_file.exists():
            logger.warning("⚠️ 3層検証メトリクスファイルが見つかりません")
            return {}

        try:
            with open(verification_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 最新データのみ使用（直近5件）
            recent_data = data[-5:] if len(data) > 5 else data

            return {
                "recent_runs": recent_data,
                "total_runs": len(data),
                "data_available": True
            }

        except Exception as e:
            logger.error(f"❌ 3層検証メトリクス読み込みエラー: {e}")
            return {"data_available": False}

    def _load_failsafe_metrics(self) -> Dict[str, Any]:
        """フェイルセーフメトリクス読み込み"""

        failsafe_file = self.monitoring_dir / "failsafe_usage.json"

        if not failsafe_file.exists():
            logger.warning("⚠️ フェイルセーフメトリクスファイルが見つかりません")
            return {}

        try:
            with open(failsafe_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 最新データのみ使用
            recent_data = data[-10:] if len(data) > 10 else data

            return {
                "recent_usage": recent_data,
                "total_records": len(data),
                "data_available": True
            }

        except Exception as e:
            logger.error(f"❌ フェイルセーフメトリクス読み込みエラー: {e}")
            return {"data_available": False}

    def _load_cost_metrics(self) -> Dict[str, Any]:
        """コスト・トークンメトリクス読み込み"""

        cost_file = self.monitoring_dir / "cost_tracking.json"

        if not cost_file.exists():
            logger.warning("⚠️ コストトラッキングファイルが見つかりません")
            return {}

        try:
            with open(cost_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "total_cost": data.get("total_cost", 0.0),
                "tasks": data.get("tasks", []),
                "data_available": True
            }

        except Exception as e:
            logger.error(f"❌ コストメトリクス読み込みエラー: {e}")
            return {"data_available": False}

    def _calculate_comprehensive_metrics(self, verification_data: Dict[str, Any],
                                       failsafe_data: Dict[str, Any],
                                       cost_data: Dict[str, Any]) -> CollaborationMetrics:
        """包括的メトリクス計算"""

        timestamp = datetime.datetime.now().isoformat()

        # 3層検証成功率計算
        layer_success_rates = self._calculate_layer_success_rates(verification_data)
        overall_success_rate = self._calculate_overall_success_rate(layer_success_rates)

        # フェイルセーフ使用率計算
        failsafe_usage_rate = self._calculate_failsafe_usage_rate(failsafe_data)

        # 処理時間計算
        avg_processing_time = self._calculate_processing_time(verification_data)

        # トークン効率計算
        token_efficiency = self._calculate_token_efficiency(cost_data)

        # 協業安全性スコア計算 (Issue #860核心指標)
        safety_score = self._calculate_safety_score(
            overall_success_rate, failsafe_usage_rate,
            avg_processing_time, token_efficiency
        )

        # 安全性レベル判定
        safety_level = self._determine_safety_level(safety_score)

        # タスク処理数
        total_tasks = self._count_total_tasks(verification_data, failsafe_data)

        return CollaborationMetrics(
            timestamp=timestamp,
            overall_safety_score=safety_score,
            safety_level=safety_level,
            task_success_rate=overall_success_rate,
            layer_success_rates=layer_success_rates,
            failsafe_usage_rate=failsafe_usage_rate,
            average_processing_time=avg_processing_time,
            token_efficiency=token_efficiency,
            total_tasks_processed=total_tasks,
            detected_bottlenecks=[],  # _detect_bottlenecksで設定
            recommendations=[]        # _generate_recommendationsで設定
        )

    def _calculate_layer_success_rates(self, verification_data: Dict[str, Any]) -> Dict[str, float]:
        """各層の成功率計算"""

        if not verification_data.get("data_available", False):
            return {
                "layer1_success_rate": 0.0,
                "layer2_success_rate": 0.0,
                "layer3_success_rate": 0.0,
                "integration_success_rate": 0.0
            }

        recent_runs = verification_data.get("recent_runs", [])

        if not recent_runs:
            return {
                "layer1_success_rate": 0.0,
                "layer2_success_rate": 0.0,
                "layer3_success_rate": 0.0,
                "integration_success_rate": 0.0
            }

        # 各層の成功率を平均化
        layer1_rates = [run["success_rates"]["layer1_success_rate"] for run in recent_runs]
        layer2_rates = [run["success_rates"]["layer2_success_rate"] for run in recent_runs]
        layer3_rates = [run["success_rates"]["layer3_approval_rate"] for run in recent_runs]
        integration_rates = [run["success_rates"]["integration_success_rate"] for run in recent_runs]

        return {
            "layer1_success_rate": statistics.mean(layer1_rates) if layer1_rates else 0.0,
            "layer2_success_rate": statistics.mean(layer2_rates) if layer2_rates else 0.0,
            "layer3_success_rate": statistics.mean(layer3_rates) if layer3_rates else 0.0,
            "integration_success_rate": statistics.mean(integration_rates) if integration_rates else 0.0
        }

    def _calculate_overall_success_rate(self, layer_rates: Dict[str, float]) -> float:
        """全体成功率計算"""

        # 重み付き平均 (Layer2品質が最重要、Layer3 Claude承認が次重要)
        weights = {
            "layer1_success_rate": 0.2,
            "layer2_success_rate": 0.3,
            "layer3_success_rate": 0.3,
            "integration_success_rate": 0.2
        }

        weighted_sum = sum(layer_rates[key] * weights[key] for key in weights.keys())

        return min(weighted_sum, 1.0)  # 1.0で上限制限

    def _calculate_failsafe_usage_rate(self, failsafe_data: Dict[str, Any]) -> float:
        """フェイルセーフ使用率計算"""

        if not failsafe_data.get("data_available", False):
            return 0.0

        recent_usage = failsafe_data.get("recent_usage", [])

        if not recent_usage:
            return 0.0

        # フェイルセーフ使用頻度 (件数 / 総ファイル数)
        total_failsafe_count = sum(usage["failsafe_count"] for usage in recent_usage)
        total_files_processed = sum(usage["total_files"] for usage in recent_usage)

        if total_files_processed == 0:
            return 0.0

        # フェイルセーフ率 = 使用回数 / 処理ファイル数
        usage_rate = total_failsafe_count / total_files_processed

        return min(usage_rate, 1.0)  # 1.0で上限制限

    def _calculate_processing_time(self, verification_data: Dict[str, Any]) -> float:
        """平均処理時間計算"""

        if not verification_data.get("data_available", False):
            return 0.0

        recent_runs = verification_data.get("recent_runs", [])

        if not recent_runs:
            return 0.0

        execution_times = [run["execution_time"] for run in recent_runs]

        return statistics.mean(execution_times) if execution_times else 0.0

    def _calculate_token_efficiency(self, cost_data: Dict[str, Any]) -> float:
        """トークン効率計算"""

        if not cost_data.get("data_available", False):
            return 0.99  # デフォルト高効率

        total_cost = cost_data.get("total_cost", 0.0)
        tasks = cost_data.get("tasks", [])

        if not tasks:
            return 0.99

        # 平均トークン効率を推定
        # コストが低い = 効率が高い と仮定
        if total_cost <= 0.02:  # $0.02以下は非常に効率的
            return 0.99
        elif total_cost <= 0.05:  # $0.05以下は効率的
            return 0.95
        elif total_cost <= 0.10:  # $0.10以下は普通
            return 0.90
        else:
            return 0.85  # それ以上は改善余地あり

    def _calculate_safety_score(self, success_rate: float, failsafe_rate: float,
                              processing_time: float, token_efficiency: float) -> float:
        """協業安全性スコア計算 (Issue #860核心指標)

        目標: 40/100 → 75-80/100
        """

        # 成功率スコア (40点満点)
        success_score = success_rate * 40

        # フェイルセーフスコア (25点満点) - 使用率が低いほど高スコア
        failsafe_score = max(0, (1.0 - failsafe_rate) * 25)

        # 処理時間スコア (20点満点) - 2秒以内で満点
        if processing_time <= 2.0:
            time_score = 20
        elif processing_time <= 5.0:
            time_score = 20 * (5.0 - processing_time) / 3.0
        else:
            time_score = 0

        # トークン効率スコア (15点満点)
        efficiency_score = token_efficiency * 15

        total_score = success_score + failsafe_score + time_score + efficiency_score

        return min(total_score, 100.0)  # 100点満点

    def _determine_safety_level(self, safety_score: float) -> CollaborationSafetyLevel:
        """安全性レベル判定"""

        if safety_score >= 86:
            return CollaborationSafetyLevel.EXCELLENT
        elif safety_score >= 71:
            return CollaborationSafetyLevel.GOOD
        elif safety_score >= 51:
            return CollaborationSafetyLevel.MODERATE
        elif safety_score >= 31:
            return CollaborationSafetyLevel.LOW
        else:
            return CollaborationSafetyLevel.CRITICAL

    def _count_total_tasks(self, verification_data: Dict[str, Any],
                          failsafe_data: Dict[str, Any]) -> int:
        """総タスク処理数計算"""

        verification_count = 0
        if verification_data.get("data_available", False):
            verification_count = verification_data.get("total_runs", 0)

        failsafe_count = 0
        if failsafe_data.get("data_available", False):
            failsafe_count = failsafe_data.get("total_records", 0)

        return max(verification_count, failsafe_count)

    def _detect_bottlenecks(self, metrics: CollaborationMetrics) -> List[BottleneckType]:
        """協業ボトルネック検出"""

        bottlenecks = []

        # Layer1構文検証ボトルネック
        if metrics.layer_success_rates["layer1_success_rate"] < 0.8:
            bottlenecks.append(BottleneckType.LAYER1_SYNTAX)

        # Layer2品質チェックボトルネック
        if metrics.layer_success_rates["layer2_success_rate"] < 0.9:
            bottlenecks.append(BottleneckType.LAYER2_QUALITY)

        # Layer3 Claude承認ボトルネック
        if metrics.layer_success_rates["layer3_success_rate"] < 0.7:
            bottlenecks.append(BottleneckType.LAYER3_APPROVAL)

        # 統合テストボトルネック
        if metrics.layer_success_rates["integration_success_rate"] < 0.8:
            bottlenecks.append(BottleneckType.INTEGRATION)

        # フェイルセーフ過使用ボトルネック
        if metrics.failsafe_usage_rate > self.TARGET_FAILSAFE_RATE:
            bottlenecks.append(BottleneckType.FAILSAFE_OVERUSE)

        # 処理時間ボトルネック
        if metrics.average_processing_time > self.TARGET_PROCESSING_TIME:
            bottlenecks.append(BottleneckType.PROCESSING_TIME)

        # トークン効率ボトルネック
        if metrics.token_efficiency < self.TARGET_TOKEN_EFFICIENCY:
            bottlenecks.append(BottleneckType.TOKEN_EFFICIENCY)

        return bottlenecks

    def _generate_recommendations(self, metrics: CollaborationMetrics) -> List[str]:
        """最適化推奨事項生成"""

        recommendations = []

        # 安全性スコア別推奨
        if metrics.overall_safety_score < 50:
            recommendations.append("🚨 緊急: 協業安全性が危険レベルです。即座の改善が必要です")
            recommendations.append("3層検証システムの全面見直しを実施してください")
        elif metrics.overall_safety_score < self.TARGET_SAFETY_SCORE:
            recommendations.append("⚠️ 協業安全性が目標値未達です。システム最適化を推奨します")

        # ボトルネック別推奨
        for bottleneck in metrics.detected_bottlenecks:
            if bottleneck == BottleneckType.LAYER1_SYNTAX:
                recommendations.append("📝 Layer1構文検証の改善: 事前バリデーション強化を推奨")
            elif bottleneck == BottleneckType.LAYER2_QUALITY:
                recommendations.append("🔍 Layer2品質チェックの改善: 品質基準見直しを推奨")
            elif bottleneck == BottleneckType.LAYER3_APPROVAL:
                recommendations.append("👤 Layer3 Claude承認の改善: 承認プロセス最適化を推奨")
            elif bottleneck == BottleneckType.FAILSAFE_OVERUSE:
                recommendations.append("🛡️ フェイルセーフ過使用: 予防的品質チェック強化を推奨")
            elif bottleneck == BottleneckType.PROCESSING_TIME:
                recommendations.append("⏱️ 処理時間改善: 並列処理・最適化アルゴリズム導入を推奨")

        # 成功率別推奨
        if metrics.task_success_rate < self.TARGET_SUCCESS_RATE:
            recommendations.append(f"📈 タスク成功率向上: 現在{metrics.task_success_rate:.1%} → 目標70%+")

        # ポジティブフィードバック
        if metrics.overall_safety_score >= self.TARGET_SAFETY_SCORE:
            recommendations.append("✅ 協業安全性が目標値を達成しています！")

        if metrics.token_efficiency >= self.TARGET_TOKEN_EFFICIENCY:
            recommendations.append("💰 トークン効率が優秀です！コスト最適化が成功しています")

        return recommendations

    def _save_metrics(self, metrics: CollaborationMetrics) -> None:
        """メトリクス保存"""

        try:
            # 既存メトリクス読み込み
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    all_metrics = json.load(f)
            else:
                all_metrics = []

            # 新しいメトリクス追加
            all_metrics.append(asdict(metrics))

            # 最新100件のみ保持
            if len(all_metrics) > 100:
                all_metrics = all_metrics[-100:]

            # 保存
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(all_metrics, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"✅ 協業メトリクス保存完了: {self.metrics_file}")

        except Exception as e:
            logger.error(f"❌ メトリクス保存エラー: {e}")

    def _create_fallback_metrics(self) -> CollaborationMetrics:
        """フォールバックメトリクス作成"""

        return CollaborationMetrics(
            timestamp=datetime.datetime.now().isoformat(),
            overall_safety_score=40.0,  # 現状ベースライン
            safety_level=CollaborationSafetyLevel.LOW,
            task_success_rate=0.5,
            layer_success_rates={
                "layer1_success_rate": 0.5,
                "layer2_success_rate": 0.8,
                "layer3_success_rate": 0.6,
                "integration_success_rate": 0.7
            },
            failsafe_usage_rate=0.6,
            average_processing_time=1.5,
            token_efficiency=0.99,
            total_tasks_processed=0,
            detected_bottlenecks=[BottleneckType.LAYER1_SYNTAX, BottleneckType.FAILSAFE_OVERUSE],
            recommendations=["📊 データ不足: 協業メトリクス収集を継続してください"]
        )

    def analyze_efficiency_trends(self, timeframe: str = "24h") -> EfficiencyTrend:
        """効率トレンド分析"""

        logger.info(f"📈 効率トレンド分析開始: {timeframe}")

        try:
            # 過去メトリクス読み込み
            if not self.metrics_file.exists():
                logger.warning("⚠️ 過去メトリクスデータが不足しています")
                return self._create_fallback_trend(timeframe)

            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                all_metrics = json.load(f)

            if len(all_metrics) < 2:
                logger.warning("⚠️ トレンド分析に十分なデータがありません")
                return self._create_fallback_trend(timeframe)

            # 時間範囲でフィルタリング
            filtered_metrics = self._filter_metrics_by_timeframe(all_metrics, timeframe)

            if len(filtered_metrics) < 2:
                logger.warning(f"⚠️ {timeframe}の範囲に十分なデータがありません")
                return self._create_fallback_trend(timeframe)

            # トレンド計算
            trend = self._calculate_trends(filtered_metrics, timeframe)

            # トレンド保存
            self._save_trend(trend)

            logger.info(f"✅ 効率トレンド分析完了: {timeframe}")

            return trend

        except Exception as e:
            logger.error(f"❌ 効率トレンド分析エラー: {e}")
            return self._create_fallback_trend(timeframe)

    def _filter_metrics_by_timeframe(self, all_metrics: List[Dict], timeframe: str) -> List[Dict]:
        """時間範囲でメトリクスフィルタリング"""

        now = datetime.datetime.now()

        if timeframe == "1h":
            cutoff = now - datetime.timedelta(hours=1)
        elif timeframe == "24h":
            cutoff = now - datetime.timedelta(hours=24)
        elif timeframe == "7d":
            cutoff = now - datetime.timedelta(days=7)
        elif timeframe == "30d":
            cutoff = now - datetime.timedelta(days=30)
        else:
            # デフォルト24時間
            cutoff = now - datetime.timedelta(hours=24)

        filtered = []
        for metric in all_metrics:
            try:
                metric_time = datetime.datetime.fromisoformat(metric["timestamp"])
                if metric_time >= cutoff:
                    filtered.append(metric)
            except Exception:
                continue  # タイムスタンプ解析エラーは無視

        return filtered

    def _calculate_trends(self, metrics: List[Dict], timeframe: str) -> EfficiencyTrend:
        """トレンド計算"""

        # 最初と最後のメトリクスで比較
        first_metric = metrics[0]
        last_metric = metrics[-1]

        # 各指標のトレンド計算 (改善=positive, 悪化=negative)
        safety_trend = last_metric["overall_safety_score"] - first_metric["overall_safety_score"]
        success_trend = last_metric["task_success_rate"] - first_metric["task_success_rate"]
        processing_trend = first_metric["average_processing_time"] - last_metric["average_processing_time"]  # 時間短縮=positive
        failsafe_trend = first_metric["failsafe_usage_rate"] - last_metric["failsafe_usage_rate"]  # 使用率減少=positive

        # 重要な問題検出
        critical_issues = []
        improvement_opportunities = []

        # 安全性スコアが悪化している場合
        if safety_trend < -5:
            critical_issues.append("協業安全性スコアが大幅に悪化しています")

        # 成功率が悪化している場合
        if success_trend < -0.1:
            critical_issues.append("タスク成功率が悪化傾向にあります")

        # フェイルセーフ使用率が増加している場合
        if failsafe_trend < -0.1:
            critical_issues.append("フェイルセーフ使用率が増加しています")

        # 改善機会の特定
        if safety_trend > 0:
            improvement_opportunities.append("協業安全性が改善傾向にあります")

        if success_trend > 0:
            improvement_opportunities.append("タスク成功率が向上しています")

        if processing_trend > 0:
            improvement_opportunities.append("処理時間が短縮されています")

        return EfficiencyTrend(
            timeframe=timeframe,
            safety_score_trend=safety_trend,
            success_rate_trend=success_trend,
            processing_time_trend=processing_trend,
            failsafe_usage_trend=failsafe_trend,
            critical_issues=critical_issues,
            improvement_opportunities=improvement_opportunities
        )

    def _create_fallback_trend(self, timeframe: str) -> EfficiencyTrend:
        """フォールバックトレンド作成"""

        return EfficiencyTrend(
            timeframe=timeframe,
            safety_score_trend=0.0,
            success_rate_trend=0.0,
            processing_time_trend=0.0,
            failsafe_usage_trend=0.0,
            critical_issues=["データ不足: トレンド分析に十分なデータがありません"],
            improvement_opportunities=["継続的なメトリクス収集でトレンド分析が可能になります"]
        )

    def _save_trend(self, trend: EfficiencyTrend) -> None:
        """トレンド保存"""

        try:
            # 既存トレンド読み込み
            if self.trends_file.exists():
                with open(self.trends_file, 'r', encoding='utf-8') as f:
                    all_trends = json.load(f)
            else:
                all_trends = []

            # 新しいトレンド追加
            trend_dict = asdict(trend)
            trend_dict["timestamp"] = datetime.datetime.now().isoformat()
            all_trends.append(trend_dict)

            # 最新50件のみ保持
            if len(all_trends) > 50:
                all_trends = all_trends[-50:]

            # 保存
            with open(self.trends_file, 'w', encoding='utf-8') as f:
                json.dump(all_trends, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ 効率トレンド保存完了: {self.trends_file}")

        except Exception as e:
            logger.error(f"❌ トレンド保存エラー: {e}")

    def generate_efficiency_report(self) -> Dict[str, Any]:
        """協業効率レポート生成"""

        logger.info("📄 協業効率レポート生成開始")

        try:
            # 現在のメトリクス取得
            current_metrics = self.collect_current_metrics()

            # トレンド分析
            trends_24h = self.analyze_efficiency_trends("24h")
            trends_7d = self.analyze_efficiency_trends("7d")

            # 包括的レポート作成
            report = {
                "report_timestamp": datetime.datetime.now().isoformat(),
                "collaboration_status": {
                    "current_safety_score": current_metrics.overall_safety_score,
                    "safety_level": current_metrics.safety_level.value,
                    "target_achievement": {
                        "safety_score_target": self.TARGET_SAFETY_SCORE,
                        "target_achieved": current_metrics.overall_safety_score >= self.TARGET_SAFETY_SCORE,
                        "gap_to_target": self.TARGET_SAFETY_SCORE - current_metrics.overall_safety_score
                    }
                },
                "performance_metrics": {
                    "task_success_rate": current_metrics.task_success_rate,
                    "layer_performance": current_metrics.layer_success_rates,
                    "failsafe_usage_rate": current_metrics.failsafe_usage_rate,
                    "average_processing_time": current_metrics.average_processing_time,
                    "token_efficiency": current_metrics.token_efficiency,
                    "total_tasks_processed": current_metrics.total_tasks_processed
                },
                "bottleneck_analysis": {
                    "detected_bottlenecks": [b.value for b in current_metrics.detected_bottlenecks],
                    "bottleneck_count": len(current_metrics.detected_bottlenecks),
                    "critical_bottlenecks": [
                        b.value for b in current_metrics.detected_bottlenecks
                        if b in [BottleneckType.LAYER1_SYNTAX, BottleneckType.FAILSAFE_OVERUSE]
                    ]
                },
                "trend_analysis": {
                    "24h_trends": asdict(trends_24h),
                    "7d_trends": asdict(trends_7d),
                    "trend_summary": self._summarize_trends(trends_24h, trends_7d)
                },
                "recommendations": current_metrics.recommendations,
                "next_actions": self._generate_next_actions(current_metrics, trends_24h)
            }

            # レポート保存
            report_file = self.collaboration_dir / f"efficiency_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ 協業効率レポート生成完了: {report_file}")

            return report

        except Exception as e:
            logger.error(f"❌ 協業効率レポート生成エラー: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }

    def _summarize_trends(self, trends_24h: EfficiencyTrend, trends_7d: EfficiencyTrend) -> Dict[str, Any]:
        """トレンドサマリー"""

        summary = {
            "overall_direction": "stable",
            "key_improvements": [],
            "key_concerns": [],
            "trend_confidence": "low"  # データが少ない間は低い
        }

        # 24時間トレンド分析
        if trends_24h.safety_score_trend > 5:
            summary["key_improvements"].append("24時間で協業安全性が大幅改善")
            summary["overall_direction"] = "improving"
        elif trends_24h.safety_score_trend < -5:
            summary["key_concerns"].append("24時間で協業安全性が悪化")
            summary["overall_direction"] = "declining"

        # 7日間トレンド分析
        if trends_7d.safety_score_trend > 10:
            summary["key_improvements"].append("7日間で協業安全性が継続改善")
            summary["trend_confidence"] = "high"
        elif trends_7d.safety_score_trend < -10:
            summary["key_concerns"].append("7日間で協業安全性が継続悪化")
            summary["trend_confidence"] = "high"

        return summary

    def _generate_next_actions(self, metrics: CollaborationMetrics, trends: EfficiencyTrend) -> List[str]:
        """次のアクション提案"""

        actions = []

        # 安全性スコア別アクション
        if metrics.overall_safety_score < 60:
            actions.append("🚨 緊急アクション: 3層検証システムの全面監査と改善")
            actions.append("📊 詳細ログ分析でボトルネック特定")
            actions.append("🔧 フェイルセーフ機能の最適化")

        # ボトルネック別アクション
        if BottleneckType.LAYER1_SYNTAX in metrics.detected_bottlenecks:
            actions.append("📝 Layer1構文検証アルゴリズムの改善実施")

        if BottleneckType.FAILSAFE_OVERUSE in metrics.detected_bottlenecks:
            actions.append("🛡️ 予防的品質チェック機能の強化")

        # トレンド別アクション
        if trends.safety_score_trend < 0:
            actions.append("📈 協業安全性悪化への対策検討")

        # 定期的なアクション
        actions.append("📊 週次効率レビューの実施")
        actions.append("🔄 協業パラメータの継続最適化")

        return actions


def main() -> None:
    """テスト実行"""
    monitor = CollaborationEfficiencyMonitor()

    # 現在のメトリクス収集
    metrics = monitor.collect_current_metrics()
    print(f"協業安全性スコア: {metrics.overall_safety_score:.1f}/100")
    print(f"安全性レベル: {metrics.safety_level.value}")

    # トレンド分析
    trend = monitor.analyze_efficiency_trends("24h")
    print(f"24時間トレンド: {trend.safety_score_trend:+.1f}")

    # 効率レポート生成
    report = monitor.generate_efficiency_report()
    print("協業効率レポート生成完了")


if __name__ == "__main__":
    main()
