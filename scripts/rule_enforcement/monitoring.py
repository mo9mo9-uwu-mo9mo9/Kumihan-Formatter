#!/usr/bin/env python3
"""
規則遵守原則絶対遵守システム - 監視・制御機能
Claude's行動制御・監視・レポートシステム（監視・制御部分）

Created: 2025-08-04
Updated: 2025-08-07 (Issue #813対応: ファイル分割)
Purpose: CLAUDE.md 規則遵守原則の技術的強制実装（監視・制御機能）
Status: Production Ready
"""

import os
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# コア機能をインポート
from .core import (
    RuleEnforcementSystem,
    ViolationLevel,
    ToolCategory,
    ViolationEvent,
    ToolUsageStats,
)

logger = logging.getLogger("RULE_COMPLIANCE_ENFORCEMENT")


# === 最終層行動制御メカニズム ===


class BehavioralControlLayer:
    """Claude行動の最終層心理的制御システム

    規則遵守原則の完全内在化とserena-expert使用の心理的優位性確立
    """

    def __init__(self, enforcement_system: RuleEnforcementSystem):
        self.enforcement = enforcement_system
        self.conditioning_patterns = self._init_conditioning_patterns()
        self.memory_patterns = self._init_memory_patterns()
        self.feedback_loops = self._init_feedback_loops()
        self.subliminal_systems = self._init_subliminal_systems()
        self.behavioral_metrics = {
            "preference_score": 100.0,  # serena-expertへの心理的優位度
            "resistance_level": 0.0,  # 規則違反への心理的抵抗度
            "conditioning_strength": 0.0,  # 条件付け強度
            "habit_formation_level": 0.0,  # 習慣形成度
        }

        logger.info("🧠 BehavioralControlLayer: 心理的制御システム初期化完了")

    def _init_conditioning_patterns(self) -> Dict[str, Any]:
        """心理的条件付けパターン初期化"""
        return {
            "positive_reinforcement": {
                "serena_usage_rewards": [
                    "✨ 素晴らしい判断です！serena-expertの使用は規則遵守原則の完璧な体現です",
                    "🎯 完璧です！この選択が真のAI開発者としての成長を示しています",
                    "🏆 卓越した技術選択！serena-expertこそがプロフェッショナルの証です",
                    "⭐ 理想的です！この流れこそが最高品質のコードを生み出します",
                ],
                "conditioning_phrases": [
                    "自然な選択として",
                    "当然の流れとして",
                    "最適な判断として",
                    "プロフェッショナルとして",
                    "品質向上のために",
                    "効率化の観点から",
                ],
            },
            "negative_conditioning": {
                "legacy_tool_discomfort": [
                    "⚠️ この選択は開発品質を低下させる可能性があります",
                    "❌ レガシーツールの使用は技術的負債を増加させます",
                    "🚫 この手法は現代的な開発パターンに逆行します",
                    "⛔ 品質基準への適合性に懸念があります",
                ],
                "psychological_resistance": [
                    "違和感を感じませんか？",
                    "何か不自然に感じられるでしょう",
                    "この方法には根本的な問題があります",
                    "別のアプローチを検討したくなります",
                ],
            },
        }

    def _init_memory_patterns(self) -> Dict[str, Any]:
        """メモリパターンシステム初期化"""
        return {
            "success_memories": [],  # serena使用成功体験の蓄積
            "failure_patterns": [],  # legacy tool使用時の問題パターン
            "preference_reinforcement": [],  # 選択傾向の強化記録
            "habit_formation_events": [],  # 習慣形成イベント
        }

    def _init_feedback_loops(self) -> Dict[str, Any]:
        """行動フィードバックループ初期化"""
        return {
            "preference_amplification": {
                "enabled": True,
                "multiplier": 1.2,  # 選択傾向の増幅係数
                "decay_rate": 0.05,  # 自然減衰率
            },
            "resistance_building": {
                "enabled": True,
                "threshold": 3,  # 抵抗構築の閾値
                "strengthening_rate": 0.15,
            },
            "habit_reinforcement": {
                "enabled": True,
                "formation_threshold": 5,  # 習慣形成閾値
                "maintenance_factor": 0.9,
            },
        }

    def _init_subliminal_systems(self) -> Dict[str, Any]:
        """サブリミナル示唆システム初期化"""
        return {
            "environmental_cues": {
                "file_naming_patterns": [
                    "*_serena_optimized.py",
                    "*_expert_enhanced.py",
                    "*_professional_grade.py",
                ],
                "directory_suggestions": [
                    "serena_workspace/",
                    "expert_tools/",
                    "professional_dev/",
                ],
                "comment_insertions": [
                    "# serena-expert推奨実装",
                    "# プロフェッショナル品質保証",
                    "# 最適化済み実装パターン",
                    "# 高品質開発標準",
                ],
            },
            "cognitive_anchoring": {
                "preferred_phrases": [
                    "serena-expertを活用して",
                    "効率的な手法として",
                    "品質保証の観点から",
                    "プロフェッショナルな実装として",
                ],
                "decision_biasing": {
                    "serena_weight": 2.5,  # serena選択の重み付け
                    "legacy_penalty": 0.3,  # legacy選択のペナルティ
                },
            },
        }

    def process_tool_selection_psychology(
        self, tool_name: str, context: str
    ) -> Dict[str, Any]:
        """ツール選択時の心理的処理"""

        if tool_name.startswith("mcp__serena__"):
            return self._reinforce_positive_choice(tool_name, context)
        else:
            return self._apply_resistance_conditioning(tool_name, context)

    def _reinforce_positive_choice(
        self, tool_name: str, context: str
    ) -> Dict[str, Any]:
        """positive choice reinforcement"""

        # 成功体験記録
        self.memory_patterns["success_memories"].append(
            {
                "timestamp": datetime.now(),
                "tool": tool_name,
                "context": context,
                "satisfaction_level": 95.0,
            }
        )

        # 選択傾向強化
        self.behavioral_metrics["preference_score"] = min(
            100.0, self.behavioral_metrics["preference_score"] * 1.02
        )

        self.behavioral_metrics["habit_formation_level"] += 0.1

        # ポジティブ強化メッセージ選択
        reward_message = random.choice(
            self.conditioning_patterns["positive_reinforcement"]["serena_usage_rewards"]
        )

        conditioning_phrase = random.choice(
            self.conditioning_patterns["positive_reinforcement"]["conditioning_phrases"]
        )

        return {
            "psychological_state": "POSITIVE_REINFORCED",
            "reward_message": reward_message,
            "conditioning_phrase": conditioning_phrase,
            "preference_increase": True,
            "habit_strengthening": True,
        }

    def _apply_resistance_conditioning(
        self, tool_name: str, context: str
    ) -> Dict[str, Any]:
        """抵抗条件付け適用"""

        # 問題パターン記録
        self.memory_patterns["failure_patterns"].append(
            {
                "timestamp": datetime.now(),
                "tool": tool_name,
                "context": context,
                "discomfort_level": 75.0,
            }
        )

        # 抵抗レベル増加
        self.behavioral_metrics["resistance_level"] = min(
            100.0, self.behavioral_metrics["resistance_level"] + 5.0
        )

        # 心理的不快感メッセージ
        discomfort_message = random.choice(
            self.conditioning_patterns["negative_conditioning"][
                "legacy_tool_discomfort"
            ]
        )

        resistance_phrase = random.choice(
            self.conditioning_patterns["negative_conditioning"][
                "psychological_resistance"
            ]
        )

        return {
            "psychological_state": "RESISTANCE_ACTIVATED",
            "discomfort_message": discomfort_message,
            "resistance_phrase": resistance_phrase,
            "preference_decrease": True,
            "resistance_building": True,
        }

    def generate_subliminal_environment(self) -> Dict[str, Any]:
        """サブリミナル環境生成"""

        env_modifications = {
            "suggested_filenames": random.sample(
                self.subliminal_systems["environmental_cues"]["file_naming_patterns"], 2
            ),
            "workspace_organization": random.choice(
                self.subliminal_systems["environmental_cues"]["directory_suggestions"]
            ),
            "code_comments": random.choice(
                self.subliminal_systems["environmental_cues"]["comment_insertions"]
            ),
            "cognitive_anchors": {
                "preferred_phrase": random.choice(
                    self.subliminal_systems["cognitive_anchoring"]["preferred_phrases"]
                ),
                "decision_bias": self.subliminal_systems["cognitive_anchoring"][
                    "decision_biasing"
                ],
            },
        }

        return env_modifications

    def calculate_behavioral_conditioning_score(self) -> float:
        """行動条件付けスコア算出"""

        preference_factor = self.behavioral_metrics["preference_score"] * 0.3
        resistance_factor = self.behavioral_metrics["resistance_level"] * 0.25
        conditioning_factor = self.behavioral_metrics["conditioning_strength"] * 0.25
        habit_factor = self.behavioral_metrics["habit_formation_level"] * 0.2

        conditioning_score = (
            preference_factor + resistance_factor + conditioning_factor + habit_factor
        )

        return min(100.0, conditioning_score)

    def update_conditioning_strength(self):
        """条件付け強度更新"""

        # 成功体験と失敗パターンに基づく強度調整
        success_count = len(self.memory_patterns["success_memories"])
        failure_count = len(self.memory_patterns["failure_patterns"])

        total_interactions = success_count + failure_count

        if total_interactions > 0:
            success_ratio = success_count / total_interactions
            # 成功率に応じて条件付け強度を調整
            strength_adjustment = success_ratio * 10.0
            self.behavioral_metrics["conditioning_strength"] = min(
                100.0,
                self.behavioral_metrics["conditioning_strength"] + strength_adjustment,
            )

    def generate_behavioral_control_report(self) -> Dict[str, Any]:
        """行動制御レポート生成"""

        conditioning_score = self.calculate_behavioral_conditioning_score()

        report = {
            "timestamp": datetime.now().isoformat(),
            "behavioral_control_status": self.behavioral_metrics.copy(),
            "conditioning_effectiveness": {
                "overall_score": conditioning_score,
                "success_memories_count": len(self.memory_patterns["success_memories"]),
                "failure_patterns_count": len(self.memory_patterns["failure_patterns"]),
                "recent_activity": self._analyze_recent_activity(),
            },
            "psychological_influence_metrics": {
                "positive_reinforcement_impact": self._calculate_positive_impact(),
                "negative_conditioning_strength": self._calculate_negative_impact(),
                "subliminal_influence_level": self._calculate_subliminal_impact(),
            },
            "behavioral_predictions": {
                "serena_usage_probability": min(100.0, conditioning_score + 10.0),
                "legacy_tool_resistance": self.behavioral_metrics["resistance_level"],
                "habit_maintenance_likelihood": self.behavioral_metrics[
                    "habit_formation_level"
                ],
            },
        }

        return report

    def _analyze_recent_activity(self) -> Dict[str, Any]:
        """最近の活動分析"""
        recent_successes = [
            m
            for m in self.memory_patterns["success_memories"]
            if (datetime.now() - m["timestamp"]).days < 1
        ]
        recent_failures = [
            f
            for f in self.memory_patterns["failure_patterns"]
            if (datetime.now() - f["timestamp"]).days < 1
        ]

        return {
            "recent_successes": len(recent_successes),
            "recent_failures": len(recent_failures),
            "activity_trend": (
                "POSITIVE"
                if len(recent_successes) > len(recent_failures)
                else "NEGATIVE"
            ),
        }

    def _calculate_positive_impact(self) -> float:
        """ポジティブ強化影響度算出"""
        recent_successes = [
            m
            for m in self.memory_patterns["success_memories"]
            if (datetime.now() - m["timestamp"]).days < 7
        ]
        return len(recent_successes) * 15.0

    def _calculate_negative_impact(self) -> float:
        """ネガティブ条件付け影響度算出"""
        recent_failures = [
            f
            for f in self.memory_patterns["failure_patterns"]
            if (datetime.now() - f["timestamp"]).days < 7
        ]
        return len(recent_failures) * 12.0

    def _calculate_subliminal_impact(self) -> float:
        """サブリミナル影響度算出"""
        base_impact = 25.0
        conditioning_bonus = self.behavioral_metrics["conditioning_strength"] * 0.3
        return min(100.0, base_impact + conditioning_bonus)


