"""
benchmark_analyzer.py分割のためのテスト

TDD: 分割後の新しいモジュール構造のテスト
Issue #492 Phase 5A - benchmark_analyzer.py分割
"""

from unittest.mock import Mock

import pytest


class TestBenchmarkAnalyzerCore:
    """ベンチマーク分析器コア機能のテスト"""

    def test_benchmark_analyzer_core_import(self):
        """GREEN: ベンチマーク分析器コアモジュールインポートテスト"""
        from kumihan_formatter.core.performance.benchmark_analyzer_core import (
            BenchmarkAnalyzerCore,
        )

        assert BenchmarkAnalyzerCore is not None

    def test_benchmark_analyzer_core_initialization(self):
        """GREEN: ベンチマーク分析器コア初期化テスト"""
        from kumihan_formatter.core.performance.benchmark_analyzer_core import (
            BenchmarkAnalyzerCore,
        )

        analyzer = BenchmarkAnalyzerCore()
        assert analyzer is not None

    def test_analyze_results_method(self):
        """GREEN: 結果分析メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_analyzer_core import (
            BenchmarkAnalyzerCore,
        )

        analyzer = BenchmarkAnalyzerCore()
        results = analyzer.analyze_results([])
        assert isinstance(results, dict)


class TestBenchmarkRegressionAnalyzer:
    """ベンチマーク回帰分析のテスト"""

    def test_regression_analyzer_import(self):
        """GREEN: 回帰分析モジュールインポートテスト"""
        from kumihan_formatter.core.performance.benchmark_regression_analyzer import (
            BenchmarkRegressionAnalyzer,
        )

        assert BenchmarkRegressionAnalyzer is not None

    def test_regression_analyzer_initialization(self):
        """GREEN: 回帰分析器初期化テスト"""
        from kumihan_formatter.core.performance.benchmark_regression_analyzer import (
            BenchmarkRegressionAnalyzer,
        )

        analyzer = BenchmarkRegressionAnalyzer()
        assert analyzer is not None

    def test_analyze_regression_method(self):
        """GREEN: 回帰分析メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_regression_analyzer import (
            BenchmarkRegressionAnalyzer,
        )

        analyzer = BenchmarkRegressionAnalyzer()
        result = analyzer.analyze_regression({}, {})
        assert isinstance(result, dict)

    def test_analyze_single_regression_method(self):
        """GREEN: 単一回帰分析メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_regression_analyzer import (
            BenchmarkRegressionAnalyzer,
        )
        from kumihan_formatter.core.performance.benchmark_types import BenchmarkResult

        analyzer = BenchmarkRegressionAnalyzer()
        # BenchmarkResultオブジェクトを使用
        current = BenchmarkResult(
            name="test_benchmark",
            iterations=5,
            total_time=5.0,
            avg_time=1.0,
            min_time=0.8,
            max_time=1.2,
            std_dev=0.1,
            memory_usage={"peak": 100},
            cache_stats={"hits": 10, "misses": 1},
        )
        baseline = BenchmarkResult(
            name="test_benchmark",
            iterations=5,
            total_time=6.0,
            avg_time=1.2,
            min_time=1.0,
            max_time=1.4,
            std_dev=0.1,
            memory_usage={"peak": 120},
            cache_stats={"hits": 8, "misses": 3},
        )
        result = analyzer.analyze_single_regression(current, baseline)
        from kumihan_formatter.core.performance.benchmark_types import (
            RegressionAnalysis,
        )

        assert isinstance(result, RegressionAnalysis)


class TestBenchmarkStatistics:
    """ベンチマーク統計計算のテスト"""

    def test_statistics_module_import(self):
        """GREEN: 統計モジュールインポートテスト"""
        from kumihan_formatter.core.performance.benchmark_statistics import (
            BenchmarkStatistics,
        )

        assert BenchmarkStatistics is not None

    def test_statistics_initialization(self):
        """GREEN: 統計計算器初期化テスト"""
        from kumihan_formatter.core.performance.benchmark_statistics import (
            BenchmarkStatistics,
        )

        stats = BenchmarkStatistics()
        assert stats is not None

    def test_calculate_basic_statistics_method(self):
        """GREEN: 基本統計計算メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_statistics import (
            BenchmarkStatistics,
        )

        stats = BenchmarkStatistics()
        result = stats.calculate_basic_statistics([])
        assert isinstance(result, dict)

    def test_calculate_performance_score_method(self):
        """GREEN: パフォーマンススコア計算メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_statistics import (
            BenchmarkStatistics,
        )

        stats = BenchmarkStatistics()
        score = stats.calculate_performance_score([])
        assert isinstance(score, (int, float))

    def test_analyze_memory_usage_method(self):
        """GREEN: メモリ使用量分析メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_statistics import (
            BenchmarkStatistics,
        )

        stats = BenchmarkStatistics()
        analysis = stats.analyze_memory_usage([])
        assert isinstance(analysis, dict)

    def test_analyze_cache_performance_method(self):
        """GREEN: キャッシュパフォーマンス分析メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_statistics import (
            BenchmarkStatistics,
        )

        stats = BenchmarkStatistics()
        analysis = stats.analyze_cache_performance([])
        assert isinstance(analysis, dict)


class TestBenchmarkFormatters:
    """ベンチマークフォーマッターのテスト"""

    def test_formatters_module_import(self):
        """GREEN: フォーマッターモジュールインポートテスト"""
        from kumihan_formatter.core.performance.benchmark_formatters import (
            BenchmarkFormatters,
        )

        assert BenchmarkFormatters is not None

    def test_formatters_initialization(self):
        """GREEN: フォーマッター初期化テスト"""
        from kumihan_formatter.core.performance.benchmark_formatters import (
            BenchmarkFormatters,
        )

        formatters = BenchmarkFormatters()
        assert formatters is not None

    def test_generate_benchmark_summary_method(self):
        """GREEN: ベンチマークサマリー生成メソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_formatters import (
            BenchmarkFormatters,
        )

        formatters = BenchmarkFormatters()
        # 空リストでエラーが発生することを確認
        with pytest.raises(ValueError, match="No results to summarize"):
            formatters.generate_benchmark_summary([])

    def test_format_result_summary_method(self):
        """GREEN: 結果サマリーフォーマットメソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_formatters import (
            BenchmarkFormatters,
        )
        from kumihan_formatter.core.performance.benchmark_types import BenchmarkResult

        formatters = BenchmarkFormatters()
        # BenchmarkResultオブジェクトを使用
        result = BenchmarkResult(
            name="test_benchmark",
            iterations=5,
            total_time=5.0,
            avg_time=1.0,
            min_time=0.8,
            max_time=1.2,
            std_dev=0.1,
            memory_usage={"peak": 100},
            cache_stats={"hits": 10, "misses": 1},
        )
        formatted = formatters.format_result_summary(result)
        assert isinstance(formatted, dict)
        assert "name" in formatted
        assert "avg_time" in formatted

    def test_format_regression_analysis_method(self):
        """GREEN: 回帰分析フォーマットメソッドテスト"""
        from kumihan_formatter.core.performance.benchmark_formatters import (
            BenchmarkFormatters,
        )
        from kumihan_formatter.core.performance.benchmark_types import (
            RegressionAnalysis,
        )

        formatters = BenchmarkFormatters()
        # RegressionAnalysisオブジェクトを使用
        analysis = RegressionAnalysis(
            benchmark_name="test_benchmark",
            baseline_avg_time=1.2,
            current_avg_time=1.0,
            performance_change_percent=-16.7,
            is_regression=False,
            severity="minor",
            memory_change_percent=0.0,
            cache_performance_change={"hits": 10.0, "misses": -50.0},
        )
        formatted = formatters.format_regression_analysis(analysis)
        assert isinstance(formatted, dict)
        assert "benchmark_name" in formatted
        assert "performance_change_percent" in formatted


class TestOriginalBenchmarkAnalyzer:
    """元のBenchmarkAnalyzerクラスとの互換性テスト"""

    def test_original_benchmark_analyzer_still_works(self):
        """元のBenchmarkAnalyzerが正常動作することを確認"""
        from kumihan_formatter.core.performance.benchmark_analyzer import (
            BenchmarkAnalyzer,
        )

        # 初期化テスト
        analyzer = BenchmarkAnalyzer()
        assert analyzer is not None

        # 基本メソッドが存在することを確認
        assert hasattr(analyzer, "analyze_results")
        assert hasattr(analyzer, "analyze_regression")
        assert hasattr(analyzer, "generate_benchmark_summary")

    def test_original_analyze_results_functionality(self):
        """元の結果分析機能テスト"""
        from kumihan_formatter.core.performance.benchmark_analyzer import (
            BenchmarkAnalyzer,
        )

        analyzer = BenchmarkAnalyzer()

        # 空のリストでの基本動作テスト
        result = analyzer.analyze_results([])
        assert isinstance(result, dict)
        assert "error" in result

    def test_original_analyze_regression_functionality(self):
        """元の回帰分析機能テスト"""
        from kumihan_formatter.core.performance.benchmark_analyzer import (
            BenchmarkAnalyzer,
        )

        analyzer = BenchmarkAnalyzer()

        # 空の辞書での基本動作テスト
        result = analyzer.analyze_regression({}, {})
        assert isinstance(result, dict)
        assert "overall_regression" in result
        assert "summary" in result

    def test_original_generate_summary_functionality(self):
        """元のサマリー生成機能テスト"""
        from kumihan_formatter.core.performance.benchmark_analyzer import (
            BenchmarkAnalyzer,
        )

        analyzer = BenchmarkAnalyzer()

        # 空のリストでエラーが発生することを確認
        with pytest.raises(ValueError, match="No results to summarize"):
            analyzer.generate_benchmark_summary([])
