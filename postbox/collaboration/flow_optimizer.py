#!/usr/bin/env python3
"""
CollaborationFlowOptimizer - Issue #860対応
Gemini×Claude協業フローの最適化エンジン

タスクルーティング最適化・作業分担判定・自動実行パス選択の精度向上により
協業安全性を40/100から75-80/100に向上させる
"""

import json
import datetime
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import os
import re

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TaskComplexity(Enum):
    """タスク複雑度"""
    SIMPLE = "simple"           # 単純作業
    MODERATE = "moderate"       # 中程度
    COMPLEX = "complex"         # 複雑
    CRITICAL = "critical"       # 重要・高リスク


class AgentCapability(Enum):
    """エージェント能力"""
    GEMINI_OPTIMAL = "gemini_optimal"     # Gemini最適
    CLAUDE_OPTIMAL = "claude_optimal"     # Claude最適
    HYBRID_REQUIRED = "hybrid_required"   # 協業必須
    AUTO_DECISION = "auto_decision"       # 自動判定


class OptimizationStrategy(Enum):
    """最適化戦略"""
    SPEED_FOCUSED = "speed_focused"       # 速度重視
    QUALITY_FOCUSED = "quality_focused"   # 品質重視
    COST_FOCUSED = "cost_focused"         # コスト重視
    BALANCED = "balanced"                 # バランス重視


@dataclass
class TaskRoutingDecision:
    """タスクルーティング決定"""
    task_id: str
    recommended_agent: AgentCapability
    confidence_score: float  # 0.0-1.0
    reasoning: List[str]
    estimated_success_rate: float
    estimated_processing_time: float
    risk_factors: List[str]
    optimization_strategy: OptimizationStrategy


@dataclass
class CollaborationPattern:
    """協業パターン"""
    pattern_id: str
    task_type: str
    success_rate: float
    average_processing_time: float
    failure_modes: List[str]
    optimization_tips: List[str]
    last_updated: str


@dataclass
class FlowOptimizationResult:
    """フロー最適化結果"""
    timestamp: str
    optimizations_applied: List[str]
    performance_improvement: Dict[str, float]
    new_routing_rules: List[Dict[str, Any]]
    updated_patterns: List[str]
    recommendations: List[str]


