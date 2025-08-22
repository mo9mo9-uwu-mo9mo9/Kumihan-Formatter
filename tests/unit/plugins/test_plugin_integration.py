"""プラグイン統合テスト

Issue #914 Phase 3対応: 動的プラグインシステムの統合テスト
プラグインシステム全体の動作、他システムとの連携をテスト
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.patterns.dependency_injection import DIContainer
from kumihan_formatter.core.patterns.event_bus import (
    ExtendedEventType,
    IntegratedEventBus,
)
from kumihan_formatter.core.plugins.plugin_manager import (
    PluginInfo,
    PluginManager,
    PluginProtocol,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestPluginEventIntegration:
    """プラグインとイベントシステムの統合テスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()
        self.manager = PluginManager(self.container)
        self.temp_dir = tempfile.mkdtemp()
        self.event_listeners = []

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        # 全プラグインをアンロード
        for plugin_name in list(self.manager._plugins.keys()):
            self.manager.unload_plugin(plugin_name)

    def _create_plugin_file(self, content: str, filename: str = "test_plugin.py") -> str:
        """テスト用プラグインファイルを作成"""
        plugin_path = os.path.join(self.temp_dir, filename)
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(content)
        return plugin_path

    def test_プラグインロード時イベント発行(self) -> None:
        """プラグインロード時にイベントが正しく発行される"""
        # Given: プラグインファイルとイベントリスナー
        plugin_content = """
class EventPlugin:
    @property
    def name(self):
        return "event_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_path = self._create_plugin_file(plugin_content, "event_plugin.py")
        plugin_info = PluginInfo(
            name="event_plugin",
            version="1.0.0",
            description="イベントプラグイン",
            entry_point="EventPlugin",
        )

        events_captured = []

        def event_listener(event_type, sender, data):
            events_captured.append((event_type, sender, data))

        # When: イベントリスナーを設定してプラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event") as mock_publish:
            mock_publish.side_effect = event_listener
            result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが成功し、イベントが発行される
        assert result is True
        mock_publish.assert_called_once_with(
            ExtendedEventType.PLUGIN_LOADED,
            "PluginManager",
            {"plugin_name": "event_plugin", "version": "1.0.0"},
        )

    def test_プラグインアンロード時イベント発行(self) -> None:
        """プラグインアンロード時にイベントが正しく発行される"""
        # Given: ロード済みプラグイン
        plugin_content = """
class UnloadEventPlugin:
    @property
    def name(self):
        return "unload_event_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_path = self._create_plugin_file(plugin_content, "unload_event.py")
        plugin_info = PluginInfo(
            name="unload_event_plugin",
            version="1.0.0",
            description="アンロードイベントプラグイン",
            entry_point="UnloadEventPlugin",
        )

        # プラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            self.manager.load_plugin(plugin_path, plugin_info)

        # When: プラグインをアンロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event") as mock_publish:
            result = self.manager.unload_plugin("unload_event_plugin")

        # Then: アンロードが成功し、イベントが発行される
        assert result is True
        mock_publish.assert_called_once_with(
            ExtendedEventType.PLUGIN_UNLOADED,
            "PluginManager",
            {"plugin_name": "unload_event_plugin"},
        )


class TestPluginDIIntegration:
    """プラグインと依存性注入システムの統合テスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()
        self.manager = PluginManager(self.container)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        # 全プラグインをアンロード
        for plugin_name in list(self.manager._plugins.keys()):
            self.manager.unload_plugin(plugin_name)

    def _create_plugin_file(self, content: str, filename: str = "test_plugin.py") -> str:
        """テスト用プラグインファイルを作成"""
        plugin_path = os.path.join(self.temp_dir, filename)
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(content)
        return plugin_path

    def test_プラグイン初期化時DIコンテナ渡し(self) -> None:
        """プラグイン初期化時にDIコンテナが正しく渡される"""
        # Given: シンプルなプラグイン
        plugin_content = """
class DIPlugin:
    @property
    def name(self):
        return "di_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.container = container
        self.has_container = container is not None

    def cleanup(self):
        pass
"""
        plugin_path = self._create_plugin_file(plugin_content, "di_plugin.py")
        plugin_info = PluginInfo(
            name="di_plugin",
            version="1.0.0",
            description="DIプラグイン",
            entry_point="DIPlugin",
        )

        # When: プラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが成功し、DIコンテナが渡される
        assert result is True
        plugin = self.manager.get_plugin("di_plugin")
        assert plugin is not None
        assert plugin.container is self.container
        assert plugin.has_container is True

    def test_複数プラグインのDI共有(self) -> None:
        """複数プラグイン間でDIコンテナが共有される"""
        # Given: 複数のプラグイン
        plugin1_content = """
