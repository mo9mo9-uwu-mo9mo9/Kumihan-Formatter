#!/usr/bin/env python3
"""
QualityLearningSystem
品質パターン学習・蓄積システム - プロジェクト固有品質基準進化・品質予測・事前改善提案
機械学習ベースの品質向上・パターン認識・自動基準調整システム
"""

import os
import json
import pickle
import datetime
import time
import math
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import collections

class LearningCategory(Enum):
    """学習カテゴリ"""
    QUALITY_PATTERNS = "quality_patterns"       # 品質パターン
    ERROR_PATTERNS = "error_patterns"           # エラーパターン
    IMPROVEMENT_PATTERNS = "improvement_patterns" # 改善パターン
    PROJECT_STANDARDS = "project_standards"     # プロジェクト基準
    DEVELOPER_PATTERNS = "developer_patterns"  # 開発者パターン

class LearningConfidence(Enum):
    """学習信頼度"""
    HIGH = "high"        # 高（十分なデータ）
    MEDIUM = "medium"    # 中（ある程度のデータ）
    LOW = "low"          # 低（限定的なデータ）
    LEARNING = "learning" # 学習中

@dataclass
class QualityPattern:
    """品質パターン"""
    pattern_id: str
    category: LearningCategory
    pattern_type: str
    description: str
    
    # パターンデータ
    code_patterns: List[str]
    quality_indicators: Dict[str, float]
    success_conditions: Dict[str, Any]
    
    # 学習データ
    occurrence_count: int
    success_rate: float
    confidence: LearningConfidence
    
    # 統計
    first_seen: str
    last_updated: str
    effectiveness_score: float

@dataclass
class LearningEvent:
    """学習イベント"""
    event_id: str
    timestamp: str
    category: LearningCategory
    
    # 品質データ
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement: float
    
    # コンテキスト
    file_path: str
    change_type: str
    ai_agent: str
    
    # 学習用データ
    code_before: Optional[str] = None
    code_after: Optional[str] = None
    correction_applied: Optional[str] = None

@dataclass
class ProjectStandard:
    """プロジェクト固有品質基準"""
    standard_id: str
    name: str
    description: str
    
    # 基準値
    thresholds: Dict[str, float]
    weights: Dict[str, float]
    
    # 学習データ
    adaptation_count: int
    effectiveness: float
    last_updated: str
    
    # 適用条件
    applicable_files: List[str]
    applicable_phases: List[str]

