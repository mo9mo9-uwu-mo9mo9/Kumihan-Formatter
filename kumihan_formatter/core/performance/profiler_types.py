"""プロファイラー用データクラス定義

このモジュールは、プロファイラーシステムで使用される
データクラスと定数を定義します。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FunctionProfile:
    """関数プロファイル情報"""

    name: str
    module: str
    calls: int = 0
    total_time: float = 0.0
    cumulative_time: float = 0.0
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float("inf")
    memory_usage: int | None = None
    memory_delta: int | None = None


@dataclass
class ProfilingSession:
    """プロファイリングセッション"""

    name: str
    start_time: float
    end_time: float | None = None
    function_profiles: dict[str, FunctionProfile] = field(default_factory=dict)
    total_calls: int = 0
    total_time: float = 0.0
    memory_snapshots: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """セッション持続時間"""
        if self.end_time:
            return self.end_time - self.start_time
        import time

        return time.perf_counter() - self.start_time


# プロファイラー用定数
PROFILER_CONSTANTS = {
    "MEMORY_WARNING_THRESHOLD_MB": 500,
    "SLOW_FUNCTION_THRESHOLD_SECONDS": 0.1,
    "HIGH_CALL_COUNT_THRESHOLD": 1000,
    "MAX_PERFORMANCE_METRICS": 100,
    "BOTTLENECK_THRESHOLD_PERCENT": 5.0,
}
