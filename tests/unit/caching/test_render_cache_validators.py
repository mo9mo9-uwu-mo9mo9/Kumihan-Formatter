"""レンダーキャッシュバリデーターテスト - Issue #596対応

レンダリングキャッシュのバリデーター・ユーティリティ機能のテスト
実装に合わせたメソッド名で修正
"""

import hashlib
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

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
        assert hasattr(validators, "generate_cache_key")
        assert hasattr(validators, "calculate_ttl")
        assert hasattr(validators, "validate_cache_key")
        assert hasattr(validators, "validate_render_options")
        assert hasattr(validators, "estimate_cache_efficiency")

    def test_generate_cache_key_basic(self):
        """基本的なキャッシュキー生成テスト"""
        content_hash = "abc123def456"
        template_name = "base.html.j2"
        render_options = {"theme": "dark", "lang": "ja"}

        cache_key = self.validators.generate_cache_key(
            content_hash, template_name, render_options
        )

        assert cache_key is not None
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    def test_generate_cache_key_different_inputs(self):
        """異なる入力での異なるキー生成テスト"""
        key1 = self.validators.generate_cache_key("hash1", "template1.html")
        key2 = self.validators.generate_cache_key("hash2", "template1.html")
        key3 = self.validators.generate_cache_key("hash1", "template2.html")

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_generate_cache_key_with_config_hash(self):
        """設定ハッシュ付きキー生成テスト"""
        cache_key = self.validators.generate_cache_key(
            "content_hash", "template.html", None, "config_hash"
        )

        assert cache_key is not None
        assert isinstance(cache_key, str)

    def test_calculate_ttl_default(self):
        """デフォルトTTL計算テスト"""
        ttl = self.validators.calculate_ttl(1024, 0.1, 10)
        assert ttl > 0
        assert isinstance(ttl, int)

    def test_calculate_ttl_size_based(self):
        """サイズベースTTL計算テスト"""
        small_ttl = self.validators.calculate_ttl(100, 0.1, 5)
        large_ttl = self.validators.calculate_ttl(100000, 0.1, 5)

        # 大きいファイルの方がTTLが長い（キャッシュ効果が高い）
        assert large_ttl >= small_ttl

    def test_calculate_ttl_with_render_time(self):
        """レンダリング時間を考慮したTTL計算テスト"""
        slow_render_ttl = self.validators.calculate_ttl(1024, 2.5, 10)
        fast_render_ttl = self.validators.calculate_ttl(1024, 0.1, 10)

        # レンダリング時間が長い方がTTLが長い（コスト高）
        assert slow_render_ttl >= fast_render_ttl

    def test_validate_cache_key_valid(self):
        """有効なキャッシュキー検証テスト"""
        valid_key = "render:abc123def456:template.html:12345"
        result = self.validators.validate_cache_key(valid_key)
        assert result is True

    def test_validate_cache_key_invalid(self):
        """無効なキャッシュキー検証テスト"""
        invalid_keys = [
            "",  # 空文字
            "invalid",  # 形式が違う
            "render:",  # 不完全
            None,  # None
        ]

        for key in invalid_keys:
            result = self.validators.validate_cache_key(key)
            assert result is False

    def test_validate_render_options_valid(self):
        """有効なレンダリングオプション検証テスト"""
        valid_options = {
            "theme": "dark",
            "language": "ja",
            "format": "html",
        }

        result = self.validators.validate_render_options(valid_options)
        assert result is True

    def test_validate_render_options_invalid(self):
        """無効なレンダリングオプション検証テスト"""
        invalid_options = [
            None,  # None
            "not_dict",  # 辞書ではない
            [],  # リスト
        ]

        for options in invalid_options:
            result = self.validators.validate_render_options(options)
            assert result is False

    def test_validate_render_options_empty(self):
        """空のレンダリングオプション検証テスト"""
        result = self.validators.validate_render_options({})
        assert result is True  # 空の辞書は有効

    def test_estimate_cache_efficiency_high(self):
        """高効率キャッシュ推定テスト"""
        # 大きなファイル、高頻度アクセス
        efficiency = self.validators.estimate_cache_efficiency(
            output_size=10000, access_frequency=50, render_time=2.0
        )

        assert efficiency > 0.7  # 高い効率

    def test_estimate_cache_efficiency_low(self):
        """低効率キャッシュ推定テスト"""
        # 小さなファイル、低頻度アクセス、短いレンダリング時間
        efficiency = self.validators.estimate_cache_efficiency(
            output_size=100, access_frequency=1, render_time=0.01
        )

        assert efficiency < 0.5  # 低い効率

    def test_cache_key_consistency(self):
        """キャッシュキー一貫性テスト"""
        content_hash = "test_hash"
        template_name = "test.html"
        render_options = {"key": "value"}

        # 同じ入力で複数回生成
        key1 = self.validators.generate_cache_key(
            content_hash, template_name, render_options
        )
        key2 = self.validators.generate_cache_key(
            content_hash, template_name, render_options
        )

        assert key1 == key2  # 同じ入力なら同じキー

    def test_ttl_custom_default(self):
        """カスタムデフォルトTTL設定テスト"""
        custom_validators = RenderCacheValidators(default_ttl=3600)
        ttl = custom_validators.calculate_ttl(1024, 0.1, 10)

        # デフォルトTTLを反映しているかテスト
        assert ttl >= 3600

    def test_cache_key_format(self):
        """キャッシュキー形式テスト"""
        cache_key = self.validators.generate_cache_key(
            "content123", "template.html", {"opt": "val"}
        )

        # キーがハッシュ形式になっているか確認
        assert isinstance(cache_key, str)
        assert len(cache_key) >= 32  # MD5ハッシュなら32文字以上

    def test_validators_error_handling(self):
        """バリデーターエラーハンドリングテスト"""
        # None値での処理
        cache_key = self.validators.generate_cache_key(None, None)
        assert cache_key is not None

        # 不正な型での処理
        result = self.validators.validate_cache_key(123)
        assert result is False

    def test_efficiency_boundary_values(self):
        """効率推定境界値テスト"""
        # 境界値での動作確認
        zero_efficiency = self.validators.estimate_cache_efficiency(0, 0, 0)
        assert zero_efficiency >= 0

        max_efficiency = self.validators.estimate_cache_efficiency(100000, 1000, 10.0)
        assert max_efficiency <= 1.0