class SharedPlugin1:
    @property
    def name(self):
        return "shared_plugin1"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.container = container
        self.container_id = id(container)

    def cleanup(self):
        pass
"""
        plugin2_content = """
class SharedPlugin2:
    @property
    def name(self):
        return "shared_plugin2"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.container = container
        self.container_id = id(container)

    def cleanup(self):
        pass
"""
        plugin1_path = self._create_plugin_file(plugin1_content, "shared1.py")
        plugin2_path = self._create_plugin_file(plugin2_content, "shared2.py")

        plugin1_info = PluginInfo(
            name="shared_plugin1",
            version="1.0.0",
            description="共有プラグイン1",
            entry_point="SharedPlugin1",
        )
        plugin2_info = PluginInfo(
            name="shared_plugin2",
            version="1.0.0",
            description="共有プラグイン2",
            entry_point="SharedPlugin2",
        )

        # When: 両プラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            result1 = self.manager.load_plugin(plugin1_path, plugin1_info)
            result2 = self.manager.load_plugin(plugin2_path, plugin2_info)

        # Then: 両方のロードが成功し、同じコンテナが共有される
        assert result1 is True
        assert result2 is True

        plugin1 = self.manager.get_plugin("shared_plugin1")
        plugin2 = self.manager.get_plugin("shared_plugin2")
        assert plugin1 is not None
        assert plugin2 is not None
        assert plugin1.container_id == plugin2.container_id  # 同一のコンテナ


class TestPluginComplexScenarios:
    """プラグインの複雑なシナリオテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()
        self.manager = PluginManager(self.container)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        # 全プラグインをアンロード
        for plugin_name in list(self.manager._plugins.keys()):
            self.manager.unload_plugin(plugin_name)

    def _create_plugin_file(self, content: str, filename: str = "test_plugin.py") -> str:
        """テスト用プラグインファイルを作成"""
        plugin_path = os.path.join(self.temp_dir, filename)
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(content)
        return plugin_path

    def test_プラグインチェーン依存関係(self) -> None:
        """プラグインのチェーン依存関係テスト（A→B→C）"""
        # Given: チェーン依存関係を持つ3つのプラグイン
        plugin_a_content = """
class PluginA:
    @property
    def name(self):
        return "plugin_a"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_b_content = """
class PluginB:
    @property
    def name(self):
        return "plugin_b"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_c_content = """
class PluginC:
    @property
    def name(self):
        return "plugin_c"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_a_path = self._create_plugin_file(plugin_a_content, "plugin_a.py")
        plugin_b_path = self._create_plugin_file(plugin_b_content, "plugin_b.py")
        plugin_c_path = self._create_plugin_file(plugin_c_content, "plugin_c.py")

        plugin_a_info = PluginInfo(
            name="plugin_a",
            version="1.0.0",
            description="プラグインA",
            entry_point="PluginA",
        )
        plugin_b_info = PluginInfo(
            name="plugin_b",
            version="1.0.0",
            description="プラグインB",
            entry_point="PluginB",
            dependencies=["plugin_a"],
        )
        plugin_c_info = PluginInfo(
            name="plugin_c",
            version="1.0.0",
            description="プラグインC",
            entry_point="PluginC",
            dependencies=["plugin_b"],
        )

        # When: 正しい順序でロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            result_a = self.manager.load_plugin(plugin_a_path, plugin_a_info)
            result_b = self.manager.load_plugin(plugin_b_path, plugin_b_info)
            result_c = self.manager.load_plugin(plugin_c_path, plugin_c_info)

        # Then: 全てのロードが成功
        assert result_a is True
        assert result_b is True
        assert result_c is True
        assert len(self.manager.list_plugins()) == 3

    def test_プラグインチェーン依存関係_逆順ロード失敗(self) -> None:
        """プラグインのチェーン依存関係で逆順ロードが失敗する"""
        # Given: チェーン依存関係を持つ3つのプラグイン
        plugin_a_content = """
