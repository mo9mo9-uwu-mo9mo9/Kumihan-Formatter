"""DI テスト支援機能"""

import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from unittest.mock import MagicMock, Mock

from .container import DIContainer
from .interfaces import ServiceLifetime, ServiceProvider

T = TypeVar("T")


class TestDIContainer(DIContainer):
    """テスト用DIコンテナ"""

    def __init__(self):
        super().__init__()
        self._mocks: Dict[Type, Any] = {}
        self._originals: Dict[Type, Any] = {}

    def mock_service(self, service_type: Type[T], mock_instance: Optional[T] = None, **mock_kwargs) -> T:
        """サービスをモックに置き換え"""

        # 元のサービスを保存
        if service_type in self._services:
            self._originals[service_type] = self._services[service_type]

        # モックインスタンスを作成
        if mock_instance is None:
            if hasattr(service_type, "__abstractmethods__"):
                # 抽象クラスの場合はMagicMockを使用
                mock_instance = MagicMock(spec=service_type, **mock_kwargs)
            else:
                # 具象クラスの場合はMockを使用
                mock_instance = Mock(spec=service_type, **mock_kwargs)

        # モックを登録
        self._mocks[service_type] = mock_instance
        self.register_singleton(service_type, instance=mock_instance)

        return mock_instance

    def get_mock(self, service_type: Type[T]) -> Optional[T]:
        """モックインスタンスを取得"""
        return self._mocks.get(service_type)

    def restore_service(self, service_type: Type[T]) -> None:
        """サービスを元に戻す"""
        if service_type in self._originals:
            self._services[service_type] = self._originals[service_type]
            if service_type in self._singletons:
                del self._singletons[service_type]
            del self._originals[service_type]

        if service_type in self._mocks:
            del self._mocks[service_type]

    def restore_all_services(self) -> None:
        """全てのサービスを元に戻す"""
        for service_type in list(self._mocks.keys()):
            self.restore_service(service_type)

    def verify_mock_calls(self, service_type: Type[T]) -> bool:
        """モックの呼び出しを検証"""
        mock_instance = self.get_mock(service_type)
        if mock_instance is None:
            return False

        # 基本的な検証（called, call_count等）
        return hasattr(mock_instance, "called") and mock_instance.called

    def reset_mocks(self) -> None:
        """全てのモックをリセット"""
        for mock in self._mocks.values():
            if hasattr(mock, "reset_mock"):
                mock.reset_mock()


class DITestFixture:
    """DIテスト用フィクスチャ"""

    def __init__(self):
        self._container: Optional[TestDIContainer] = None
        self._original_container: Optional[DIContainer] = None

    def setup(self) -> TestDIContainer:
        """テストセットアップ"""
        from .container import get_default_container, set_default_container

        # 元のコンテナを保存
        self._original_container = get_default_container()

        # テストコンテナを作成・設定
        self._container = TestDIContainer()
        set_default_container(self._container)

        return self._container

    def teardown(self) -> None:
        """テストクリーンアップ"""
        if self._container:
            self._container.restore_all_services()
            self._container.clear()

        if self._original_container:
            from .container import set_default_container

            set_default_container(self._original_container)

        self._container = None
        self._original_container = None

    @contextmanager
    def test_context(self):
        """テストコンテキストマネージャー"""
        container = self.setup()
        try:
            yield container
        finally:
            self.teardown()


class ServiceMockBuilder:
    """サービスモック構築ヘルパー"""

    def __init__(self, service_type: Type[T]):
        self.service_type = service_type
        self._return_values: Dict[str, Any] = {}
        self._side_effects: Dict[str, Any] = {}
        self._properties: Dict[str, Any] = {}

    def returns(self, method_name: str, return_value: Any) -> "ServiceMockBuilder":
        """メソッドの戻り値を設定"""
        self._return_values[method_name] = return_value
        return self

    def raises(self, method_name: str, exception: Exception) -> "ServiceMockBuilder":
        """メソッドが例外を発生させるよう設定"""
        self._side_effects[method_name] = exception
        return self

    def property_value(self, property_name: str, value: Any) -> "ServiceMockBuilder":
        """プロパティの値を設定"""
        self._properties[property_name] = value
        return self

    def build(self) -> Mock:
        """モックを構築"""
        mock = Mock(spec=self.service_type)

        # 戻り値を設定
        for method_name, return_value in self._return_values.items():
            getattr(mock, method_name).return_value = return_value

        # 副作用を設定
        for method_name, side_effect in self._side_effects.items():
            getattr(mock, method_name).side_effect = side_effect

        # プロパティを設定
        for property_name, value in self._properties.items():
            setattr(mock, property_name, value)

        return mock