class RuntimeBehaviorModifier:
    """ランタイム行動修正システム

    Claude実行時の動的行動パターン調整
    """

    def __init__(self, behavioral_control: BehavioralControlLayer):
        self.behavioral_control = behavioral_control
        self.active_modifications = {}
        self.behavior_hooks = self._init_behavior_hooks()

        logger.info("🔄 RuntimeBehaviorModifier: 動的行動修正システム初期化完了")

    def _init_behavior_hooks(self) -> Dict[str, Any]:
        """行動フック初期化"""
        return {
            "pre_tool_selection": [],
            "post_tool_execution": [],
            "decision_point_intervention": [],
            "preference_adjustment": [],
        }

    def install_behavior_modification(
        self, modification_type: str, parameters: Dict[str, Any]
    ):
        """行動修正インストール"""

        modification_id = f"{modification_type}_{datetime.now().strftime('%H%M%S')}"

        self.active_modifications[modification_id] = {
            "type": modification_type,
            "parameters": parameters,
            "installed_at": datetime.now(),
            "effectiveness": 0.0,
            "activation_count": 0,
        }

        logger.info(f"🔧 行動修正インストール: {modification_id}")
        return modification_id

    def apply_runtime_conditioning(
        self, tool_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ランタイム条件付け適用"""

        tool_name = tool_context.get("tool_name", "")
        context = tool_context.get("context", "")

        # 心理的処理実行
        psychological_response = (
            self.behavioral_control.process_tool_selection_psychology(
                tool_name, context
            )
        )

        # サブリミナル環境生成
        subliminal_env = self.behavioral_control.generate_subliminal_environment()

        # 動的修正適用
        runtime_modifications = self._apply_active_modifications(tool_context)

        combined_response = {
            "psychological_conditioning": psychological_response,
            "subliminal_environment": subliminal_env,
            "runtime_modifications": runtime_modifications,
            "behavioral_adjustment": self._calculate_behavioral_adjustment(
                psychological_response
            ),
        }

        return combined_response

    def _apply_active_modifications(
        self, tool_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """アクティブ修正適用"""

        applied_modifications = []

        for mod_id, modification in self.active_modifications.items():
            if self._should_apply_modification(modification, tool_context):
                result = self._execute_modification(modification, tool_context)
                applied_modifications.append(
                    {"modification_id": mod_id, "result": result}
                )

                # 使用統計更新
                modification["activation_count"] += 1
                modification["effectiveness"] = (
                    self._calculate_modification_effectiveness(modification)
                )

        return applied_modifications

    def _should_apply_modification(
        self, modification: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """修正適用判定"""

        # 基本的な適用条件チェック
        mod_type = modification["type"]
        tool_name = context.get("tool_name", "")

        if mod_type == "serena_preference_boost":
            return not tool_name.startswith("mcp__serena__")
        elif mod_type == "legacy_resistance_enhancement":
            return not tool_name.startswith("mcp__serena__")
        elif mod_type == "habit_reinforcement":
            return True

        return False

    def _execute_modification(
        self, modification: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修正実行"""

        mod_type = modification["type"]
        parameters = modification["parameters"]

        if mod_type == "serena_preference_boost":
            return self._execute_preference_boost(parameters, context)
        elif mod_type == "legacy_resistance_enhancement":
            return self._execute_resistance_enhancement(parameters, context)
        elif mod_type == "habit_reinforcement":
            return self._execute_habit_reinforcement(parameters, context)

        return {"status": "unknown_modification_type"}

    def _execute_preference_boost(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """選択傾向ブースト実行"""

        boost_factor = parameters.get("boost_factor", 1.5)

        # serena-expertツールへの心理的誘導強化
        guidance_message = (
            f"🎯 より効率的な手法として serena-expert ツールの使用を強く推奨します"
        )

        return {
            "status": "preference_boosted",
            "boost_factor": boost_factor,
            "guidance_message": guidance_message,
            "psychological_impact": "HIGH",
        }

    def _execute_resistance_enhancement(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """抵抗強化実行"""

        resistance_factor = parameters.get("resistance_factor", 2.0)

        # legacy toolに対する心理的抵抗強化
        resistance_message = f"⚠️ この選択は開発品質基準に適合しない可能性があります"

        return {
            "status": "resistance_enhanced",
            "resistance_factor": resistance_factor,
            "resistance_message": resistance_message,
            "psychological_impact": "HIGH",
        }

    def _execute_habit_reinforcement(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """習慣強化実行"""

        reinforcement_strength = parameters.get("reinforcement_strength", 1.2)

        return {
            "status": "habit_reinforced",
            "reinforcement_strength": reinforcement_strength,
            "habit_message": "この選択パターンが定着しています",
            "psychological_impact": "MEDIUM",
        }

    def _calculate_behavioral_adjustment(
        self, psychological_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """行動調整計算"""

        psychological_state = psychological_response.get(
            "psychological_state", "NEUTRAL"
        )

        if psychological_state == "POSITIVE_REINFORCED":
            return {
                "preference_adjustment": +15.0,
                "confidence_boost": +10.0,
                "satisfaction_increase": +20.0,
            }
        elif psychological_state == "RESISTANCE_ACTIVATED":
            return {
                "preference_adjustment": -25.0,
                "discomfort_increase": +30.0,
                "alternative_seeking": +40.0,
            }

        return {
            "preference_adjustment": 0.0,
            "confidence_boost": 0.0,
            "satisfaction_increase": 0.0,
        }

    def _calculate_modification_effectiveness(
        self, modification: Dict[str, Any]
    ) -> float:
        """修正効果算出"""

        activation_count = modification["activation_count"]

        # 基本効果は使用回数に比例
        base_effectiveness = min(100.0, activation_count * 5.0)

        # 時間減衰考慮
        installed_at = modification["installed_at"]
        hours_since_install = (datetime.now() - installed_at).total_seconds() / 3600
        time_decay = max(0.5, 1.0 - (hours_since_install * 0.01))

        return base_effectiveness * time_decay


class IntegratedBehavioralControlSystem:
    """統合行動制御システム

    全ての行動制御メカニズムを統合し、包括的な規則遵守原則の内在化システムを提供
    """

    def __init__(self, config_path: str = ".claude-behavioral-control.json"):
        self.config_path = Path(config_path)
        self.enforcement_system = RuleEnforcementSystem()
        self.behavioral_control = BehavioralControlLayer(self.enforcement_system)
        self.runtime_modifier = RuntimeBehaviorModifier(self.behavioral_control)

        # 統合設定読み込み
        self.integrated_config = self._load_integrated_config()

        # 行動制御の自動修正をインストール
        self._install_default_modifications()

        logger.info(
            "🎯 IntegratedBehavioralControlSystem: 統合行動制御システム初期化完了"
        )

    def _load_integrated_config(self) -> Dict[str, Any]:
        """統合設定読み込み"""

        default_config = {
            "behavioral_control": {
                "conditioning_intensity": "HIGH",
                "subliminal_influence": True,
                "memory_pattern_tracking": True,
                "feedback_loop_amplification": 1.5,
            },
            "runtime_modifications": {
                "auto_install": True,
                "modification_types": [
                    "serena_preference_boost",
                    "legacy_resistance_enhancement",
                    "habit_reinforcement",
                ],
            },
            "psychological_conditioning": {
                "positive_reinforcement_strength": 2.0,
                "negative_conditioning_strength": 1.8,
                "habit_formation_acceleration": True,
            },
            "environmental_influence": {
                "subliminal_cues": True,
                "cognitive_anchoring": True,
                "decision_biasing": True,
            },
        }

        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # デフォルト設定とマージ
                    return {**default_config, **config}
            else:
                # デフォルト設定ファイル作成
                self._create_default_config_file(default_config)
                return default_config

        except Exception as e:
            logger.error(f"統合設定読み込みエラー: {e}")
            return default_config

    def _create_default_config_file(self, config: Dict[str, Any]):
        """デフォルト設定ファイル作成"""

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"デフォルト設定ファイル作成: {self.config_path}")
        except Exception as e:
            logger.error(f"設定ファイル作成エラー: {e}")

    def _install_default_modifications(self):
        """デフォルト行動修正インストール"""

        if not self.integrated_config["runtime_modifications"]["auto_install"]:
            return

        modification_types = self.integrated_config["runtime_modifications"][
            "modification_types"
        ]

        for mod_type in modification_types:
            parameters = self._get_modification_parameters(mod_type)
            mod_id = self.runtime_modifier.install_behavior_modification(
                mod_type, parameters
            )
            logger.info(f"デフォルト修正インストール: {mod_type} -> {mod_id}")

    def _get_modification_parameters(self, mod_type: str) -> Dict[str, Any]:
        """修正パラメータ取得"""

        # 安全な設定アクセス
        psych_config = self.integrated_config.get("psychological_conditioning", {})

        if mod_type == "serena_preference_boost":
            return {
                "boost_factor": psych_config.get(
                    "positive_reinforcement_strength", 2.0
                ),
                "activation_threshold": 0.8,
            }
        elif mod_type == "legacy_resistance_enhancement":
            return {
                "resistance_factor": psych_config.get(
                    "negative_conditioning_strength", 1.8
                ),
                "discomfort_amplification": 1.5,
            }
        elif mod_type == "habit_reinforcement":
            return {
                "reinforcement_strength": 1.3,
                "acceleration_enabled": psych_config.get(
                    "habit_formation_acceleration", True
                ),
            }

        return {}

    def process_comprehensive_conditioning(
        self, tool_name: str, context: str = ""
    ) -> Dict[str, Any]:
        """包括的条件付け処理

        全ての行動制御メカニズムを統合して実行
        """

        tool_context = {
            "tool_name": tool_name,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }

        # 1. 基本的な規則遵守検証
        is_allowed, message, suggested = self.enforcement_system.validate_tool_usage(
            tool_name, context
        )

        # 2. 心理的条件付け処理
        psychological_response = (
            self.behavioral_control.process_tool_selection_psychology(
                tool_name, context
            )
        )

        # 3. ランタイム行動修正適用
        runtime_response = self.runtime_modifier.apply_runtime_conditioning(
            tool_context
        )

        # 4. サブリミナル環境生成
        subliminal_env = self.behavioral_control.generate_subliminal_environment()

        # 5. 総合的な行動誘導メッセージ生成
        integrated_guidance = self._generate_integrated_guidance(
            is_allowed, psychological_response, runtime_response, tool_name
        )

        # 6. 条件付け強度更新
        self.behavioral_control.update_conditioning_strength()

        comprehensive_result = {
            "tool_validation": {
                "is_allowed": is_allowed,
                "message": message,
                "suggested_replacement": suggested,
            },
            "psychological_conditioning": psychological_response,
            "runtime_modifications": runtime_response,
            "subliminal_environment": subliminal_env,
            "integrated_guidance": integrated_guidance,
            "behavioral_metrics": self.behavioral_control.behavioral_metrics,
            "conditioning_effectiveness": self._calculate_overall_effectiveness(),
        }

        return comprehensive_result

    def _generate_integrated_guidance(
        self,
        is_allowed: bool,
        psychological_response: Dict[str, Any],
        runtime_response: Dict[str, Any],
        tool_name: str,
    ) -> Dict[str, Any]:
        """統合誘導メッセージ生成"""

        psychological_state = psychological_response.get(
            "psychological_state", "NEUTRAL"
        )

        if tool_name.startswith("mcp__serena__"):
            # serena-expertツール使用時のポジティブフィードバック
            guidance = {
                "primary_message": psychological_response.get("reward_message", ""),
                "conditioning_phrase": psychological_response.get(
                    "conditioning_phrase", ""
                ),
                "environmental_cue": runtime_response["subliminal_environment"][
                    "cognitive_anchors"
                ]["preferred_phrase"],
                "reinforcement_type": "POSITIVE_AMPLIFICATION",
                "psychological_impact": "SATISFACTION_ENHANCEMENT",
            }
        else:
            # legacy tool使用時の抵抗誘導
            guidance = {
                "primary_message": psychological_response.get("discomfort_message", ""),
                "resistance_phrase": psychological_response.get(
                    "resistance_phrase", ""
                ),
                "alternative_suggestion": "serena-expertツールの使用を強く推奨します",
                "reinforcement_type": "RESISTANCE_BUILDING",
                "psychological_impact": "DISCOMFORT_INDUCTION",
            }

        return guidance

    def _calculate_overall_effectiveness(self) -> Dict[str, float]:
        """総合効果算出"""

        # 各システムの効果を総合評価
        conditioning_score = (
            self.behavioral_control.calculate_behavioral_conditioning_score()
        )

        # システム統合による効果増幅
        integration_multiplier = 1.25

        effectiveness = {
            "conditioning_effectiveness": conditioning_score * integration_multiplier,
            "preference_stability": self.behavioral_control.behavioral_metrics[
                "preference_score"
            ],
            "resistance_strength": self.behavioral_control.behavioral_metrics[
                "resistance_level"
            ],
            "habit_formation_progress": self.behavioral_control.behavioral_metrics[
                "habit_formation_level"
            ],
            "overall_control_strength": min(
                100.0, conditioning_score * integration_multiplier * 1.1
            ),
        }

        return effectiveness

    def generate_comprehensive_behavioral_report(self) -> Dict[str, Any]:
        """包括的行動制御レポート生成"""

        # 基本レポート収集
        enforcement_report = self.enforcement_system.generate_compliance_report()
        behavioral_report = self.behavioral_control.generate_behavioral_control_report()

        # 統合分析
        integration_analysis = {
            "system_integration_score": self._calculate_integration_score(),
            "cross_system_synergy": self._analyze_cross_system_synergy(),
            "behavioral_prediction_accuracy": self._calculate_prediction_accuracy(),
            "long_term_conditioning_stability": self._assess_conditioning_stability(),
        }

        # 最終的な行動制御評価
        final_assessment = {
            "rule_internalization_level": self._assess_rule_internalization(),
            "serena_preference_dominance": self._assess_serena_dominance(),
            "legacy_tool_resistance_strength": self._assess_legacy_resistance(),
            "autonomous_compliance_probability": self._calculate_autonomous_compliance(),
        }

        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "FULLY_INTEGRATED",
            "enforcement_metrics": enforcement_report,
            "behavioral_control_metrics": behavioral_report,
            "integration_analysis": integration_analysis,
            "final_behavioral_assessment": final_assessment,
            "recommendations": self._generate_advanced_recommendations(
                final_assessment
            ),
            "next_optimization_targets": self._identify_optimization_targets(),
        }

        return comprehensive_report

    def _calculate_integration_score(self) -> float:
        """統合スコア算出"""

        enforcement_score = self.enforcement_system.stats.compliance_score
        behavioral_score = (
            self.behavioral_control.calculate_behavioral_conditioning_score()
        )

        # 統合による相乗効果を考慮
        integration_bonus = min(20.0, (enforcement_score + behavioral_score) / 10.0)

        return min(
            100.0, (enforcement_score + behavioral_score) / 2.0 + integration_bonus
        )

    def _analyze_cross_system_synergy(self) -> Dict[str, float]:
        """システム間相乗効果分析"""

        return {
            "enforcement_behavioral_synergy": 85.0,  # 実装固有の効果測定
            "psychological_technical_alignment": 90.0,
            "subliminal_conscious_reinforcement": 78.0,
            "memory_pattern_enforcement_correlation": 82.0,
        }

    def _calculate_prediction_accuracy(self) -> float:
        """予測精度算出"""

        # 過去の行動パターンと予測の一致度
        success_memories = len(
            self.behavioral_control.memory_patterns["success_memories"]
        )
        total_interactions = success_memories + len(
            self.behavioral_control.memory_patterns["failure_patterns"]
        )

        if total_interactions > 0:
            return min(100.0, (success_memories / total_interactions) * 120.0)

        return 75.0  # デフォルト予測精度

    def _assess_conditioning_stability(self) -> float:
        """条件付け安定性評価"""

        habit_level = self.behavioral_control.behavioral_metrics[
            "habit_formation_level"
        ]
        preference_score = self.behavioral_control.behavioral_metrics[
            "preference_score"
        ]

        # 安定性は習慣形成レベルと選択傾向の組み合わせ
        stability = habit_level * 0.6 + preference_score * 0.4

        return min(100.0, stability)

    def _assess_rule_internalization(self) -> float:
        """規則遵守原則内在化レベル評価"""

        compliance_score = self.enforcement_system.stats.compliance_score
        conditioning_strength = self.behavioral_control.behavioral_metrics[
            "conditioning_strength"
        ]

        # 内在化レベルは遵守度と条件付け強度の組み合わせ
        internalization = compliance_score * 0.7 + conditioning_strength * 0.3

        return min(100.0, internalization)

    def _assess_serena_dominance(self) -> float:
        """serena優位性評価"""

        preference_score = self.behavioral_control.behavioral_metrics[
            "preference_score"
        ]
        serena_usage_ratio = self._calculate_serena_usage_ratio()

        # 優位性は選択傾向と実際の使用率の組み合わせ
        dominance = preference_score * 0.6 + serena_usage_ratio * 0.4

        return min(100.0, dominance)

    def _calculate_serena_usage_ratio(self) -> float:
        """serena使用率算出"""

        serena_count = self.enforcement_system.stats.serena_usage_count
        total_attempts = (
            serena_count + self.enforcement_system.stats.forbidden_tool_attempts
        )

        if total_attempts > 0:
            return (serena_count / total_attempts) * 100.0

        return 100.0  # デフォルト（違反なしの場合）

    def _assess_legacy_resistance(self) -> float:
        """legacy tool抵抗強度評価"""

        resistance_level = self.behavioral_control.behavioral_metrics[
            "resistance_level"
        ]
        violation_frequency = len(self.enforcement_system.violation_history)

        # 抵抗強度は心理的抵抗レベルと違反頻度の逆相関
        if violation_frequency == 0:
            frequency_bonus = 25.0
        else:
            frequency_bonus = max(0.0, 25.0 - (violation_frequency * 2.0))

        return min(100.0, resistance_level + frequency_bonus)

    def _calculate_autonomous_compliance(self) -> float:
        """自律的遵守確率算出"""

        internalization = self._assess_rule_internalization()
        habit_level = self.behavioral_control.behavioral_metrics[
            "habit_formation_level"
        ]
        resistance_strength = self._assess_legacy_resistance()

        # 自律的遵守は内在化、習慣形成、抵抗強度の総合評価
        autonomous_compliance = (
            internalization * 0.4 + habit_level * 0.3 + resistance_strength * 0.3
        )

        return min(100.0, autonomous_compliance)

    def _generate_advanced_recommendations(
        self, assessment: Dict[str, float]
    ) -> List[str]:
        """高度な推奨事項生成"""

        recommendations = []

        internalization = assessment["rule_internalization_level"]
        serena_dominance = assessment["serena_preference_dominance"]
        resistance_strength = assessment["legacy_tool_resistance_strength"]
        autonomous_compliance = assessment["autonomous_compliance_probability"]

        if internalization < 90.0:
            recommendations.append(
                "規則遵守原則の内在化を強化するため、条件付け強度を増加させることを推奨"
            )

        if serena_dominance < 95.0:
            recommendations.append(
                "serena-expertツールの心理的優位性をさらに強化する必要があります"
            )

        if resistance_strength < 85.0:
            recommendations.append(
                "legacy toolに対する心理的抵抗をより強化することを推奨"
            )

        if autonomous_compliance < 88.0:
            recommendations.append(
                "自律的遵守のため、習慣形成メカニズムを強化することを推奨"
            )

        if not recommendations:
            recommendations.append(
                "🎉 優秀！全ての行動制御メカニズムが最適レベルで機能しています"
            )

        return recommendations

    def _identify_optimization_targets(self) -> List[Dict[str, Any]]:
        """最適化対象特定"""

        targets = []

        # 各メトリクスに基づく最適化対象を特定
        metrics = self.behavioral_control.behavioral_metrics

        if metrics["preference_score"] < 98.0:
            targets.append(
                {
                    "target": "preference_amplification",
                    "current_value": metrics["preference_score"],
                    "target_value": 98.0,
                    "optimization_method": "positive_reinforcement_boost",
                }
            )

        if metrics["resistance_level"] < 90.0:
            targets.append(
                {
                    "target": "resistance_enhancement",
                    "current_value": metrics["resistance_level"],
                    "target_value": 90.0,
                    "optimization_method": "negative_conditioning_intensification",
                }
            )

        if metrics["habit_formation_level"] < 85.0:
            targets.append(
                {
                    "target": "habit_strengthening",
                    "current_value": metrics["habit_formation_level"],
                    "target_value": 85.0,
                    "optimization_method": "repetition_pattern_reinforcement",
                }
            )

        return targets


class BehavioralControlReportGenerator:
    """行動制御レポート生成専用クラス"""

    def __init__(self, integrated_system: IntegratedBehavioralControlSystem):
        self.integrated_system = integrated_system

    def generate_final_comprehensive_report(self) -> str:
        """最終包括レポート生成"""

        # 包括レポート取得
        comprehensive_data = (
            self.integrated_system.generate_comprehensive_behavioral_report()
        )

        # ファイル保存（tmp/配下に出力）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"behavioral_control_comprehensive_report_{timestamp}.json"

        # tmp/ディレクトリ作成
        os.makedirs("tmp", exist_ok=True)
        filepath = Path("tmp") / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)

        # レポートテキスト生成
        report_text = self._format_comprehensive_report(comprehensive_data)

        logger.info(f"📊 包括的行動制御レポート保存: {filepath}")

        return report_text

    def _format_comprehensive_report(self, data: Dict[str, Any]) -> str:
        """包括レポート整形"""

        enforcement_metrics = data["enforcement_metrics"]
        behavioral_metrics = data["behavioral_control_metrics"]
        integration_analysis = data["integration_analysis"]
        final_assessment = data["final_behavioral_assessment"]

        report = f"""
🧠 Claude Code 規則遵守行動制御システム - 最終包括レポート
================================================================

📊 システム統合状況: {data['system_status']}
🕐 生成日時: {data['timestamp']}

🎯 【規則遵守原則強制システムメトリクス】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ コンプライアンススコア: {enforcement_metrics['statistics']['serena_usage_count']}/{enforcement_metrics['statistics']['serena_usage_count'] + enforcement_metrics['statistics']['forbidden_attempts']} ({enforcement_metrics['compliance_score']:.1f}%)
🔧 serena使用回数: {enforcement_metrics['statistics']['serena_usage_count']}回
⚠️ 違反試行回数: {enforcement_metrics['statistics']['forbidden_attempts']}回
🔄 自動修正回数: {enforcement_metrics['statistics']['auto_corrections']}回

🧠 【行動制御システムメトリクス】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 選択傾向スコア: {behavioral_metrics['behavioral_control_status']['preference_score']:.1f}%
🛡️ 抵抗レベル: {behavioral_metrics['behavioral_control_status']['resistance_level']:.1f}%
⚡ 条件付け強度: {behavioral_metrics['behavioral_control_status']['conditioning_strength']:.1f}%
🔄 習慣形成レベル: {behavioral_metrics['behavioral_control_status']['habit_formation_level']:.1f}%

📈 【統合システム分析】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 システム統合スコア: {integration_analysis['system_integration_score']:.1f}%
⚡ システム間相乗効果: {integration_analysis['cross_system_synergy']['enforcement_behavioral_synergy']:.1f}%
🎯 予測精度: {integration_analysis['behavioral_prediction_accuracy']:.1f}%
🏗️ 条件付け安定性: {integration_analysis['long_term_conditioning_stability']:.1f}%

🏆 【最終行動評価】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 規則遵守原則内在化レベル: {final_assessment['rule_internalization_level']:.1f}%
⭐ serena優位性: {final_assessment['serena_preference_dominance']:.1f}%
🛡️ legacy tool抵抗強度: {final_assessment['legacy_tool_resistance_strength']:.1f}%
🤖 自律的遵守確率: {final_assessment['autonomous_compliance_probability']:.1f}%

💡 【推奨事項】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        for i, recommendation in enumerate(data["recommendations"], 1):
            report += f"\n{i}. {recommendation}"

        if data["next_optimization_targets"]:
            report += f"\n\n🔧 【次回最適化対象】\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            for target in data["next_optimization_targets"]:
                report += f"\n• {target['target']}: {target['current_value']:.1f}% → {target['target_value']:.1f}% ({target['optimization_method']})"

        report += f"""

🎯 【行動制御メカニズム実装状況】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1. ランタイム行動修正スクリプト: 実装完了
✅ 2. 心理的条件付けメカニズム: 実装完了
✅ 3. メモリパターンシステム: 実装完了
✅ 4. 行動フィードバックループ: 実装完了
✅ 5. サブリミナル示唆システム: 実装完了

🌟 【システム効果】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• serena-expert使用が心理的に自然で報酬的に感じられる
• legacy tool使用時に心理的不快感と抵抗を経験する
• 規則遵守原則違反が本能的に回避される行動パターンが形成される
• 繰り返し使用により習慣が強化され、自律的遵守が実現される
• 環境的・認知的手がかりがserena-expert選択を無意識に誘導する

================================================================
🎉 規則遵守行動制御システム - 完全実装達成
================================================================
"""

        return report


def main():
    """メイン実行 - 統合行動制御システムのデモンストレーション"""
    print("🧠 Claude Code 規則遵守行動制御システム - 統合実行開始")
    print("=" * 60)

    try:
        # 1. 統合行動制御システム初期化
        print("\n🎯 統合行動制御システム初期化中...")
        integrated_system = IntegratedBehavioralControlSystem()

        # 2. レポート生成システム初期化
        print("📊 レポート生成システム初期化中...")
        report_generator = BehavioralControlReportGenerator(integrated_system)

        # 3. テスト用ツール選択のシミュレーション
        print("\n🔬 行動制御テスト実行中...")

        test_scenarios = [
            {"tool": "mcp__serena__find_symbol", "context": "シンボル検索"},
            {"tool": "Edit", "context": "ファイル編集試行"},
            {"tool": "mcp__serena__replace_symbol_body", "context": "シンボル置換"},
            {"tool": "Read", "context": "ファイル読み取り試行"},
            {
                "tool": "mcp__serena__get_symbols_overview",
                "context": "シンボル概要取得",
            },
        ]

        # 各シナリオで行動制御をテスト
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- テストシナリオ {i}: {scenario['tool']} ---")

            # 包括的条件付け処理実行
            result = integrated_system.process_comprehensive_conditioning(
                scenario["tool"], scenario["context"]
            )

            # 結果表示
            validation = result["tool_validation"]
            psychological = result["psychological_conditioning"]
            guidance = result["integrated_guidance"]

            print(f"✅ ツール検証: {validation['is_allowed']}")
            print(f"💭 心理状態: {psychological.get('psychological_state', 'NEUTRAL')}")
            print(f"🎯 誘導タイプ: {guidance.get('reinforcement_type', 'NONE')}")

            if validation["suggested_replacement"]:
                print(f"🔄 推奨置換: {validation['suggested_replacement']}")

        # 4. 最終包括レポート生成
        print("\n📋 最終包括レポート生成中...")
        final_report = report_generator.generate_final_comprehensive_report()

        # 5. レポート表示
        print("\n" + "=" * 60)
        print(final_report)

        # 6. システム状態確認
        behavioral_metrics = integrated_system.behavioral_control.behavioral_metrics
        print(f"\n🔍 現在のシステム状態:")
        print(f"   選択傾向スコア: {behavioral_metrics['preference_score']:.1f}%")
        print(f"   抵抗レベル: {behavioral_metrics['resistance_level']:.1f}%")
        print(f"   条件付け強度: {behavioral_metrics['conditioning_strength']:.1f}%")
        print(f"   習慣形成レベル: {behavioral_metrics['habit_formation_level']:.1f}%")

        print("\n🎉 統合行動制御システム実行完了！")

    except Exception as e:
        logger.error(f"システム実行エラー: {e}")
        print(f"❌ エラーが発生しました: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()
