#!/usr/bin/env python3
"""
規則遵守原則コアシステム
基本的なツール検証・統計・違反記録機能

Created: 2025-08-16 (分割元: rule_enforcement_system.py)
Purpose: コアな規則遵守機能の分離・モジュール化
Status: Production Ready
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".claude-rule-enforcement.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("RULE_ENFORCEMENT")


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

        # serenaツールは基本推奨
        if tool_name in self.serena_tools:
            self._record_serena_usage(tool_name)
            return True, f"✅ serenaコマンド使用：効率的な構造化操作", None

        # 禁止ツールチェック
        if tool_name in self.forbidden_tools:
            violation = self._create_violation_event(
                tool_name, ViolationLevel.CRITICAL, context
            )
            self.violation_history.append(violation)

            # 置換提案
            suggested = self.replacement_mapping.get(tool_name)
            if suggested:
                message = f"🚨 規則遵守原則違反検出！'{tool_name}'は禁止されています。'{suggested}'を使用してください"
                logger.error(message)
                return False, message, suggested
            else:
                message = f"⛔ 規則遵守原則違反：'{tool_name}'は禁止されています。適切なツールを選択してください"
                logger.error(message)
                return False, message, None

        # その他のツールは理由明記が推奨
        logger.info(
            f"ℹ️  '{tool_name}'使用：効率性または技術制約による選択を推奨（理由明記）"
        )
        return True, f"✅ '{tool_name}'使用許可（理由明記推奨）", None

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
            user_notified=True,
        )

    def _record_serena_usage(self, tool_name: str):
        """serena使用記録"""
        self.stats.serena_usage_count += 1
        self._update_compliance_score()
        logger.info(
            f"✅ serena使用記録: {tool_name} (累計: {self.stats.serena_usage_count})"
        )

    def _update_compliance_score(self):
        """コンプライアンススコア更新"""
        total_attempts = (
            self.stats.serena_usage_count + self.stats.forbidden_tool_attempts
        )
        if total_attempts > 0:
            self.stats.compliance_score = (
                self.stats.serena_usage_count / total_attempts
            ) * 100.0
        logger.info(f"📊 コンプライアンススコア: {self.stats.compliance_score:.1f}%")

    def attempt_auto_correction(
        self, forbidden_tool: str, context: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """自動是正試行"""
        if (
            not self.config.get("violation_response", {})
            .get("auto_correction", {})
            .get("enabled", False)
        ):
            return False, "自動是正は無効です", None

        suggested_tool = self.replacement_mapping.get(forbidden_tool)
        if suggested_tool:
            self.stats.auto_corrections += 1
            correction_msg = f"🔄 自動是正実行: '{forbidden_tool}' → '{suggested_tool}'"
            logger.info(correction_msg)
            return True, correction_msg, suggested_tool

        return False, f"'{forbidden_tool}'の自動是正ができません", None

    def generate_compliance_report(self) -> Dict[str, Any]:
        """コンプライアンスレポート生成"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "compliance_score": self.stats.compliance_score,
            "statistics": {
                "serena_usage_count": self.stats.serena_usage_count,
                "forbidden_attempts": self.stats.forbidden_tool_attempts,
                "auto_corrections": self.stats.auto_corrections,
                "total_violations": len(self.violation_history),
            },
            "recent_violations": [
                {
                    "timestamp": v.timestamp.isoformat(),
                    "tool_name": v.tool_name,
                    "level": v.violation_level.value,
                    "context": v.context,
                }
                for v in self.violation_history[-10:]  # 最新10件
            ],
            "recommendations": self._generate_recommendations(),
        }

        logger.info("📋 コンプライアンスレポート生成完了")
        return report

    def _generate_recommendations(self) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []

        if self.stats.compliance_score < 90.0:
            recommendations.append(
                "serenaコマンドの効率的活用と適切な理由明記を心がけてください"
            )

        if self.stats.forbidden_tool_attempts > 0:
            recommendations.append("禁止ツールの使用を完全に停止してください")

        if len(self.violation_history) > 5:
            recommendations.append("規則遵守原則の理解を深め、習慣化を図ってください")

        if not recommendations:
            recommendations.append("素晴らしい！規則遵守原則を完全に遵守しています")

        return recommendations

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """レポート保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rule_compliance_report_{timestamp}.json"

        filepath = Path(filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 レポート保存完了: {filepath}")
        return str(filepath)

    def display_startup_message(self):
        """起動メッセージ表示"""
        startup_config = self.config.get("startup_message", "")
        if startup_config:
            print("\n" + "=" * 60)
            print(startup_config)
            print("=" * 60 + "\n")

        # システム状態表示
        print(f"🔧 システム状態:")
        print(f"   - 禁止ツール監視: {len(self.forbidden_tools)}個")
        print(f"   - serenaツール登録: {len(self.serena_tools)}個")
        print(f"   - 自動置換マッピング: {len(self.replacement_mapping)}個")
        print(f"   - コンプライアンススコア: {self.stats.compliance_score:.1f}%")
        print()
