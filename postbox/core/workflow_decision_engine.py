#!/usr/bin/env python3
"""
Workflow Decision Engine for Claude ↔ Gemini Collaboration
Claude側でのGemini使用自動判断システム
"""

import os
import json
import datetime
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class AutomationLevel(Enum):
    """自動化レベル設定"""
    MANUAL_ONLY = "manual_only"          # 手動のみ
    APPROVAL_REQUIRED = "approval_required"  # 承認必須
    SEMI_AUTO = "semi_auto"              # 半自動（重要な場合のみ承認）
    FULL_AUTO = "full_auto"              # 完全自動

class TaskComplexity(Enum):
    """タスク複雑度レベル"""
    TRIVIAL = "trivial"      # 些細（5分以内）
    SIMPLE = "simple"        # 簡単（30分以内）
    MODERATE = "moderate"    # 中程度（2時間以内）
    COMPLEX = "complex"      # 複雑（半日以内）
    CRITICAL = "critical"    # 重要（1日以上）

@dataclass
class TaskAnalysis:
    """タスク分析結果"""
    complexity: TaskComplexity
    estimated_time: int  # 分
    estimated_tokens: int
    estimated_cost: float
    risk_level: str  # low, medium, high
    gemini_benefit_score: float  # 0.0-1.0
    automation_recommendation: AutomationLevel
    confidence: float  # 0.0-1.0

@dataclass
class DecisionResult:
    """判定結果"""
    use_gemini: bool
    automation_level: AutomationLevel
    task_analysis: TaskAnalysis
    reasoning: str
    alternative_approaches: List[str]
    cost_benefit_analysis: Dict[str, Any]

