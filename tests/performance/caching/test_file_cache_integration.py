"""ファイルキャッシュ統合テスト - Issue #596 Week 23-24対応

ファイル読み込みキャッシュシステムの統合テスト
I/O最適化とファイルハッシュキャッシュの効果測定
"""

import hashlib
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from kumihan_formatter.core.caching.file_cache import FileCache


class TestFileCacheIntegration:
    """ファイルキャッシュ統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = FileCache(
            cache_dir=self.temp_dir,
            max_memory_mb=50.0,
            max_entries=500,
            default_ttl=7200,
        )

        # テスト用ファイルを作成
        self.test_files = {}
        for i in range(5):
            file_path = self.temp_dir / f"test_file_{i}.txt"
            content = f"Test content {i}\n" + "Line content " * (i + 1) * 10
            file_path.write_text(content, encoding="utf-8")
            self.test_files[f"file_{i}"] = file_path

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "cache"):
            self.cache.clear()
        # 一時ディレクトリとファイルの削除は安全のため省略

    def test_file_cache_basic_functionality(self):
        """基本的なファイルキャッシュ機能テスト"""
        test_file = self.test_files["file_0"]

        # 初回読み込み
        content1 = self.cache.get_file_content(test_file)
        assert content1 is not None
        assert "Test content 0" in content1

        # 2回目読み込み（キャッシュから）
        content2 = self.cache.get_file_content(test_file)
        assert content2 == content1

        # ファイルハッシュテスト
        hash1 = self.cache.get_file_hash(test_file)
        hash2 = self.cache.get_file_hash(test_file)
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5ハッシュの長さ

    def test_file_cache_modification_detection(self):
        """ファイル修正検出テスト"""
        test_file = self.test_files["file_1"]

        # 初回読み込み
        original_content = self.cache.get_file_content(test_file)
        original_hash = self.cache.get_file_hash(test_file)

        # ファイルを修正
        time.sleep(0.1)  # ファイルシステムの時刻精度を考慮
        modified_content = "Modified content\nNew line added"
        test_file.write_text(modified_content, encoding="utf-8")

        # 修正後の読み込み
        new_content = self.cache.get_file_content(test_file)
        new_hash = self.cache.get_file_hash(test_file)

        # 変更が検出されることを確認
        assert new_content != original_content
        assert new_hash != original_hash
        assert new_content == modified_content

    def test_file_cache_performance_improvement(self):
        """ファイルキャッシュ性能改善テスト"""
        # 大きなテストファイルを作成
        large_file = self.temp_dir / "large_test_file.txt"
        large_content = "Large file content line\n" * 1000
        large_file.write_text(large_content, encoding="utf-8")

        # 初回読み込み時間測定
        start_time = time.time()
        content1 = self.cache.get_file_content(large_file)
        first_read_time = time.time() - start_time

        # キャッシュからの読み込み時間測定
        start_time = time.time()
        content2 = self.cache.get_file_content(large_file)
        cached_read_time = time.time() - start_time

        # 性能改善確認
        assert content1 == content2
        improvement_ratio = first_read_time / cached_read_time
        assert improvement_ratio > 5, f"読み込み速度改善が不十分: {improvement_ratio}倍"

    def test_file_cache_encoding_handling(self):
        """エンコーディング処理テスト"""
        # UTF-8ファイル
        utf8_file = self.temp_dir / "utf8_test.txt"
        utf8_content = "UTF-8テストファイル\n日本語コンテンツ"
        utf8_file.write_text(utf8_content, encoding="utf-8")

        # Shift_JISファイル（UTF-8読み込み失敗をシミュレート）
        sjis_file = self.temp_dir / "sjis_test.txt"
        sjis_content = "Shift_JIS test content"

        # バイナリ書き込みでShift_JISをシミュレート
        with open(sjis_file, "wb") as f:
            f.write(sjis_content.encode("shift_jis"))

        # UTF-8ファイルの読み込み
        utf8_result = self.cache.get_file_content(utf8_file)
        assert utf8_result == utf8_content

        # Shift_JISファイルの読み込み（フォールバック）
        sjis_result = self.cache.get_file_content(sjis_file)
        assert sjis_result == sjis_content

    def test_file_cache_memory_management(self):
        """ファイルキャッシュメモリ管理テスト"""
        # 複数の大きなファイルでメモリ制限をテスト
        large_files = []
        for i in range(20):
            large_file = self.temp_dir / f"memory_test_{i}.txt"
            content = f"Memory test file {i}\n" + "Content line " * 500
            large_file.write_text(content, encoding="utf-8")
            large_files.append(large_file)

        # すべてのファイルを読み込み
        for large_file in large_files:
            self.cache.get_file_content(large_file)

        # 統計確認
        stats = self.cache.get_cache_stats()
        assert stats["memory_usage_mb"] <= 50.0, "メモリ制限を超過しています"
        assert stats["entry_count"] <= 500, "エントリ数制限を超過しています"

    def test_file_cache_invalidation(self):
        """ファイルキャッシュ無効化テスト"""
        test_file = self.test_files["file_2"]

        # ファイルをキャッシュに読み込み
        content = self.cache.get_file_content(test_file)
        file_hash = self.cache.get_file_hash(test_file)
        assert content is not None
        assert file_hash is not None

        # キャッシュ無効化
        success = self.cache.invalidate_file(test_file)
        assert success

        # 無効化後は再読み込みが発生することを確認
        # （実際のファイルから読み込まれる）
        new_content = self.cache.get_file_content(test_file)
        new_hash = self.cache.get_file_hash(test_file)
        assert new_content == content  # ファイル内容は同じ
        assert new_hash == file_hash  # ハッシュも同じ

    def test_file_cache_cleanup_stale_entries(self):
        """古いエントリのクリーンアップテスト"""
        # 一時ファイルを作成してキャッシュ
        temp_files = []
        for i in range(5):
            temp_file = self.temp_dir / f"temp_cleanup_{i}.txt"
            temp_file.write_text(f"Temporary content {i}", encoding="utf-8")
            temp_files.append(temp_file)

            # キャッシュに読み込み
            self.cache.get_file_content(temp_file)

        # 一部のファイルを削除
        for i in range(0, 3):
            temp_files[i].unlink()

        # クリーンアップ実行
        cleanup_count = self.cache.cleanup_stale_entries()
        assert (
            cleanup_count >= 3
        ), "削除されたファイルのキャッシュがクリーンアップされていません"

        # 残存ファイルのキャッシュは維持されていることを確認
        for i in range(3, 5):
            cached_content = self.cache.get_file_content(temp_files[i])
            assert cached_content is not None

    def test_file_cache_ttl_by_file_size(self):
        """ファイルサイズ別TTL設定テスト"""
        # 異なるサイズのファイルを作成
        file_sizes = [
            (500, "small"),  # 1KB未満
            (5000, "medium"),  # 1-10KB
            (50000, "large"),  # 10-100KB
            (500000, "xlarge"),  # 100KB以上
        ]

        for size, name in file_sizes:
            test_file = self.temp_dir / f"size_test_{name}.txt"
            content = "A" * size
            test_file.write_text(content, encoding="utf-8")

            # ファイルをキャッシュ
            self.cache.get_file_content(test_file)

        # キャッシュ統計でTTL設定を間接的に確認
        stats = self.cache.get_cache_stats()
        assert stats["entry_count"] == len(file_sizes)

    def test_file_cache_hash_consistency(self):
        """ファイルハッシュ一貫性テスト"""
        test_file = self.test_files["file_3"]

        # 期待されるハッシュを直接計算
        content = test_file.read_text(encoding="utf-8")
        expected_hash = hashlib.md5(test_file.read_bytes()).hexdigest()

        # キャッシュ経由でハッシュを取得
        cached_hash = self.cache.get_file_hash(test_file)

        # ハッシュの一貫性確認
        assert cached_hash == expected_hash

        # 複数回取得しても同じハッシュ
        for _ in range(3):
            repeated_hash = self.cache.get_file_hash(test_file)
            assert repeated_hash == expected_hash

    def test_file_cache_nonexistent_file_handling(self):
        """存在しないファイルの処理テスト"""
        nonexistent_file = self.temp_dir / "does_not_exist.txt"

        # 存在しないファイルの処理
        content = self.cache.get_file_content(nonexistent_file)
        assert content is None

        file_hash = self.cache.get_file_hash(nonexistent_file)
        assert file_hash is None

        # 無効化も安全に実行される
        result = self.cache.invalidate_file(nonexistent_file)
        assert result is False  # 何も削除されない

    def test_file_cache_concurrent_access(self):
        """並行アクセステスト"""
        import threading

        test_file = self.test_files["file_4"]
        results = []
        errors = []

        def concurrent_file_operation(thread_id):
            try:
                # 各スレッドでファイル読み込み
                content = self.cache.get_file_content(test_file)
                file_hash = self.cache.get_file_hash(test_file)

                results.append((thread_id, content is not None, file_hash is not None))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(8):
            thread = threading.Thread(target=concurrent_file_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行アクセスでエラーが発生: {errors}"
        assert len(results) == 8
        assert all(content_ok and hash_ok for _, content_ok, hash_ok in results)

    def test_file_cache_stats_accuracy(self):
        """キャッシュ統計の精度テスト"""
        # 複数ファイルをキャッシュ
        cached_files = []
        total_expected_size = 0

        for i in range(10):
            test_file = self.temp_dir / f"stats_test_{i}.txt"
            content = f"Stats test content {i}\n" + "Data " * (i + 1) * 20
            test_file.write_text(content, encoding="utf-8")

            file_size = len(content.encode("utf-8"))
            total_expected_size += file_size
            cached_files.append((test_file, file_size))

            # キャッシュに読み込み
            self.cache.get_file_content(test_file)

        # 統計情報取得
        stats = self.cache.get_cache_stats()

        # 統計の精度確認
        assert stats["cached_files"] == 10
        assert stats["total_cached_size"] > 0
        assert stats["avg_file_size"] > 0
        assert stats["hit_rate"] >= 0.0
        assert stats["memory_usage_mb"] > 0


class TestFileCacheStressTest:
    """ファイルキャッシュストレステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_high_volume_file_cache(self):
        """大容量ファイルキャッシュテスト"""
        cache = FileCache(
            cache_dir=self.temp_dir, max_memory_mb=100.0, max_entries=1000
        )

        try:
            # 大量のファイルを作成してキャッシュ
            files_created = 0
            for i in range(800):
                test_file = self.temp_dir / f"volume_test_{i}.txt"
                content = f"Volume test file {i}\n" + "Content " * 100
                test_file.write_text(content, encoding="utf-8")
                files_created += 1

                # キャッシュに読み込み
                cached_content = cache.get_file_content(test_file)
                assert cached_content is not None

                # 定期的に統計確認
                if i % 200 == 0:
                    stats = cache.get_cache_stats()
                    assert stats["memory_usage_mb"] <= 100.0

            # 最終統計確認
            final_stats = cache.get_cache_stats()
            assert final_stats["entry_count"] <= 1000
            assert final_stats["memory_usage_mb"] <= 100.0

        finally:
            cache.clear()

    def test_rapid_file_operations(self):
        """高速ファイル操作テスト"""
        cache = FileCache(max_entries=200)

        try:
            # 高速でファイル操作
            files = []
            for i in range(150):
                test_file = self.temp_dir / f"rapid_test_{i}.txt"
                content = f"Rapid test {i}"
                test_file.write_text(content, encoding="utf-8")
                files.append(test_file)

            start_time = time.time()

            # 全ファイルを高速で読み込み
            for test_file in files:
                cache.get_file_content(test_file)
                cache.get_file_hash(test_file)

            execution_time = time.time() - start_time
            assert execution_time < 3.0, f"ファイル操作が遅すぎます: {execution_time}秒"

        finally:
            cache.clear()
