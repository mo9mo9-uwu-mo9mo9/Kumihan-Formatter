"""パフォーマンス監視システムのコア機能

Single Responsibility Principle適用: 基底クラスとメトリクスの統合
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

from .base import (
    MeasurementSession,
    PerformanceComponent,
    PerformanceMetric,
    SystemInfo,
    create_measurement_session,
)
from .metrics import (
    BenchmarkConfig,
    BenchmarkResult,
    CacheStats,
    MemoryLeak,
    MemorySnapshot,
    OptimizationMetrics,
    OptimizationReport,
    ProfileData,
    calculate_improvement_percentage,
    determine_significance,
    merge_cache_stats,
)
from .persistence import (
    BaselineManager,
    DataPersistence,
    ReportExporter,
    get_global_persistence,
    initialize_persistence,
)

__all__ = [
    # Base classes
    "PerformanceComponent",
    "PerformanceMetric",
    "SystemInfo",
    "MeasurementSession",
    "create_measurement_session",
    # Metrics
    "BenchmarkResult",
    "BenchmarkConfig",
    "MemorySnapshot",
    "MemoryLeak",
    "OptimizationMetrics",
    "OptimizationReport",
    "CacheStats",
    "ProfileData",
    # Persistence
    "DataPersistence",
    "BaselineManager",
    "ReportExporter",
    "get_global_persistence",
    "initialize_persistence",
    # Utility functions
    "calculate_improvement_percentage",
    "determine_significance",
    "merge_cache_stats",
]