class PatternMatcher:
    """パターンマッチング・学習システム"""
    
    def __init__(self):
        self.patterns: Dict[str, QualityPattern] = {}
        self.pattern_stats = {
            "total_patterns": 0,
            "successful_matches": 0,
            "learning_accuracy": 0.0
        }
    
    def learn_from_quality_data(self, learning_event: LearningEvent) -> None:
        """品質データからの学習"""
        
        print(f"📚 パターン学習: {learning_event.category.value}")
        
        # 改善パターン抽出
        if learning_event.improvement > 0.1:  # 10%以上の改善
            self._extract_improvement_pattern(learning_event)
        
        # エラーパターン抽出
        if learning_event.improvement < -0.05:  # 5%以上の劣化
            self._extract_error_pattern(learning_event)
        
        # コード変更パターン学習
        if learning_event.code_before and learning_event.code_after:
            self._learn_code_change_pattern(learning_event)
    
    def _extract_improvement_pattern(self, event: LearningEvent) -> None:
        """改善パターン抽出"""
        
        pattern_id = f"improve_{event.change_type}_{hash(event.file_path) % 1000}"
        
        if pattern_id in self.patterns:
            # 既存パターンの更新
            pattern = self.patterns[pattern_id]
            pattern.occurrence_count += 1
            pattern.effectiveness_score = (
                pattern.effectiveness_score * (pattern.occurrence_count - 1) + event.improvement
            ) / pattern.occurrence_count
            pattern.last_updated = event.timestamp
            
            # 信頼度更新
            if pattern.occurrence_count >= 10:
                pattern.confidence = LearningConfidence.HIGH
            elif pattern.occurrence_count >= 5:
                pattern.confidence = LearningConfidence.MEDIUM
            else:
                pattern.confidence = LearningConfidence.LOW
                
        else:
            # 新しいパターンの作成
            pattern = QualityPattern(
                pattern_id=pattern_id,
                category=LearningCategory.IMPROVEMENT_PATTERNS,
                pattern_type=event.change_type,
                description=f"改善パターン: {event.change_type}",
                code_patterns=[],
                quality_indicators=event.after_metrics,
                success_conditions={"min_improvement": 0.1},
                occurrence_count=1,
                success_rate=1.0,
                confidence=LearningConfidence.LEARNING,
                first_seen=event.timestamp,
                last_updated=event.timestamp,
                effectiveness_score=event.improvement
            )
            
            self.patterns[pattern_id] = pattern
            self.pattern_stats["total_patterns"] += 1
        
        print(f"   ✅ 改善パターン学習完了: {pattern_id} (効果: {event.improvement:.3f})")
    
    def _extract_error_pattern(self, event: LearningEvent) -> None:
        """エラーパターン抽出"""
        
        pattern_id = f"error_{event.change_type}_{hash(event.file_path) % 1000}"
        
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.occurrence_count += 1
            pattern.last_updated = event.timestamp
        else:
            pattern = QualityPattern(
                pattern_id=pattern_id,
                category=LearningCategory.ERROR_PATTERNS,
                pattern_type=event.change_type,
                description=f"エラーパターン: {event.change_type}",
                code_patterns=[],
                quality_indicators=event.before_metrics,
                success_conditions={"avoid_degradation": True},
                occurrence_count=1,
                success_rate=0.0,
                confidence=LearningConfidence.LEARNING,
                first_seen=event.timestamp,
                last_updated=event.timestamp,
                effectiveness_score=abs(event.improvement)
            )
            
            self.patterns[pattern_id] = pattern
        
        print(f"   ⚠️ エラーパターン学習: {pattern_id} (劣化: {abs(event.improvement):.3f})")
    
    def _learn_code_change_pattern(self, event: LearningEvent) -> None:
        """コード変更パターン学習"""
        
        # 簡単な差分パターン抽出
        try:
            before_lines = event.code_before.split('\n')
            after_lines = event.code_after.split('\n')
            
            # 変更されたパターンを抽出
            change_patterns = []
            for i, (before, after) in enumerate(zip(before_lines, after_lines)):
                if before.strip() != after.strip():
                    change_patterns.append({
                        "before": before.strip(),
                        "after": after.strip(),
                        "line": i + 1
                    })
            
            if change_patterns:
                pattern_id = f"code_change_{event.change_type}_{len(change_patterns)}"
                
                if pattern_id in self.patterns:
                    pattern = self.patterns[pattern_id]
                    pattern.occurrence_count += 1
                    # 成功率更新
                    if event.improvement > 0:
                        pattern.success_rate = (
                            pattern.success_rate * (pattern.occurrence_count - 1) + 1
                        ) / pattern.occurrence_count
                    else:
                        pattern.success_rate = (
                            pattern.success_rate * (pattern.occurrence_count - 1)
                        ) / pattern.occurrence_count
                else:
                    pattern = QualityPattern(
                        pattern_id=pattern_id,
                        category=LearningCategory.QUALITY_PATTERNS,
                        pattern_type="code_change",
                        description=f"コード変更パターン: {event.change_type}",
                        code_patterns=[json.dumps(change_patterns)],
                        quality_indicators=event.after_metrics,
                        success_conditions={"improvement_required": True},
                        occurrence_count=1,
                        success_rate=1.0 if event.improvement > 0 else 0.0,
                        confidence=LearningConfidence.LEARNING,
                        first_seen=event.timestamp,
                        last_updated=event.timestamp,
                        effectiveness_score=event.improvement
                    )
                    
                    self.patterns[pattern_id] = pattern
                
        except Exception as e:
            print(f"⚠️ コード変更パターン学習エラー: {e}")
    
    def predict_quality_improvement(self, file_path: str, change_type: str) -> Dict[str, Any]:
        """品質改善予測"""
        
        # 関連パターン検索
        relevant_patterns = []
        for pattern in self.patterns.values():
            if (pattern.pattern_type == change_type and 
                pattern.category in [LearningCategory.IMPROVEMENT_PATTERNS, LearningCategory.QUALITY_PATTERNS]):
                relevant_patterns.append(pattern)
        
        if not relevant_patterns:
            return {
                "predicted_improvement": 0.0,
                "confidence": "low",
                "recommendations": ["十分な学習データがありません"]
            }
        
        # 予測計算
        total_weight = 0
        weighted_improvement = 0
        
        for pattern in relevant_patterns:
            # 信頼度による重み
            confidence_weights = {
                LearningConfidence.HIGH: 1.0,
                LearningConfidence.MEDIUM: 0.7,
                LearningConfidence.LOW: 0.4,
                LearningConfidence.LEARNING: 0.2
            }
            
            weight = confidence_weights.get(pattern.confidence, 0.2) * pattern.occurrence_count
            weighted_improvement += pattern.effectiveness_score * weight
            total_weight += weight
        
        predicted_improvement = weighted_improvement / total_weight if total_weight > 0 else 0.0
        
        # 信頼度評価
        confidence = "high" if total_weight > 10 else "medium" if total_weight > 5 else "low"
        
        # 推奨事項生成
        recommendations = self._generate_improvement_recommendations(relevant_patterns)
        
        return {
            "predicted_improvement": predicted_improvement,
            "confidence": confidence,
            "supporting_patterns": len(relevant_patterns),
            "recommendations": recommendations
        }
    
    def _generate_improvement_recommendations(self, patterns: List[QualityPattern]) -> List[str]:
        """改善推奨事項生成"""
        
        recommendations = []
        
        # 高効果パターンの推奨
        high_effect_patterns = [p for p in patterns if p.effectiveness_score > 0.2]
        if high_effect_patterns:
            best_pattern = max(high_effect_patterns, key=lambda p: p.effectiveness_score)
            recommendations.append(f"高効果パターン '{best_pattern.pattern_type}' の適用を推奨します")
        
        # 高信頼度パターンの推奨
        high_confidence_patterns = [p for p in patterns if p.confidence == LearningConfidence.HIGH]
        if high_confidence_patterns:
            recommendations.append(f"実績のあるパターン（{len(high_confidence_patterns)}件）を活用してください")
        
        # 成功率による推奨
        high_success_patterns = [p for p in patterns if p.success_rate > 0.8]
        if high_success_patterns:
            recommendations.append(f"成功率の高いアプローチ（{len(high_success_patterns)}件）を検討してください")
        
        return recommendations