class PluginA:
    @property
    def name(self):
        return "plugin_a"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_c_content = """
class PluginC:
    @property
    def name(self):
        return "plugin_c"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_a_path = self._create_plugin_file(plugin_a_content, "plugin_a2.py")
        plugin_c_path = self._create_plugin_file(plugin_c_content, "plugin_c2.py")

        plugin_a_info = PluginInfo(
            name="plugin_a",
            version="1.0.0",
            description="プラグインA",
            entry_point="PluginA",
        )
        plugin_c_info = PluginInfo(
            name="plugin_c",
            version="1.0.0",
            description="プラグインC",
            entry_point="PluginC",
            dependencies=["plugin_b"],  # plugin_bが存在しない
        )

        # When: 依存関係が満たされていない状態でロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            result_a = self.manager.load_plugin(plugin_a_path, plugin_a_info)
            result_c = self.manager.load_plugin(plugin_c_path, plugin_c_info)

        # Then: Aは成功、Cは失敗
        assert result_a is True
        assert result_c is False
        assert len(self.manager.list_plugins()) == 1

    def test_大量プラグインロード_境界値(self) -> None:
        """大量プラグインのロード（境界値テスト）"""
        # Given: 大量のプラグインファイル（100個）
        plugin_count = 100
        plugin_paths = []
        plugin_infos = []

        for i in range(plugin_count):
            plugin_content = f"""
class Plugin{i}:
    @property
    def name(self):
        return "plugin_{i}"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
            plugin_path = self._create_plugin_file(plugin_content, f"plugin_{i}.py")
            plugin_info = PluginInfo(
                name=f"plugin_{i}",
                version="1.0.0",
                description=f"プラグイン{i}",
                entry_point=f"Plugin{i}",
            )
            plugin_paths.append(plugin_path)
            plugin_infos.append(plugin_info)

        # When: 全プラグインをロード
        success_count = 0
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            for path, info in zip(plugin_paths, plugin_infos):
                if self.manager.load_plugin(path, info):
                    success_count += 1

        # Then: 全プラグインのロードが成功
        assert success_count == plugin_count
        assert len(self.manager.list_plugins()) == plugin_count

    def test_プラグイン同時ロードアンロード(self) -> None:
        """プラグインの同時ロード・アンロードテスト"""
        # Given: 複数のプラグイン
        plugin_contents = []
        plugin_paths = []
        plugin_infos = []

        for i in range(5):
            content = f"""
class ConcurrentPlugin{i}:
    @property
    def name(self):
        return "concurrent_plugin_{i}"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
            path = self._create_plugin_file(content, f"concurrent_{i}.py")
            info = PluginInfo(
                name=f"concurrent_plugin_{i}",
                version="1.0.0",
                description=f"同時実行プラグイン{i}",
                entry_point=f"ConcurrentPlugin{i}",
            )
            plugin_contents.append(content)
            plugin_paths.append(path)
            plugin_infos.append(info)

        # When: 全プラグインをロード後、一部をアンロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            # ロード
            for path, info in zip(plugin_paths, plugin_infos):
                result = self.manager.load_plugin(path, info)
                assert result is True

            # 一部アンロード
            self.manager.unload_plugin("concurrent_plugin_1")
            self.manager.unload_plugin("concurrent_plugin_3")

        # Then: 残りのプラグインが正常に動作
        assert len(self.manager.list_plugins()) == 3
        assert self.manager.get_plugin("concurrent_plugin_0") is not None
        assert self.manager.get_plugin("concurrent_plugin_1") is None
        assert self.manager.get_plugin("concurrent_plugin_2") is not None
        assert self.manager.get_plugin("concurrent_plugin_3") is None
        assert self.manager.get_plugin("concurrent_plugin_4") is not None


class TestPluginErrorRecovery:
    """プラグインエラー回復テスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()
        self.manager = PluginManager(self.container)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        # 全プラグインをアンロード
        for plugin_name in list(self.manager._plugins.keys()):
            self.manager.unload_plugin(plugin_name)

    def _create_plugin_file(self, content: str, filename: str = "test_plugin.py") -> str:
        """テスト用プラグインファイルを作成"""
        plugin_path = os.path.join(self.temp_dir, filename)
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(content)
        return plugin_path

    def test_エラープラグイン後の正常プラグインロード(self) -> None:
        """エラープラグインの後に正常プラグインがロードできる"""
        # Given: エラープラグインと正常プラグイン
        error_plugin_content = """
class ErrorPlugin:
    @property
    def name(self):
        return "error_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        raise RuntimeError("初期化エラー")

    def cleanup(self):
        pass
"""
        normal_plugin_content = """
class NormalPlugin:
    @property
    def name(self):
        return "normal_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        error_path = self._create_plugin_file(error_plugin_content, "error.py")
        normal_path = self._create_plugin_file(normal_plugin_content, "normal.py")

        error_info = PluginInfo(
            name="error_plugin",
            version="1.0.0",
            description="エラープラグイン",
            entry_point="ErrorPlugin",
        )
        normal_info = PluginInfo(
            name="normal_plugin",
            version="1.0.0",
            description="正常プラグイン",
            entry_point="NormalPlugin",
        )

        # When: エラープラグインロード後、正常プラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            error_result = self.manager.load_plugin(error_path, error_info)
            normal_result = self.manager.load_plugin(normal_path, normal_info)

        # Then: エラープラグインは失敗、正常プラグインは成功
        assert error_result is False
        assert normal_result is True
        assert len(self.manager.list_plugins()) == 1
        assert self.manager.get_plugin("normal_plugin") is not None

    def test_プラグインマネージャー状態隔離(self) -> None:
        """プラグインマネージャーの状態隔離テスト"""
        # Given: 2つの独立したプラグインマネージャー
        manager1 = PluginManager(DIContainer())
        manager2 = PluginManager(DIContainer())

        plugin_content = """
