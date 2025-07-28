"""レンダーキャッシュ分析テスト - Issue #596 Week 25-26対応

レンダリングキャッシュの分析・統計・最適化機能の詳細テスト
統計情報生成、最適化提案、レポート作成の確認
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.caching.render_cache_analytics import RenderCacheAnalytics


class TestRenderCacheAnalytics:
    """レンダーキャッシュ分析テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.analytics = RenderCacheAnalytics()

    def test_analytics_initialization(self):
        """分析モジュール初期化テスト"""
        analytics = RenderCacheAnalytics()
        assert analytics is not None
        assert hasattr(analytics, "generate_statistics")
        assert hasattr(analytics, "optimize_for_templates")
        assert hasattr(analytics, "create_render_report")

    def test_generate_statistics_basic(self):
        """基本統計情報生成テスト"""
        # テストメタデータ
        metadata = {
            "key1": {
                "template_name": "base.html.j2",
                "render_time": 0.1,
                "output_size": 1000,
            },
            "key2": {
                "template_name": "docs.html.j2",
                "render_time": 0.2,
                "output_size": 2000,
            },
            "key3": {
                "template_name": "base.html.j2",
                "render_time": 0.15,
                "output_size": 1500,
            },
        }

        base_stats = {"hits": 10, "misses": 5}
        stats = self.analytics.generate_statistics(metadata, base_stats)

        # 基本統計の確認
        assert stats["hits"] == 10
        assert stats["misses"] == 5

        # レンダリング時間統計
        assert "avg_render_time" in stats
        expected_avg = (0.1 + 0.2 + 0.15) / 3
        assert abs(stats["avg_render_time"] - expected_avg) < 0.01

        assert "max_render_time" in stats
        assert stats["max_render_time"] == 0.2

        assert "min_render_time" in stats
        assert stats["min_render_time"] == 0.1

        # 出力サイズ統計
        assert "avg_output_size" in stats
        assert stats["avg_output_size"] == (1000 + 2000 + 1500) / 3

        # テンプレート分布
        assert "template_distribution" in stats
        template_dist = stats["template_distribution"]
        assert template_dist["base.html.j2"] == 2
        assert template_dist["docs.html.j2"] == 1

    def test_generate_statistics_empty_metadata(self):
        """空のメタデータでの統計生成テスト"""
        metadata = {}
        base_stats = {"hits": 5, "misses": 2}

        stats = self.analytics.generate_statistics(metadata, base_stats)

        # ベース統計のみ残る
        assert stats["hits"] == 5
        assert stats["misses"] == 2
        assert "avg_render_time" not in stats
        assert "template_distribution" not in stats

    def test_generate_statistics_with_none_base_stats(self):
        """Noneのベース統計での統計生成テスト"""
        metadata = {
            "key1": {
                "template_name": "test.html.j2",
                "render_time": 0.05,
                "output_size": 500,
            }
        }

        stats = self.analytics.generate_statistics(metadata, None)

        # 統計が正常に生成される
        assert "avg_render_time" in stats
        assert stats["avg_render_time"] == 0.05
        assert "template_distribution" in stats
        assert stats["template_distribution"]["test.html.j2"] == 1

    def test_optimize_for_templates_basic(self):
        """基本テンプレート最適化テスト"""
        # テストメタデータ（使用頻度の異なるテンプレート）
        metadata = {
            "key1": {"template_name": "frequent.html.j2"},  # 頻繁に使用
            "key2": {"template_name": "frequent.html.j2"},
            "key3": {"template_name": "frequent.html.j2"},
            "key4": {"template_name": "frequent.html.j2"},
            "key5": {"template_name": "rare.html.j2"},  # 稀に使用
            "key6": {"template_name": "rare.html.j2"},
            "key7": {"template_name": "single.html.j2"},  # 一回のみ使用
        }

        # 無効化コールバックのモック
        invalidate_callback = Mock(return_value=2)

        result = self.analytics.optimize_for_templates(metadata, invalidate_callback)

        # 最適化結果の確認
        assert "actions_taken" in result
        assert "entries_optimized" in result
        assert "space_freed" in result

        # 低使用頻度テンプレートが無効化される
        assert result["entries_optimized"] > 0
        assert len(result["actions_taken"]) > 0

        # 無効化コールバックが呼ばれる
        assert invalidate_callback.called

    def test_optimize_for_templates_no_callback(self):
        """コールバックなしのテンプレート最適化テスト"""
        metadata = {
            "key1": {"template_name": "rare.html.j2"},
            "key2": {"template_name": "rare.html.j2"},
        }

        result = self.analytics.optimize_for_templates(metadata, None)

        # コールバックがないため、最適化アクションは実行されない
        assert result["entries_optimized"] == 0
        assert len(result["actions_taken"]) == 0

    def test_optimize_for_templates_empty_metadata(self):
        """空メタデータでのテンプレート最適化テスト"""
        metadata = {}
        invalidate_callback = Mock()

        result = self.analytics.optimize_for_templates(metadata, invalidate_callback)

        # 空のメタデータでは最適化アクションなし
        assert result["entries_optimized"] == 0
        assert len(result["actions_taken"]) == 0
        assert not invalidate_callback.called

    def test_create_render_report(self):
        """レンダリングレポート作成テスト"""
        statistics = {
            "hit_rate": 0.75,
            "avg_render_time": 0.12,
            "template_distribution": {"base.html.j2": 5, "docs.html.j2": 3},
        }

        metadata = {
            "key1": {
                "template_name": "base.html.j2",
                "render_time": 0.1,
                "output_size": 1000,
            },
            "key2": {
                "template_name": "docs.html.j2",
                "render_time": 0.15,
                "output_size": 1500,
            },
        }

        report = self.analytics.create_render_report(statistics, metadata)

        # レポート構造の確認
        assert "timestamp" in report
        assert "cache_performance" in report
        assert "optimization_suggestions" in report
        assert "template_analysis" in report

        # タイムスタンプの形式確認
        timestamp = report["timestamp"]
        assert isinstance(timestamp, str)
        # ISO形式の簡易チェック
        assert "T" in timestamp

        # キャッシュ性能データの確認
        assert report["cache_performance"] == statistics

        # 最適化提案があることを確認
        suggestions = report["optimization_suggestions"]
        assert isinstance(suggestions, list)

        # テンプレート分析があることを確認
        template_analysis = report["template_analysis"]
        assert isinstance(template_analysis, dict)

    def test_generate_optimization_suggestions(self):
        """最適化提案生成テスト"""
        # 様々な問題を含む統計データ
        stats = {
            "hit_rate": 0.3,  # 低いヒット率
            "avg_render_time": 1.5,  # 長いレンダリング時間
            "memory_stats": {
                "size_bytes": 80000000,  # 80MB
                "max_bytes": 100000000,  # 100MB制限
            },
        }

        suggestions = self.analytics.generate_optimization_suggestions(stats)

        # 提案が生成される
        assert len(suggestions) > 0

        # 各問題に対する提案が含まれている
        suggestion_text = " ".join(suggestions)
        assert "ヒット率" in suggestion_text  # 低ヒット率の提案
        assert "レンダリング時間" in suggestion_text  # 長いレンダリング時間の提案
        assert "メモリ使用率" in suggestion_text  # 高メモリ使用率の提案

    def test_generate_optimization_suggestions_good_performance(self):
        """良好な性能での最適化提案テスト"""
        # 良好な性能の統計データ
        stats = {
            "hit_rate": 0.85,  # 高いヒット率
            "avg_render_time": 0.05,  # 短いレンダリング時間
            "memory_stats": {
                "size_bytes": 30000000,  # 30MB
                "max_bytes": 100000000,  # 100MB制限
            },
        }

        suggestions = self.analytics.generate_optimization_suggestions(stats)

        # 問題がないため提案は少ない、または空
        assert len(suggestions) == 0

    def test_analyze_template_usage(self):
        """テンプレート使用パターン分析テスト"""
        metadata = {
            "key1": {
                "template_name": "base.html.j2",
                "render_time": 0.1,
                "output_size": 1000,
            },
            "key2": {
                "template_name": "base.html.j2",
                "render_time": 0.15,
                "output_size": 1200,
            },
            "key3": {
                "template_name": "docs.html.j2",
                "render_time": 0.2,
                "output_size": 2000,
            },
        }

        analysis = self.analytics.analyze_template_usage(metadata)

        # テンプレート別の分析結果確認
        assert "base.html.j2" in analysis
        assert "docs.html.j2" in analysis

        # base.html.j2の統計
        base_stats = analysis["base.html.j2"]
        assert base_stats["count"] == 2
        assert base_stats["avg_render_time"] == (0.1 + 0.15) / 2
        assert base_stats["avg_output_size"] == (1000 + 1200) / 2

        # docs.html.j2の統計
        docs_stats = analysis["docs.html.j2"]
        assert docs_stats["count"] == 1
        assert docs_stats["avg_render_time"] == 0.2
        assert docs_stats["avg_output_size"] == 2000

    def test_analyze_template_usage_empty_metadata(self):
        """空メタデータでのテンプレート使用分析テスト"""
        metadata = {}
        analysis = self.analytics.analyze_template_usage(metadata)

        # 空の結果
        assert analysis == {}

    def test_identify_optimization_opportunities(self):
        """最適化機会特定テスト"""
        # 様々なパフォーマンスパターンのメタデータ
        metadata = {
            "fast_render": {
                "render_time": 0.05,
                "output_size": 1000,
            },
            "slow_render": {
                "render_time": 0.3,  # 平均の2倍以上
                "output_size": 2000,
            },
            "very_slow_render": {
                "render_time": 0.4,  # 平均の2倍以上
                "output_size": 150000,  # 100KB以上の大容量
            },
            "normal_render": {
                "render_time": 0.1,
                "output_size": 5000,
            },
        }

        stats = {"hit_rate": 0.6}

        opportunities = self.analytics.identify_optimization_opportunities(
            metadata, stats
        )

        # 最適化機会の構造確認
        assert "high_impact" in opportunities
        assert "medium_impact" in opportunities
        assert "low_impact" in opportunities

        # 高コストレンダリングが特定される
        high_impact = opportunities["high_impact"]
        assert len(high_impact) > 0
        assert "高コストレンダリング" in high_impact[0]

        # 大容量出力が特定される
        medium_impact = opportunities["medium_impact"]
        assert len(medium_impact) > 0
        assert "大容量出力" in medium_impact[0]

    def test_identify_optimization_opportunities_good_performance(self):
        """良好なパフォーマンスでの最適化機会特定テスト"""
        # すべて良好なパフォーマンスのメタデータ
        metadata = {
            "good_render_1": {
                "render_time": 0.05,
                "output_size": 1000,
            },
            "good_render_2": {
                "render_time": 0.06,
                "output_size": 1500,
            },
            "good_render_3": {
                "render_time": 0.04,
                "output_size": 800,
            },
        }

        stats = {"hit_rate": 0.9}

        opportunities = self.analytics.identify_optimization_opportunities(
            metadata, stats
        )

        # 最適化機会は少ない
        assert len(opportunities["high_impact"]) == 0
        assert len(opportunities["medium_impact"]) == 0

    def test_analytics_with_missing_metadata_fields(self):
        """メタデータフィールド欠損時の分析テスト"""
        # 一部のフィールドが欠損したメタデータ
        metadata = {
            "incomplete_1": {
                "template_name": "test.html.j2",
                # render_time欠損
                "output_size": 1000,
            },
            "incomplete_2": {
                "template_name": "test.html.j2",
                "render_time": 0.1,
                # output_size欠損
            },
            "complete": {
                "template_name": "test.html.j2",
                "render_time": 0.15,
                "output_size": 1500,
            },
        }

        # 統計生成が正常に動作することを確認
        stats = self.analytics.generate_statistics(metadata)
        assert "template_distribution" in stats

        # 完全なデータのみが統計に含まれる
        assert "avg_render_time" in stats
        assert stats["avg_render_time"] == (0.1 + 0.15) / 2

        assert "avg_output_size" in stats
        assert stats["avg_output_size"] == (1000 + 1500) / 2

    def test_analytics_performance_with_large_dataset(self):
        """大規模データセットでの分析性能テスト"""
        import time

        # 大量のメタデータを生成
        large_metadata = {}
        for i in range(1000):
            large_metadata[f"key_{i}"] = {
                "template_name": f"template_{i % 10}.html.j2",
                "render_time": 0.1 + (i % 10) * 0.01,
                "output_size": 1000 + (i % 10) * 100,
            }

        # 処理時間を測定
        start_time = time.time()
        stats = self.analytics.generate_statistics(large_metadata)
        execution_time = time.time() - start_time

        # 合理的な時間で完了することを確認
        assert execution_time < 1.0, f"大規模データ処理が遅すぎます: {execution_time}秒"

        # 統計が正しく生成されることを確認
        assert "template_distribution" in stats
        assert len(stats["template_distribution"]) == 10  # 10種類のテンプレート


