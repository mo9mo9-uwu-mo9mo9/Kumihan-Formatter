"""
Token Usage and Complexity Analyzers
===================================

トークン使用量分析とコンテンツ複雑度分析機能を提供します。

機能:
- TokenUsageAnalyzer: リアルタイムToken使用量監視と分析
- ComplexityAnalyzer: コンテンツ複雑度評価

Issue #804 対応
"""

import threading
import time
from collections import defaultdict, deque
from statistics import mean

# WorkContextのインポート（循環インポート回避のため型ヒント用）
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from kumihan_formatter.core.unified_config import (
    EnhancedConfigAdapter as EnhancedConfig,
)
from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from .manager import WorkContext


class TokenUsageAnalyzer:
    """
    Token使用量分析システム - Issue #804 実装

    機能:
    - リアルタイムToken使用量監視
    - 使用パターン分析と予測
    - 使用量最適化提案
    - コスト効率性分析
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)
        self.config = config

        # Token使用量追跡
        self.usage_history = deque(maxlen=1000)
        self.current_session_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "operations_count": 0,
            "start_time": time.time(),
        }

        # 使用パターン分析
        self.usage_patterns = {
            "hourly_patterns": defaultdict(list),
            "operation_patterns": defaultdict(list),
            "efficiency_patterns": defaultdict(list),
        }

        # 最適化提案履歴
        self.optimization_suggestions = deque(maxlen=50)

        # 制御
        self._lock = threading.Lock()

        self.logger.info("TokenUsageAnalyzer initialized for real-time monitoring")

    def record_token_usage(
        self,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        context: Optional["WorkContext"] = None,
    ) -> Dict[str, Any]:
        """
        Token使用量を記録し分析

        Args:
            operation_type: 操作種別
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            context: 作業コンテキスト

        Returns:
            使用量分析結果
        """
        with self._lock:
            total_tokens = input_tokens + output_tokens
            timestamp = time.time()

            # 使用量記録
            usage_record = {
                "timestamp": timestamp,
                "operation_type": operation_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "context_size": context.content_size if context else 0,
                "complexity_score": context.complexity_score if context else 0.0,
            }

            self.usage_history.append(usage_record)

            # セッション統計更新
            self.current_session_usage["input_tokens"] += input_tokens
            self.current_session_usage["output_tokens"] += output_tokens
            self.current_session_usage["total_tokens"] += total_tokens
            self.current_session_usage["operations_count"] += 1

            # パターン分析更新
            self._update_usage_patterns(usage_record)

            # 分析結果生成
            analysis_result = {
                "recorded_usage": usage_record,
                "session_cumulative": self.current_session_usage.copy(),
                "efficiency_score": self._calculate_operation_efficiency(usage_record),
                "optimization_opportunities": self._identify_optimization_opportunities(
                    usage_record
                ),
            }

            # 最適化提案生成（条件付き）
            if total_tokens > self._get_optimization_threshold():
                suggestions = self._generate_optimization_suggestions(
                    usage_record, analysis_result
                )
                if suggestions:
                    analysis_result["optimization_suggestions"] = suggestions
                    self.optimization_suggestions.extend(suggestions)

            return analysis_result

    def _update_usage_patterns(self, usage_record: Dict[str, Any]):
        """使用パターンを更新"""
        hour = time.strftime("%H", time.localtime(usage_record["timestamp"]))
        operation_type = usage_record["operation_type"]

        # 時間別パターン
        self.usage_patterns["hourly_patterns"][hour].append(
            usage_record["total_tokens"]
        )

        # 操作別パターン
        self.usage_patterns["operation_patterns"][operation_type].append(
            {
                "tokens": usage_record["total_tokens"],
                "efficiency": usage_record["total_tokens"]
                / max(usage_record["context_size"], 1),
            }
        )

        # 効率パターン（複雑性対トークン比）
        if usage_record["complexity_score"] > 0:
            efficiency_ratio = (
                usage_record["total_tokens"] / usage_record["complexity_score"]
            )
            complexity_class = (
                "high" if usage_record["complexity_score"] > 0.7 else "low"
            )
            self.usage_patterns["efficiency_patterns"][complexity_class].append(
                efficiency_ratio
            )

    def _calculate_operation_efficiency(self, usage_record: Dict[str, Any]) -> float:
        """操作効率スコアを計算"""
        base_efficiency = 1.0
        total_tokens = usage_record["total_tokens"]
        context_size = usage_record["context_size"]
        complexity = usage_record["complexity_score"]

        # コンテンツサイズ対トークン効率
        if context_size > 0:
            token_ratio = total_tokens / context_size
            if token_ratio < 0.1:  # 非常に効率的
                base_efficiency += 0.3
            elif token_ratio < 0.3:  # 効率的
                base_efficiency += 0.1
            elif token_ratio > 0.8:  # 非効率
                base_efficiency -= 0.2

        # 複雑性対効率
        if complexity > 0:
            complexity_efficiency = 1.0 - (total_tokens / (complexity * 10000))
            base_efficiency += complexity_efficiency * 0.2

        return max(0.0, min(1.0, base_efficiency))

    def _identify_optimization_opportunities(
        self, usage_record: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """最適化機会を特定"""
        opportunities = []

        # 高トークン使用量の場合
        if usage_record["total_tokens"] > 5000:
            opportunities.append(
                {
                    "type": "high_token_usage",
                    "severity": "medium",
                    "description": f"高トークン使用量検出: {usage_record['total_tokens']} tokens",
                    "suggested_actions": [
                        "ファイルサイズ制限の適用",
                        "コンテンツの分割処理",
                        "不要な詳細情報の除去",
                    ],
                }
            )

        # 効率性の問題
        efficiency = self._calculate_operation_efficiency(usage_record)
        if efficiency < 0.6:
            opportunities.append(
                {
                    "type": "low_efficiency",
                    "severity": "high",
                    "description": f"低効率操作検出: 効率スコア {efficiency:.2f}",
                    "suggested_actions": [
                        "操作アプローチの見直し",
                        "コンテキスト情報の最適化",
                        "処理順序の改善",
                    ],
                }
            )

        # 不均衡な入出力比率
        if usage_record["output_tokens"] > usage_record["input_tokens"] * 3:
            opportunities.append(
                {
                    "type": "output_heavy",
                    "severity": "low",
                    "description": "出力過多パターン検出",
                    "suggested_actions": [
                        "出力内容の簡潔化",
                        "要約手法の適用",
                        "テンプレート使用の検討",
                    ],
                }
            )

        return opportunities

    def _generate_optimization_suggestions(
        self, usage_record: Dict[str, Any], analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """最適化提案を生成"""
        suggestions = []
        total_tokens = usage_record["total_tokens"]

        # 具体的な最適化提案
        if total_tokens > 8000:
            suggestions.append(
                {
                    "type": "immediate_action",
                    "priority": "high",
                    "title": "大量Token使用の緊急最適化",
                    "description": f"{total_tokens} tokens使用により効率性低下",
                    "actions": [
                        {
                            "action": "apply_file_size_limits",
                            "expected_reduction": 0.25,
                        },
                        {
                            "action": "enable_content_filtering",
                            "expected_reduction": 0.15,
                        },
                        {"action": "use_summary_mode", "expected_reduction": 0.35},
                    ],
                    "estimated_total_reduction": 0.55,
                }
            )

        # パターン基づく提案
        operation_type = usage_record["operation_type"]
        if operation_type in self.usage_patterns["operation_patterns"]:
            pattern_data = self.usage_patterns["operation_patterns"][operation_type]
            if len(pattern_data) >= 3:
                avg_tokens = sum(p["tokens"] for p in pattern_data) / len(pattern_data)
                if total_tokens > avg_tokens * 1.5:
                    suggestions.append(
                        {
                            "type": "pattern_based",
                            "priority": "medium",
                            "title": f"{operation_type}操作の効率化",
                            "description": f"平均比 {total_tokens/avg_tokens:.1f}倍の使用量",
                            "actions": [
                                {
                                    "action": "optimize_operation_flow",
                                    "expected_reduction": 0.20,
                                },
                                {"action": "apply_caching", "expected_reduction": 0.10},
                            ],
                            "estimated_total_reduction": 0.30,
                        }
                    )

        return suggestions

    def _get_optimization_threshold(self) -> int:
        """最適化提案を開始するトークン数閾値を取得"""
        # 基本閾値
        base_threshold = 3000

        # 最近のセッション平均に基づく動的調整
        if len(self.usage_history) >= 10:
            recent_avg = (
                sum(record["total_tokens"] for record in list(self.usage_history)[-10:])
                / 10
            )
            base_threshold = max(base_threshold, int(recent_avg * 1.5))

        return base_threshold

    def get_usage_analytics(self) -> Dict[str, Any]:
        """使用量分析結果を取得"""
        with self._lock:
            if not self.usage_history:
                return {"status": "no_data"}

            # 基本統計の計算
            total_operations = len(self.usage_history)
            total_tokens_all = sum(
                record["total_tokens"] for record in self.usage_history
            )
            avg_tokens_per_operation = (
                total_tokens_all / total_operations if total_operations > 0 else 0
            )

            # 効率性の計算
            efficiency_scores = [
                record.get("efficiency", 0.5) for record in self.usage_history
            ]
            avg_efficiency = (
                sum(efficiency_scores) / len(efficiency_scores)
                if efficiency_scores
                else 0.5
            )

            # トレンド分析
            trend_direction = "stable"
            if len(self.usage_history) >= 20:
                mid_point = len(self.usage_history) // 2
                recent_avg = sum(
                    record["total_tokens"]
                    for record in list(self.usage_history)[mid_point:]
                ) / (len(self.usage_history) - mid_point)
                older_avg = (
                    sum(
                        record["total_tokens"]
                        for record in list(self.usage_history)[:mid_point]
                    )
                    / mid_point
                )

                if recent_avg > older_avg * 1.1:
                    trend_direction = "increasing"
                elif recent_avg < older_avg * 0.9:
                    trend_direction = "decreasing"

            # 操作別効率性
            operation_efficiency = {}
            for op_type, pattern_data in self.usage_patterns[
                "operation_patterns"
            ].items():
                if len(pattern_data) >= 3:
                    avg_efficiency_op = sum(
                        p["efficiency"] for p in pattern_data
                    ) / len(pattern_data)
                    operation_efficiency[op_type] = avg_efficiency_op

            return {
                "session_summary": self.current_session_usage,
                "historical_analytics": {
                    "total_operations": total_operations,
                    "total_tokens_consumed": total_tokens_all,
                    "average_tokens_per_operation": avg_tokens_per_operation,
                    "overall_efficiency_score": avg_efficiency,
                    "usage_trend": trend_direction,
                },
                "pattern_insights": {
                    "operation_efficiency": operation_efficiency,
                    "peak_usage_hours": self._get_peak_usage_hours(),
                    "efficiency_by_complexity": self._get_complexity_efficiency_analysis(),
                },
                "optimization_status": {
                    "active_suggestions_count": len(self.optimization_suggestions),
                    "recent_optimizations": list(self.optimization_suggestions)[-5:],
                    "potential_savings": self._calculate_potential_savings(),
                },
                "recommendations": self._generate_usage_recommendations(),
            }

    def _get_peak_usage_hours(self) -> List[str]:
        """ピーク使用時間を取得"""
        hourly_averages = {}
        for hour, tokens_list in self.usage_patterns["hourly_patterns"].items():
            if tokens_list:
                hourly_averages[hour] = sum(tokens_list) / len(tokens_list)

        # 上位3時間を返す
        sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:3]]

    def _get_complexity_efficiency_analysis(self) -> Dict[str, float]:
        """複雑性別効率分析"""
        analysis = {}
        for complexity_class, ratios in self.usage_patterns[
            "efficiency_patterns"
        ].items():
            if ratios:
                analysis[complexity_class] = sum(ratios) / len(ratios)
        return analysis

    def _calculate_potential_savings(self) -> Dict[str, Any]:
        """潜在的節約効果を計算"""
        if not self.optimization_suggestions:
            return {"total_potential_reduction": 0.0, "estimated_token_savings": 0}

        # 最近の提案を取得
        recent_suggestions = list(self.optimization_suggestions)[-10:]
        total_reduction = 0.0

        for suggestion in recent_suggestions:
            if "estimated_total_reduction" in suggestion:
                total_reduction += suggestion["estimated_total_reduction"]

        avg_reduction = (
            total_reduction / len(recent_suggestions) if recent_suggestions else 0.0
        )
        recent_token_usage = (
            sum(record["total_tokens"] for record in list(self.usage_history)[-20:])
            if len(self.usage_history) >= 20
            else 0
        )

        estimated_savings = int(recent_token_usage * avg_reduction)

        return {
            "average_potential_reduction": avg_reduction,
            "estimated_token_savings": estimated_savings,
            "basis_operations": len(recent_suggestions),
        }

    def _generate_usage_recommendations(self) -> List[Dict[str, Any]]:
        """使用量に基づく推奨事項を生成"""
        recommendations = []

        # セッション使用量に基づく推奨
        session_tokens = self.current_session_usage["total_tokens"]
        if session_tokens > 50000:
            recommendations.append(
                {
                    "category": "session_optimization",
                    "priority": "high",
                    "title": "セッション使用量最適化",
                    "description": f"現在セッションで {session_tokens} tokens使用",
                    "action": "セッション分割またはコンテンツ最適化を検討",
                }
            )

        # 効率性に基づく推奨
        if len(self.usage_history) >= 10:
            recent_efficiency = [
                self._calculate_operation_efficiency(record)
                for record in list(self.usage_history)[-10:]
            ]
            avg_recent_efficiency = sum(recent_efficiency) / len(recent_efficiency)

            if avg_recent_efficiency < 0.7:
                recommendations.append(
                    {
                        "category": "efficiency_improvement",
                        "priority": "medium",
                        "title": "操作効率性改善",
                        "description": f"最近の効率スコア: {avg_recent_efficiency:.2f}",
                        "action": "ファイルサイズ制限や並列制御の適用を推奨",
                    }
                )

        # パターンに基づく推奨
        for op_type, pattern_data in self.usage_patterns["operation_patterns"].items():
            if len(pattern_data) >= 5:
                avg_tokens = sum(p["tokens"] for p in pattern_data) / len(pattern_data)
                if avg_tokens > 4000:
                    recommendations.append(
                        {
                            "category": "operation_specific",
                            "priority": "low",
                            "title": f"{op_type}操作最適化",
                            "description": f"平均 {avg_tokens:.0f} tokens使用",
                            "action": f"{op_type}操作のアプローチ見直しを推奨",
                        }
                    )

        return recommendations


class ComplexityAnalyzer:
    """コンテンツ複雑度分析"""

    def analyze(self, content: str) -> float:
        """コンテンツ複雑度を0-1で評価"""
        factors = []

        # 記法種類数
        notation_count = self._count_notations(content)
        factors.append(min(notation_count / 10, 1.0))

        # ネスト深度
        nest_depth = self._analyze_nesting(content)
        factors.append(min(nest_depth / 5, 1.0))

        # 特殊文字密度
        special_char_ratio = self._calculate_special_char_ratio(content)
        factors.append(special_char_ratio)

        # 行数
        line_count = content.count("\n")
        factors.append(min(line_count / 1000, 1.0))

        return mean(factors)

    def _count_notations(self, content: str) -> int:
        """記法種類数をカウント"""
        notations = ["太字", "イタリック", "見出し", "ハイライト", "枠線"]
        count = 0
        for notation in notations:
            if f"# {notation} #" in content:
                count += 1
        return count

    def _analyze_nesting(self, content: str) -> int:
        """ネスト深度を分析"""
        max_depth = 0
        current_depth = 0

        for char in content:
            if char == "#":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "\n":
                current_depth = 0

        return max_depth

    def _calculate_special_char_ratio(self, content: str) -> float:
        """特殊文字密度を計算"""
        special_chars = set("#[](){}*_~`")
        special_count = sum(1 for char in content if char in special_chars)
        return min(special_count / len(content), 1.0) if content else 0.0
