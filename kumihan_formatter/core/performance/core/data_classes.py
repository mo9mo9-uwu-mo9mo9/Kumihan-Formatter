"""パフォーマンス監視システムのメトリクスデータクラス統合

Single Responsibility Principle適用: データクラス統合インターフェース
Issue #476 Phase2対応 - パフォーマンスモジュール統合（後方互換性維持）

このファイルは後方互換性を維持するため、分割されたデータクラスを
再エクスポートします。
"""

# Benchmark-related classes
from .benchmark_data import (
    BenchmarkConfig,
    BenchmarkResult,
    CacheStats,
    ProfileData,
)

# Memory-related classes
from .memory_data import (
    MemoryLeak,
    MemorySnapshot,
)

# Optimization-related classes
from .optimization_data import (
    OptimizationMetrics,
    OptimizationReport,
)

# Re-export all classes for backward compatibility
__all__ = [
    "BenchmarkResult",
    "MemorySnapshot",
    "MemoryLeak",
    "OptimizationMetrics",
    "OptimizationReport",
    "BenchmarkConfig",
    "CacheStats",
    "ProfileData",
]
