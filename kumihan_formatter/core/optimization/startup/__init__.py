"""
起動時間最適化モジュール

Phase 4-4: 起動時間50%短縮を目標とした
最適化コンポーネント統合
"""

from .cache_warmer import CacheWarmer, create_default_cache_warmer
from .import_optimizer import ImportAnalyzer, benchmark_import_performance
from .lazy_loading import LazyImporter, LazyLoadManager, get_lazy_manager, lazy_import
from .startup_profiler import (
    StartupProfile,
    StartupProfiler,
    profile_application_startup,
)

__all__ = [
    # キャッシュウォーマー
    "CacheWarmer",
    "create_default_cache_warmer",
    # インポート最適化
    "ImportAnalyzer",
    "benchmark_import_performance",
    # 遅延ローディング
    "LazyImporter",
    "LazyLoadManager",
    "get_lazy_manager",
    "lazy_import",
    # 起動プロファイラー
    "StartupProfiler",
    "StartupProfile",
    "profile_application_startup",
]

__version__ = "1.0.0"