class ProjectStandardsEvolver:
    """プロジェクト固有品質基準進化システム"""
    
    def __init__(self):
        self.standards: Dict[str, ProjectStandard] = {}
        self.evolution_history: List[Dict[str, Any]] = []
        
        # デフォルト基準を初期化
        self._initialize_default_standards()
    
    def _initialize_default_standards(self) -> None:
        """デフォルト品質基準初期化"""
        
        # 基本品質基準
        basic_standard = ProjectStandard(
            standard_id="basic_quality",
            name="基本品質基準",
            description="プロジェクト基本的な品質基準",
            thresholds={
                "syntax": 0.95,
                "type_check": 0.8,
                "lint": 0.8,
                "format": 0.9,
                "security": 0.9,
                "performance": 0.7
            },
            weights={
                "syntax": 0.2,
                "type_check": 0.25,
                "lint": 0.2,
                "format": 0.1,
                "security": 0.15,
                "performance": 0.1
            },
            adaptation_count=0,
            effectiveness=0.8,
            last_updated=datetime.datetime.now().isoformat(),
            applicable_files=["*.py"],
            applicable_phases=["implementation", "integration"]
        )
        
        self.standards["basic_quality"] = basic_standard
    
    def evolve_standards(self, learning_events: List[LearningEvent]) -> Dict[str, Any]:
        """品質基準進化"""
        
        print(f"🔄 品質基準進化開始: {len(learning_events)}イベント分析")
        
        evolution_results = {}
        
        for standard_id, standard in self.standards.items():
            print(f"   📊 基準進化: {standard.name}")
            
            # 関連イベント抽出
            relevant_events = self._filter_relevant_events(learning_events, standard)
            
            if len(relevant_events) < 3:
                print(f"   ⚠️ 学習データ不足: {len(relevant_events)}件")
                continue
            
            # 基準値の最適化
            optimized_thresholds = self._optimize_thresholds(standard, relevant_events)
            optimized_weights = self._optimize_weights(standard, relevant_events)
            
            # 効果評価
            effectiveness = self._evaluate_effectiveness(standard, relevant_events)
            
            # 基準更新
            if effectiveness > standard.effectiveness:
                old_thresholds = standard.thresholds.copy()
                old_weights = standard.weights.copy()
                
                standard.thresholds = optimized_thresholds
                standard.weights = optimized_weights
                standard.effectiveness = effectiveness
                standard.adaptation_count += 1
                standard.last_updated = datetime.datetime.now().isoformat()
                
                evolution_results[standard_id] = {
                    "updated": True,
                    "old_effectiveness": standard.effectiveness,
                    "new_effectiveness": effectiveness,
                    "threshold_changes": self._calculate_changes(old_thresholds, optimized_thresholds),
                    "weight_changes": self._calculate_changes(old_weights, optimized_weights)
                }
                
                print(f"   ✅ 基準更新: 効果 {standard.effectiveness:.3f} → {effectiveness:.3f}")
            else:
                evolution_results[standard_id] = {
                    "updated": False,
                    "reason": "改善効果なし"
                }
                print(f"   📋 基準維持: 現在の効果 {effectiveness:.3f}")
        
        # 進化履歴記録
        self.evolution_history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "events_analyzed": len(learning_events),
            "standards_updated": len([r for r in evolution_results.values() if r.get("updated")]),
            "results": evolution_results
        })
        
        return evolution_results
    
    def _filter_relevant_events(self, events: List[LearningEvent], standard: ProjectStandard) -> List[LearningEvent]:
        """関連イベント抽出"""
        
        relevant_events = []
        
        for event in events:
            # ファイルタイプチェック
            file_matches = any(
                event.file_path.endswith(pattern.replace("*", ""))
                for pattern in standard.applicable_files
            )
            
            if file_matches:
                relevant_events.append(event)
        
        return relevant_events
    
    def _optimize_thresholds(self, standard: ProjectStandard, events: List[LearningEvent]) -> Dict[str, float]:
        """閾値最適化"""
        
        optimized = standard.thresholds.copy()
        
        # 各品質指標の成功率分析
        for metric_name in standard.thresholds.keys():
            metric_values = []
            improvements = []
            
            for event in events:
                if metric_name in event.after_metrics:
                    metric_values.append(event.after_metrics[metric_name])
                    improvements.append(event.improvement)
            
            if len(metric_values) < 2:
                continue
            
            # 改善との相関から最適閾値を推定
            correlation = self._calculate_correlation(metric_values, improvements)
            
            if correlation > 0.3:  # 正の相関がある場合
                # 成功例の平均値を基準に設定
                successful_values = [
                    v for v, i in zip(metric_values, improvements) if i > 0
                ]
                if successful_values:
                    avg_successful = sum(successful_values) / len(successful_values)
                    # 現在値との重み付き平均で調整
                    optimized[metric_name] = (
                        standard.thresholds[metric_name] * 0.7 + avg_successful * 0.3
                    )
        
        return optimized
    
    def _optimize_weights(self, standard: ProjectStandard, events: List[LearningEvent]) -> Dict[str, float]:
        """重み最適化"""
        
        # 各品質指標の改善への影響度分析
        influences = {}
        
        for metric_name in standard.weights.keys():
            metric_changes = []
            improvements = []
            
            for event in events:
                if (metric_name in event.before_metrics and 
                    metric_name in event.after_metrics):
                    change = event.after_metrics[metric_name] - event.before_metrics[metric_name]
                    metric_changes.append(change)
                    improvements.append(event.improvement)
            
            if len(metric_changes) >= 2:
                # 変化量と改善の相関から影響度計算
                correlation = self._calculate_correlation(metric_changes, improvements)
                influences[metric_name] = max(0, correlation)
        
        # 重みの正規化
        if influences:
            total_influence = sum(influences.values())
            if total_influence > 0:
                optimized_weights = {}
                for metric_name in standard.weights.keys():
                    influence = influences.get(metric_name, 0.1)
                    # 現在の重みとの重み付き平均
                    new_weight = standard.weights[metric_name] * 0.8 + (influence / total_influence) * 0.2
                    optimized_weights[metric_name] = new_weight
                
                return optimized_weights
        
        return standard.weights.copy()
    
    def _evaluate_effectiveness(self, standard: ProjectStandard, events: List[LearningEvent]) -> float:
        """効果評価"""
        
        if not events:
            return standard.effectiveness
        
        # 平均改善率を効果として評価
        improvements = [event.improvement for event in events]
        avg_improvement = sum(improvements) / len(improvements)
        
        # 成功率も考慮
        successful_events = len([i for i in improvements if i > 0])
        success_rate = successful_events / len(improvements)
        
        # 総合効果スコア
        effectiveness = (avg_improvement + success_rate) / 2
        
        return max(0.0, min(1.0, effectiveness))
    
    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """相関係数計算"""
        
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        x_variance = sum((x - x_mean) ** 2 for x in x_values)
        y_variance = sum((y - y_mean) ** 2 for y in y_values)
        
        denominator = math.sqrt(x_variance * y_variance)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_changes(self, old_values: Dict[str, float], new_values: Dict[str, float]) -> Dict[str, float]:
        """変更量計算"""
        
        changes = {}
        for key in old_values.keys():
            if key in new_values:
                changes[key] = new_values[key] - old_values[key]
        
        return changes
    
    def get_project_standards(self, file_path: str, phase: str) -> Optional[ProjectStandard]:
        """プロジェクト基準取得"""
        
        for standard in self.standards.values():
            # ファイル適用チェック
            file_matches = any(
                file_path.endswith(pattern.replace("*", ""))
                for pattern in standard.applicable_files
            )
            
            # フェーズ適用チェック
            phase_matches = phase in standard.applicable_phases
            
            if file_matches and phase_matches:
                return standard
        
        return None

