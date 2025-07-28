"""レンダーキャッシュメタデータテスト - Issue #596 Week 25-26対応

レンダリングキャッシュのメタデータ管理機能の詳細テスト
メタデータ追跡、統計収集、分析機能の確認
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.caching.cache_types import CacheEntry
from kumihan_formatter.core.caching.render_cache_metadata import RenderCacheMetadata


class TestRenderCacheMetadata:
    """レンダーキャッシュメタデータテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.metadata_manager = RenderCacheMetadata()

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "metadata_manager"):
            self.metadata_manager.clear()

    def test_metadata_manager_initialization(self):
        """メタデータマネージャー初期化テスト"""
        manager = RenderCacheMetadata()
        assert manager is not None
        assert hasattr(manager, "add_metadata")
        assert hasattr(manager, "get_metadata")
        assert hasattr(manager, "update_last_accessed")
        assert hasattr(manager, "get_template_stats")

    def test_add_metadata_basic(self):
        """基本的なレンダリングメタデータ追加テスト"""
        # add_metadata メソッドに必要なパラメータ
        cache_key = "test_key"
        content_hash = "abc123def456"
        template_name = "base.html.j2"
        render_time = 0.15
        node_count = 10
        output_size = 2048

        self.metadata_manager.add_metadata(
            cache_key, content_hash, template_name, render_time, node_count, output_size
        )

        # 追加されたメタデータを取得
        retrieved_metadata = self.metadata_manager.get_metadata(cache_key)
        assert retrieved_metadata is not None
        assert retrieved_metadata["template_name"] == template_name
        assert retrieved_metadata["render_time"] == render_time
        assert retrieved_metadata["content_hash"] == content_hash
        assert retrieved_metadata["node_count"] == node_count
        assert retrieved_metadata["output_size"] == output_size
        assert "cached_at" in retrieved_metadata
        assert "last_accessed" in retrieved_metadata

    def test_update_last_accessed(self):
        """最終アクセス時刻更新テスト"""
        cache_key = "access_test"
        self.metadata_manager.add_metadata(
            cache_key, "hash", "template.html", 0.1, 5, 1024
        )

        # 初期の最終アクセス時刻を取得
        initial_metadata = self.metadata_manager.get_metadata(cache_key)
        initial_accessed = initial_metadata["last_accessed"]

        # 少し待つ
        time.sleep(0.01)

        # 最終アクセス時刻を更新
        self.metadata_manager.update_last_accessed(cache_key)

        # 更新後の時刻が異なることを確認
        updated_metadata = self.metadata_manager.get_metadata(cache_key)
        assert updated_metadata["last_accessed"] != initial_accessed

    def test_get_keys_by_template(self):
        """テンプレート名による検索テスト"""
        # 複数のエントリを追加
        self.metadata_manager.add_metadata(
            "key1", "hash1", "template_a.html", 0.1, 5, 1024
        )
        self.metadata_manager.add_metadata(
            "key2", "hash2", "template_b.html", 0.2, 10, 2048
        )
        self.metadata_manager.add_metadata(
            "key3", "hash3", "template_a.html", 0.15, 7, 1536
        )

        # template_a.htmlのキーを検索
        keys = self.metadata_manager.get_keys_by_template("template_a.html")
        assert len(keys) == 2
        assert "key1" in keys
        assert "key3" in keys

    def test_get_keys_by_content_hash(self):
        """コンテンツハッシュによる検索テスト"""
        # 同じコンテンツハッシュを持つエントリを追加
        self.metadata_manager.add_metadata(
            "key1", "same_hash", "template_a.html", 0.1, 5, 1024
        )
        self.metadata_manager.add_metadata(
            "key2", "different_hash", "template_b.html", 0.2, 10, 2048
        )
        self.metadata_manager.add_metadata(
            "key3", "same_hash", "template_c.html", 0.15, 7, 1536
        )

        # same_hashのキーを検索
        keys = self.metadata_manager.get_keys_by_content_hash("same_hash")
        assert len(keys) == 2
        assert "key1" in keys
        assert "key3" in keys

    def test_get_template_stats(self):
        """テンプレート統計情報テスト"""
        # 複数のエントリを追加
        self.metadata_manager.add_metadata(
            "key1", "hash1", "template_a.html", 0.1, 5, 1024
        )
        self.metadata_manager.add_metadata(
            "key2", "hash2", "template_a.html", 0.2, 10, 2048
        )
        self.metadata_manager.add_metadata(
            "key3", "hash3", "template_b.html", 0.15, 7, 1536
        )

        # 統計情報を取得
        stats = self.metadata_manager.get_template_stats()
        assert stats["template_a.html"] == 2
        assert stats["template_b.html"] == 1

    def test_get_template_usage_stats(self):
        """テンプレート使用パターン詳細統計テスト"""
        # 複数のエントリを追加
        self.metadata_manager.add_metadata(
            "key1", "hash1", "template_a.html", 0.1, 5, 1024
        )
        self.metadata_manager.add_metadata(
            "key2", "hash2", "template_a.html", 0.2, 10, 2048
        )
        self.metadata_manager.add_metadata(
            "key3", "hash3", "template_b.html", 0.15, 7, 1536
        )

        # 詳細統計を取得
        usage_stats = self.metadata_manager.get_template_usage_stats()

        # template_a.htmlの統計
        assert usage_stats["template_a.html"]["count"] == 2
        assert abs(usage_stats["template_a.html"]["avg_render_time"] - 0.15) < 0.001
        assert usage_stats["template_a.html"]["avg_output_size"] == 1536

    def test_remove_metadata(self):
        """メタデータ削除テスト"""
        cache_key = "remove_test"
        self.metadata_manager.add_metadata(
            cache_key, "hash", "template.html", 0.1, 5, 1024
        )

        # 削除前に存在確認
        assert self.metadata_manager.get_metadata(cache_key) is not None

        # 削除
        result = self.metadata_manager.remove_metadata(cache_key)
        assert result is True

        # 削除後に存在しないことを確認
        assert self.metadata_manager.get_metadata(cache_key) is None

        # 存在しないキーの削除
        result = self.metadata_manager.remove_metadata("non_existent")
        assert result is False

    def test_clear(self):
        """全メタデータクリアテスト"""
        # 複数のエントリを追加
        self.metadata_manager.add_metadata(
            "key1", "hash1", "template_a.html", 0.1, 5, 1024
        )
        self.metadata_manager.add_metadata(
            "key2", "hash2", "template_b.html", 0.2, 10, 2048
        )

        # クリア前の確認
        assert len(self.metadata_manager.get_all_metadata()) == 2

        # クリア
        self.metadata_manager.clear()

        # クリア後の確認
        assert len(self.metadata_manager.get_all_metadata()) == 0

    def test_get_render_times(self):
        """レンダリング時間リスト取得テスト"""
        # 複数のエントリを追加
        self.metadata_manager.add_metadata(
            "key1", "hash1", "template.html", 0.1, 5, 1024
        )
        self.metadata_manager.add_metadata(
            "key2", "hash2", "template.html", 0.2, 10, 2048
        )
        self.metadata_manager.add_metadata(
            "key3", "hash3", "template.html", 0.15, 7, 1536
        )

        # レンダリング時間を取得
        render_times = self.metadata_manager.get_render_times()
        assert len(render_times) == 3
        assert 0.1 in render_times
        assert 0.2 in render_times
        assert 0.15 in render_times

    def test_get_output_sizes(self):
        """出力サイズリスト取得テスト"""
        # 複数のエントリを追加
        self.metadata_manager.add_metadata(
            "key1", "hash1", "template.html", 0.1, 5, 1024
        )
        self.metadata_manager.add_metadata(
            "key2", "hash2", "template.html", 0.2, 10, 2048
        )
        self.metadata_manager.add_metadata(
            "key3", "hash3", "template.html", 0.15, 7, 1536
        )

        # 出力サイズを取得
        output_sizes = self.metadata_manager.get_output_sizes()
        assert len(output_sizes) == 3
        assert 1024 in output_sizes
        assert 2048 in output_sizes
        assert 1536 in output_sizes
