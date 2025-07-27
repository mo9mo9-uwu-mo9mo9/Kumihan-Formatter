"""高度キャッシュ戦略テスト - Issue #616対応

FrequencyBasedStrategy・SizeAwareStrategy等の高度戦略テスト
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.caching.advanced_strategies import (
    AdaptiveStrategy,
    FrequencyBasedStrategy,
    PerformanceAwareStrategy,
    SizeAwareStrategy,
)
from kumihan_formatter.core.caching.cache_types import CacheEntry


class TestFrequencyBasedStrategy:
    """頻度ベース戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = FrequencyBasedStrategy(frequency_threshold=3)

    def test_frequency_strategy_initialization(self):
        """頻度戦略初期化テスト"""
        assert self.strategy.frequency_threshold == 3

    def test_should_evict_low_frequency(self):
        """低頻度アクセスエントリの削除判定テスト"""
        # 低頻度アクセスエントリ (access_count < threshold)
        low_freq_entry = Mock(spec=CacheEntry)
        low_freq_entry.is_expired.return_value = False
        low_freq_entry.access_count = 2

        assert self.strategy.should_evict(low_freq_entry) is True

    def test_should_evict_high_frequency(self):
        """高頻度アクセスエントリの保持判定テスト"""
        # 高頻度アクセスエントリ (access_count >= threshold)
        high_freq_entry = Mock(spec=CacheEntry)
        high_freq_entry.is_expired.return_value = False
        high_freq_entry.access_count = 5

        assert self.strategy.should_evict(high_freq_entry) is False

    def test_should_evict_expired_entry(self):
        """期限切れエントリの削除判定テスト"""
        expired_entry = Mock(spec=CacheEntry)
        expired_entry.is_expired.return_value = True
        expired_entry.access_count = 10  # 高頻度でも期限切れなら削除

        assert self.strategy.should_evict(expired_entry) is True

    def test_get_priority_ordering(self):
        """優先度取得テスト"""
        entry1 = Mock(spec=CacheEntry)
        entry1.access_count = 1

        entry2 = Mock(spec=CacheEntry)
        entry2.access_count = 5

        entry3 = Mock(spec=CacheEntry)
        entry3.access_count = 3

        # アクセス頻度が低いほど優先度が低い（先に削除）
        assert self.strategy.get_priority(entry1) < self.strategy.get_priority(entry3)
        assert self.strategy.get_priority(entry3) < self.strategy.get_priority(entry2)

    def test_custom_threshold(self):
        """カスタム閾値テスト"""
        custom_strategy = FrequencyBasedStrategy(frequency_threshold=10)

        entry = Mock(spec=CacheEntry)
        entry.is_expired.return_value = False
        entry.access_count = 5

        # 閾値10の場合、access_count=5は削除対象
        assert custom_strategy.should_evict(entry) is True

        entry.access_count = 15
        # 閾値10の場合、access_count=15は保持
        assert custom_strategy.should_evict(entry) is False


class TestSizeAwareStrategy:
    """サイズ認識戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = SizeAwareStrategy(max_size_mb=5.0)  # 5MB閾値

    def test_size_strategy_initialization(self):
        """サイズ戦略初期化テスト"""
        expected_bytes = 5.0 * 1024 * 1024  # 5MB in bytes
        assert self.strategy.max_size_bytes == expected_bytes

    def test_should_evict_large_file(self):
        """大きなファイルの削除判定テスト"""
        large_entry = Mock(spec=CacheEntry)
        large_entry.is_expired.return_value = False
        large_entry.size_bytes = 10 * 1024 * 1024  # 10MB

        assert self.strategy.should_evict(large_entry) is True

    def test_should_evict_small_file(self):
        """小さなファイルの保持判定テスト"""
        small_entry = Mock(spec=CacheEntry)
        small_entry.is_expired.return_value = False
        small_entry.size_bytes = 1 * 1024 * 1024  # 1MB

        assert self.strategy.should_evict(small_entry) is False

    def test_should_evict_no_size_info(self):
        """サイズ情報なしエントリの処理テスト"""
        no_size_entry = Mock(spec=CacheEntry)
        no_size_entry.is_expired.return_value = False
        no_size_entry.size_bytes = None

        # サイズ情報がない場合は保持
        assert self.strategy.should_evict(no_size_entry) is False

    def test_should_evict_expired_entry(self):
        """期限切れエントリの削除判定テスト"""
        expired_entry = Mock(spec=CacheEntry)
        expired_entry.is_expired.return_value = True
        expired_entry.size_bytes = 1024  # 小さなファイルでも期限切れなら削除

        assert self.strategy.should_evict(expired_entry) is True

    def test_get_priority_ordering(self):
        """優先度取得テスト"""
        small_entry = Mock(spec=CacheEntry)
        small_entry.size_bytes = 1024  # 1KB

        large_entry = Mock(spec=CacheEntry)
        large_entry.size_bytes = 10 * 1024 * 1024  # 10MB

        no_size_entry = Mock(spec=CacheEntry)
        no_size_entry.size_bytes = None

        # ファイルサイズが大きいほど優先度が低い（先に削除）
        assert self.strategy.get_priority(small_entry) < self.strategy.get_priority(
            large_entry
        )
        assert self.strategy.get_priority(no_size_entry) == 0.0

    def test_custom_size_threshold(self):
        """カスタムサイズ閾値テスト"""
        custom_strategy = SizeAwareStrategy(max_size_mb=1.0)  # 1MB閾値

        entry = Mock(spec=CacheEntry)
        entry.is_expired.return_value = False
        entry.size_bytes = 2 * 1024 * 1024  # 2MB

        # 閾値1MBの場合、2MBファイルは削除対象
        assert custom_strategy.should_evict(entry) is True


class TestAdaptiveStrategy:
    """適応型戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = AdaptiveStrategy(frequency_weight=0.7, size_weight=0.3)

    def test_adaptive_strategy_initialization(self):
        """適応型戦略初期化テスト"""
        assert self.strategy.frequency_weight == 0.7
        assert self.strategy.size_weight == 0.3

    def test_should_evict_only_expired(self):
        """適応型戦略は期限切れのみ削除判定テスト"""
        entry = Mock(spec=CacheEntry)
        entry.is_expired.return_value = False

        # 期限切れでなければ保持
        assert self.strategy.should_evict(entry) is False

        entry.is_expired.return_value = True
        # 期限切れなら削除
        assert self.strategy.should_evict(entry) is True

    def test_get_priority_calculation(self):
        """優先度計算テスト"""
        entry = Mock(spec=CacheEntry)
        entry.access_count = 5
        entry.size_bytes = 2048  # 2KB

        priority = self.strategy.get_priority(entry)

        # 負の値になることを確認（重み付き合計の反転）
        assert priority < 0

        # 計算ロジックの確認
        frequency_score = 5
        size_score = 1.0 / 2048
        expected = -(0.7 * frequency_score + 0.3 * size_score)
        assert abs(priority - expected) < 0.001

    def test_priority_with_no_size(self):
        """サイズ情報なしでの優先度計算テスト"""
        entry = Mock(spec=CacheEntry)
        entry.access_count = 3
        entry.size_bytes = None

        priority = self.strategy.get_priority(entry)

        # サイズ情報がない場合のデフォルト処理確認
        assert priority < 0


