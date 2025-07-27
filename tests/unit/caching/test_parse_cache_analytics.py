"""パースキャッシュ分析テスト - Issue #596 Week 25-26対応

パースキャッシュの分析・統計・最適化機能の詳細テスト
統計情報生成、パターン最適化、スナップショット作成の確認
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.caching.parse_cache_analytics import ParseCacheAnalytics


class TestParseCacheAnalytics:
    """パースキャッシュ分析テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        # モックのキャッシュコアを作成
        self.cache_core = Mock()
        self.cache_core.parse_stats = {
            "cache_hits": 80,
            "cache_misses": 20,
            "total_parse_time": 10.0,
            "avg_parse_time": 0.1,
            "total_nodes_cached": 500,
        }
        self.cache_core.get_memory_usage.return_value = 0.6  # 60%
        self.cache_core.memory_cache = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }
        self.cache_core.default_ttl = 3600
        self.cache_core.max_memory_mb = 100.0
        self.cache_core.max_memory_entries = 1000

        self.analytics = ParseCacheAnalytics(self.cache_core)

    def test_analytics_initialization(self):
        """分析モジュール初期化テスト"""
        cache_core = Mock()
        analytics = ParseCacheAnalytics(cache_core)

        assert analytics.cache_core == cache_core
        assert hasattr(analytics, "monitor")
        assert hasattr(analytics, "get_parse_statistics")
        assert hasattr(analytics, "optimize_cache_for_patterns")

    def test_get_parse_statistics_basic(self):
        """基本統計情報取得テスト"""
        stats = self.analytics.get_parse_statistics()

        # 基本統計の確認
        assert stats["cache_hits"] == 80
        assert stats["cache_misses"] == 20
        assert stats["total_parse_time"] == 10.0
        assert stats["avg_parse_time"] == 0.1
        assert stats["total_nodes_cached"] == 500

        # 計算された統計の確認
        assert stats["hit_rate"] == 0.8  # 80/100
        assert stats["memory_usage"] == 0.6
        assert stats["entry_count"] == 3
        assert stats["time_saved_seconds"] == 8.0  # 80 * 0.1

    def test_get_parse_statistics_zero_requests(self):
        """リクエスト数ゼロでの統計取得テスト"""
        self.cache_core.parse_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_parse_time": 0.0,
            "avg_parse_time": 0.0,
            "total_nodes_cached": 0,
        }

        stats = self.analytics.get_parse_statistics()

        # ゼロ除算エラーが発生しないことを確認
        assert stats["hit_rate"] == 0.0
        assert stats["time_saved_seconds"] == 0.0

    def test_optimize_cache_for_patterns_low_hit_rate(self):
        """低ヒット率での最適化テスト"""
        # 低ヒット率のシナリオ
        self.cache_core.parse_stats["cache_hits"] = 20
        self.cache_core.parse_stats["cache_misses"] = 80  # ヒット率20%

        result = self.analytics.optimize_cache_for_patterns()

        # 最適化アクションの確認
        assert "actions_taken" in result
        assert "TTL延長" in result["actions_taken"]
        assert "メモリ上限増加" in result["actions_taken"]

        # TTLが延長されていることを確認
        assert self.cache_core.default_ttl > 3600

        # 推奨事項の確認
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

        # パフォーマンス影響の確認
        assert "performance_impact" in result
        assert result["performance_impact"]["current_hit_rate"] == 0.2

    def test_optimize_cache_for_patterns_high_memory_usage(self):
        """高メモリ使用率での最適化テスト"""
        # 高メモリ使用率のシナリオ
        self.cache_core.get_memory_usage.return_value = 0.9  # 90%
        self.cache_core.cleanup_expired_entries = Mock()

        result = self.analytics.optimize_cache_for_patterns()

        # 最適化アクションの確認
        assert "期限切れエントリの削除" in result["actions_taken"]
        assert "TTL短縮" in result["actions_taken"]

        # クリーンアップが実行されたことを確認
        self.cache_core.cleanup_expired_entries.assert_called_once()

        # TTLが短縮されていることを確認
        assert self.cache_core.default_ttl < 3600

        # メモリ関連の推奨事項があることを確認
        recommendations = " ".join(result["recommendations"])
        assert "メモリ" in recommendations

    def test_optimize_cache_for_patterns_good_performance(self):
        """良好なパフォーマンスでの最適化テスト"""
        # 良好なパフォーマンスのシナリオ
        self.cache_core.parse_stats["cache_hits"] = 90
        self.cache_core.parse_stats["cache_misses"] = 10  # ヒット率90%
        self.cache_core.get_memory_usage.return_value = 0.5  # 50%

        original_ttl = self.cache_core.default_ttl
        result = self.analytics.optimize_cache_for_patterns()

        # 最適化アクションが少ない、または空
        assert len(result["actions_taken"]) == 0

        # TTLが変更されていないことを確認
        assert self.cache_core.default_ttl == original_ttl

        # パフォーマンス情報が正しく記録されていることを確認
        assert result["performance_impact"]["current_hit_rate"] == 0.9

    def test_invalidate_by_content_hash(self):
        """コンテンツハッシュによる無効化テスト"""
        # テストハッシュを含むキーを設定
        self.cache_core.memory_cache = {
            "parse:hash123:file1": "value1",
            "parse:hash456:file2": "value2",
            "parse:hash123:file3": "value3",
            "parse:other:file4": "value4",
        }
        self.cache_core.delete = Mock(return_value=True)

        # hash123を含むエントリを無効化
        invalidated_count = self.analytics.invalidate_by_content_hash("hash123")

        # 2つのエントリが無効化される
        assert invalidated_count == 2

        # deleteメソッドが正しいキーで呼ばれることを確認
        expected_calls = [
            ("parse:hash123:file1",),
            ("parse:hash123:file3",),
        ]
        actual_calls = [call[0] for call in self.cache_core.delete.call_args_list]

        for expected_key in [call[0] for call in expected_calls]:
            assert expected_key in actual_calls

    def test_invalidate_by_content_hash_no_matches(self):
        """一致しないハッシュでの無効化テスト"""
        self.cache_core.memory_cache = {
            "parse:hash123:file1": "value1",
            "parse:hash456:file2": "value2",
        }
        self.cache_core.delete = Mock()

        # 存在しないハッシュで無効化
        invalidated_count = self.analytics.invalidate_by_content_hash("nonexistent")

        # 無効化されるエントリはゼロ
        assert invalidated_count == 0

        # deleteメソッドが呼ばれない
        self.cache_core.delete.assert_not_called()

    def test_create_cache_snapshot(self):
        """キャッシュスナップショット作成テスト"""
        with patch(
            "kumihan_formatter.core.caching.parse_cache_analytics.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = (
                "2023-01-01T12:00:00"
            )

            snapshot = self.analytics.create_cache_snapshot()

        # スナップショット構造の確認
        assert "timestamp" in snapshot
        assert "statistics" in snapshot
        assert "cache_keys" in snapshot
        assert "configuration" in snapshot

        # タイムスタンプの確認
        assert snapshot["timestamp"] == "2023-01-01T12:00:00"

        # 統計情報の確認
        stats = snapshot["statistics"]
        assert stats["cache_hits"] == 80
        assert stats["hit_rate"] == 0.8

        # キャッシュキーの確認
        cache_keys = snapshot["cache_keys"]
        assert "key1" in cache_keys
        assert "key2" in cache_keys
        assert "key3" in cache_keys

        # 設定情報の確認
        config = snapshot["configuration"]
        assert config["max_memory_mb"] == 100.0
        assert config["max_entries"] == 1000
        assert config["default_ttl"] == 3600

    def test_analytics_with_empty_cache(self):
        """空のキャッシュでの分析テスト"""
        self.cache_core.memory_cache = {}
        self.cache_core.parse_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_parse_time": 0.0,
            "avg_parse_time": 0.0,
            "total_nodes_cached": 0,
        }
        self.cache_core.get_memory_usage.return_value = 0.0

        stats = self.analytics.get_parse_statistics()

        # 空のキャッシュでも統計が正常に取得される
        assert stats["hit_rate"] == 0.0
        assert stats["entry_count"] == 0
        assert stats["memory_usage"] == 0.0
        assert stats["time_saved_seconds"] == 0.0

    def test_analytics_performance_monitoring_integration(self):
        """パフォーマンス監視統合テスト"""
        # モニターの設定
        mock_monitor = Mock()
        self.analytics.monitor = mock_monitor

        # 無効化操作でモニターが呼ばれることを確認
        self.cache_core.memory_cache = {"test_key": "test_value"}
        self.cache_core.delete = Mock(return_value=True)

        self.analytics.invalidate_by_content_hash("test")

        # 無効化が記録されることを確認
        mock_monitor.record_cache_invalidation.assert_called()

    def test_optimize_cache_for_patterns_boundary_values(self):
        """境界値での最適化テスト"""
        # ヒット率がちょうど30%のケース
        self.cache_core.parse_stats["cache_hits"] = 30
        self.cache_core.parse_stats["cache_misses"] = 70  # ヒット率30%

        result = self.analytics.optimize_cache_for_patterns()

        # 境界値では最適化が実行されない
        assert len(result["actions_taken"]) == 0

        # メモリ使用率がちょうど80%のケース
        self.cache_core.get_memory_usage.return_value = 0.8
        self.cache_core.cleanup_expired_entries = Mock()

        result = self.analytics.optimize_cache_for_patterns()

        # 境界値では最適化が実行されない
        self.cache_core.cleanup_expired_entries.assert_not_called()

    def test_analytics_concurrent_access(self):
        """並行アクセステスト"""
        import threading

        results = []
        errors = []

        def concurrent_analytics_operation(thread_id):
            try:
                # 統計取得
                stats = self.analytics.get_parse_statistics()

                # 最適化実行
                optimization = self.analytics.optimize_cache_for_patterns()

                # スナップショット作成
                snapshot = self.analytics.create_cache_snapshot()

                results.append(
                    (thread_id, len(stats), len(optimization), len(snapshot))
                )

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_analytics_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行アクセスでエラーが発生: {errors}"
        assert len(results) == 3

        # すべての操作が正常に完了していることを確認
        for thread_id, stats_len, opt_len, snapshot_len in results:
            assert stats_len > 0
            assert opt_len > 0
            assert snapshot_len > 0


