"""
Settings Module 統合テストスイート - Issue #813 対応

settingsモジュール全体の統合テスト
- AdaptiveSettingsManager + 各種最適化コンポーネントの連携
- A/Bテストフレームワークとの統合
- リアルタイム最適化システムの動作検証
- エンドツーエンドワークフロー
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from collections import deque
from typing import Any, Dict, List

from kumihan_formatter.core.optimization.settings.manager import (
    AdaptiveSettingsManager,
    ConfigAdjustment,
    WorkContext,
)
from kumihan_formatter.core.optimization.settings.analyzers import (
    TokenUsageAnalyzer,
    ComplexityAnalyzer,
)
from kumihan_formatter.core.optimization.settings.ab_testing import (
    StatisticalTestingEngine,
    ABTestConfig,
    ABTestResult,
)
from kumihan_formatter.core.optimization.settings.optimizers import (
    FileSizeLimitOptimizer,
    ConcurrentToolCallLimiter,
)
from kumihan_formatter.core.config.config_manager import EnhancedConfig
from kumihan_formatter.core.utilities.logger import get_logger


class TestSettingsModuleIntegration:
    """Settings モジュール統合テストクラス"""

    @pytest.fixture
    def enhanced_config(self):
        """強化されたコンフィグモック"""
        config = Mock(spec=EnhancedConfig)
        config.get.side_effect = lambda key, default=None: {
            "serena.max_answer_chars": 25000,
            "performance.max_recursion_depth": 50,
            "cache.templates": True,
            "monitoring.interval": 30,
            "optimization.max_concurrent_tools": 5,
        }.get(key, default)
        config.set.return_value = None
        return config

    @pytest.fixture
    def integrated_manager(self, enhanced_config):
        """統合された AdaptiveSettingsManager"""
        manager = AdaptiveSettingsManager(enhanced_config)

        # モックコンポーネントを手動で設定
        manager.statistical_engine = Mock(spec=StatisticalTestingEngine)
        manager.file_size_optimizer = Mock(spec=FileSizeLimitOptimizer)
        manager.concurrent_limiter = Mock(spec=ConcurrentToolCallLimiter)
        manager.token_analyzer = Mock(spec=TokenUsageAnalyzer)

        return manager

    @pytest.fixture
    def real_components_manager(self, enhanced_config):
        """実際のコンポーネントを使用する統合マネージャー"""
        manager = AdaptiveSettingsManager(enhanced_config)
        return manager

    @pytest.fixture
    def work_contexts(self):
        """多様なワークコンテキスト"""
        return [
            WorkContext("parsing", 15000, 0.4, "simple_document"),
            WorkContext("rendering", 45000, 0.7, "complex_document"),
            WorkContext("optimization", 8000, 0.3, "maintenance_task"),
            WorkContext("parsing", 120000, 0.9, "large_codebase"),
            WorkContext("tool_call", 2000, 0.2, "utility_operation"),
        ]

    def test_manager_with_all_components_initialized(self, integrated_manager):
        """全コンポーネント初期化後のマネージャー動作"""
        # コンポーネントが適切に設定されていることを確認
        assert integrated_manager.statistical_engine is not None
        assert integrated_manager.file_size_optimizer is not None
        assert integrated_manager.concurrent_limiter is not None
        assert integrated_manager.token_analyzer is not None

        # AI最適化統合サマリー取得
        summary = integrated_manager.get_ai_optimization_summary()

        assert "file_size_optimization" in summary
        assert "concurrent_control" in summary
        assert "token_analysis" in summary
        assert "integration_status" in summary
        assert "system_health" in summary

        # システム健全性確認
        system_health = summary["system_health"]
        assert system_health["file_optimizer_active"] is True
        assert system_health["concurrent_limiter_active"] is True
        assert system_health["token_analyzer_active"] is True
        assert system_health["integration_complete"] is True

    def test_end_to_end_optimization_workflow(self, integrated_manager, work_contexts):
        """エンドツーエンド最適化ワークフロー"""
        # モック設定
        integrated_manager.file_size_optimizer.adjust_limits_dynamically.return_value = True
        integrated_manager.file_size_optimizer.get_optimization_statistics.return_value = {
            "effectiveness_score": 0.8
        }
        integrated_manager.concurrent_limiter.get_concurrency_statistics.return_value = {
            "max_concurrent_calls": 5
        }
        integrated_manager.concurrent_limiter.adjust_limits_based_on_performance.return_value = None
        integrated_manager.token_analyzer.record_token_usage.return_value = {
            "efficiency_score": 0.85,
            "optimization_suggestions": []
        }

        all_adjustments = []
        for context in work_contexts:
            adjustments = integrated_manager.adjust_for_context(context)
            all_adjustments.extend(adjustments)

        # 調整が実行されたことを確認
        assert len(all_adjustments) > 0

        # 各コンポーネントが呼び出されたことを確認
        integrated_manager.file_size_optimizer.adjust_limits_dynamically.assert_called()
        integrated_manager.token_analyzer.record_token_usage.assert_called()

        # 最適化状況確認
        status = integrated_manager.get_current_optimization_status()
        assert status["total_adjustments"] >= len(all_adjustments)
        assert "ai_optimization_summary" in status

    def test_ab_test_integration_workflow(self, integrated_manager):
        """A/Bテスト統合ワークフロー"""
        # A/Bテスト開始
        test_id = integrated_manager.start_ab_test(
            "serena.max_answer_chars",
            [20000, 25000, 30000],
            sample_size=5
        )

        assert test_id is not None
        assert test_id in integrated_manager.active_tests

        # テスト結果を段階的に記録
        test_values = [0.7, 0.8, 0.6, 0.75, 0.85]  # 5つのサンプル

        for value in test_values:
            success = integrated_manager.record_ab_test_result(test_id, value)
            assert success is True

        # テスト状況確認
        test_data = integrated_manager.active_tests.get(test_id)
        if test_data:  # テストが完了していない場合
            assert len(test_data["results"]) == len(test_values)

        # 完了したテストの結果確認
        results = integrated_manager.get_ab_test_results("serena.max_answer_chars")
        assert isinstance(results, list)

    def test_learning_system_integration(self, integrated_manager, work_contexts):
        """学習システム統合テスト"""
        # 複数回の同じパターン実行でパターン学習
        parsing_context = WorkContext("parsing", 20000, 0.5, "learning_test")

        # 学習のための複数回実行
        for _ in range(4):  # 学習に必要な最小回数
            integrated_manager.adjust_for_context(parsing_context)

        # パターンが学習されていることを確認
        pattern_key = f"parsing_{integrated_manager._classify_content_size(20000)}"
        assert pattern_key in integrated_manager.context_patterns
        assert integrated_manager.context_patterns[pattern_key]["count"] == 4

        # 学習状況確認
        learning_status = integrated_manager.get_learning_status()
        assert learning_status["total_context_patterns"] >= 1
        assert learning_status["learned_patterns"] >= 1
        assert learning_status["learning_active"] is True

        # 使用パターン学習実行
        learning_summary = integrated_manager.learn_usage_patterns()
        assert learning_summary["patterns_discovered"] >= 1

        # 学習済み最適化適用
        learned_adjustments = integrated_manager.apply_learned_optimizations()
        assert isinstance(learned_adjustments, list)

    def test_concurrent_optimization_operations(self, integrated_manager):
        """並行最適化操作テスト"""
        results = []
        errors = []

        def optimization_worker(worker_id):
            try:
                context = WorkContext(
                    f"concurrent_test_{worker_id}",
                    10000 + worker_id * 1000,
                    0.5 + worker_id * 0.1,
                )

                adjustments = integrated_manager.adjust_for_context(context)
                results.append(len(adjustments))
            except Exception as e:
                errors.append(e)

        # 複数スレッドでの並行実行
        threads = [threading.Thread(target=optimization_worker, args=(i,))
                  for i in range(10)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # エラーなしで実行完了
        assert len(errors) == 0
        assert len(results) == 10

        # 並行実行でもデータ整合性が保たれていることを確認
        status = integrated_manager.get_current_optimization_status()
        assert status["total_adjustments"] >= 0

    def test_file_operation_optimization_integration(self, integrated_manager):
        """ファイル操作最適化統合テスト"""
        # ファイル操作最適化の設定
        integrated_manager.file_size_optimizer.optimize_read_size.return_value = (
            35000,
            {
                "optimized": True,
                "original_size": 50000,
                "optimized_size": 35000,
                "reduction_rate": 0.3,
                "file_type": "code",
                "tokens_saved_estimate": 3750,
            }
        )

        # ファイル操作最適化実行
        result = integrated_manager.optimize_for_file_operation(
            "/test/path/file.py", "read"
        )

        assert result["original_file_size"] == 0  # ファイルが存在しないため
        assert "optimized_size" in result
        assert "optimization_info" in result
        assert "adjustments_applied" in result

        # ファイルサイズオプティマイザーが呼び出されたことを確認
        integrated_manager.file_size_optimizer.optimize_read_size.assert_called()

    def test_tool_permission_integration(self, integrated_manager):
        """ツール許可システム統合テスト"""
        # ツール許可取得の設定
        integrated_manager.concurrent_limiter.acquire_call_permission.return_value = (
            True, "permission_123"
        )
        integrated_manager.concurrent_limiter.release_call_permission.return_value = None

        # ツール許可取得
        granted, permission_id = integrated_manager.acquire_tool_permission(
            "test_tool", 0.7
        )

        assert granted is True
        assert permission_id == "permission_123"

        # ツール許可解放
        integrated_manager.release_tool_permission(permission_id)

        # コンカレントリミッターが適切に呼び出されたことを確認
        integrated_manager.concurrent_limiter.acquire_call_permission.assert_called_once()
        integrated_manager.concurrent_limiter.release_call_permission.assert_called_once_with(
            permission_id
        )

    def test_real_world_scenario_simulation(self, real_components_manager):
        """リアルワールドシナリオシミュレーション"""
        # 実際のコンポーネントを使用したテスト
        scenarios = [
            ("文書解析", "parsing", 25000, 0.6),
            ("レンダリング", "rendering", 40000, 0.8),
            ("最適化処理", "optimization", 12000, 0.4),
            ("大規模処理", "parsing", 100000, 0.9),
        ]

        with patch.object(real_components_manager, "_initialize_components"):
            # モックコンポーネントを設定
            real_components_manager.file_size_optimizer = Mock()
            real_components_manager.concurrent_limiter = Mock()
            real_components_manager.token_analyzer = Mock()

            # デフォルトの戻り値を設定
            real_components_manager.file_size_optimizer.adjust_limits_dynamically.return_value = False
            real_components_manager.concurrent_limiter.get_concurrency_statistics.return_value = {
                "max_concurrent_calls": 5
            }
            real_components_manager.token_analyzer.record_token_usage.return_value = {
                "efficiency_score": 0.8,
                "optimization_suggestions": []
            }

            all_results = []
            for name, operation, size, complexity in scenarios:
                context = WorkContext(operation, size, complexity, name)

                # 最適化実行
                adjustments = real_components_manager.adjust_for_context(context)

                # 結果記録
                all_results.append({
                    "scenario": name,
                    "adjustments_count": len(adjustments),
                    "context": context,
                })

        # 結果検証
        assert len(all_results) == len(scenarios)

        # 最終的な最適化状況確認
        final_status = real_components_manager.get_current_optimization_status()
        assert final_status["total_adjustments"] >= 0

    def test_error_resilience_integration(self, integrated_manager):
        """エラー耐性統合テスト"""
        # コンポーネントエラーシミュレーション
        integrated_manager.file_size_optimizer.adjust_limits_dynamically.side_effect = Exception(
            "File optimizer error"
        )
        integrated_manager.token_analyzer.record_token_usage.side_effect = Exception(
            "Token analyzer error"
        )

        # エラーが発生してもシステム全体が停止しないことを確認
        context = WorkContext("error_test", 30000, 0.7)

        # adjust_for_context は例外を吸収して継続すべき
        adjustments = integrated_manager.adjust_for_context(context)

        # エラーが発生しても何らかの調整は実行される
        assert isinstance(adjustments, list)

        # システム状況は取得可能
        status = integrated_manager.get_current_optimization_status()
        assert status is not None

    def test_performance_under_load(self, integrated_manager, work_contexts):
        """負荷時のパフォーマンステスト"""
        # 高負荷シミュレーション
        start_time = time.time()

        # 100回の最適化実行
        for i in range(100):
            context = work_contexts[i % len(work_contexts)]
            integrated_manager.adjust_for_context(context)

        end_time = time.time()
        elapsed = end_time - start_time

        # パフォーマンス要件（100回の実行が2秒以内）
        assert elapsed < 2.0, f"Performance test failed: {elapsed:.3f}s"

        # メモリ使用量確認（履歴サイズ制限）
        assert len(integrated_manager.adjustment_history) <= 1000
        assert len(integrated_manager.context_patterns) <= 50  # 合理的な上限


class TestAnalyzersWithOptimizersIntegration:
    """Analyzers と Optimizers の統合テスト"""

    @pytest.fixture
    def token_analyzer(self):
        """Token使用量分析器"""
        config = Mock(spec=EnhancedConfig)
        config.get.return_value = 25000
        return TokenUsageAnalyzer(config)

    @pytest.fixture
    def complexity_analyzer(self):
        """複雑度分析器"""
        return ComplexityAnalyzer()

    @pytest.fixture
    def file_size_optimizer(self):
        """ファイルサイズオプティマイザー"""
        config = Mock(spec=EnhancedConfig)
        return FileSizeLimitOptimizer(config)

    def test_analyzer_optimizer_coordination(
        self, token_analyzer, complexity_analyzer, file_size_optimizer
    ):
        """分析器と最適化器の協調動作テスト"""
        test_content = """
        # 太字 #重要な情報## * 複数行
        # イタリック #詳細説明## * にわたる
        # 見出し1 #メインタイトル## * 複雑な
        """ * 100  # 大きなコンテンツ

        # Step 1: 複雑度分析
        complexity = complexity_analyzer.analyze(test_content)
        assert complexity > 0.5  # 複雑なコンテンツ

        # Step 2: ファイルサイズ最適化
        original_size = len(test_content)
        optimized_size, optimization_info = file_size_optimizer.optimize_read_size(
            "test.md", original_size
        )

        assert optimized_size <= original_size
        assert optimization_info["file_type"] == "documentation"

        # Step 3: Token使用量記録（最適化後のサイズで）
        context = WorkContext(
            "integrated_analysis",
            optimized_size,
            complexity,
        )

        # 推定Token数（最適化後）
        estimated_tokens = int(optimized_size * 0.25)
        result = token_analyzer.record_token_usage(
            "integrated_test",
            estimated_tokens,
            int(estimated_tokens * 0.6),
            context,
        )

        # 統合結果検証
        assert result["recorded_usage"]["context_size"] == optimized_size
        assert result["recorded_usage"]["complexity_score"] == complexity

        # 最適化によりToken使用量が削減されていることを間接的に確認
        if optimization_info["optimized"]:
            assert optimized_size < original_size

    def test_feedback_loop_integration(
        self, token_analyzer, file_size_optimizer
    ):
        """フィードバックループ統合テスト"""
        # 初期設定
        large_files = [
            ("large_code.py", 80000),
            ("huge_doc.md", 150000),
            ("big_config.json", 60000),
        ]

        optimization_results = []

        for file_path, file_size in large_files:
            # ファイルサイズ最適化
            optimized_size, opt_info = file_size_optimizer.optimize_read_size(
                file_path, file_size
            )

            # Token使用量記録
            estimated_tokens = int(optimized_size * 0.25)
            context = WorkContext("feedback_test", optimized_size, 0.6)

            token_result = token_analyzer.record_token_usage(
                "feedback_analysis",
                estimated_tokens,
                int(estimated_tokens * 0.5),
                context,
            )

            optimization_results.append({
                "file_path": file_path,
                "original_size": file_size,
                "optimized_size": optimized_size,
                "tokens_estimated": estimated_tokens,
                "efficiency_score": token_result["efficiency_score"],
            })

        # フィードバック分析
        total_reduction = sum(
            (r["original_size"] - r["optimized_size"])
            for r in optimization_results
        )
        avg_efficiency = sum(r["efficiency_score"] for r in optimization_results) / len(
            optimization_results
        )

        assert total_reduction > 0  # 全体的な削減効果
        assert avg_efficiency > 0.5  # 平均的な効率性

        # 最適化器の統計確認
        opt_stats = file_size_optimizer.get_optimization_statistics()
        assert opt_stats["size_limited_reads"] == len(large_files)
        assert opt_stats["effectiveness_score"] > 0

        # Token分析器の分析結果確認
        analytics = token_analyzer.get_usage_analytics()
        assert analytics["historical_analytics"]["total_operations"] == len(large_files)


class TestOptimizersAdvancedIntegration:
    """最適化システム詳細統合テスト"""

    @pytest.fixture
    def file_optimizer(self):
        """ファイルサイズオプティマイザー"""
        config = Mock(spec=EnhancedConfig)
        return FileSizeLimitOptimizer(config)

    @pytest.fixture
    def concurrent_limiter(self):
        """並列制御システム"""
        config = Mock(spec=EnhancedConfig)
        config.get.return_value = 3
        return ConcurrentToolCallLimiter(config)

    def test_file_size_optimizer_detailed(self, file_optimizer):
        """ファイルサイズオプティマイザー詳細テスト"""
        # 各種ファイルタイプのテスト
        test_cases = [
            ("test.py", 120000, "code", 100000),
            ("README.md", 200000, "documentation", 150000),
            ("config.json", 40000, "config", 25000),
            ("data.txt", 90000, "text", 75000),
            ("unknown.xyz", 80000, "default", 50000),
        ]

        for file_path, original_size, expected_type, expected_limit in test_cases:
            optimized_size, opt_info = file_optimizer.optimize_read_size(
                file_path, original_size
            )

            assert opt_info["file_type"] == expected_type
            if original_size > expected_limit:
                assert optimized_size == expected_limit
                assert opt_info["optimized"] is True
                assert opt_info["reduction_rate"] > 0
            else:
                assert optimized_size == original_size
                assert opt_info["optimized"] is False

        # 統計情報確認
        stats = file_optimizer.get_optimization_statistics()
        assert stats["total_file_reads"] == len(test_cases)
        assert stats["optimization_rate"] > 0
        assert stats["effectiveness_score"] > 0

    def test_concurrent_limiter_detailed(self, concurrent_limiter):
        """並列制御システム詳細テスト"""
        # 異なるツールタイプの許可取得
        tools = [
            ("file_read", "file_operations"),
            ("grep_search", "search_operations"),
            ("analyze_code", "analysis_operations"),
            ("custom_tool", "default"),
        ]

        granted_permissions = []

        for tool_name, expected_category in tools:
            granted, perm_id = concurrent_limiter.acquire_call_permission(tool_name)

            if granted:
                granted_permissions.append(perm_id)

                # 統計確認
                stats = concurrent_limiter.get_concurrency_statistics()
                assert stats["current_active_calls"] == len(granted_permissions)

                # アクティブコールの詳細確認
                active_calls = stats["active_calls_detail"]
                matching_call = next(
                    (call for call in active_calls if call["tool"] == tool_name),
                    None
                )
                assert matching_call is not None
                assert matching_call["category"] == expected_category

        # 許可解放
        for perm_id in granted_permissions:
            concurrent_limiter.release_call_permission(perm_id)

        # 解放後の状況確認
        final_stats = concurrent_limiter.get_concurrency_statistics()
        assert final_stats["current_active_calls"] == 0

    def test_concurrent_limiter_resource_throttling(self, concurrent_limiter):
        """リソーススロットリング機能テスト"""
        # 大きなコンテキストでのスロットリング
        large_context = WorkContext(
            "resource_test",
            150000,  # 大きなコンテンツ
            0.95,    # 高複雑性
        )

        # 複数の大きなリクエストを送信
        granted_count = 0
        for i in range(10):
            granted, _ = concurrent_limiter.acquire_call_permission(
                f"large_tool_{i}", large_context
            )
            if granted:
                granted_count += 1

        # リソーススロットリングにより制限されることを確認
        stats = concurrent_limiter.get_concurrency_statistics()
        assert stats["current_active_calls"] <= concurrent_limiter.max_concurrent_calls

    def test_performance_based_limit_adjustment(self, concurrent_limiter):
        """パフォーマンス基準の制限調整テスト"""
        initial_limit = concurrent_limiter.max_concurrent_calls

        # 低パフォーマンス状況をシミュレート
        poor_performance = {
            "average_response_time": 15.0,  # 遅い
            "resource_usage_percent": 85,   # 高使用率
        }

        concurrent_limiter.adjust_limits_based_on_performance(poor_performance)
        assert concurrent_limiter.max_concurrent_calls < initial_limit

        # 良好なパフォーマンス状況をシミュレート
        good_performance = {
            "average_response_time": 2.0,  # 高速
            "resource_usage_percent": 30,  # 低使用率
        }

        concurrent_limiter.adjust_limits_based_on_performance(good_performance)
        # 制限が緩和される可能性がある（元に戻るまたはさらに緩和）

        stats = concurrent_limiter.get_concurrency_statistics()
        assert stats["max_concurrent_calls"] >= 1  # 最低でも1は維持

    def test_optimizers_integration_workflow(self, file_optimizer, concurrent_limiter):
        """最適化システム統合ワークフロー"""
        # ステップ1: ファイルサイズ最適化
        large_files = [
            "large_code.py",
            "huge_documentation.md",
            "big_config.json"
        ]

        optimization_results = []
        for file_path in large_files:
            size, info = file_optimizer.optimize_read_size(file_path, 80000)
            optimization_results.append((file_path, size, info))

        # ステップ2: 並列処理許可取得
        permissions = []
        for file_path, size, info in optimization_results:
            # ファイル処理のためのツール許可
            context = WorkContext("file_processing", size, 0.5)
            granted, perm_id = concurrent_limiter.acquire_call_permission(
                "file_processor", context
            )

            if granted:
                permissions.append(perm_id)

        # ステップ3: 統計確認
        file_stats = file_optimizer.get_optimization_statistics()
        concurrent_stats = concurrent_limiter.get_concurrency_statistics()

        assert file_stats["total_file_reads"] == len(large_files)
        assert concurrent_stats["current_active_calls"] == len(permissions)

        # ステップ4: リソース解放
        for perm_id in permissions:
            concurrent_limiter.release_call_permission(perm_id)

        # 効率性スコア確認
        assert file_stats["effectiveness_score"] > 0
        assert concurrent_stats["efficiency_score"] > 0


class TestABTestingIntegrationFlow:
    """A/Bテスティング統合フローテスト"""

    @pytest.fixture
    def statistical_engine(self):
        """統計エンジン"""
        return StatisticalTestingEngine()

    @pytest.fixture
    def manager_with_ab(self, enhanced_config):
        """A/Bテスト機能付きマネージャー"""
        manager = AdaptiveSettingsManager(enhanced_config)
        manager.statistical_engine = StatisticalTestingEngine()
        return manager

    def test_statistical_engine_integration(self, statistical_engine):
        """統計エンジン統合テスト"""
        # サンプルデータ
        group_a = [0.7, 0.8, 0.6, 0.75, 0.82, 0.79]  # 高性能グループ
        group_b = [0.5, 0.6, 0.45, 0.55, 0.58, 0.52]  # 低性能グループ

        # 統計テスト実行
        test_result = statistical_engine.perform_statistical_test(
            group_a, group_b, "t_test"
        )

        assert test_result.test_type == "t_test"
        assert isinstance(test_result.p_value, float)
        assert isinstance(test_result.statistic, float)
        assert test_result.p_value < 0.05  # 有意差があるはず

        # 効果量計算
        cohens_d = statistical_engine.calculate_cohens_d(group_a, group_b)
        assert cohens_d > 0.5  # 中程度以上の効果量

        # 信頼区間計算
        ci_a = statistical_engine.calculate_confidence_interval(group_a)
        assert ci_a is not None
        assert len(ci_a) == 2
        assert ci_a[0] < ci_a[1]

    def test_ab_test_complete_cycle(self, manager_with_ab):
        """A/Bテスト完全サイクルテスト"""
        # テスト設定
        parameter = "serena.max_answer_chars"
        test_values = [20000, 25000, 30000]
        sample_size = 6

        # A/Bテスト開始
        test_id = manager_with_ab.start_ab_test(parameter, test_values, sample_size)
        assert test_id is not None

        # 各値に対してサンプルデータを記録
        # 値1: 20000 - 効率的
        for i in range(sample_size):
            success = manager_with_ab.record_ab_test_result(test_id, 0.85 + i * 0.02)
            assert success is True

        # 値2: 25000 - 中程度
        for i in range(sample_size):
            success = manager_with_ab.record_ab_test_result(test_id, 0.75 + i * 0.02)
            assert success is True

        # 値3: 30000 - 低効率
        for i in range(sample_size):
            success = manager_with_ab.record_ab_test_result(test_id, 0.65 + i * 0.02)
            assert success is True

        # テスト完了後の結果確認
        results = manager_with_ab.get_ab_test_results(parameter)
        assert len(results) >= 1

        # 勝利値が20000であることを確認（最も効率的）
        if results:
            latest_result = results[-1]
            assert latest_result["winning_value"] == 20000

    def test_simple_ab_test_integration(self, manager_with_ab):
        """シンプルA/Bテスト統合（Phase B.2用）"""
        # シンプルテスト実行
        test_id = manager_with_ab.run_simple_ab_test(
            "monitoring.interval", [15, 30, 45], 8
        )

        assert test_id is not None
        assert test_id in manager_with_ab.active_tests

        # 少数のサンプルで結果記録
        sample_results = [0.8, 0.7, 0.6, 0.75, 0.85, 0.65, 0.78, 0.72]
        for result in sample_results:
            success = manager_with_ab.record_ab_test_result(test_id, result)
            assert success is True

        # アクティブテストの状況確認
        active_test = manager_with_ab.active_tests.get(test_id)
        if active_test:  # まだ完了していない場合
            assert len(active_test["results"]) == len(sample_results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
