"""レンダーキャッシュ統合テスト - Issue #596 Week 23-24対応

HTML出力結果のキャッシングシステム統合テスト
レンダリングパフォーマンス最適化の効果測定
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.caching.render_cache import RenderCache


class TestRenderCacheIntegration:
    """レンダーキャッシュ統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = RenderCache(
            cache_dir=self.temp_dir,
            max_memory_mb=150.0,
            max_entries=500,
            default_ttl=1800,
        )

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, "cache"):
            self.cache.clear()
        # 一時ディレクトリの削除は安全のため省略

    def test_render_cache_basic_functionality(self):
        """基本的なレンダーキャッシュ機能テスト"""
        # テストデータ
        content_hash = "render_test_hash"
        template_name = "base.html.j2"
        render_options = {"include_toc": True, "theme": "default"}

        # HTML出力をシミュレート
        html_output = "<html><body><h1>Test Document</h1></body></html>"

        # キャッシュキー生成とデータ保存
        cache_key = self.cache.validators.generate_cache_key(
            content_hash, template_name, render_options, self.cache._config_hash
        )
        self.cache.set(cache_key, html_output)

        # キャッシュ取得テスト
        cached_result = self.cache.get(cache_key)
        assert cached_result == html_output

    def test_render_cache_template_optimization(self):
        """テンプレート最適化機能テスト"""
        # 複数のテンプレートでキャッシュデータを作成
        templates = ["base.html.j2", "docs.html.j2", "custom.html.j2"]

        for i, template in enumerate(templates):
            content_hash = f"template_test_hash_{i}"
            html_output = f"<html><body><h1>Template {template}</h1></body></html>"

            cache_key = self.cache.validators.generate_cache_key(
                content_hash, template, {}, self.cache._config_hash
            )
            self.cache.set(cache_key, html_output)

        # テンプレート最適化実行
        optimization_result = self.cache.optimize_for_templates()

        # 最適化結果確認
        assert "optimized_templates" in optimization_result
        assert "performance_improvement" in optimization_result
        assert len(optimization_result["optimized_templates"]) > 0

    def test_render_cache_performance_measurement(self):
        """レンダリングパフォーマンス測定テスト"""
        content_hash = "performance_hash"
        template_name = "base.html.j2"

        # 重いレンダリング処理をシミュレート
        def simulate_heavy_rendering():
            time.sleep(0.15)  # 150ms の処理時間をシミュレート
            return "<html><body><h1>Heavy Rendered Content</h1></body></html>"

        # 初回レンダリング（キャッシュなし）
        start_time = time.time()
        html_output = simulate_heavy_rendering()
        first_render_time = time.time() - start_time

        # キャッシュに保存
        cache_key = self.cache.validators.generate_cache_key(
            content_hash, template_name, {}, self.cache._config_hash
        )
        self.cache.set(cache_key, html_output)

        # 2回目レンダリング（キャッシュ使用）
        start_time = time.time()
        cached_output = self.cache.get(cache_key)
        second_render_time = time.time() - start_time

        # パフォーマンス改善確認
        assert cached_output == html_output
        improvement_ratio = first_render_time / second_render_time
        assert (
            improvement_ratio > 15
        ), f"レンダリング速度改善が不十分: {improvement_ratio}倍"

    def test_render_cache_memory_management(self):
        """レンダーキャッシュメモリ管理テスト"""
        # 大きなHTMLコンテンツでメモリ使用量をテスト
        large_html_template = "<html><body>" + "A" * 10000 + "</body></html>"

        # 複数の大きなキャッシュエントリを作成
        for i in range(100):
            content_hash = f"memory_test_hash_{i}"
            template_name = "large_template.html.j2"

            large_html = large_html_template.replace("A", f"Content_{i}")

            cache_key = self.cache.validators.generate_cache_key(
                content_hash, template_name, {}, self.cache._config_hash
            )
            self.cache.set(cache_key, large_html)

        # 統計情報取得とメモリ確認
        stats = self.cache.get_render_statistics()
        assert stats["memory_usage_mb"] <= 150.0, "メモリ制限を超過しています"
        assert stats["entry_count"] <= 500, "エントリ数制限を超過しています"

    def test_render_cache_template_invalidation(self):
        """テンプレート別キャッシュ無効化テスト"""
        # 複数のテンプレートでキャッシュを作成
        templates_data = [
            ("base.html.j2", "hash1", "<html><body>Base</body></html>"),
            ("docs.html.j2", "hash2", "<html><body>Docs</body></html>"),
            ("base.html.j2", "hash3", "<html><body>Base2</body></html>"),
        ]

        cache_keys = []
        for template, content_hash, html_output in templates_data:
            cache_key = self.cache.validators.generate_cache_key(
                content_hash, template, {}, self.cache._config_hash
            )
            cache_keys.append((cache_key, template))
            self.cache.set(cache_key, html_output)

        # base.html.j2テンプレートのキャッシュを無効化
        invalidated_count = self.cache.invalidate_by_template("base.html.j2")
        assert invalidated_count >= 2  # base.html.j2を使用する2つのエントリ

        # 無効化結果の確認
        for cache_key, template in cache_keys:
            result = self.cache.get(cache_key)
            if template == "base.html.j2":
                assert (
                    result is None
                ), f"base.html.j2のキャッシュが残っています: {cache_key}"
            else:
                assert (
                    result is not None
                ), f"他のテンプレートのキャッシュが削除されました: {cache_key}"

    def test_render_cache_analytics_reporting(self):
        """レンダーキャッシュ分析レポート生成テスト"""
        # 様々なパターンでキャッシュデータを作成
        test_patterns = [
            ("base.html.j2", {"theme": "light"}),
            ("base.html.j2", {"theme": "dark"}),
            ("docs.html.j2", {"include_toc": True}),
            ("docs.html.j2", {"include_toc": False}),
            ("custom.html.j2", {"layout": "grid"}),
        ]

        for i, (template, options) in enumerate(test_patterns):
            content_hash = f"analytics_hash_{i}"
            html_output = f"<html><body>Content {i}</body></html>"

            cache_key = self.cache.validators.generate_cache_key(
                content_hash, template, options, self.cache._config_hash
            )
            self.cache.set(cache_key, html_output)

        # 分析レポート生成
        report = self.cache.create_render_report()

        # レポート内容確認
        assert "cache_statistics" in report
        assert "template_usage" in report
        assert "performance_metrics" in report
        assert "optimization_suggestions" in report

        # 統計データの妥当性確認
        stats = report["cache_statistics"]
        assert stats["entry_count"] == len(test_patterns)
        assert stats["hit_rate"] >= 0.0

    def test_render_cache_ttl_management(self):
        """TTL管理テスト"""
        content_hash = "ttl_management_hash"
        template_name = "ttl_test.html.j2"
        html_output = "<html><body>TTL Test</body></html>"

        # 動的TTL計算テスト
        output_size = len(html_output.encode("utf-8"))
        render_time = 0.1
        node_count = 5

        calculated_ttl = self.cache.validators.calculate_ttl(
            output_size, render_time, node_count
        )
        assert isinstance(calculated_ttl, int)
        assert calculated_ttl > 0

        # TTL付きキャッシュ保存
        cache_key = self.cache.validators.generate_cache_key(
            content_hash, template_name, {}, self.cache._config_hash
        )

        with patch("time.time") as mock_time:
            # 現在時刻設定
            mock_time.return_value = 2000.0
            self.cache.set(cache_key, html_output, ttl=calculated_ttl)

            # 有効期限内での取得
            result = self.cache.get(cache_key)
            assert result == html_output

            # 期限切れ後の取得
            mock_time.return_value = 2000.0 + calculated_ttl + 1
            expired_result = self.cache.get(cache_key)
            assert expired_result is None

    def test_render_cache_concurrent_rendering(self):
        """並行レンダリングキャッシュテスト"""
        import threading

        results = []
        errors = []

        def concurrent_render_operation(thread_id):
            try:
                content_hash = f"concurrent_hash_{thread_id}"
                template_name = f"template_{thread_id % 3}.html.j2"
                html_output = f"<html><body>Thread {thread_id}</body></html>"

                cache_key = self.cache.validators.generate_cache_key(
                    content_hash, template_name, {}, self.cache._config_hash
                )

                # キャッシュ保存
                self.cache.set(cache_key, html_output)

                # 即座に取得
                result = self.cache.get(cache_key)
                results.append((thread_id, result == html_output))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(8):
            thread = threading.Thread(target=concurrent_render_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行処理でエラーが発生: {errors}"
        assert len(results) == 8
        assert all(success for _, success in results), "一部の並行処理が失敗"

    def test_render_cache_optimization_suggestions(self):
        """最適化提案生成テスト"""
        # 非効率なキャッシュパターンを作成
        inefficient_patterns = [
            # 同じコンテンツを異なるオプションでキャッシュ
            ("same_content_hash", "base.html.j2", {"theme": "light"}),
            ("same_content_hash", "base.html.j2", {"theme": "dark"}),
            ("same_content_hash", "base.html.j2", {"theme": "auto"}),
        ]

        for content_hash, template, options in inefficient_patterns:
            html_output = f"<html><body>Content with {options}</body></html>"
            cache_key = self.cache.validators.generate_cache_key(
                content_hash, template, options, self.cache._config_hash
            )
            self.cache.set(cache_key, html_output)

        # 最適化提案を取得
        suggestions = self.cache.analytics.generate_optimization_suggestions(
            self.cache.get_render_statistics()
        )

        # 提案内容確認
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # 具体的な提案があることを確認
        suggestion_text = " ".join(suggestions)
        assert any(
            keyword in suggestion_text.lower()
            for keyword in ["template", "cache", "memory", "performance"]
        )


class TestRenderCacheStressTest:
    """レンダーキャッシュストレステスト"""

    def test_high_volume_render_cache(self):
        """大容量レンダーキャッシュテスト"""
        cache = RenderCache(max_memory_mb=200.0, max_entries=1000)

        try:
            # 大量のレンダリング結果をキャッシュ
            for i in range(800):
                content_hash = f"volume_hash_{i}"
                template_name = f"template_{i % 5}.html.j2"

                # 大きなHTMLコンテンツ
                html_output = f"<html><body>{'Content ' * 100} {i}</body></html>"

                cache_key = cache.validators.generate_cache_key(
                    content_hash, template_name, {}, cache._config_hash
                )
                cache.set(cache_key, html_output)

                # 定期的に統計確認
                if i % 200 == 0:
                    stats = cache.get_render_statistics()
                    assert stats["memory_usage_mb"] <= 200.0

            # 最終確認
            final_stats = cache.get_render_statistics()
            assert final_stats["entry_count"] <= 1000
            assert final_stats["memory_usage_mb"] <= 200.0

        finally:
            cache.clear()

    def test_rapid_render_cache_operations(self):
        """高速レンダーキャッシュ操作テスト"""
        cache = RenderCache(max_entries=200)

        try:
            start_time = time.time()

            # 高速でレンダーキャッシュ操作
            for i in range(300):
                content_hash = f"rapid_render_hash_{i}"
                template_name = "rapid_template.html.j2"
                html_output = f"<html><body>Rapid {i}</body></html>"

                cache_key = cache.validators.generate_cache_key(
                    content_hash, template_name, {}, cache._config_hash
                )

                cache.set(cache_key, html_output)
                result = cache.get(cache_key)

                # LRUで古いエントリは削除される可能性がある
                assert result is not None or i >= 200

            execution_time = time.time() - start_time
            assert (
                execution_time < 2.0
            ), f"レンダーキャッシュ操作が遅すぎます: {execution_time}秒"

        finally:
            cache.clear()
