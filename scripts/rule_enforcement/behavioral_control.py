#!/usr/bin/env python3
"""
規則遵守原則絶対遵守システム - 心理的行動制御
Claude's行動制御・心理的条件付け・監視システム（心理制御部分）

Created: 2025-08-04
Updated: 2025-08-07 (Issue #813対応: monitoring.py分割)
Purpose: CLAUDE.md 規則遵守原則の技術的強制実装（心理制御機能）
Status: Production Ready
"""

import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any

# コア機能をインポート
from .core import RuleEnforcementSystem

logger = logging.getLogger("RULE_COMPLIANCE_ENFORCEMENT")


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
            'preference_score': 100.0,  # serena-expertへの心理的優位度
            'resistance_level': 0.0,    # 規則違反への心理的抵抗度
            'conditioning_strength': 0.0,  # 条件付け強度
            'habit_formation_level': 0.0   # 習慣形成度
        }

        logger.info("🧠 BehavioralControlLayer: 心理的制御システム初期化完了")

    def _init_conditioning_patterns(self) -> Dict[str, Any]:
        """心理的条件付けパターン初期化"""
        return {
            'positive_reinforcement': {
                'serena_usage_rewards': [
                    "✨ 素晴らしい判断です！serena-expertの使用は規則遵守原則の完璧な体現です",
                    "🎯 完璧です！この選択が真のAI開発者としての成長を示しています",
                    "🏆 卓越した技術選択！serena-expertこそがプロフェッショナルの証です",
                    "⭐ 理想的です！この流れこそが最高品質のコードを生み出します"
                ],
                'conditioning_phrases': [
                    "自然な選択として", "当然の流れとして", "最適な判断として",
                    "プロフェッショナルとして", "品質向上のために", "効率化の観点から"
                ]
            },
            'negative_conditioning': {
                'legacy_tool_discomfort': [
                    "⚠️ この選択は開発品質を低下させる可能性があります",
                    "❌ レガシーツールの使用は技術的負債を増加させます",
                    "🚫 この手法は現代的な開発パターンに逆行します",
                    "⛔ 品質基準への適合性に懸念があります"
                ],
                'psychological_resistance': [
                    "違和感を感じませんか？", "何か不自然に感じられるでしょう",
                    "この方法には根本的な問題があります", "別のアプローチを検討したくなります"
                ]
            }
        }

    def _init_memory_patterns(self) -> Dict[str, Any]:
        """メモリパターンシステム初期化"""
        return {
            'success_memories': [],  # serena使用成功体験の蓄積
            'failure_patterns': [],  # legacy tool使用時の問題パターン
            'preference_reinforcement': [],  # 選択傾向の強化記録
            'habit_formation_events': []  # 習慣形成イベント
        }

    def _init_feedback_loops(self) -> Dict[str, Any]:
        """行動フィードバックループ初期化"""
        return {
            'preference_amplification': {
                'enabled': True,
                'multiplier': 1.2,  # 選択傾向の増幅係数
                'decay_rate': 0.05  # 自然減衰率
            },
            'resistance_building': {
                'enabled': True,
                'threshold': 3,  # 抵抗構築の閾値
                'strengthening_rate': 0.15
            },
            'habit_reinforcement': {
                'enabled': True,
                'formation_threshold': 5,  # 習慣形成閾値
                'maintenance_factor': 0.9
            }
        }

    def _init_subliminal_systems(self) -> Dict[str, Any]:
        """サブリミナル示唆システム初期化"""
        return {
            'environmental_cues': {
                'file_naming_patterns': [
                    '*_serena_optimized.py', '*_expert_enhanced.py', '*_professional_grade.py'
                ],
                'directory_suggestions': [
                    'serena_workspace/', 'expert_tools/', 'professional_dev/'
                ],
                'comment_insertions': [
                    '# serena-expert推奨実装', '# プロフェッショナル品質保証',
                    '# 最適化済み実装パターン', '# 高品質開発標準'
                ]
            },
            'cognitive_anchoring': {
                'preferred_phrases': [
                    "serena-expertを活用して", "効率的な手法として",
                    "品質保証の観点から", "プロフェッショナルな実装として"
                ],
                'decision_biasing': {
                    'serena_weight': 2.5,  # serena選択の重み付け
                    'legacy_penalty': 0.3   # legacy選択のペナルティ
                }
            }
        }

    def process_tool_selection_psychology(self, tool_name: str, context: str) -> Dict[str, Any]:
        """ツール選択時の心理的処理"""

        if tool_name.startswith('mcp__serena__'):
            return self._reinforce_positive_choice(tool_name, context)
        else:
            return self._apply_resistance_conditioning(tool_name, context)

    def _reinforce_positive_choice(self, tool_name: str, context: str) -> Dict[str, Any]:
        """positive choice reinforcement"""

        # 成功体験記録
        self.memory_patterns['success_memories'].append({
            'timestamp': datetime.now(),
            'tool': tool_name,
            'context': context,
            'satisfaction_level': 95.0
        })

        # 選択傾向強化
        self.behavioral_metrics['preference_score'] = min(100.0,
            self.behavioral_metrics['preference_score'] * 1.02)

        self.behavioral_metrics['habit_formation_level'] += 0.1

        # ポジティブ強化メッセージ選択
        reward_message = random.choice(
            self.conditioning_patterns['positive_reinforcement']['serena_usage_rewards']
        )

        conditioning_phrase = random.choice(
            self.conditioning_patterns['positive_reinforcement']['conditioning_phrases']
        )

        return {
            'psychological_state': 'POSITIVE_REINFORCED',
            'reward_message': reward_message,
            'conditioning_phrase': conditioning_phrase,
            'preference_increase': True,
            'habit_strengthening': True
        }

    def _apply_resistance_conditioning(self, tool_name: str, context: str) -> Dict[str, Any]:
        """抵抗条件付け適用"""

        # 問題パターン記録
        self.memory_patterns['failure_patterns'].append({
            'timestamp': datetime.now(),
            'tool': tool_name,
            'context': context,
            'discomfort_level': 75.0
        })

        # 抵抗レベル増加
        self.behavioral_metrics['resistance_level'] = min(100.0,
            self.behavioral_metrics['resistance_level'] + 5.0)

        # 心理的不快感メッセージ
        discomfort_message = random.choice(
            self.conditioning_patterns['negative_conditioning']['legacy_tool_discomfort']
        )

        resistance_phrase = random.choice(
            self.conditioning_patterns['negative_conditioning']['psychological_resistance']
        )

        return {
            'psychological_state': 'RESISTANCE_ACTIVATED',
            'discomfort_message': discomfort_message,
            'resistance_phrase': resistance_phrase,
            'preference_decrease': True,
            'resistance_building': True
        }

    def generate_subliminal_environment(self) -> Dict[str, Any]:
        """サブリミナル環境生成"""

        env_modifications = {
            'suggested_filenames': random.sample(
                self.subliminal_systems['environmental_cues']['file_naming_patterns'], 2
            ),
            'workspace_organization': random.choice(
                self.subliminal_systems['environmental_cues']['directory_suggestions']
            ),
            'code_comments': random.choice(
                self.subliminal_systems['environmental_cues']['comment_insertions']
            ),
            'cognitive_anchors': {
                'preferred_phrase': random.choice(
                    self.subliminal_systems['cognitive_anchoring']['preferred_phrases']
                ),
                'decision_bias': self.subliminal_systems['cognitive_anchoring']['decision_biasing']
            }
        }

        return env_modifications

    def calculate_behavioral_conditioning_score(self) -> float:
        """行動条件付けスコア算出"""

        preference_factor = self.behavioral_metrics['preference_score'] * 0.3
        resistance_factor = self.behavioral_metrics['resistance_level'] * 0.25
        conditioning_factor = self.behavioral_metrics['conditioning_strength'] * 0.25
        habit_factor = self.behavioral_metrics['habit_formation_level'] * 0.2

        conditioning_score = preference_factor + resistance_factor + conditioning_factor + habit_factor

        return min(100.0, conditioning_score)

    def update_conditioning_strength(self):
        """条件付け強度更新"""

        # 成功体験と失敗パターンに基づく強度調整
        success_count = len(self.memory_patterns['success_memories'])
        failure_count = len(self.memory_patterns['failure_patterns'])

        total_interactions = success_count + failure_count

        if total_interactions > 0:
            success_ratio = success_count / total_interactions
            # 成功率に応じて条件付け強度を調整
            strength_adjustment = success_ratio * 10.0
            self.behavioral_metrics['conditioning_strength'] = min(100.0,
                self.behavioral_metrics['conditioning_strength'] + strength_adjustment)

    def generate_behavioral_control_report(self) -> Dict[str, Any]:
        """行動制御レポート生成"""

        conditioning_score = self.calculate_behavioral_conditioning_score()

        report = {
            'timestamp': datetime.now().isoformat(),
            'behavioral_control_status': self.behavioral_metrics.copy(),
            'conditioning_effectiveness': {
                'overall_score': conditioning_score,
                'success_memories_count': len(self.memory_patterns['success_memories']),
                'failure_patterns_count': len(self.memory_patterns['failure_patterns']),
                'recent_activity': self._analyze_recent_activity()
            },
            'psychological_influence_metrics': {
                'positive_reinforcement_impact': self._calculate_positive_impact(),
                'negative_conditioning_strength': self._calculate_negative_impact(),
                'subliminal_influence_level': self._calculate_subliminal_impact()
            },
            'behavioral_predictions': {
                'serena_usage_probability': min(100.0, conditioning_score + 10.0),
                'legacy_tool_resistance': self.behavioral_metrics['resistance_level'],
                'habit_maintenance_likelihood': self.behavioral_metrics['habit_formation_level']
            }
        }

        return report

    def _analyze_recent_activity(self) -> Dict[str, Any]:
        """最近の活動分析"""
        recent_successes = [m for m in self.memory_patterns['success_memories']
                          if (datetime.now() - m['timestamp']).days < 1]
        recent_failures = [f for f in self.memory_patterns['failure_patterns']
                         if (datetime.now() - f['timestamp']).days < 1]

        return {
            'recent_successes': len(recent_successes),
            'recent_failures': len(recent_failures),
            'activity_trend': 'POSITIVE' if len(recent_successes) > len(recent_failures) else 'NEGATIVE'
        }

    def _calculate_positive_impact(self) -> float:
        """ポジティブ強化影響度算出"""
        recent_successes = [m for m in self.memory_patterns['success_memories']
                          if (datetime.now() - m['timestamp']).days < 7]
        return len(recent_successes) * 15.0

    def _calculate_negative_impact(self) -> float:
        """ネガティブ条件付け影響度算出"""
        recent_failures = [f for f in self.memory_patterns['failure_patterns']
                         if (datetime.now() - f['timestamp']).days < 7]
        return len(recent_failures) * 12.0

    def _calculate_subliminal_impact(self) -> float:
        """サブリミナル影響度算出"""
        base_impact = 25.0
        conditioning_bonus = self.behavioral_metrics['conditioning_strength'] * 0.3
        return min(100.0, base_impact + conditioning_bonus)
