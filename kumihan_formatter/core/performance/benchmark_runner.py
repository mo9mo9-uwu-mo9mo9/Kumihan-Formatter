"""
ベンチマーク実行器 - 個別ベンチマーク実行機能

各種ベンチマークの実行とモック関数を管理
Issue #476対応 - ファイルサイズ制限遵守
"""

import statistics
import time
from pathlib import Path
from typing import Any, Callable

from ..caching.file_cache import FileCache
from ..caching.parse_cache import ParseCache
from ..caching.render_cache import RenderCache
from ..utilities.logger import get_logger
from .benchmark_types import BenchmarkResult, BenchmarkConfig
from .memory_monitor import MemoryMonitor
from .profiler import AdvancedProfiler


class BenchmarkRunner:
    """個別ベンチマーク実行機能
    
    機能:
    - ファイル読み込みベンチマーク
    - パースベンチマーク
    - レンダリングベンチマーク
    - フルパイプラインベンチマーク
    - キャッシュパフォーマンステスト
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
        """ベンチマーク実行器を初期化"""
        self.logger = get_logger(__name__)
        self.config = config
        self.file_cache = file_cache
        self.parse_cache = parse_cache
        self.render_cache = render_cache
        self.memory_monitor = memory_monitor
        self.profiler = profiler

    def run_file_benchmarks(self) -> list[BenchmarkResult]:
        """ファイル読み込みベンチマーク"""
        results = []
        
        # 小ファイル読み込み
        result = self.benchmark_file_reading(file_size="small")
        results.append(result)
        print(f"  Small files: {result.avg_time:.3f}s avg")

        # 大ファイル読み込み
        result = self.benchmark_file_reading(file_size="large")
        results.append(result)
        print(f"  Large files: {result.avg_time:.3f}s avg")
        
        return results

    def run_parse_benchmarks(self) -> list[BenchmarkResult]:
        """パースベンチマーク"""
        results = []
        
        # 基本パース
        result = self.benchmark_parsing(complexity="basic")
        results.append(result)
        print(f"  Basic parsing: {result.avg_time:.3f}s avg")

        # 複雑パース
        result = self.benchmark_parsing(complexity="complex")
        results.append(result)
        print(f"  Complex parsing: {result.avg_time:.3f}s avg")
        
        return results

    def run_render_benchmarks(self) -> list[BenchmarkResult]:
        """レンダリングベンチマーク"""
        results = []
        
        # 基本レンダリング
        result = self.benchmark_rendering(template="basic")
        results.append(result)
        print(f"  Basic rendering: {result.avg_time:.3f}s avg")

        # 複雑レンダリング
        result = self.benchmark_rendering(template="complex")
        results.append(result)
        print(f"  Complex rendering: {result.avg_time:.3f}s avg")
        
        return results

    def run_e2e_benchmarks(self) -> list[BenchmarkResult]:
        """エンドツーエンドベンチマーク"""
        result = self.benchmark_full_pipeline()
        print(f"  Full pipeline: {result.avg_time:.3f}s avg")
        return [result]

    def run_cache_benchmarks(self) -> list[BenchmarkResult]:
        """キャッシュパフォーマンステスト"""
        if not self.config.cache_enabled:
            print("  Cache disabled, skipping cache benchmarks")
            return []

        # キャッシュヒット率テスト
        result = self.benchmark_cache_performance()
        print(f"  Cache performance: {result.avg_time:.3f}s avg")
        return [result]

    def benchmark_file_reading(self, file_size: str = "medium") -> BenchmarkResult:
        """ファイル読み込みベンチマーク"""
        name = f"file_reading_{file_size}"

        # テストファイルを生成
        test_content = self._generate_test_content(file_size)
        test_file = Path(f"/tmp/benchmark_{file_size}.txt")
        test_file.write_text(test_content, encoding="utf-8")

        def benchmark_func() -> str:
            if self.file_cache:
                return self.file_cache.get_file_content(test_file)
            else:
                return test_file.read_text(encoding="utf-8")

        return self._run_benchmark(name, benchmark_func)

    def benchmark_parsing(self, complexity: str = "basic") -> BenchmarkResult:
        """パースベンチマーク"""
        name = f"parsing_{complexity}"

        # テストコンテンツを生成
        test_content = self._generate_parse_test_content(complexity)

        def benchmark_func() -> Any:
            if self.parse_cache:
                return self.parse_cache.get_parse_or_compute(
                    test_content, self._mock_parse_function
                )
            else:
                return self._mock_parse_function(test_content)

        return self._run_benchmark(name, benchmark_func)

    def benchmark_rendering(self, template: str = "basic") -> BenchmarkResult:
        """レンダリングベンチマーク"""
        name = f"rendering_{template}"

        # テストデータを生成
        test_data = self._generate_render_test_data(template)
        content_hash = "test_hash"

        def benchmark_func() -> str:
            if self.render_cache:
                return self.render_cache.get_render_or_compute(
                    content_hash, template, self._mock_render_function, data=test_data
                )
            else:
                return self._mock_render_function(data=test_data)

        return self._run_benchmark(name, benchmark_func)

    def benchmark_full_pipeline(self) -> BenchmarkResult:
        """フルパイプラインベンチマーク"""
        name = "full_pipeline"

        # テストファイルを準備
        test_content = self._generate_test_content("medium")
        test_file = Path("/tmp/benchmark_pipeline.txt")
        test_file.write_text(test_content, encoding="utf-8")

        def benchmark_func() -> str:
            # 1. ファイル読み込み
            if self.file_cache:
                content = self.file_cache.get_file_content(test_file)
            else:
                content = test_file.read_text(encoding="utf-8")

            # 2. パース
            if self.parse_cache:
                ast_nodes = self.parse_cache.get_parse_or_compute(
                    content, self._mock_parse_function
                )
            else:
                ast_nodes = self._mock_parse_function(content)

            # 3. レンダリング
            content_hash = "pipeline_hash"
            if self.render_cache:
                html = self.render_cache.get_render_or_compute(
                    content_hash,
                    "basic",
                    self._mock_render_function,
                    ast_nodes=ast_nodes,
                )
            else:
                html = self._mock_render_function(ast_nodes=ast_nodes)

            return html

        return self._run_benchmark(name, benchmark_func)

    def benchmark_cache_performance(self) -> BenchmarkResult:
        """キャッシュパフォーマンステスト"""
        name = "cache_performance"

        # キャッシュを事前にウォームアップ
        test_content = self._generate_test_content("medium")

        if self.file_cache:
            test_file = Path("/tmp/benchmark_cache.txt")
            test_file.write_text(test_content, encoding="utf-8")
            # 一度読み込んでキャッシュに保存
            self.file_cache.get_file_content(test_file)

        if self.parse_cache:
            # 一度パースしてキャッシュに保存
            self.parse_cache.get_parse_or_compute(
                test_content, self._mock_parse_function
            )

        def benchmark_func() -> str:
            # キャッシュヒットを期待
            if self.file_cache:
                self.file_cache.get_file_content(test_file)

            if self.parse_cache:
                self.parse_cache.get_parse_or_compute(
                    test_content, self._mock_parse_function
                )

            return "cached_result"

        return self._run_benchmark(name, benchmark_func)

    def _run_benchmark(self, name: str, func: Callable[[], Any]) -> BenchmarkResult:
        """ベンチマークを実行"""
        # ウォームアップ
        self.logger.debug(f"ウォームアップ開始: {self.config.warmup_iterations}回")
        for i in range(self.config.warmup_iterations):
            func()
            self.logger.debug(
                f"ウォームアップ {i+1}/{self.config.warmup_iterations} 完了"
            )

        # メモリ監視開始
        start_memory = None
        if self.memory_monitor:
            start_memory = self.memory_monitor.take_snapshot()

        # プロファイリング開始
        session_name = f"benchmark_{name}"
        profiler_context = None
        if self.profiler:
            profiler_context = self.profiler.profile_session(session_name)
            profiler_context.__enter__()

        # 実際の測定
        self.logger.debug(f"ベンチマーク測定開始: {self.config.iterations}回")
        times = []
        for i in range(self.config.iterations):
            start_time = time.perf_counter()
            func()
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            times.append(execution_time)
            self.logger.debug(f"実行 {i+1}/{self.config.iterations}: {execution_time:.3f}s")

        # プロファイリング終了
        if profiler_context:
            profiler_context.__exit__(None, None, None)

        # メモリ監視終了
        end_memory = None
        if self.memory_monitor:
            end_memory = self.memory_monitor.take_snapshot()

        # 統計計算
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

        # メモリ使用量計算
        memory_usage = {}
        if start_memory and end_memory:
            memory_usage = {
                "start_mb": start_memory.memory_mb,
                "end_mb": end_memory.memory_mb,
                "peak_mb": max(start_memory.memory_mb, end_memory.memory_mb),
                "increase_mb": end_memory.memory_mb - start_memory.memory_mb,
            }

        # キャッシュ統計を取得
        cache_stats = self._get_cache_stats()

        # スループット計算
        throughput = self.config.iterations / total_time if total_time > 0 else None

        result = BenchmarkResult(
            name=name,
            iterations=self.config.iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            memory_usage=memory_usage,
            cache_stats=cache_stats,
            throughput=throughput,
        )

        self.logger.info(
            f"ベンチマーク完了: {name}, avg={avg_time:.3f}s, "
            f"throughput={throughput:.1f}ops/s" if throughput else ""
        )

        return result

    def _get_cache_stats(self) -> dict[str, Any]:
        """キャッシュ統計を取得"""
        stats = {}
        
        if self.file_cache:
            file_stats = self.file_cache.get_stats()
            stats["file_cache"] = file_stats
            
        if self.parse_cache:
            parse_stats = self.parse_cache.get_stats()
            stats["parse_cache"] = parse_stats
            
        if self.render_cache:
            render_stats = self.render_cache.get_stats()
            stats["render_cache"] = render_stats
            
        return stats

    def _generate_test_content(self, size: str) -> str:
        """テストコンテンツを生成"""
        base_content = "これはテストコンテンツです。"
        
        if size == "small":
            return base_content * 10  # 約240文字
        elif size == "medium":
            return base_content * 100  # 約2.4KB
        elif size == "large":
            return base_content * 1000  # 約24KB
        else:
            return base_content * 100

    def _generate_parse_test_content(self, complexity: str) -> str:
        """パーステスト用コンテンツを生成"""
        if complexity == "basic":
            return ";;装飾名;; 基本的なテキスト ;;;\n" * 10
        elif complexity == "complex":
            return (
                ";;脚注記法;; ((注釈)) とルビ ｜漢字《かんじ》 の複合テキスト ;;;\n"
                ";;サイドノート;; 複雑な記法のテスト ;;;\n"
            ) * 20
        else:
            return ";;装飾名;; 標準的なテキスト ;;;\n" * 15

    def _generate_render_test_data(self, template: str) -> dict[str, Any]:
        """レンダーテスト用データを生成"""
        if template == "basic":
            return {
                "title": "基本テンプレート",
                "content": "シンプルなコンテンツ",
                "items": list(range(10)),
            }
        elif template == "complex":
            return {
                "title": "複雑テンプレート",
                "content": "多くの要素を含むコンテンツ",
                "items": list(range(100)),
                "nested": {"data": list(range(50))},
                "metadata": {"key": "value"} * 20,
            }
        else:
            return {
                "title": "標準テンプレート",
                "content": "標準的なコンテンツ",
                "items": list(range(25)),
            }

    def _mock_parse_function(self, content: str) -> list[dict[str, Any]]:
        """モックパース関数"""
        # 簡単なパース処理をシミュレート
        lines = content.split('\n')
        return [{"type": "text", "content": line, "index": i} for i, line in enumerate(lines)]

    def _mock_render_function(self, **kwargs: Any) -> str:
        """モックレンダー関数"""
        # 簡単なレンダリング処理をシミュレート
        data = kwargs.get("data", {})
        ast_nodes = kwargs.get("ast_nodes", [])
        
        if ast_nodes:
            return "\n".join([f"<p>{node.get('content', '')}</p>" for node in ast_nodes])
        elif data:
            title = data.get("title", "No Title")
            content = data.get("content", "No Content")
            return f"<h1>{title}</h1><p>{content}</p>"
        else:
            return "<p>Mock rendered content</p>"