class QualityLearningSystem:
    """品質学習システム統合管理"""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.standards_evolver = ProjectStandardsEvolver()
        
        self.data_dir = Path("postbox/quality/learning")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.learning_events_path = self.data_dir / "learning_events.json"
        self.patterns_path = self.data_dir / "patterns.json"
        self.standards_path = self.data_dir / "standards.json"
        self.predictions_path = self.data_dir / "predictions.json"
        
        # 既存データ読み込み
        self._load_learning_data()
        
        print("📚 QualityLearningSystem 初期化完了")
    
    def learn_from_quality_change(self, file_path: str, change_type: str,
                                before_metrics: Dict[str, float], after_metrics: Dict[str, float],
                                ai_agent: str = "unknown", code_before: Optional[str] = None,
                                code_after: Optional[str] = None, correction_applied: Optional[str] = None) -> str:
        """品質変化からの学習"""
        
        improvement = self._calculate_improvement(before_metrics, after_metrics)
        
        # 学習イベント作成
        event = LearningEvent(
            event_id=f"learn_{int(time.time() * 1000)}",
            timestamp=datetime.datetime.now().isoformat(),
            category=LearningCategory.QUALITY_PATTERNS,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement=improvement,
            file_path=file_path,
            change_type=change_type,
            ai_agent=ai_agent,
            code_before=code_before,
            code_after=code_after,
            correction_applied=correction_applied
        )
        
        print(f"📚 品質学習開始: {file_path} ({change_type}) - 改善: {improvement:.3f}")
        
        # パターン学習
        self.pattern_matcher.learn_from_quality_data(event)
        
        # 学習イベント保存
        self._save_learning_event(event)
        
        # 定期的な基準進化（イベント数が一定数に達した場合）
        if self._should_evolve_standards():
            self._trigger_standards_evolution()
        
        print(f"✅ 学習完了: {event.event_id}")
        
        return event.event_id
    
    def predict_quality_impact(self, file_path: str, change_type: str, 
                             current_metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """品質影響予測"""
        
        print(f"🔮 品質影響予測: {file_path} ({change_type})")
        
        # パターンベース予測
        pattern_prediction = self.pattern_matcher.predict_quality_improvement(file_path, change_type)
        
        # プロジェクト基準ベース予測
        standards_prediction = self._predict_from_standards(file_path, change_type, current_metrics)
        
        # 統合予測
        combined_prediction = self._combine_predictions(pattern_prediction, standards_prediction)
        
        # 予測結果保存
        self._save_prediction(file_path, change_type, combined_prediction)
        
        return combined_prediction
    
    def get_adaptive_quality_standards(self, file_path: str, phase: str = "implementation") -> Dict[str, Any]:
        """適応的品質基準取得"""
        
        # プロジェクト固有基準取得
        project_standard = self.standards_evolver.get_project_standards(file_path, phase)
        
        if project_standard:
            return {
                "standard_id": project_standard.standard_id,
                "name": project_standard.name,
                "thresholds": project_standard.thresholds,
                "weights": project_standard.weights,
                "effectiveness": project_standard.effectiveness,
                "adaptation_count": project_standard.adaptation_count,
                "last_updated": project_standard.last_updated,
                "is_adaptive": True
            }
        else:
            # デフォルト基準
            return {
                "standard_id": "default",
                "name": "デフォルト品質基準",
                "thresholds": {
                    "syntax": 0.95, "type_check": 0.8, "lint": 0.8,
                    "format": 0.9, "security": 0.9, "performance": 0.7
                },
                "weights": {
                    "syntax": 0.2, "type_check": 0.25, "lint": 0.2,
                    "format": 0.1, "security": 0.15, "performance": 0.1
                },
                "effectiveness": 0.7,
                "adaptation_count": 0,
                "last_updated": datetime.datetime.now().isoformat(),
                "is_adaptive": False
            }
    
    def generate_improvement_recommendations(self, file_path: str, 
                                           current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """改善推奨事項生成"""
        
        recommendations = []
        
        # 現在の品質基準取得
        standards = self.get_adaptive_quality_standards(file_path)
        
        # 基準未達成項目の特定
        underperforming_metrics = []
        for metric, threshold in standards["thresholds"].items():
            if metric in current_metrics and current_metrics[metric] < threshold:
                underperforming_metrics.append({
                    "metric": metric,
                    "current": current_metrics[metric],
                    "threshold": threshold,
                    "gap": threshold - current_metrics[metric]
                })
        
        # 学習パターンベースの推奨事項
        for metric_info in underperforming_metrics:
            metric = metric_info["metric"]
            
            # 関連する改善パターン検索
            relevant_patterns = [
                p for p in self.pattern_matcher.patterns.values()
                if (p.category == LearningCategory.IMPROVEMENT_PATTERNS and
                    metric in p.quality_indicators)
            ]
            
            if relevant_patterns:
                best_pattern = max(relevant_patterns, key=lambda p: p.effectiveness_score)
                
                recommendation = {
                    "metric": metric,
                    "current_score": metric_info["current"],
                    "target_score": metric_info["threshold"],
                    "recommended_action": f"{best_pattern.pattern_type}による改善",
                    "expected_improvement": best_pattern.effectiveness_score,
                    "confidence": best_pattern.confidence.value,
                    "pattern_id": best_pattern.pattern_id,
                    "evidence": f"{best_pattern.occurrence_count}回の成功実績"
                }
                
                recommendations.append(recommendation)
        
        # 優先度順にソート
        recommendations.sort(key=lambda r: r["expected_improvement"] * (r["target_score"] - r["current_score"]), reverse=True)
        
        return recommendations
    
    def _calculate_improvement(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        """改善度計算"""
        
        common_metrics = set(before.keys()) & set(after.keys())
        if not common_metrics:
            return 0.0
        
        improvements = []
        for metric in common_metrics:
            if before[metric] > 0:  # ゼロ除算回避
                improvement = (after[metric] - before[metric]) / before[metric]
                improvements.append(improvement)
        
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def _should_evolve_standards(self) -> bool:
        """基準進化トリガー判定"""
        
        # 学習イベント数チェック
        try:
            if self.learning_events_path.exists():
                with open(self.learning_events_path, 'r', encoding='utf-8') as f:
                    events = json.load(f)
                return len(events) % 20 == 0  # 20イベントごとに進化
        except:
            pass
        
        return False
    
    def _trigger_standards_evolution(self) -> None:
        """基準進化実行"""
        
        print("🔄 品質基準進化トリガー")
        
        try:
            # 最近の学習イベント取得
            recent_events = self._get_recent_learning_events()
            
            if len(recent_events) >= 5:
                # 基準進化実行
                evolution_results = self.standards_evolver.evolve_standards(recent_events)
                
                # 進化結果保存
                self._save_evolution_results(evolution_results)
                
                print(f"✅ 基準進化完了: {len(evolution_results)}基準処理")
            else:
                print(f"⚠️ 進化データ不足: {len(recent_events)}イベント")
                
        except Exception as e:
            print(f"❌ 基準進化エラー: {e}")
    
    def _predict_from_standards(self, file_path: str, change_type: str, 
                              current_metrics: Optional[Dict[str, float]]) -> Dict[str, Any]:
        """基準ベース予測"""
        
        standards = self.get_adaptive_quality_standards(file_path)
        
        if not current_metrics:
            return {
                "predicted_improvement": 0.0,
                "confidence": "low",
                "recommendations": ["現在のメトリクスが不明です"]
            }
        
        # 基準との差分から改善可能性推定
        potential_improvements = []
        for metric, threshold in standards["thresholds"].items():
            if metric in current_metrics:
                gap = threshold - current_metrics[metric]
                if gap > 0:
                    potential_improvements.append(gap)
        
        if potential_improvements:
            avg_potential = sum(potential_improvements) / len(potential_improvements)
            
            return {
                "predicted_improvement": min(avg_potential, 0.3),  # 最大30%改善
                "confidence": "medium",
                "recommendations": [f"基準未達成項目（{len(potential_improvements)}件）の改善を推奨"]
            }
        else:
            return {
                "predicted_improvement": 0.05,  # 微小改善
                "confidence": "high",
                "recommendations": ["現在の品質基準を満たしています"]
            }
    
    def _combine_predictions(self, pattern_pred: Dict[str, Any], 
                           standards_pred: Dict[str, Any]) -> Dict[str, Any]:
        """予測結果統合"""
        
        # 重み付き平均で統合
        pattern_weight = 0.7 if pattern_pred["confidence"] == "high" else 0.5
        standards_weight = 1.0 - pattern_weight
        
        combined_improvement = (
            pattern_pred["predicted_improvement"] * pattern_weight +
            standards_pred["predicted_improvement"] * standards_weight
        )
        
        # 信頼度統合
        confidences = [pattern_pred["confidence"], standards_pred["confidence"]]
        if "high" in confidences:
            combined_confidence = "high"
        elif "medium" in confidences:
            combined_confidence = "medium"
        else:
            combined_confidence = "low"
        
        # 推奨事項統合
        combined_recommendations = (
            pattern_pred["recommendations"] + standards_pred["recommendations"]
        )
        
        return {
            "predicted_improvement": combined_improvement,
            "confidence": combined_confidence,
            "recommendations": combined_recommendations,
            "pattern_contribution": pattern_weight,
            "standards_contribution": standards_weight,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _save_learning_event(self, event: LearningEvent) -> None:
        """学習イベント保存"""
        
        try:
            events = []
            if self.learning_events_path.exists():
                with open(self.learning_events_path, 'r', encoding='utf-8') as f:
                    events = json.load(f)
            
            events.append(asdict(event))
            
            # サイズ制限（最新1000件）
            if len(events) > 1000:
                events = events[-1000:]
            
            with open(self.learning_events_path, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 学習イベント保存エラー: {e}")
    
    def _save_prediction(self, file_path: str, change_type: str, prediction: Dict[str, Any]) -> None:
        """予測結果保存"""
        
        try:
            predictions = []
            if self.predictions_path.exists():
                with open(self.predictions_path, 'r', encoding='utf-8') as f:
                    predictions = json.load(f)
            
            prediction_entry = {
                "file_path": file_path,
                "change_type": change_type,
                "prediction": prediction,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            predictions.append(prediction_entry)
            
            # サイズ制限（最新500件）
            if len(predictions) > 500:
                predictions = predictions[-500:]
            
            with open(self.predictions_path, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 予測結果保存エラー: {e}")
    
    def _get_recent_learning_events(self) -> List[LearningEvent]:
        """最近の学習イベント取得"""
        
        try:
            if self.learning_events_path.exists():
                with open(self.learning_events_path, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
                
                # 最新20件を取得
                recent_data = events_data[-20:]
                
                # LearningEventオブジェクトに変換
                events = []
                for data in recent_data:
                    event = LearningEvent(
                        event_id=data["event_id"],
                        timestamp=data["timestamp"],
                        category=LearningCategory(data["category"]),
                        before_metrics=data["before_metrics"],
                        after_metrics=data["after_metrics"],
                        improvement=data["improvement"],
                        file_path=data["file_path"],
                        change_type=data["change_type"],
                        ai_agent=data["ai_agent"],
                        code_before=data.get("code_before"),
                        code_after=data.get("code_after"),
                        correction_applied=data.get("correction_applied")
                    )
                    events.append(event)
                
                return events
        except Exception as e:
            print(f"⚠️ 学習イベント読み込みエラー: {e}")
        
        return []
    
    def _save_evolution_results(self, results: Dict[str, Any]) -> None:
        """進化結果保存"""
        
        evolution_path = self.data_dir / "evolution_history.json"
        
        try:
            history = []
            if evolution_path.exists():
                with open(evolution_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "results": results
            })
            
            # サイズ制限（最新100件）
            if len(history) > 100:
                history = history[-100:]
            
            with open(evolution_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 進化結果保存エラー: {e}")
    
    def _load_learning_data(self) -> None:
        """学習データ読み込み"""
        
        try:
            # パターンデータ読み込み
            if self.patterns_path.exists():
                with open(self.patterns_path, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                # TODO: QualityPatternオブジェクトに変換
                print("📋 学習パターン読み込み完了")
            
            # 基準データ読み込み
            if self.standards_path.exists():
                with open(self.standards_path, 'r', encoding='utf-8') as f:
                    standards_data = json.load(f)
                # TODO: ProjectStandardオブジェクトに変換
                print("📋 品質基準読み込み完了")
                
        except Exception as e:
            print(f"⚠️ 学習データ読み込みエラー: {e}")
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """学習システムサマリー取得"""
        
        return {
            "patterns": {
                "total": len(self.pattern_matcher.patterns),
                "by_category": {
                    category.value: len([
                        p for p in self.pattern_matcher.patterns.values() 
                        if p.category == category
                    ])
                    for category in LearningCategory
                },
                "statistics": self.pattern_matcher.pattern_stats
            },
            "standards": {
                "total": len(self.standards_evolver.standards),
                "adaptation_counts": {
                    std_id: std.adaptation_count
                    for std_id, std in self.standards_evolver.standards.items()
                },
                "evolution_history": len(self.standards_evolver.evolution_history)
            },
            "learning_status": "active",
            "last_updated": datetime.datetime.now().isoformat()
        }

def main():
    """テスト実行"""
    print("🧪 QualityLearningSystem テスト開始")
    
    learning_system = QualityLearningSystem()
    
    # 学習テスト
    print("\n=== 品質学習テスト ===")
    
    before_metrics = {"syntax": 0.8, "type_check": 0.7, "lint": 0.75}
    after_metrics = {"syntax": 0.95, "type_check": 0.85, "lint": 0.9}
    
    event_id = learning_system.learn_from_quality_change(
        file_path="test_file.py",
        change_type="type_annotation",
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        ai_agent="test_agent"
    )
    
    print(f"✅ 学習完了: {event_id}")
    
    # 予測テスト
    print("\n=== 品質予測テスト ===")
    
    prediction = learning_system.predict_quality_impact(
        file_path="test_file.py",
        change_type="type_annotation",
        current_metrics={"syntax": 0.9, "type_check": 0.8}
    )
    
    print(f"🔮 予測結果:")
    print(f"   改善予測: {prediction['predicted_improvement']:.3f}")
    print(f"   信頼度: {prediction['confidence']}")
    
    # 適応的基準テスト
    print("\n=== 適応的品質基準テスト ===")
    
    standards = learning_system.get_adaptive_quality_standards("test_file.py")
    print(f"📊 適応基準: {standards['name']}")
    print(f"   効果: {standards['effectiveness']:.3f}")
    print(f"   適応回数: {standards['adaptation_count']}")
    
    # 推奨事項テスト
    print("\n=== 改善推奨事項テスト ===")
    
    recommendations = learning_system.generate_improvement_recommendations(
        "test_file.py",
        {"syntax": 0.9, "type_check": 0.7, "lint": 0.8}
    )
    
    print(f"💡 推奨事項: {len(recommendations)}件")
    for rec in recommendations[:2]:
        print(f"   - {rec['metric']}: {rec['recommended_action']}")
    
    # サマリー表示
    summary = learning_system.get_learning_summary()
    print(f"\n📊 学習システムサマリー:")
    print(f"   学習パターン: {summary['patterns']['total']}件")
    print(f"   品質基準: {summary['standards']['total']}件")
    
    print("✅ QualityLearningSystem テスト完了")

if __name__ == "__main__":
    main()