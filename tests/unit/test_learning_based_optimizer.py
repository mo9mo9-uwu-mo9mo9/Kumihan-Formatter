"""
LearningBasedOptimizer テストスイート - 包括的テストケース

対象モジュール: kumihan_formatter.core.optimization.settings.settings_optimizers
- LearningBasedOptimizer: 学習型最適化システム

テスト範囲:
- 基本動作（初期化、設定調整）
- 学習サイクル実行機能
- データ統合分析機能
- 最適化提案生成機能
- 自動最適化適用機能
- A/Bテスト設定機能
- ステータス取得機能
- エラーハンドリング
- パフォーマンス測定
"""

import time
from collections import deque
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.config.config_manager import EnhancedConfig
from kumihan_formatter.core.config.optimization.settings_optimizers import (
    LearningBasedOptimizer,
)


# 共通フィクスチャ（全テストクラス共用）
@pytest.fixture
def mock_config():
    """モックされた EnhancedConfig"""
    config = Mock(spec=EnhancedConfig)
    config.get.side_effect = lambda key, default=None: {
        "serena.max_answer_chars": 25000,
        "performance.max_recursion_depth": 50,
        "cache.templates": True,
        "monitoring.interval": 30,
        "optimization.max_concurrent_tools": 5,
    }.get(key, default)
    config.get_all.return_value = {
        "serena.max_answer_chars": 25000,
        "performance.max_recursion_depth": 50,
    }
    config.set.return_value = None
    return config


@pytest.fixture
def mock_adaptive_manager():
    """モックされた AdaptiveSettingsManager"""
    from kumihan_formatter.core.config.optimization.manager import (
        AdaptiveSettingsManager,
        ConfigAdjustment,
    )

    manager = Mock(spec=AdaptiveSettingsManager)
    manager.learn_usage_patterns.return_value = {
        "patterns_discovered": 3,
        "efficiency_insights": {
            "parsing_medium": {
                "efficiency_score": 0.7,
                "sample_count": 10,
            },
            "rendering_large": {
                "efficiency_score": 0.5,
                "sample_count": 15,
            },
        },
        "optimization_opportunities": [
            {
                "pattern": "parsing_medium",
                "recommendations": [
                    {
                        "type": "max_answer_chars_reduction",
                        "expected_improvement": 0.08,
                    }
                ],
            }
        ],
    }
    manager.get_learning_status.return_value = {
        "total_context_patterns": 5,
        "learned_patterns": 3,
        "learning_coverage": 0.6,
    }
    manager.run_simple_ab_test.return_value = "ab_test_123"
    manager._apply_adjustment.return_value = None

    # ConfigAdjustment mock
    config_adjustment = ConfigAdjustment(
        key="serena.max_answer_chars",
        old_value=25000,
        new_value=20000,
        context="learning_based_auto_parsing_medium",
        timestamp=time.time(),
        reason="LearningBasedOptimizer auto-optimization: 8.0% expected",
        expected_benefit=0.08,
    )
    config_adjustment.expected_benefit = 0.08

    return manager


@pytest.fixture
def mock_efficiency_analyzer():
    """モックされた TokenEfficiencyAnalyzer"""
    analyzer = Mock()
    analyzer.get_pattern_insights.return_value = {
        "pattern_rankings": {
            "parsing_medium": 0.6,
            "rendering_large": 0.4,
        }
    }
    analyzer.auto_suggest_optimizations.return_value = [
        {
            "pattern": "new_pattern",
            "type": "memory_optimization",
            "expected_improvement": 0.05,
        }
    ]
    return analyzer


