"""
軽量設定最適化エンジン - Lightweight Config Optimizer

従来の複雑なAI最適化システムを簡素化した設定最適化システム
基本的なルールベース最適化とパターンマッチングに特化

Target: 200行以内・高効率・低コスト
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger


@dataclass
class OptimizationResult:
    """最適化結果"""

    success: bool
    optimizations_applied: int
    performance_gain: float
    processing_time: float
    recommendations: List[str]
    config_changes: Dict[str, Any]
    error: Optional[str] = None


class ConfigOptimizer:
    """軽量設定最適化エンジン

    シンプルなルールベース最適化システム
    - 基本的な設定調整
    - パフォーマンスパターン認識
    - 軽量な最適化提案
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = get_logger(__name__)
        self.config = config or {}

        # 最適化履歴
        self.optimization_history: List[OptimizationResult] = []

        # 基本最適化ルール
        self.optimization_rules = {
            "file_size_large": {
                "condition": lambda ctx: ctx.get("file_size", 0) > 50000,
                "action": "reduce_processing_depth",
                "expected_gain": 0.15,
            },
            "complexity_high": {
                "condition": lambda ctx: ctx.get("complexity_score", 0) > 0.8,
                "action": "optimize_parsing_strategy",
                "expected_gain": 0.20,
            },
            "token_usage_high": {
                "condition": lambda ctx: ctx.get("token_count", 0) > 10000,
                "action": "enable_compression",
                "expected_gain": 0.25,
            },
            "memory_pressure": {
                "condition": lambda ctx: ctx.get("memory_usage", 0) > 0.8,
                "action": "reduce_cache_size",
                "expected_gain": 0.10,
            },
        }

        self.logger.info("Lightweight ConfigOptimizer initialized")

    def optimize(self, context: Dict[str, Any]) -> OptimizationResult:
        """設定最適化実行"""
        try:
            start_time = time.time()

            # 適用可能な最適化を識別
            applicable_optimizations = self._identify_optimizations(context)

            # 最適化適用
            config_changes = {}
            recommendations = []
            total_gain = 0.0

            for rule_name, rule in applicable_optimizations.items():
                change, gain = self._apply_optimization(rule_name, rule, context)
                if change:
                    config_changes.update(change)
                    total_gain += gain
                    recommendations.append(f"Applied {rule['action']} for {rule_name}")

            # パフォーマンス予測
            performance_gain = min(total_gain, 0.5)  # 最大50%向上に制限

            processing_time = time.time() - start_time

            result = OptimizationResult(
                success=True,
                optimizations_applied=len(config_changes),
                performance_gain=performance_gain,
                processing_time=processing_time,
                recommendations=recommendations,
                config_changes=config_changes,
            )

            # 履歴保存
            self.optimization_history.append(result)

            self.logger.info(
                f"Optimization completed: {len(config_changes)} changes, "
                f"{performance_gain:.1%} expected gain"
            )

            return result

        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return OptimizationResult(
                success=False,
                optimizations_applied=0,
                performance_gain=0.0,
                processing_time=time.time() - start_time,
                recommendations=[],
                config_changes={},
                error=str(e),
            )

    def _identify_optimizations(
        self, context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """適用可能な最適化を識別"""
        applicable = {}

        for rule_name, rule in self.optimization_rules.items():
            try:
                condition_func = rule.get("condition")
                if callable(condition_func) and condition_func(context):
                    applicable[rule_name] = rule
            except Exception as e:
                self.logger.warning(f"Rule condition check failed for {rule_name}: {e}")

        return applicable

    def _apply_optimization(
        self, rule_name: str, rule: Dict[str, Any], context: Dict[str, Any]
    ) -> tuple[Dict[str, Any], float]:
        """最適化適用"""
        try:
            action = rule["action"]
            expected_gain = rule["expected_gain"]

            if action == "reduce_processing_depth":
                return {
                    "processing.max_depth": min(
                        context.get("processing.max_depth", 10), 8
                    ),
                    "processing.batch_size": max(
                        context.get("processing.batch_size", 100), 200
                    ),
                }, expected_gain

            elif action == "optimize_parsing_strategy":
                return {
                    "parser.complexity_threshold": 0.6,
                    "parser.use_simplified_mode": True,
                }, expected_gain

            elif action == "enable_compression":
                return {
                    "output.enable_compression": True,
                    "output.compression_level": 6,
                }, expected_gain

            elif action == "reduce_cache_size":
                return {
                    "cache.max_size": context.get("cache.max_size", 1000) // 2,
                    "cache.cleanup_threshold": 0.7,
                }, expected_gain

            return {}, 0.0

        except Exception as e:
            self.logger.error(f"Failed to apply optimization {action}: {e}")
            return {}, 0.0

    def get_optimization_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """最適化提案を取得"""
        suggestions = []

        # ファイルサイズベース提案
        file_size = context.get("file_size", 0)
        if file_size > 100000:
            suggestions.append("Consider splitting large files for better performance")
        elif file_size > 50000:
            suggestions.append("Enable batch processing for large files")

        # 複雑度ベース提案
        complexity = context.get("complexity_score", 0)
        if complexity > 0.9:
            suggestions.append("Use simplified parsing for highly complex content")
        elif complexity > 0.7:
            suggestions.append("Enable complexity-aware optimization")

        # メモリ使用量ベース提案
        memory_usage = context.get("memory_usage", 0)
        if memory_usage > 0.9:
            suggestions.append("Reduce cache size and enable cleanup")
        elif memory_usage > 0.7:
            suggestions.append("Monitor memory usage and optimize cache")

        return suggestions

    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス取得"""
        if not self.optimization_history:
            return {"status": "no_data"}

        recent_results = self.optimization_history[-10:]  # 最新10件

        avg_gain = sum(r.performance_gain for r in recent_results) / len(recent_results)
        avg_processing_time = sum(r.processing_time for r in recent_results) / len(
            recent_results
        )
        total_optimizations = sum(r.optimizations_applied for r in recent_results)

        return {
            "status": "active",
            "total_optimizations": len(self.optimization_history),
            "recent_average_gain": avg_gain,
            "recent_average_processing_time": avg_processing_time,
            "recent_total_optimizations": total_optimizations,
            "success_rate": sum(1 for r in recent_results if r.success)
            / len(recent_results),
        }