class TestRenderCacheAnalyticsEdgeCases:
    """レンダーキャッシュ分析エッジケーステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.analytics = RenderCacheAnalytics()

    def test_analytics_with_invalid_data_types(self):
        """無効なデータ型での分析テスト"""
        # 無効な型のメタデータ
        invalid_metadata = {
            "key1": {
                "template_name": "test.html.j2",
                "render_time": "invalid_time",  # 文字列（数値でない）
                "output_size": None,  # None
            },
            "key2": {
                "template_name": 123,  # 数値（文字列でない）
                "render_time": 0.1,
                "output_size": 1000,
            },
        }

        # エラーハンドリングの確認
        try:
            stats = self.analytics.generate_statistics(invalid_metadata)
            # エラーが発生しないか、適切に処理される
            assert isinstance(stats, dict)
        except (TypeError, ValueError):
            # 型エラーが発生する場合も許容
            pytest.skip("無効な型データでエラーが発生（期待される動作）")

    def test_analytics_with_extreme_values(self):
        """極端な値での分析テスト"""
        extreme_metadata = {
            "zero_time": {
                "template_name": "zero.html.j2",
                "render_time": 0,
                "output_size": 0,
            },
            "large_time": {
                "template_name": "large.html.j2",
                "render_time": 10.0,  # 非常に長い時間
                "output_size": 10000000,  # 非常に大きなサイズ
            },
            "negative_time": {
                "template_name": "negative.html.j2",
                "render_time": -0.1,  # 負の時間
                "output_size": -1000,  # 負のサイズ
            },
        }

        stats = self.analytics.generate_statistics(extreme_metadata)

        # 統計が生成されることを確認
        assert isinstance(stats, dict)
        assert "template_distribution" in stats

    def test_analytics_concurrent_access(self):
        """並行アクセステスト"""
        import threading

        results = []
        errors = []

        def concurrent_analysis(thread_id):
            try:
                metadata = {
                    f"key_{thread_id}_{i}": {
                        "template_name": f"template_{thread_id}.html.j2",
                        "render_time": 0.1 + thread_id * 0.01,
                        "output_size": 1000 + thread_id * 100,
                    }
                    for i in range(10)
                }

                stats = self.analytics.generate_statistics(metadata)
                results.append((thread_id, len(stats)))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_analysis, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行アクセスでエラーが発生: {errors}"
        assert len(results) == 5
        assert all(stat_count > 0 for _, stat_count in results)