class TestLearningBasedOptimizerInitialization:
    """LearningBasedOptimizer 初期化テスト"""

    def test_initialization_basic(self, mock_config):
        """基本的な初期化テスト"""
        optimizer = LearningBasedOptimizer(mock_config)

        assert optimizer.config == mock_config
        assert optimizer.logger is not None
        assert optimizer.adaptive_manager is None  # 遅延初期化
        assert optimizer.efficiency_analyzer is None

        # 学習型最適化専用設定の確認
        assert optimizer.learning_enabled is True
        assert optimizer.ab_testing_enabled is True
        assert optimizer.auto_optimization_threshold == 0.03

        # 学習履歴の初期化確認
        assert isinstance(optimizer.learning_sessions, deque)
        assert len(optimizer.learning_sessions) == 0
        assert optimizer.learning_sessions.maxlen == 50

        assert isinstance(optimizer.optimization_results, deque)
        assert len(optimizer.optimization_results) == 0
        assert optimizer.optimization_results.maxlen == 100

        # 学習型最適化メトリクスの初期化確認
        expected_metrics = {
            "patterns_learned": 0,
            "optimizations_applied": 0,
            "ab_tests_completed": 0,
            "total_improvement": 0.0,
            "last_learning_session": None,
        }
        assert optimizer.learning_metrics == expected_metrics

    def test_initialization_with_adaptive_manager(
        self, mock_config, mock_adaptive_manager
    ):
        """AdaptiveSettingsManagerありの初期化テスト"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)

        assert optimizer.adaptive_manager == mock_adaptive_manager
        assert optimizer.config == mock_config

    def test_initialize_adaptive_manager_lazy(self, mock_config):
        """AdaptiveSettingsManagerの遅延初期化テスト"""
        optimizer = LearningBasedOptimizer(mock_config)

        # 初期状態ではNone
        assert optimizer.adaptive_manager is None

        with patch(
            "kumihan_formatter.core.optimization.settings.manager.AdaptiveSettingsManager"
        ) as mock_adaptive_class:
            mock_adaptive_instance = Mock()
            mock_adaptive_class.return_value = mock_adaptive_instance

            # 遅延初期化実行
            optimizer._initialize_adaptive_manager()

            # AdaptiveSettingsManagerが初期化されることを確認
            mock_adaptive_class.assert_called_once_with(mock_config)
            assert optimizer.adaptive_manager == mock_adaptive_instance

    def test_integrate_efficiency_analyzer(self, mock_config, mock_efficiency_analyzer):
        """TokenEfficiencyAnalyzer統合テスト"""
        optimizer = LearningBasedOptimizer(mock_config)

        # 統合前は None
        assert optimizer.efficiency_analyzer is None

        # 統合実行
        optimizer.integrate_efficiency_analyzer(mock_efficiency_analyzer)

        # 統合後は設定済み
        assert optimizer.efficiency_analyzer == mock_efficiency_analyzer


class TestLearningBasedOptimizerLearningCycle:
    """LearningBasedOptimizer 学習サイクルテスト"""

    @pytest.fixture
    def optimizer_with_mocks(
        self, mock_config, mock_adaptive_manager, mock_efficiency_analyzer
    ):
        """モック付きオプティマイザー"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)
        optimizer.integrate_efficiency_analyzer(mock_efficiency_analyzer)
        return optimizer

    def test_run_learning_cycle_success(self, optimizer_with_mocks):
        """正常な学習サイクル実行テスト"""
        optimizer = optimizer_with_mocks

        with (
            patch.object(optimizer, "_integrate_learning_data") as mock_integrate,
            patch.object(
                optimizer, "_generate_optimization_proposals"
            ) as mock_generate,
            patch.object(optimizer, "_apply_automatic_optimizations") as mock_apply,
            patch.object(optimizer, "_setup_ab_tests") as mock_setup_ab,
        ):

            # モックの戻り値設定
            mock_integrate.return_value = {"integrated": "data"}
            mock_generate.return_value = [
                {"pattern": "test", "expected_improvement": 0.05}
            ]

            from kumihan_formatter.core.config.optimization.manager import (
                ConfigAdjustment,
            )

            mock_adjustment = ConfigAdjustment(
                key="test.key",
                old_value=100,
                new_value=200,
                context="test",
                timestamp=time.time(),
                reason="test",
                expected_benefit=0.05,
            )
            mock_apply.return_value = [mock_adjustment]
            mock_setup_ab.return_value = ["ab_test_1"]

            # 学習サイクル実行
            result = optimizer.run_learning_cycle()

            # 結果の検証
            assert result["status"] == "completed"
            assert result["patterns_analyzed"] == 3
            assert result["optimizations_applied"] == 1
            assert result["ab_tests_started"] == 1
            assert result["expected_improvement"] == 0.05
            assert "timestamp" in result
            assert "duration" in result

            # 履歴に記録されることを確認
            assert len(optimizer.learning_sessions) == 1
            assert optimizer.learning_sessions[0] == result

            # メトリクスが更新されることを確認
            assert optimizer.learning_metrics["patterns_learned"] == 3
            assert optimizer.learning_metrics["optimizations_applied"] == 1

    def test_run_learning_cycle_exception_handling(self, optimizer_with_mocks):
        """学習サイクル例外処理テスト"""
        optimizer = optimizer_with_mocks

        with patch.object(
            optimizer.adaptive_manager,
            "learn_usage_patterns",
            side_effect=Exception("Test error"),
        ):
            # 例外発生時の学習サイクル実行
            result = optimizer.run_learning_cycle()

            # エラー結果の検証
            assert result["status"] == "failed"
            assert result["error"] == "Test error"
            assert "timestamp" in result
            assert "duration" in result

    def test_force_learning_cycle(self, optimizer_with_mocks):
        """強制学習サイクル実行テスト"""
        optimizer = optimizer_with_mocks

        with patch.object(optimizer, "run_learning_cycle") as mock_run:
            mock_run.return_value = {"status": "completed"}

            # 強制学習サイクル実行
            result = optimizer.force_learning_cycle()

            # run_learning_cycleが呼ばれることを確認
            mock_run.assert_called_once()
            assert result == {"status": "completed"}


