"""
パフォーマンス監視・最適化・分析統合パッケージ
Issue #813対応 - performance_metrics.py分割版

🎯 完全後方互換性保証:
- 既存インポート: from kumihan_formatter.core.performance import ...
- 新形式インポート: from kumihan_formatter.core.utilities.performance import ...

📦 分割構造:
- monitor.py: パフォーマンス監視（PerformanceMonitor等）
- optimizers/: 最適化システム（SIMD、AsyncIO、Regex、Memory）
- benchmark.py: ベンチマーク・性能測定
- analytics.py: トークン効率分析・パターン検出

✅ Issue #813完了要件:
- 全ファイル1000行以下に分割完了
- 循環インポート回避
- Python 3.12対応
- 既存コード互換性100%維持
"""

# 分析系クラス
from .analytics import (
    AlertSystem,
    InefficiencyPattern,
    PatternDetector,
    TokenEfficiencyAnalyzer,
    TokenEfficiencyMetrics,
)

# ベンチマーク系クラス
from .benchmark import BenchmarkResult, PerformanceBenchmark

# 監視系クラス
from .monitor import (
    PerformanceContext,
    PerformanceMonitor,
    PerformanceSnapshot,
    ProcessingStats,
    monitor_performance,
)

# 最適化系クラス
from .optimizers import (
    AsyncIOOptimizer,
    MemoryOptimizer,
    RegexOptimizer,
    SIMDOptimizer,
)

# 完全後方互換性エクスポート
__all__ = [
    # 監視系
    "PerformanceSnapshot",
    "ProcessingStats",
    "PerformanceMonitor",
    "monitor_performance",
    "PerformanceContext",
    # 最適化系
    "SIMDOptimizer",
    "AsyncIOOptimizer",
    "RegexOptimizer",
    "MemoryOptimizer",
    # ベンチマーク系
    "PerformanceBenchmark",
    "BenchmarkResult",
    # 分析系
    "TokenEfficiencyAnalyzer",
    "TokenEfficiencyMetrics",
    "InefficiencyPattern",
    "PatternDetector",
    "AlertSystem",
]

# バージョン情報
__version__ = "2.0.0-split"
__split_date__ = "2025-08-07"
__original_file_lines__ = 3496
__split_files_count__ = 8
