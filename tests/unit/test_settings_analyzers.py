"""
Settings Analyzers テストスイート - Issue #813 対応

対象モジュール: kumihan_formatter.core.optimization.settings.analyzers
- TokenUsageAnalyzer: Token使用量分析システム
- ComplexityAnalyzer: コンテンツ複雑度分析システム

テスト範囲:
- TokenUsageAnalyzer: リアルタイム監視、パターン分析、最適化提案
- ComplexityAnalyzer: 記法複雑度評価、ネスト分析、特殊文字密度
- エラーハンドリング
- パフォーマンス基本測定
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from collections import deque, defaultdict
from typing import Any, Dict, List, Optional
from statistics import mean

from kumihan_formatter.core.optimization.settings.analyzers import (
    TokenUsageAnalyzer,
    ComplexityAnalyzer,
)
from kumihan_formatter.core.config.config_manager import EnhancedConfig
from kumihan_formatter.core.optimization.settings.manager import WorkContext
from kumihan_formatter.core.utilities.logger import get_logger


class TestComplexityAnalyzer:
    """ComplexityAnalyzer テストクラス"""

    @pytest.fixture
    def analyzer(self):
        """ComplexityAnalyzer インスタンス"""
        return ComplexityAnalyzer()

    def test_simple_content_analysis(self, analyzer):
        """シンプルなコンテンツの複雑度分析"""
        simple_content = "これは簡単なテキストです。"
        complexity = analyzer.analyze(simple_content)

        assert isinstance(complexity, float)
        assert 0.0 <= complexity <= 1.0
        assert complexity < 0.3  # シンプルなので低複雑度

    def test_complex_notation_analysis(self, analyzer):
        """記法を含む複雑なコンテンツの分析"""
        complex_content = """
        # 太字 #これは太字です##
        # イタリック #斜体テキスト##
        # 見出し1 #メインタイトル##
        # ハイライト #重要な部分##
        # 枠線 #囲み文字##
        """
        complexity = analyzer.analyze(complex_content)

        assert complexity > 0.3  # 複数記法なので高複雑度

    def test_notation_counting(self, analyzer):
        """記法種類カウント機能"""
        # 記法なし
        no_notation = "普通のテキストです"
        count = analyzer._count_notations(no_notation)
        assert count == 0

        # 単一記法
        single_notation = "# 太字 #テスト##"
        count = analyzer._count_notations(single_notation)
        assert count == 1

        # 複数記法
        multiple_notation = """
        # 太字 #テスト##
        # イタリック #テスト##
        # 見出し #テスト##
        """
        count = analyzer._count_notations(multiple_notation)
        assert count == 3

    def test_nesting_analysis(self, analyzer):
        """ネスト深度分析"""
        # ネストなし
        no_nest = "# 太字 #テスト##"
        depth = analyzer._analyze_nesting(no_nest)
        assert depth == 4  # 実際の # 文字の連続最大数

        # 深いネスト
        deep_nest = "######"
        depth = analyzer._analyze_nesting(deep_nest)
        assert depth == 6

        # 複数行での最大深度
        multiline_nest = """
        ###
        ######
        ##
        """
        depth = analyzer._analyze_nesting(multiline_nest)
        assert depth == 6  # 最大深度

    def test_special_char_ratio_calculation(self, analyzer):
        """特殊文字密度計算"""
        # 特殊文字なし
        no_special = "普通のテキスト"
        ratio = analyzer._calculate_special_char_ratio(no_special)
        assert ratio == 0.0

        # 特殊文字のみ
        all_special = "###***"
        ratio = analyzer._calculate_special_char_ratio(all_special)
        assert ratio == 1.0

        # 混合
        mixed = "テスト###"
        ratio = analyzer._calculate_special_char_ratio(mixed)
        assert 0.0 < ratio < 1.0

        # 空文字列
        empty = ""
        ratio = analyzer._calculate_special_char_ratio(empty)
        assert ratio == 0.0

    def test_complexity_factors_integration(self, analyzer):
        """複雑度要因統合テスト"""
        test_cases = [
            ("簡単なテキスト", 0.0, 0.3),  # 低複雑度
            ("# 太字 #テスト##", 0.1, 0.5),  # 中程度
            ("# 太字 ## イタリック ## 見出し #複雑##", 0.3, 0.6),  # 調整された範囲
        ]

        for content, min_expected, max_expected in test_cases:
            complexity = analyzer.analyze(content)
            assert min_expected <= complexity <= max_expected, (
                f"Content: '{content}' -> complexity: {complexity}, "
                f"expected: {min_expected}-{max_expected}"
            )

    def test_long_content_complexity(self, analyzer):
        """長文コンテンツの複雑度"""
        # 長い単純テキスト（記法なしなので複雑度は低い）
        long_simple = "テスト" * 1000  # 4000文字
        complexity = analyzer.analyze(long_simple)
        assert complexity == 0.0  # 記法がないため複雑度は0

        # 長い複雑テキスト
        long_complex = ("# 太字 #テスト##\n" * 500) + ("# イタリック #テスト##\n" * 500)
        complexity = analyzer.analyze(long_complex)
        assert complexity > 0.5  # 記法 + 行数で高複雑度（実測値約0.57）


class TestTokenUsageAnalyzer:
    """TokenUsageAnalyzer テストクラス"""

    @pytest.fixture
    def mock_config(self):
        """モックされた EnhancedConfig"""
        config = Mock(spec=EnhancedConfig)
        config.get.side_effect = lambda key, default=None: {
            "serena.max_answer_chars": 25000,
            "performance.max_recursion_depth": 50,
        }.get(key, default)
        return config

    @pytest.fixture
    def work_context(self):
        """テスト用 WorkContext"""
        return WorkContext(
            operation_type="test_operation",
            content_size=5000,
            complexity_score=0.6,
            user_pattern="test_pattern",
        )

    @pytest.fixture
    def analyzer(self, mock_config):
        """TokenUsageAnalyzer インスタンス"""
        return TokenUsageAnalyzer(mock_config)

    def test_analyzer_initialization(self, mock_config):
        """TokenUsageAnalyzer の初期化"""
        analyzer = TokenUsageAnalyzer(mock_config)

        assert analyzer.config == mock_config
        assert analyzer.logger is not None
        assert isinstance(analyzer.usage_history, deque)
        assert analyzer.usage_history.maxlen == 1000
        assert isinstance(analyzer.current_session_usage, dict)
        assert analyzer.current_session_usage["input_tokens"] == 0
        assert analyzer.current_session_usage["output_tokens"] == 0
        assert isinstance(analyzer._lock, threading.Lock)

    def test_token_usage_recording(self, analyzer, work_context):
        """Token使用量記録機能"""
        # Token使用量記録
        result = analyzer.record_token_usage(
            operation_type="parsing",
            input_tokens=1000,
            output_tokens=500,
            context=work_context,
        )

        # 記録結果の確認
        assert "recorded_usage" in result
        assert result["recorded_usage"]["input_tokens"] == 1000
        assert result["recorded_usage"]["output_tokens"] == 500
        assert result["recorded_usage"]["total_tokens"] == 1500

        # セッション統計の確認
        assert result["session_cumulative"]["input_tokens"] == 1000
        assert result["session_cumulative"]["output_tokens"] == 500
        assert result["session_cumulative"]["total_tokens"] == 1500
        assert result["session_cumulative"]["operations_count"] == 1

        # 履歴の確認
        assert len(analyzer.usage_history) == 1

    def test_multiple_token_recordings(self, analyzer, work_context):
        """複数回のToken使用量記録"""
        recordings = [
            (500, 300, "parsing"),
            (1000, 800, "rendering"),
            (200, 100, "optimization"),
        ]

        total_input = 0
        total_output = 0

        for input_tokens, output_tokens, operation in recordings:
            result = analyzer.record_token_usage(
                operation_type=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                context=work_context,
            )
            total_input += input_tokens
            total_output += output_tokens

        # セッション累積の確認
        session = analyzer.current_session_usage
        assert session["input_tokens"] == total_input
        assert session["output_tokens"] == total_output
        assert session["total_tokens"] == total_input + total_output
        assert session["operations_count"] == 3

        # 履歴の確認
        assert len(analyzer.usage_history) == 3

    def test_usage_pattern_updates(self, analyzer, work_context):
        """使用パターン更新機能"""
        # 複数の記録を追加
        analyzer.record_token_usage("parsing", 1000, 500, work_context)
        analyzer.record_token_usage("rendering", 800, 600, work_context)
        analyzer.record_token_usage("parsing", 1200, 400, work_context)  # 同じ操作

        # パターン確認
        assert "parsing" in analyzer.usage_patterns["operation_patterns"]
        assert "rendering" in analyzer.usage_patterns["operation_patterns"]

        # 時間別パターンも記録されていることを確認
        current_hour = time.strftime("%H")
        assert current_hour in analyzer.usage_patterns["hourly_patterns"]

    def test_efficiency_calculation(self, analyzer, work_context):
        """効率性スコア計算"""
        # 効率的なケース（少ないToken使用）
        result_efficient = analyzer.record_token_usage(
            operation_type="parsing",
            input_tokens=100,
            output_tokens=50,
            context=work_context,
        )
        efficiency_high = result_efficient["efficiency_score"]

        # 非効率的なケース（多いToken使用）
        result_inefficient = analyzer.record_token_usage(
            operation_type="parsing",
            input_tokens=5000,
            output_tokens=3000,
            context=work_context,
        )
        efficiency_low = result_inefficient["efficiency_score"]

        # 効率的なケースの方がスコアが高いことを確認
        assert efficiency_high > efficiency_low

    def test_optimization_opportunities_identification(self, analyzer, work_context):
        """最適化機会特定機能"""
        # 高Token使用量でのテスト
        result = analyzer.record_token_usage(
            operation_type="parsing",
            input_tokens=6000,
            output_tokens=2000,
            context=work_context,
        )

        opportunities = result["optimization_opportunities"]
        assert len(opportunities) > 0

        # 高Token使用量の警告が含まれることを確認
        high_usage_opportunity = next(
            (op for op in opportunities if op["type"] == "high_token_usage"), None
        )
        assert high_usage_opportunity is not None
        assert high_usage_opportunity["severity"] in ["medium", "high"]

    def test_optimization_suggestions_generation(self, analyzer, work_context):
        """最適化提案生成機能"""
        # 高Token使用量での記録（閾値を超えるように）
        result = analyzer.record_token_usage(
            operation_type="parsing",
            input_tokens=9000,  # 高い使用量
            output_tokens=2000,
            context=work_context,
        )

        # 最適化提案が生成されることを確認
        if "optimization_suggestions" in result:
            suggestions = result["optimization_suggestions"]
            assert len(suggestions) > 0

            for suggestion in suggestions:
                assert "type" in suggestion
                assert "priority" in suggestion
                assert "title" in suggestion
                assert "actions" in suggestion
                assert "estimated_total_reduction" in suggestion

    def test_optimization_threshold_calculation(self, analyzer):
        """最適化閾値計算"""
        # 初期閾値
        initial_threshold = analyzer._get_optimization_threshold()
        assert initial_threshold >= 3000

        # 履歴追加後の閾値変動
        for i in range(15):
            analyzer.usage_history.append(
                {
                    "timestamp": time.time(),
                    "operation_type": "test",
                    "input_tokens": 4000,
                    "output_tokens": 2000,
                    "total_tokens": 6000,
                    "context_size": 10000,
                    "complexity_score": 0.5,
                }
            )

        updated_threshold = analyzer._get_optimization_threshold()
        assert updated_threshold > initial_threshold

    def test_usage_analytics_generation(self, analyzer, work_context):
        """使用量分析結果生成"""
        # データなしの場合
        analytics_empty = analyzer.get_usage_analytics()
        assert analytics_empty["status"] == "no_data"

        # データ追加
        for i in range(5):
            analyzer.record_token_usage(
                operation_type="test_operation",
                input_tokens=1000 + i * 100,
                output_tokens=500 + i * 50,
                context=work_context,
            )

        # 分析実行
        analytics = analyzer.get_usage_analytics()

        # 基本構造確認
        assert "session_summary" in analytics
        assert "historical_analytics" in analytics
        assert "pattern_insights" in analytics
        assert "optimization_status" in analytics
        assert "recommendations" in analytics

        # 統計値確認
        historical = analytics["historical_analytics"]
        assert historical["total_operations"] == 5
        assert historical["total_tokens_consumed"] > 0
        assert historical["average_tokens_per_operation"] > 0
        assert 0.0 <= historical["overall_efficiency_score"] <= 1.0

    def test_peak_usage_hours_analysis(self, analyzer, work_context):
        """ピーク使用時間分析"""
        # 現在時刻での使用記録
        analyzer.record_token_usage("test", 1000, 500, work_context)

        peak_hours = analyzer._get_peak_usage_hours()
        assert isinstance(peak_hours, list)
        assert len(peak_hours) <= 3

        # 現在時刻が含まれていることを確認
        current_hour = time.strftime("%H")
        if peak_hours:  # データがある場合
            assert current_hour in peak_hours

    def test_potential_savings_calculation(self, analyzer):
        """潜在的節約効果計算"""
        # 最適化提案なしの場合
        savings_empty = analyzer._calculate_potential_savings()
        assert savings_empty["total_potential_reduction"] == 0.0
        assert savings_empty["estimated_token_savings"] == 0

        # 最適化提案追加
        analyzer.optimization_suggestions.append(
            {
                "estimated_total_reduction": 0.25,
                "type": "test_suggestion",
            }
        )

        # 使用履歴追加
        for i in range(25):
            analyzer.usage_history.append(
                {
                    "total_tokens": 2000,
                    "timestamp": time.time(),
                    "operation_type": "test",
                    "input_tokens": 1000,
                    "output_tokens": 1000,
                    "context_size": 5000,
                    "complexity_score": 0.5,
                }
            )

        savings = analyzer._calculate_potential_savings()
        assert savings["average_potential_reduction"] > 0.0
        assert savings["estimated_token_savings"] > 0

    def test_usage_recommendations_generation(self, analyzer):
        """使用量推奨事項生成"""
        # セッション使用量を高く設定
        analyzer.current_session_usage["total_tokens"] = 60000  # 高使用量

        # 履歴追加（低効率）
        for i in range(15):
            analyzer.usage_history.append(
                {
                    "timestamp": time.time(),
                    "operation_type": "test",
                    "input_tokens": 3000,
                    "output_tokens": 2000,
                    "total_tokens": 5000,
                    "context_size": 1000,  # 低効率になる
                    "complexity_score": 0.3,
                }
            )

        recommendations = analyzer._generate_usage_recommendations()
        assert isinstance(recommendations, list)

        # セッション最適化推奨が含まれることを確認
        session_rec = next(
            (
                rec
                for rec in recommendations
                if rec["category"] == "session_optimization"
            ),
            None,
        )
        assert session_rec is not None
        assert session_rec["priority"] == "high"

    def test_thread_safety(self, analyzer, work_context):
        """スレッドセーフティテスト"""
        results = []
        errors = []

        def worker(worker_id):
            try:
                result = analyzer.record_token_usage(
                    operation_type=f"worker_{worker_id}",
                    input_tokens=1000 + worker_id * 100,
                    output_tokens=500 + worker_id * 50,
                    context=work_context,
                )
                results.append(result["recorded_usage"]["total_tokens"])
            except Exception as e:
                errors.append(e)

        # 複数スレッドで同時実行
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # エラーが発生しないことを確認
        assert len(errors) == 0
        assert len(results) == 5
        assert len(analyzer.usage_history) == 5


class TestTokenUsageAnalyzerErrorHandling:
    """TokenUsageAnalyzer エラーハンドリングテスト"""

    @pytest.fixture
    def analyzer(self):
        """エラーテスト用アナライザー"""
        config = Mock(spec=EnhancedConfig)
        config.get.return_value = 25000
        return TokenUsageAnalyzer(config)

    def test_negative_token_handling(self, analyzer):
        """負のToken数の処理"""
        result = analyzer.record_token_usage(
            operation_type="test",
            input_tokens=-100,  # 負の値
            output_tokens=-50,  # 負の値
            context=None,
        )

        # エラーが発生せず処理されることを確認
        assert "recorded_usage" in result
        assert result["recorded_usage"]["input_tokens"] == -100
        assert result["recorded_usage"]["total_tokens"] == -150

    def test_none_context_handling(self, analyzer):
        """None コンテキストの処理"""
        result = analyzer.record_token_usage(
            operation_type="test",
            input_tokens=1000,
            output_tokens=500,
            context=None,  # Noneコンテキスト
        )

        # エラーが発生しないことを確認
        assert result["recorded_usage"]["context_size"] == 0
        assert result["recorded_usage"]["complexity_score"] == 0.0

    def test_extreme_values_handling(self, analyzer, work_context):
        """極端な値の処理"""
        # 極端に大きな値
        result_large = analyzer.record_token_usage(
            operation_type="test",
            input_tokens=1_000_000,  # 100万Token
            output_tokens=500_000,  # 50万Token
            context=work_context,
        )

        # 極端に小さな値
        result_zero = analyzer.record_token_usage(
            operation_type="test",
            input_tokens=0,
            output_tokens=0,
            context=work_context,
        )

        # 両方とも正常に処理されることを確認
        assert "recorded_usage" in result_large
        assert "recorded_usage" in result_zero


class TestTokenUsageAnalyzerPerformance:
    """TokenUsageAnalyzer パフォーマンステスト"""

    @pytest.fixture
    def analyzer(self):
        """パフォーマンステスト用アナライザー"""
        config = Mock(spec=EnhancedConfig)
        config.get.return_value = 25000
        return TokenUsageAnalyzer(config)

    @pytest.fixture
    def work_context(self):
        """パフォーマンステスト用コンテキスト"""
        return WorkContext(
            operation_type="performance_test",
            content_size=10000,
            complexity_score=0.5,
        )

    def test_recording_performance(self, analyzer, work_context):
        """記録処理のパフォーマンス"""
        start_time = time.time()

        # 100回の記録
        for i in range(100):
            analyzer.record_token_usage(
                operation_type="perf_test",
                input_tokens=1000 + i,
                output_tokens=500 + i,
                context=work_context,
            )

        end_time = time.time()
        elapsed = end_time - start_time

        # 100回の記録が0.5秒以内に完了することを確認
        assert elapsed < 0.5, f"Recording performance too slow: {elapsed:.3f}s"

    def test_analytics_generation_performance(self, analyzer, work_context):
        """分析生成のパフォーマンス"""
        # データ準備
        for i in range(200):
            analyzer.record_token_usage(
                operation_type=f"test_{i % 5}",
                input_tokens=1000 + i,
                output_tokens=500 + i,
                context=work_context,
            )

        start_time = time.time()
        analytics = analyzer.get_usage_analytics()
        end_time = time.time()
        elapsed = end_time - start_time

        # 分析生成が0.1秒以内に完了することを確認
        assert elapsed < 0.1, f"Analytics generation too slow: {elapsed:.3f}s"
        assert analytics is not None

    def test_memory_usage_control(self, analyzer, work_context):
        """メモリ使用量制御"""
        # maxlenを超える記録を追加
        for i in range(1500):  # maxlen=1000を超える
            analyzer.record_token_usage(
                operation_type="memory_test",
                input_tokens=1000,
                output_tokens=500,
                context=work_context,
            )

        # 履歴がmaxlenで制限されていることを確認
        assert len(analyzer.usage_history) == 1000
        assert analyzer.usage_history.maxlen == 1000

        # 最新の記録が保持されていることを確認
        latest_record = analyzer.usage_history[-1]
        assert latest_record["operation_type"] == "memory_test"


class TestAnalyzersIntegration:
    """Analyzers統合テスト"""

    @pytest.fixture
    def token_analyzer(self):
        """Token分析器"""
        config = Mock(spec=EnhancedConfig)
        config.get.return_value = 25000
        return TokenUsageAnalyzer(config)

    @pytest.fixture
    def complexity_analyzer(self):
        """複雑度分析器"""
        return ComplexityAnalyzer()

    def test_analyzers_coordination(self, token_analyzer, complexity_analyzer):
        """分析器の連携テスト"""
        test_content = """
        # 太字 #重要な情報##
        # イタリック #斜体テキスト##
        # 見出し1 #メインタイトル##
        """

        # 複雑度分析
        complexity_score = complexity_analyzer.analyze(test_content)

        # WorkContextの作成（複雑度を使用）
        work_context = WorkContext(
            operation_type="integration_test",
            content_size=len(test_content),
            complexity_score=complexity_score,
        )

        # Token使用量記録（複雑度を考慮）
        estimated_tokens = int(complexity_score * 2000)  # 複雑度ベースの推定
        result = token_analyzer.record_token_usage(
            operation_type="complexity_based_analysis",
            input_tokens=estimated_tokens,
            output_tokens=int(estimated_tokens * 0.5),
            context=work_context,
        )

        # 統合結果確認
        assert result["recorded_usage"]["complexity_score"] == complexity_score
        assert result["efficiency_score"] is not None

        # 複雑度が効率性に影響することを確認
        if complexity_score > 0.5:
            assert len(result["optimization_opportunities"]) > 0

    def test_real_world_scenario(self, token_analyzer, complexity_analyzer):
        """実世界シナリオテスト"""
        scenarios = [
            ("簡単な文書", "これは簡単な文書です。", 500, 300),
            (
                "中程度の文書",
                "# 太字 #重要##\n# イタリック #説明##\n通常のテキスト",
                1500,
                800,
            ),
            (
                "複雑な文書",
                "# 太字 ## イタリック ## 見出し1 ## ハイライト #複雑##" * 10,
                5000,
                3000,
            ),
        ]

        analytics_results = []

        for name, content, input_tokens, output_tokens in scenarios:
            # 複雑度分析
            complexity = complexity_analyzer.analyze(content)

            # コンテキスト作成
            context = WorkContext(
                operation_type="real_world_test",
                content_size=len(content),
                complexity_score=complexity,
                user_pattern=name.replace(" ", "_"),
            )

            # Token使用量記録
            result = token_analyzer.record_token_usage(
                operation_type="real_world_analysis",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                context=context,
            )

            analytics_results.append(
                {
                    "scenario": name,
                    "complexity": complexity,
                    "efficiency": result["efficiency_score"],
                    "total_tokens": input_tokens + output_tokens,
                }
            )

        # 結果の妥当性確認
        assert len(analytics_results) == 3

        # 複雑度と効率性の相関確認
        simple_scenario = analytics_results[0]
        complex_scenario = analytics_results[2]

        # 複雑なシナリオの方が複雑度が高い
        assert complex_scenario["complexity"] > simple_scenario["complexity"]

        # 総合分析レポート生成
        final_analytics = token_analyzer.get_usage_analytics()
        assert final_analytics["historical_analytics"]["total_operations"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
