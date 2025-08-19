"""PluginManagerクラスのテスト

Issue #914 Phase 3対応: 動的プラグインシステムの包括的テスト
カバレッジ80%以上を目標とした正常系・異常系・境界値テストを実装
"""

import importlib.util
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock, patch

import pytest

from kumihan_formatter.core.patterns.dependency_injection import DIContainer
from kumihan_formatter.core.patterns.event_bus import ExtendedEventType
from kumihan_formatter.core.plugins.plugin_manager import (
    PluginInfo,
    PluginManager,
    PluginProtocol,
    get_plugin_manager,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class MockPlugin:
    """テスト用モックプラグイン"""

    def __init__(self, name: str = "test_plugin", version: str = "1.0.0"):
        self._name = name
        self._version = version
        self.initialized = False
        self.cleaned_up = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    def initialize(self, container: DIContainer) -> None:
        """プラグイン初期化"""
        self.initialized = True
        self.container = container

    def cleanup(self) -> None:
        """プラグインクリーンアップ"""
        self.cleaned_up = True


class InvalidPlugin:
    """不正なプラグイン（プロトコル非適合）"""

    def __init__(self):
        self.name = "invalid"
        # version属性がない
        # initializeメソッドがない
        # cleanupメソッドがない


class BrokenPlugin:
    """初期化時にエラーを発生させるプラグイン"""

    @property
    def name(self) -> str:
        return "broken_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, container: DIContainer) -> None:
        """初期化時にエラーを発生"""
        raise RuntimeError("初期化エラー")

    def cleanup(self) -> None:
        """クリーンアップ"""
        pass


class TestPluginManager:
    """PluginManagerクラスのテスト"""

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

    def test_正常系_プラグインロード成功(self) -> None:
        """正常系: プラグインのロードが成功する"""
        # Given: 有効なプラグインファイル
        plugin_content = '''
class TestPlugin:
    @property
    def name(self):
        return "test_plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    def initialize(self, container):
        self.initialized = True
    
    def cleanup(self):
        self.cleaned_up = True
'''
        plugin_path = self._create_plugin_file(plugin_content)
        plugin_info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="テストプラグイン",
            entry_point="TestPlugin",
        )

        # When: プラグインをロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event") as mock_publish:
            result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが成功する
        assert result is True
        assert "test_plugin" in self.manager._plugins
        assert "test_plugin" in self.manager._plugin_info
        assert self.manager._plugin_info["test_plugin"] == plugin_info

        # イベントが発行されることを確認
        mock_publish.assert_called_once_with(
            ExtendedEventType.PLUGIN_LOADED,
            "PluginManager",
            {"plugin_name": "test_plugin", "version": "1.0.0"},
        )

    def test_正常系_プラグインアンロード成功(self) -> None:
        """正常系: プラグインのアンロードが成功する"""
        # Given: ロード済みのプラグイン
        mock_plugin = MockPlugin()
        self.manager._plugins["test_plugin"] = mock_plugin
        self.manager._plugin_info["test_plugin"] = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="テストプラグイン",
            entry_point="MockPlugin",
        )

        # When: プラグインをアンロード
        with patch("kumihan_formatter.core.plugins.plugin_manager.publish_event") as mock_publish:
            result = self.manager.unload_plugin("test_plugin")

        # Then: アンロードが成功する
        assert result is True
        assert "test_plugin" not in self.manager._plugins
        assert "test_plugin" not in self.manager._plugin_info
        assert mock_plugin.cleaned_up is True

        # イベントが発行されることを確認
        mock_publish.assert_called_once_with(
            ExtendedEventType.PLUGIN_UNLOADED,
            "PluginManager",
            {"plugin_name": "test_plugin"},
        )

    def test_正常系_プラグイン取得成功(self) -> None:
        """正常系: プラグインの取得が成功する"""
        # Given: ロード済みのプラグイン
        mock_plugin = MockPlugin()
        self.manager._plugins["test_plugin"] = mock_plugin

        # When: プラグインを取得
        result = self.manager.get_plugin("test_plugin")

        # Then: プラグインが取得できる
        assert result is mock_plugin

    def test_正常系_プラグイン一覧取得(self) -> None:
        """正常系: プラグイン一覧の取得が成功する"""
        # Given: 複数のプラグイン情報
        plugin_info1 = PluginInfo(
            name="plugin1", version="1.0.0", description="プラグイン1", entry_point="Plugin1"
        )
        plugin_info2 = PluginInfo(
            name="plugin2", version="2.0.0", description="プラグイン2", entry_point="Plugin2"
        )
        self.manager._plugin_info["plugin1"] = plugin_info1
        self.manager._plugin_info["plugin2"] = plugin_info2

        # When: プラグイン一覧を取得
        result = self.manager.list_plugins()

        # Then: 全プラグイン情報が取得できる
        assert len(result) == 2
        assert plugin_info1 in result
        assert plugin_info2 in result

    def test_正常系_依存関係なしプラグイン(self) -> None:
        """正常系: 依存関係のないプラグインの依存関係チェック"""
        # Given: 依存関係のないプラグイン情報
        plugin_info = PluginInfo(
            name="no_deps_plugin",
            version="1.0.0",
            description="依存関係なしプラグイン",
            entry_point="Plugin",
            dependencies=None,
        )

        # When: 依存関係をチェック
        result = self.manager._check_dependencies(plugin_info)

        # Then: チェックが成功する
        assert result is True

    def test_正常系_依存関係ありプラグイン(self) -> None:
        """正常系: 依存関係のあるプラグインの依存関係チェック"""
        # Given: 依存プラグインがロード済み
        dep_plugin = MockPlugin("dependency_plugin", "1.0.0")
        self.manager._plugins["dependency_plugin"] = dep_plugin

        plugin_info = PluginInfo(
            name="dependent_plugin",
            version="1.0.0",
            description="依存プラグイン",
            entry_point="Plugin",
            dependencies=["dependency_plugin"],
        )

        # When: 依存関係をチェック
        result = self.manager._check_dependencies(plugin_info)

        # Then: チェックが成功する
        assert result is True

    def test_異常系_存在しないファイル(self) -> None:
        """異常系: 存在しないプラグインファイルの処理"""
        # Given: 存在しないファイルパス
        plugin_info = PluginInfo(
            name="nonexistent_plugin",
            version="1.0.0",
            description="存在しないプラグイン",
            entry_point="Plugin",
        )

        # When: 存在しないファイルをロード
        result = self.manager.load_plugin("/nonexistent/path/plugin.py", plugin_info)

        # Then: ロードが失敗する
        assert result is False
        assert "nonexistent_plugin" not in self.manager._plugins

    def test_異常系_不正なプラグインファイル(self) -> None:
        """異常系: 不正なプラグインファイルの処理"""
        # Given: 構文エラーのあるプラグインファイル
        plugin_content = '''
class BrokenPlugin:
    def invalid_syntax(self:
        # 構文エラー
'''
        plugin_path = self._create_plugin_file(plugin_content, "broken.py")
        plugin_info = PluginInfo(
            name="broken_plugin",
            version="1.0.0",
            description="壊れたプラグイン",
            entry_point="BrokenPlugin",
        )

        # When: 不正なファイルをロード
        result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが失敗する
        assert result is False
        assert "broken_plugin" not in self.manager._plugins

    def test_異常系_プロトコル非適合プラグイン(self) -> None:
        """異常系: プラグインプロトコルに適合しないプラグイン"""
        # Given: プロトコル非適合のプラグインファイル
        plugin_content = '''
class InvalidPlugin:
    def __init__(self):
        self.name = "invalid"
        # version属性がない
        # initializeメソッドがない
        # cleanupメソッドがない
'''
        plugin_path = self._create_plugin_file(plugin_content, "invalid.py")
        plugin_info = PluginInfo(
            name="invalid_plugin",
            version="1.0.0",
            description="不正なプラグイン",
            entry_point="InvalidPlugin",
        )

        # When: プロトコル非適合プラグインをロード
        result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが失敗する
        assert result is False
        assert "invalid_plugin" not in self.manager._plugins

    def test_異常系_初期化エラープラグイン(self) -> None:
        """異常系: 初期化時にエラーを発生するプラグイン"""
        # Given: 初期化エラーのプラグインファイル
        plugin_content = '''
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
'''
        plugin_path = self._create_plugin_file(plugin_content, "error.py")
        plugin_info = PluginInfo(
            name="error_plugin",
            version="1.0.0",
            description="エラープラグイン",
            entry_point="ErrorPlugin",
        )

        # When: エラープラグインをロード
        result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが失敗する
        assert result is False
        assert "error_plugin" not in self.manager._plugins

    def test_異常系_依存関係未満足(self) -> None:
        """異常系: 依存関係が満たされていないプラグイン"""
        # Given: 依存プラグインが未ロードの状態
        plugin_content = '''
class DependentPlugin:
    @property
    def name(self):
        return "dependent_plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    def initialize(self, container):
        pass
    
    def cleanup(self):
        pass
'''
        plugin_path = self._create_plugin_file(plugin_content, "dependent.py")
        plugin_info = PluginInfo(
            name="dependent_plugin",
            version="1.0.0",
            description="依存プラグイン",
            entry_point="DependentPlugin",
            dependencies=["missing_dependency"],
        )

        # When: 依存関係未満足のプラグインをロード
        result = self.manager.load_plugin(plugin_path, plugin_info)

        # Then: ロードが失敗する
        assert result is False
        assert "dependent_plugin" not in self.manager._plugins

    def test_異常系_未登録プラグインのアンロード(self) -> None:
        """異常系: 未登録プラグインのアンロード試行"""
        # When: 未登録プラグインをアンロード
        result = self.manager.unload_plugin("nonexistent_plugin")

        # Then: アンロードが失敗する
        assert result is False

    def test_異常系_アンロード時エラー(self) -> None:
        """異常系: アンロード時にクリーンアップエラーが発生"""
        # Given: クリーンアップエラーを発生するプラグイン
        mock_plugin = Mock()
        mock_plugin.cleanup.side_effect = RuntimeError("クリーンアップエラー")
        self.manager._plugins["error_plugin"] = mock_plugin
        self.manager._plugin_info["error_plugin"] = PluginInfo(
            name="error_plugin",
            version="1.0.0",
            description="エラープラグイン",
            entry_point="ErrorPlugin",
        )

        # When: プラグインをアンロード
        result = self.manager.unload_plugin("error_plugin")

        # Then: アンロードが失敗する
        assert result is False
        # プラグインは削除されない
        assert "error_plugin" in self.manager._plugins

    def test_異常系_存在しないプラグイン取得(self) -> None:
        """異常系: 存在しないプラグインの取得"""
        # When: 存在しないプラグインを取得
        result = self.manager.get_plugin("nonexistent_plugin")

        # Then: Noneが返される
        assert result is None

    def test_境界値_空の依存関係リスト(self) -> None:
        """境界値: 空の依存関係リスト"""
        # Given: 空の依存関係リストを持つプラグイン情報
        plugin_info = PluginInfo(
            name="empty_deps_plugin",
            version="1.0.0",
            description="空依存関係プラグイン",
            entry_point="Plugin",
            dependencies=[],
        )

        # When: 依存関係をチェック
        result = self.manager._check_dependencies(plugin_info)

        # Then: チェックが成功する
        assert result is True

    def test_境界値_プラグインプロトコルチェック詳細(self) -> None:
        """境界値: プラグインプロトコルの詳細チェック"""
        # Given: 各種不正なプラグインインスタンス
        test_cases = [
            # name属性が文字列でない
            type("BadPlugin", (), {
                "name": 123,
                "version": "1.0.0",
                "initialize": lambda self, c: None,
                "cleanup": lambda self: None,
            })(),
            # version属性が文字列でない
            type("BadPlugin", (), {
                "name": "test",
                "version": 123,
                "initialize": lambda self, c: None,
                "cleanup": lambda self: None,
            })(),
            # initializeがcallableでない
            type("BadPlugin", (), {
                "name": "test",
                "version": "1.0.0",
                "initialize": "not_callable",
                "cleanup": lambda self: None,
            })(),
            # cleanupがcallableでない
            type("BadPlugin", (), {
                "name": "test",
                "version": "1.0.0",
                "initialize": lambda self, c: None,
                "cleanup": "not_callable",
            })(),
        ]

        for plugin_instance in test_cases:
            # When: プロトコルチェック
            result = self.manager._check_plugin_protocol(plugin_instance)

            # Then: チェックが失敗する
            assert result is False

    def test_境界値_プロトコルチェック属性エラー(self) -> None:
        """境界値: プロトコルチェック時の属性エラー"""
        # Given: 属性アクセス時にエラーを発生するプラグイン
        class ErrorPropPlugin:
            @property
            def name(self) -> str:
                raise AttributeError("name属性エラー")

            @property
            def version(self) -> str:
                return "1.0.0"

            def initialize(self, container: DIContainer) -> None:
                pass

            def cleanup(self) -> None:
                pass

        plugin_instance = ErrorPropPlugin()

        # When: プロトコルチェック
        result = self.manager._check_plugin_protocol(plugin_instance)

        # Then: チェックが失敗する
        assert result is False

    def test_統合_プラグインライフサイクル完全テスト(self) -> None:
        """統合: プラグインのライフサイクル完全テスト"""
        # Given: 有効なプラグインファイル
        plugin_content = '''
class LifecyclePlugin:
    def __init__(self):
        self.state = "created"
    
    @property
    def name(self):
        return "lifecycle_plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    def initialize(self, container):
        self.state = "initialized"
        self.container = container
    
    def cleanup(self):
        self.state = "cleaned_up"
'''
        plugin_path = self._create_plugin_file(plugin_content, "lifecycle.py")
        plugin_info = PluginInfo(
            name="lifecycle_plugin",
            version="1.0.0",
            description="ライフサイクルプラグイン",
            entry_point="LifecyclePlugin",
        )

        # When: プラグインのライフサイクル実行
        # 1. ロード
        load_result = self.manager.load_plugin(plugin_path, plugin_info)
        assert load_result is True

        # 2. 取得・確認
        plugin = self.manager.get_plugin("lifecycle_plugin")
        assert plugin is not None
        assert plugin.state == "initialized"
        assert hasattr(plugin, "container")

        # 3. 一覧確認
        plugins = self.manager.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].name == "lifecycle_plugin"

        # 4. アンロード
        unload_result = self.manager.unload_plugin("lifecycle_plugin")
        assert unload_result is True
        assert plugin.state == "cleaned_up"

        # 5. 削除確認
        assert self.manager.get_plugin("lifecycle_plugin") is None
        assert len(self.manager.list_plugins()) == 0

    def test_統合_複数プラグイン依存関係テスト(self) -> None:
        """統合: 複数プラグインの依存関係テスト"""
        # Given: 依存関係を持つ複数のプラグインファイル
        base_plugin_content = '''
class BasePlugin:
    @property
    def name(self):
        return "base_plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    def initialize(self, container):
        self.initialized = True
    
    def cleanup(self):
        self.cleaned_up = True
'''
        dependent_plugin_content = '''
class DependentPlugin:
    @property
    def name(self):
        return "dependent_plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    def initialize(self, container):
        self.initialized = True
    
    def cleanup(self):
        self.cleaned_up = True
'''
        base_path = self._create_plugin_file(base_plugin_content, "base.py")
        dependent_path = self._create_plugin_file(dependent_plugin_content, "dependent.py")

        base_info = PluginInfo(
            name="base_plugin",
            version="1.0.0",
            description="基盤プラグイン",
            entry_point="BasePlugin",
        )
        dependent_info = PluginInfo(
            name="dependent_plugin",
            version="1.0.0",
            description="依存プラグイン",
            entry_point="DependentPlugin",
            dependencies=["base_plugin"],
        )

        # When & Then: プラグインを順次ロード
        # 1. 依存プラグインを先にロードしようとして失敗
        result = self.manager.load_plugin(dependent_path, dependent_info)
        assert result is False

        # 2. 基盤プラグインをロード
        result = self.manager.load_plugin(base_path, base_info)
        assert result is True

        # 3. 依存プラグインをロード
        result = self.manager.load_plugin(dependent_path, dependent_info)
        assert result is True

        # 4. 両方がロードされていることを確認
        assert len(self.manager.list_plugins()) == 2
        assert self.manager.get_plugin("base_plugin") is not None
        assert self.manager.get_plugin("dependent_plugin") is not None