class TestPerformanceAwareStrategy:
    """パフォーマンス重視戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = PerformanceAwareStrategy()

    def test_performance_strategy_initialization(self):
        """パフォーマンス戦略初期化テスト"""
        assert hasattr(self.strategy, "processing_costs")
        assert isinstance(self.strategy.processing_costs, dict)
        assert len(self.strategy.processing_costs) == 0

    def test_should_evict_only_expired(self):
        """パフォーマンス戦略は期限切れのみ削除判定テスト"""
        entry = Mock(spec=CacheEntry)
        entry.is_expired.return_value = False

        assert self.strategy.should_evict(entry) is False

        entry.is_expired.return_value = True
        assert self.strategy.should_evict(entry) is True

    def test_get_priority_calculation(self):
        """優先度計算テスト"""
        now = datetime.now()
        entry = Mock(spec=CacheEntry)
        entry.last_accessed = now
        entry.access_count = 8

        priority = self.strategy.get_priority(entry)

        # アクセス頻度と最新アクセスの組み合わせによる負の値
        assert priority < 0

        # 計算ロジックの確認
        access_score = now.timestamp()
        frequency_score = 8
        expected = -(frequency_score * 0.7 + access_score * 0.3)
        assert abs(priority - expected) < 0.001

    def test_processing_costs_tracking(self):
        """処理コスト追跡機能テスト"""
        # 処理コスト記録の基本機能確認
        self.strategy.processing_costs["test_key"] = 1.5
        assert self.strategy.processing_costs["test_key"] == 1.5


class TestStrategiesIntegration:
    """戦略統合テスト"""

    def test_all_strategies_implement_interface(self):
        """全戦略がインターフェースを実装していることのテスト"""
        strategies = [
            FrequencyBasedStrategy(),
            SizeAwareStrategy(),
            AdaptiveStrategy(),
            PerformanceAwareStrategy(),
        ]

        for strategy in strategies:
            # CacheStrategyインターフェースの実装確認
            assert hasattr(strategy, "should_evict")
            assert hasattr(strategy, "get_priority")
            assert callable(strategy.should_evict)
            assert callable(strategy.get_priority)

    def test_strategy_priority_consistency(self):
        """戦略間の優先度一貫性テスト"""
        # テスト用エントリ作成
        high_freq_entry = Mock(spec=CacheEntry)
        high_freq_entry.is_expired.return_value = False
        high_freq_entry.access_count = 10
        high_freq_entry.size_bytes = 1024
        high_freq_entry.last_accessed = datetime.now()

        low_freq_entry = Mock(spec=CacheEntry)
        low_freq_entry.is_expired.return_value = False
        low_freq_entry.access_count = 1
        low_freq_entry.size_bytes = 1024
        low_freq_entry.last_accessed = datetime.now() - timedelta(hours=1)

        # FrequencyBasedStrategyで高頻度エントリが保護されることを確認
        freq_strategy = FrequencyBasedStrategy(frequency_threshold=5)
        assert freq_strategy.get_priority(high_freq_entry) > freq_strategy.get_priority(
            low_freq_entry
        )