class TestLearningBasedOptimizerDataIntegration:
    """LearningBasedOptimizer データ統合テスト"""

    @pytest.fixture
    def optimizer_with_analyzer(self, mock_config, mock_efficiency_analyzer):
        """効率性アナライザー付きオプティマイザー"""
        optimizer = LearningBasedOptimizer(mock_config)
        optimizer.integrate_efficiency_analyzer(mock_efficiency_analyzer)
        return optimizer

    def test_integrate_learning_data_with_analyzer(self, optimizer_with_analyzer):
        """効率性アナライザーありのデータ統合テスト"""
        optimizer = optimizer_with_analyzer

        learning_summary = {
            "efficiency_insights": {
                "parsing_medium": {
                    "efficiency_score": 0.5,
                    "sample_count": 12,
                },
                "rendering_large": {
                    "efficiency_score": 0.3,
                    "sample_count": 8,
                },
            },
            "optimization_opportunities": [
                {
                    "pattern": "parsing_medium",
                    "recommendations": [
                        {
                            "type": "max_answer_chars_reduction",
                            "expected_improvement": 0.06,
                        }
                    ],
                }
            ],
        }

        efficiency_insights = {
            "pattern_rankings": {
                "parsing_medium": 0.7,
                "rendering_large": 0.4,
            }
        }

        # データ統合実行
        result = optimizer._integrate_learning_data(
            learning_summary, efficiency_insights
        )

        # 統合結果の検証
        assert "high_priority_patterns" in result
        assert "optimization_opportunities" in result
        assert "confidence_scores" in result

        # 高優先度パターンの検証
        high_priority = result["high_priority_patterns"]
        assert len(high_priority) > 0

        for pattern in high_priority:
            assert "pattern" in pattern
            assert "integrated_score" in pattern
            assert "confidence" in pattern

    def test_integrate_learning_data_without_analyzer(self, mock_config):
        """効率性アナライザーなしのデータ統合テスト"""
        optimizer = LearningBasedOptimizer(mock_config)
        # analyzer は None

        learning_summary = {
            "efficiency_insights": {
                "parsing_medium": {
                    "efficiency_score": 0.5,
                    "sample_count": 10,
                }
            },
            "optimization_opportunities": [
                {
                    "pattern": "parsing_medium",
                    "recommendations": [
                        {
                            "type": "max_answer_chars_reduction",
                            "expected_improvement": 0.04,
                        }
                    ],
                }
            ],
        }

        efficiency_insights = {}

        # データ統合実行
        result = optimizer._integrate_learning_data(
            learning_summary, efficiency_insights
        )

        # 基本的な統合が行われることを確認
        assert "high_priority_patterns" in result
        assert "optimization_opportunities" in result
        assert len(result["optimization_opportunities"]) > 0


class TestLearningBasedOptimizerProposalGeneration:
    """LearningBasedOptimizer 提案生成テスト"""

    @pytest.fixture
    def optimizer(self, mock_config):
        """基本オプティマイザー"""
        return LearningBasedOptimizer(mock_config)

    def test_generate_optimization_proposals_basic(self, optimizer):
        """基本的な最適化提案生成テスト"""
        integrated_analysis = {
            "optimization_opportunities": [
                {
                    "pattern": "parsing_medium",
                    "recommendations": [
                        {
                            "type": "max_answer_chars_reduction",
                            "expected_improvement": 0.08,
                        },
                        {
                            "type": "memory_optimization",
                            "expected_improvement": 0.02,  # 閾値未満
                        },
                    ],
                },
                {
                    "pattern": "rendering_large",
                    "recommendations": [
                        {
                            "type": "cache_optimization",
                            "expected_improvement": 0.04,
                        }
                    ],
                },
            ],
            "confidence_scores": {
                "parsing_medium": 0.8,
                "rendering_large": 0.6,
            },
        }

        # 提案生成実行
        proposals = optimizer._generate_optimization_proposals(integrated_analysis)

        # 提案の検証
        assert isinstance(proposals, list)
        assert len(proposals) >= 1

        # 閾値以上の提案のみ含まれることを確認
        for proposal in proposals:
            assert (
                proposal["expected_improvement"]
                >= optimizer.auto_optimization_threshold
            )
            assert "pattern" in proposal
            assert "type" in proposal
            assert "confidence" in proposal
            assert "auto_apply" in proposal
            assert "ab_test_candidate" in proposal

        # 期待改善率でソートされることを確認
        improvements = [p["expected_improvement"] for p in proposals]
        assert improvements == sorted(improvements, reverse=True)

    def test_generate_optimization_proposals_auto_apply_logic(self, optimizer):
        """自動適用ロジックテスト"""
        integrated_analysis = {
            "optimization_opportunities": [
                {
                    "pattern": "high_improvement",
                    "recommendations": [
                        {
                            "type": "optimization",
                            "expected_improvement": 0.06,  # 5%以上で自動適用
                        }
                    ],
                },
                {
                    "pattern": "medium_improvement",
                    "recommendations": [
                        {
                            "type": "optimization",
                            "expected_improvement": 0.04,  # 3-5%でA/Bテスト
                        }
                    ],
                },
            ],
            "confidence_scores": {
                "high_improvement": 0.8,
                "medium_improvement": 0.7,
            },
        }

        proposals = optimizer._generate_optimization_proposals(integrated_analysis)

        # 自動適用フラグの確認
        high_improvement_proposal = next(
            p for p in proposals if p["pattern"] == "high_improvement"
        )
        assert high_improvement_proposal["auto_apply"] is True
        assert high_improvement_proposal["ab_test_candidate"] is False

        medium_improvement_proposal = next(
            p for p in proposals if p["pattern"] == "medium_improvement"
        )
        assert medium_improvement_proposal["auto_apply"] is False
        assert medium_improvement_proposal["ab_test_candidate"] is True


