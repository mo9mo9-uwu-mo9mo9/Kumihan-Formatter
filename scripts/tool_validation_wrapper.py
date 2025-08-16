#!/usr/bin/env python3
"""
Claude Tool Validation Wrapper
規則遵守原則リアルタイム検証・自動是正システム

Created: 2025-08-04
Purpose: Claude's tool execution を wrapper して 規則遵守原則違反を防止
Status: Production Ready
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from functools import wraps

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".claude-tool-validation.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("TOOL_VALIDATION")


class ToolInterceptor:
    """ツール実行インターセプター"""

    def __init__(self):
        """初期化"""
        self.forbidden_tools = {
            "Edit",
            "MultiEdit",
            "Read",
            "Write",
            "Glob",
            "Grep",
            "Bash",
            "LS",
        }

        self.serena_tools = {
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

        self.replacement_mapping = {
            "Edit": "mcp__serena__replace_symbol_body",
            "MultiEdit": "mcp__serena__replace_symbol_body",
            "Read": "mcp__serena__find_symbol",
            "Write": "mcp__serena__insert_after_symbol",
            "Glob": "mcp__serena__search_for_pattern",
            "Grep": "mcp__serena__search_for_pattern",
            "LS": "mcp__serena__get_symbols_overview",
        }

        self.violation_count = 0
        self.correction_count = 0
        self.session_start = datetime.now()

        logger.info("🛡️ ツールインターセプター初期化完了")

    def intercept_tool_call(
        self, tool_name: str, parameters: Dict[str, Any] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        ツール呼び出しインターセプト

        Returns:
            (should_proceed, message, alternative_tool)
        """
        logger.info(f"🔍 ツール呼び出し検証: {tool_name}")

        # serenaツールは常に許可
        if tool_name in self.serena_tools:
            self._log_serena_usage(tool_name)
            return True, f"✅ serena-expert使用承認: {tool_name}", None

        # 禁止ツールチェック
        if tool_name in self.forbidden_tools:
            self.violation_count += 1
            alternative = self.replacement_mapping.get(tool_name)

            violation_msg = (
                f"🚨 規則遵守原則違反検出！'{tool_name}'の使用は禁止されています"
            )

            if alternative:
                suggestion_msg = f"代替ツール: '{alternative}' を使用してください"
                logger.error(f"{violation_msg} | {suggestion_msg}")
                return False, f"{violation_msg}\n{suggestion_msg}", alternative
            else:
                fallback_msg = "serena-expertツールを使用してください"
                logger.error(f"{violation_msg} | {fallback_msg}")
                return False, f"{violation_msg}\n{fallback_msg}", None

        # その他のツール（条件付き許可）
        warning_msg = f"⚠️ 注意: '{tool_name}' - serena-expertツール推奨"
        logger.warning(warning_msg)
        return True, warning_msg, None

    def _log_serena_usage(self, tool_name: str):
        """serena使用ログ"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"✅ [{timestamp}] serena使用: {tool_name} - 規則遵守原則遵守"
        logger.info(success_msg)

        # 使用パターン分析
        self._analyze_usage_pattern(tool_name)

    def _analyze_usage_pattern(self, tool_name: str):
        """使用パターン分析"""
        pattern_analysis = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "category": "serena-expert",
            "compliance": True,
        }

        # パターンファイル保存
        pattern_file = Path(".claude-usage-patterns.jsonl")
        with open(pattern_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(pattern_analysis, ensure_ascii=False) + "\n")

    def generate_session_summary(self) -> Dict[str, Any]:
        """セッション要約生成"""
        session_duration = (datetime.now() - self.session_start).total_seconds()

        summary = {
            "session_start": self.session_start.isoformat(),
            "session_duration_seconds": session_duration,
            "violations_detected": self.violation_count,
            "auto_corrections": self.correction_count,
            "compliance_status": (
                "EXCELLENT" if self.violation_count == 0 else "NEEDS_IMPROVEMENT"
            ),
            "rule_adherence_score": max(0, 100 - (self.violation_count * 10)),
            "recommendations": self._generate_session_recommendations(),
        }

        logger.info(f"📊 セッション要約生成: {summary['compliance_status']}")
        return summary

    def _generate_session_recommendations(self) -> List[str]:
        """セッション推奨事項"""
        recommendations = []

        if self.violation_count == 0:
            recommendations.append("素晴らしい！規則遵守原則を完全に遵守しました")
        elif self.violation_count <= 2:
            recommendations.append(
                "良好です。小さな改善で規則遵守原則完全遵守を達成できます"
            )
        else:
            recommendations.append(
                "規則遵守原則の理解を深め、serena-expertツールの習慣化を図ってください"
            )

        recommendations.append("継続的にserena-expertツールを使用してください")
        recommendations.append("従来ツールの使用を完全に停止してください")

        return recommendations


class RuleComplianceValidationDecorator:
    """規則遵守検証デコレーター"""

    def __init__(self):
        self.interceptor = ToolInterceptor()

    def validate_tool(self, tool_name: str):
        """ツール検証デコレーター"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 実行前検証
                should_proceed, message, alternative = (
                    self.interceptor.intercept_tool_call(tool_name, kwargs)
                )

                if not should_proceed:
                    # 違反検出時の処理
                    violation_error = f"❌ 規則遵守原則違反により実行停止\n{message}"
                    logger.error(violation_error)

                    # 自動是正試行
                    if alternative:
                        correction_msg = (
                            f"🔄 自動是正提案: {alternative} を使用してください"
                        )
                        logger.info(correction_msg)
                        return {"error": violation_error, "suggestion": alternative}

                    return {"error": violation_error}

                # 実行許可時
                logger.info(f"✅ ツール実行許可: {tool_name}")

                try:
                    result = func(*args, **kwargs)
                    logger.info(f"✅ ツール実行完了: {tool_name}")
                    return result
                except Exception as e:
                    error_msg = f"❌ ツール実行エラー: {tool_name} - {str(e)}"
                    logger.error(error_msg)
                    return {"error": error_msg}

            return wrapper

        return decorator