class WorkflowDecisionEngine:
    """Claude ↔ Gemini協業の自動判断エンジン"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.history_path = Path("postbox/monitoring/decision_history.json")
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        # 判断基準設定
        self.thresholds = {
            "min_tokens_for_gemini": self.config.get("min_tokens_for_gemini", 1000),
            "max_cost_auto_approval": self.config.get("max_cost_auto_approval", 0.01),
            "min_benefit_score": self.config.get("min_benefit_score", 0.6),
            "complexity_threshold": self.config.get("complexity_threshold", "moderate")
        }

        print("🧠 WorkflowDecisionEngine 初期化完了")
        print(f"📊 判断基準: Token閾値={self.thresholds['min_tokens_for_gemini']}, "
              f"コスト閾値=${self.thresholds['max_cost_auto_approval']:.3f}")

    def analyze_task(self, task_description: str, target_files: List[str],
                    error_type: str = "", context: Dict[str, Any] = None) -> TaskAnalysis:
        """タスクの詳細分析"""

        print(f"🔍 タスク分析開始: {task_description}")

        # 1. ファイル分析
        file_analysis = self._analyze_target_files(target_files, error_type)

        # 2. 複雑度計算
        complexity = self._calculate_complexity(task_description, file_analysis, error_type)

        # 3. 時間・コスト見積もり
        time_estimate = self._estimate_time(complexity, file_analysis)
        token_estimate = self._estimate_tokens(task_description, file_analysis)
        cost_estimate = self._estimate_cost(token_estimate)

        # 4. リスク評価
        risk_level = self._assess_risk(complexity, file_analysis, context or {})

        # 5. Gemini効果スコア
        benefit_score = self._calculate_gemini_benefit(
            complexity, file_analysis, time_estimate, cost_estimate
        )

        # 6. 自動化レベル推奨
        automation_rec = self._recommend_automation_level(
            complexity, cost_estimate, risk_level, benefit_score
        )

        # 7. 信頼度計算
        confidence = self._calculate_confidence(file_analysis, context or {})

        analysis = TaskAnalysis(
            complexity=complexity,
            estimated_time=time_estimate,
            estimated_tokens=token_estimate,
            estimated_cost=cost_estimate,
            risk_level=risk_level,
            gemini_benefit_score=benefit_score,
            automation_recommendation=automation_rec,
            confidence=confidence
        )

        print(f"📊 分析完了: 複雑度={complexity.value}, 時間={time_estimate}分, "
              f"Token={token_estimate}, コスト=${cost_estimate:.4f}")

        return analysis

    def make_decision(self, task_analysis: TaskAnalysis,
                     user_preferences: Dict[str, Any] = None) -> DecisionResult:
        """Gemini使用判定"""

        print("🤔 Gemini使用判定開始")

        user_prefs = user_preferences or {}
        forced_mode = user_prefs.get("force_mode")  # "gemini", "claude", None

        # 強制モード処理
        if forced_mode == "gemini":
            return self._create_decision(True, AutomationLevel.FULL_AUTO, task_analysis,
                                       "ユーザー強制指定によりGemini使用")
        elif forced_mode == "claude":
            return self._create_decision(False, AutomationLevel.MANUAL_ONLY, task_analysis,
                                       "ユーザー強制指定によりClaude単独使用")

        # 自動判定ロジック
        use_gemini = False
        reasoning_parts = []

        # 1. Token数による判定
        if task_analysis.estimated_tokens >= self.thresholds["min_tokens_for_gemini"]:
            use_gemini = True
            reasoning_parts.append(f"大量Token使用予測({task_analysis.estimated_tokens})")

        # 2. 複雑度による判定
        complexity_threshold = TaskComplexity(self.thresholds["complexity_threshold"])
        if self._complexity_value(task_analysis.complexity) >= self._complexity_value(complexity_threshold):
            use_gemini = True
            reasoning_parts.append(f"高複雑度タスク({task_analysis.complexity.value})")

        # 3. 効果スコアによる判定
        if task_analysis.gemini_benefit_score >= self.thresholds["min_benefit_score"]:
            use_gemini = True
            reasoning_parts.append(f"高効果期待({task_analysis.gemini_benefit_score:.2f})")

        # 4. コスト制約チェック
        if task_analysis.estimated_cost > self.thresholds["max_cost_auto_approval"]:
            if task_analysis.automation_recommendation == AutomationLevel.FULL_AUTO:
                task_analysis.automation_recommendation = AutomationLevel.APPROVAL_REQUIRED
                reasoning_parts.append("高コストのため承認必須に変更")

        # 5. リスク考慮
        if task_analysis.risk_level == "high":
            if task_analysis.automation_recommendation in [AutomationLevel.FULL_AUTO, AutomationLevel.SEMI_AUTO]:
                task_analysis.automation_recommendation = AutomationLevel.APPROVAL_REQUIRED
                reasoning_parts.append("高リスクのため承認必須に変更")

        # 判定理由作成
        if use_gemini:
            reasoning = f"Gemini使用推奨: {', '.join(reasoning_parts)}"
        else:
            reasoning = "Claude単独処理推奨: 閾値未満またはリスクを考慮"

        print(f"🎯 判定結果: {'Gemini使用' if use_gemini else 'Claude単独'}")
        print(f"📝 理由: {reasoning}")

        decision = self._create_decision(use_gemini, task_analysis.automation_recommendation,
                                       task_analysis, reasoning)

        # 判定履歴保存
        self._save_decision_history(decision)

        return decision

    def _analyze_target_files(self, target_files: List[str], error_type: str) -> Dict[str, Any]:
        """対象ファイルの分析"""

        analysis = {
            "file_count": len(target_files),
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "error_count": 0,
            "file_sizes": [],
            "complexity_factors": []
        }

        for file_path in target_files:
            if not os.path.exists(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                lines = len(content.split('\n'))
                functions = content.count('def ')
                classes = content.count('class ')

                analysis["total_lines"] += lines
                analysis["total_functions"] += functions
                analysis["total_classes"] += classes
                analysis["file_sizes"].append(lines)

                # エラー数カウント
                if error_type:
                    error_count = self._count_file_errors(file_path, error_type)
                    analysis["error_count"] += error_count

                # 複雑度要因
                if lines > 500:
                    analysis["complexity_factors"].append(f"大規模ファイル: {file_path}")
                if functions > 20:
                    analysis["complexity_factors"].append(f"多数関数: {file_path}")
                if classes > 5:
                    analysis["complexity_factors"].append(f"多数クラス: {file_path}")

            except Exception as e:
                print(f"⚠️ ファイル分析エラー {file_path}: {e}")

        return analysis

    def _calculate_complexity(self, task_description: str, file_analysis: Dict, error_type: str) -> TaskComplexity:
        """複雑度計算"""

        score = 0

        # ファイル数による加算
        score += min(file_analysis["file_count"] * 0.5, 3)

        # 総行数による加算
        score += min(file_analysis["total_lines"] / 1000, 3)

        # エラー数による加算
        score += min(file_analysis["error_count"] / 10, 3)

        # タスクタイプによる加算
        task_lower = task_description.lower()
        if "refactor" in task_lower or "リファクタ" in task_lower:
            score += 2
        if "migrate" in task_lower or "移行" in task_lower:
            score += 2
        if "architecture" in task_lower or "アーキテクチャ" in task_lower:
            score += 3

        # エラータイプによる加算
        error_complexity = {
            "no-untyped-def": 1,
            "no-untyped-call": 2,
            "type-arg": 2,
            "call-arg": 3,
            "attr-defined": 3
        }
        score += error_complexity.get(error_type, 1)

        # 複雑度決定
        if score <= 2:
            return TaskComplexity.TRIVIAL
        elif score <= 4:
            return TaskComplexity.SIMPLE
        elif score <= 7:
            return TaskComplexity.MODERATE
        elif score <= 10:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.CRITICAL

    def _estimate_time(self, complexity: TaskComplexity, file_analysis: Dict) -> int:
        """時間見積もり（分）"""

        base_times = {
            TaskComplexity.TRIVIAL: 5,
            TaskComplexity.SIMPLE: 20,
            TaskComplexity.MODERATE: 60,
            TaskComplexity.COMPLEX: 180,
            TaskComplexity.CRITICAL: 480
        }

        base_time = base_times[complexity]

        # ファイル数による調整
        file_factor = min(file_analysis["file_count"] * 0.2, 2.0)

        # エラー数による調整
        error_factor = min(file_analysis["error_count"] * 0.1, 1.5)

        estimated_time = int(base_time * (1 + file_factor + error_factor))

        return estimated_time

    def _estimate_tokens(self, task_description: str, file_analysis: Dict) -> int:
        """Token使用量見積もり"""

        # 基本Token数
        base_tokens = 500

        # タスク説明による加算
        base_tokens += len(task_description) * 2

        # ファイル内容による加算（概算）
        content_tokens = file_analysis["total_lines"] * 3

        # コンテキスト・指示による加算
        instruction_tokens = 1000

        # Flash 2.5の効率性を考慮した調整
        total_tokens = base_tokens + content_tokens + instruction_tokens

        # Dual-Agent効率化（30%削減）
        optimized_tokens = int(total_tokens * 0.7)

        return optimized_tokens

    def _estimate_cost(self, token_estimate: int) -> float:
        """コスト見積もり（USD）"""

        # Gemini 2.5 Flash料金
        input_cost = (token_estimate / 1_000_000) * 0.30   # $0.30/1M tokens
        output_cost = (token_estimate * 0.3 / 1_000_000) * 2.50  # $2.50/1M tokens (出力は入力の30%と仮定)

        return input_cost + output_cost

    def _assess_risk(self, complexity: TaskComplexity, file_analysis: Dict, context: Dict) -> str:
        """リスク評価"""

        risk_score = 0

        # 複雑度によるリスク
        complexity_risk = {
            TaskComplexity.TRIVIAL: 0,
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 2,
            TaskComplexity.COMPLEX: 3,
            TaskComplexity.CRITICAL: 4
        }
        risk_score += complexity_risk[complexity]

        # ファイル重要度によるリスク
        critical_paths = ["main", "core", "app", "index", "__init__"]
        for factor in file_analysis.get("complexity_factors", []):
            if any(path in factor.lower() for path in critical_paths):
                risk_score += 1

        # コンテキストによるリスク
        if context.get("production_impact", False):
            risk_score += 2
        if context.get("breaking_change", False):
            risk_score += 2

        # リスクレベル決定
        if risk_score <= 2:
            return "low"
        elif risk_score <= 4:
            return "medium"
        else:
            return "high"

    def _calculate_gemini_benefit(self, complexity: TaskComplexity, file_analysis: Dict,
                                time_estimate: int, cost_estimate: float) -> float:
        """Gemini使用による効果スコア計算"""

        benefit_score = 0.0

        # 複雑度による効果
        complexity_benefit = {
            TaskComplexity.TRIVIAL: 0.1,
            TaskComplexity.SIMPLE: 0.3,
            TaskComplexity.MODERATE: 0.6,
            TaskComplexity.COMPLEX: 0.8,
            TaskComplexity.CRITICAL: 0.9
        }
        benefit_score += complexity_benefit[complexity]

        # ファイル数による効果（多いほど効果的）
        if file_analysis["file_count"] > 5:
            benefit_score += 0.2
        if file_analysis["file_count"] > 10:
            benefit_score += 0.2

        # エラー数による効果（多いほど効果的）
        if file_analysis["error_count"] > 10:
            benefit_score += 0.2
        if file_analysis["error_count"] > 50:
            benefit_score += 0.2

        # 時間節約効果
        if time_estimate > 60:  # 1時間以上
            benefit_score += 0.1
        if time_estimate > 180:  # 3時間以上
            benefit_score += 0.2

        # コスト効率性
        if cost_estimate < 0.01:  # 1セント未満
            benefit_score += 0.1

        return min(benefit_score, 1.0)

    def _recommend_automation_level(self, complexity: TaskComplexity, cost: float,
                                   risk: str, benefit: float) -> AutomationLevel:
        """自動化レベル推奨"""

        # 高リスクは承認必須
        if risk == "high":
            return AutomationLevel.APPROVAL_REQUIRED

        # 高コストは承認必須
        if cost > self.thresholds["max_cost_auto_approval"]:
            return AutomationLevel.APPROVAL_REQUIRED

        # 低効果は手動推奨
        if benefit < 0.4:
            return AutomationLevel.MANUAL_ONLY

        # 複雑度による判定
        if complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE] and risk == "low":
            return AutomationLevel.FULL_AUTO
        elif complexity == TaskComplexity.MODERATE and risk == "low":
            return AutomationLevel.SEMI_AUTO
        else:
            return AutomationLevel.APPROVAL_REQUIRED

    def _calculate_confidence(self, file_analysis: Dict, context: Dict) -> float:
        """判定信頼度計算"""

        confidence = 0.7  # ベース信頼度

        # ファイル分析の信頼性
        if file_analysis["file_count"] > 0:
            confidence += 0.1

        # コンテキスト情報の豊富さ
        confidence += min(len(context) * 0.05, 0.2)

        return min(confidence, 1.0)

    def _create_decision(self, use_gemini: bool, automation_level: AutomationLevel,
                        task_analysis: TaskAnalysis, reasoning: str) -> DecisionResult:
        """判定結果作成"""

        # 代替アプローチ生成
        alternatives = []
        if use_gemini:
            alternatives.append("Claude単独での段階的実行")
            alternatives.append("部分的なGemini活用（重要部分のみ）")
        else:
            alternatives.append("Geminiでの並列処理による効率化")
            alternatives.append("タスク分割によるGemini部分活用")

        # コスト効果分析
        cost_benefit = {
            "estimated_cost": task_analysis.estimated_cost,
            "estimated_time_saving": task_analysis.estimated_time * 0.6 if use_gemini else 0,
            "quality_improvement": task_analysis.gemini_benefit_score,
            "risk_mitigation": "適切" if automation_level != AutomationLevel.FULL_AUTO else "限定的"
        }

        return DecisionResult(
            use_gemini=use_gemini,
            automation_level=automation_level,
            task_analysis=task_analysis,
            reasoning=reasoning,
            alternative_approaches=alternatives,
            cost_benefit_analysis=cost_benefit
        )

    def _count_file_errors(self, file_path: str, error_type: str) -> int:
        """ファイルのエラー数カウント"""
        try:
            result = subprocess.run(
                ["python3", "-m", "mypy", "--strict", file_path],
                capture_output=True,
                text=True
            )

            error_count = 0
            for line in result.stdout.split('\n'):
                if error_type in line and 'error:' in line:
                    error_count += 1

            return error_count
        except:
            return 0

    def _complexity_value(self, complexity: TaskComplexity) -> int:
        """複雑度の数値変換"""
        values = {
            TaskComplexity.TRIVIAL: 1,
            TaskComplexity.SIMPLE: 2,
            TaskComplexity.MODERATE: 3,
            TaskComplexity.COMPLEX: 4,
            TaskComplexity.CRITICAL: 5
        }
        return values[complexity]

    def _save_decision_history(self, decision: DecisionResult) -> None:
        """判定履歴保存"""

        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "decision": {
                "use_gemini": decision.use_gemini,
                "automation_level": decision.automation_level.value,
                "reasoning": decision.reasoning
            },
            "analysis": {
                "complexity": decision.task_analysis.complexity.value,
                "estimated_time": decision.task_analysis.estimated_time,
                "estimated_cost": decision.task_analysis.estimated_cost,
                "benefit_score": decision.task_analysis.gemini_benefit_score,
                "confidence": decision.task_analysis.confidence
            }
        }

        # 履歴読み込み
        history = []
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []

        # 新しいエントリ追加
        history.append(history_entry)

        # 履歴サイズ制限（最新100件）
        if len(history) > 100:
            history = history[-100:]

        # 保存
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """設定ファイル読み込み"""

        default_config = {
            "min_tokens_for_gemini": 1000,
            "max_cost_auto_approval": 0.01,
            "min_benefit_score": 0.6,
            "complexity_threshold": "moderate",
            "automation_preferences": {
                "default_level": "semi_auto",
                "risk_tolerance": "medium",
                "cost_sensitivity": "high"
            }
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 設定ファイル読み込みエラー: {e}")

        return default_config

    def get_decision_stats(self) -> Dict[str, Any]:
        """判定統計情報取得"""

        if not self.history_path.exists():
            return {"total_decisions": 0}

        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

            total = len(history)
            gemini_used = sum(1 for h in history if h["decision"]["use_gemini"])

            avg_cost = sum(h["analysis"]["estimated_cost"] for h in history) / total if total > 0 else 0
            avg_benefit = sum(h["analysis"]["benefit_score"] for h in history) / total if total > 0 else 0

            return {
                "total_decisions": total,
                "gemini_usage_rate": gemini_used / total if total > 0 else 0,
                "average_cost": avg_cost,
                "average_benefit_score": avg_benefit,
                "recent_decisions": history[-5:] if history else []
            }

        except Exception as e:
            print(f"⚠️ 統計取得エラー: {e}")
            return {"error": str(e)}

def main():
    """テスト実行"""
    engine = WorkflowDecisionEngine()

    # テストタスク
    test_files = ["kumihan_formatter/core/utilities/logger.py"]

    analysis = engine.analyze_task(
        "no-untyped-def エラー修正",
        test_files,
        "no-untyped-def"
    )

    decision = engine.make_decision(analysis)

    print(f"\n📊 判定結果:")
    print(f"Gemini使用: {decision.use_gemini}")
    print(f"自動化レベル: {decision.automation_level.value}")
    print(f"理由: {decision.reasoning}")
    print(f"コスト効果: ${decision.cost_benefit_analysis['estimated_cost']:.4f}")

if __name__ == "__main__":
    main()