class TestLearningBasedOptimizerAutomaticOptimizations:
    """LearningBasedOptimizer 自動最適化テスト"""

    @pytest.fixture
    def optimizer_with_manager(self, mock_config, mock_adaptive_manager):
        """AdaptiveSettingsManager付きオプティマイザー"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)
        return optimizer

    def test_apply_automatic_optimizations_success(self, optimizer_with_manager):
        """自動最適化適用成功テスト"""
        optimizer = optimizer_with_manager

        proposals = [
            {
                "pattern": "parsing_medium",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.08,
                "confidence": 0.7,
                "auto_apply": True,
                "ab_test_candidate": False,
            },
            {
                "pattern": "low_confidence",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.06,
                "confidence": 0.5,  # 閾値未満
                "auto_apply": True,
                "ab_test_candidate": False,
            },
            {
                "pattern": "no_auto_apply",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.04,
                "confidence": 0.8,
                "auto_apply": False,  # 自動適用対象外
                "ab_test_candidate": True,
            },
        ]

        with patch(
            "kumihan_formatter.core.optimization.settings.manager.ConfigAdjustment"
        ) as mock_config_adjustment_class:
            from kumihan_formatter.core.config.optimization.manager import (
                ConfigAdjustment,
            )

            mock_adjustment = ConfigAdjustment(
                key="serena.max_answer_chars",
                old_value=25000,
                new_value=20000,
                context="learning_based_auto_parsing_medium",
                timestamp=time.time(),
                reason="LearningBasedOptimizer auto-optimization: 8.0% expected",
                expected_benefit=0.08,
            )
            mock_config_adjustment_class.return_value = mock_adjustment

            # 自動最適化適用実行
            applied = optimizer._apply_automatic_optimizations(proposals)

            # 適用結果の検証
            assert isinstance(applied, list)
            assert len(applied) == 1  # confidence > 0.6 かつ auto_apply のみ

            # AdaptiveSettingsManagerの_apply_adjustmentが呼ばれることを確認
            optimizer.adaptive_manager._apply_adjustment.assert_called_once()

    def test_apply_automatic_optimizations_max_answer_chars_logic(
        self, optimizer_with_manager
    ):
        """max_answer_chars削減ロジックテスト"""
        optimizer = optimizer_with_manager

        # config.get の戻り値を動的に設定するように変更
        def mock_get(key, default=None):
            config_values = {
                "serena.max_answer_chars": 30000,  # テスト用に30000に設定
                "performance.max_recursion_depth": 50,
                "cache.templates": True,
                "monitoring.interval": 30,
                "optimization.max_concurrent_tools": 5,
            }
            return config_values.get(key, default)

        optimizer.config.get.side_effect = mock_get

        proposals = [
            {
                "pattern": "test_pattern",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.08,
                "confidence": 0.8,
                "auto_apply": True,
                "ab_test_candidate": False,
            }
        ]

        with patch(
            "kumihan_formatter.core.optimization.settings.manager.ConfigAdjustment"
        ) as mock_config_adjustment_class:
            # ConfigAdjustmentのモック設定（specを使わずに単純なMock）
            mock_adjustment = Mock()
            mock_config_adjustment_class.return_value = mock_adjustment

            applied = optimizer._apply_automatic_optimizations(proposals)

            # ConfigAdjustmentが適切な値で呼ばれることを確認
            call_args = mock_config_adjustment_class.call_args
            assert call_args[1]["key"] == "serena.max_answer_chars"
            assert call_args[1]["old_value"] == 30000
            assert call_args[1]["new_value"] == max(
                15000, int(30000 * 0.8)
            )  # 20%削減、最低15000  # 20%削減、最低15000  # 20%削減、最低15000


class TestLearningBasedOptimizerABTests:
    """LearningBasedOptimizer A/Bテストテスト"""

    @pytest.fixture
    def optimizer_with_ab_enabled(self, mock_config, mock_adaptive_manager):
        """A/Bテスト有効なオプティマイザー"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)
        optimizer.ab_testing_enabled = True
        return optimizer

    def test_setup_ab_tests_success(self, optimizer_with_ab_enabled):
        """A/Bテスト設定成功テスト"""
        optimizer = optimizer_with_ab_enabled

        proposals = [
            {
                "pattern": "ab_test_candidate",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.04,
                "confidence": 0.7,
                "auto_apply": False,
                "ab_test_candidate": True,
            },
            {
                "pattern": "no_ab_test",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.08,
                "confidence": 0.7,
                "auto_apply": True,
                "ab_test_candidate": False,  # A/Bテスト対象外
            },
        ]

        # A/Bテスト設定実行
        started_tests = optimizer._setup_ab_tests(proposals)

        # 設定結果の検証
        assert isinstance(started_tests, list)
        assert len(started_tests) == 1
        assert "serena.max_answer_chars" in started_tests

        # AdaptiveSettingsManagerのrun_simple_ab_testが呼ばれることを確認
        optimizer.adaptive_manager.run_simple_ab_test.assert_called_once()

    def test_setup_ab_tests_disabled(self, optimizer_with_ab_enabled):
        """A/Bテスト無効時のテスト"""
        optimizer = optimizer_with_ab_enabled
        optimizer.ab_testing_enabled = False

        proposals = [
            {
                "pattern": "ab_test_candidate",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.04,
                "confidence": 0.7,
                "auto_apply": False,
                "ab_test_candidate": True,
            }
        ]

        # A/Bテスト設定実行
        started_tests = optimizer._setup_ab_tests(proposals)

        # A/Bテストが設定されないことを確認
        assert len(started_tests) == 0
        optimizer.adaptive_manager.run_simple_ab_test.assert_not_called()

    def test_setup_ab_tests_value_calculation(self, optimizer_with_ab_enabled):
        """A/Bテスト値計算テスト"""
        optimizer = optimizer_with_ab_enabled
        optimizer.config.get.return_value = 20000  # ベース値

        proposals = [
            {
                "pattern": "value_test",
                "type": "max_answer_chars_reduction",
                "expected_improvement": 0.04,
                "confidence": 0.7,
                "auto_apply": False,
                "ab_test_candidate": True,
            }
        ]

        started_tests = optimizer._setup_ab_tests(proposals)

        # run_simple_ab_testが期待される値で呼ばれることを確認
        call_args = optimizer.adaptive_manager.run_simple_ab_test.call_args
        parameter, test_values, sample_size = call_args[0]

        assert parameter == "serena.max_answer_chars"
        assert test_values == [
            20000,
            int(20000 * 0.9),
            int(20000 * 0.8),
        ]  # 元値、10%削減、20%削減
        assert sample_size == 8


