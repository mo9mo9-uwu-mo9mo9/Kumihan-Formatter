"""キャッシュストレージテスト - Issue #596 Week 25-26対応

キャッシュストレージシステムの詳細テスト
メモリ・ファイルストレージの統合管理と効率性の確認
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from kumihan_formatter.core.caching.basic_strategies import LRUStrategy
from kumihan_formatter.core.caching.cache_storage import CacheStorage
from kumihan_formatter.core.caching.cache_types import CacheEntry


class TestCacheStorage:
    """キャッシュストレージテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage = CacheStorage(
            name="test_cache",
            max_memory_entries=10,
            max_memory_bytes=1024 * 1024,  # 1MB
            strategy=LRUStrategy(),
            cache_dir=self.temp_dir,
            enable_file_cache=True,
        )

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "storage"):
            self.storage.clear_memory()

    def test_storage_initialization(self):
        """ストレージ初期化テスト"""
        assert self.storage.name == "test_cache"
        assert self.storage.max_memory_entries == 10
        assert self.storage.max_memory_bytes == 1024 * 1024
        assert self.storage.cache_dir == self.temp_dir
        assert self.storage.enable_file_cache is True
        assert len(self.storage._memory_cache) == 0

    def test_store_and_get_from_memory(self):
        """メモリストレージ保存・取得テスト"""
        # エントリを作成
        entry = CacheEntry(
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=3600,
            size_bytes=len("test_value"),
        )

        # メモリに保存
        self.storage.store_in_memory("test_key", entry)

        # メモリから取得
        retrieved_entry = self.storage.get_from_memory("test_key")
        assert retrieved_entry is not None
        assert retrieved_entry.value == "test_value"

    def test_memory_stats(self):
        """メモリ統計テスト"""
        # 初期状態の統計
        stats = self.storage.get_memory_stats()
        assert stats["entries"] == 0
        assert stats["size_bytes"] == 0
        assert stats["max_entries"] == 10
        assert stats["max_bytes"] == 1024 * 1024

        # エントリ追加後の統計
        entry = CacheEntry(
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            size_bytes=100,
        )
        self.storage.store_in_memory("test_key", entry)

        stats = self.storage.get_memory_stats()
        assert stats["entries"] == 1
        # サイズは計算されたもの（実際の文字列"test_value"のバイト数）
        assert stats["size_bytes"] > 0

    def test_eviction_when_capacity_exceeded(self):
        """容量超過時の削除テスト"""
        # 容量を超えるエントリを追加
        for i in range(15):  # max_memory_entries=10を超える
            entry = CacheEntry(
                value=f"value_{i}",
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                size_bytes=10,
            )
            self.storage.store_in_memory(f"key_{i}", entry)

        # エントリ数が制限内に収まっていることを確認
        stats = self.storage.get_memory_stats()
        assert stats["entries"] <= 10
