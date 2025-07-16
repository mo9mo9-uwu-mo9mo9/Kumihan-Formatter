"""
ベンチマーク型定義 - データクラスと設定

ベンチマーク結果とベンチマーク設定のデータ型定義
Issue #476対応 - ファイルサイズ制限遵守
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    memory_usage: dict[str, float]
    cache_stats: dict[str, Any]
    throughput: float | None = None
    regression_score: float | None = None


@dataclass
class BenchmarkConfig:
    """ベンチマーク設定"""

    iterations: int = 5
    warmup_iterations: int = 2
    enable_profiling: bool = True
    enable_memory_monitoring: bool = True
    cache_enabled: bool = True
    baseline_file: Path | None = None


@dataclass
class RegressionAnalysis:
    """回帰分析結果"""

    benchmark_name: str
    baseline_avg_time: float
    current_avg_time: float
    performance_change_percent: float
    is_regression: bool
    severity: str  # "minor", "moderate", "severe"
    memory_change_percent: float | None = None
    cache_performance_change: dict[str, float] | None = None


@dataclass
class BenchmarkSummary:
    """ベンチマーク結果サマリー"""

    total_benchmarks: int
    total_runtime: float
    fastest_benchmark: BenchmarkResult
    slowest_benchmark: BenchmarkResult
    memory_peak: float
    cache_hit_rate: float
    regressions_detected: list[RegressionAnalysis]
    performance_score: float


# ベンチマーク設定の定数
DEFAULT_BENCHMARK_CONFIG = BenchmarkConfig(
    iterations=5,
    warmup_iterations=2,
    enable_profiling=True,
    enable_memory_monitoring=True,
    cache_enabled=True,
)

REGRESSION_CONFIG = BenchmarkConfig(
    iterations=3,
    warmup_iterations=1,
    enable_profiling=False,
    enable_memory_monitoring=True,
    cache_enabled=True,
)

# パフォーマンス閾値
PERFORMANCE_THRESHOLDS = {
    "regression_threshold_percent": 10.0,  # 10%以上の性能劣化で回帰とみなす
    "severe_regression_percent": 25.0,  # 25%以上の劣化で深刻な回帰
    "memory_increase_threshold": 20.0,  # 20%以上のメモリ増加で警告
    "cache_hit_rate_minimum": 0.8,  # キャッシュヒット率80%未満で警告
}
