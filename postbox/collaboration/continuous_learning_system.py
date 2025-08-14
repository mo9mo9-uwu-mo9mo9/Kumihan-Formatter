#!/usr/bin/env python3
"""
ContinuousLearningSystem - Issue #860対応
継続学習・改善システム

協業パターン学習・自動最適化・フィードバックループにより
Gemini×Claude協業システムの継続的品質向上を実現
"""

import json
import datetime
import statistics
import os
import pickle
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class LearningCategory(Enum):
    """学習カテゴリ"""
    TASK_ROUTING = "task_routing"
    QUALITY_PREDICTION = "quality_prediction"
    FAILURE_PREVENTION = "failure_prevention"
    OPTIMIZATION_STRATEGY = "optimization_strategy"
    PERFORMANCE_TUNING = "performance_tuning"


class FeedbackType(Enum):
    """フィードバックタイプ"""
    SUCCESS = "success"
    FAILURE = "failure"
    IMPROVEMENT = "improvement"
    REGRESSION = "regression"
    USER_RATING = "user_rating"


class LearningConfidence(Enum):
    """学習信頼度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class LearningPattern:
    """学習パターン"""
    pattern_id: str
    category: LearningCategory
    context: Dict[str, Any]  # タスクコンテキスト
    action_taken: str
    outcome: Dict[str, Any]  # 結果指標
    feedback_score: float  # -1.0 to 1.0
    confidence: LearningConfidence
    frequency: int  # 出現頻度
    last_seen: str
    effectiveness: float  # 0.0-1.0


@dataclass
class OptimizationRecommendation:
    """最適化推奨"""
    recommendation_id: str
    category: LearningCategory
    title: str
    description: str
    expected_improvement: Dict[str, float]
    implementation_steps: List[str]
    confidence_score: float
    risk_level: str  # "low", "medium", "high"
    estimated_effort: str
    supporting_patterns: List[str]


@dataclass
class FeedbackData:
    """フィードバックデータ"""
    feedback_id: str
    feedback_type: FeedbackType
    target_pattern: str
    target_action: str
    performance_metrics: Dict[str, float]
    user_satisfaction: Optional[float]
    timestamp: str
    context: Dict[str, Any]


@dataclass
class LearningReport:
    """学習レポート"""
    timestamp: str
    total_patterns_learned: int
    active_patterns: int
    learning_accuracy: float
    optimization_suggestions: List[OptimizationRecommendation]
    performance_improvements: Dict[str, float]
    confidence_distribution: Dict[str, int]
    recent_discoveries: List[str]


class ContinuousLearningSystem:
    """継続学習・改善システム

    協業パターンの学習・分析・最適化により、
    システム全体の継続的な性能向上を実現
    """

    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.collaboration_dir = self.postbox_dir / "collaboration"
        self.learning_dir = self.collaboration_dir / "learning"
        self.models_dir = self.learning_dir / "models"

        # ディレクトリ作成
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.patterns_file = self.learning_dir / "learned_patterns.json"
        self.feedback_file = self.learning_dir / "feedback_data.json"
        self.recommendations_file = self.learning_dir / "optimization_recommendations.json"
        self.learning_metrics_file = self.learning_dir / "learning_metrics.json"

        # 学習パターン
        self.learned_patterns = self._load_learned_patterns()

        # フィードバックデータ
        self.feedback_history = self._load_feedback_history()

        # 学習メトリクス
        self.learning_metrics = self._load_learning_metrics()

        # 最適化推奨キャッシュ
        self.recommendation_cache = {}

        logger.info("🧠 ContinuousLearningSystem 初期化完了")
        logger.info(f"📚 学習済みパターン: {len(self.learned_patterns)}件")
        logger.info(f"📝 フィードバック履歴: {len(self.feedback_history)}件")

    def learn_from_collaboration_data(self) -> Dict[str, Any]:
        """協業データからの学習実行

        Returns:
            Dict[str, Any]: 学習結果
        """

        logger.info("🧠 協業データからの学習開始")

        try:
            learning_results = {
                "new_patterns_discovered": 0,
                "patterns_updated": 0,
                "confidence_improvements": 0,
                "optimization_opportunities": 0,
                "learning_accuracy": 0.0
            }

            # 1. 協業データ収集・分析
            collaboration_data = self._collect_collaboration_data()

            # 2. パターン抽出・学習
            new_patterns = self._extract_patterns_from_data(collaboration_data)
            learning_results["new_patterns_discovered"] = len(new_patterns)

            # 3. 既存パターン更新
            updated_count = self._update_existing_patterns(collaboration_data)
            learning_results["patterns_updated"] = updated_count

            # 4. 信頼度調整
            confidence_improvements = self._adjust_pattern_confidence()
            learning_results["confidence_improvements"] = confidence_improvements

            # 5. 最適化機会特定
            optimization_opportunities = self._identify_optimization_opportunities()
            learning_results["optimization_opportunities"] = len(optimization_opportunities)

            # 6. 学習精度評価
            learning_accuracy = self._evaluate_learning_accuracy()
            learning_results["learning_accuracy"] = learning_accuracy

            # 7. 学習結果保存
            self._save_learning_results(learning_results)

            logger.info(f"✅ 協業データ学習完了: {learning_results['new_patterns_discovered']}新パターン, {learning_results['patterns_updated']}更新")

            return learning_results

        except Exception as e:
            logger.error(f"❌ 協業データ学習エラー: {e}")
            return {"error": str(e)}

    def _collect_collaboration_data(self) -> Dict[str, Any]:
        """協業データ収集"""

        data = {
            "efficiency_metrics": [],
            "routing_decisions": [],
            "quality_checks": [],
            "failsafe_usage": [],
            "verification_results": []
        }

        try:
            # 効率メトリクス
            efficiency_file = self.collaboration_dir / "efficiency_metrics.json"
            if efficiency_file.exists():
                with open(efficiency_file, 'r', encoding='utf-8') as f:
                    data["efficiency_metrics"] = json.load(f)

            # ルーティング決定
            routing_file = self.collaboration_dir / "routing_decisions.json"
            if routing_file.exists():
                with open(routing_file, 'r', encoding='utf-8') as f:
                    data["routing_decisions"] = json.load(f)

            # 品質チェック
            preventive_dir = self.postbox_dir / "quality" / "preventive_checks"
            if preventive_dir.exists():
                check_files = list(preventive_dir.glob("check_*.json"))
                for check_file in check_files[-20:]:  # 最新20件
                    try:
                        with open(check_file, 'r', encoding='utf-8') as f:
                            check_data = json.load(f)
                            data["quality_checks"].append(check_data)
                    except Exception:
                        continue

            # フェイルセーフ使用状況
            monitoring_dir = self.postbox_dir / "monitoring"
            failsafe_file = monitoring_dir / "failsafe_usage.json"
            if failsafe_file.exists():
                with open(failsafe_file, 'r', encoding='utf-8') as f:
                    data["failsafe_usage"] = json.load(f)

            # 3層検証結果
            verification_file = monitoring_dir / "three_layer_verification_metrics.json"
            if verification_file.exists():
                with open(verification_file, 'r', encoding='utf-8') as f:
                    data["verification_results"] = json.load(f)

        except Exception as e:
            logger.warning(f"⚠️ 協業データ収集エラー: {e}")

        return data

    def _extract_patterns_from_data(self, collaboration_data: Dict[str, Any]) -> List[LearningPattern]:
        """データからパターン抽出"""

        new_patterns = []

        try:
            # ルーティングパターン学習
            routing_patterns = self._extract_routing_patterns(collaboration_data["routing_decisions"])
            new_patterns.extend(routing_patterns)

            # 品質予測パターン学習
            quality_patterns = self._extract_quality_patterns(collaboration_data["quality_checks"])
            new_patterns.extend(quality_patterns)

            # 失敗防止パターン学習
            failure_patterns = self._extract_failure_patterns(
                collaboration_data["failsafe_usage"],
                collaboration_data["verification_results"]
            )
            new_patterns.extend(failure_patterns)

            # 最適化戦略パターン学習
            optimization_patterns = self._extract_optimization_patterns(collaboration_data["efficiency_metrics"])
            new_patterns.extend(optimization_patterns)

            # 重複除去
            unique_patterns = self._deduplicate_patterns(new_patterns)

            # 新パターンを既存パターンに追加
            for pattern in unique_patterns:
                if not self._pattern_exists(pattern):
                    self.learned_patterns.append(pattern)

        except Exception as e:
            logger.warning(f"⚠️ パターン抽出エラー: {e}")

        return new_patterns

    def _extract_routing_patterns(self, routing_data: List[Dict]) -> List[LearningPattern]:
        """ルーティングパターン抽出"""

        patterns = []

        for decision in routing_data:
            try:
                # 高信頼度ルーティング決定をパターン化
                confidence = decision.get("confidence_score", 0.0)
                if confidence >= 0.8:

                    # コンテキスト特徴抽出
                    context = {
                        "task_type": decision.get("optimization_strategy", "unknown"),
                        "estimated_success_rate": decision.get("estimated_success_rate", 0.0),
                        "estimated_processing_time": decision.get("estimated_processing_time", 0.0),
                        "risk_factors_count": len(decision.get("risk_factors", []))
                    }

                    # パターン作成
                    pattern_id = self._generate_pattern_id("routing", context)

                    pattern = LearningPattern(
                        pattern_id=pattern_id,
                        category=LearningCategory.TASK_ROUTING,
                        context=context,
                        action_taken=decision.get("recommended_agent", "unknown"),
                        outcome={"confidence": confidence, "success_rate": decision.get("estimated_success_rate", 0.0)},
                        feedback_score=confidence * 2 - 1,  # 0.8-1.0 -> 0.6-1.0
                        confidence=self._determine_learning_confidence(confidence),
                        frequency=1,
                        last_seen=datetime.datetime.now().isoformat(),
                        effectiveness=confidence
                    )

                    patterns.append(pattern)

            except Exception as e:
                logger.warning(f"⚠️ ルーティングパターン抽出エラー: {e}")
                continue

        return patterns

    def _extract_quality_patterns(self, quality_data: List[Dict]) -> List[LearningPattern]:
        """品質パターン抽出"""

        patterns = []

        for check in quality_data:
            try:
                # 高品質または改善パターンを学習
                quality_score = check.get("overall_quality_score", 0.0)
                prevention_score = check.get("failsafe_prevention_score", 0.0)

                if quality_score >= 0.8 or prevention_score >= 0.8:

                    # コンテキスト特徴抽出
                    context = {
                        "file_type": Path(check.get("file_path", "")).suffix,
                        "risk_count": len(check.get("detected_risks", [])),
                        "quality_score_range": self._get_score_range(quality_score),
                        "has_immediate_actions": len(check.get("immediate_actions", [])) > 0
                    }

                    pattern_id = self._generate_pattern_id("quality", context)

                    pattern = LearningPattern(
                        pattern_id=pattern_id,
                        category=LearningCategory.QUALITY_PREDICTION,
                        context=context,
                        action_taken="preventive_check",
                        outcome={
                            "quality_score": quality_score,
                            "prevention_score": prevention_score,
                            "risk_count": len(check.get("detected_risks", []))
                        },
                        feedback_score=quality_score * 2 - 1,
                        confidence=self._determine_learning_confidence(quality_score),
                        frequency=1,
                        last_seen=datetime.datetime.now().isoformat(),
                        effectiveness=max(quality_score, prevention_score)
                    )

                    patterns.append(pattern)

            except Exception as e:
                logger.warning(f"⚠️ 品質パターン抽出エラー: {e}")
                continue

        return patterns

    def _extract_failure_patterns(self, failsafe_data: List[Dict],
                                 verification_data: List[Dict]) -> List[LearningPattern]:
        """失敗防止パターン抽出"""

        patterns = []

        try:
            # フェイルセーフ使用率が低い成功パターンを学習
            for i, verification in enumerate(verification_data):
                failsafe_entry = failsafe_data[i] if i < len(failsafe_data) else None

                if failsafe_entry and verification:
                    failsafe_rate = failsafe_entry["failsafe_count"] / max(failsafe_entry["total_files"], 1)
                    success_rate = verification["success_rates"]["overall_success_rate"]

                    # 低フェイルセーフ + 高成功率のパターンを学習
                    if failsafe_rate <= 0.3 and success_rate >= 0.8:

                        context = {
                            "layer1_success": verification["success_rates"]["layer1_success_rate"],
                            "layer2_success": verification["success_rates"]["layer2_success_rate"],
                            "layer3_success": verification["success_rates"]["layer3_approval_rate"],
                            "execution_time_range": self._get_time_range(verification["execution_time"]),
                            "file_count": failsafe_entry["total_files"]
                        }

                        pattern_id = self._generate_pattern_id("failure_prevention", context)

                        pattern = LearningPattern(
                            pattern_id=pattern_id,
                            category=LearningCategory.FAILURE_PREVENTION,
                            context=context,
                            action_taken="low_failsafe_high_success",
                            outcome={
                                "failsafe_rate": failsafe_rate,
                                "success_rate": success_rate,
                                "prevention_effectiveness": 1.0 - failsafe_rate
                            },
                            feedback_score=success_rate * 2 - 1,
                            confidence=self._determine_learning_confidence(success_rate),
                            frequency=1,
                            last_seen=datetime.datetime.now().isoformat(),
                            effectiveness=success_rate * (1.0 - failsafe_rate)
                        )

                        patterns.append(pattern)

        except Exception as e:
            logger.warning(f"⚠️ 失敗防止パターン抽出エラー: {e}")

        return patterns

    def _extract_optimization_patterns(self, efficiency_data: List[Dict]) -> List[LearningPattern]:
        """最適化パターン抽出"""

        patterns = []

        if len(efficiency_data) < 2:
            return patterns

        try:
            # 効率改善パターンを学習
            for i in range(1, len(efficiency_data)):
                current = efficiency_data[i]
                previous = efficiency_data[i-1]

                # 安全性スコア改善パターン
                score_improvement = current["overall_safety_score"] - previous["overall_safety_score"]

                if score_improvement > 2.0:  # 2点以上の改善

                    context = {
                        "initial_safety_level": previous["safety_level"],
                        "improvement_magnitude": self._get_improvement_range(score_improvement),
                        "task_success_improvement": current["task_success_rate"] - previous["task_success_rate"],
                        "failsafe_reduction": previous["failsafe_usage_rate"] - current["failsafe_usage_rate"]
                    }

                    pattern_id = self._generate_pattern_id("optimization", context)

                    pattern = LearningPattern(
                        pattern_id=pattern_id,
                        category=LearningCategory.OPTIMIZATION_STRATEGY,
                        context=context,
                        action_taken="safety_score_improvement",
                        outcome={
                            "score_improvement": score_improvement,
                            "final_score": current["overall_safety_score"],
                            "improvement_rate": score_improvement / previous["overall_safety_score"]
                        },
                        feedback_score=min(score_improvement / 10.0, 1.0),  # 10点改善で最大スコア
                        confidence=self._determine_learning_confidence(score_improvement / 10.0),
                        frequency=1,
                        last_seen=datetime.datetime.now().isoformat(),
                        effectiveness=score_improvement / 10.0
                    )

                    patterns.append(pattern)

        except Exception as e:
            logger.warning(f"⚠️ 最適化パターン抽出エラー: {e}")

        return patterns

    def _update_existing_patterns(self, collaboration_data: Dict[str, Any]) -> int:
        """既存パターン更新"""

        updated_count = 0

        try:
            for pattern in self.learned_patterns:
                # パターンマッチング・更新ロジック
                if self._should_update_pattern(pattern, collaboration_data):
                    self._update_pattern_metrics(pattern, collaboration_data)
                    updated_count += 1

        except Exception as e:
            logger.warning(f"⚠️ パターン更新エラー: {e}")

        return updated_count

    def _should_update_pattern(self, pattern: LearningPattern, data: Dict[str, Any]) -> bool:
        """パターン更新判定"""

        # 最近のデータでパターンが観測されたかチェック
        try:
            last_seen = datetime.datetime.fromisoformat(pattern.last_seen)
            now = datetime.datetime.now()

            # 1週間以内に更新されている場合はスキップ
            if (now - last_seen).days < 7:
                return False

            # パターンに一致するデータがあるかチェック
            if pattern.category == LearningCategory.TASK_ROUTING:
                return self._check_routing_pattern_match(pattern, data["routing_decisions"])
            elif pattern.category == LearningCategory.QUALITY_PREDICTION:
                return self._check_quality_pattern_match(pattern, data["quality_checks"])

        except Exception:
            pass

        return False

    def _check_routing_pattern_match(self, pattern: LearningPattern, routing_data: List[Dict]) -> bool:
        """ルーティングパターンマッチチェック"""

        for decision in routing_data[-10:]:  # 最新10件
            try:
                # コンテキスト類似性チェック
                context_match = self._calculate_context_similarity(
                    pattern.context,
                    {
                        "task_type": decision.get("optimization_strategy", "unknown"),
                        "estimated_success_rate": decision.get("estimated_success_rate", 0.0),
                        "estimated_processing_time": decision.get("estimated_processing_time", 0.0),
                        "risk_factors_count": len(decision.get("risk_factors", []))
                    }
                )

                if context_match > 0.8:  # 80%以上の類似性
                    return True

            except Exception:
                continue

        return False

    def _check_quality_pattern_match(self, pattern: LearningPattern, quality_data: List[Dict]) -> bool:
        """品質パターンマッチチェック"""

        for check in quality_data[-10:]:  # 最新10件
            try:
                context_match = self._calculate_context_similarity(
                    pattern.context,
                    {
                        "file_type": Path(check.get("file_path", "")).suffix,
                        "risk_count": len(check.get("detected_risks", [])),
                        "quality_score_range": self._get_score_range(check.get("overall_quality_score", 0.0)),
                        "has_immediate_actions": len(check.get("immediate_actions", [])) > 0
                    }
                )

                if context_match > 0.8:
                    return True

            except Exception:
                continue

        return False

    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """コンテキスト類似度計算"""

        try:
            if not context1 or not context2:
                return 0.0

            # 共通キーの一致度計算
            common_keys = set(context1.keys()) & set(context2.keys())
            if not common_keys:
                return 0.0

            similarity_scores = []

            for key in common_keys:
                val1, val2 = context1[key], context2[key]

                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # 数値の類似度
                    if val1 == 0 and val2 == 0:
                        similarity_scores.append(1.0)
                    elif val1 == 0 or val2 == 0:
                        similarity_scores.append(0.0)
                    else:
                        diff = abs(val1 - val2) / max(abs(val1), abs(val2))
                        similarity_scores.append(1.0 - diff)

                elif str(val1) == str(val2):
                    # 文字列完全一致
                    similarity_scores.append(1.0)
                else:
                    # 文字列不一致
                    similarity_scores.append(0.0)

            return statistics.mean(similarity_scores) if similarity_scores else 0.0

        except Exception:
            return 0.0

    def _update_pattern_metrics(self, pattern: LearningPattern, data: Dict[str, Any]) -> None:
        """パターンメトリクス更新"""

        try:
            # 頻度増加
            pattern.frequency += 1

            # 最終確認時刻更新
            pattern.last_seen = datetime.datetime.now().isoformat()

            # 信頼度調整（頻度に基づく）
            if pattern.frequency >= 10:
                pattern.confidence = LearningConfidence.VERY_HIGH
            elif pattern.frequency >= 5:
                pattern.confidence = LearningConfidence.HIGH
            elif pattern.frequency >= 3:
                pattern.confidence = LearningConfidence.MEDIUM

        except Exception as e:
            logger.warning(f"⚠️ パターンメトリクス更新エラー: {e}")

    def _adjust_pattern_confidence(self) -> int:
        """パターン信頼度調整"""

        adjustments = 0

        try:
            for pattern in self.learned_patterns:
                old_confidence = pattern.confidence

                # 効果性に基づく信頼度調整
                if pattern.effectiveness >= 0.9:
                    pattern.confidence = LearningConfidence.VERY_HIGH
                elif pattern.effectiveness >= 0.8:
                    pattern.confidence = LearningConfidence.HIGH
                elif pattern.effectiveness >= 0.6:
                    pattern.confidence = LearningConfidence.MEDIUM
                else:
                    pattern.confidence = LearningConfidence.LOW

                if old_confidence != pattern.confidence:
                    adjustments += 1

        except Exception as e:
            logger.warning(f"⚠️ 信頼度調整エラー: {e}")

        return adjustments

    def _identify_optimization_opportunities(self) -> List[OptimizationRecommendation]:
        """最適化機会特定"""

        opportunities = []

        try:
            # 高信頼度パターンから最適化推奨を生成
            high_confidence_patterns = [
                p for p in self.learned_patterns
                if p.confidence in [LearningConfidence.HIGH, LearningConfidence.VERY_HIGH]
            ]

            # カテゴリ別最適化機会
            for category in LearningCategory:
                category_patterns = [p for p in high_confidence_patterns if p.category == category]

                if category_patterns:
                    opportunity = self._generate_category_optimization(category, category_patterns)
                    if opportunity:
                        opportunities.append(opportunity)

            # 相関分析による最適化機会
            correlation_opportunities = self._analyze_pattern_correlations(high_confidence_patterns)
            opportunities.extend(correlation_opportunities)

        except Exception as e:
            logger.warning(f"⚠️ 最適化機会特定エラー: {e}")

        return opportunities

    def _generate_category_optimization(self, category: LearningCategory,
                                      patterns: List[LearningPattern]) -> Optional[OptimizationRecommendation]:
        """カテゴリ別最適化推奨生成"""

        if not patterns:
            return None

        try:
            # 最も効果的なパターンを基に推奨生成
            best_pattern = max(patterns, key=lambda p: p.effectiveness)

            recommendation_templates = {
                LearningCategory.TASK_ROUTING: {
                    "title": "タスクルーティング精度向上",
                    "description": f"学習済みパターンに基づくルーティング精度向上により、成功率{best_pattern.effectiveness:.1%}達成可能",
                    "expected_improvement": {"routing_accuracy": 0.05, "processing_efficiency": 0.03},
                    "implementation_steps": [
                        "高信頼度ルーティングパターンの自動適用",
                        "コンテキスト分析精度の向上",
                        "ルーティング決定の継続学習"
                    ]
                },
                LearningCategory.QUALITY_PREDICTION: {
                    "title": "品質予測システム強化",
                    "description": f"予測パターンの活用により、品質スコア{best_pattern.effectiveness:.1%}の精度達成",
                    "expected_improvement": {"quality_prediction_accuracy": 0.08, "failsafe_reduction": 0.1},
                    "implementation_steps": [
                        "予測モデルの学習パターン統合",
                        "事前品質チェックの強化",
                        "リスク予測精度の向上"
                    ]
                },
                LearningCategory.FAILURE_PREVENTION: {
                    "title": "失敗防止機能最適化",
                    "description": f"防止パターンにより、フェイルセーフ削減{(1-best_pattern.effectiveness):.1%}達成",
                    "expected_improvement": {"failsafe_reduction": 0.15, "prevention_effectiveness": 0.1},
                    "implementation_steps": [
                        "防止パターンの予防的適用",
                        "早期警告システムの強化",
                        "自動修正機能の拡張"
                    ]
                }
            }

            template = recommendation_templates.get(category)
            if not template:
                return None

            recommendation = OptimizationRecommendation(
                recommendation_id=f"{category.value}_{datetime.datetime.now().strftime('%Y%m%d')}",
                category=category,
                title=template["title"],
                description=template["description"],
                expected_improvement=template["expected_improvement"],
                implementation_steps=template["implementation_steps"],
                confidence_score=best_pattern.effectiveness,
                risk_level="low" if best_pattern.effectiveness > 0.8 else "medium",
                estimated_effort="medium",
                supporting_patterns=[p.pattern_id for p in patterns[:3]]
            )

            return recommendation

        except Exception as e:
            logger.warning(f"⚠️ カテゴリ最適化推奨生成エラー: {e}")
            return None

    def _analyze_pattern_correlations(self, patterns: List[LearningPattern]) -> List[OptimizationRecommendation]:
        """パターン相関分析"""

        correlations = []

        try:
            # 協業安全性向上に寄与するパターン組み合わせを特定
            safety_contributing_patterns = [
                p for p in patterns
                if p.category in [LearningCategory.FAILURE_PREVENTION, LearningCategory.QUALITY_PREDICTION]
                and p.effectiveness > 0.8
            ]

            if len(safety_contributing_patterns) >= 2:
                combined_effectiveness = statistics.mean([p.effectiveness for p in safety_contributing_patterns])

                correlation_rec = OptimizationRecommendation(
                    recommendation_id=f"correlation_safety_{datetime.datetime.now().strftime('%Y%m%d')}",
                    category=LearningCategory.OPTIMIZATION_STRATEGY,
                    title="統合的安全性向上戦略",
                    description=f"複数パターンの組み合わせにより、協業安全性{combined_effectiveness:.1%}の向上を実現",
                    expected_improvement={
                        "collaboration_safety_score": 5.0,
                        "failsafe_reduction": 0.2,
                        "overall_efficiency": 0.15
                    },
                    implementation_steps=[
                        "品質予測と失敗防止の統合実行",
                        "パターン間の相乗効果活用",
                        "包括的最適化戦略の適用"
                    ],
                    confidence_score=combined_effectiveness,
                    risk_level="low",
                    estimated_effort="high",
                    supporting_patterns=[p.pattern_id for p in safety_contributing_patterns]
                )

                correlations.append(correlation_rec)

        except Exception as e:
            logger.warning(f"⚠️ パターン相関分析エラー: {e}")

        return correlations

    def _evaluate_learning_accuracy(self) -> float:
        """学習精度評価"""

        try:
            if not self.learned_patterns:
                return 0.0

            # 効果性スコアの分布を評価
            effectiveness_scores = [p.effectiveness for p in self.learned_patterns]

            # 高効果パターンの割合
            high_effectiveness_count = len([s for s in effectiveness_scores if s >= 0.8])
            high_effectiveness_ratio = high_effectiveness_count / len(effectiveness_scores)

            # 平均効果性
            avg_effectiveness = statistics.mean(effectiveness_scores)

            # 学習精度 = 高効果割合 * 0.6 + 平均効果性 * 0.4
            learning_accuracy = high_effectiveness_ratio * 0.6 + avg_effectiveness * 0.4

            return learning_accuracy

        except Exception as e:
            logger.warning(f"⚠️ 学習精度評価エラー: {e}")
            return 0.0

    def add_feedback(self, target_pattern: str, target_action: str,
                    feedback_type: FeedbackType, performance_metrics: Dict[str, float],
                    user_satisfaction: Optional[float] = None,
                    context: Optional[Dict[str, Any]] = None) -> None:
        """フィードバック追加

        Args:
            target_pattern: 対象パターンID
            target_action: 対象アクション
            feedback_type: フィードバックタイプ
            performance_metrics: パフォーマンス指標
            user_satisfaction: ユーザー満足度 (0.0-1.0)
            context: コンテキスト情報
        """

        logger.info(f"📝 フィードバック追加: {target_pattern} - {feedback_type.value}")

        try:
            feedback = FeedbackData(
                feedback_id=f"feedback_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                feedback_type=feedback_type,
                target_pattern=target_pattern,
                target_action=target_action,
                performance_metrics=performance_metrics,
                user_satisfaction=user_satisfaction,
                timestamp=datetime.datetime.now().isoformat(),
                context=context or {}
            )

            self.feedback_history.append(feedback)

            # フィードバックに基づくパターン調整
            self._adjust_pattern_from_feedback(feedback)

            # フィードバック保存
            self._save_feedback_history()

        except Exception as e:
            logger.error(f"❌ フィードバック追加エラー: {e}")

    def _adjust_pattern_from_feedback(self, feedback: FeedbackData) -> None:
        """フィードバックからパターン調整"""

        try:
            # 対象パターンを特定
            target_pattern = None
            for pattern in self.learned_patterns:
                if pattern.pattern_id == feedback.target_pattern:
                    target_pattern = pattern
                    break

            if not target_pattern:
                return

            # フィードバックスコア計算
            if feedback.feedback_type == FeedbackType.SUCCESS:
                feedback_score = 0.8
            elif feedback.feedback_type == FeedbackType.IMPROVEMENT:
                feedback_score = 0.6
            elif feedback.feedback_type == FeedbackType.FAILURE:
                feedback_score = -0.6
            elif feedback.feedback_type == FeedbackType.REGRESSION:
                feedback_score = -0.8
            else:
                feedback_score = 0.0

            # ユーザー満足度を考慮
            if feedback.user_satisfaction is not None:
                feedback_score = (feedback_score + feedback.user_satisfaction * 2 - 1) / 2

            # パターンのフィードバックスコア更新（移動平均）
            alpha = 0.3  # 学習率
            target_pattern.feedback_score = (
                target_pattern.feedback_score * (1 - alpha) + feedback_score * alpha
            )

            # 効果性更新
            target_pattern.effectiveness = max(0.0, min(1.0, (target_pattern.feedback_score + 1) / 2))

        except Exception as e:
            logger.warning(f"⚠️ フィードバックパターン調整エラー: {e}")

    def generate_learning_report(self) -> LearningReport:
        """学習レポート生成"""

        logger.info("📊 学習レポート生成開始")

        try:
            # パターン統計
            total_patterns = len(self.learned_patterns)
            active_patterns = len([p for p in self.learned_patterns
                                 if datetime.datetime.now() - datetime.datetime.fromisoformat(p.last_seen)
                                 <= datetime.timedelta(days=30)])

            # 学習精度
            learning_accuracy = self._evaluate_learning_accuracy()

            # 最適化推奨
            optimization_suggestions = self._identify_optimization_opportunities()

            # パフォーマンス改善推定
            performance_improvements = self._estimate_performance_improvements()

            # 信頼度分布
            confidence_distribution = {}
            for conf in LearningConfidence:
                count = len([p for p in self.learned_patterns if p.confidence == conf])
                confidence_distribution[conf.value] = count

            # 最近の発見
            recent_discoveries = self._get_recent_discoveries()

            report = LearningReport(
                timestamp=datetime.datetime.now().isoformat(),
                total_patterns_learned=total_patterns,
                active_patterns=active_patterns,
                learning_accuracy=learning_accuracy,
                optimization_suggestions=optimization_suggestions,
                performance_improvements=performance_improvements,
                confidence_distribution=confidence_distribution,
                recent_discoveries=recent_discoveries
            )

            # レポート保存
            self._save_learning_report(report)

            logger.info(f"✅ 学習レポート生成完了: {total_patterns}パターン, 精度{learning_accuracy:.1%}")

            return report

        except Exception as e:
            logger.error(f"❌ 学習レポート生成エラー: {e}")
            return self._create_fallback_learning_report()

    def _estimate_performance_improvements(self) -> Dict[str, float]:
        """パフォーマンス改善推定"""

        improvements = {
            "collaboration_safety_score": 0.0,
            "task_success_rate": 0.0,
            "failsafe_reduction": 0.0,
            "processing_efficiency": 0.0
        }

        try:
            # 高効果パターンから改善推定
            high_effectiveness_patterns = [
                p for p in self.learned_patterns
                if p.effectiveness >= 0.8
            ]

            if high_effectiveness_patterns:
                avg_effectiveness = statistics.mean([p.effectiveness for p in high_effectiveness_patterns])

                # カテゴリ別改善推定
                for category in LearningCategory:
                    category_patterns = [p for p in high_effectiveness_patterns if p.category == category]

                    if category_patterns:
                        if category == LearningCategory.TASK_ROUTING:
                            improvements["task_success_rate"] += avg_effectiveness * 0.05
                            improvements["processing_efficiency"] += avg_effectiveness * 0.03

                        elif category == LearningCategory.QUALITY_PREDICTION:
                            improvements["collaboration_safety_score"] += avg_effectiveness * 2.0
                            improvements["failsafe_reduction"] += avg_effectiveness * 0.1

                        elif category == LearningCategory.FAILURE_PREVENTION:
                            improvements["failsafe_reduction"] += avg_effectiveness * 0.15
                            improvements["collaboration_safety_score"] += avg_effectiveness * 1.5

        except Exception as e:
            logger.warning(f"⚠️ パフォーマンス改善推定エラー: {e}")

        return improvements

    def _get_recent_discoveries(self) -> List[str]:
        """最近の発見取得"""

        discoveries = []

        try:
            # 最近1週間の高効果パターン
            cutoff = datetime.datetime.now() - datetime.timedelta(days=7)

            recent_patterns = [
                p for p in self.learned_patterns
                if datetime.datetime.fromisoformat(p.last_seen) >= cutoff
                and p.effectiveness >= 0.8
            ]

            for pattern in recent_patterns[:5]:  # 上位5件
                discoveries.append(
                    f"{pattern.category.value}: {pattern.action_taken} (効果性: {pattern.effectiveness:.1%})"
                )

        except Exception as e:
            logger.warning(f"⚠️ 最近の発見取得エラー: {e}")

        return discoveries

    def apply_learned_optimizations(self) -> Dict[str, Any]:
        """学習済み最適化の適用

        Returns:
            Dict[str, Any]: 適用結果
        """

        logger.info("🚀 学習済み最適化適用開始")

        try:
            application_results = {
                "optimizations_applied": 0,
                "patterns_activated": 0,
                "estimated_improvement": {},
                "application_success": True
            }

            # 高信頼度パターンの自動適用
            high_confidence_patterns = [
                p for p in self.learned_patterns
                if p.confidence == LearningConfidence.VERY_HIGH
                and p.effectiveness >= 0.9
            ]

            for pattern in high_confidence_patterns:
                try:
                    if self._apply_pattern_optimization(pattern):
                        application_results["patterns_activated"] += 1

                except Exception as e:
                    logger.warning(f"⚠️ パターン適用エラー: {pattern.pattern_id} - {e}")

            # 最適化推奨の自動実装
            optimization_suggestions = self._identify_optimization_opportunities()

            for suggestion in optimization_suggestions:
                if suggestion.risk_level == "low" and suggestion.confidence_score >= 0.9:
                    try:
                        if self._apply_optimization_suggestion(suggestion):
                            application_results["optimizations_applied"] += 1

                    except Exception as e:
                        logger.warning(f"⚠️ 最適化適用エラー: {suggestion.recommendation_id} - {e}")

            # 改善推定
            application_results["estimated_improvement"] = self._estimate_performance_improvements()

            logger.info(f"✅ 学習済み最適化適用完了: {application_results['optimizations_applied']}最適化, {application_results['patterns_activated']}パターン")

            return application_results

        except Exception as e:
            logger.error(f"❌ 学習済み最適化適用エラー: {e}")
            return {"application_success": False, "error": str(e)}

    def _apply_pattern_optimization(self, pattern: LearningPattern) -> bool:
        """パターン最適化適用"""

        try:
            # パターンカテゴリに基づく最適化適用
            if pattern.category == LearningCategory.TASK_ROUTING:
                return self._apply_routing_optimization(pattern)
            elif pattern.category == LearningCategory.QUALITY_PREDICTION:
                return self._apply_quality_optimization(pattern)
            elif pattern.category == LearningCategory.FAILURE_PREVENTION:
                return self._apply_prevention_optimization(pattern)
            else:
                return self._apply_general_optimization(pattern)

        except Exception as e:
            logger.warning(f"⚠️ パターン最適化適用エラー: {e}")
            return False

    def _apply_routing_optimization(self, pattern: LearningPattern) -> bool:
        """ルーティング最適化適用"""

        # フロー最適化システムへの統合
        try:
            optimization_file = self.collaboration_dir / "learned_routing_optimizations.json"

            optimization_data = {
                "pattern_id": pattern.pattern_id,
                "context": pattern.context,
                "recommended_action": pattern.action_taken,
                "effectiveness": pattern.effectiveness,
                "applied_timestamp": datetime.datetime.now().isoformat()
            }

            # 既存最適化読み込み
            existing_optimizations = []
            if optimization_file.exists():
                with open(optimization_file, 'r', encoding='utf-8') as f:
                    existing_optimizations = json.load(f)

            existing_optimizations.append(optimization_data)

            # 保存
            with open(optimization_file, 'w', encoding='utf-8') as f:
                json.dump(existing_optimizations, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.warning(f"⚠️ ルーティング最適化適用エラー: {e}")
            return False

    def _apply_quality_optimization(self, pattern: LearningPattern) -> bool:
        """品質最適化適用"""

        # 予防的品質チェックシステムへの統合
        try:
            quality_optimization_file = self.collaboration_dir / "learned_quality_optimizations.json"

            optimization_data = {
                "pattern_id": pattern.pattern_id,
                "quality_context": pattern.context,
                "optimization_action": pattern.action_taken,
                "expected_quality_improvement": pattern.effectiveness,
                "applied_timestamp": datetime.datetime.now().isoformat()
            }

            # 保存
            existing_optimizations = []
            if quality_optimization_file.exists():
                with open(quality_optimization_file, 'r', encoding='utf-8') as f:
                    existing_optimizations = json.load(f)

            existing_optimizations.append(optimization_data)

            with open(quality_optimization_file, 'w', encoding='utf-8') as f:
                json.dump(existing_optimizations, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.warning(f"⚠️ 品質最適化適用エラー: {e}")
            return False

    def _apply_prevention_optimization(self, pattern: LearningPattern) -> bool:
        """防止最適化適用"""

        # 効率監視システムへの統合
        try:
            prevention_optimization_file = self.collaboration_dir / "learned_prevention_optimizations.json"

            optimization_data = {
                "pattern_id": pattern.pattern_id,
                "prevention_context": pattern.context,
                "prevention_action": pattern.action_taken,
                "failsafe_reduction_potential": pattern.effectiveness,
                "applied_timestamp": datetime.datetime.now().isoformat()
            }

            # 保存
            existing_optimizations = []
            if prevention_optimization_file.exists():
                with open(prevention_optimization_file, 'r', encoding='utf-8') as f:
                    existing_optimizations = json.load(f)

            existing_optimizations.append(optimization_data)

            with open(prevention_optimization_file, 'w', encoding='utf-8') as f:
                json.dump(existing_optimizations, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.warning(f"⚠️ 防止最適化適用エラー: {e}")
            return False

    def _apply_general_optimization(self, pattern: LearningPattern) -> bool:
        """一般最適化適用"""

        try:
            # 一般的な最適化パターンの記録
            general_optimization_file = self.collaboration_dir / "learned_general_optimizations.json"

            optimization_data = {
                "pattern_id": pattern.pattern_id,
                "category": pattern.category.value,
                "optimization_context": pattern.context,
                "optimization_outcome": pattern.outcome,
                "applied_timestamp": datetime.datetime.now().isoformat()
            }

            existing_optimizations = []
            if general_optimization_file.exists():
                with open(general_optimization_file, 'r', encoding='utf-8') as f:
                    existing_optimizations = json.load(f)

            existing_optimizations.append(optimization_data)

            with open(general_optimization_file, 'w', encoding='utf-8') as f:
                json.dump(existing_optimizations, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.warning(f"⚠️ 一般最適化適用エラー: {e}")
            return False

    def _apply_optimization_suggestion(self, suggestion: OptimizationRecommendation) -> bool:
        """最適化推奨適用"""

        try:
            # 推奨の実装記録
            suggestion_implementation_file = self.collaboration_dir / "implemented_suggestions.json"

            implementation_data = {
                "recommendation_id": suggestion.recommendation_id,
                "title": suggestion.title,
                "category": suggestion.category.value,
                "expected_improvement": suggestion.expected_improvement,
                "implementation_steps": suggestion.implementation_steps,
                "confidence_score": suggestion.confidence_score,
                "implemented_timestamp": datetime.datetime.now().isoformat()
            }

            existing_implementations = []
            if suggestion_implementation_file.exists():
                with open(suggestion_implementation_file, 'r', encoding='utf-8') as f:
                    existing_implementations = json.load(f)

            existing_implementations.append(implementation_data)

            with open(suggestion_implementation_file, 'w', encoding='utf-8') as f:
                json.dump(existing_implementations, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.warning(f"⚠️ 最適化推奨適用エラー: {e}")
            return False

    # ヘルパーメソッド
    def _generate_pattern_id(self, prefix: str, context: Dict[str, Any]) -> str:
        """パターンID生成"""

        context_str = json.dumps(context, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        return f"{prefix}_{context_hash}"

    def _determine_learning_confidence(self, score: float) -> LearningConfidence:
        """学習信頼度判定"""

        if score >= 0.9:
            return LearningConfidence.VERY_HIGH
        elif score >= 0.8:
            return LearningConfidence.HIGH
        elif score >= 0.6:
            return LearningConfidence.MEDIUM
        else:
            return LearningConfidence.LOW

    def _get_score_range(self, score: float) -> str:
        """スコア範囲取得"""

        if score >= 0.9:
            return "very_high"
        elif score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "very_low"

    def _get_time_range(self, time_val: float) -> str:
        """時間範囲取得"""

        if time_val <= 1.0:
            return "very_fast"
        elif time_val <= 2.0:
            return "fast"
        elif time_val <= 5.0:
            return "normal"
        else:
            return "slow"

    def _get_improvement_range(self, improvement: float) -> str:
        """改善範囲取得"""

        if improvement >= 10.0:
            return "major"
        elif improvement >= 5.0:
            return "significant"
        elif improvement >= 2.0:
            return "moderate"
        else:
            return "minor"

    def _deduplicate_patterns(self, patterns: List[LearningPattern]) -> List[LearningPattern]:
        """パターン重複除去"""

        unique_patterns = {}

        for pattern in patterns:
            if pattern.pattern_id not in unique_patterns:
                unique_patterns[pattern.pattern_id] = pattern
            else:
                # 重複パターンは頻度を増加
                existing = unique_patterns[pattern.pattern_id]
                existing.frequency += 1
                existing.last_seen = pattern.last_seen

        return list(unique_patterns.values())

    def _pattern_exists(self, pattern: LearningPattern) -> bool:
        """パターン存在チェック"""

        return any(p.pattern_id == pattern.pattern_id for p in self.learned_patterns)

    # データ保存・読み込みメソッド
    def _save_learning_results(self, results: Dict[str, Any]) -> None:
        """学習結果保存"""

        try:
            # パターン保存
            self._save_learned_patterns()

            # 学習メトリクス更新
            self.learning_metrics.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "results": results
            })

            # 最新20件のみ保持
            if len(self.learning_metrics) > 20:
                self.learning_metrics = self.learning_metrics[-20:]

            with open(self.learning_metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_metrics, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ 学習結果保存エラー: {e}")

    def _save_learned_patterns(self) -> None:
        """学習済みパターン保存"""

        try:
            patterns_data = [asdict(pattern) for pattern in self.learned_patterns]

            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"❌ 学習パターン保存エラー: {e}")

    def _save_feedback_history(self) -> None:
        """フィードバック履歴保存"""

        try:
            feedback_data = [asdict(feedback) for feedback in self.feedback_history]

            # 最新100件のみ保持
            if len(feedback_data) > 100:
                feedback_data = feedback_data[-100:]
                self.feedback_history = self.feedback_history[-100:]

            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ フィードバック履歴保存エラー: {e}")

    def _save_learning_report(self, report: LearningReport) -> None:
        """学習レポート保存"""

        try:
            report_file = self.learning_dir / f"learning_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"❌ 学習レポート保存エラー: {e}")

    def _load_learned_patterns(self) -> List[LearningPattern]:
        """学習済みパターン読み込み"""

        if not self.patterns_file.exists():
            return []

        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)

            patterns = []
            for data in patterns_data:
                # Enum変換
                data["category"] = LearningCategory(data["category"])
                data["confidence"] = LearningConfidence(data["confidence"])

                pattern = LearningPattern(**data)
                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.warning(f"⚠️ 学習パターン読み込みエラー: {e}")
            return []

    def _load_feedback_history(self) -> List[FeedbackData]:
        """フィードバック履歴読み込み"""

        if not self.feedback_file.exists():
            return []

        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)

            feedback_list = []
            for data in feedback_data:
                # Enum変換
                data["feedback_type"] = FeedbackType(data["feedback_type"])

                feedback = FeedbackData(**data)
                feedback_list.append(feedback)

            return feedback_list

        except Exception as e:
            logger.warning(f"⚠️ フィードバック履歴読み込みエラー: {e}")
            return []

    def _load_learning_metrics(self) -> List[Dict[str, Any]]:
        """学習メトリクス読み込み"""

        if not self.learning_metrics_file.exists():
            return []

        try:
            with open(self.learning_metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ 学習メトリクス読み込みエラー: {e}")
            return []

    def _create_fallback_learning_report(self) -> LearningReport:
        """フォールバック学習レポート"""

        return LearningReport(
            timestamp=datetime.datetime.now().isoformat(),
            total_patterns_learned=0,
            active_patterns=0,
            learning_accuracy=0.0,
            optimization_suggestions=[],
            performance_improvements={},
            confidence_distribution={},
            recent_discoveries=[]
        )


def main() -> None:
    """テスト実行"""
    learning_system = ContinuousLearningSystem()

    # 協業データから学習
    learning_results = learning_system.learn_from_collaboration_data()
    print(f"新パターン発見: {learning_results.get('new_patterns_discovered', 0)}件")
    print(f"パターン更新: {learning_results.get('patterns_updated', 0)}件")
    print(f"学習精度: {learning_results.get('learning_accuracy', 0):.1%}")

    # 学習レポート生成
    report = learning_system.generate_learning_report()
    print(f"学習済みパターン: {report.total_patterns_learned}件")
    print(f"最適化提案: {len(report.optimization_suggestions)}件")

    # 学習済み最適化適用
    application_results = learning_system.apply_learned_optimizations()
    print(f"適用された最適化: {application_results.get('optimizations_applied', 0)}件")


if __name__ == "__main__":
    main()
