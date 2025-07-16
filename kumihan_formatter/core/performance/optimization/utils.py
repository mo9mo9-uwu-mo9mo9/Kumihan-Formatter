"""
最適化分析ユーティリティ - Issue #402対応

最適化分析で使用するヘルパー関数とユーティリティ。
"""

import platform
from datetime import datetime
from typing import Any

import psutil

from .models import OptimizationMetrics


def calculate_significance(
    before_value: float, after_value: float, improvement_percent: float
) -> str:
    """改善の統計的有意性を計算

    Args:
        before_value: 最適化前の値
        after_value: 最適化後の値
        improvement_percent: 改善率（%）

    Returns:
        有意性レベル: "critical", "high", "medium", "low"
    """
    abs_improvement = abs(improvement_percent)

    if abs_improvement >= 50:
        return "critical"
    elif abs_improvement >= 20:
        return "high"
    elif abs_improvement >= 5:
        return "medium"
    else:
        return "low"


def calculate_total_improvement_score(metrics: list[OptimizationMetrics]) -> float:
    """総合改善スコアを計算

    Args:
        metrics: 最適化メトリクスのリスト

    Returns:
        総合改善スコア
    """
    if not metrics:
        return 0.0

    # 重み付きスコア計算
    total_score = 0.0
    weight_map = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5}

    for metric in metrics:
        weight = weight_map.get(metric.significance, 0.5)
        score = metric.improvement_percent * weight
        total_score += score

    return total_score / len(metrics) if metrics else 0.0


def capture_system_info() -> dict[str, Any]:
    """システム情報を収集

    Returns:
        システム情報の辞書
    """
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": psutil.virtual_memory().total / 1024**3,
        "timestamp": datetime.now().isoformat(),
    }


def create_performance_summary(metrics: list[OptimizationMetrics]) -> dict[str, Any]:
    """パフォーマンスサマリーを作成

    Args:
        metrics: 最適化メトリクスのリスト

    Returns:
        パフォーマンスサマリーの辞書
    """
    if not metrics:
        return {}

    improvements = [m for m in metrics if m.is_improvement]
    regressions = [m for m in metrics if m.is_regression]

    return {
        "total_metrics": len(metrics),
        "improvements_count": len(improvements),
        "regressions_count": len(regressions),
        "avg_improvement_percent": (
            sum(m.improvement_percent for m in improvements) / len(improvements)
            if improvements
            else 0
        ),
        "max_improvement_percent": (
            max(m.improvement_percent for m in improvements) if improvements else 0
        ),
        "significant_improvements": len(
            [m for m in metrics if m.is_significant and m.is_improvement]
        ),
    }


def generate_recommendations(metrics: list[OptimizationMetrics]) -> list[str]:
    """推奨事項を生成

    Args:
        metrics: 最適化メトリクスのリスト

    Returns:
        推奨事項のリスト
    """
    recommendations = []

    # 性能改善の推奨
    performance_metrics = [m for m in metrics if m.category == "performance"]
    significant_improvements = [
        m for m in performance_metrics if m.is_significant and m.is_improvement
    ]

    if significant_improvements:
        recommendations.append(
            f"{len(significant_improvements)}個の重要な性能改善が確認されました。この最適化を采用することを推奨します。"
        )

    # 回帰の警告
    regressions = [m for m in metrics if m.is_regression]
    if regressions:
        recommendations.append(
            f"{len(regressions)}個のパフォーマンス回帰が検出されました。最適化の見直しを検討してください。"
        )

    return recommendations


def detect_regressions(metrics: list[OptimizationMetrics]) -> list[str]:
    """パフォーマンス回帰を検出

    Args:
        metrics: 最適化メトリクスのリスト

    Returns:
        回帰警告のリスト
    """
    warnings = []

    for metric in metrics:
        if metric.is_regression:
            warnings.append(
                f"{metric.name}: {abs(metric.improvement_percent):.1f}%のパフォーマンス低下"
            )

    return warnings