class IsolationPlugin:
    @property
    def name(self):
        return "isolation_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        self.initialized = True

    def cleanup(self):
        self.cleaned_up = True
"""
        plugin_path = self._create_plugin_file(plugin_content, "isolation.py")
        plugin_info = PluginInfo(
            name="isolation_plugin",
            version="1.0.0",
            description="隔離プラグイン",
            entry_point="IsolationPlugin",
        )

        # When: manager1のみにプラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            result1 = manager1.load_plugin(plugin_path, plugin_info)

        # Then: manager1にのみプラグインが存在
        assert result1 is True
        assert len(manager1.list_plugins()) == 1
        assert len(manager2.list_plugins()) == 0
        assert manager1.get_plugin("isolation_plugin") is not None
        assert manager2.get_plugin("isolation_plugin") is None

        # Cleanup
        manager1.unload_plugin("isolation_plugin")


class TestPluginProtocolValidation:
    """プラグインプロトコル検証の詳細テスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()
        self.manager = PluginManager(self.container)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        # 全プラグインをアンロード
        for plugin_name in list(self.manager._plugins.keys()):
            self.manager.unload_plugin(plugin_name)

    def _create_plugin_file(self, content: str, filename: str = "test_plugin.py") -> str:
        """テスト用プラグインファイルを作成"""
        plugin_path = os.path.join(self.temp_dir, filename)
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(content)
        return plugin_path

    def test_プロトコル適合性_全属性存在(self) -> None:
        """プロトコル適合性: 全必須属性が存在する場合"""
        # Given: 完全なプラグイン
        plugin_content = """
class CompletePlugin:
    @property
    def name(self):
        return "complete_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        pass

    def cleanup(self):
        pass
"""
        plugin_path = self._create_plugin_file(plugin_content, "complete.py")
        plugin_info = PluginInfo(
            name="complete_plugin",
            version="1.0.0",
            description="完全プラグイン",
            entry_point="CompletePlugin",
        )

        # When: プラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
            result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが成功
        assert result is True

    def test_プロトコル非適合性_各属性欠損(self) -> None:
        """プロトコル非適合性: 各属性が欠損している場合"""
        # Given: 各属性が欠損したプラグインのテストケース
        test_cases = [
            # name属性欠損
            (
                """
class NoNamePlugin:
    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        pass

    def cleanup(self):
        pass
""",
                "no_name.py",
                "NoNamePlugin",
            ),
            # version属性欠損
            (
                """
class NoVersionPlugin:
    @property
    def name(self):
        return "no_version_plugin"

    def initialize(self, container):
        pass

    def cleanup(self):
        pass
""",
                "no_version.py",
                "NoVersionPlugin",
            ),
            # initializeメソッド欠損
            (
                """
class NoInitPlugin:
    @property
    def name(self):
        return "no_init_plugin"

    @property
    def version(self):
        return "1.0.0"

    def cleanup(self):
        pass
""",
                "no_init.py",
                "NoInitPlugin",
            ),
            # cleanupメソッド欠損
            (
                """
class NoCleanupPlugin:
    @property
    def name(self):
        return "no_cleanup_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, container):
        pass
""",
                "no_cleanup.py",
                "NoCleanupPlugin",
            ),
        ]

        for plugin_content, filename, entry_point in test_cases:
            plugin_path = self._create_plugin_file(plugin_content, filename)
            plugin_info = PluginInfo(
                name=f"test_{filename}",
                version="1.0.0",
                description="テストプラグイン",
                entry_point=entry_point,
            )

            # When: 不完全なプラグインをロード
            with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event"):
                result = self.manager.load_plugin(plugin_path, plugin_info)

            # Then: ロードが失敗
            assert result is False, f"ケース {filename} でロードが失敗すべき"