class DITestCase:
    """DIテストケースの基底クラス"""

    def setUp(self) -> None:
        """テストケースのセットアップ"""
        self.fixture = DITestFixture()
        self.container = self.fixture.setup()

    def tearDown(self) -> None:
        """テストケースのクリーンアップ"""
        self.fixture.teardown()

    def mock_service(self, service_type: Type[T], mock_instance: Optional[T] = None, **mock_kwargs) -> T:
        """サービスをモック"""
        return self.container.mock_service(service_type, mock_instance, **mock_kwargs)

    def build_mock(self, service_type: Type[T]) -> ServiceMockBuilder:
        """モックビルダーを取得"""
        return ServiceMockBuilder(service_type)

    def verify_service_called(self, service_type: Type[T], method_name: str) -> bool:
        """サービスのメソッドが呼ばれたかを検証"""
        mock = self.container.get_mock(service_type)
        if mock is None:
            return False

        method_mock = getattr(mock, method_name, None)
        return method_mock is not None and method_mock.called

    def get_service_call_args(self, service_type: Type[T], method_name: str, call_index: int = 0) -> tuple:
        """サービスメソッドの呼び出し引数を取得"""
        mock = self.container.get_mock(service_type)
        if mock is None:
            return ()

        method_mock = getattr(mock, method_name, None)
        if method_mock is None or not method_mock.called:
            return ()

        call_list = method_mock.call_args_list
        if call_index >= len(call_list):
            return ()

        return call_list[call_index].args


# テスト用ユーティリティ関数


def create_test_container() -> TestDIContainer:
    """テスト用コンテナを作成"""
    return TestDIContainer()


@contextmanager
def isolated_container():
    """分離されたコンテナコンテキスト"""
    fixture = DITestFixture()
    container = fixture.setup()
    try:
        yield container
    finally:
        fixture.teardown()


def auto_mock_dependencies(target_class: Type[T]) -> T:
    """依存関係を自動的にモックして対象クラスのインスタンスを作成"""
    import inspect

    # コンストラクタの型ヒントを取得
    sig = inspect.signature(target_class.__init__)
    kwargs = {}

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        if param.annotation != param.empty:
            # 型に基づいてモックを作成
            mock_instance = Mock(spec=param.annotation)
            kwargs[param_name] = mock_instance

    return target_class(**kwargs)


class DIAssertions:
    """DI関連のアサーションヘルパー"""

    @staticmethod
    def assert_service_registered(container: ServiceProvider, service_type: Type) -> None:
        """サービスが登録されていることをアサート"""
        assert container.has_service(service_type), f"Service {service_type.__name__} is not registered"

    @staticmethod
    def assert_service_not_registered(container: ServiceProvider, service_type: Type) -> None:
        """サービスが登録されていないことをアサート"""
        assert not container.has_service(service_type), f"Service {service_type.__name__} should not be registered"

    @staticmethod
    def assert_same_instance(container: ServiceProvider, service_type: Type, expected_instance: Any) -> None:
        """サービスインスタンスが期待されるものと同じことをアサート"""
        actual_instance = container.get_service(service_type)
        assert actual_instance is expected_instance, f"Service instance mismatch for {service_type.__name__}"

    @staticmethod
    def assert_different_instances(container: ServiceProvider, service_type: Type) -> None:
        """毎回異なるインスタンスが返されることをアサート（トランジェント）"""
        instance1 = container.get_service(service_type)
        instance2 = container.get_service(service_type)
        assert instance1 is not instance2, f"Service {service_type.__name__} should return different instances"
