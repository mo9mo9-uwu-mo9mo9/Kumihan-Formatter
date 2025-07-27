"""基本キャッシュ戦略テスト - Issue #596 Week 23-24対応

LRU・FIFO基本戦略の詳細テスト
キャッシュアルゴリズムの正確性確認
"""

import time
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.caching.basic_strategies import (
    CacheStrategy,
    FIFOStrategy,
    LRUStrategy,
)


class TestLRUStrategy:
    """LRU戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = LRUStrategy()

    def test_lru_strategy_initialization(self):
        """LRU戦略初期化テスト"""
        assert self.strategy.name == "LRU"
        assert hasattr(self.strategy, "_access_order")
        assert len(self.strategy._access_order) == 0

    def test_lru_basic_eviction_order(self):
        """LRU基本的な削除順序テスト"""
        # エントリを順次追加
        entries = ["A", "B", "C", "D"]
        for entry in entries:
            self.strategy.on_access(entry)

        # 削除対象の確認
        eviction_candidate = self.strategy.choose_eviction_candidate(entries)
        assert eviction_candidate == "A"  # 最も古いエントリ

    def test_lru_access_updates_order(self):
        """LRUアクセス時の順序更新テスト"""
        # エントリを追加
        entries = ["A", "B", "C", "D"]
        for entry in entries:
            self.strategy.on_access(entry)

        # Aにアクセス（最新に移動）
        self.strategy.on_access("A")

        # 削除対象がBになることを確認
        eviction_candidate = self.strategy.choose_eviction_candidate(entries)
        assert eviction_candidate == "B"

    def test_lru_eviction_notification(self):
        """LRU削除通知テスト"""
        entries = ["A", "B", "C"]
        for entry in entries:
            self.strategy.on_access(entry)

        # Aを削除
        self.strategy.on_evict("A")

        # アクセス順序からAが削除されることを確認
        assert "A" not in self.strategy._access_order
        assert "B" in self.strategy._access_order
        assert "C" in self.strategy._access_order

    def test_lru_multiple_access_same_key(self):
        """LRU同一キー複数アクセステスト"""
        entries = ["A", "B", "C"]
        for entry in entries:
            self.strategy.on_access(entry)

        # Bに複数回アクセス
        for _ in range(3):
            self.strategy.on_access("B")

        # Bが最新になり、Aが削除対象
        eviction_candidate = self.strategy.choose_eviction_candidate(entries)
        assert eviction_candidate == "A"

    def test_lru_empty_entries_handling(self):
        """LRU空エントリ処理テスト"""
        # エントリが空の場合
        eviction_candidate = self.strategy.choose_eviction_candidate([])
        assert eviction_candidate is None

        # アクセス履歴があるが現在のエントリが空
        self.strategy.on_access("A")
        eviction_candidate = self.strategy.choose_eviction_candidate([])
        assert eviction_candidate is None

    def test_lru_strategy_stats(self):
        """LRU戦略統計テスト"""
        entries = ["A", "B", "C", "D", "E"]
        for entry in entries:
            self.strategy.on_access(entry)

        # いくつかのエントリに追加アクセス
        self.strategy.on_access("A")
        self.strategy.on_access("C")

        stats = self.strategy.get_stats()
        assert "strategy_name" in stats
        assert stats["strategy_name"] == "LRU"
        assert "total_accesses" in stats
        assert stats["total_accesses"] == 7  # 5 + 2追加アクセス

    def test_lru_large_scale_operations(self):
        """LRU大規模操作テスト"""
        # 大量のエントリでテスト
        large_entries = [f"entry_{i}" for i in range(1000)]

        for entry in large_entries:
            self.strategy.on_access(entry)

        # 最初のエントリが削除対象
        eviction_candidate = self.strategy.choose_eviction_candidate(large_entries)
        assert eviction_candidate == "entry_0"

        # 中間のエントリにアクセス
        self.strategy.on_access("entry_500")

        # entry_1が新しい削除対象
        eviction_candidate = self.strategy.choose_eviction_candidate(large_entries)
        assert eviction_candidate == "entry_1"


class TestFIFOStrategy:
    """FIFO戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = FIFOStrategy()

    def test_fifo_strategy_initialization(self):
        """FIFO戦略初期化テスト"""
        assert self.strategy.name == "FIFO"
        assert hasattr(self.strategy, "_insertion_order")
        assert len(self.strategy._insertion_order) == 0

    def test_fifo_basic_eviction_order(self):
        """FIFO基本的な削除順序テスト"""
        # エントリを順次追加
        entries = ["first", "second", "third", "fourth"]
        for entry in entries:
            self.strategy.on_access(entry)

        # 最初に挿入されたエントリが削除対象
        eviction_candidate = self.strategy.choose_eviction_candidate(entries)
        assert eviction_candidate == "first"

    def test_fifo_access_does_not_change_order(self):
        """FIFOアクセスが順序に影響しないテスト"""
        entries = ["A", "B", "C", "D"]
        for entry in entries:
            self.strategy.on_access(entry)

        # Aに複数回アクセス
        for _ in range(5):
            self.strategy.on_access("A")

        # アクセス回数に関係なく、Aが削除対象のまま
        eviction_candidate = self.strategy.choose_eviction_candidate(entries)
        assert eviction_candidate == "A"

    def test_fifo_eviction_notification(self):
        """FIFO削除通知テスト"""
        entries = ["A", "B", "C", "D"]
        for entry in entries:
            self.strategy.on_access(entry)

        # Aを削除
        self.strategy.on_evict("A")

        # 挿入順序からAが削除され、Bが次の削除対象
        remaining_entries = ["B", "C", "D"]
        eviction_candidate = self.strategy.choose_eviction_candidate(remaining_entries)
        assert eviction_candidate == "B"

    def test_fifo_duplicate_access_handling(self):
        """FIFO重複アクセス処理テスト"""
        # 同じエントリを複数回アクセス
        self.strategy.on_access("duplicate")
        self.strategy.on_access("other")
        self.strategy.on_access("duplicate")  # 重複アクセス

        # 重複は挿入順序に影響しない
        entries = ["duplicate", "other"]
        eviction_candidate = self.strategy.choose_eviction_candidate(entries)
        assert eviction_candidate == "duplicate"

    def test_fifo_empty_entries_handling(self):
        """FIFO空エントリ処理テスト"""
        # エントリが空の場合
        eviction_candidate = self.strategy.choose_eviction_candidate([])
        assert eviction_candidate is None

        # 挿入履歴があるが現在のエントリが空
        self.strategy.on_access("A")
        eviction_candidate = self.strategy.choose_eviction_candidate([])
        assert eviction_candidate is None

    def test_fifo_strategy_stats(self):
        """FIFO戦略統計テスト"""
        entries = ["X", "Y", "Z"]
        for entry in entries:
            self.strategy.on_access(entry)

        # 追加アクセス
        self.strategy.on_access("X")
        self.strategy.on_access("Y")

        stats = self.strategy.get_stats()
        assert stats["strategy_name"] == "FIFO"
        assert stats["total_accesses"] == 5  # 3 + 2追加アクセス

    def test_fifo_consistency_over_time(self):
        """FIFO時間経過による一貫性テスト"""
        # 時間差をつけてエントリを追加
        time_ordered_entries = []

        for i in range(10):
            entry = f"time_entry_{i}"
            time_ordered_entries.append(entry)
            self.strategy.on_access(entry)

            # 小さな時間差（実際の使用では不要だが、テストの確実性のため）
            time.sleep(0.001)

        # 時間順序通りに削除される
        for i, expected_entry in enumerate(time_ordered_entries):
            remaining_entries = time_ordered_entries[i:]
            eviction_candidate = self.strategy.choose_eviction_candidate(
                remaining_entries
            )
            assert eviction_candidate == expected_entry

            # 削除を通知
            self.strategy.on_evict(expected_entry)


