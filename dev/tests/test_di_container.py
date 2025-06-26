"""DIコンテナのテスト"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Protocol

from kumihan_formatter.core.di import (
    DIContainer, ServiceLifetime, inject, injectable, service,
    ServiceNotFoundError, CircularDependencyError, ServiceRegistrationError
)
from kumihan_formatter.core.di.testing import (
    TestDIContainer, DITestFixture, ServiceMockBuilder, isolated_container
)


# テスト用のインターフェースとクラス

class ILogger(Protocol):
    def log(self, message: str) -> None: ...


class IRepository(Protocol):
    def save(self, data: str) -> bool: ...
    def load(self) -> str: ...


@injectable
class ConsoleLogger:
    def log(self, message: str) -> None:
        print(f"LOG: {message}")


@injectable
class FileRepository:
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.data = ""
    
    def save(self, data: str) -> bool:
        self.logger.log(f"Saving: {data}")
        self.data = data
        return True
    
    def load(self) -> str:
        self.logger.log("Loading data")
        return self.data


@injectable
class BusinessService:
    def __init__(self, repository: IRepository, logger: ILogger):
        self.repository = repository
        self.logger = logger
    
    def process_data(self, data: str) -> str:
        self.logger.log("Processing data")
        self.repository.save(data.upper())
        return self.repository.load()


# 循環依存のテスト用クラス
@injectable
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b


@injectable
class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a


class TestDIContainer:
    """DIコンテナの基本機能テスト"""
    
    def test_register_and_resolve_singleton(self):
        """シングルトン登録と解決のテスト"""
        container = DIContainer()
        
        # シングルトンとして登録
        container.register_singleton(ILogger, ConsoleLogger)
        
        # 同じインスタンスが返されることを確認
        logger1 = container.get_service(ILogger)
        logger2 = container.get_service(ILogger)
        
        assert logger1 is logger2
        assert isinstance(logger1, ConsoleLogger)
    
    def test_register_and_resolve_transient(self):
        """トランジェント登録と解決のテスト"""
        container = DIContainer()
        
        # トランジェントとして登録
        container.register_transient(ILogger, ConsoleLogger)
        
        # 異なるインスタンスが返されることを確認
        logger1 = container.get_service(ILogger)
        logger2 = container.get_service(ILogger)
        
        assert logger1 is not logger2
        assert isinstance(logger1, ConsoleLogger)
        assert isinstance(logger2, ConsoleLogger)
    
    def test_dependency_injection(self):
        """依存性注入のテスト"""
        container = DIContainer()
        
        # 依存関係を登録
        container.register_singleton(ILogger, ConsoleLogger)
        container.register_transient(IRepository, FileRepository)
        container.register_transient(BusinessService)
        
        # ビジネスサービスを取得
        service = container.get_service(BusinessService)
        
        assert isinstance(service, BusinessService)
        assert isinstance(service.logger, ConsoleLogger)
        assert isinstance(service.repository, FileRepository)
        
        # 動作確認
        result = service.process_data("test")
        assert result == "TEST"
    
    def test_service_not_found(self):
        """未登録サービスのエラーテスト"""
        container = DIContainer()
        
        with pytest.raises(ServiceNotFoundError):
            container.get_service(ILogger)
    
    def test_circular_dependency_detection(self):
        """循環依存の検出テスト"""
        container = DIContainer()
        
        container.register_transient(ServiceA)
        container.register_transient(ServiceB)
        
        with pytest.raises(CircularDependencyError):
            container.get_service(ServiceA)
    
    def test_scoped_services(self):
        """スコープドサービスのテスト"""
        container = DIContainer()
        
        container.register_scoped(ILogger, ConsoleLogger)
        
        # 異なるスコープで異なるインスタンス
        with container.create_scope() as scope1:
            logger1a = scope1.get_service(ILogger)
            logger1b = scope1.get_service(ILogger)
            assert logger1a is logger1b  # 同一スコープ内では同じインスタンス
        
        with container.create_scope() as scope2:
            logger2 = scope2.get_service(ILogger)
            assert logger1a is not logger2  # 異なるスコープでは異なるインスタンス
    
    def test_factory_registration(self):
        """ファクトリー登録のテスト"""
        container = DIContainer()
        
        def logger_factory(provider):
            return ConsoleLogger()
        
        container.register_singleton(ILogger, factory=logger_factory)
        
        logger = container.get_service(ILogger)
        assert isinstance(logger, ConsoleLogger)
    
    def test_instance_registration(self):
        """インスタンス登録のテスト"""
        container = DIContainer()
        
        logger_instance = ConsoleLogger()
        container.register_singleton(ILogger, instance=logger_instance)
        
        retrieved_logger = container.get_service(ILogger)
        assert retrieved_logger is logger_instance


class TestDecorators:
    """デコレータのテスト"""
    
    def test_injectable_decorator(self):
        """@injectableデコレータのテスト"""
        
        @injectable
        class TestClass:
            pass
        
        assert hasattr(TestClass, '_injectable')
        assert TestClass._injectable is True
    
    def test_service_decorator(self):
        """@serviceデコレータのテスト"""
        
        @service(ILogger, ServiceLifetime.SINGLETON)
        class TestLogger:
            def log(self, message: str) -> None:
                pass
        
        assert hasattr(TestLogger, '_service_type')
        assert hasattr(TestLogger, '_service_lifetime')
        assert hasattr(TestLogger, '_auto_register')
        
        assert TestLogger._service_type is ILogger
        assert TestLogger._service_lifetime == ServiceLifetime.SINGLETON
        assert TestLogger._auto_register is True
    
    def test_inject_decorator(self):
        """@injectデコレータのテスト"""
        container = DIContainer()
        container.register_singleton(ILogger, ConsoleLogger)
        
        @inject
        def test_function(logger: ILogger, message: str = "test") -> str:
            logger.log(message)
            return message
        
        # 依存性が自動注入されることを確認
        result = test_function(message="hello")
        assert result == "hello"


class TestDITestSupport:
    """DIテスト支援機能のテスト"""
    
    def test_test_container_mocking(self):
        """テストコンテナのモック機能"""
        container = TestDIContainer()
        
        # モックを作成
        mock_logger = container.mock_service(ILogger)
        
        # モックが返されることを確認
        retrieved_logger = container.get_service(ILogger)
        assert retrieved_logger is mock_logger
        
        # モックの動作確認
        mock_logger.log("test")
        mock_logger.log.assert_called_with("test")
    
    def test_service_mock_builder(self):
        """サービスモックビルダーのテスト"""
        builder = ServiceMockBuilder(IRepository)
        
        mock = (builder
                .returns('load', 'test_data')
                .raises('save', ValueError("Test error"))
                .build())
        
        # 戻り値の確認
        assert mock.load() == 'test_data'
        
        # 例外の確認
        with pytest.raises(ValueError, match="Test error"):
            mock.save("data")
    
    def test_isolated_container_context(self):
        """分離コンテナコンテキストのテスト"""
        
        with isolated_container() as container:
            # テスト用のサービスを登録
            container.register_singleton(ILogger, ConsoleLogger)
            
            logger = container.get_service(ILogger)
            assert isinstance(logger, ConsoleLogger)
        
        # コンテキスト外では影響しない
        # （デフォルトコンテナが復元される）


class TestDIConfiguration:
    """DI設定機能のテスト"""
    
    def test_configuration_loading(self):
        """設定読み込みのテスト"""
        from kumihan_formatter.core.di.config_integration import (
            ConfigurationLoader, DIConfiguration, ServiceConfiguration
        )
        
        config_data = {
            'services': [
                {
                    'type_name': 'ILogger',
                    'implementation_name': 'ConsoleLogger',
                    'lifetime': 'singleton'
                }
            ],
            'auto_discovery': True
        }
        
        loader = ConfigurationLoader()
        config = loader.load_from_dict(config_data)
        
        assert isinstance(config, DIConfiguration)
        assert len(config.services) == 1
        assert config.auto_discovery is True
        
        service_config = config.services[0]
        assert service_config.type_name == 'ILogger'
        assert service_config.implementation_name == 'ConsoleLogger'
        assert service_config.lifetime == 'singleton'


class TestPerformance:
    """パフォーマンステスト"""
    
    def test_large_number_of_services(self):
        """大量のサービス登録・解決のテスト"""
        container = DIContainer()
        
        # 1000個のサービスを登録
        for i in range(1000):
            service_type = type(f'Service{i}', (), {'value': i})
            container.register_transient(service_type, service_type)
        
        # すべて解決できることを確認
        for i in range(1000):
            service_type = type(f'Service{i}', (), {'value': i})
            service = container.get_service(service_type)
            assert service.value == i
    
    def test_deep_dependency_chain(self):
        """深い依存関係チェーンのテスト"""
        container = DIContainer()
        
        # 深い依存関係チェーンを作成
        class BaseService:
            pass
        
        prev_type = BaseService
        for i in range(10):
            current_type = type(f'Service{i}', (), {
                '__init__': lambda self, dep=prev_type: setattr(self, 'dependency', dep)
            })
            container.register_transient(current_type)
            prev_type = current_type
        
        # 最終サービスを解決
        final_service = container.get_service(prev_type)
        assert final_service is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])