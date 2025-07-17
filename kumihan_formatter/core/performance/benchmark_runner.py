"""
ベンチマーク実行器統合クラス - 分割された各ベンチマーク機能を統合

各種ベンチマークの統合管理と委譲機能
Issue #476対応 - ファイルサイズ制限遵守（300行制限）
"""

from typing import Any, Optional

from ..caching.file_cache import FileCache
from ..caching.parse_cache import ParseCache
from ..caching.render_cache import RenderCache
from ..utilities.logger import get_logger
from .benchmark_cache import BenchmarkCache
from .benchmark_file_operations import BenchmarkFileOperations
from .benchmark_rendering import BenchmarkRendering
from .benchmark_types import BenchmarkConfig, BenchmarkResult
from .memory_monitor import MemoryMonitor
from .profiler import AdvancedProfiler


class BenchmarkRunner:
    """ベンチマーク実行器統合クラス

    分割された各ベンチマーク機能への委譲機能:
    - ファイル操作関連 (benchmark_file_operations)
    - レンダリング関連 (benchmark_rendering)
    - キャッシュ関連 (benchmark_cache)
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        file_cache: FileCache | None = None,
        parse_cache: ParseCache | None = None,
        render_cache: RenderCache | None = None,
        memory_monitor: MemoryMonitor | None = None,
        profiler: AdvancedProfiler | None = None,
    ):
        """ベンチマーク実行器を初期化し、各専門クラスに委譲"""
        self.logger = get_logger(__name__)
        self.config = config

        # 各専門ベンチマーククラスを初期化
        self.file_operations = BenchmarkFileOperations(
            config, file_cache, parse_cache, memory_monitor, profiler
        )
        self.rendering = BenchmarkRendering(
            config, file_cache, parse_cache, render_cache, memory_monitor, profiler
        )
        self.cache = BenchmarkCache(
            config, file_cache, parse_cache, render_cache, memory_monitor, profiler
        )

    def run_file_benchmarks(self) -> list[BenchmarkResult]:
        """ファイル読み込みベンチマーク（委譲）"""
        return self.file_operations.run_file_benchmarks()

    def run_parse_benchmarks(self) -> list[BenchmarkResult]:
        """パースベンチマーク（委譲）"""
        return self.file_operations.run_parse_benchmarks()

    def run_render_benchmarks(self) -> list[BenchmarkResult]:
        """レンダリングベンチマーク（委譲）"""
        return self.rendering.run_render_benchmarks()

    def run_e2e_benchmarks(self) -> list[BenchmarkResult]:
        """エンドツーエンドベンチマーク（委譲）"""
        return self.rendering.run_e2e_benchmarks()

    def run_cache_benchmarks(self) -> list[BenchmarkResult]:
        """キャッシュパフォーマンステスト（委譲）"""
        return self.cache.run_cache_benchmarks()

    def benchmark_file_reading(self, file_size: str = "medium") -> BenchmarkResult:
        """ファイル読み込みベンチマーク（委譲）"""
        return self.file_operations.benchmark_file_reading(file_size)

    def benchmark_parsing(self, complexity: str = "basic") -> BenchmarkResult:
        """パースベンチマーク（委譲）"""
        return self.file_operations.benchmark_parsing(complexity)

    def benchmark_rendering(self, template: str = "basic") -> BenchmarkResult:
        """レンダリングベンチマーク（委譲）"""
        return self.rendering.benchmark_rendering(template)

    def benchmark_full_pipeline(self) -> BenchmarkResult:
        """フルパイプラインベンチマーク（委譲）"""
        return self.rendering.benchmark_full_pipeline()

    def benchmark_cache_performance(self) -> BenchmarkResult:
        """キャッシュパフォーマンステスト（委譲）"""
        return self.cache.benchmark_cache_performance()

    # 下位互換性のためのメソッド
    # 既存のコードが直接これらのメソッドを呼び出す可能性があるため残しておく

    def _get_cache_stats(self) -> dict[str, Any]:
        """キャッシュ統計を取得（下位互換）"""
        return self.cache._get_cache_stats()

    def _generate_test_content(self, size: str) -> str:
        """テストコンテンツを生成（下位互換）"""
        return self.file_operations._generate_test_content(size)

    def _generate_parse_test_content(self, complexity: str) -> str:
        """パーステスト用コンテンツを生成（下位互換）"""
        return self.file_operations._generate_parse_test_content(complexity)

    def _generate_render_test_data(self, template: str) -> dict[str, Any]:
        """レンダーテスト用データを生成（下位互換）"""
        return self.rendering._generate_render_test_data(template)

    def _mock_parse_function(self, content: str) -> Any:
        """モックパース関数（下位互換）"""
        return self.file_operations._mock_parse_function(content)

    def _mock_render_function(self, **kwargs: Any) -> str:
        """モックレンダー関数（下位互換）"""
        return self.rendering._mock_render_function(**kwargs)