class TestLearningBasedOptimizerStatus:
    """LearningBasedOptimizer ステータステスト"""

    @pytest.fixture
    def optimizer_with_history(self, mock_config, mock_adaptive_manager):
        """履歴付きオプティマイザー"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)

        # 学習メトリクスにデータを設定
        optimizer.learning_metrics.update(
            {
                "patterns_learned": 5,
                "optimizations_applied": 3,
                "ab_tests_completed": 2,
                "total_improvement": 0.12,
                "last_learning_session": time.time() - 1800,  # 30分前
            }
        )

        # 学習セッション履歴を追加
        for i in range(3):
            session = {
                "timestamp": time.time() - (i * 3600),
                "duration": 0.5,
                "patterns_analyzed": 2,
                "optimizations_applied": 1,
                "status": "completed",
            }
            optimizer.learning_sessions.append(session)

        return optimizer

    def test_get_learning_status_full(self, optimizer_with_history):
        """完全な学習ステータス取得テスト"""
        optimizer = optimizer_with_history

        # ステータス取得
        status = optimizer.get_learning_status()

        # 基本メトリクスの検証
        assert status["learning_metrics"]["patterns_learned"] == 5
        assert status["learning_metrics"]["optimizations_applied"] == 3
        assert status["learning_metrics"]["ab_tests_completed"] == 2
        assert status["learning_metrics"]["total_improvement"] == 0.12

        # AdaptiveSettingsManagerのステータスが含まれることを確認
        assert "learning_status" in status
        optimizer.adaptive_manager.get_learning_status.assert_called_once()

        # 総合削減率計算の検証
        assert "total_reduction_achieved" in status
        expected_total = 0.618 + min(
            0.12, 0.1
        )  # 統合設定最適化 + 学習追加分（上限10%）
        assert status["total_reduction_achieved"] == expected_total

        # 目標進捗の検証
        target_progress = status["target_progress"]
        assert target_progress["integrated_baseline"] == 0.618
        assert target_progress["learning_target"] == 0.05
        assert target_progress["learning_actual"] == 0.1  # min(0.12, 0.1)
        assert target_progress["remaining_to_target"] == 0.0  # max(0, 0.05 - 0.1)

        # その他のステータス項目
        assert status["learning_sessions_count"] == 3
        assert status["recent_learning_active"] is True  # 30分前 < 1時間

    def test_get_learning_status_no_recent_activity(self, optimizer_with_history):
        """最近の学習活動なしの場合のテスト"""
        optimizer = optimizer_with_history
        optimizer.learning_metrics["last_learning_session"] = (
            time.time() - 7200
        )  # 2時間前

        status = optimizer.get_learning_status()

        # 最近の学習活動がないことを確認
        assert status["recent_learning_active"] is False

    def test_get_learning_status_no_learning_session_history(
        self, mock_config, mock_adaptive_manager
    ):
        """学習セッション履歴がない場合のテスト"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)

        status = optimizer.get_learning_status()

        # デフォルト値での動作確認
        assert status["learning_metrics"]["patterns_learned"] == 0
        assert status["learning_metrics"]["total_improvement"] == 0.0
        assert status["learning_metrics"]["last_learning_session"] is None
        assert status["recent_learning_active"] is False

    def test_update_learning_metrics(self, mock_config):
        """学習メトリクス更新テスト"""
        optimizer = LearningBasedOptimizer(mock_config)

        cycle_result = {
            "patterns_analyzed": 3,
            "optimizations_applied": 2,
            "ab_tests_started": 1,
            "expected_improvement": 0.06,
            "timestamp": time.time(),
        }

        # 初期状態の確認
        initial_metrics = optimizer.learning_metrics.copy()
        assert initial_metrics["patterns_learned"] == 0

        # メトリクス更新実行
        optimizer._update_learning_metrics(cycle_result)

        # 更新結果の確認
        updated_metrics = optimizer.learning_metrics
        assert (
            updated_metrics["patterns_learned"]
            == initial_metrics["patterns_learned"] + 3
        )
        assert (
            updated_metrics["optimizations_applied"]
            == initial_metrics["optimizations_applied"] + 2
        )
        assert (
            updated_metrics["ab_tests_completed"]
            == initial_metrics["ab_tests_completed"] + 1
        )
        assert (
            updated_metrics["total_improvement"]
            == initial_metrics["total_improvement"] + 0.06
        )
        assert updated_metrics["last_learning_session"] == cycle_result["timestamp"]


