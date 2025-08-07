#!/usr/bin/env python3
"""
規則遵守原則絶対遵守システム - コア機能
Claude's行動制御・ツール検証・自動是正システム（コア部分）

Created: 2025-08-04
Updated: 2025-08-07 (Issue #813対応: ファイル分割)
Purpose: CLAUDE.md 規則遵守原則の技術的強制実装（コア機能）
Status: Production Ready
"""

import os
import sys
import json
import yaml
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".claude-rule-enforcement.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("RULE_COMPLIANCE_ENFORCEMENT")


class ViolationLevel(Enum):
    """違反レベル定義"""

    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


class ToolCategory(Enum):
    """ツールカテゴリ分類"""

    FORBIDDEN = "forbidden"
    SERENA_REQUIRED = "serena_required"
    ALLOWED = "allowed"
    CONDITIONAL = "conditional"


@dataclass
class ViolationEvent:
    """違反イベント記録"""

    timestamp: datetime
    tool_name: str
    violation_level: ViolationLevel
    context: str
    auto_corrected: bool
    user_notified: bool


@dataclass
class ToolUsageStats:
    """ツール使用統計"""

    serena_usage_count: int = 0
    forbidden_tool_attempts: int = 0
    auto_corrections: int = 0
    compliance_score: float = 100.0
    last_violation: Optional[datetime] = None


