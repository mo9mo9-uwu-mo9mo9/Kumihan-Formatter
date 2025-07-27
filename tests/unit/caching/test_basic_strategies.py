"""基本キャッシュ戦略テスト - Issue #596 Week 23-24対応

LRU・FIFO基本戦略の詳細テスト
キャッシュアルゴリズムの正確性確認
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.caching.basic_strategies import (
    CacheStrategy,
    FIFOStrategy,
    LFUStrategy,
    LRUStrategy,
    TTLStrategy,
)


class TestLRUStrategy:
    """LRU戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = LRUStrategy()

    def test_lru_strategy_initialization(self):
        """LRU戦略初期化テスト"""
        # LRUStrategyは単純なクラスで、特別な初期化は不要
        assert isinstance(self.strategy, LRUStrategy)

    def test_lru_priority_calculation(self):
        """LRU優先度計算テスト"""
        from kumihan_formatter.core.caching.cache_types import CacheEntry

        # 異なるアクセス時刻のエントリを作成
        now = datetime.now()
        older_entry = Mock(spec=CacheEntry)
        older_entry.last_accessed = now - timedelta(seconds=10)

        newer_entry = Mock(spec=CacheEntry)
        newer_entry.last_accessed = now

        # 古いエントリほど優先度が低い（削除されやすい）
        assert self.strategy.get_priority(older_entry) < self.strategy.get_priority(
            newer_entry
        )

    def test_should_evict_expired_entry(self):
        """期限切れエントリの削除判定テスト"""
        expired_entry = Mock()
        expired_entry.is_expired.return_value = True

        valid_entry = Mock()
        valid_entry.is_expired.return_value = False

        # 期限切れエントリは削除対象
        assert self.strategy.should_evict(expired_entry) is True
        # 有効なエントリは削除対象外
        assert self.strategy.should_evict(valid_entry) is False


class TestLFUStrategy:
    """LFU戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = LFUStrategy()

    def test_lfu_priority_calculation(self):
        """LFU優先度計算テスト"""
        low_freq_entry = Mock()
        low_freq_entry.access_count = 2

        high_freq_entry = Mock()
        high_freq_entry.access_count = 10

        # アクセス頻度が低いほど優先度が低い（削除されやすい）
        assert self.strategy.get_priority(low_freq_entry) < self.strategy.get_priority(
            high_freq_entry
        )


class TestFIFOStrategy:
    """FIFO戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = FIFOStrategy()

    def test_fifo_priority_calculation(self):
        """FIFO優先度計算テスト"""
        now = datetime.now()
        older_entry = Mock()
        older_entry.created_at = now - timedelta(seconds=10)

        newer_entry = Mock()
        newer_entry.created_at = now

        # 古いエントリほど優先度が低い（削除されやすい）
        assert self.strategy.get_priority(older_entry) < self.strategy.get_priority(
            newer_entry
        )


class TestTTLStrategy:
    """TTL戦略テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.strategy = TTLStrategy()

    def test_ttl_priority_calculation(self):
        """TTL優先度計算テスト"""
        now = datetime.now()
        older_entry = Mock()
        older_entry.created_at = now - timedelta(seconds=10)

        newer_entry = Mock()
        newer_entry.created_at = now

        # 作成時刻が古いほど優先度が低い（削除されやすい）
        assert self.strategy.get_priority(older_entry) < self.strategy.get_priority(
            newer_entry
        )
