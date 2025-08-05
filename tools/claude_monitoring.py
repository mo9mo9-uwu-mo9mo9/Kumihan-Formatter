#!/usr/bin/env python3
"""
Claude Code Serena-Expert監視システム
Kumihan-Formatter専用

CLAUDE.md P7原則違反を検出・防止するためのツール使用監視システム
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple  # List removed - unused import (F401)
from dataclasses import dataclass, asdict
import yaml


@dataclass
class ToolUsageRecord:
    """ツール使用記録"""
    timestamp: str
    tool_name: str
    tool_type: str  # 'serena', 'legacy', 'forbidden'
    task_type: str
    violation: bool
    context: str


@dataclass
class ViolationAlert:
    """違反アラート"""
    timestamp: str
    tool_used: str
    expected_tool: str
    severity: str  # 'critical', 'warning', 'info'
    message: str
    auto_corrected: bool


class SerenaMonitoringSystem:
    """Serena-Expert強制使用監視システム"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.config_file = self.project_root / ".claude-config.yml"
        self.log_file = self.project_root / ".claude-usage.log"
        self.violation_log = self.project_root / ".claude-violations.log"

        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("SerenaMonitor")

        # 設定読み込み
        self.config = self._load_config()

        # 監視対象ツール定義
        self.serena_tools = {
            'mcp__serena__find_symbol',
            'mcp__serena__replace_symbol_body',
            'mcp__serena__insert_after_symbol',
            'mcp__serena__search_for_pattern',
            'mcp__serena__get_symbols_overview',
            'mcp__serena__replace_regex',
            'mcp__serena__list_dir',
            'mcp__serena__find_file'
        }

        self.forbidden_tools = {
            'Edit', 'MultiEdit', 'Read', 'Write', 'Bash', 'Glob', 'Grep'
        }

        # 開発タスク識別キーワード
        self.development_keywords = {
            'implement', 'create', 'build', 'develop', 'code', 'component',
            'function', 'class', 'method', 'api', 'endpoint', 'feature',
            '実装', '作成', '開発', 'コンポーネント', '機能', 'クラス', 'メソッド'
        }

    def _load_config(self) -> Dict:
        """設定ファイル読み込み"""
        if not self.config_file.exists():
            self.logger.warning(f"設定ファイルが見つかりません: {self.config_file}")
            return self._default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            return self._default_config()

    def _default_config(self) -> Dict:
        """デフォルト設定"""
        return {
            'enforcement': {'level': 'strict', 'monitoring': True},
            'mandatory_tools': {'development_tasks': 'serena-expert'}
        }

    def is_development_task(self, context: str) -> bool:
        """開発タスクかどうかを判定"""
        context_lower = context.lower()
        return any(keyword in context_lower for keyword in self.development_keywords)

    def classify_tool(self, tool_name: str) -> str:
        """ツール分類"""
        if tool_name in self.serena_tools:
            return 'serena'
        elif tool_name in self.forbidden_tools:
            return 'forbidden'
        else:
            return 'legacy'

    def check_tool_usage(self, tool_name: str, context: str = "") -> Tuple[bool, Optional[ViolationAlert]]:
        """ツール使用チェック"""
        is_dev_task = self.is_development_task(context)
        tool_type = self.classify_tool(tool_name)

        # 開発タスクでserena以外のツール使用は違反
        if is_dev_task and tool_type != 'serena':
            severity = 'critical' if tool_type == 'forbidden' else 'warning'

            violation = ViolationAlert(
                timestamp=datetime.datetime.now().isoformat(),
                tool_used=tool_name,
                expected_tool='serena-expert (mcp__serena__*)',
                severity=severity,
                message=f"🚨 P7原則違反: 開発タスクでserena-expert以外のツール使用を検出",
                auto_corrected=False
            )

            return True, violation

        return False, None

    def log_tool_usage(self, tool_name: str, task_type: str, context: str = ""):
        """ツール使用をログ記録"""
        is_violation, violation_alert = self.check_tool_usage(tool_name, context)

        record = ToolUsageRecord(
            timestamp=datetime.datetime.now().isoformat(),
            tool_name=tool_name,
            tool_type=self.classify_tool(tool_name),
            task_type=task_type,
            violation=is_violation,
            context=context
        )

        # 通常ログ
        self.logger.info(f"Tool Usage: {tool_name} | Type: {record.tool_type} | Violation: {is_violation}")

        # 違反ログ
        if is_violation and violation_alert:
            self._log_violation(violation_alert)

            # 厳格モードでは即座に停止
            if self.config.get('enforcement', {}).get('level') == 'strict':
                self._handle_strict_violation(violation_alert)

        return record

    def _log_violation(self, violation: ViolationAlert):
        """違反ログ記録"""
        try:
            with open(self.violation_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(violation), ensure_ascii=False) + '\n')

            self.logger.error(f"🚨 VIOLATION: {violation.message}")
            self.logger.error(f"使用ツール: {violation.tool_used}")
            self.logger.error(f"期待ツール: {violation.expected_tool}")

        except Exception as e:
            self.logger.error(f"違反ログ記録エラー: {e}")

    def _handle_strict_violation(self, violation: ViolationAlert):
        """厳格違反処理"""
        print("\n" + "="*80)
        print("🚨 CLAUDE.md P7原則違反検出 - 強制停止 🚨")
        print("="*80)
        print(f"違反ツール: {violation.tool_used}")
        print(f"期待ツール: {violation.expected_tool}")
        print(f"メッセージ: {violation.message}")
        print("\n【対処方法】:")
        print("1. 現在の作業を中止")
        print("2. serena-expertツール (mcp__serena__*) に切り替え")
        print("3. CLAUDE.md P7原則を再確認")
        print("="*80)

        # 自動是正が有効な場合の提案
        if self.config.get('enforcement', {}).get('auto_correction'):
            print("\n🔧 推奨serena-expertツール:")
            self._suggest_serena_alternative(violation.tool_used)

    def _suggest_serena_alternative(self, used_tool: str):
        """Serena代替ツール提案"""
        suggestions = {
            'Read': 'mcp__serena__find_symbol または mcp__serena__get_symbols_overview',
            'Edit': 'mcp__serena__replace_symbol_body',
            'MultiEdit': 'mcp__serena__replace_regex',
            'Write': 'mcp__serena__insert_after_symbol',
            'Grep': 'mcp__serena__search_for_pattern',
            'Glob': 'mcp__serena__find_file'
        }

        if used_tool in suggestions:
            print(f"- {used_tool} → {suggestions[used_tool]}")
        else:
            print("- 適切なserena-expertツールを選択してください")

    def generate_usage_report(self) -> Dict:
        """使用状況レポート生成"""
        if not self.log_file.exists():
            return {"error": "ログファイルが存在しません"}

        # ログ解析実装（簡略版）
        return {
            "status": "monitoring_active",
            "config_file": str(self.config_file),
            "log_file": str(self.log_file),
            "violation_log": str(self.violation_log),
            "enforcement_level": self.config.get('enforcement', {}).get('level', 'unknown')
        }


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("使用法: python claude_monitoring.py <command> [args]")
        print("コマンド:")
        print("  check <tool_name> <context> - ツール使用チェック")
        print("  report - 使用状況レポート生成")
        return

    monitor = SerenaMonitoringSystem()
    command = sys.argv[1]

    if command == "check" and len(sys.argv) >= 4:
        tool_name = sys.argv[2]
        context = " ".join(sys.argv[3:])
        record = monitor.log_tool_usage(tool_name, "manual_check", context)
        print(f"チェック完了: {record.tool_name} | 違反: {record.violation}")

    elif command == "report":
        report = monitor.generate_usage_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))

    else:
        print("無効なコマンドです")


if __name__ == "__main__":
    main()
