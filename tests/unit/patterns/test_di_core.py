"""DIパターンコアテスト

Dependency Injection パターンの効率化されたコアテストスイート。
Issue #1114対応: 22テスト → 8テストに最適化
"""

from unittest.mock import Mock

import pytest

from kumihan_formatter.core.patterns.dependency_injection import DIContainer
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class MockService:
    """テスト用サービス"""

    def __init__(self, name="mock_service"):
        self.name = name

    def process(self, data):
        return f"processed_{self.name}:{data}"


class MockDependentService:
    """依存関係を持つサービス"""

    def __init__(self, dependency: MockService):
        self.dependency = dependency

    def execute(self, data):
        processed = self.dependency.process(data)
        return f"executed:{processed}"


class TestDICore:
    """DI コア機能テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()

    def test_基本_service_登録_解決(self):
        """基本的なサービス登録と解決"""
        service = MockService("test_service")
        self.container.register(MockService, service)

        resolved = self.container.resolve(MockService)

        assert resolved is service
        assert resolved.name == "test_service"

    def test_基本_dependency_injection(self):
        """依存関係注入の基本動作"""
        # 依存関係を登録
        dependency = MockService("dependency")
        self.container.register(MockService, dependency)

        # 依存関係を持つサービスを登録
        self.container.register(MockDependentService, MockDependentService)

        # 解決時に自動で依存関係が注入される
        service = self.container.resolve(MockDependentService)
        result = service.execute("test_data")

        assert "processed_dependency:test_data" in result
        assert "executed:" in result

    def test_統合_複雑dependency_解決(self):
        """複雑な依存関係チェーンの解決"""
        # 3層の依存関係を構築
        class Level1Service:
            def __init__(self):
                self.level = "level1"

        class Level2Service:
            def __init__(self, level1: Level1Service):
                self.level1 = level1
                self.level = "level2"

        class Level3Service:
            def __init__(self, level2: Level2Service):
                self.level2 = level2
                self.level = "level3"

        # 登録
        self.container.register(Level1Service, Level1Service)
        self.container.register(Level2Service, Level2Service)
        self.container.register(Level3Service, Level3Service)

        # 解決
        level3 = self.container.resolve(Level3Service)

        # 依存関係チェーン確認
        assert level3.level == "level3"
        assert level3.level2.level == "level2"
        assert level3.level2.level1.level == "level1"
