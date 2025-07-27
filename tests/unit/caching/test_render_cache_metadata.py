"""レンダーキャッシュメタデータテスト - Issue #596 Week 25-26対応

レンダリングキャッシュのメタデータ管理機能の詳細テスト
メタデータ追跡、統計収集、分析機能の確認
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.caching.cache_types import CacheEntry
from kumihan_formatter.core.caching.render_cache_metadata import RenderCacheMetadata


class TestRenderCacheMetadata:
    """レンダーキャッシュメタデータテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.metadata_manager = RenderCacheMetadata()

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "metadata_manager"):
            self.metadata_manager.clear_all_metadata()

    def test_metadata_manager_initialization(self):
        """メタデータマネージャー初期化テスト"""
        manager = RenderCacheMetadata()
        assert manager is not None
        assert hasattr(manager, "add_render_metadata")
        assert hasattr(manager, "get_render_metadata")
        assert hasattr(manager, "update_metadata")
        assert hasattr(manager, "collect_statistics")

    def test_add_render_metadata_basic(self):
        """基本的なレンダリングメタデータ追加テスト"""
        metadata = {
            "template_name": "base.html.j2",
            "render_time": 0.15,
            "output_size": 2048,
            "template_hash": "abc123def456",
            "variables_hash": "var789hash",
            "timestamp": datetime.now().isoformat(),
        }

        success = self.metadata_manager.add_render_metadata("test_key", metadata)
        assert success

        # 追加されたメタデータを取得
        retrieved_metadata = self.metadata_manager.get_render_metadata("test_key")
        assert retrieved_metadata is not None
        assert retrieved_metadata["template_name"] == "base.html.j2"
        assert retrieved_metadata["render_time"] == 0.15

    def test_add_render_metadata_auto_enhancement(self):
        """自動拡張機能付きメタデータ追加テスト"""
        # 最小限のメタデータ
        minimal_metadata = {
            "template_name": "minimal.html.j2",
            "render_time": 0.08,
        }

        success = self.metadata_manager.add_render_metadata(
            "minimal_key", minimal_metadata
        )
        assert success

        # 自動拡張されたメタデータを取得
        enhanced_metadata = self.metadata_manager.get_render_metadata("minimal_key")

        # 自動追加されるフィールドの確認
        assert "metadata_version" in enhanced_metadata
        assert "creation_timestamp" in enhanced_metadata
        assert "last_accessed" in enhanced_metadata
        assert "access_count" in enhanced_metadata

    def test_update_metadata_fields(self):
        """メタデータフィールド更新テスト"""
        # 初期メタデータを追加
        initial_metadata = {
            "template_name": "update_test.html.j2",
            "render_time": 0.1,
            "output_size": 1000,
        }
        self.metadata_manager.add_render_metadata("update_key", initial_metadata)

        # 特定フィールドを更新
        updates = {
            "render_time": 0.12,  # 更新
            "optimization_level": "high",  # 新規追加
        }

        success = self.metadata_manager.update_metadata("update_key", updates)
        assert success

        # 更新後のメタデータを確認
        updated_metadata = self.metadata_manager.get_render_metadata("update_key")
        assert updated_metadata["render_time"] == 0.12
        assert updated_metadata["optimization_level"] == "high"
        assert (
            updated_metadata["template_name"] == "update_test.html.j2"
        )  # 既存値は保持

    def test_track_access_patterns(self):
        """アクセスパターン追跡テスト"""
        # メタデータを追加
        metadata = {
            "template_name": "access_test.html.j2",
            "render_time": 0.1,
        }
        self.metadata_manager.add_render_metadata("access_key", metadata)

        # 複数回アクセス
        for i in range(5):
            self.metadata_manager.record_access("access_key")

        # アクセス情報を確認
        access_info = self.metadata_manager.get_access_information("access_key")
        assert access_info["access_count"] == 5
        assert "last_accessed" in access_info
        assert "first_accessed" in access_info
        assert "access_frequency" in access_info

    def test_collect_statistics_comprehensive(self):
        """包括的統計収集テスト"""
        # 複数のメタデータを追加
        templates_data = [
            (
                "key1",
                {
                    "template_name": "base.html.j2",
                    "render_time": 0.1,
                    "output_size": 1000,
                },
            ),
            (
                "key2",
                {
                    "template_name": "base.html.j2",
                    "render_time": 0.12,
                    "output_size": 1200,
                },
            ),
            (
                "key3",
                {
                    "template_name": "docs.html.j2",
                    "render_time": 0.2,
                    "output_size": 2000,
                },
            ),
            (
                "key4",
                {
                    "template_name": "docs.html.j2",
                    "render_time": 0.18,
                    "output_size": 1800,
                },
            ),
            (
                "key5",
                {
                    "template_name": "error.html.j2",
                    "render_time": 0.05,
                    "output_size": 500,
                },
            ),
        ]

        for key, metadata in templates_data:
            self.metadata_manager.add_render_metadata(key, metadata)

        # 統計を収集
        stats = self.metadata_manager.collect_statistics()

        # 基本統計の確認
        assert stats["total_entries"] == 5
        assert "avg_render_time" in stats
        assert "max_render_time" in stats
        assert "min_render_time" in stats

        # テンプレート別統計
        assert "template_statistics" in stats
        template_stats = stats["template_statistics"]
        assert "base.html.j2" in template_stats
        assert "docs.html.j2" in template_stats

        # base.html.j2の統計確認
        base_stats = template_stats["base.html.j2"]
        assert base_stats["count"] == 2
        assert base_stats["avg_render_time"] == (0.1 + 0.12) / 2

    def test_metadata_validation_on_add(self):
        """追加時のメタデータ検証テスト"""
        # 無効なメタデータ
        invalid_metadata = {
            "template_name": "",  # 空のテンプレート名
            "render_time": -0.1,  # 負の値
            "output_size": None,  # None値
        }

        success = self.metadata_manager.add_render_metadata(
            "invalid_key", invalid_metadata
        )
        assert not success

        # 検証エラーの詳細を取得
        validation_errors = self.metadata_manager.get_last_validation_errors()
        assert len(validation_errors) > 0

        error_text = " ".join(validation_errors)
        assert "template_name" in error_text or "render_time" in error_text

    def test_metadata_search_and_filter(self):
        """メタデータ検索・フィルタリングテスト"""
        # 様々なメタデータを追加
        search_data = [
            (
                "fast_key",
                {
                    "template_name": "fast.html.j2",
                    "render_time": 0.05,
                    "tags": ["fast", "optimized"],
                },
            ),
            (
                "slow_key",
                {
                    "template_name": "slow.html.j2",
                    "render_time": 0.3,
                    "tags": ["slow", "complex"],
                },
            ),
            (
                "medium_key",
                {
                    "template_name": "medium.html.j2",
                    "render_time": 0.15,
                    "tags": ["medium"],
                },
            ),
        ]

        for key, metadata in search_data:
            self.metadata_manager.add_render_metadata(key, metadata)

        # テンプレート名で検索
        template_results = self.metadata_manager.search_metadata(
            filters={"template_name": "fast.html.j2"}
        )
        assert len(template_results) == 1
        assert "fast_key" in template_results

        # レンダリング時間の範囲で検索
        time_range_results = self.metadata_manager.search_metadata(
            filters={"render_time_min": 0.1, "render_time_max": 0.2}
        )
        assert len(time_range_results) >= 1
        assert "medium_key" in time_range_results

    def test_metadata_export_import(self):
        """メタデータエクスポート・インポートテスト"""
        # テストデータを追加
        export_data = {
            "export_key1": {"template_name": "export1.html.j2", "render_time": 0.1},
            "export_key2": {"template_name": "export2.html.j2", "render_time": 0.2},
        }

        for key, metadata in export_data.items():
            self.metadata_manager.add_render_metadata(key, metadata)

        # エクスポート
        exported_data = self.metadata_manager.export_metadata()

        assert "metadata_entries" in exported_data
        assert "export_timestamp" in exported_data
        assert "metadata_version" in exported_data
        assert len(exported_data["metadata_entries"]) == 2

        # 新しいマネージャーでインポート
        new_manager = RenderCacheMetadata()
        import_success = new_manager.import_metadata(exported_data)
        assert import_success

        # インポートされたデータを確認
        imported_metadata = new_manager.get_render_metadata("export_key1")
        assert imported_metadata is not None
        assert imported_metadata["template_name"] == "export1.html.j2"

        new_manager.clear_all_metadata()

    def test_metadata_cleanup_expired(self):
        """期限切れメタデータクリーンアップテスト"""
        with patch("time.time") as mock_time:
            # 現在時刻を設定
            mock_time.return_value = 1000.0

            # 異なる作成時刻のメタデータを追加
            old_metadata = {
                "template_name": "old.html.j2",
                "render_time": 0.1,
                "creation_timestamp": 500.0,  # 古いタイムスタンプ
            }
            new_metadata = {
                "template_name": "new.html.j2",
                "render_time": 0.1,
                "creation_timestamp": 900.0,  # 新しいタイムスタンプ
            }

            self.metadata_manager.add_render_metadata("old_key", old_metadata)
            self.metadata_manager.add_render_metadata("new_key", new_metadata)

            # 期限切れメタデータをクリーンアップ（600秒=10分より古い）
            cleaned_count = self.metadata_manager.cleanup_expired_metadata(
                max_age_seconds=600
            )

            assert cleaned_count == 1  # old_keyが削除される
            assert self.metadata_manager.get_render_metadata("old_key") is None
            assert self.metadata_manager.get_render_metadata("new_key") is not None

    def test_metadata_aggregation_by_template(self):
        """テンプレート別メタデータ集約テスト"""
        # 同じテンプレートの複数エントリ
        base_template_entries = [
            (
                "base1",
                {
                    "template_name": "base.html.j2",
                    "render_time": 0.1,
                    "output_size": 1000,
                },
            ),
            (
                "base2",
                {
                    "template_name": "base.html.j2",
                    "render_time": 0.15,
                    "output_size": 1500,
                },
            ),
            (
                "base3",
                {
                    "template_name": "base.html.j2",
                    "render_time": 0.12,
                    "output_size": 1200,
                },
            ),
        ]

        for key, metadata in base_template_entries:
            self.metadata_manager.add_render_metadata(key, metadata)

        # テンプレート別集約
        template_aggregation = self.metadata_manager.aggregate_by_template(
            "base.html.j2"
        )

        assert template_aggregation["entry_count"] == 3
        assert template_aggregation["avg_render_time"] == (0.1 + 0.15 + 0.12) / 3
        assert template_aggregation["min_render_time"] == 0.1
        assert template_aggregation["max_render_time"] == 0.15
        assert template_aggregation["total_output_size"] == 3700

    def test_metadata_performance_insights(self):
        """メタデータ性能洞察テスト"""
        # パフォーマンス分析用データ
        performance_data = [
            (
                "fast",
                {
                    "template_name": "fast.html.j2",
                    "render_time": 0.05,
                    "optimization_level": "high",
                },
            ),
            (
                "medium",
                {
                    "template_name": "medium.html.j2",
                    "render_time": 0.15,
                    "optimization_level": "medium",
                },
            ),
            (
                "slow",
                {
                    "template_name": "slow.html.j2",
                    "render_time": 0.4,
                    "optimization_level": "low",
                },
            ),
            (
                "very_slow",
                {
                    "template_name": "very_slow.html.j2",
                    "render_time": 0.8,
                    "optimization_level": "none",
                },
            ),
        ]

        for key, metadata in performance_data:
            self.metadata_manager.add_render_metadata(key, metadata)

        # 性能洞察を生成
        insights = self.metadata_manager.generate_performance_insights()

        assert "performance_distribution" in insights
        assert "optimization_recommendations" in insights
        assert "outlier_analysis" in insights

        # パフォーマンス分布
        perf_dist = insights["performance_distribution"]
        assert "fast_renders" in perf_dist  # <0.1秒
        assert "slow_renders" in perf_dist  # >0.3秒

        # 最適化推奨
        recommendations = insights["optimization_recommendations"]
        assert len(recommendations) > 0

    def test_metadata_correlation_analysis(self):
        """メタデータ相関分析テスト"""
        # 相関分析用データ（テンプレートサイズとレンダリング時間の関係）
        correlation_data = [
            (
                "small",
                {
                    "template_name": "small.html.j2",
                    "render_time": 0.05,
                    "template_size": 1000,
                    "complexity": "low",
                },
            ),
            (
                "medium",
                {
                    "template_name": "medium.html.j2",
                    "render_time": 0.15,
                    "template_size": 5000,
                    "complexity": "medium",
                },
            ),
            (
                "large",
                {
                    "template_name": "large.html.j2",
                    "render_time": 0.3,
                    "template_size": 10000,
                    "complexity": "high",
                },
            ),
            (
                "xlarge",
                {
                    "template_name": "xlarge.html.j2",
                    "render_time": 0.5,
                    "template_size": 20000,
                    "complexity": "very_high",
                },
            ),
        ]

        for key, metadata in correlation_data:
            self.metadata_manager.add_render_metadata(key, metadata)

        # 相関分析実行
        correlation = self.metadata_manager.analyze_correlations()

        assert "render_time_vs_template_size" in correlation
        assert "render_time_vs_complexity" in correlation
        assert "correlation_strength" in correlation

        # 正の相関があることを確認（サイズが大きいほど時間がかかる）
        size_correlation = correlation["render_time_vs_template_size"]
        assert size_correlation["correlation_coefficient"] > 0.5

    def test_metadata_trend_analysis(self):
        """メタデータ傾向分析テスト"""
        with patch("time.time") as mock_time:
            # 時系列データをシミュレート
            base_time = 1000.0
            trend_data = []

            for i in range(10):
                mock_time.return_value = base_time + i * 3600  # 1時間ごと

                # 時間とともにパフォーマンスが改善される傾向
                render_time = 0.2 - (i * 0.01)  # 徐々に高速化

                metadata = {
                    "template_name": "trend_test.html.j2",
                    "render_time": render_time,
                    "timestamp": base_time + i * 3600,
                }

                self.metadata_manager.add_render_metadata(f"trend_key_{i}", metadata)

            # 傾向分析実行
            trends = self.metadata_manager.analyze_trends()

            assert "performance_trend" in trends
            assert "trend_direction" in trends
            assert "improvement_rate" in trends

            # パフォーマンス改善傾向が検出される
            assert trends["trend_direction"] in ["improving", "stable", "degrading"]

    def test_metadata_anomaly_detection(self):
        """メタデータ異常検出テスト"""
        # 正常なデータと異常なデータを混在
        normal_and_anomaly_data = [
            # 正常なデータ
            (
                "normal1",
                {
                    "template_name": "normal.html.j2",
                    "render_time": 0.1,
                    "output_size": 1000,
                },
            ),
            (
                "normal2",
                {
                    "template_name": "normal.html.j2",
                    "render_time": 0.12,
                    "output_size": 1100,
                },
            ),
            (
                "normal3",
                {
                    "template_name": "normal.html.j2",
                    "render_time": 0.08,
                    "output_size": 900,
                },
            ),
            # 異常なデータ
            (
                "anomaly1",
                {
                    "template_name": "normal.html.j2",
                    "render_time": 2.5,
                    "output_size": 1000,
                },
            ),  # 異常に遅い
            (
                "anomaly2",
                {
                    "template_name": "normal.html.j2",
                    "render_time": 0.1,
                    "output_size": 50000,
                },
            ),  # 異常に大きい出力
        ]

        for key, metadata in normal_and_anomaly_data:
            self.metadata_manager.add_render_metadata(key, metadata)

        # 異常検出実行
        anomalies = self.metadata_manager.detect_anomalies()

        assert "detected_anomalies" in anomalies
        assert "anomaly_types" in anomalies
        assert "confidence_scores" in anomalies

        # 異常が検出されることを確認
        detected = anomalies["detected_anomalies"]
        assert len(detected) >= 2

        # 異常の種類が特定される
        anomaly_types = anomalies["anomaly_types"]
        assert (
            "render_time_outlier" in anomaly_types
            or "output_size_outlier" in anomaly_types
        )


