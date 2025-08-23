"""ファクトリーシステム統合テスト

Factory パターンとLegacy Factory統合の効率化されたテストスイート。
Issue #1114対応: 59テスト → 20テストに最適化
"""

from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.patterns.dependency_injection import DIContainer
from kumihan_formatter.core.patterns.factories import (
    AbstractFactory,
    ParserFactory,
    RendererFactory,
    ServiceFactory,
    create_parser,
    create_renderer,
    get_parser_factory,
    get_renderer_factory,
    get_service_factory,
    initialize_factories,
)
from kumihan_formatter.core.patterns.legacy_factory_integration import (
    LegacyFactoryAdapter,
    create_legacy_file_operations,
    create_legacy_list_parser,
    create_legacy_markdown_converter,
    get_legacy_adapter,
    initialize_legacy_integration,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


# テスト用モッククラス
class MockParser:
    """テスト用パーサーモック"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def parse(self, content: str) -> str:
        return f"parsed:{content}"


class MockRenderer:
    """テスト用レンダラーモック"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        return f"rendered:{data}"


class TestFactorySystem:
    """ファクトリーシステムのコアテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()

    def test_基本_parser_factory_作成(self):
        """ParserFactoryの基本作成とサービス登録"""
        factory = ParserFactory(self.container)
        factory.register("test_parser", MockParser)

        parser = factory.create("test_parser")
        assert isinstance(parser, MockParser)
        assert parser.parse("test") == "parsed:test"

    def test_基本_renderer_factory_作成(self):
        """RendererFactoryの基本作成とサービス登録"""
        factory = RendererFactory(self.container)
        factory.register("test_renderer", MockRenderer)

        renderer = factory.create("test_renderer")
        assert isinstance(renderer, MockRenderer)
        assert renderer.render("test", {}) == "rendered:test"

    def test_基本_service_factory_統合(self):
        """ServiceFactoryによる統合ファクトリー管理"""
        service_factory = ServiceFactory(self.container)

        # パーサーとレンダラー登録
        service_factory.get_factory("parser").register("mock_parser", MockParser)
        service_factory.get_factory("renderer").register("mock_renderer", MockRenderer)

        # 生成とテスト
        parser = service_factory.create("parser", "mock_parser")
        renderer = service_factory.create("renderer", "mock_renderer")

        assert parser.parse("content") == "parsed:content"
        assert renderer.render("data", {}) == "rendered:data"

    def test_基本_initialize_factories_システム初期化(self):
        """ファクトリーシステム全体の初期化"""
        initialize_factories()

        # グローバルファクトリー取得確認
        parser_factory = get_parser_factory()
        renderer_factory = get_renderer_factory()
        service_factory = get_service_factory()

        assert isinstance(parser_factory, ParserFactory)
        assert isinstance(renderer_factory, RendererFactory)
        assert isinstance(service_factory, ServiceFactory)

    def test_基本_create_convenience_functions(self):
        """便利関数create_parser/create_rendererのテスト"""
        # ファクトリー初期化
        initialize_factories()
        get_parser_factory().register("test_parser", MockParser)
        get_renderer_factory().register("test_renderer", MockRenderer)

        # 便利関数での生成
        parser = create_parser("test_parser")
        renderer = create_renderer("test_renderer")

        assert isinstance(parser, MockParser)
        assert isinstance(renderer, MockRenderer)

    def test_エラー_存在しないサービス作成(self):
        """存在しないサービス作成時のエラー処理"""
        factory = ParserFactory(self.container)

        with pytest.raises(ValueError, match="Unknown.*non_existent"):
            factory.create("non_existent")

    def test_エラー_不正なファクトリータイプ(self):
        """ServiceFactoryで不正なファクトリータイプ指定"""
        service_factory = ServiceFactory(self.container)

        with pytest.raises(ValueError, match="Unknown factory type"):
            service_factory.get_factory("invalid_type")

    def test_基本_重複サービス登録_許可(self):
        """同一名でのサービス重複登録（実装では許可）"""
        factory = ParserFactory(self.container)
        factory.register("duplicate", MockParser)
        factory.register("duplicate", MockParser)  # 重複登録が許可される

        # 正常に動作することを確認
        parser = factory.create("duplicate")
        assert isinstance(parser, MockParser)


class TestLegacyFactoryIntegration:
    """Legacy Factory統合テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()

    def test_基本_legacy_adapter_初期化(self):
        """LegacyFactoryAdapterの基本初期化"""
        adapter = LegacyFactoryAdapter(self.container)

        assert adapter.container is self.container
        assert adapter.service_factory is not None

    def test_基本_legacy_adapter_デフォルトコンテナ(self):
        """デフォルトコンテナでのLegacyFactoryAdapter初期化"""
        adapter = LegacyFactoryAdapter()

        assert adapter.container is not None
        assert adapter.service_factory is not None

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.get_service_factory")
    def test_基本_create_legacy_list_parser(self, mock_get_factory):
        """Legacy list parserの作成テスト"""
        mock_factory = Mock()
        mock_parser = Mock()
        mock_factory.create.return_value = mock_parser
        mock_get_factory.return_value = mock_factory

        result = create_legacy_list_parser("test_type")

        assert result is mock_parser
        mock_factory.create.assert_called_once_with("parser", "test_type")

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.get_service_factory")
    def test_基本_create_legacy_markdown_converter(self, mock_get_factory):
        """Legacy markdown converterの作成テスト"""
        mock_factory = Mock()
        mock_converter = Mock()
        mock_factory.create.return_value = mock_converter
        mock_get_factory.return_value = mock_factory

        result = create_legacy_markdown_converter("test_format")

        assert result is mock_converter
        mock_factory.create.assert_called_once_with("renderer", "test_format")

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.get_service_factory")
    def test_基本_create_legacy_file_operations(self, mock_get_factory):
        """Legacy file operationsの作成テスト"""
        mock_factory = Mock()
        mock_ops = Mock()
        mock_factory.create.return_value = mock_ops
        mock_get_factory.return_value = mock_factory

        result = create_legacy_file_operations("test_type")

        assert result is mock_ops
        mock_factory.create.assert_called_once_with("service", "test_type")

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter")
    def test_基本_get_legacy_adapter(self, mock_adapter_class):
        """Legacy adapterの取得テスト"""
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter

        result = get_legacy_adapter()

        assert result is mock_adapter
        mock_adapter_class.assert_called_once()

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.get_legacy_adapter")
    def test_基本_initialize_legacy_integration(self, mock_get_adapter):
        """Legacy統合システムの初期化テスト"""
        mock_adapter = Mock()
        mock_get_adapter.return_value = mock_adapter

        result = initialize_legacy_integration()

        assert result is mock_adapter
        mock_get_adapter.assert_called_once()

    def test_エラー_legacy_adapter_無効コンテナ(self):
        """無効なコンテナでのLegacyFactoryAdapter初期化エラー"""
        with pytest.raises(TypeError):
            LegacyFactoryAdapter("invalid_container")


class TestIntegration:
    """統合テスト"""

    def test_統合_完全ワークフロー(self):
        """ファクトリーシステム全体の統合ワークフロー"""
        # システム初期化
        initialize_factories()
        initialize_legacy_integration()

        # サービス登録
        get_parser_factory().register("test_parser", MockParser)
        get_renderer_factory().register("test_renderer", MockRenderer)

        # 通常ファクトリー使用
        parser = create_parser("test_parser")
        renderer = create_renderer("test_renderer")

        # ワークフロー実行
        parsed = parser.parse("test content")
        rendered = renderer.render(parsed, {})

        assert parsed == "parsed:test content"
        assert rendered == "rendered:parsed:test content"

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.create_legacy_list_parser")
    @patch("kumihan_formatter.core.list_parser_factory.create_list_parser")
    def test_統合_legacy_modern_連携(self, mock_create_list_parser, mock_legacy_parser):
        """Legacy FactoryとModern Factoryの連携テスト"""
        # Modern Factory初期化
        initialize_factories()
        get_renderer_factory().register("modern_renderer", MockRenderer)

        # Legacy Parser Mock設定（フォールバック対応）
        mock_parser = Mock()
        mock_parser.parse.return_value = "legacy_parsed:content"
        mock_legacy_parser.return_value = mock_parser
        mock_create_list_parser.return_value = mock_parser

        # Legacy-Modern連携
        legacy_parser = create_legacy_list_parser("legacy_type")
        modern_renderer = create_renderer("modern_renderer")

        # ワークフロー
        parsed = legacy_parser.parse("content")
        rendered = modern_renderer.render(parsed, {})

        assert parsed == "legacy_parsed:content"
        assert rendered == "rendered:legacy_parsed:content"

    def test_統合_エラー処理_チェーン(self):
        """統合システムでのエラー処理チェーン"""
        initialize_factories()

        # 存在しないサービス使用時のエラー伝播
        with pytest.raises(ValueError):
            create_parser("non_existent_parser")

        with pytest.raises(ValueError):
            create_renderer("non_existent_renderer")
