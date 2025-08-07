"""
Token効率性分析システム
Issue #813対応 - performance_metrics.pyから分離
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Optional

from ..utilities.logger import get_logger


@dataclass
class TokenEfficiencyMetrics:
    """Token効率性メトリクス"""

    tokens_per_second: float
    tokens_per_mb_memory: float
    efficiency_score: float
    trend_direction: str
    baseline_comparison: float
    pattern_efficiency: Dict[str, float]


@dataclass
class InefficiencyPattern:
    """非効率性パターン"""

    pattern_name: str
    frequency: int
    impact_score: float
    suggested_optimization: str
    affected_operations: List[str]


class TokenEfficiencyAnalyzer:
    """
    Token効率性分析システム

    機能:
    - リアルタイムToken効率監視
    - 効率性スコアリング
    - 効率性傾向分析
    - ベースライン比較
    """

    def __init__(self, monitoring_window_size: int = 100):
        self.logger = get_logger(__name__)
        self.monitoring_window_size = monitoring_window_size

        # 効率性データ履歴
        self.efficiency_history: deque[TokenEfficiencyMetrics] = deque(
            maxlen=monitoring_window_size
        )
        self.baseline_efficiency: Optional[float] = None

        # パターン別効率性追跡
        self.pattern_efficiencies: Dict[str, List[float]] = defaultdict(list)

        # 効率性閾値設定
        self.efficiency_thresholds = {
            "excellent": 0.9,
            "good": 0.7,
            "acceptable": 0.5,
            "poor": 0.3,
        }

        self.logger.info("TokenEfficiencyAnalyzer initialized")

    def analyze_efficiency(
        self,
        tokens_used: int,
        processing_time: float,
        memory_mb: float,
        operation_pattern: str = "default",
    ) -> TokenEfficiencyMetrics:
        """Token効率性を分析"""

        # 基本効率性メトリクス計算
        tokens_per_second = tokens_used / processing_time if processing_time > 0 else 0
        tokens_per_mb_memory = tokens_used / memory_mb if memory_mb > 0 else 0

        # 効率性スコア計算（0-1正規化）
        efficiency_score = self._calculate_efficiency_score(
            tokens_per_second, tokens_per_mb_memory, tokens_used
        )

        # 傾向分析
        trend_direction = self._analyze_trend()

        # ベースライン比較
        baseline_comparison = self._compare_to_baseline(efficiency_score)

        # パターン別効率性更新
        self.pattern_efficiencies[operation_pattern].append(efficiency_score)
        pattern_efficiency = {
            pattern: mean(scores[-10:]) if scores else 0.0
            for pattern, scores in self.pattern_efficiencies.items()
        }

        metrics = TokenEfficiencyMetrics(
            tokens_per_second=tokens_per_second,
            tokens_per_mb_memory=tokens_per_mb_memory,
            efficiency_score=efficiency_score,
            trend_direction=trend_direction,
            baseline_comparison=baseline_comparison,
            pattern_efficiency=pattern_efficiency,
        )

        # 履歴に追加
        self.efficiency_history.append(metrics)

        # ベースライン設定（初回）
        if self.baseline_efficiency is None:
            self.baseline_efficiency = efficiency_score

        self.logger.debug(
            f"Efficiency analysis: score={efficiency_score:.3f}, trend={trend_direction}"
        )
        return metrics

    def _calculate_efficiency_score(
        self, tokens_per_second: float, tokens_per_mb_memory: float, total_tokens: int
    ) -> float:
        """効率性スコアを計算"""
        # 正規化ファクター（実際の運用データに基づいて調整）
        time_efficiency = min(tokens_per_second / 1000, 1.0)  # 1000 tokens/sec が最大
        memory_efficiency = min(
            tokens_per_mb_memory / 10000, 1.0
        )  # 10000 tokens/MB が最大

        # Token使用量効率性（少ないほど良い）
        token_efficiency = max(0, 1.0 - (total_tokens / 50000))  # 50000トークンを基準

        # 重み付き統合スコア
        weighted_score = (
            time_efficiency * 0.4 + memory_efficiency * 0.3 + token_efficiency * 0.3
        )

        return min(max(weighted_score, 0.0), 1.0)

    def _analyze_trend(self) -> str:
        """効率性の傾向を分析"""
        if len(self.efficiency_history) < 3:
            return "insufficient_data"

        recent_scores = [m.efficiency_score for m in list(self.efficiency_history)[-5:]]
        if len(recent_scores) < 2:
            return "insufficient_data"

        # 簡易トレンド分析
        trend_sum = sum(
            recent_scores[i] - recent_scores[i - 1]
            for i in range(1, len(recent_scores))
        )

        if trend_sum > 0.05:
            return "improving"
        elif trend_sum < -0.05:
            return "degrading"
        else:
            return "stable"

    def _compare_to_baseline(self, current_score: float) -> float:
        """ベースラインとの比較"""
        if self.baseline_efficiency is None:
            return 0.0

        return (current_score - self.baseline_efficiency) / self.baseline_efficiency

    def get_efficiency_summary(self) -> Dict:
        """効率性概要を取得"""
        if not self.efficiency_history:
            return {"status": "no_data"}

        recent_scores = [m.efficiency_score for m in self.efficiency_history]
        current_score = recent_scores[-1] if recent_scores else 0.0

        # 効率性レベル判定
        efficiency_level = "poor"
        for level, threshold in sorted(
            self.efficiency_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if current_score >= threshold:
                efficiency_level = level
                break

        return {
            "current_score": current_score,
            "efficiency_level": efficiency_level,
            "average_score": mean(recent_scores),
            "trend": self._analyze_trend(),
            "baseline_comparison_percent": self._compare_to_baseline(current_score)
            * 100,
            "pattern_efficiencies": {
                pattern: mean(scores[-5:]) if scores else 0.0
                for pattern, scores in self.pattern_efficiencies.items()
            },
        }


class PatternDetector:
    """
    非効率性パターン検出システム

    機能:
    - 実行時非効率性パターンの自動検出
    - パターン頻度分析
    - 最適化推奨の生成
    - パフォーマンスボトルネックの特定
    """

    def __init__(self):
        self.logger = get_logger(__name__)

        # パターン検出履歴
        self.detected_patterns: List[InefficiencyPattern] = []

        # パターン検出ルール
        self.detection_rules = {
            "high_token_usage": {
                "threshold": 10000,
                "description": "高Token使用量",
                "optimization": "処理単位の分割、キャッシュ活用を検討",
            },
            "slow_processing": {
                "threshold": 30.0,  # 秒
                "description": "処理時間が長い",
                "optimization": "並列処理、アルゴリズム最適化を検討",
            },
            "high_memory_usage": {
                "threshold": 500.0,  # MB
                "description": "高メモリ使用量",
                "optimization": "メモリ効率的なデータ構造、ストリーミング処理を検討",
            },
            "frequent_gc": {
                "threshold": 10,  # 回数
                "description": "頻繁なガベージコレクション",
                "optimization": "オブジェクト生成の削減、プールパターン適用を検討",
            },
        }

        self.logger.info("PatternDetector initialized")

    def detect_patterns(
        self,
        tokens_used: int,
        processing_time: float,
        memory_mb: float,
        gc_count: int = 0,
        operation_name: str = "unknown",
    ) -> List[InefficiencyPattern]:
        """非効率性パターンを検出"""
        patterns = []

        # 高Token使用量パターン検出
        if tokens_used > self.detection_rules["high_token_usage"]["threshold"]:
            pattern = InefficiencyPattern(
                pattern_name="high_token_usage",
                frequency=1,
                impact_score=min(tokens_used / 50000, 1.0),
                suggested_optimization=self.detection_rules["high_token_usage"][
                    "optimization"
                ],
                affected_operations=[operation_name],
            )
            patterns.append(pattern)

        # 低速処理パターン検出
        if processing_time > self.detection_rules["slow_processing"]["threshold"]:
            pattern = InefficiencyPattern(
                pattern_name="slow_processing",
                frequency=1,
                impact_score=min(processing_time / 60, 1.0),
                suggested_optimization=self.detection_rules["slow_processing"][
                    "optimization"
                ],
                affected_operations=[operation_name],
            )
            patterns.append(pattern)

        # 高メモリ使用パターン検出
        if memory_mb > self.detection_rules["high_memory_usage"]["threshold"]:
            pattern = InefficiencyPattern(
                pattern_name="high_memory_usage",
                frequency=1,
                impact_score=min(memory_mb / 1000, 1.0),
                suggested_optimization=self.detection_rules["high_memory_usage"][
                    "optimization"
                ],
                affected_operations=[operation_name],
            )
            patterns.append(pattern)

        # 頻繁GCパターン検出
        if gc_count > self.detection_rules["frequent_gc"]["threshold"]:
            pattern = InefficiencyPattern(
                pattern_name="frequent_gc",
                frequency=gc_count,
                impact_score=min(gc_count / 50, 1.0),
                suggested_optimization=self.detection_rules["frequent_gc"][
                    "optimization"
                ],
                affected_operations=[operation_name],
            )
            patterns.append(pattern)

        # 検出したパターンを履歴に追加
        for pattern in patterns:
            self._update_pattern_history(pattern)

        if patterns:
            self.logger.info(
                f"Detected {len(patterns)} inefficiency patterns for operation: {operation_name}"
            )

        return patterns

    def _update_pattern_history(self, new_pattern: InefficiencyPattern):
        """パターン履歴を更新"""
        # 既存の同じパターンを検索
        existing_pattern = None
        for pattern in self.detected_patterns:
            if pattern.pattern_name == new_pattern.pattern_name:
                existing_pattern = pattern
                break

        if existing_pattern:
            # 既存パターンの頻度を更新
            existing_pattern.frequency += new_pattern.frequency
            existing_pattern.impact_score = max(
                existing_pattern.impact_score, new_pattern.impact_score
            )
            existing_pattern.affected_operations.extend(new_pattern.affected_operations)
            existing_pattern.affected_operations = list(
                set(existing_pattern.affected_operations)
            )
        else:
            # 新しいパターンを追加
            self.detected_patterns.append(new_pattern)

    def get_pattern_summary(self) -> Dict:
        """パターン検出概要を取得"""
        if not self.detected_patterns:
            return {"total_patterns": 0, "patterns": []}

        # パターンを影響度でソート
        sorted_patterns = sorted(
            self.detected_patterns, key=lambda x: x.impact_score, reverse=True
        )

        pattern_summary = []
        for pattern in sorted_patterns[:10]:  # 上位10パターン
            pattern_summary.append(
                {
                    "name": pattern.pattern_name,
                    "frequency": pattern.frequency,
                    "impact_score": pattern.impact_score,
                    "optimization": pattern.suggested_optimization,
                    "affected_operations": pattern.affected_operations,
                }
            )

        return {
            "total_patterns": len(self.detected_patterns),
            "patterns": pattern_summary,
        }

    def generate_optimization_recommendations(self) -> List[str]:
        """最適化推奨事項を生成"""
        if not self.detected_patterns:
            return ["現在、最適化が必要なパターンは検出されていません。"]

        recommendations = []

        # 高影響度パターンから推奨事項を生成
        high_impact_patterns = [
            p for p in self.detected_patterns if p.impact_score > 0.5
        ]

        if high_impact_patterns:
            recommendations.append("🚨 高優先度の最適化項目:")
            for pattern in sorted(
                high_impact_patterns, key=lambda x: x.impact_score, reverse=True
            ):
                recommendations.append(
                    f"  - {pattern.suggested_optimization} "
                    f"(影響度: {pattern.impact_score:.2f}, 頻度: {pattern.frequency})"
                )

        # 頻出パターンから推奨事項を生成
        frequent_patterns = [p for p in self.detected_patterns if p.frequency > 5]

        if frequent_patterns:
            recommendations.append("\n🔄 頻出パターンの最適化:")
            for pattern in sorted(
                frequent_patterns, key=lambda x: x.frequency, reverse=True
            ):
                recommendations.append(
                    f"  - {pattern.suggested_optimization} "
                    f"(頻度: {pattern.frequency}回)"
                )

        if not recommendations:
            recommendations.append("定期的な最適化レビューを継続してください。")

        return recommendations
