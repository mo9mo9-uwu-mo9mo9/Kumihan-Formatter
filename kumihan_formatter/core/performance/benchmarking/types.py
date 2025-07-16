"""
ベンチマークデータ型定義 - Issue #402対応

ベンチマーク結果や設定のデータクラス。
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
