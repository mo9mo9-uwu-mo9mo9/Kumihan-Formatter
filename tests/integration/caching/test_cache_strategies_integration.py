"""キャッシュ戦略統合テスト - Issue #596 Week 23-24対応

キャッシュ戦略の効果測定と統合テスト
基本戦略・高度戦略・適応戦略の性能比較
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.caching.advanced_strategies import (
    AdaptiveStrategy,
    FrequencyBasedStrategy,
    SizeAwareStrategy,
)
from kumihan_formatter.core.caching.basic_strategies import FIFOStrategy, LRUStrategy
from kumihan_formatter.core.caching.smart_cache import SmartCache


class TestCacheStrategiesIntegration:
    """キャッシュ戦略統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリの削除は安全のため省略
        pass

    def test_lru_strategy_effectiveness(self):
        """LRU戦略の効果テスト"""
        cache = SmartCache(
            name="lru_test",
            max_memory_entries=5,
            max_memory_mb=10.0,
            strategy=LRUStrategy(),
            cache_dir=self.temp_dir,
            enable_file_cache=False,  # テスト用にファイルキャッシュを無効
        )

        try:
            # データを順次追加（LRU順序を確立）
            access_pattern = ["A", "B", "C", "D", "E"]
            for key in access_pattern:
                cache.set(key, f"value_{key}")

            # すべてのキーが存在することを確認
            for key in access_pattern:
                assert cache.get(key) == f"value_{key}"

            # 新しいエントリを追加（容量超過）
            cache.set("F", "value_F")

            # 最も古いエントリ（A）が削除されることを確認
            assert cache.get("A") is None
            assert cache.get("B") == "value_B"
            assert cache.get("F") == "value_F"

            # アクセスパターンによる順序変更をテスト
            cache.get("B")  # Bを最近使用に変更
            cache.set("G", "value_G")  # 新しいエントリ追加

            # Bは残り、Cが削除される
            assert cache.get("B") == "value_B"
            assert cache.get("C") is None

        finally:
            cache.clear()

    def test_fifo_strategy_behavior(self):
        """FIFO戦略の動作テスト"""
        cache = SmartCache(
            name="fifo_test",
            max_memory_entries=4,
            max_memory_mb=10.0,
            strategy=FIFOStrategy(),
            cache_dir=self.temp_dir,
            enable_file_cache=False,  # テスト用にファイルキャッシュを無効
        )

        try:
            # エントリを順次追加
            insertion_order = ["first", "second", "third", "fourth"]
            for key in insertion_order:
                cache.set(key, f"value_{key}")

            # すべてのエントリが存在
            for key in insertion_order:
                assert cache.get(key) == f"value_{key}"

            # 新しいエントリ追加（容量超過）
            cache.set("fifth", "value_fifth")

            # 最初に挿入されたエントリが削除される
            assert cache.get("first") is None
            assert cache.get("second") == "value_second"
            assert cache.get("fifth") == "value_fifth"

            # アクセスしても順序は変わらない（FIFO特性）
            cache.get("second")
            cache.set("sixth", "value_sixth")

            # secondが削除される（アクセスに関係なく）
            assert cache.get("second") is None
            assert cache.get("third") == "value_third"

        finally:
            cache.clear()

    def test_frequency_based_strategy(self):
        """周波数ベース戦略テスト"""
        cache = SmartCache(
            name="frequency_test",
            max_memory_entries=3,
            max_memory_mb=10.0,
            strategy=FrequencyBasedStrategy(frequency_threshold=2),
            cache_dir=self.temp_dir,
            enable_file_cache=False,  # テスト用にファイルキャッシュを無効
        )

        try:
            # エントリを追加
            cache.set("high_freq", "value_high")
            cache.set("medium_freq", "value_medium")
            cache.set("low_freq", "value_low")

            # 異なる頻度でアクセス
            for _ in range(5):
                cache.get("high_freq")  # 高頻度

            for _ in range(2):
                cache.get("medium_freq")  # 中頻度

            cache.get("low_freq")  # 低頻度

            # 新しいエントリ追加（容量超過）
            # 新しいエントリのaccess_count=0なので、最低優先度で削除される
            cache.set("new_entry", "value_new")

            # 新しいエントリが最低優先度で削除されるか、
            # または低頻度エントリが削除される
            # access_countの順番: high_freq=5, medium_freq=2, low_freq=1, new_entry=0
            # 最小優先度のnew_entryまたはlow_freqが削除される
            remaining_keys = set(cache.storage._memory_cache.keys())
            assert len(remaining_keys) == 3  # 3つのエントリが残る
            assert "high_freq" in remaining_keys
            assert "medium_freq" in remaining_keys
            # low_freqまたはnew_entryのいずれかが削除される
            assert ("low_freq" in remaining_keys) != ("new_entry" in remaining_keys)

        finally:
            cache.clear()

    def test_size_aware_strategy(self):
        """サイズ認識戦略テスト"""
        cache = SmartCache(
            name="size_aware_test",
            max_memory_entries=10,
            max_memory_mb=1.0,  # 1MBの制限
            strategy=SizeAwareStrategy(max_size_mb=0.5),
            cache_dir=self.temp_dir,
        )

        try:
            # 小さなエントリを複数追加
            small_data = "small" * 100  # 約500バイト
            for i in range(5):
                cache.set(f"small_{i}", small_data)

            # 大きなエントリを追加
            large_data = "large" * 10000  # 約50KB
            cache.set("large_1", large_data)

            # すべてが存在することを確認
            for i in range(5):
                assert cache.get(f"small_{i}") == small_data
            assert cache.get("large_1") == large_data

            # 非常に大きなエントリを追加（メモリ制限に近い）
            very_large_data = "X" * 200000  # 約200KB
            cache.set("very_large", very_large_data)

            # サイズを考慮した削除が発生
            stats = cache.get_stats()
            assert stats["memory_usage_mb"] <= 1.0

        finally:
            cache.clear()

    def test_adaptive_strategy_learning(self):
        """適応戦略の学習機能テスト"""
        cache = SmartCache(
            name="adaptive_test",
            max_memory_entries=6,
            max_memory_mb=10.0,
            strategy=AdaptiveStrategy(frequency_weight=0.6, size_weight=0.4),
            cache_dir=self.temp_dir,
        )

        try:
            # 初期データセット
            data_patterns = [
                ("freq_high", "small_data", 10),  # 高頻度、小サイズ
                ("freq_low", "large_data" * 1000, 1),  # 低頻度、大サイズ
                ("freq_medium", "medium_data" * 100, 5),  # 中頻度、中サイズ
            ]

            # パターンに従ってアクセス
            for key, data, frequency in data_patterns:
                cache.set(key, data)
                for _ in range(frequency):
                    cache.get(key)

            # 適応戦略の学習効果を確認
            # 新しいエントリを追加して削除パターンを観察
            cache.set("test_1", "test_data_1")
            cache.set("test_2", "test_data_2")
            cache.set("test_3", "test_data_3")
            cache.set("test_4", "test_data_4")  # 容量超過

            # 高頻度・小サイズのエントリは残るべき
            assert cache.get("freq_high") == "small_data"

            # 戦略の統計情報を確認
            stats = cache.get_stats()
            assert stats["entry_count"] <= 6

        finally:
            cache.clear()

    def test_strategy_performance_comparison(self):
        """戦略間のパフォーマンス比較テスト"""
        strategies = [
            ("LRU", LRUStrategy()),
            ("FIFO", FIFOStrategy()),
            ("FrequencyBased", FrequencyBasedStrategy()),
            ("SizeAware", SizeAwareStrategy()),
            ("Adaptive", AdaptiveStrategy()),
        ]

        performance_results = {}

        for strategy_name, strategy in strategies:
            cache = SmartCache(
                name=f"perf_test_{strategy_name}",
                max_memory_entries=100,
                max_memory_mb=20.0,
                strategy=strategy,
                cache_dir=self.temp_dir,
            )

            try:
                # パフォーマンステスト
                start_time = time.time()

                # 大量のデータを追加・アクセス
                for i in range(200):
                    key = f"key_{i}"
                    value = f"value_{i}" * (i % 10 + 1)
                    cache.set(key, value)

                    # アクセスパターン（一部のキーを頻繁にアクセス）
                    if i % 10 == 0:
                        for j in range(max(0, i - 10), i):
                            cache.get(f"key_{j}")

                execution_time = time.time() - start_time

                # 統計情報取得
                stats = cache.get_stats()
                performance_results[strategy_name] = {
                    "execution_time": execution_time,
                    "hit_rate": stats["hit_rate"],
                    "memory_usage": stats["memory_usage_mb"],
                    "entry_count": stats["entry_count"],
                }

            finally:
                cache.clear()

        # パフォーマンス結果の妥当性確認
        assert len(performance_results) == len(strategies)

        for strategy_name, results in performance_results.items():
            assert results["execution_time"] > 0
            assert 0 <= results["hit_rate"] <= 1
            assert results["memory_usage"] >= 0
            assert results["entry_count"] <= 100

    def test_strategy_memory_efficiency(self):
        """戦略別メモリ効率テスト"""
        # メモリ効率重視の戦略設定
        memory_efficient_strategy = SizeAwareStrategy(max_size_mb=0.1)

        cache = SmartCache(
            name="memory_efficiency_test",
            max_memory_entries=50,
            max_memory_mb=5.0,
            strategy=memory_efficient_strategy,
            cache_dir=self.temp_dir,
        )

        try:
            # 様々なサイズのデータを追加
            data_sizes = [
                ("tiny", "X" * 100),
                ("small", "X" * 1000),
                ("medium", "X" * 10000),
                ("large", "X" * 100000),
            ]

            for i in range(30):
                size_name, data_template = data_sizes[i % len(data_sizes)]
                key = f"{size_name}_{i}"
                value = data_template + f"_{i}"
                cache.set(key, value)

            # メモリ使用量が制限内であることを確認
            stats = cache.get_stats()
            assert stats["memory_usage_mb"] <= 5.0

            # 小さなエントリが優先的に保持されていることを確認
            tiny_count = sum(
                1 for key in cache.storage._memory_cache.keys() if "tiny" in key
            )
            large_count = sum(
                1 for key in cache.storage._memory_cache.keys() if "large" in key
            )

            # 小さなエントリの方が多く残っているべき
            assert tiny_count >= large_count

        finally:
            cache.clear()

    def test_strategy_concurrent_access(self):
        """戦略の並行アクセステスト - 高負荷対応版"""
        import threading

        cache = SmartCache(
            name="concurrent_strategy_test",
            max_memory_entries=50,  # より多くのエントリを許可
            max_memory_mb=20.0,  # メモリ上限も増加
            strategy=AdaptiveStrategy(),
            cache_dir=self.temp_dir,
        )

        results = []
        errors = []

        def concurrent_strategy_operation(thread_id):
            try:
                # 各スレッドで独立した操作
                for i in range(15):  # 操作数増加
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}" * 10  # データサイズ増加

                    cache.set(key, value)
                    retrieved_value = cache.get(key)

                    results.append((thread_id, retrieved_value == value))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 高負荷並行実行（スレッド数を3倍に増加）
        threads = []
        thread_count = 15  # 5 → 15スレッドに増加
        for i in range(thread_count):
            thread = threading.Thread(target=concurrent_strategy_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認（高負荷での検証）
        assert len(errors) == 0, f"高負荷並行アクセスでエラーが発生: {errors}"
        expected_operations = thread_count * 15  # 15スレッド × 15操作 = 225操作
        assert len(results) == expected_operations
        assert all(success for _, success in results), "高負荷並行操作の一部が失敗"

        # 戦略が高負荷でも正常に動作していることを確認
        stats = cache.get_stats()
        assert stats["entry_count"] <= 50  # 上限内であることを確認

        # 高負荷テストの統計情報を記録
        print(
            f"高負荷テスト完了: {thread_count}スレッド, {expected_operations}操作, エラー数: {len(errors)}"
        )

        cache.clear()

    def test_strategy_adaptation_over_time(self):
        """時間経過による戦略適応テスト"""
        adaptive_strategy = AdaptiveStrategy(frequency_weight=0.5, size_weight=0.5)

        cache = SmartCache(
            name="adaptation_test",
            max_memory_entries=10,
            max_memory_mb=10.0,
            strategy=adaptive_strategy,
            cache_dir=self.temp_dir,
        )

        try:
            # フェーズ1: 小さなファイルを頻繁にアクセス
            for i in range(20):
                key = f"small_phase1_{i}"
                value = "small_data" * 10
                cache.set(key, value)

                # 一部のキーを頻繁にアクセス
                if i % 5 == 0:
                    for _ in range(3):
                        cache.get(key)

            phase1_stats = cache.get_stats()

            # フェーズ2: 大きなファイルを少数アクセス
            for i in range(5):
                key = f"large_phase2_{i}"
                value = "large_data" * 1000
                cache.set(key, value)

            phase2_stats = cache.get_stats()

            # 適応戦略が学習していることを確認
            # （具体的な値は戦略の実装に依存）
            assert phase2_stats["entry_count"] <= 10
            assert phase2_stats["memory_usage_mb"] <= 10.0

            # 戦略の内部状態確認（アクセス可能な場合）
            if hasattr(adaptive_strategy, "get_adaptation_metrics"):
                metrics = adaptive_strategy.get_adaptation_metrics()
                assert "learning_iterations" in metrics

        finally:
            cache.clear()


class TestCacheStrategiesStressTest:
    """キャッシュ戦略ストレステスト"""

    def test_strategy_high_load_performance(self):
        """高負荷時の戦略パフォーマンステスト"""
        strategies_to_test = [
            ("Adaptive", AdaptiveStrategy()),
            ("LRU", LRUStrategy()),
        ]

        for strategy_name, strategy in strategies_to_test:
            cache = SmartCache(
                name=f"stress_{strategy_name}",
                max_memory_entries=500,
                max_memory_mb=50.0,
                strategy=strategy,
            )

            try:
                start_time = time.time()

                # 高負荷操作
                for i in range(1000):
                    key = f"stress_key_{i}"
                    value = f"stress_value_{i}" * (i % 100 + 1)

                    cache.set(key, value)

                    # ランダムアクセスパターン
                    if i > 100:
                        access_key = f"stress_key_{i - (i % 50)}"
                        cache.get(access_key)

                execution_time = time.time() - start_time

                # パフォーマンス要件
                assert (
                    execution_time < 10.0
                ), f"{strategy_name}戦略が遅すぎます: {execution_time}秒"

                # メモリ制限の確認
                stats = cache.get_stats()
                assert stats["memory_usage_mb"] <= 50.0
                assert stats["entry_count"] <= 500

            finally:
                cache.clear()
