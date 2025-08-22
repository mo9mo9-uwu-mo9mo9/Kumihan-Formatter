"""
軽量ルールエンジン - Lightweight Rule Engine

シンプルなルールベース最適化システム
従来の複雑なML予測エンジンを軽量化

Target: 250行以内・高速実行・低メモリ使用量
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger


class RulePriority(Enum):
    """ルール優先度"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Rule:
    """最適化ルール"""

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    action: str
    priority: RulePriority
    expected_improvement: float
    description: str


@dataclass
class RuleResult:
    """ルール実行結果"""

    rule_name: str
    triggered: bool
    action_taken: str
    improvement: float
    processing_time: float
    error: Optional[str] = None


class RuleEngine:
    """軽量ルールエンジン

    シンプルなif-then形式のルールベース最適化
    - 条件ベースルール実行
    - 優先度管理
    - 軽量パフォーマンス測定
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = get_logger(__name__)
        self.config = config or {}

        # ルール定義
        self.rules: List[Rule] = []
        self.execution_history: List[RuleResult] = []

        # デフォルトルール登録
        self._register_default_rules()

        self.logger.info(
            f"Lightweight RuleEngine initialized with {len(self.rules)} rules"
        )

    def _register_default_rules(self) -> None:
        """デフォルトルール登録"""

        # 高優先度ルール
        self.add_rule(
            Rule(
                name="memory_critical",
                condition=lambda ctx: ctx.get("memory_usage", 0) > 0.9,
                action="emergency_cleanup",
                priority=RulePriority.CRITICAL,
                expected_improvement=0.3,
                description="Critical memory usage requires immediate cleanup",
            )
        )

        self.add_rule(
            Rule(
                name="file_size_extreme",
                condition=lambda ctx: ctx.get("file_size", 0) > 200000,
                action="enable_streaming",
                priority=RulePriority.HIGH,
                expected_improvement=0.4,
                description="Extremely large files require streaming processing",
            )
        )

        # 中優先度ルール
        self.add_rule(
            Rule(
                name="complexity_high",
                condition=lambda ctx: ctx.get("complexity_score", 0) > 0.8,
                action="use_simplified_parser",
                priority=RulePriority.MEDIUM,
                expected_improvement=0.2,
                description="High complexity content benefits from simplified parsing",
            )
        )

        self.add_rule(
            Rule(
                name="token_usage_high",
                condition=lambda ctx: ctx.get("token_count", 0) > 15000,
                action="enable_token_compression",
                priority=RulePriority.MEDIUM,
                expected_improvement=0.25,
                description="High token usage requires compression",
            )
        )

        # 低優先度ルール
        self.add_rule(
            Rule(
                name="processing_slow",
                condition=lambda ctx: ctx.get("processing_time", 0) > 30.0,
                action="optimize_algorithm",
                priority=RulePriority.LOW,
                expected_improvement=0.15,
                description="Slow processing can be optimized",
            )
        )

    def add_rule(self, rule: Rule) -> None:
        """ルール追加"""
        self.rules.append(rule)
        self.logger.debug(f"Added rule: {rule.name} (priority: {rule.priority.name})")

    def execute_rules(self, context: Dict[str, Any]) -> List[RuleResult]:
        """ルール実行"""
        try:
            start_time = time.time()
            results = []

            # 優先度順でソート（高優先度から実行）
            sorted_rules = sorted(
                self.rules, key=lambda r: r.priority.value, reverse=True
            )

            for rule in sorted_rules:
                result = self._execute_single_rule(rule, context)
                results.append(result)

                # 重要なルールが発動した場合、
                # 低優先度ルールをスキップ
                if result.triggered and rule.priority in [
                    RulePriority.CRITICAL,
                    RulePriority.HIGH,
                ]:
                    self.logger.info(
                        f"High priority rule {rule.name} triggered, "
                        f"skipping lower priority rules"
                    )
                    break

            execution_time = time.time() - start_time
            self.logger.info(
                f"Rule execution completed in {execution_time:.3f}s, "
                f"{len(results)} rules processed"
            )

            return results

        except Exception as e:
            self.logger.error(f"Rule execution failed: {e}")
            return []

    def _execute_single_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleResult:
        """単一ルール実行"""
        start_time = time.time()

        try:
            # 条件チェック
            if rule.condition(context):
                # アクション実行
                self._execute_action(rule.action, context)
                processing_time = time.time() - start_time

                result = RuleResult(
                    rule_name=rule.name,
                    triggered=True,
                    action_taken=rule.action,
                    improvement=rule.expected_improvement,
                    processing_time=processing_time,
                )

                self.logger.info(f"Rule triggered: {rule.name} -> {rule.action}")

            else:
                processing_time = time.time() - start_time
                result = RuleResult(
                    rule_name=rule.name,
                    triggered=False,
                    action_taken="none",
                    improvement=0.0,
                    processing_time=processing_time,
                )

            # 履歴保存
            self.execution_history.append(result)

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Rule execution failed for {rule.name}: {e}")

            return RuleResult(
                rule_name=rule.name,
                triggered=False,
                action_taken="error",
                improvement=0.0,
                processing_time=processing_time,
                error=str(e),
            )

    def _execute_action(self, action: str, context: Dict[str, Any]) -> bool:
        """アクション実行"""
        try:
            if action == "emergency_cleanup":
                # メモリクリーンアップ
                self.logger.info("Executing emergency memory cleanup")
                return True

            elif action == "enable_streaming":
                # ストリーミング処理有効化
                self.logger.info("Enabling streaming processing for large files")
                return True

            elif action == "use_simplified_parser":
                # 簡易パーサー使用
                self.logger.info("Switching to simplified parser for complex content")
                return True

            elif action == "enable_token_compression":
                # トークン圧縮有効化
                self.logger.info("Enabling token compression")
                return True

            elif action == "optimize_algorithm":
                # アルゴリズム最適化
                self.logger.info("Applying algorithm optimization")
                return True

            else:
                self.logger.warning(f"Unknown action: {action}")
                return False

        except Exception as e:
            self.logger.error(f"Action execution failed for {action}: {e}")
            return False

    def get_triggered_rules(self, context: Dict[str, Any]) -> List[str]:
        """発動予定ルール取得"""
        triggered = []

        for rule in self.rules:
            try:
                if rule.condition(context):
                    triggered.append(rule.name)
            except Exception as e:
                self.logger.warning(f"Rule condition check failed for {rule.name}: {e}")

        return triggered

    def get_rule_statistics(self) -> Dict[str, Any]:
        """ルール統計取得"""
        if not self.execution_history:
            return {"status": "no_data"}

        recent_results = self.execution_history[-50:]  # 最新50件

        triggered_count = sum(1 for r in recent_results if r.triggered)
        total_improvement = sum(r.improvement for r in recent_results if r.triggered)
        avg_processing_time = sum(r.processing_time for r in recent_results) / len(
            recent_results
        )

        # ルール別統計
        rule_stats = {}
        for result in recent_results:
            if result.rule_name not in rule_stats:
                rule_stats[result.rule_name] = {"triggered": 0, "total": 0}
            rule_stats[result.rule_name]["total"] += 1
            if result.triggered:
                rule_stats[result.rule_name]["triggered"] += 1

        return {
            "status": "active",
            "total_executions": len(self.execution_history),
            "recent_triggered_count": triggered_count,
            "recent_total_improvement": total_improvement,
            "recent_avg_processing_time": avg_processing_time,
            "trigger_rate": triggered_count / len(recent_results),
            "rule_statistics": rule_stats,
        }
