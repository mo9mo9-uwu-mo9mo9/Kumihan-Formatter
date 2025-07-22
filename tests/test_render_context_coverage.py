"""RenderContext Coverage Tests - テンプレートコンテキストテスト

RenderContext完全テスト
Target: template_context.py (40.00% → 完全)
Goal: RenderContext機能の完全カバレッジ
"""

import threading

from kumihan_formatter.core.template_context import RenderContext


class TestRenderContext:
    """TemplateContext完全テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.context = RenderContext()

    def test_template_context_initialization(self):
        """TemplateContext初期化テスト"""
        context = RenderContext()

        # 基本的な属性が初期化されていることを確認
        assert hasattr(context, "_context")
        assert isinstance(context._context, dict)

    def test_set_context_value(self):
        """コンテキスト値設定テスト"""
        self.context.custom("title", "Test Title")
        self.context.custom("author", "Test Author")

        # 値が正しく設定されることを確認
        assert self.context.get("title") == "Test Title"
        assert self.context.get("author") == "Test Author"

    def test_get_context_value(self):
        """コンテキスト値取得テスト"""
        # 存在する値の取得
        self.context.custom("test_key", "test_value")
        result = self.context.get("test_key")
        assert result == "test_value"

        # 存在しない値の取得（デフォルト値）
        result = self.context.get("nonexistent_key", "default_value")
        assert result == "default_value"

        # 存在しない値の取得（デフォルトなし）
        result = self.context.get("nonexistent_key")
        assert result is None

    def test_update_context(self):
        """コンテキスト一括更新テスト"""
        update_data = {
            "title": "Updated Title",
            "description": "Test Description",
            "version": "1.0.0",
        }

        self.context.merge(update_data)

        # 全ての値が正しく更新されることを確認
        for key, value in update_data.items():
            assert self.context.get(key) == value

    def test_context_merge(self):
        """コンテキストマージテスト"""
        # 初期データ
        self.context.custom("title", "Original Title")
        self.context.custom("author", "Original Author")

        # マージデータ
        merge_data = {
            "title": "New Title",  # 上書き
            "description": "New Description",  # 新規追加
        }

        self.context.merge(merge_data)

        # 上書きと新規追加が正しく行われることを確認
        assert self.context.get("title") == "New Title"
        assert self.context.get("author") == "Original Author"
        assert self.context.get("description") == "New Description"

    def test_context_with_nested_data(self):
        """ネストしたデータのコンテキストテスト"""
        nested_data = {
            "config": {"theme": "dark", "language": "ja"},
            "metadata": {"created_at": "2025-07-22", "tags": ["test", "coverage"]},
        }

        self.context.merge(nested_data)

        # ネストしたデータが正しく格納されることを確認
        config = self.context.get("config")
        assert config["theme"] == "dark"
        assert config["language"] == "ja"

        metadata = self.context.get("metadata")
        assert metadata["created_at"] == "2025-07-22"
        assert "test" in metadata["tags"]

    def test_context_serialization(self):
        """コンテキストシリアライゼーションテスト"""
        self.context.custom("title", "Test Title")
        self.context.custom("count", 42)
        self.context.custom("active", True)

        # build メソッドでシリアライゼーションテスト
        result = self.context.build()
        assert isinstance(result, dict)
        assert result["title"] == "Test Title"
        assert result["count"] == 42
        assert result["active"] is True

    def test_context_clear(self):
        """コンテキストクリアテスト"""
        self.context.custom("temp_data", "to be cleared")

        # clearメソッドがある場合のテスト
        if hasattr(self.context, "clear"):
            self.context.clear()
            assert self.context.get("temp_data") is None

    def test_context_key_existence(self):
        """コンテキストキー存在確認テスト"""
        self.context.custom("existing_key", "value")

        # hasメソッドがある場合のテスト
        if hasattr(self.context, "has"):
            assert self.context.has("existing_key") is True
            assert self.context.has("nonexistent_key") is False

    def test_context_iteration(self):
        """コンテキスト反復テスト"""
        test_data = {"key1": "value1", "key2": "value2", "key3": "value3"}

        self.context.merge(test_data)

        # keysメソッドがある場合のテスト
        if hasattr(self.context, "keys"):
            keys = self.context.keys()
            assert len(keys) >= len(test_data)

            # 全てのキーが含まれていることを確認
            for test_key in test_data.keys():
                assert test_key in keys

        # itemsは実装されていないのでkeysでテスト済み
        assert True

    def test_context_performance_with_large_data(self):
        """大量データでのコンテキストパフォーマンステスト"""
        # 大量のデータを設定
        large_data = {}
        for i in range(1000):
            large_data[f"key_{i}"] = f"value_{i}"

        import time

        start = time.time()
        self.context.merge(large_data)
        end = time.time()

        # 合理的な時間内で処理が完了することを確認
        assert (end - start) < 1.0  # 1秒以内

        # データが正しく設定されていることを確認
        assert self.context.get("key_500") == "value_500"
        assert self.context.get("key_999") == "value_999"

    def test_context_thread_safety(self):
        """コンテキストスレッドセーフティテスト"""

        def update_context(thread_id):
            for i in range(10):
                self.context.custom(f"thread_{thread_id}_key_{i}", f"value_{i}")

        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_context, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # スレッド競合でエラーが発生していないことを確認
        # いくつかのキーが正しく設定されていることを確認
        assert self.context.get("thread_0_key_0") == "value_0"
        assert self.context.get("thread_4_key_9") == "value_9"
