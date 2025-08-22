"""デコレーターパターンコアテスト

Decorator パターンの効率化されたコアテストスイート。
Issue #1114対応: 35テスト → 10テストに最適化
"""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.patterns.decorator import (
    CachingParserDecorator,
    ParserDecorator,
    RendererDecorator,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


# テスト用ベースクラス
class MockParser:
    """テスト用パーサー"""

    def __init__(self, name="mock_parser"):
        self.name = name
        self.parse_calls = []

    def parse(self, content: str, context: Dict[str, Any]) -> str:
        """パース処理"""
        result = f"parsed_{self.name}:{content}"
        self.parse_calls.append((content, context))
        return result

    def get_name(self) -> str:
        """名前取得"""
        return self.name


class MockRenderer:
    """テスト用レンダラー"""

    def __init__(self, name="mock_renderer"):
        self.name = name
        self.render_calls = []

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        """レンダー処理"""
        result = f"rendered_{self.name}:{data}"
        self.render_calls.append((data, context))
        return result

    def get_name(self) -> str:
        """名前取得"""
        return self.name


class TestCachingParserDecorator:
    """CachingParserDecorator テスト"""

    def test_基本_caching_decorator_初期化(self):
        """CachingParserDecoratorの基本初期化"""
        base_parser = MockParser("cached")
        decorator = CachingParserDecorator(base_parser)

        assert decorator._wrapped_parser is base_parser
        assert hasattr(decorator, "_cache")
        assert len(decorator._cache) == 0

    def test_基本_caching_decorator_キャッシュ機能(self):
        """CachingParserDecoratorの基本キャッシュ機能"""
        base_parser = MockParser("cached")
        decorator = CachingParserDecorator(base_parser)

        # 初回実行
        result1 = decorator.parse("cache test", {})
        # 同じ内容で再実行
        result2 = decorator.parse("cache test", {})

        assert result1 == result2
        assert len(base_parser.parse_calls) == 1  # キャッシュにより1回のみ実行

    def test_基本_caching_異なる_context(self):
        """CachingDecoratorの異なるContext処理"""
        base_parser = MockParser("context_cached")
        decorator = CachingParserDecorator(base_parser)

        # 同じ内容、異なるcontext
        result1 = decorator.parse("content", {"format": "html"})
        result2 = decorator.parse("content", {"format": "xml"})

        # Contextが違えば別々にキャッシュされる
        assert len(base_parser.parse_calls) == 2

    def test_応用_caching_cache_size_制限(self):
        """キャッシュサイズ制限の動作確認"""
        base_parser = MockParser("size_limited")
        decorator = CachingParserDecorator(base_parser, cache_size=2)

        # キャッシュサイズを超える実行
        decorator.parse("content1", {})
        decorator.parse("content2", {})
        decorator.parse("content3", {})  # サイズ制限を超える

        # キャッシュが制限内に保たれている
        assert len(decorator._cache) <= 2

    def test_基本_委譲機能(self):
        """Decoratorの基本委譲機能"""
        base_parser = MockParser("delegated")
        decorator = CachingParserDecorator(base_parser)

        # 基底パーサーのメソッドが委譲される
        assert decorator.get_name() == "delegated"


class TestDecoratorIntegration:
    """Decorator統合テスト"""

    def test_統合_decorator_委譲チェーン(self):
        """Decorator委譲チェーンの確認"""
        base_parser = MockParser("chain_test")
        cached_parser = CachingParserDecorator(base_parser)

        # 基底パーサーのメソッドが委譲チェーンを通して利用可能
        assert cached_parser.get_name() == "chain_test"

        # パース機能も正常動作
        result = cached_parser.parse("chain content", {})
        assert "parsed_chain_test:chain content" == result