class TestLearningBasedOptimizerErrorHandling:
    """LearningBasedOptimizer エラーハンドリングテスト"""

    @pytest.fixture
    def optimizer_with_failing_dependencies(self, mock_config):
        """依存関係が失敗するオプティマイザー"""
        failing_manager = Mock()
        failing_manager.learn_usage_patterns.side_effect = Exception("Manager error")
        failing_manager.get_learning_status.side_effect = Exception("Status error")
        failing_manager._apply_adjustment.side_effect = Exception("Apply error")

        optimizer = LearningBasedOptimizer(mock_config, failing_manager)
        return optimizer

    def test_run_learning_cycle_with_manager_error(
        self, optimizer_with_failing_dependencies
    ):
        """AdaptiveSettingsManagerエラー時の学習サイクルテスト"""
        optimizer = optimizer_with_failing_dependencies

        # エラーが発生する学習サイクル実行
        result = optimizer.run_learning_cycle()

        # エラーハンドリングの確認
        assert result["status"] == "failed"
        assert "Manager error" in result["error"]
        assert "timestamp" in result
        assert "duration" in result

    def test_get_learning_status_with_manager_error(
        self, optimizer_with_failing_dependencies
    ):
        """AdaptiveSettingsManagerエラー時のステータス取得テスト"""
        optimizer = optimizer_with_failing_dependencies

        # エラーが発生してもプログラムが停止しないことを確認
        try:
            status = optimizer.get_learning_status()
            # エラーが発生した場合でも基本的な応答があることを確認
            assert "learning_metrics" in status
        except Exception as e:
            # 例外が適切にハンドリングされることを確認
            assert "Status error" in str(e)

    def test_invalid_configuration_handling(self, mock_config):
        """不正な設定での動作テスト"""
        # 不正な値を返すコンフィグ
        mock_config.get.return_value = "invalid_value"

        optimizer = LearningBasedOptimizer(mock_config)

        # 不正な設定でも初期化が完了することを確認
        assert optimizer.config == mock_config

    def test_empty_data_handling(self, mock_config, mock_adaptive_manager):
        """空データでの処理テスト"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)

        # 空の学習結果を設定
        mock_adaptive_manager.learn_usage_patterns.return_value = {
            "patterns_discovered": 0,
            "efficiency_insights": {},
            "optimization_opportunities": [],
        }

        # 空データでの学習サイクル実行
        result = optimizer.run_learning_cycle()

        # 正常に完了することを確認
        assert result["status"] == "completed"
        assert result["patterns_analyzed"] == 0
        assert result["optimizations_applied"] == 0


class TestLearningBasedOptimizerPerformance:
    """LearningBasedOptimizer パフォーマンステスト"""

    @pytest.fixture
    def performance_optimizer(
        self, mock_config, mock_adaptive_manager, mock_efficiency_analyzer
    ):
        """パフォーマンステスト用オプティマイザー"""
        optimizer = LearningBasedOptimizer(mock_config, mock_adaptive_manager)
        optimizer.integrate_efficiency_analyzer(mock_efficiency_analyzer)
        return optimizer

    def test_learning_cycle_performance(self, performance_optimizer):
        """学習サイクルパフォーマンステスト"""
        optimizer = performance_optimizer

        start_time = time.time()

        # 学習サイクルを複数回実行
        results = []
        for _ in range(5):
            result = optimizer.run_learning_cycle()
            results.append(result)

        end_time = time.time()
        elapsed = end_time - start_time

        # パフォーマンス要件の確認（5回実行が2秒以内）
        assert elapsed < 2.0, f"Performance test took too long: {elapsed:.3f}s"

        # すべての実行が完了していることを確認
        for result in results:
            assert result["status"] == "completed"

    def test_memory_usage_deque_limits(self, performance_optimizer):
        """deque制限によるメモリ使用量テスト"""
        optimizer = performance_optimizer

        # 大量のセッションデータを追加
        for i in range(100):  # maxlen=50を超える数
            session = {
                "timestamp": time.time() - i,
                "duration": 0.1,
                "status": "completed",
            }
            optimizer.learning_sessions.append(session)

        # deque制限が機能していることを確認
        assert len(optimizer.learning_sessions) == 50  # maxlen通り

        # 大量の最適化結果を追加
        for i in range(150):  # maxlen=100を超える数
            result = {
                "timestamp": time.time() - i,
                "improvement": 0.01,
            }
            optimizer.optimization_results.append(result)

        # deque制限が機能していることを確認
        assert len(optimizer.optimization_results) == 100  # maxlen通り

    def test_large_data_processing(self, performance_optimizer):
        """大容量データ処理テスト"""
        optimizer = performance_optimizer

        # 大量のパターンデータでテスト
        large_learning_summary = {
            "patterns_discovered": 50,
            "efficiency_insights": {
                f"pattern_{i}": {
                    "efficiency_score": 0.5 + (i % 10) * 0.05,
                    "sample_count": 10 + (i % 20),
                }
                for i in range(100)  # 100パターン
            },
            "optimization_opportunities": [
                {
                    "pattern": f"pattern_{i}",
                    "recommendations": [
                        {
                            "type": "optimization",
                            "expected_improvement": 0.03 + (i % 10) * 0.01,
                        }
                    ],
                }
                for i in range(50)  # 50機会
            ],
        }

        large_efficiency_insights = {
            "pattern_rankings": {
                f"pattern_{i}": 0.3 + (i % 10) * 0.07 for i in range(100)
            }
        }

        start_time = time.time()

        # 大容量データでの統合処理
        result = optimizer._integrate_learning_data(
            large_learning_summary, large_efficiency_insights
        )

        end_time = time.time()
        processing_time = end_time - start_time

        # 処理時間の確認（1秒以内）
        assert (
            processing_time < 1.0
        ), f"Large data processing took too long: {processing_time:.3f}s"

        # 結果の基本検証
        assert isinstance(result, dict)
        assert "high_priority_patterns" in result
        assert "optimization_opportunities" in result


class TestLearningBasedOptimizerIntegration:
    """LearningBasedOptimizer 統合テスト"""

    @pytest.fixture
    def full_integration_optimizer(self, mock_config):
        """完全統合テスト用オプティマイザー"""
        # リアルに近いAdaptiveSettingsManagerモック
        adaptive_manager = Mock()
        adaptive_manager.learn_usage_patterns.return_value = {
            "patterns_discovered": 4,
            "efficiency_insights": {
                "parsing_large": {"efficiency_score": 0.4, "sample_count": 15},
                "rendering_medium": {"efficiency_score": 0.6, "sample_count": 12},
                "optimization_small": {"efficiency_score": 0.8, "sample_count": 8},
            },
            "optimization_opportunities": [
                {
                    "pattern": "parsing_large",
                    "recommendations": [
                        {
                            "type": "max_answer_chars_reduction",
                            "expected_improvement": 0.09,
                        },
                    ],
                },
                {
                    "pattern": "rendering_medium",
                    "recommendations": [
                        {"type": "cache_optimization", "expected_improvement": 0.04},
                    ],
                },
            ],
        }
        adaptive_manager.get_learning_status.return_value = {
            "total_context_patterns": 10,
            "learned_patterns": 4,
            "learning_coverage": 0.4,
        }
        adaptive_manager.run_simple_ab_test.return_value = "ab_test_integration_001"
        adaptive_manager._apply_adjustment.return_value = None

        # TokenEfficiencyAnalyzer モック
        efficiency_analyzer = Mock()
        efficiency_analyzer.get_pattern_insights.return_value = {
            "pattern_rankings": {
                "parsing_large": 0.3,
                "rendering_medium": 0.7,
                "optimization_small": 0.9,
            }
        }
        efficiency_analyzer.auto_suggest_optimizations.return_value = [
            {
                "pattern": "new_integrated_pattern",
                "type": "memory_optimization",
                "expected_improvement": 0.03,
            }
        ]

        # オプティマイザー構築
        optimizer = LearningBasedOptimizer(mock_config, adaptive_manager)
        optimizer.integrate_efficiency_analyzer(efficiency_analyzer)

        return optimizer

    def test_full_workflow_integration(self, full_integration_optimizer):
        """完全ワークフロー統合テスト"""
        optimizer = full_integration_optimizer

        # 1. 学習サイクル実行
        with patch(
            "kumihan_formatter.core.optimization.settings.manager.ConfigAdjustment"
        ) as mock_adjustment:
            from kumihan_formatter.core.config.optimization.manager import (
                ConfigAdjustment,
            )

            mock_adj_instance = ConfigAdjustment(
                key="serena.max_answer_chars",
                old_value=25000,
                new_value=20000,
                context="learning_based_auto_parsing_large",
                timestamp=time.time(),
                reason="LearningBasedOptimizer auto-optimization: 9.0% expected",
                expected_benefit=0.09,
            )
            mock_adjustment.return_value = mock_adj_instance

            cycle_result = optimizer.run_learning_cycle()

        # 2. 学習サイクル結果の検証
        assert cycle_result["status"] == "completed"
        assert cycle_result["patterns_analyzed"] == 4
        assert cycle_result["optimizations_applied"] >= 1
        assert cycle_result["ab_tests_started"] >= 1
        assert cycle_result["expected_improvement"] > 0

        # 3. 学習履歴の確認
        assert len(optimizer.learning_sessions) == 1
        assert optimizer.learning_sessions[0] == cycle_result

        # 4. 学習メトリクス確認
        assert optimizer.learning_metrics["patterns_learned"] == 4
        assert optimizer.learning_metrics["optimizations_applied"] >= 1
        assert optimizer.learning_metrics["total_improvement"] > 0

        # 5. 学習ステータス取得
        status = optimizer.get_learning_status()
        assert status["learning_metrics"]["patterns_learned"] == 4
        assert status["total_reduction_achieved"] > 0.618  # 統合最適化ベースライン以上
        assert status["learning_sessions_count"] == 1

        # 6. 強制学習サイクルテスト
        force_result = optimizer.force_learning_cycle()
        assert force_result["status"] == "completed"
        assert len(optimizer.learning_sessions) == 2

    def test_multi_cycle_learning_progression(self, full_integration_optimizer):
        """複数サイクル学習進捗テスト"""
        optimizer = full_integration_optimizer

        # 複数の学習サイクルを実行
        cycle_results = []
        with patch(
            "kumihan_formatter.core.optimization.settings.manager.ConfigAdjustment"
        ) as mock_adjustment:
            from kumihan_formatter.core.config.optimization.manager import (
                ConfigAdjustment,
            )

            for i in range(3):
                mock_adj_instance = ConfigAdjustment(
                    key=f"test.key_{i}",
                    old_value=100,
                    new_value=90,
                    context=f"learning_cycle_{i}",
                    timestamp=time.time(),
                    reason=f"Learning cycle {i}",
                    expected_benefit=0.05,
                )
                mock_adjustment.return_value = mock_adj_instance

                result = optimizer.run_learning_cycle()
                cycle_results.append(result)
                time.sleep(0.01)  # タイムスタンプ重複回避

        # 学習進捗の確認
        assert len(optimizer.learning_sessions) == 3
        assert optimizer.learning_metrics["patterns_learned"] == 12  # 4 * 3
        assert optimizer.learning_metrics["total_improvement"] > 0

        # 各サイクルが正常に完了していることを確認
        for i, result in enumerate(cycle_results):
            assert result["status"] == "completed"
            assert f"learning_cycle_{i}" in str(optimizer.learning_sessions)

        # 最終ステータスの確認
        final_status = optimizer.get_learning_status()
        assert final_status["learning_sessions_count"] == 3
        assert final_status["learning_metrics"]["patterns_learned"] == 12

    def test_error_recovery_integration(self, mock_config):
        """エラー回復統合テスト"""
        # エラーを発生させるマネージャー
        failing_manager = Mock()
        failing_manager.learn_usage_patterns.side_effect = [
            Exception("First error"),  # 最初はエラー
            {  # 2回目は成功
                "patterns_discovered": 2,
                "efficiency_insights": {
                    "recovery_pattern": {"efficiency_score": 0.7, "sample_count": 5}
                },
                "optimization_opportunities": [],
            },
        ]
        failing_manager.get_learning_status.return_value = {
            "total_context_patterns": 2,
            "learned_patterns": 1,
            "learning_coverage": 0.5,
        }

        optimizer = LearningBasedOptimizer(mock_config, failing_manager)

        # 1回目：エラー発生
        result1 = optimizer.run_learning_cycle()
        assert result1["status"] == "failed"
        assert "First error" in result1["error"]

        # 2回目：エラー回復して成功
        result2 = optimizer.run_learning_cycle()
        assert result2["status"] == "completed"
        assert result2["patterns_analyzed"] == 2

        # エラー回復が機能していることを確認
        assert len(optimizer.learning_sessions) == 2
        assert optimizer.learning_sessions[0]["status"] == "failed"
        assert optimizer.learning_sessions[1]["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