class TestCacheStrategyBase:
    """キャッシュ戦略ベースクラステスト"""

    def test_strategy_interface_compliance(self):
        """戦略インターフェース準拠テスト"""
        # LRUとFIFOが基本インターフェースを実装していることを確認
        strategies = [LRUStrategy(), FIFOStrategy()]

        for strategy in strategies:
            # 必要なメソッドが存在することを確認
            assert hasattr(strategy, "on_access")
            assert hasattr(strategy, "on_evict")
            assert hasattr(strategy, "choose_eviction_candidate")
            assert hasattr(strategy, "get_stats")
            assert hasattr(strategy, "name")

            # メソッドが呼び出し可能であることを確認
            assert callable(strategy.on_access)
            assert callable(strategy.on_evict)
            assert callable(strategy.choose_eviction_candidate)
            assert callable(strategy.get_stats)

    def test_strategy_error_handling(self):
        """戦略エラーハンドリングテスト"""
        strategies = [LRUStrategy(), FIFOStrategy()]

        for strategy in strategies:
            # None値での操作
            strategy.on_access(None)
            strategy.on_evict(None)

            # 存在しないエントリの削除
            strategy.on_evict("nonexistent")

            # 無効な入力での削除候補選択
            result = strategy.choose_eviction_candidate(None)
            assert result is None

    def test_strategy_concurrent_access_safety(self):
        """戦略並行アクセス安全性テスト"""
        import threading

        strategies = [LRUStrategy(), FIFOStrategy()]

        for strategy in strategies:
            results = []
            errors = []

            def concurrent_access(thread_id):
                try:
                    for i in range(100):
                        key = f"thread_{thread_id}_key_{i}"
                        strategy.on_access(key)

                    results.append(thread_id)

                except Exception as e:
                    errors.append((thread_id, str(e)))

            # 並行実行
            threads = []
            for i in range(3):
                thread = threading.Thread(target=concurrent_access, args=(i,))
                threads.append(thread)
                thread.start()

            # 完了待機
            for thread in threads:
                thread.join()

            # 結果確認
            assert len(errors) == 0, f"並行アクセスでエラー: {errors}"
            assert len(results) == 3

    def test_strategy_memory_efficiency(self):
        """戦略メモリ効率テスト"""
        strategies = [LRUStrategy(), FIFOStrategy()]

        for strategy in strategies:
            # 大量のエントリアクセス
            for i in range(10000):
                strategy.on_access(f"key_{i}")

            # メモリ使用量が合理的であることを確認
            stats = strategy.get_stats()
            assert stats["total_accesses"] == 10000

            # 内部データ構造のサイズが合理的
            if hasattr(strategy, "_access_order"):
                assert len(strategy._access_order) <= 10000
            if hasattr(strategy, "_insertion_order"):
                assert len(strategy._insertion_order) <= 10000


