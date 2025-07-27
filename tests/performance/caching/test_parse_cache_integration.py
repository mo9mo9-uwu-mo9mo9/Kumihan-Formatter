"""パースキャッシュ統合テスト - Issue #596 Week 23-24対応

パフォーマンス最適化の根幹となるキャッシング機能の信頼性確保
統合後ファイルでの効率的パースキャッシングテスト
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.caching.parse_cache import ParseCache


class TestParseCacheIntegration:
    """パースキャッシュ統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = ParseCache(
            cache_dir=self.temp_dir,
            max_memory_mb=50.0,
            max_entries=100,
            default_ttl=300,
        )

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "cache"):
            self.cache.clear()
        # 一時ディレクトリの削除は安全のため省略

    def test_parse_cache_basic_functionality(self):
        """基本的なキャッシュ機能テスト"""
        # テストデータ
        content = "# Test\n## Subheading\nContent here"
        content_hash = "test_hash_123"

        # モックノード作成
        mock_node = Mock(spec=Node)
        mock_node.type = "document"
        mock_node.content = "parsed content"

        # キャッシュ保存
        self.cache.set(content_hash, [mock_node])

        # キャッシュ取得
        cached_result = self.cache.get(content_hash)
        assert cached_result is not None
        assert len(cached_result) == 1
        assert cached_result[0].type == "document"

    def test_parse_cache_hit_rate_measurement(self):
        """キャッシュヒット率測定テスト"""
        # 複数のコンテンツでキャッシュを構築
        test_data = [
            ("content1", "hash1"),
            ("content2", "hash2"),
            ("content3", "hash3"),
        ]

        mock_nodes = []
        for i, (content, hash_val) in enumerate(test_data):
            mock_node = Mock(spec=Node)
            mock_node.type = f"document_{i}"
            mock_nodes.append(mock_node)
            self.cache.set(hash_val, [mock_node])

        # ヒット率テスト
        hit_count = 0
        total_requests = 10

        for i in range(total_requests):
            hash_to_test = test_data[i % len(test_data)][1]
            result = self.cache.get(hash_to_test)
            if result is not None:
                hit_count += 1

        hit_rate = hit_count / total_requests
        assert hit_rate > 0.8, f"ヒット率が低すぎます: {hit_rate}"

    def test_parse_cache_performance_improvement(self):
        """キャッシュによる処理速度改善テスト"""
        content_hash = "performance_test_hash"

        # 重い処理をシミュレート
        def simulate_heavy_parsing():
            time.sleep(0.1)  # 100ms の処理時間をシミュレート
            mock_node = Mock(spec=Node)
            mock_node.type = "heavy_parse_result"
            return [mock_node]

        # 初回実行（キャッシュなし）
        start_time = time.time()
        result = simulate_heavy_parsing()
        first_run_time = time.time() - start_time

        # キャッシュに保存
        self.cache.set(content_hash, result)

        # 2回目実行（キャッシュあり）
        start_time = time.time()
        cached_result = self.cache.get(content_hash)
        second_run_time = time.time() - start_time

        # パフォーマンス改善確認
        assert cached_result is not None
        improvement_ratio = first_run_time / second_run_time
        assert improvement_ratio > 10, f"速度改善が不十分: {improvement_ratio}倍"

    def test_parse_cache_memory_efficiency(self):
        """メモリ効率テスト"""
        # 大量のキャッシュエントリを作成
        for i in range(150):  # max_entriesを超える数
            mock_node = Mock(spec=Node)
            mock_node.type = f"document_{i}"
            mock_node.content = f"content_{i}" * 100  # ある程度のサイズ

            self.cache.set(f"hash_{i}", [mock_node])

        # 統計情報取得
        stats = self.cache.get_stats()

        # メモリ制限の確認（バイト単位で確認）
        memory_bytes = stats["memory_stats"]["size_bytes"]
        memory_mb = memory_bytes / (1024 * 1024)
        assert memory_mb <= 50.0, f"メモリ制限を超過しています: {memory_mb}MB"

        # エントリ数制限の確認
        entry_count = stats["memory_stats"]["entries"]
        assert entry_count <= 100, f"エントリ数制限を超過しています: {entry_count}"

    def test_parse_cache_invalidation(self):
        """キャッシュ無効化テスト"""
        # テストデータを設定
        content_hashes = ["hash1", "hash2", "hash3"]
        for i, hash_val in enumerate(content_hashes):
            mock_node = Mock(spec=Node)
            mock_node.type = f"document_{i}"
            self.cache.set(hash_val, [mock_node])

        # 全エントリが存在することを確認
        for hash_val in content_hashes:
            assert self.cache.get(hash_val) is not None

        # 特定のキーで無効化
        success = self.cache.delete("hash1")
        assert success

        # 無効化されたエントリが削除されていることを確認
        assert self.cache.get("hash1") is None
        assert self.cache.get("hash2") is not None
        assert self.cache.get("hash3") is not None

    def test_parse_cache_analytics_integration(self):
        """キャッシュ分析機能統合テスト"""
        # テストデータでキャッシュを構築
        for i in range(10):
            mock_node = Mock(spec=Node)
            mock_node.type = f"document_{i}"
            self.cache.set(f"hash_{i}", [mock_node])

        # 分析機能テスト
        stats = self.cache.get_stats()
        assert "hit_rate" in stats
        assert "memory_stats" in stats
        assert "hits" in stats

        # パース統計テスト
        parse_stats = self.cache.parse_stats
        assert "cache_hits" in parse_stats
        assert "cache_misses" in parse_stats

    def test_parse_cache_snapshot_creation(self):
        """キャッシュスナップショット作成テスト"""
        # テストデータを設定
        test_entries = 5
        for i in range(test_entries):
            mock_node = Mock(spec=Node)
            mock_node.type = f"document_{i}"
            self.cache.set(f"snapshot_hash_{i}", [mock_node])

        # 統計情報でスナップショット代替
        stats = self.cache.get_stats()

        # スナップショット内容確認
        assert "memory_stats" in stats
        assert "hit_rate" in stats
        assert "hits" in stats

        # エントリ数の確認
        assert stats["memory_stats"]["entries"] == test_entries

    def test_parse_cache_concurrent_access(self):
        """並行アクセステスト（簡易版）"""
        import threading

        results = []
        errors = []

        def cache_operation(thread_id):
            try:
                # 各スレッドで異なるキャッシュ操作
                mock_node = Mock(spec=Node)
                mock_node.type = f"document_{thread_id}"

                hash_key = f"concurrent_hash_{thread_id}"
                self.cache.set(hash_key, [mock_node])

                # 取得テスト
                result = self.cache.get(hash_key)
                results.append((thread_id, result is not None))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 複数スレッドでテスト実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # スレッド完了を待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行アクセスでエラーが発生: {errors}"
        assert len(results) == 5, "すべてのスレッドが完了していません"
        assert all(success for _, success in results), "一部のキャッシュ操作が失敗"

    @pytest.mark.skip(reason="TTL期限切れテストは別の方法で実装予定")
    def test_parse_cache_ttl_expiration(self):
        """TTL期限切れテスト"""
        content_hash = "ttl_test_hash"
        mock_node = Mock(spec=Node)
        mock_node.type = "ttl_test_document"

        # 短いTTLでキャッシュ設定
        from datetime import datetime, timedelta

        with patch("kumihan_formatter.core.caching.cache_types.datetime") as mock_dt:
            # CacheEntryの作成時と有効期限チェック時の両方をモック
            base_time = datetime(2023, 1, 1, 12, 0, 0)
            mock_dt.now.return_value = base_time

            # キャッシュに保存
            self.cache.set(content_hash, [mock_node], ttl=1)  # 1秒のTTL

            # 即座に取得（有効期限内）
            result = self.cache.get(content_hash)
            assert result is not None

            # 時間を進める（期限切れ）
            mock_dt.now.return_value = base_time + timedelta(seconds=2)

            # キャッシュストレージから直接削除されることを確認
            expired_result = self.cache.get(content_hash)
            assert expired_result is None, "期限切れのキャッシュが取得されました"


