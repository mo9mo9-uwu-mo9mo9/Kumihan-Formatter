"""
トークン効率分析・パターン検出システム
Issue #813対応 - performance_metrics.py分割版（分析系）

責任範囲:
- トークン効率分析
- 非効率パターン検出
- アラート・通知システム
- パフォーマンス分析レポート
"""

import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..logger import get_logger


@dataclass
class TokenEfficiencyMetrics:
    """トークン効率メトリクス"""

    total_tokens: int = 0
    effective_tokens: int = 0
    efficiency_rate: float = 0.0
    waste_tokens: int = 0
    optimization_potential: float = 0.0


@dataclass
class InefficiencyPattern:
    """非効率パターン"""

    pattern_type: str
    description: str
    occurrences: int = 0
    waste_estimate: float = 0.0
    severity: str = "medium"  # low, medium, high, critical


class TokenEfficiencyAnalyzer:
    """
    トークン効率分析システム

    機能:
    - トークン使用効率の詳細分析
    - 非効率パターンの自動検出
    - 最適化提案の生成
    - 効率改善の定量的測定
    """

    def __init__(self, analysis_window: int = 1000):
        self.logger = get_logger(__name__)
        self.analysis_window = analysis_window

        # 分析データ
        self.token_history: List[int] = []
        self.pattern_history: List[Dict[str, Any]] = []

        # 非効率パターン定義
        self.inefficiency_patterns = self._initialize_patterns()

        self.logger.info(
            f"TokenEfficiencyAnalyzer initialized with window size: {analysis_window}"
        )

    def _initialize_patterns(self) -> Dict[str, InefficiencyPattern]:
        """非効率パターンを初期化"""
        patterns = {
            "repetitive_operations": InefficiencyPattern(
                pattern_type="repetitive_operations",
                description="同一操作の反復実行",
                severity="high",
            ),
            "inefficient_regex": InefficiencyPattern(
                pattern_type="inefficient_regex",
                description="非効率な正規表現パターン",
                severity="medium",
            ),
            "memory_leaks": InefficiencyPattern(
                pattern_type="memory_leaks",
                description="メモリリーク傾向",
                severity="critical",
            ),
            "excessive_io": InefficiencyPattern(
                pattern_type="excessive_io",
                description="過剰なI/O操作",
                severity="high",
            ),
            "redundant_processing": InefficiencyPattern(
                pattern_type="redundant_processing",
                description="冗長な処理ロジック",
                severity="medium",
            ),
        }

        return patterns

    def analyze_token_efficiency(
        self, execution_data: Dict[str, Any]
    ) -> TokenEfficiencyMetrics:
        """
        実行データからトークン効率を分析

        Args:
            execution_data: 実行時データ（処理時間、メモリ使用量等）

        Returns:
            TokenEfficiencyMetrics: 効率メトリクス
        """
        # トークン数の推定（処理時間とメモリ使用量から）
        processing_time = execution_data.get("processing_time", 0)
        memory_usage = execution_data.get("memory_usage_mb", 0)
        operations_count = execution_data.get("operations_count", 0)

        # 効率性計算の簡易実装
        estimated_tokens = int(processing_time * 1000 + memory_usage * 10)

        # 基準効率と比較
        baseline_efficiency = 0.75  # 75%を基準とする
        actual_efficiency = min(1.0, operations_count / max(1, estimated_tokens))

        effective_tokens = int(estimated_tokens * actual_efficiency)
        waste_tokens = estimated_tokens - effective_tokens

        optimization_potential = max(0, baseline_efficiency - actual_efficiency) * 100

        metrics = TokenEfficiencyMetrics(
            total_tokens=estimated_tokens,
            effective_tokens=effective_tokens,
            efficiency_rate=actual_efficiency,
            waste_tokens=waste_tokens,
            optimization_potential=optimization_potential,
        )

        # 履歴に追加
        self.token_history.append(estimated_tokens)
        if len(self.token_history) > self.analysis_window:
            self.token_history.pop(0)

        return metrics

    def detect_inefficiency_patterns(
        self, execution_logs: List[str]
    ) -> List[InefficiencyPattern]:
        """
        実行ログから非効率パターンを検出

        Args:
            execution_logs: 実行ログリスト

        Returns:
            List[InefficiencyPattern]: 検出されたパターン
        """
        detected_patterns = []

        # ログを結合して分析
        log_text = "\n".join(execution_logs)

        # 反復操作の検出
        repetitive_count = self._detect_repetitive_operations(log_text)
        if repetitive_count > 10:
            pattern = self.inefficiency_patterns["repetitive_operations"].copy()
            pattern.occurrences = repetitive_count
            pattern.waste_estimate = repetitive_count * 0.1
            detected_patterns.append(pattern)

        # 非効率な正規表現の検出
        regex_issues = self._detect_inefficient_regex(log_text)
        if regex_issues > 5:
            pattern = self.inefficiency_patterns["inefficient_regex"].copy()
            pattern.occurrences = regex_issues
            pattern.waste_estimate = regex_issues * 0.05
            detected_patterns.append(pattern)

        # メモリリークの検出
        memory_trend = self._analyze_memory_trend()
        if memory_trend > 0.2:  # 20%以上の増加傾向
            pattern = self.inefficiency_patterns["memory_leaks"].copy()
            pattern.occurrences = 1
            pattern.waste_estimate = memory_trend * 100
            detected_patterns.append(pattern)

        return detected_patterns

    def _detect_repetitive_operations(self, log_text: str) -> int:
        """反復操作を検出"""
        # 同じエラーメッセージや警告の繰り返しを検出
        lines = log_text.split("\n")
        line_counts = Counter(line.strip() for line in lines if line.strip())

        repetitive_count = 0
        for line, count in line_counts.items():
            if count > 5 and ("error" in line.lower() or "warning" in line.lower()):
                repetitive_count += count - 1  # 初回以外をカウント

        return repetitive_count

    def _detect_inefficient_regex(self, log_text: str) -> int:
        """非効率な正規表現パターンを検出"""
        # 正規表現のコンパイル失敗や時間のかかるパターンを検出
        regex_error_patterns = [
            r"regex.*error",
            r"pattern.*timeout",
            r"compilation.*failed",
        ]

        issues = 0
        for pattern in regex_error_patterns:
            matches = re.findall(pattern, log_text, re.IGNORECASE)
            issues += len(matches)

        return issues

    def _analyze_memory_trend(self) -> float:
        """メモリ使用量の増加傾向を分析"""
        if len(self.token_history) < 10:
            return 0.0

        # 簡易的な線形回帰で傾向を計算
        recent_data = self.token_history[-10:]
        n = len(recent_data)

        x_sum = sum(range(n))
        y_sum = sum(recent_data)
        xy_sum = sum(i * recent_data[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        if n * x2_sum - x_sum * x_sum == 0:
            return 0.0

        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)

        # 正規化（最大値に対する増加率）
        if max(recent_data) > 0:
            return slope / max(recent_data)
        return 0.0

    def generate_optimization_recommendations(
        self, patterns: List[InefficiencyPattern]
    ) -> List[str]:
        """非効率パターンに基づく最適化推奨事項を生成"""
        recommendations = []

        for pattern in patterns:
            if pattern.pattern_type == "repetitive_operations":
                recommendations.append(
                    f"🔄 反復操作の最適化: {pattern.occurrences}回の重複操作を統合することで"
                    f"約{pattern.waste_estimate:.1f}%の効率向上が期待できます"
                )

            elif pattern.pattern_type == "inefficient_regex":
                recommendations.append(
                    f"🔍 正規表現の最適化: {pattern.occurrences}個の非効率パターンを"
                    f"改善することで処理速度が向上します"
                )

            elif pattern.pattern_type == "memory_leaks":
                recommendations.append(
                    "💾 メモリ管理の改善: メモリ使用量の増加傾向を改善することで"
                    "長期実行の安定性が向上します"
                )

        if not recommendations:
            recommendations.append(
                "✅ 現在のところ、大きな最適化の余地は検出されていません"
            )

        return recommendations

    def get_efficiency_trend_report(self) -> str:
        """効率性の傾向レポートを生成"""
        if len(self.token_history) < 5:
            return "効率性分析には十分なデータがありません"

        recent_avg = sum(self.token_history[-5:]) / 5
        older_avg = (
            sum(self.token_history[-10:-5]) / 5
            if len(self.token_history) >= 10
            else recent_avg
        )

        if older_avg > 0:
            trend_percent = (recent_avg - older_avg) / older_avg * 100
        else:
            trend_percent = 0

        if trend_percent > 5:
            trend_text = f"効率性が{trend_percent:.1f}%向上しています 📈"
        elif trend_percent < -5:
            trend_text = f"効率性が{abs(trend_percent):.1f}%低下しています 📉"
        else:
            trend_text = "効率性は安定しています ➡️"

        return f"トークン効率分析: {trend_text}"


class PatternDetector:
    """パターン検出・分析エンジン"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.detection_rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict[str, Any]:
        """検出ルールを初期化"""
        return {
            "performance_degradation": {
                "threshold": 0.2,
                "window": 10,
                "severity": "high",
            },
            "error_spike": {"threshold": 5, "window": 5, "severity": "critical"},
        }

    def analyze_patterns(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """データからパターンを分析"""
        patterns = []

        # パフォーマンス劣化パターン
        if self._detect_performance_degradation(data):
            patterns.append(
                {
                    "type": "performance_degradation",
                    "severity": "high",
                    "description": "処理性能の継続的な劣化を検出",
                }
            )

        return patterns

    def _detect_performance_degradation(self, data: List[Dict[str, Any]]) -> bool:
        """パフォーマンス劣化を検出"""
        if len(data) < 10:
            return False

        recent_times = [d.get("processing_time", 0) for d in data[-5:]]
        older_times = [d.get("processing_time", 0) for d in data[-10:-5]]

        if older_times and recent_times:
            recent_avg = sum(recent_times) / len(recent_times)
            older_avg = sum(older_times) / len(older_times)

            if older_avg > 0:
                degradation = (recent_avg - older_avg) / older_avg
                return degradation > 0.2  # 20%以上の劣化

        return False


class AlertSystem:
    """アラート・通知システム"""

    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.logger = get_logger(__name__)

        # デフォルトのアラート閾値
        self.thresholds = alert_thresholds or {
            "memory_usage": 80.0,  # %
            "processing_time": 10.0,  # seconds
            "error_rate": 5.0,  # %
            "efficiency_drop": 20.0,  # %
        }

        self.alert_history: List[Dict[str, Any]] = []

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """メトリクスをチェックしてアラートを生成"""
        alerts = []

        # メモリ使用量アラート
        memory_percent = metrics.get("memory_percent", 0)
        if memory_percent > self.thresholds["memory_usage"]:
            alerts.append(
                {
                    "type": "high_memory",
                    "severity": "warning",
                    "message": f"高メモリ使用量: {memory_percent:.1f}%",
                    "value": memory_percent,
                    "threshold": self.thresholds["memory_usage"],
                }
            )

        # 処理時間アラート
        processing_time = metrics.get("processing_time", 0)
        if processing_time > self.thresholds["processing_time"]:
            alerts.append(
                {
                    "type": "slow_processing",
                    "severity": "warning",
                    "message": f"処理時間が長い: {processing_time:.2f}秒",
                    "value": processing_time,
                    "threshold": self.thresholds["processing_time"],
                }
            )

        # アラート履歴に追加
        for alert in alerts:
            alert["timestamp"] = time.time()
            self.alert_history.append(alert)

        return alerts

    def get_alert_summary(self) -> str:
        """アラートサマリーを生成"""
        if not self.alert_history:
            return "アラートは発生していません"

        recent_alerts = self.alert_history[-10:]  # 直近10件
        alert_counts = Counter(alert["type"] for alert in recent_alerts)

        summary_lines = ["🚨 最近のアラート:"]
        for alert_type, count in alert_counts.items():
            summary_lines.append(f"  {alert_type}: {count}件")

        return "\n".join(summary_lines)