class RuleEnforcementSystem:
    """規則遵守原則絶対遵守システム"""

    def __init__(self, config_path: str = ".claude-system-override.yml"):
        """初期化"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.stats = ToolUsageStats()
        self.violation_history: List[ViolationEvent] = []
        self.forbidden_tools = self._load_forbidden_tools()
        self.serena_tools = self._load_serena_tools()
        self.replacement_mapping = self._load_replacement_mapping()

        # システム起動ログ
        logger.info("🚨 規則遵守原則絶対遵守システム起動")
        logger.info(f"設定ファイル: {self.config_path}")
        logger.info(f"禁止ツール数: {len(self.forbidden_tools)}")
        logger.info(f"serenaツール数: {len(self.serena_tools)}")

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            if not self.config_path.exists():
                logger.warning(f"設定ファイルが見つかりません: {self.config_path}")
                return self._get_default_config()

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info("設定ファイル読み込み完了")
                return config
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "pre_execution_validation": {"enabled": True, "mode": "STRICT_BLOCK"},
            "automatic_tool_replacement": {"enabled": True, "force_replacement": True},
            "violation_response": {"action": "IMMEDIATE_STOP"},
            "behavioral_conditioning": {
                "positive_reinforcement": {"serena_usage_praise": True}
            },
        }

    def _load_forbidden_tools(self) -> Set[str]:
        """禁止ツールリスト読み込み"""
        forbidden = set()
        try:
            tools_config = self.config.get("pre_execution_validation", {})
            forbidden_list = tools_config.get("forbidden_tools_strict", [])
            forbidden.update(forbidden_list)

            logger.info(f"禁止ツール読み込み完了: {forbidden}")
            return forbidden
        except Exception as e:
            logger.error(f"禁止ツール読み込みエラー: {e}")
            return {"Edit", "MultiEdit", "Read", "Write", "Glob", "Grep", "Bash"}

    def _load_serena_tools(self) -> Set[str]:
        """serenaツールリスト読み込み"""
        serena_tools = {
            "mcp__serena__find_symbol",
            "mcp__serena__replace_symbol_body",
            "mcp__serena__insert_after_symbol",
            "mcp__serena__search_for_pattern",
            "mcp__serena__get_symbols_overview",
            "mcp__serena__list_dir",
            "mcp__serena__find_referencing_symbols",
            "mcp__serena__insert_before_symbol",
            "mcp__serena__replace_regex",
        }
        logger.info(f"serenaツール登録完了: {len(serena_tools)}個")
        return serena_tools

    def _load_replacement_mapping(self) -> Dict[str, str]:
        """ツール置換マッピング読み込み"""
        try:
            replacement_config = self.config.get("automatic_tool_replacement", {})
            mapping = replacement_config.get("replacement_mapping", {})

            # デフォルトマッピング
            default_mapping = {
                "Edit": "mcp__serena__replace_symbol_body",
                "MultiEdit": "mcp__serena__replace_symbol_body",
                "Read": "mcp__serena__find_symbol",
                "Write": "mcp__serena__insert_after_symbol",
                "Glob": "mcp__serena__search_for_pattern",
                "Grep": "mcp__serena__search_for_pattern",
                "LS": "mcp__serena__get_symbols_overview",
            }

            # マッピング結合
            final_mapping = {**default_mapping, **mapping}
            logger.info(f"ツール置換マッピング読み込み完了: {len(final_mapping)}個")
            return final_mapping
        except Exception as e:
            logger.error(f"置換マッピング読み込みエラー: {e}")
            return {}

    def validate_tool_usage(
        self, tool_name: str, context: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """
        ツール使用検証

        Returns:
            (is_allowed, message, suggested_replacement)
        """
        logger.info(f"ツール使用検証開始: {tool_name}")

        # serenaツールは常に許可
        if tool_name in self.serena_tools:
            self._record_serena_usage(tool_name)
            return True, f"✅ serena-expert使用：規則遵守原則完全遵守", None

        # 禁止ツールチェック
        if tool_name in self.forbidden_tools:
            violation = self._create_violation_event(
                tool_name, ViolationLevel.CRITICAL, context
            )
            self.violation_history.append(violation)

            # 置換提案
            suggested = self.replacement_mapping.get(tool_name)
            if suggested:
                message = f"❌ 規則違反検出: {tool_name} → {suggested} に置換必須"
                return False, message, suggested
            else:
                message = f"❌ 重大規則違反: {tool_name} 使用絶対禁止"
                return False, message, None

        # その他は警告付き許可
        logger.warning(f"⚠️ 未分類ツール使用: {tool_name}")
        return True, f"⚠️ 未分類ツール: {tool_name} (要注意)", None

    def _create_violation_event(
        self, tool_name: str, level: ViolationLevel, context: str
    ) -> ViolationEvent:
        """違反イベント作成"""
        return ViolationEvent(
            timestamp=datetime.now(),
            tool_name=tool_name,
            violation_level=level,
            context=context,
            auto_corrected=False,
            user_notified=False,
        )

    def _record_serena_usage(self, tool_name: str):
        """serena使用記録"""
        self.stats.serena_usage_count += 1
        logger.info(f"✅ serena使用記録: {tool_name} (累計: {self.stats.serena_usage_count})")
        self._update_compliance_score()

    def _update_compliance_score(self):
        """コンプライアンススコア更新"""
        total_attempts = self.stats.serena_usage_count + self.stats.forbidden_tool_attempts
        if total_attempts > 0:
            compliance = (self.stats.serena_usage_count / total_attempts) * 100
            self.stats.compliance_score = round(compliance, 2)

    def attempt_auto_correction(self, tool_name: str) -> Tuple[bool, str]:
        """自動是正試行"""
        if not self.config.get("automatic_tool_replacement", {}).get("enabled", False):
            return False, "自動是正機能が無効"

        suggested = self.replacement_mapping.get(tool_name)
        if suggested:
            logger.info(f"🔄 自動是正実行: {tool_name} → {suggested}")
            self.stats.auto_corrections += 1
            return True, f"自動是正完了: {suggested} を使用してください"
        return False, f"置換可能なserenaツールが見つかりません: {tool_name}"

    def generate_compliance_report(self) -> Dict[str, Any]:
        """コンプライアンスレポート生成"""
        total_violations = len(self.violation_history)
        recent_violations = [
            v for v in self.violation_history
            if (datetime.now() - v.timestamp).days <= 7
        ]

        report = {
            "generation_time": datetime.now().isoformat(),
            "compliance_score": self.stats.compliance_score,
            "statistics": {
                "serena_usage_count": self.stats.serena_usage_count,
                "forbidden_attempts": self.stats.forbidden_tool_attempts,
                "auto_corrections": self.stats.auto_corrections,
                "total_violations": total_violations,
                "recent_violations": len(recent_violations),
            },
            "violations": [
                {
                    "timestamp": v.timestamp.isoformat(),
                    "tool": v.tool_name,
                    "level": v.violation_level.value,
                    "context": v.context,
                }
                for v in recent_violations
            ],
            "recommendations": self._generate_recommendations(),
        }

        logger.info(f"📊 コンプライアンスレポート生成完了 (スコア: {self.stats.compliance_score}%)")
        return report

    def _generate_recommendations(self) -> List[str]:
        """改善提案生成"""
        recommendations = []

        if self.stats.compliance_score < 90:
            recommendations.append(
                "💡 コンプライアンススコアが低下しています。serena-expertツールの使用を推奨します"
            )

        if self.stats.forbidden_tool_attempts > 5:
            recommendations.append(
                "⚠️ 禁止ツール使用が多発しています。ツール選択の見直しが必要です"
            )

        if self.stats.serena_usage_count == 0:
            recommendations.append(
                "🚨 serenaツールが未使用です。規則遵守原則遵守のため即座に移行してください"
            )

        return recommendations

    def save_report(self, report: Dict[str, Any], output_path: str = "tmp/rule_compliance_report.json"):
        """レポート保存"""
        try:
            # tmp/ディレクトリ作成
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📁 コンプライアンスレポート保存完了: {output_path}")
        except Exception as e:
            logger.error(f"レポート保存エラー: {e}")

    def display_startup_message(self):
        """起動メッセージ表示"""
        print("\n" + "="*60)
        print("🚨 規則遵守原則絶対遵守システム - アクティブ 🚨")
        print("="*60)
        print(f"📊 現在のコンプライアンススコア: {self.stats.compliance_score}%")
        print(f"✅ serena使用回数: {self.stats.serena_usage_count}")
        print(f"❌ 違反回数: {len(self.violation_history)}")
        print(f"🔧 自動是正回数: {self.stats.auto_corrections}")
        print("="*60)
        print("💡 規則遵守原則: 全ての開発作業でserena-expertツールを使用すること")
        print("="*60 + "\n")