class CollaborationFlowOptimizer:
    """協業フロー最適化エンジン

    Gemini×Claude間の最適なタスクルーティング、作業分担判定、
    自動実行パス選択を行い、協業効率を最大化する
    """

    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.collaboration_dir = self.postbox_dir / "collaboration"
        self.monitoring_dir = self.postbox_dir / "monitoring"

        # 最適化データディレクトリ作成
        self.collaboration_dir.mkdir(exist_ok=True)

        self.routing_rules_file = self.collaboration_dir / "routing_rules.json"
        self.patterns_file = self.collaboration_dir / "collaboration_patterns.json"
        self.optimization_history_file = self.collaboration_dir / "optimization_history.json"

        # デフォルトルーティングルール読み込み/作成
        self.routing_rules = self._load_or_create_routing_rules()

        # 協業パターン読み込み/作成
        self.collaboration_patterns = self._load_or_create_patterns()

        logger.info("🚀 CollaborationFlowOptimizer 初期化完了")

    def optimize_task_routing(self, task_data: Dict[str, Any],
                            strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> TaskRoutingDecision:
        """タスクルーティング最適化

        Args:
            task_data: タスク詳細データ
            strategy: 最適化戦略

        Returns:
            TaskRoutingDecision: ルーティング決定
        """

        logger.info(f"🎯 タスクルーティング最適化開始: {task_data.get('task_id', 'unknown')}")

        try:
            # タスク複雑度分析
            complexity = self._analyze_task_complexity(task_data)

            # 過去パターン分析
            matching_patterns = self._find_matching_patterns(task_data)

            # エージェント能力評価
            agent_capability = self._evaluate_agent_capability(task_data, complexity, strategy)

            # 成功率予測
            success_rate = self._predict_success_rate(task_data, agent_capability, matching_patterns)

            # 処理時間予測
            processing_time = self._predict_processing_time(task_data, agent_capability, matching_patterns)

            # リスク要因分析
            risk_factors = self._analyze_risk_factors(task_data, complexity)

            # 推論理由生成
            reasoning = self._generate_routing_reasoning(
                task_data, complexity, agent_capability, strategy
            )

            # 信頼度スコア計算
            confidence = self._calculate_confidence_score(
                matching_patterns, success_rate, risk_factors
            )

            decision = TaskRoutingDecision(
                task_id=task_data.get("task_id", f"task_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                recommended_agent=agent_capability,
                confidence_score=confidence,
                reasoning=reasoning,
                estimated_success_rate=success_rate,
                estimated_processing_time=processing_time,
                risk_factors=risk_factors,
                optimization_strategy=strategy
            )

            # ルーティング決定を記録
            self._record_routing_decision(decision)

            logger.info(f"✅ タスクルーティング最適化完了: {agent_capability.value} (信頼度: {confidence:.3f})")

            return decision

        except Exception as e:
            logger.error(f"❌ タスクルーティング最適化エラー: {e}")
            return self._create_fallback_routing_decision(task_data, strategy)

    def _analyze_task_complexity(self, task_data: Dict[str, Any]) -> TaskComplexity:
        """タスク複雑度分析"""

        task_type = task_data.get("type", "unknown")
        description = task_data.get("description", "")
        requirements = task_data.get("requirements", {})
        target_files = task_data.get("target_files", [])

        complexity_score = 0

        # タスクタイプ別複雑度
        if task_type in ["new_implementation", "new_feature_development"]:
            complexity_score += 3
        elif task_type in ["hybrid_implementation", "code_modification"]:
            complexity_score += 2
        elif task_type in ["error_fixing", "simple_modification"]:
            complexity_score += 1

        # ファイル数による複雑度
        file_count = len(target_files)
        if file_count > 10:
            complexity_score += 3
        elif file_count > 5:
            complexity_score += 2
        elif file_count > 1:
            complexity_score += 1

        # 説明文の複雑さ
        description_words = len(description.split()) if description else 0
        if description_words > 100:
            complexity_score += 2
        elif description_words > 50:
            complexity_score += 1

        # 要件の複雑さ
        if isinstance(requirements, dict):
            req_count = len(requirements)
            if req_count > 5:
                complexity_score += 2
            elif req_count > 2:
                complexity_score += 1

        # キーワードベース複雑度
        complex_keywords = [
            "architecture", "integration", "security", "performance",
            "database", "api", "complex", "critical", "refactor"
        ]

        description_lower = description.lower()
        for keyword in complex_keywords:
            if keyword in description_lower:
                complexity_score += 1

        # 複雑度判定
        if complexity_score >= 8:
            return TaskComplexity.CRITICAL
        elif complexity_score >= 5:
            return TaskComplexity.COMPLEX
        elif complexity_score >= 2:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    def _evaluate_agent_capability(self, task_data: Dict[str, Any],
                                 complexity: TaskComplexity,
                                 strategy: OptimizationStrategy) -> AgentCapability:
        """エージェント能力評価"""

        task_type = task_data.get("type", "unknown")
        description = task_data.get("description", "")

        # Gemini最適タスク
        gemini_optimal_types = [
            "error_fixing", "simple_modification", "type_annotation_fix",
            "syntax_fix", "format_fix", "import_fix"
        ]

        # Claude最適タスク
        claude_optimal_types = [
            "new_implementation", "architecture_design", "complex_refactor",
            "security_implementation", "code_review", "design_decision"
        ]

        # ハイブリッド必須タスク
        hybrid_required_types = [
            "hybrid_implementation", "new_feature_development",
            "integration_development", "system_integration"
        ]

        # タスクタイプベース判定
        if task_type in gemini_optimal_types:
            base_recommendation = AgentCapability.GEMINI_OPTIMAL
        elif task_type in claude_optimal_types:
            base_recommendation = AgentCapability.CLAUDE_OPTIMAL
        elif task_type in hybrid_required_types:
            base_recommendation = AgentCapability.HYBRID_REQUIRED
        else:
            base_recommendation = AgentCapability.AUTO_DECISION

        # 複雑度による調整
        if complexity == TaskComplexity.CRITICAL:
            # 重要タスクはClaude主導またはハイブリッド
            if base_recommendation == AgentCapability.GEMINI_OPTIMAL:
                base_recommendation = AgentCapability.HYBRID_REQUIRED
        elif complexity == TaskComplexity.SIMPLE:
            # 単純タスクはGemini最適化
            if base_recommendation == AgentCapability.CLAUDE_OPTIMAL:
                base_recommendation = AgentCapability.GEMINI_OPTIMAL

        # 戦略による調整
        if strategy == OptimizationStrategy.SPEED_FOCUSED:
            # 速度重視ならGemini優先
            if base_recommendation == AgentCapability.AUTO_DECISION:
                base_recommendation = AgentCapability.GEMINI_OPTIMAL
        elif strategy == OptimizationStrategy.QUALITY_FOCUSED:
            # 品質重視ならClaude優先
            if base_recommendation == AgentCapability.AUTO_DECISION:
                base_recommendation = AgentCapability.CLAUDE_OPTIMAL
        elif strategy == OptimizationStrategy.COST_FOCUSED:
            # コスト重視ならGemini優先
            if base_recommendation in [AgentCapability.AUTO_DECISION, AgentCapability.CLAUDE_OPTIMAL]:
                base_recommendation = AgentCapability.GEMINI_OPTIMAL

        # 説明文キーワード分析
        description_lower = description.lower()

        # Claude最適キーワード
        claude_keywords = [
            "design", "architecture", "strategy", "analysis", "review",
            "decision", "planning", "complex", "critical", "security"
        ]

        # Gemini最適キーワード
        gemini_keywords = [
            "fix", "error", "type", "syntax", "format", "simple",
            "quick", "batch", "auto", "generate"
        ]

        claude_score = sum(1 for kw in claude_keywords if kw in description_lower)
        gemini_score = sum(1 for kw in gemini_keywords if kw in description_lower)

        # キーワードスコアによる微調整
        if claude_score > gemini_score + 2:
            if base_recommendation == AgentCapability.GEMINI_OPTIMAL:
                base_recommendation = AgentCapability.HYBRID_REQUIRED
        elif gemini_score > claude_score + 2:
            if base_recommendation == AgentCapability.CLAUDE_OPTIMAL:
                base_recommendation = AgentCapability.HYBRID_REQUIRED

        return base_recommendation

    def _find_matching_patterns(self, task_data: Dict[str, Any]) -> List[CollaborationPattern]:
        """類似パターン検索"""

        task_type = task_data.get("type", "unknown")
        description = task_data.get("description", "")

        matching_patterns = []

        for pattern in self.collaboration_patterns:
            # タスクタイプマッチング
            if pattern.task_type == task_type:
                matching_patterns.append(pattern)
                continue

            # 説明文類似度チェック（簡易）
            pattern_words = set(pattern.task_type.split("_"))
            description_words = set(description.lower().split())

            overlap = len(pattern_words & description_words)
            if overlap > 0:
                matching_patterns.append(pattern)

        # 成功率順でソート
        matching_patterns.sort(key=lambda p: p.success_rate, reverse=True)

        return matching_patterns[:5]  # 上位5件

    def _predict_success_rate(self, task_data: Dict[str, Any],
                            agent_capability: AgentCapability,
                            matching_patterns: List[CollaborationPattern]) -> float:
        """成功率予測"""

        # ベース成功率
        base_rates = {
            AgentCapability.GEMINI_OPTIMAL: 0.85,
            AgentCapability.CLAUDE_OPTIMAL: 0.80,
            AgentCapability.HYBRID_REQUIRED: 0.75,
            AgentCapability.AUTO_DECISION: 0.70
        }

        base_rate = base_rates.get(agent_capability, 0.70)

        # 過去パターンによる調整
        if matching_patterns:
            pattern_rates = [p.success_rate for p in matching_patterns[:3]]
            pattern_avg = statistics.mean(pattern_rates)

            # 過去パターンの重み: 30%
            adjusted_rate = base_rate * 0.7 + pattern_avg * 0.3
        else:
            adjusted_rate = base_rate

        # ファイル数による調整
        target_files = task_data.get("target_files", [])
        file_count = len(target_files)

        if file_count > 10:
            adjusted_rate *= 0.9  # 10%減
        elif file_count > 5:
            adjusted_rate *= 0.95  # 5%減

        return min(adjusted_rate, 1.0)

    def _predict_processing_time(self, task_data: Dict[str, Any],
                               agent_capability: AgentCapability,
                               matching_patterns: List[CollaborationPattern]) -> float:
        """処理時間予測"""

        # ベース処理時間（秒）
        base_times = {
            AgentCapability.GEMINI_OPTIMAL: 1.0,
            AgentCapability.CLAUDE_OPTIMAL: 1.5,
            AgentCapability.HYBRID_REQUIRED: 2.0,
            AgentCapability.AUTO_DECISION: 1.8
        }

        base_time = base_times.get(agent_capability, 1.8)

        # 過去パターンによる調整
        if matching_patterns:
            pattern_times = [p.average_processing_time for p in matching_patterns[:3]]
            pattern_avg = statistics.mean(pattern_times)

            # 過去パターンの重み: 40%
            adjusted_time = base_time * 0.6 + pattern_avg * 0.4
        else:
            adjusted_time = base_time

        # ファイル数による調整
        target_files = task_data.get("target_files", [])
        file_count = len(target_files)

        if file_count > 10:
            adjusted_time *= 2.0
        elif file_count > 5:
            adjusted_time *= 1.5
        elif file_count > 1:
            adjusted_time *= 1.2

        # 説明文の長さによる調整
        description = task_data.get("description", "")
        word_count = len(description.split()) if description else 0

        if word_count > 100:
            adjusted_time *= 1.3
        elif word_count > 50:
            adjusted_time *= 1.1

        return adjusted_time

    def _analyze_risk_factors(self, task_data: Dict[str, Any],
                            complexity: TaskComplexity) -> List[str]:
        """リスク要因分析"""

        risk_factors = []

        # 複雑度リスク
        if complexity == TaskComplexity.CRITICAL:
            risk_factors.append("タスク複雑度が非常に高い")
        elif complexity == TaskComplexity.COMPLEX:
            risk_factors.append("タスク複雑度が高い")

        # ファイル数リスク
        target_files = task_data.get("target_files", [])
        file_count = len(target_files)

        if file_count > 10:
            risk_factors.append("対象ファイル数が多い（10+）")
        elif file_count > 5:
            risk_factors.append("対象ファイル数がやや多い（5+）")

        # タスクタイプリスク
        high_risk_types = [
            "new_implementation", "architecture_design", "security_implementation",
            "database_modification", "api_integration"
        ]

        task_type = task_data.get("type", "unknown")
        if task_type in high_risk_types:
            risk_factors.append(f"高リスクタスクタイプ: {task_type}")

        # 説明文リスク要因
        description = task_data.get("description", "").lower()
        risk_keywords = [
            "critical", "urgent", "breaking", "security", "production",
            "database", "migration", "refactor", "legacy"
        ]

        for keyword in risk_keywords:
            if keyword in description:
                risk_factors.append(f"リスクキーワード検出: {keyword}")

        # 要件不明確リスク
        requirements = task_data.get("requirements", {})
        if not requirements or len(requirements) < 2:
            risk_factors.append("要件が不明確または不足")

        return risk_factors

    def _generate_routing_reasoning(self, task_data: Dict[str, Any],
                                  complexity: TaskComplexity,
                                  agent_capability: AgentCapability,
                                  strategy: OptimizationStrategy) -> List[str]:
        """ルーティング推論理由生成"""

        reasoning = []

        # 基本推論
        task_type = task_data.get("type", "unknown")
        reasoning.append(f"タスクタイプ '{task_type}' を分析")
        reasoning.append(f"複雑度レベル: {complexity.value}")
        reasoning.append(f"最適化戦略: {strategy.value}")

        # エージェント選択理由
        if agent_capability == AgentCapability.GEMINI_OPTIMAL:
            reasoning.append("Gemini最適: 効率的な自動処理が可能")
            reasoning.append("高速処理とコスト効率を重視")
        elif agent_capability == AgentCapability.CLAUDE_OPTIMAL:
            reasoning.append("Claude最適: 高度な判断力と品質が必要")
            reasoning.append("戦略的思考と複雑な問題解決を重視")
        elif agent_capability == AgentCapability.HYBRID_REQUIRED:
            reasoning.append("ハイブリッド協業: 両エージェントの強みを活用")
            reasoning.append("高品質と効率のバランスを重視")
        else:
            reasoning.append("自動判定: 動的な最適化判断を実施")

        # 戦略別理由
        if strategy == OptimizationStrategy.SPEED_FOCUSED:
            reasoning.append("速度重視戦略により処理時間を最小化")
        elif strategy == OptimizationStrategy.QUALITY_FOCUSED:
            reasoning.append("品質重視戦略により最高品質を確保")
        elif strategy == OptimizationStrategy.COST_FOCUSED:
            reasoning.append("コスト重視戦略によりToken使用量を最小化")

        # ファイル数考慮
        target_files = task_data.get("target_files", [])
        file_count = len(target_files)
        if file_count > 5:
            reasoning.append(f"多数ファイル処理（{file_count}件）を考慮")

        return reasoning

    def _calculate_confidence_score(self, matching_patterns: List[CollaborationPattern],
                                  success_rate: float, risk_factors: List[str]) -> float:
        """信頼度スコア計算"""

        # ベース信頼度
        base_confidence = 0.7

        # 過去パターンによる調整
        if matching_patterns:
            pattern_count = len(matching_patterns)
            pattern_boost = min(pattern_count * 0.05, 0.15)  # 最大15%向上
            base_confidence += pattern_boost

        # 成功率による調整
        success_boost = (success_rate - 0.7) * 0.5  # 成功率70%を基準
        base_confidence += success_boost

        # リスク要因による調整
        risk_penalty = len(risk_factors) * 0.03  # リスク要因1つにつき3%減
        base_confidence -= risk_penalty

        return max(min(base_confidence, 1.0), 0.1)  # 0.1-1.0の範囲

    def _record_routing_decision(self, decision: TaskRoutingDecision) -> None:
        """ルーティング決定記録"""

        try:
            # 既存記録読み込み
            history_file = self.collaboration_dir / "routing_decisions.json"

            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    decisions = json.load(f)
            else:
                decisions = []

            # 新しい決定追加
            decision_dict = asdict(decision)
            decision_dict["timestamp"] = datetime.datetime.now().isoformat()
            decisions.append(decision_dict)

            # 最新100件のみ保持
            if len(decisions) > 100:
                decisions = decisions[-100:]

            # 保存
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(decisions, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"✅ ルーティング決定記録完了: {decision.task_id}")

        except Exception as e:
            logger.error(f"❌ ルーティング決定記録エラー: {e}")

    def _create_fallback_routing_decision(self, task_data: Dict[str, Any],
                                        strategy: OptimizationStrategy) -> TaskRoutingDecision:
        """フォールバックルーティング決定"""

        return TaskRoutingDecision(
            task_id=task_data.get("task_id", "fallback_task"),
            recommended_agent=AgentCapability.AUTO_DECISION,
            confidence_score=0.5,
            reasoning=["フォールバック決定: 詳細分析に失敗"],
            estimated_success_rate=0.7,
            estimated_processing_time=2.0,
            risk_factors=["分析データ不足"],
            optimization_strategy=strategy
        )

    def optimize_collaboration_flow(self) -> FlowOptimizationResult:
        """協業フロー最適化実行"""

        logger.info("🔄 協業フロー最適化開始")

        try:
            # 過去の協業データ分析
            performance_analysis = self._analyze_collaboration_performance()

            # ボトルネック特定
            bottlenecks = self._identify_collaboration_bottlenecks(performance_analysis)

            # 最適化ルール更新
            new_rules = self._update_routing_rules(bottlenecks)

            # パターン学習・更新
            updated_patterns = self._update_collaboration_patterns(performance_analysis)

            # 最適化推奨事項生成
            recommendations = self._generate_optimization_recommendations(bottlenecks)

            # 改善見積もり
            performance_improvement = self._estimate_performance_improvement(bottlenecks, new_rules)

            result = FlowOptimizationResult(
                timestamp=datetime.datetime.now().isoformat(),
                optimizations_applied=[
                    f"ルーティングルール更新: {len(new_rules)}件",
                    f"協業パターン更新: {len(updated_patterns)}件",
                    f"ボトルネック対策: {len(bottlenecks)}件"
                ],
                performance_improvement=performance_improvement,
                new_routing_rules=new_rules,
                updated_patterns=updated_patterns,
                recommendations=recommendations
            )

            # 最適化結果保存
            self._save_optimization_result(result)

            logger.info("✅ 協業フロー最適化完了")

            return result

        except Exception as e:
            logger.error(f"❌ 協業フロー最適化エラー: {e}")
            return self._create_fallback_optimization_result()

    def _analyze_collaboration_performance(self) -> Dict[str, Any]:
        """協業パフォーマンス分析"""

        analysis = {
            "total_tasks": 0,
            "success_rates": {},
            "processing_times": {},
            "failure_modes": [],
            "bottleneck_indicators": {}
        }

        # 3層検証データ分析
        verification_file = self.monitoring_dir / "three_layer_verification_metrics.json"
        if verification_file.exists():
            try:
                with open(verification_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)

                if verification_data:
                    recent_data = verification_data[-10:]  # 最新10件

                    # 成功率分析
                    for layer in ["layer1", "layer2", "layer3", "integration"]:
                        rates = [d["success_rates"].get(f"{layer}_success_rate", 0) for d in recent_data]
                        analysis["success_rates"][layer] = statistics.mean(rates) if rates else 0

                    # 処理時間分析
                    times = [d["execution_time"] for d in recent_data]
                    analysis["processing_times"]["average"] = statistics.mean(times) if times else 0
                    analysis["processing_times"]["max"] = max(times) if times else 0

                    analysis["total_tasks"] = len(verification_data)

            except Exception as e:
                logger.warning(f"⚠️ 検証データ分析エラー: {e}")

        # フェイルセーフデータ分析
        failsafe_file = self.monitoring_dir / "failsafe_usage.json"
        if failsafe_file.exists():
            try:
                with open(failsafe_file, 'r', encoding='utf-8') as f:
                    failsafe_data = json.load(f)

                if failsafe_data:
                    recent_failsafe = failsafe_data[-10:]

                    # 失敗モード分析
                    for entry in recent_failsafe:
                        for failsafe_type in entry.get("failsafe_types", []):
                            analysis["failure_modes"].append(failsafe_type)

                    # ボトルネック指標
                    total_failsafe = sum(entry["failsafe_count"] for entry in recent_failsafe)
                    total_files = sum(entry["total_files"] for entry in recent_failsafe)

                    if total_files > 0:
                        analysis["bottleneck_indicators"]["failsafe_rate"] = total_failsafe / total_files

            except Exception as e:
                logger.warning(f"⚠️ フェイルセーフデータ分析エラー: {e}")

        return analysis

    def _identify_collaboration_bottlenecks(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """協業ボトルネック特定"""

        bottlenecks = []

        # 成功率ボトルネック
        success_rates = performance_analysis.get("success_rates", {})
        for layer, rate in success_rates.items():
            if rate < 0.8:
                bottlenecks.append(f"{layer}_low_success_rate")

        # 処理時間ボトルネック
        processing_times = performance_analysis.get("processing_times", {})
        avg_time = processing_times.get("average", 0)
        max_time = processing_times.get("max", 0)

        if avg_time > 2.0:
            bottlenecks.append("slow_average_processing")

        if max_time > 5.0:
            bottlenecks.append("extremely_slow_processing")

        # フェイルセーフボトルネック
        bottleneck_indicators = performance_analysis.get("bottleneck_indicators", {})
        failsafe_rate = bottleneck_indicators.get("failsafe_rate", 0)

        if failsafe_rate > 0.3:
            bottlenecks.append("high_failsafe_usage")

        # 失敗モードボトルネック
        failure_modes = performance_analysis.get("failure_modes", [])
        failure_counts = {}

        for mode in failure_modes:
            failure_counts[mode] = failure_counts.get(mode, 0) + 1

        for mode, count in failure_counts.items():
            if count > 3:  # 3回以上の同じ失敗
                bottlenecks.append(f"repeated_{mode}")

        return bottlenecks

    def _update_routing_rules(self, bottlenecks: List[str]) -> List[Dict[str, Any]]:
        """ルーティングルール更新"""

        new_rules = []

        # ボトルネック別ルール生成
        for bottleneck in bottlenecks:
            if "layer1" in bottleneck:
                new_rules.append({
                    "condition": "syntax_validation_required",
                    "action": "prefer_gemini_with_pre_validation",
                    "reason": f"Layer1ボトルネック対策: {bottleneck}"
                })

            elif "layer2" in bottleneck:
                new_rules.append({
                    "condition": "quality_check_critical",
                    "action": "require_claude_review",
                    "reason": f"Layer2品質ボトルネック対策: {bottleneck}"
                })

            elif "layer3" in bottleneck:
                new_rules.append({
                    "condition": "claude_approval_needed",
                    "action": "optimize_approval_process",
                    "reason": f"Layer3承認ボトルネック対策: {bottleneck}"
                })

            elif "failsafe" in bottleneck:
                new_rules.append({
                    "condition": "high_failsafe_risk",
                    "action": "enable_preventive_validation",
                    "reason": f"フェイルセーフ過使用対策: {bottleneck}"
                })

            elif "slow" in bottleneck:
                new_rules.append({
                    "condition": "processing_time_critical",
                    "action": "prefer_parallel_processing",
                    "reason": f"処理時間ボトルネック対策: {bottleneck}"
                })

        # 既存ルールに追加
        try:
            self.routing_rules.extend(new_rules)

            # ルール重複除去
            unique_rules = []
            seen_conditions = set()

            for rule in self.routing_rules:
                condition = rule.get("condition")
                if condition not in seen_conditions:
                    unique_rules.append(rule)
                    seen_conditions.add(condition)

            self.routing_rules = unique_rules

            # 保存
            with open(self.routing_rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.routing_rules, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ ルーティングルール更新エラー: {e}")

        return new_rules

    def _update_collaboration_patterns(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """協業パターン更新"""

        updated_patterns = []

        try:
            # 新しいパフォーマンス情報でパターン更新
            for pattern in self.collaboration_patterns:
                old_success_rate = pattern.success_rate

                # パフォーマンス分析に基づく調整
                layer_rates = performance_analysis.get("success_rates", {})
                if layer_rates:
                    avg_success_rate = statistics.mean(layer_rates.values())
                    # 加重平均で更新 (既存70%, 新データ30%)
                    pattern.success_rate = old_success_rate * 0.7 + avg_success_rate * 0.3

                # 処理時間更新
                avg_time = performance_analysis.get("processing_times", {}).get("average", 0)
                if avg_time > 0:
                    pattern.average_processing_time = pattern.average_processing_time * 0.7 + avg_time * 0.3

                # 更新時刻
                pattern.last_updated = datetime.datetime.now().isoformat()

                if abs(pattern.success_rate - old_success_rate) > 0.05:  # 5%以上の変化
                    updated_patterns.append(pattern.pattern_id)

            # パターン保存
            patterns_data = [asdict(p) for p in self.collaboration_patterns]
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ 協業パターン更新エラー: {e}")

        return updated_patterns

    def _generate_optimization_recommendations(self, bottlenecks: List[str]) -> List[str]:
        """最適化推奨事項生成"""

        recommendations = []

        # ボトルネック別推奨
        for bottleneck in bottlenecks:
            if "layer1" in bottleneck:
                recommendations.append("📝 Layer1構文検証の事前バリデーション強化を実施")
            elif "layer2" in bottleneck:
                recommendations.append("🔍 Layer2品質チェックの基準見直しと最適化")
            elif "layer3" in bottleneck:
                recommendations.append("👤 Layer3 Claude承認プロセスの効率化")
            elif "failsafe" in bottleneck:
                recommendations.append("🛡️ フェイルセーフ使用率削減のため予防的チェック強化")
            elif "slow" in bottleneck:
                recommendations.append("⚡ 処理時間短縮のため並列処理機能の活用")

        # 一般的な推奨
        if not bottlenecks:
            recommendations.append("✅ 協業フローは良好に動作しています")
            recommendations.append("📊 継続的な監視とパフォーマンス追跡を推奨")
        else:
            recommendations.append(f"🎯 {len(bottlenecks)}個のボトルネックが特定されました")
            recommendations.append("🔄 最適化後の効果測定を実施してください")

        # 予防的推奨
        recommendations.append("📈 定期的な協業フロー見直しの実施")
        recommendations.append("🎓 協業パターンの継続学習と改善")

        return recommendations

    def _estimate_performance_improvement(self, bottlenecks: List[str],
                                        new_rules: List[Dict[str, Any]]) -> Dict[str, float]:
        """パフォーマンス改善見積もり"""

        improvement = {
            "safety_score_improvement": 0.0,
            "success_rate_improvement": 0.0,
            "processing_time_improvement": 0.0,
            "failsafe_usage_reduction": 0.0
        }

        # ボトルネック解決による改善見積もり
        for bottleneck in bottlenecks:
            if "layer1" in bottleneck:
                improvement["success_rate_improvement"] += 0.05  # 5%改善
                improvement["safety_score_improvement"] += 2.0   # 2点改善
            elif "layer2" in bottleneck:
                improvement["success_rate_improvement"] += 0.08  # 8%改善
                improvement["safety_score_improvement"] += 3.0   # 3点改善
            elif "layer3" in bottleneck:
                improvement["success_rate_improvement"] += 0.06  # 6%改善
                improvement["safety_score_improvement"] += 2.5   # 2.5点改善
            elif "failsafe" in bottleneck:
                improvement["failsafe_usage_reduction"] += 0.10  # 10%削減
                improvement["safety_score_improvement"] += 4.0   # 4点改善
            elif "slow" in bottleneck:
                improvement["processing_time_improvement"] += 0.20  # 20%短縮
                improvement["safety_score_improvement"] += 1.5     # 1.5点改善

        # 新ルールによる追加改善
        rule_count = len(new_rules)
        improvement["safety_score_improvement"] += rule_count * 0.5  # ルール1つにつき0.5点

        return improvement

    def _save_optimization_result(self, result: FlowOptimizationResult) -> None:
        """最適化結果保存"""

        try:
            # 既存履歴読み込み
            if self.optimization_history_file.exists():
                with open(self.optimization_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []

            # 新しい結果追加
            history.append(asdict(result))

            # 最新20件のみ保持
            if len(history) > 20:
                history = history[-20:]

            # 保存
            with open(self.optimization_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ 最適化結果保存完了: {self.optimization_history_file}")

        except Exception as e:
            logger.error(f"❌ 最適化結果保存エラー: {e}")

    def _create_fallback_optimization_result(self) -> FlowOptimizationResult:
        """フォールバック最適化結果"""

        return FlowOptimizationResult(
            timestamp=datetime.datetime.now().isoformat(),
            optimizations_applied=["フォールバック最適化実行"],
            performance_improvement={
                "safety_score_improvement": 0.0,
                "success_rate_improvement": 0.0,
                "processing_time_improvement": 0.0,
                "failsafe_usage_reduction": 0.0
            },
            new_routing_rules=[],
            updated_patterns=[],
            recommendations=["データ不足により最適化が制限されました"]
        )

    def _load_or_create_routing_rules(self) -> List[Dict[str, Any]]:
        """ルーティングルール読み込み/作成"""

        if self.routing_rules_file.exists():
            try:
                with open(self.routing_rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ ルーティングルール読み込みエラー: {e}")

        # デフォルトルール作成
        default_rules = [
            {
                "condition": "error_fixing",
                "action": "prefer_gemini",
                "reason": "エラー修正はGeminiが効率的"
            },
            {
                "condition": "new_implementation",
                "action": "prefer_claude",
                "reason": "新規実装はClaude判断が重要"
            },
            {
                "condition": "complex_task",
                "action": "require_hybrid",
                "reason": "複雑タスクは協業が最適"
            }
        ]

        # 保存
        try:
            with open(self.routing_rules_file, 'w', encoding='utf-8') as f:
                json.dump(default_rules, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ デフォルトルール保存エラー: {e}")

        return default_rules

    def _load_or_create_patterns(self) -> List[CollaborationPattern]:
        """協業パターン読み込み/作成"""

        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)

                patterns = []
                for data in patterns_data:
                    pattern = CollaborationPattern(**data)
                    patterns.append(pattern)

                return patterns

            except Exception as e:
                logger.warning(f"⚠️ 協業パターン読み込みエラー: {e}")

        # デフォルトパターン作成
        default_patterns = [
            CollaborationPattern(
                pattern_id="error_fixing_pattern",
                task_type="error_fixing",
                success_rate=0.85,
                average_processing_time=1.2,
                failure_modes=["syntax_error", "type_error"],
                optimization_tips=["事前構文チェック", "型注釈確認"],
                last_updated=datetime.datetime.now().isoformat()
            ),
            CollaborationPattern(
                pattern_id="new_implementation_pattern",
                task_type="new_implementation",
                success_rate=0.75,
                average_processing_time=2.5,
                failure_modes=["design_complexity", "integration_issues"],
                optimization_tips=["段階的実装", "詳細設計書作成"],
                last_updated=datetime.datetime.now().isoformat()
            )
        ]

        # 保存
        try:
            patterns_data = [asdict(p) for p in default_patterns]
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ デフォルトパターン保存エラー: {e}")

        return default_patterns


def main() -> None:
    """テスト実行"""
    optimizer = CollaborationFlowOptimizer()

    # サンプルタスクでルーティング最適化テスト
    sample_task = {
        "task_id": "test_task_001",
        "type": "error_fixing",
        "description": "型注釈エラーの修正",
        "target_files": ["file1.py", "file2.py"],
        "requirements": {"error_type": "type_annotation"}
    }

    # ルーティング決定
    decision = optimizer.optimize_task_routing(sample_task)
    print(f"推奨エージェント: {decision.recommended_agent.value}")
    print(f"信頼度: {decision.confidence_score:.3f}")

    # フロー最適化
    optimization = optimizer.optimize_collaboration_flow()
    print(f"最適化適用: {len(optimization.optimizations_applied)}件")


if __name__ == "__main__":
    main()
