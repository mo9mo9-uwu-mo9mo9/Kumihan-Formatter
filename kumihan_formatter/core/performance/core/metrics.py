"""パフォーマンス監視システムのメトリクス統合インターフェース

Single Responsibility Principle適用: 既存APIとの後方互換性維持
Issue #476 Phase2対応 - パフォーマンスモジュール統合（300行制限対応）

このファイルは後方互換性を維持するため、分割されたモジュールから
すべてのメトリクス関連機能をre-exportします。
"""

# Data classes
from .data_classes import (
    BenchmarkConfig,
    BenchmarkResult,
    CacheStats,
    MemoryLeak,
    MemorySnapshot,
    OptimizationMetrics,
    OptimizationReport,
    ProfileData,
)

# Utility functions
from .metric_utils import (
    calculate_improvement_percentage,
    determine_significance,
    merge_cache_stats,
)

# Ensure all original exports are available
__all__ = [
    # Data classes
    "BenchmarkResult",
    "MemorySnapshot",
    "MemoryLeak",
    "OptimizationMetrics",
    "OptimizationReport",
    "BenchmarkConfig",
    "CacheStats",
    "ProfileData",
    # Utility functions
    "merge_cache_stats",
    "calculate_improvement_percentage",
    "determine_significance",
]