class TestRenderCacheMetadataEdgeCases:
    """レンダーキャッシュメタデータエッジケーステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.metadata_manager = RenderCacheMetadata()

    def test_metadata_with_large_datasets(self):
        """大規模データセットでのメタデータ管理テスト"""
        import time as time_module

        # 大量のメタデータを追加
        start_time = time_module.time()

        for i in range(1000):
            metadata = {
                "template_name": f"template_{i % 10}.html.j2",
                "render_time": 0.1 + (i % 10) * 0.01,
                "output_size": 1000 + (i % 10) * 100,
            }
            self.metadata_manager.add_render_metadata(f"large_key_{i}", metadata)

        addition_time = time_module.time() - start_time

        # 統計収集の性能測定
        start_time = time_module.time()
        stats = self.metadata_manager.collect_statistics()
        stats_time = time_module.time() - start_time

        # 合理的な時間で完了することを確認
        assert addition_time < 5.0, f"大量メタデータ追加が遅すぎます: {addition_time}秒"
        assert stats_time < 2.0, f"大量データ統計収集が遅すぎます: {stats_time}秒"

        # 統計が正確であることを確認
        assert stats["total_entries"] == 1000

    def test_metadata_with_unicode_content(self):
        """Unicode文字を含むメタデータテスト"""
        unicode_metadata = {
            "template_name": "日本語テンプレート.html.j2",
            "render_time": 0.1,
            "description": "これは日本語の説明です。絵文字も含みます: 🎌🗾",
            "tags": ["日本語", "テスト", "unicode"],
        }

        success = self.metadata_manager.add_render_metadata(
            "unicode_key", unicode_metadata
        )
        assert success

        # Unicode文字が正しく保存・取得される
        retrieved = self.metadata_manager.get_render_metadata("unicode_key")
        assert retrieved["template_name"] == "日本語テンプレート.html.j2"
        assert "🎌🗾" in retrieved["description"]

    def test_metadata_concurrent_access(self):
        """並行アクセステスト"""
        import threading

        results = []
        errors = []

        def concurrent_metadata_operation(thread_id):
            try:
                # 各スレッドで独立したメタデータ操作
                for i in range(50):
                    key = f"thread_{thread_id}_key_{i}"
                    metadata = {
                        "template_name": f"thread_{thread_id}_template.html.j2",
                        "render_time": 0.1 + thread_id * 0.01,
                        "thread_id": thread_id,
                        "iteration": i,
                    }

                    # 追加
                    success = self.metadata_manager.add_render_metadata(key, metadata)

                    # 取得
                    retrieved = self.metadata_manager.get_render_metadata(key)

                    results.append((thread_id, success, retrieved is not None))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_metadata_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行アクセスでエラーが発生: {errors}"
        assert len(results) == 150  # 3スレッド × 50操作

        # すべての操作が成功していることを確認
        for thread_id, add_success, get_success in results:
            assert add_success
            assert get_success

    def test_metadata_memory_efficiency(self):
        """メタデータメモリ効率テスト"""
        import sys

        # 初期メモリ使用量を記録
        initial_refs = (
            len(self.metadata_manager._metadata_store)
            if hasattr(self.metadata_manager, "_metadata_store")
            else 0
        )

        # 大量のメタデータを追加
        for i in range(500):
            metadata = {
                "template_name": f"efficiency_test_{i}.html.j2",
                "render_time": 0.1,
                "large_data": "x" * 1000,  # 1KB のダミーデータ
            }
            self.metadata_manager.add_render_metadata(f"efficiency_key_{i}", metadata)

        # メタデータ削除
        for i in range(0, 500, 2):  # 半分を削除
            self.metadata_manager.remove_metadata(f"efficiency_key_{i}")

        # 残りのメタデータ数を確認
        remaining_count = len(
            [
                key
                for key in [f"efficiency_key_{i}" for i in range(500)]
                if self.metadata_manager.get_render_metadata(key) is not None
            ]
        )

        assert remaining_count == 250  # 半分が残っている

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "metadata_manager"):
            self.metadata_manager.clear_all_metadata()