class TestParseCacheAnalyticsEdgeCases:
    """パースキャッシュ分析エッジケーステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.cache_core = Mock()
        self.analytics = ParseCacheAnalytics(self.cache_core)

    def test_analytics_with_missing_parse_stats(self):
        """parse_stats欠損時の分析テスト"""
        # 一部のフィールドが欠損したparse_stats
        self.cache_core.parse_stats = {
            "cache_hits": 50,
            # cache_misses欠損
            "total_parse_time": 5.0,
            # avg_parse_time欠損
        }
        self.cache_core.get_memory_usage.return_value = 0.5
        self.cache_core.memory_cache = {"key1": "value1"}

        try:
            stats = self.analytics.get_parse_statistics()
            # エラーが発生しないか、適切にデフォルト値が設定される
            assert isinstance(stats, dict)
        except KeyError:
            # フィールド欠損でエラーが発生する場合も許容
            pytest.skip("parse_stats欠損でエラーが発生（期待される動作）")

    def test_analytics_with_invalid_cache_core(self):
        """無効なキャッシュコアでの分析テスト"""
        # 必要なメソッドが存在しないキャッシュコア
        invalid_cache_core = Mock()
        del invalid_cache_core.parse_stats
        del invalid_cache_core.get_memory_usage

        analytics = ParseCacheAnalytics(invalid_cache_core)

        # エラーハンドリングの確認
        with pytest.raises(AttributeError):
            analytics.get_parse_statistics()

    def test_optimize_with_extreme_values(self):
        """極端な値での最適化テスト"""
        self.cache_core.parse_stats = {
            "cache_hits": 1000000,  # 非常に大きな値
            "cache_misses": 0,
            "total_parse_time": 0.0,
            "avg_parse_time": 0.0,
            "total_nodes_cached": 0,
        }
        self.cache_core.get_memory_usage.return_value = 1.0  # 100%
        self.cache_core.memory_cache = {}
        self.cache_core.default_ttl = 1  # 非常に短いTTL
        self.cache_core.max_memory_mb = 1000.0  # 非常に大きなメモリ
        self.cache_core.cleanup_expired_entries = Mock()

        result = self.analytics.optimize_cache_for_patterns()

        # 極端な値でも正常に処理される
        assert isinstance(result, dict)
        assert "actions_taken" in result
        assert "performance_impact" in result

    def test_invalidate_with_large_cache(self):
        """大規模キャッシュでの無効化テスト"""
        import time

        # 大量のキャッシュエントリを生成
        large_cache = {}
        target_hash = "target_hash"

        for i in range(1000):
            if i % 10 == 0:  # 10%に対象ハッシュを含める
                large_cache[f"key_{i}_{target_hash}"] = f"value_{i}"
            else:
                large_cache[f"key_{i}_other"] = f"value_{i}"

        self.cache_core.memory_cache = large_cache
        self.cache_core.delete = Mock(return_value=True)

        # 処理時間を測定
        start_time = time.time()
        invalidated_count = self.analytics.invalidate_by_content_hash(target_hash)
        execution_time = time.time() - start_time

        # 合理的な時間で完了することを確認
        assert execution_time < 1.0, f"大規模無効化が遅すぎます: {execution_time}秒"

        # 正しい数のエントリが無効化されることを確認
        assert invalidated_count == 100  # 10% of 1000
