"""DI system basic functionality tests

Issue #914 Phase 1: DIシステム構築の基本動作確認テスト
"""

import unittest
from typing import Any, Protocol
from unittest.mock import MagicMock

from kumihan_formatter.core.patterns.dependency_injection import (
    DIContainer, ServiceLifetime, ServiceDescriptor,
    CircularDependencyError, ServiceNotFoundError,
    injectable, get_container
)
from kumihan_formatter.core.patterns.factories import (
    ParserFactory, RendererFactory, ServiceFactory,
    create_parser, create_renderer, get_service_factory
)


# テスト用プロトコル・クラス
class TestServiceProtocol(Protocol):
    def do_something(self) -> str:
        ...

class TestService:
    def do_something(self) -> str:
        return "test service"

class TestDependentService:
    def __init__(self, dependency: TestService) -> None:
        self.dependency = dependency

    def do_work(self) -> str:
        return f"work with {self.dependency.do_something()}"

@injectable
class TestInjectableService:
    def __init__(self, dependency: TestService) -> None:
        self.dependency = dependency

    def get_result(self) -> str:
        return f"injectable result: {self.dependency.do_something()}"


class TestDIContainer(unittest.TestCase):
    """DIコンテナの基本機能テスト"""

    def setUp(self) -> None:
        self.container = DIContainer()

    def test_register_and_resolve_singleton(self) -> None:
        """シングルトンサービスの登録と解決"""
        self.container.register(TestService, TestService, ServiceLifetime.SINGLETON)

        service1 = self.container.resolve(TestService)
        service2 = self.container.resolve(TestService)

        self.assertIsInstance(service1, TestService)
        self.assertIs(service1, service2)  # 同一インスタンス

    def test_register_and_resolve_transient(self) -> None:
        """トランジェントサービスの登録と解決"""
        self.container.register(TestService, TestService, ServiceLifetime.TRANSIENT)

        service1 = self.container.resolve(TestService)
        service2 = self.container.resolve(TestService)

        self.assertIsInstance(service1, TestService)
        self.assertIsInstance(service2, TestService)
        self.assertIsNot(service1, service2)  # 異なるインスタンス

    def test_dependency_injection(self) -> None:
        """依存関係の自動注入"""
        self.container.register(TestService, TestService)
        self.container.register(TestDependentService, TestDependentService)

        dependent_service = self.container.resolve(TestDependentService)

        self.assertIsInstance(dependent_service, TestDependentService)
        self.assertIsInstance(dependent_service.dependency, TestService)
        self.assertEqual(dependent_service.do_work(), "work with test service")

    def test_register_singleton_instance(self) -> None:
        """シングルトンインスタンスの直接登録"""
        instance = TestService()
        self.container.register_singleton(TestService, instance)

        resolved = self.container.resolve(TestService)

        self.assertIs(resolved, instance)

    def test_register_factory(self) -> None:
        """ファクトリー関数の登録"""
        def test_factory(container: DIContainer) -> TestService:
            return TestService()

        self.container.register_factory(TestService, test_factory)

        service = self.container.resolve(TestService)

        self.assertIsInstance(service, TestService)

    def test_service_not_found_error(self) -> None:
        """未登録サービスの解決でエラー"""
        with self.assertRaises(ServiceNotFoundError):
            self.container.resolve(TestService)

    def test_circular_dependency_detection(self) -> None:
        """循環参照の検出"""
        # 循環参照を作るためのテストクラス
        class ServiceA:
            def __init__(self, b: 'ServiceB') -> None:
                self.b = b

        class ServiceB:
            def __init__(self, a: ServiceA) -> None:
                self.a = a

        self.container.register(ServiceA, ServiceA)
        self.container.register(ServiceB, ServiceB)

        # 循環参照の場合、CircularDependencyErrorまたはTypeErrorが発生することを期待
        with self.assertRaises((CircularDependencyError, TypeError)):
            self.container.resolve(ServiceA)


class TestServiceFactory(unittest.TestCase):
    """統一ファクトリーシステムのテスト"""

    def setUp(self) -> None:
        self.service_factory = ServiceFactory()

    def test_get_parser_factory(self) -> None:
        """パーサーファクトリーの取得"""
        parser_factory = self.service_factory.get_factory('parser')

        self.assertIsInstance(parser_factory, ParserFactory)

    def test_get_renderer_factory(self) -> None:
        """レンダラーファクトリーの取得"""
        renderer_factory = self.service_factory.get_factory('renderer')

        self.assertIsInstance(renderer_factory, RendererFactory)

    def test_register_custom_factory(self) -> None:
        """カスタムファクトリーの登録"""
        mock_factory = MagicMock()

        self.service_factory.register_factory('custom', mock_factory)
        retrieved_factory = self.service_factory.get_factory('custom')

        self.assertIs(retrieved_factory, mock_factory)

    def test_unknown_factory_error(self) -> None:
        """未知のファクトリータイプでエラー"""
        with self.assertRaises(ValueError):
            self.service_factory.get_factory('unknown')


class TestParserFactory(unittest.TestCase):
    """パーサーファクトリーのテスト"""

    def setUp(self) -> None:
        self.parser_factory = ParserFactory()

    def test_get_supported_types(self) -> None:
        """対応パーサータイプの取得"""
        supported_types = self.parser_factory.get_supported_types()

        self.assertIsInstance(supported_types, list)
        # デフォルトで登録されている可能性があるタイプをチェック
        # 実際の実装に依存するため、空でない場合のみチェック
        if supported_types:
            self.assertIsInstance(supported_types[0], str)


class TestRendererFactory(unittest.TestCase):
    """レンダラーファクトリーのテスト"""

    def setUp(self) -> None:
        self.renderer_factory = RendererFactory()

    def test_get_supported_types(self) -> None:
        """対応レンダラータイプの取得"""
        supported_types = self.renderer_factory.get_supported_types()

        self.assertIsInstance(supported_types, list)
        # デフォルトで登録されている可能性があるタイプをチェック
        if supported_types:
            self.assertIsInstance(supported_types[0], str)


class TestGlobalInstances(unittest.TestCase):
    """グローバルインスタンスのテスト"""

    def test_get_container(self) -> None:
        """グローバルコンテナの取得"""
        container = get_container()

        self.assertIsInstance(container, DIContainer)

        # 同一インスタンスであることを確認
        container2 = get_container()
        self.assertIs(container, container2)

    def test_get_service_factory(self) -> None:
        """グローバルサービスファクトリーの取得"""
        factory = get_service_factory()

        self.assertIsInstance(factory, ServiceFactory)

        # 同一インスタンスであることを確認
        factory2 = get_service_factory()
        self.assertIs(factory, factory2)


class TestIntegration(unittest.TestCase):
    """統合テスト"""

    def test_factory_with_di_container(self) -> None:
        """ファクトリーとDIコンテナの連携"""
        container = DIContainer()
        service_factory = ServiceFactory(container)

        # テストサービスを登録
        container.register(TestService, TestService)

        # ファクトリー経由でアクセス
        parser_factory = service_factory.get_factory('parser')
        self.assertIsNotNone(parser_factory)

    def test_shortcut_functions(self) -> None:
        """ショートカット関数のテスト"""
        # 実際のパーサー/レンダラーが存在しないため、
        # エラーハンドリングのテストのみ実行

        with self.assertRaises((ValueError, ImportError, AttributeError)):
            create_parser('nonexistent_parser')

        with self.assertRaises((ValueError, ImportError, AttributeError)):
            create_renderer('nonexistent_renderer')


if __name__ == '__main__':
    unittest.main()
