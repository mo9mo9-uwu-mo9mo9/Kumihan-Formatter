"""スマートキャッシュテスト - Issue #596 Week 25-26対応

スマートキャッシュシステムの詳細テスト
自動最適化、インテリジェント削除、学習機能の確認
"""

import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.caching.cache_types import CacheEntry
from kumihan_formatter.core.caching.smart_cache import SmartCache


class TestSmartCache:
    """スマートキャッシュテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.smart_cache = SmartCache(
            name="test_smart_cache",
            max_memory_mb=10.0,
            max_memory_entries=100,
            learning_enabled=True,
            auto_optimization_enabled=True,
        )

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "smart_cache"):
            self.smart_cache.clear_all()

    def test_smart_cache_initialization(self):
        """スマートキャッシュ初期化テスト"""
        assert self.smart_cache.name == "test_smart_cache"
        assert self.smart_cache.max_memory_mb == 10.0
        assert self.smart_cache.max_memory_entries == 100
        assert self.smart_cache.learning_enabled is True
        assert self.smart_cache.auto_optimization_enabled is True
        assert hasattr(self.smart_cache, "usage_tracker")
        assert hasattr(self.smart_cache, "optimization_scheduler")

    def test_smart_cache_put_and_get(self):
        """スマートキャッシュ基本操作テスト"""
        # エントリを追加
        success = self.smart_cache.put("test_key", "test_value", ttl=3600)
        assert success

        # エントリを取得
        value = self.smart_cache.get("test_key")
        assert value == "test_value"

        # 存在しないキー
        value = self.smart_cache.get("nonexistent_key")
        assert value is None

    def test_learning_from_access_patterns(self):
        """アクセスパターン学習テスト"""
        # 複数のエントリを追加
        for i in range(10):
            self.smart_cache.put(f"key_{i}", f"value_{i}", ttl=3600)

        # 特定のキーを頻繁にアクセス
        frequent_key = "key_5"
        for _ in range(10):
            self.smart_cache.get(frequent_key)

        # 使用統計の確認
        stats = self.smart_cache.get_usage_statistics()
        assert frequent_key in stats["access_frequencies"]
        assert stats["access_frequencies"][frequent_key] > 5

        # 学習データの確認
        learning_data = self.smart_cache.get_learning_data()
        assert "hot_keys" in learning_data
        assert frequent_key in learning_data["hot_keys"]

    def test_intelligent_eviction_policy(self):
        """インテリジェント削除ポリシーテスト"""
        # メモリ制限を小さく設定
        small_cache = SmartCache(
            name="small_cache",
            max_memory_mb=0.5,  # 非常に小さなメモリ
            max_memory_entries=5,
            learning_enabled=True,
        )

        # 大量のエントリを追加（メモリ制限を超える）
        for i in range(10):
            # いくつかのキーを頻繁にアクセス
            key = f"key_{i}"
            value = f"value_{i}" * 100  # 大きめのデータ
            small_cache.put(key, value, ttl=3600)

            if i < 3:  # 最初の3つは頻繁にアクセス
                for _ in range(5):
                    small_cache.get(key)

        # 頻繁にアクセスされたキーが残っていることを確認
        assert small_cache.get("key_0") is not None
        assert small_cache.get("key_1") is not None
        assert small_cache.get("key_2") is not None

        # あまりアクセスされなかったキーは削除されている可能性
        stats = small_cache.get_usage_statistics()
        assert stats["evictions"] > 0

        small_cache.clear_all()

    def test_auto_optimization_scheduling(self):
        """自動最適化スケジューリングテスト"""
        # 時間制御の標準化モック
        self._mock_time_progression(
            start_time=1000.0,
            progression_seconds=6.0,
            test_function=self._run_optimization_test,
        )

    def _mock_time_progression(self, start_time, progression_seconds, test_function):
        """時間依存テストの標準化モック"""
        with patch("time.time") as mock_time:
            mock_time.return_value = start_time
            test_function(mock_time, start_time, progression_seconds)

    def _run_optimization_test(self, mock_time, start_time, progression_seconds):
        """最適化テストの実行"""
        # 最適化間隔を短く設定
        self.smart_cache.optimization_interval = 5  # 5秒間隔

        # データを追加
        for i in range(20):
            self.smart_cache.put(f"key_{i}", f"value_{i}", ttl=3600)

        # 時間を進める
        mock_time.return_value = start_time + progression_seconds

        # 最適化がトリガーされることを確認
        self.smart_cache._check_auto_optimization()

        # 最適化統計の確認
        opt_stats = self.smart_cache.get_optimization_statistics()
        assert opt_stats["last_optimization_time"] > 0
        assert opt_stats["optimization_count"] > 0

    def test_cache_preloading_suggestions(self):
        """キャッシュプリロード提案テスト"""
        # アクセスパターンを作成
        patterns = [
            ("morning_data", "morning_value"),
            ("daily_report", "report_value"),
            ("user_profile", "profile_value"),
        ]

        # 特定の時間帯に頻繁にアクセス
        with patch("time.time") as mock_time:
            # 朝の時間帯をシミュレート
            mock_time.return_value = 1000.0  # 起点時刻

            for hour in range(8, 12):  # 8-12時
                mock_time.return_value = 1000.0 + hour * 3600
                for key, value in patterns:
                    self.smart_cache.put(key, value, ttl=3600)
                    self.smart_cache.get(key)

        # プリロード提案を取得
        suggestions = self.smart_cache.get_preload_suggestions()

        assert "suggested_keys" in suggestions
        assert len(suggestions["suggested_keys"]) > 0
        assert "confidence_scores" in suggestions

        # 頻繁にアクセスされるキーが提案される
        suggested_keys = suggestions["suggested_keys"]
        assert any(key in suggested_keys for key, _ in patterns)

    def test_adaptive_ttl_adjustment(self):
        """適応的TTL調整テスト"""
        # 異なるアクセスパターンでエントリを作成
        frequent_key = "frequent_access"
        rare_key = "rare_access"

        # TTLを同じ値で設定
        initial_ttl = 3600
        self.smart_cache.put(frequent_key, "frequent_value", ttl=initial_ttl)
        self.smart_cache.put(rare_key, "rare_value", ttl=initial_ttl)

        # 一方を頻繁にアクセス
        for _ in range(20):
            self.smart_cache.get(frequent_key)

        # もう一方はほとんどアクセスしない
        self.smart_cache.get(rare_key)

        # TTL調整を実行
        self.smart_cache.optimize_ttl_based_on_usage()

        # 調整後のTTL情報を確認
        ttl_stats = self.smart_cache.get_ttl_optimization_stats()

        assert "adjusted_entries" in ttl_stats
        assert ttl_stats["adjusted_entries"] > 0

        # 頻繁にアクセスされるキーのTTLが延長される傾向
        # 稀にアクセスされるキーのTTLが短縮される傾向
        assert "extension_count" in ttl_stats
        assert "reduction_count" in ttl_stats

    def test_cache_warming_strategies(self):
        """キャッシュウォーミング戦略テスト"""
        # 予測キーのリストを設定
        predicted_keys = ["future_key_1", "future_key_2", "future_key_3"]

        # データ生成関数のモック
        data_generator = Mock()
        data_generator.side_effect = lambda key: f"generated_value_for_{key}"

        # キャッシュウォーミングを実行
        warming_result = self.smart_cache.warm_cache(predicted_keys, data_generator)

        assert warming_result["warmed_keys"] == len(predicted_keys)
        assert warming_result["failed_keys"] == 0

        # ウォーミングされたデータが取得できることを確認
        for key in predicted_keys:
            value = self.smart_cache.get(key)
            assert value == f"generated_value_for_{key}"

        # データ生成関数が正しく呼ばれたことを確認
        assert data_generator.call_count == len(predicted_keys)

    def test_memory_pressure_handling(self):
        """メモリ圧迫時の対応テスト"""
        # 小さなメモリ制限でテスト
        pressure_cache = SmartCache(
            name="pressure_test",
            max_memory_mb=1.0,  # 1MB制限
            max_memory_entries=50,
            learning_enabled=True,
        )

        # メモリ圧迫状況を作成
        large_data = "X" * 50000  # 50KB程度のデータ

        for i in range(30):  # メモリ制限を超える量
            pressure_cache.put(f"large_key_{i}", large_data, ttl=3600)

        # メモリ圧迫時の対応が動作していることを確認
        pressure_stats = pressure_cache.get_memory_pressure_stats()

        assert "pressure_events" in pressure_stats
        assert "emergency_cleanups" in pressure_stats
        assert pressure_stats["pressure_events"] > 0

        # メモリ使用量が制限内に収まっていることを確認
        memory_usage = pressure_cache.get_memory_usage_mb()
        assert memory_usage <= 1.0

        pressure_cache.clear_all()

    def test_cache_coherence_management(self):
        """キャッシュ一貫性管理テスト"""
        # 関連するキーのグループを作成
        base_key = "user_profile"
        related_keys = [
            "user_profile:details",
            "user_profile:settings",
            "user_profile:preferences",
        ]

        # グループとして登録
        self.smart_cache.register_key_group(base_key, related_keys)

        # データを追加
        self.smart_cache.put(base_key, "base_data", ttl=3600)
        for key in related_keys:
            self.smart_cache.put(key, f"data_for_{key}", ttl=3600)

        # ベースキーを無効化
        invalidated_count = self.smart_cache.invalidate_group(base_key)

        # 関連キーも無効化されることを確認
        assert invalidated_count == len(related_keys) + 1  # ベース + 関連

        # 無効化されたキーは取得できない
        assert self.smart_cache.get(base_key) is None
        for key in related_keys:
            assert self.smart_cache.get(key) is None

    def test_performance_monitoring_integration(self):
        """パフォーマンス監視統合テスト"""
        # パフォーマンス監視が有効になっていることを確認
        assert hasattr(self.smart_cache, "performance_monitor")

        # 操作を実行
        self.smart_cache.put("perf_key", "perf_value", ttl=3600)
        self.smart_cache.get("perf_key")
        self.smart_cache.get("nonexistent_key")  # ミス

        # パフォーマンス統計を取得
        perf_stats = self.smart_cache.get_performance_statistics()

        assert "total_operations" in perf_stats
        assert "cache_hits" in perf_stats
        assert "cache_misses" in perf_stats
        assert "avg_response_time" in perf_stats

        assert perf_stats["total_operations"] > 0
        assert perf_stats["cache_hits"] > 0
        assert perf_stats["cache_misses"] > 0

    def test_smart_cache_analytics_export(self):
        """スマートキャッシュ分析エクスポートテスト"""
        # 十分なデータを作成
        for i in range(50):
            key = f"analytics_key_{i}"
            self.smart_cache.put(key, f"value_{i}", ttl=3600)

            # 一部のキーを頻繁にアクセス
            if i % 5 == 0:
                for _ in range(10):
                    self.smart_cache.get(key)

        # 分析レポートをエクスポート
        analytics_report = self.smart_cache.export_analytics()

        # レポート構造の確認
        assert "timestamp" in analytics_report
        assert "cache_summary" in analytics_report
        assert "learning_insights" in analytics_report
        assert "optimization_recommendations" in analytics_report
        assert "performance_metrics" in analytics_report

        # キャッシュサマリー
        cache_summary = analytics_report["cache_summary"]
        assert cache_summary["total_entries"] > 0
        assert cache_summary["memory_usage_mb"] > 0

        # 学習インサイト
        learning_insights = analytics_report["learning_insights"]
        assert "access_patterns" in learning_insights
        assert "hot_keys" in learning_insights

        # 最適化推奨
        recommendations = analytics_report["optimization_recommendations"]
        assert isinstance(recommendations, list)


class TestSmartCacheEdgeCases:
    """スマートキャッシュエッジケーステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.smart_cache = SmartCache(
            name="edge_test_cache",
            max_memory_mb=5.0,
            max_memory_entries=50,
        )

    def test_smart_cache_with_disabled_features(self):
        """機能無効時のスマートキャッシュテスト"""
        disabled_cache = SmartCache(
            name="disabled_features",
            max_memory_mb=5.0,
            max_memory_entries=50,
            learning_enabled=False,
            auto_optimization_enabled=False,
        )

        # 基本操作は正常に動作
        assert disabled_cache.put("test_key", "test_value", ttl=3600)
        assert disabled_cache.get("test_key") == "test_value"

        # 学習機能は動作しない
        learning_data = disabled_cache.get_learning_data()
        assert learning_data["learning_enabled"] is False

        # 自動最適化は動作しない
        disabled_cache._check_auto_optimization()
        opt_stats = disabled_cache.get_optimization_statistics()
        assert opt_stats["optimization_count"] == 0

        disabled_cache.clear_all()

    def test_smart_cache_with_extreme_memory_limits(self):
        """極端なメモリ制限でのテスト"""
        # 非常に小さなメモリ制限
        tiny_cache = SmartCache(
            name="tiny_cache",
            max_memory_mb=0.1,  # 100KB
            max_memory_entries=5,
        )

        # 大きなデータを追加しようとする
        large_data = "X" * 200000  # 200KB
        success = tiny_cache.put("large_key", large_data, ttl=3600)

        # メモリ制限により失敗する可能性
        if not success:
            # 制限により追加できない
            assert tiny_cache.get("large_key") is None
        else:
            # 追加できた場合、他のエントリが削除される
            stats = tiny_cache.get_usage_statistics()
            assert stats["memory_usage_mb"] <= 0.1

        tiny_cache.clear_all()

    def test_smart_cache_concurrent_access(self):
        """並行アクセステスト"""
        import threading

        results = []
        errors = []

        def concurrent_cache_operation(thread_id):
            try:
                # 各スレッドで独立した操作
                for i in range(20):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"

                    # 追加
                    success = self.smart_cache.put(key, value, ttl=3600)

                    # 取得
                    retrieved_value = self.smart_cache.get(key)

                    results.append((thread_id, success, retrieved_value == value))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_cache_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行アクセスでエラーが発生: {errors}"
        assert len(results) == 60  # 3スレッド × 20操作

        # すべての操作が成功していることを確認
        for thread_id, put_success, get_success in results:
            assert put_success
            assert get_success

    def test_smart_cache_with_invalid_ttl(self):
        """無効なTTL値でのテスト"""
        # 負のTTL
        success = self.smart_cache.put("negative_ttl", "value", ttl=-100)
        assert not success or self.smart_cache.get("negative_ttl") is None

        # ゼロTTL（即座に期限切れ）
        success = self.smart_cache.put("zero_ttl", "value", ttl=0)
        assert not success or self.smart_cache.get("zero_ttl") is None

        # 非常に大きなTTL
        very_large_ttl = 2**31  # 約68年
        success = self.smart_cache.put("large_ttl", "value", ttl=very_large_ttl)
        assert success
        assert self.smart_cache.get("large_ttl") == "value"

    def test_smart_cache_data_corruption_resilience(self):
        """データ破損に対する耐性テスト"""
        # 正常なデータを追加
        self.smart_cache.put("normal_key", "normal_value", ttl=3600)

        # 内部データ構造を意図的に破損（テスト目的）
        if hasattr(self.smart_cache, "_memory_cache"):
            # 無効なエントリを注入
            invalid_entry = "invalid_data_not_cache_entry"
            self.smart_cache._memory_cache["corrupted_key"] = invalid_entry

        # 正常なキーは引き続き動作
        assert self.smart_cache.get("normal_key") == "normal_value"

        # 破損したキーに対して適切に処理される
        corrupted_value = self.smart_cache.get("corrupted_key")
        # Noneが返されるか、エラーハンドリングが適切に動作
        assert corrupted_value is None or isinstance(corrupted_value, str)

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "smart_cache"):
            self.smart_cache.clear_all()