class TestStrategyComparison:
    """戦略比較テスト"""

    def test_lru_vs_fifo_behavior_difference(self):
        """LRU vs FIFO動作差異テスト"""
        lru = LRUStrategy()
        fifo = FIFOStrategy()

        # 同じパターンでアクセス
        entries = ["A", "B", "C"]
        for entry in entries:
            lru.on_access(entry)
            fifo.on_access(entry)

        # Aに追加アクセス（LRUでは順序が変わる）
        lru.on_access("A")
        fifo.on_access("A")

        # LRU: Aが最新になるため、Bが削除対象
        lru_candidate = lru.choose_eviction_candidate(entries)
        assert lru_candidate == "B"

        # FIFO: アクセス順序に関係なく、Aが削除対象
        fifo_candidate = fifo.choose_eviction_candidate(entries)
        assert fifo_candidate == "A"

    def test_strategy_performance_characteristics(self):
        """戦略パフォーマンス特性テスト"""
        lru = LRUStrategy()
        fifo = FIFOStrategy()

        # 大量操作のタイミング測定
        entries = [f"entry_{i}" for i in range(1000)]

        # LRU操作時間
        start_time = time.time()
        for entry in entries:
            lru.on_access(entry)
        lru_time = time.time() - start_time

        # FIFO操作時間
        start_time = time.time()
        for entry in entries:
            fifo.on_access(entry)
        fifo_time = time.time() - start_time

        # 両戦略とも合理的な時間で完了
        assert lru_time < 1.0, f"LRU操作が遅すぎます: {lru_time}秒"
        assert fifo_time < 1.0, f"FIFO操作が遅すぎます: {fifo_time}秒"

    def test_strategy_accuracy_verification(self):
        """戦略精度検証テスト"""
        lru = LRUStrategy()
        fifo = FIFOStrategy()

        # 複雑なアクセスパターン
        access_pattern = [
            "A",
            "B",
            "C",
            "D",  # 初期挿入
            "A",
            "B",  # A, Bにアクセス
            "E",
            "F",  # 新しいエントリ
            "C",  # Cにアクセス
        ]

        for entry in access_pattern:
            lru.on_access(entry)
            fifo.on_access(entry)

        current_entries = ["A", "B", "C", "D", "E", "F"]

        # LRU: 最後にアクセスされたのはC、最初はD
        lru_candidate = lru.choose_eviction_candidate(current_entries)
        assert lru_candidate == "D"

        # FIFO: 最初に挿入されたのはA
        fifo_candidate = fifo.choose_eviction_candidate(current_entries)
        assert fifo_candidate == "A"