class TestGlobalPluginManager:
    """グローバルプラグインマネージャーのテスト"""

    def test_グローバルマネージャー取得(self) -> None:
        """グローバルプラグインマネージャーの取得テスト"""
        # When: グローバルマネージャーを取得
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()

        # Then: 同一のインスタンスが返される
        assert manager1 is manager2
        assert isinstance(manager1, PluginManager)


class TestPluginInfo:
    """PluginInfoクラスのテスト"""

    def test_プラグイン情報作成(self) -> None:
        """プラグイン情報の作成テスト"""
        # Given: プラグイン情報パラメータ
        name = "test_plugin"
        version = "1.0.0"
        description = "テストプラグイン"
        entry_point = "TestPlugin"
        dependencies = ["dep1", "dep2"]

        # When: プラグイン情報を作成
        info = PluginInfo(
            name=name,
            version=version,
            description=description,
            entry_point=entry_point,
            dependencies=dependencies,
            enabled=False,
        )

        # Then: 正しく設定される
        assert info.name == name
        assert info.version == version
        assert info.description == description
        assert info.entry_point == entry_point
        assert info.dependencies == dependencies
        assert info.enabled is False

    def test_プラグイン情報デフォルト値(self) -> None:
        """プラグイン情報のデフォルト値テスト"""
        # When: 最小限のパラメータでプラグイン情報を作成
        info = PluginInfo(
            name="test", version="1.0.0", description="テスト", entry_point="Test"
        )

        # Then: デフォルト値が設定される
        assert info.dependencies is None
        assert info.enabled is True