# グローバルインスタンス
_validator = RuleComplianceValidationDecorator()


# デコレーター関数群
def validate_edit_tool(func):
    """Edit系ツール検証"""
    return _validator.validate_tool("Edit")(func)


def validate_read_tool(func):
    """Read系ツール検証"""
    return _validator.validate_tool("Read")(func)


def validate_search_tool(func):
    """Search系ツール検証"""
    return _validator.validate_tool("Grep")(func)


def validate_serena_tool(tool_name: str):
    """serenaツール検証（常に許可）"""
    return _validator.validate_tool(tool_name)


# 実行時チェック関数
def pre_execution_check(tool_name: str, context: str = "") -> bool:
    """実行前チェック"""
    interceptor = ToolInterceptor()
    should_proceed, message, alternative = interceptor.intercept_tool_call(tool_name)

    if not should_proceed:
        print(f"\n🚨 {message}")
        if alternative:
            print(f"💡 推奨: {alternative}")
        return False

    print(f"✅ {message}")
    return True


def main():
    """メイン実行・テスト用"""
    print("🧪 規則遵守検証システムテスト")

    # テストケース
    test_tools = ["Edit", "Read", "mcp__serena__find_symbol", "Bash", "Write"]

    interceptor = ToolInterceptor()

    for tool in test_tools:
        print(f"\n🔍 テスト: {tool}")
        should_proceed, message, alternative = interceptor.intercept_tool_call(tool)
        print(f"   結果: {message}")
        if alternative:
            print(f"   代替: {alternative}")

    # セッション要約
    summary = interceptor.generate_session_summary()
    print(f"\n📊 セッション要約:")
    print(f"   違反数: {summary['violations_detected']}")
    print(f"   スコア: {summary['rule_adherence_score']}")
    print(f"   状態: {summary['compliance_status']}")


if __name__ == "__main__":
    main()
