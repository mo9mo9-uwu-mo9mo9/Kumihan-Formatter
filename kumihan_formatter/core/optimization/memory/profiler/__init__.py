"""メモリプロファイラーパッケージ - 分割後の公開API維持"""

from __future__ import annotations

from .config import ProfilerConfig
from .core_profiler import MemoryProfiler
from .effect_reporter import OptimizationEffectReporter
from .factory import (
    get_effect_reporter,
    get_leak_detector,
    get_memory_profiler,
    get_usage_analyzer,
    test_leak_detection,
    test_memory_profiler,
    test_optimization_effect_reporting,
    test_usage_analysis,
)
from .leak_detector import MemoryLeakDetector
from .snapshot import MemoryLeakInfo, MemorySnapshot
from .usage_analyzer import MemoryUsageAnalyzer

# 元のmemory_profiler.pyと同じ公開APIを維持
__all__ = [
    # データクラス
    "MemorySnapshot",
    "MemoryLeakInfo",
    "ProfilerConfig",
    # メインクラス
    "MemoryProfiler",
    "MemoryLeakDetector",
    "MemoryUsageAnalyzer",
    "OptimizationEffectReporter",
    # Factory関数
    "get_memory_profiler",
    "get_leak_detector",
    "get_usage_analyzer",
    "get_effect_reporter",
    # テスト関数
    "test_memory_profiler",
    "test_leak_detection",
    "test_usage_analysis",
    "test_optimization_effect_reporting",
]
