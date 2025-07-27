"""レンダーキャッシュバリデーターテスト - Issue #596 Week 25-26対応

レンダリングキャッシュの検証機能の詳細テスト
データ整合性、TTL検証、メタデータ検証の確認
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.caching.cache_types import CacheEntry
from kumihan_formatter.core.caching.render_cache_validators import RenderCacheValidators


class TestRenderCacheValidators:
    """レンダーキャッシュバリデーターテスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.validators = RenderCacheValidators()

    def test_validators_initialization(self):
        """バリデーター初期化テスト"""
        validators = RenderCacheValidators()
        assert validators is not None
        assert hasattr(validators, "validate_cache_entry")
        assert hasattr(validators, "validate_render_metadata")
        assert hasattr(validators, "validate_template_integrity")
        assert hasattr(validators, "validate_cache_consistency")

    def test_validate_cache_entry_valid(self):
        """有効なキャッシュエントリの検証テスト"""
        # 有効なエントリ
        valid_entry = CacheEntry(
            key="valid_key",
            value="valid_html_content",
            created_at=time.time(),
            ttl=3600,
            size_bytes=len("valid_html_content"),
        )

        result = self.validators.validate_cache_entry(valid_entry)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert "validation_details" in result

    def test_validate_cache_entry_invalid_key(self):
        """無効なキーのキャッシュエントリ検証テスト"""
        # 空のキー
        invalid_entry = CacheEntry(
            key="",
            value="content",
            created_at=time.time(),
            ttl=3600,
            size_bytes=7,
        )

        result = self.validators.validate_cache_entry(invalid_entry)

        assert result["is_valid"] is False
        assert "キーが空です" in " ".join(result["errors"])

        # None キー
        invalid_entry.key = None
        result = self.validators.validate_cache_entry(invalid_entry)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_cache_entry_expired(self):
        """期限切れキャッシュエントリの検証テスト"""
        with patch("time.time") as mock_time:
            # 現在時刻を設定
            mock_time.return_value = 1000.0

            # 期限切れエントリ（1時間前に作成、30分のTTL）
            expired_entry = CacheEntry(
                key="expired_key",
                value="expired_content",
                created_at=500.0,  # 500秒前に作成
                ttl=1800,  # 30分のTTL
                size_bytes=15,
            )

            result = self.validators.validate_cache_entry(expired_entry)

            assert result["is_valid"] is False
            assert "TTLが期限切れです" in " ".join(result["errors"])

    def test_validate_cache_entry_size_mismatch(self):
        """サイズ不一致のキャッシュエントリ検証テスト"""
        # 実際のサイズと記録されたサイズが異なる
        size_mismatch_entry = CacheEntry(
            key="size_test",
            value="actual_content",  # 14文字
            created_at=time.time(),
            ttl=3600,
            size_bytes=100,  # 間違ったサイズ
        )

        result = self.validators.validate_cache_entry(size_mismatch_entry)

        assert result["is_valid"] is False
        assert "サイズが一致しません" in " ".join(result["errors"])

    def test_validate_render_metadata_valid(self):
        """有効なレンダリングメタデータの検証テスト"""
        valid_metadata = {
            "template_name": "base.html.j2",
            "render_time": 0.15,
            "output_size": 2048,
            "template_hash": "abc123def456",
            "variables_hash": "var789hash",
            "timestamp": datetime.now().isoformat(),
        }

        result = self.validators.validate_render_metadata(valid_metadata)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["metadata_quality"] > 0.8  # 高品質なメタデータ

    def test_validate_render_metadata_missing_required_fields(self):
        """必須フィールド欠損のメタデータ検証テスト"""
        incomplete_metadata = {
            "template_name": "test.html.j2",
            # render_time欠損
            "output_size": 1024,
            # template_hash欠損
        }

        result = self.validators.validate_render_metadata(incomplete_metadata)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

        # 具体的なエラーメッセージの確認
        error_text = " ".join(result["errors"])
        assert "render_time" in error_text or "必須フィールド" in error_text

    def test_validate_render_metadata_invalid_values(self):
        """無効な値のメタデータ検証テスト"""
        invalid_metadata = {
            "template_name": "",  # 空のテンプレート名
            "render_time": -0.5,  # 負のレンダリング時間
            "output_size": -1,  # 負の出力サイズ
            "template_hash": "invalid",  # 短すぎるハッシュ
            "variables_hash": None,  # Noneのハッシュ
        }

        result = self.validators.validate_render_metadata(invalid_metadata)

        assert result["is_valid"] is False
        assert len(result["errors"]) >= 3  # 複数のエラー

        # 各種エラーが検出されることを確認
        error_text = " ".join(result["errors"])
        assert "テンプレート名" in error_text or "render_time" in error_text

    def test_validate_template_integrity(self):
        """テンプレート整合性検証テスト"""
        # テンプレートファイルのモック
        template_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>{{ title }}</h1>
            <p>{{ content }}</p>
        </body>
        </html>
        """

        template_file_mock = Mock()
        template_file_mock.read_text.return_value = template_content

        with patch("pathlib.Path") as mock_path:
            mock_path.return_value = template_file_mock

            result = self.validators.validate_template_integrity(
                template_path="templates/test.html.j2",
                expected_hash="calculated_hash_value",
            )

        # 整合性チェック結果の確認
        assert "integrity_check" in result
        assert "template_exists" in result
        assert "hash_match" in result
        assert result["template_exists"] is True

    def test_validate_template_integrity_missing_file(self):
        """存在しないテンプレートファイルの整合性検証テスト"""
        with patch("pathlib.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            result = self.validators.validate_template_integrity(
                template_path="nonexistent/template.html.j2", expected_hash="some_hash"
            )

        assert result["template_exists"] is False
        assert result["integrity_check"] is False

    def test_validate_cache_consistency_basic(self):
        """基本的なキャッシュ一貫性検証テスト"""
        # 一貫性のあるキャッシュエントリ群
        consistent_cache = {
            "entry1": CacheEntry(
                key="entry1",
                value="content1",
                created_at=time.time(),
                ttl=3600,
                size_bytes=8,
            ),
            "entry2": CacheEntry(
                key="entry2",
                value="content2",
                created_at=time.time(),
                ttl=3600,
                size_bytes=8,
            ),
        }

        metadata = {
            "entry1": {
                "template_name": "template1.html.j2",
                "render_time": 0.1,
                "output_size": 8,
            },
            "entry2": {
                "template_name": "template2.html.j2",
                "render_time": 0.2,
                "output_size": 8,
            },
        }

        result = self.validators.validate_cache_consistency(consistent_cache, metadata)

        assert result["is_consistent"] is True
        assert result["total_entries"] == 2
        assert result["valid_entries"] == 2
        assert len(result["inconsistencies"]) == 0

    def test_validate_cache_consistency_with_inconsistencies(self):
        """不整合のあるキャッシュ一貫性検証テスト"""
        # 不整合のあるキャッシュ
        inconsistent_cache = {
            "entry1": CacheEntry(
                key="entry1",
                value="content1",
                created_at=time.time(),
                ttl=3600,
                size_bytes=8,
            ),
            "entry2": CacheEntry(
                key="entry2",
                value="content2",
                created_at=time.time() - 7200,  # 2時間前
                ttl=3600,  # 1時間のTTL（期限切れ）
                size_bytes=8,
            ),
        }

        metadata = {
            "entry1": {
                "template_name": "template1.html.j2",
                "render_time": 0.1,
                "output_size": 8,
            },
            "entry2": {
                "template_name": "template2.html.j2",
                "render_time": 0.2,
                "output_size": 16,  # サイズ不一致
            },
            # entry3のメタデータはあるがキャッシュエントリがない
            "entry3": {
                "template_name": "template3.html.j2",
                "render_time": 0.3,
                "output_size": 10,
            },
        }

        result = self.validators.validate_cache_consistency(
            inconsistent_cache, metadata
        )

        assert result["is_consistent"] is False
        assert result["total_entries"] == 2
        assert result["valid_entries"] < result["total_entries"]
        assert len(result["inconsistencies"]) > 0

        # 具体的な不整合の確認
        inconsistencies = result["inconsistencies"]
        inconsistency_text = " ".join(inconsistencies)
        assert "期限切れ" in inconsistency_text or "サイズ不一致" in inconsistency_text

    def test_validate_cache_memory_usage(self):
        """キャッシュメモリ使用量検証テスト"""
        # メモリ使用量データ
        memory_stats = {
            "current_usage_bytes": 5 * 1024 * 1024,  # 5MB
            "max_limit_bytes": 10 * 1024 * 1024,  # 10MB
            "entry_count": 100,
            "average_entry_size": 51200,  # 50KB
        }

        result = self.validators.validate_cache_memory_usage(memory_stats)

        assert "memory_efficiency" in result
        assert "usage_ratio" in result
        assert "recommendations" in result

        # 使用率の計算が正しい
        assert result["usage_ratio"] == 0.5  # 50%

        # 効率性が評価される
        assert 0.0 <= result["memory_efficiency"] <= 1.0

    def test_validate_cache_memory_usage_over_limit(self):
        """メモリ制限超過時の検証テスト"""
        # メモリ制限を超過したケース
        over_limit_stats = {
            "current_usage_bytes": 12 * 1024 * 1024,  # 12MB
            "max_limit_bytes": 10 * 1024 * 1024,  # 10MB制限
            "entry_count": 200,
            "average_entry_size": 61440,  # 60KB
        }

        result = self.validators.validate_cache_memory_usage(over_limit_stats)

        assert result["usage_ratio"] > 1.0  # 制限超過
        assert "memory_efficiency" in result

        # 推奨事項が生成される
        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        rec_text = " ".join(recommendations)
        assert "制限超過" in rec_text or "削減" in rec_text

    def test_validate_render_output_integrity(self):
        """レンダリング出力整合性検証テスト"""
        # 有効なHTMLコンテンツ
        valid_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body><h1>Test Content</h1></body>
        </html>
        """

        result = self.validators.validate_render_output_integrity(valid_html)

        assert result["is_valid_html"] is True
        assert result["has_doctype"] is True
        assert result["has_closing_tags"] is True
        assert "validation_score" in result
        assert result["validation_score"] > 0.7

    def test_validate_render_output_integrity_malformed(self):
        """不正なレンダリング出力の検証テスト"""
        # 不正なHTMLコンテンツ
        malformed_html = """
        <html>
        <head><title>Broken HTML
        <body>
        <h1>Unclosed header
        <p>Paragraph without closing tag
        """

        result = self.validators.validate_render_output_integrity(malformed_html)

        assert result["is_valid_html"] is False
        assert result["has_doctype"] is False
        assert result["has_closing_tags"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_validate_cache_key_patterns(self):
        """キャッシュキーパターン検証テスト"""
        # 様々なキーパターン
        cache_keys = [
            "render:template:base.html.j2:hash123",
            "render:template:docs.html.j2:hash456",
            "render:component:header:hash789",
            "invalid_key_format",
            "render:template:",  # 不完全なキー
            "",  # 空のキー
        ]

        result = self.validators.validate_cache_key_patterns(cache_keys)

        assert "total_keys" in result
        assert "valid_patterns" in result
        assert "invalid_patterns" in result
        assert "pattern_distribution" in result

        assert result["total_keys"] == len(cache_keys)
        assert result["valid_patterns"] > 0
        assert result["invalid_patterns"] > 0

        # パターン分布の確認
        pattern_dist = result["pattern_distribution"]
        assert "render:template" in pattern_dist
        assert "render:component" in pattern_dist

    def test_validate_ttl_distribution(self):
        """TTL分布検証テスト"""
        # 様々なTTL値のエントリ
        ttl_data = [
            {"key": "short_ttl", "ttl": 300, "created_at": time.time()},  # 5分
            {"key": "medium_ttl", "ttl": 3600, "created_at": time.time()},  # 1時間
            {"key": "long_ttl", "ttl": 86400, "created_at": time.time()},  # 1日
            {"key": "very_long_ttl", "ttl": 604800, "created_at": time.time()},  # 1週間
        ]

        result = self.validators.validate_ttl_distribution(ttl_data)

        assert "distribution_analysis" in result
        assert "recommendations" in result
        assert "outliers" in result

        # TTL分布の分析
        dist_analysis = result["distribution_analysis"]
        assert "avg_ttl" in dist_analysis
        assert "min_ttl" in dist_analysis
        assert "max_ttl" in dist_analysis
        assert "std_deviation" in dist_analysis

    def test_cross_validation_consistency_check(self):
        """横断的整合性チェックテスト"""
        # 複数のデータ源
        cache_entries = {
            "key1": CacheEntry(
                key="key1",
                value="content1",
                created_at=time.time(),
                ttl=3600,
                size_bytes=8,
            )
        }

        metadata = {
            "key1": {
                "template_name": "test.html.j2",
                "render_time": 0.1,
                "output_size": 8,
            }
        }

        statistics = {
            "total_entries": 1,
            "total_size_bytes": 8,
            "avg_render_time": 0.1,
        }

        result = self.validators.cross_validate_consistency(
            cache_entries, metadata, statistics
        )

        assert "overall_consistency" in result
        assert "data_source_alignment" in result
        assert "discrepancies" in result

        # 一貫性スコア
        assert 0.0 <= result["overall_consistency"] <= 1.0


class TestRenderCacheValidatorsEdgeCases:
    """レンダーキャッシュバリデーターエッジケーステスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.validators = RenderCacheValidators()

    def test_validation_with_empty_inputs(self):
        """空の入力での検証テスト"""
        # 空のキャッシュエントリ
        result = self.validators.validate_cache_consistency({}, {})
        assert result["is_consistent"] is True  # 空は一貫している
        assert result["total_entries"] == 0

        # 空のメタデータ
        result = self.validators.validate_render_metadata({})
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_validation_with_none_inputs(self):
        """None入力での検証テスト"""
        # Noneエントリ
        result = self.validators.validate_cache_entry(None)
        assert result["is_valid"] is False
        assert "エントリがNullです" in " ".join(result["errors"])

        # Noneメタデータ
        result = self.validators.validate_render_metadata(None)
        assert result["is_valid"] is False

    def test_validation_with_corrupted_data(self):
        """破損データでの検証テスト"""
        # 破損したキャッシュエントリ（部分的に無効な属性）
        corrupted_entry = Mock()
        corrupted_entry.key = "valid_key"
        corrupted_entry.value = "valid_value"
        corrupted_entry.created_at = "invalid_timestamp"  # 文字列（数値でない）
        corrupted_entry.ttl = None
        corrupted_entry.size_bytes = -100

        result = self.validators.validate_cache_entry(corrupted_entry)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_validation_performance_with_large_dataset(self):
        """大規模データセットでの検証性能テスト"""
        import time as time_module

        # 大量のキャッシュエントリを生成
        large_cache = {}
        large_metadata = {}

        for i in range(1000):
            key = f"large_key_{i}"
            entry = CacheEntry(
                key=key,
                value=f"content_{i}" * 10,
                created_at=time.time(),
                ttl=3600,
                size_bytes=len(f"content_{i}" * 10),
            )
            large_cache[key] = entry

            large_metadata[key] = {
                "template_name": f"template_{i % 10}.html.j2",
                "render_time": 0.1 + (i % 10) * 0.01,
                "output_size": len(f"content_{i}" * 10),
            }

        # 検証時間を測定
        start_time = time_module.time()
        result = self.validators.validate_cache_consistency(large_cache, large_metadata)
        execution_time = time_module.time() - start_time

        # 合理的な時間で完了することを確認
        assert execution_time < 5.0, f"大規模検証が遅すぎます: {execution_time}秒"

        # 検証結果が正しいことを確認
        assert result["total_entries"] == 1000
        assert result["valid_entries"] > 0

    def test_validation_with_unicode_content(self):
        """Unicode文字を含むコンテンツの検証テスト"""
        # 日本語を含むコンテンツ
        japanese_content = """
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>日本語テスト</title>
        </head>
        <body>
            <h1>こんにちは、世界！</h1>
            <p>これは日本語のテストです。絵文字も含みます: 🎌🗾</p>
        </body>
        </html>
        """

        unicode_entry = CacheEntry(
            key="unicode_test",
            value=japanese_content,
            created_at=time.time(),
            ttl=3600,
            size_bytes=len(japanese_content.encode("utf-8")),
        )

        result = self.validators.validate_cache_entry(unicode_entry)
        assert result["is_valid"] is True

        # HTML整合性も確認
        html_result = self.validators.validate_render_output_integrity(japanese_content)
        assert html_result["is_valid_html"] is True

    def test_concurrent_validation(self):
        """並行検証テスト"""
        import threading

        results = []
        errors = []

        def concurrent_validation(thread_id):
            try:
                # 各スレッドで異なるエントリを検証
                entry = CacheEntry(
                    key=f"thread_{thread_id}_key",
                    value=f"content_for_thread_{thread_id}",
                    created_at=time.time(),
                    ttl=3600,
                    size_bytes=len(f"content_for_thread_{thread_id}"),
                )

                result = self.validators.validate_cache_entry(entry)
                results.append((thread_id, result["is_valid"]))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # 並行実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_validation, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行検証でエラーが発生: {errors}"
        assert len(results) == 5
        assert all(is_valid for _, is_valid in results)