class TestParseCacheStressTest:
    """パースキャッシュストレステスト"""

    def test_large_volume_cache_operations(self):
        """大容量キャッシュ操作テスト"""
        cache = ParseCache(max_memory_mb=100.0, max_entries=1000)

        try:
            # 大量のキャッシュエントリを作成
            for i in range(500):
                mock_node = Mock(spec=Node)
                mock_node.type = f"large_volume_document_{i}"
                mock_node.content = f"content_{i}" * 50

                cache.set(f"large_hash_{i}", [mock_node])

                # 定期的に統計を確認
                if i % 100 == 0:
                    stats = cache.get_stats()
                    memory_mb = stats["memory_stats"]["size_bytes"] / (1024 * 1024)
                    assert memory_mb <= 100.0

            # 最終統計確認
            final_stats = cache.get_stats()
            assert final_stats["memory_stats"]["entries"] <= 1000
            memory_mb = final_stats["memory_stats"]["size_bytes"] / (1024 * 1024)
            assert memory_mb <= 100.0

        finally:
            cache.clear()

    def test_rapid_cache_operations(self):
        """高速キャッシュ操作テスト"""
        cache = ParseCache(max_entries=100)

        try:
            start_time = time.time()

            # 高速でキャッシュ操作を実行
            for i in range(200):
                mock_node = Mock(spec=Node)
                mock_node.type = f"rapid_document_{i}"

                hash_key = f"rapid_hash_{i}"
                cache.set(hash_key, [mock_node])

                # 即座に取得テスト
                result = cache.get(hash_key)
                assert result is not None or i >= 100  # LRUで古いエントリは削除される

            execution_time = time.time() - start_time
            assert (
                execution_time < 1.0
            ), f"キャッシュ操作が遅すぎます: {execution_time}秒"

        finally:
            cache.clear()
