"""キャッシュストレージテスト - Issue #596 Week 25-26対応

キャッシュストレージシステムの詳細テスト
メモリ・ファイルストレージの統合管理と効率性の確認
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

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
            self.storage.clear()

    def test_storage_initialization(self):
        """ストレージ初期化テスト"""
        assert self.storage.name == "test_cache"
        assert self.storage.max_memory_entries == 10
        assert self.storage.max_memory_bytes == 1024 * 1024
        assert self.storage.cache_dir == self.temp_dir
        assert self.storage.enable_file_cache is True
        assert len(self.storage.memory_storage) == 0

    def test_store_and_get_from_memory(self):
        """メモリストレージ保存・取得テスト"""
        # エントリを作成
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=time.time(),
            ttl=3600,
            size_bytes=len("test_value"),
        )

        # メモリに保存
        success = self.storage.store_in_memory("test_key", entry)
        assert success

        # メモリから取得
        retrieved_entry = self.storage.get_from_memory("test_key")
        assert retrieved_entry is not None
        assert retrieved_entry.value == "test_value"
        assert retrieved_entry.key == "test_key"

    def test_memory_capacity_limits(self):
        """メモリ容量制限テスト"""
        # エントリ数制限のテスト
        for i in range(15):  # max_memory_entries=10を超える
            entry = CacheEntry(
                key=f"key_{i}",
                value=f"value_{i}",
                created_at=time.time(),
                ttl=3600,
                size_bytes=10,
            )
            self.storage.store_in_memory(f"key_{i}", entry)

        # エントリ数が制限内に収まることを確認
        assert len(self.storage.memory_storage) <= 10

        # 古いエントリが削除されていることを確認（LRU戦略）
        assert self.storage.get_from_memory("key_0") is None
        assert self.storage.get_from_memory("key_14") is not None

    def test_memory_size_limits(self):
        """メモリサイズ制限テスト"""
        # 大きなエントリを作成（1MBに近い）
        large_value = "A" * (500 * 1024)  # 500KB

        entry1 = CacheEntry(
            key="large_1",
            value=large_value,
            created_at=time.time(),
            ttl=3600,
            size_bytes=len(large_value),
        )

        entry2 = CacheEntry(
            key="large_2",
            value=large_value,
            created_at=time.time(),
            ttl=3600,
            size_bytes=len(large_value),
        )

        # 最初のエントリを保存
        success1 = self.storage.store_in_memory("large_1", entry1)
        assert success1

        # 2番目のエントリを保存（サイズ制限を超える）
        success2 = self.storage.store_in_memory("large_2", entry2)

        # サイズ制限により、古いエントリが削除される
        total_size = self.storage.get_memory_usage_bytes()
        assert total_size <= 1024 * 1024  # 1MB以下

    def test_file_cache_storage_and_retrieval(self):
        """ファイルキャッシュ保存・取得テスト"""
        entry = CacheEntry(
            key="file_test_key",
            value="file_test_value",
            created_at=time.time(),
            ttl=3600,
            size_bytes=len("file_test_value"),
        )

        # ファイルに保存
        success = self.storage.save_to_file("file_test_key", entry)
        assert success

        # ファイルから取得
        retrieved_entry = self.storage.load_from_file("file_test_key")
        assert retrieved_entry is not None
        assert retrieved_entry.value == "file_test_value"
        assert retrieved_entry.key == "file_test_key"

    def test_file_cache_disabled(self):
        """ファイルキャッシュ無効時のテスト"""
        # ファイルキャッシュを無効にしたストレージ
        storage_no_file = CacheStorage(
            name="no_file_cache",
            max_memory_entries=10,
            max_memory_bytes=1024 * 1024,
            strategy=LRUStrategy(),
            enable_file_cache=False,
        )

        entry = CacheEntry(
            key="no_file_key",
            value="no_file_value",
            created_at=time.time(),
            ttl=3600,
            size_bytes=len("no_file_value"),
        )

        # ファイル保存が無効
        success = storage_no_file.save_to_file("no_file_key", entry)
        assert not success

        # ファイル取得が無効
        retrieved_entry = storage_no_file.load_from_file("no_file_key")
        assert retrieved_entry is None

        storage_no_file.clear()

    def test_ttl_expiration(self):
        """TTL期限切れテスト"""
        with patch("time.time") as mock_time:
            # 現在時刻を設定
            mock_time.return_value = 1000.0

            entry = CacheEntry(
                key="expire_test",
                value="expire_value",
                created_at=1000.0,
                ttl=10,  # 10秒のTTL
                size_bytes=len("expire_value"),
            )

            # エントリを保存
            self.storage.store_in_memory("expire_test", entry)

            # 有効期限内での取得
            retrieved = self.storage.get_from_memory("expire_test")
            assert retrieved is not None

            # 時間を進める（期限切れ）
            mock_time.return_value = 1015.0  # 15秒後

            # 期限切れエントリは取得できない
            expired = self.storage.get_from_memory("expire_test")
            assert expired is None

    def test_memory_usage_calculation(self):
        """メモリ使用量計算テスト"""
        # 初期状態での使用量確認
        assert self.storage.get_memory_usage_bytes() == 0

        # エントリを追加
        entries = []
        total_expected_size = 0

        for i in range(5):
            value = f"test_value_{i}" * 10  # サイズを可変に
            entry = CacheEntry(
                key=f"size_test_{i}",
                value=value,
                created_at=time.time(),
                ttl=3600,
                size_bytes=len(value),
            )
            entries.append(entry)
            total_expected_size += len(value)

            self.storage.store_in_memory(f"size_test_{i}", entry)

        # 使用量が正しく計算される
        actual_usage = self.storage.get_memory_usage_bytes()
        assert actual_usage == total_expected_size

    def test_clear_storage(self):
        """ストレージクリアテスト"""
        # エントリを追加
        for i in range(5):
            entry = CacheEntry(
                key=f"clear_test_{i}",
                value=f"value_{i}",
                created_at=time.time(),
                ttl=3600,
                size_bytes=10,
            )
            self.storage.store_in_memory(f"clear_test_{i}", entry)

        # 削除前の確認
        assert len(self.storage.memory_storage) == 5
        assert self.storage.get_memory_usage_bytes() > 0

        # クリア実行
        self.storage.clear()

        # 削除後の確認
        assert len(self.storage.memory_storage) == 0
        assert self.storage.get_memory_usage_bytes() == 0

    def test_remove_entry(self):
        """エントリ削除テスト"""
        entry = CacheEntry(
            key="remove_test",
            value="remove_value",
            created_at=time.time(),
            ttl=3600,
            size_bytes=len("remove_value"),
        )

        # エントリを保存
        self.storage.store_in_memory("remove_test", entry)
        assert self.storage.get_from_memory("remove_test") is not None

        # エントリを削除
        success = self.storage.remove_from_memory("remove_test")
        assert success

        # 削除されていることを確認
        assert self.storage.get_from_memory("remove_test") is None

        # 存在しないエントリの削除
        success = self.storage.remove_from_memory("nonexistent")
        assert not success

    def test_file_cache_serialization(self):
        """ファイルキャッシュシリアライゼーションテスト"""
        # 複雑なオブジェクトのエントリ
        complex_value = {
            "string": "test",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        entry = CacheEntry(
            key="complex_test",
            value=complex_value,
            created_at=time.time(),
            ttl=3600,
            size_bytes=len(str(complex_value)),
        )

        # ファイルに保存
        success = self.storage.save_to_file("complex_test", entry)
        assert success

        # ファイルから取得
        retrieved_entry = self.storage.load_from_file("complex_test")
        assert retrieved_entry is not None
        assert retrieved_entry.value == complex_value

    def test_concurrent_access(self):
        """並行アクセステスト"""
        import threading

        results = []
        errors = []

        def concurrent_storage_operation(thread_id):
            try:
                # 各スレッドで異なるエントリを操作
                for i in range(10):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"

                    entry = CacheEntry(
                        key=key,
                        value=value,
                        created_at=time.time(),
                        ttl=3600,
                        size_bytes=len(value),
                    )

                    # 保存
                    success = self.storage.store_in_memory(key, entry)

                    # 取得
                    retrieved = self.storage.get_from_memory(key)

                    results.append((thread_id, success, retrieved is not None))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_storage_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行アクセスでエラーが発生: {errors}"
        assert len(results) == 30  # 3スレッド × 10操作

        # すべての操作が成功していることを確認
        for thread_id, store_success, retrieve_success in results:
            assert store_success
            assert retrieve_success

    def test_storage_statistics(self):
        """ストレージ統計テスト"""
        # エントリを追加
        for i in range(7):
            entry = CacheEntry(
                key=f"stats_test_{i}",
                value=f"value_{i}" * (i + 1),  # 可変サイズ
                created_at=time.time(),
                ttl=3600,
                size_bytes=len(f"value_{i}" * (i + 1)),
            )
            self.storage.store_in_memory(f"stats_test_{i}", entry)

        # 統計情報の確認
        stats = self.storage.get_statistics()

        assert "memory_entries" in stats
        assert "memory_usage_bytes" in stats
        assert "memory_usage_mb" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats

        assert stats["memory_entries"] == 7
        assert stats["memory_usage_bytes"] > 0
        assert stats["memory_usage_mb"] > 0

    def test_cleanup_expired_entries(self):
        """期限切れエントリクリーンアップテスト"""
        with patch("time.time") as mock_time:
            # 現在時刻を設定
            mock_time.return_value = 1000.0

            # 異なるTTLのエントリを作成
            entries_data = [
                ("short_ttl", 5),  # 5秒で期限切れ
                ("medium_ttl", 15),  # 15秒で期限切れ
                ("long_ttl", 25),  # 25秒で期限切れ
            ]

            for key, ttl in entries_data:
                entry = CacheEntry(
                    key=key,
                    value=f"value_{key}",
                    created_at=1000.0,
                    ttl=ttl,
                    size_bytes=10,
                )
                self.storage.store_in_memory(key, entry)

            # 時間を進める（10秒後）
            mock_time.return_value = 1010.0

            # クリーンアップ実行
            cleaned_count = self.storage.cleanup_expired_entries()

            # short_ttlのみが削除される
            assert cleaned_count == 1
            assert self.storage.get_from_memory("short_ttl") is None
            assert self.storage.get_from_memory("medium_ttl") is not None
            assert self.storage.get_from_memory("long_ttl") is not None


class TestCacheStorageEdgeCases:
    """キャッシュストレージエッジケーステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_storage_with_zero_limits(self):
        """ゼロ制限でのストレージテスト"""
        # ゼロ制限のストレージ
        storage = CacheStorage(
            name="zero_limit",
            max_memory_entries=0,
            max_memory_bytes=0,
            strategy=LRUStrategy(),
        )

        entry = CacheEntry(
            key="zero_test",
            value="zero_value",
            created_at=time.time(),
            ttl=3600,
            size_bytes=10,
        )

        # エントリが保存されない
        success = storage.store_in_memory("zero_test", entry)
        assert not success

        storage.clear()

    def test_storage_with_invalid_cache_dir(self):
        """無効なキャッシュディレクトリでのテスト"""
        # 存在しないディレクトリ
        invalid_dir = Path("/nonexistent/directory")

        storage = CacheStorage(
            name="invalid_dir",
            max_memory_entries=10,
            max_memory_bytes=1024,
            strategy=LRUStrategy(),
            cache_dir=invalid_dir,
            enable_file_cache=True,
        )

        entry = CacheEntry(
            key="invalid_dir_test",
            value="test_value",
            created_at=time.time(),
            ttl=3600,
            size_bytes=10,
        )

        # ファイル保存が失敗する
        success = storage.save_to_file("invalid_dir_test", entry)
        assert not success

        storage.clear()

    def test_storage_with_corrupted_file(self):
        """破損ファイルからの読み込みテスト"""
        storage = CacheStorage(
            name="corrupted_test",
            max_memory_entries=10,
            max_memory_bytes=1024,
            strategy=LRUStrategy(),
            cache_dir=self.temp_dir,
            enable_file_cache=True,
        )

        # 破損したキャッシュファイルを作成
        cache_file = self.temp_dir / "corrupted_test_corrupted_key.cache"
        cache_file.write_text("invalid pickle data", encoding="utf-8")

        # 破損ファイルからの読み込みは失敗する
        retrieved = storage.load_from_file("corrupted_key")
        assert retrieved is None

        storage.clear()

    def test_storage_performance_with_large_dataset(self):
        """大規模データセットでのストレージ性能テスト"""
        storage = CacheStorage(
            name="large_dataset",
            max_memory_entries=1000,
            max_memory_bytes=10 * 1024 * 1024,  # 10MB
            strategy=LRUStrategy(),
        )

        # 大量のエントリを保存
        start_time = time.time()

        for i in range(500):
            entry = CacheEntry(
                key=f"large_key_{i}",
                value=f"large_value_{i}" * 100,  # 中程度のサイズ
                created_at=time.time(),
                ttl=3600,
                size_bytes=len(f"large_value_{i}" * 100),
            )
            storage.store_in_memory(f"large_key_{i}", entry)

        execution_time = time.time() - start_time

        # 合理的な時間で完了することを確認
        assert execution_time < 2.0, f"大規模データ操作が遅すぎます: {execution_time}秒"

        # ストレージが正常に動作していることを確認
        stats = storage.get_statistics()
        assert stats["memory_entries"] <= 1000
        assert stats["memory_usage_bytes"] <= 10 * 1024 * 1024

        storage.clear()

    def test_storage_memory_fragmentation(self):
        """メモリ断片化テスト"""
        storage = CacheStorage(
            name="fragmentation_test",
            max_memory_entries=20,
            max_memory_bytes=1024,  # 小さなメモリ制限
            strategy=LRUStrategy(),
        )

        # 異なるサイズのエントリを追加・削除を繰り返す
        for cycle in range(5):
            # 大きなエントリを追加
            for i in range(5):
                large_value = "A" * 100
                entry = CacheEntry(
                    key=f"large_{cycle}_{i}",
                    value=large_value,
                    created_at=time.time(),
                    ttl=3600,
                    size_bytes=len(large_value),
                )
                storage.store_in_memory(f"large_{cycle}_{i}", entry)

            # 小さなエントリを追加
            for i in range(10):
                small_value = "B" * 10
                entry = CacheEntry(
                    key=f"small_{cycle}_{i}",
                    value=small_value,
                    created_at=time.time(),
                    ttl=3600,
                    size_bytes=len(small_value),
                )
                storage.store_in_memory(f"small_{cycle}_{i}", entry)

        # メモリ使用量が制限内であることを確認
        stats = storage.get_statistics()
        assert stats["memory_usage_bytes"] <= 1024

        storage.clear()
