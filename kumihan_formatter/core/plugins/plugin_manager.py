"""プラグインマネージャー

Issue #914 Phase 3: 動的プラグインシステム
"""

import importlib
import importlib.util
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from ..patterns.dependency_injection import DIContainer, get_container
from ..patterns.event_bus import ExtendedEventType, get_event_bus, publish_event
from ..utilities.logger import get_logger

logger = get_logger(__name__)


class PluginProtocol(Protocol):
    """プラグインプロトコル"""

    @property
    def name(self) -> str:
        """プラグイン名"""
        ...

    @property
    def version(self) -> str:
        """プラグインバージョン"""
        ...

    def initialize(self, container: DIContainer) -> None:
        """プラグイン初期化"""
        ...

    def cleanup(self) -> None:
        """プラグインクリーンアップ"""
        ...


@dataclass
class PluginInfo:
    """プラグイン情報"""

    name: str
    version: str
    description: str
    entry_point: str
    dependencies: Optional[List[str]] = None
    enabled: bool = True


class PluginManager:
    """プラグインマネージャー"""

    def __init__(self, container: Optional[DIContainer] = None) -> None:
        self.container = container or get_container()
        self.event_bus = get_event_bus()
        self._plugins: Dict[str, PluginProtocol] = {}
        self._plugin_info: Dict[str, PluginInfo] = {}

    def load_plugin(self, plugin_path: str, plugin_info: PluginInfo) -> bool:
        """プラグインロード"""
        try:
            # 依存関係チェック
            if not self._check_dependencies(plugin_info):
                logger.error(f"プラグイン依存関係エラー: {plugin_info.name}")
                return False

            # モジュールロード
            spec = importlib.util.spec_from_file_location(plugin_info.name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"プラグインファイル読み込みエラー: {plugin_path}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # プラグインクラス取得
            plugin_class = getattr(module, plugin_info.entry_point)
            plugin_instance = plugin_class()

            # プロトコル適合性チェック（ダックタイピング）
            if not self._check_plugin_protocol(plugin_instance):
                logger.error(f"プラグインプロトコル非適合: {plugin_info.name}")
                return False

            # 初期化
            plugin_instance.initialize(self.container)

            # 登録
            self._plugins[plugin_info.name] = plugin_instance
            self._plugin_info[plugin_info.name] = plugin_info

            # イベント発行
            publish_event(
                ExtendedEventType.PLUGIN_LOADED,
                "PluginManager",
                {"plugin_name": plugin_info.name, "version": plugin_info.version},
            )

            logger.info(
                f"プラグインロード成功: {plugin_info.name} v{plugin_info.version}"
            )
            return True

        except Exception as e:
            logger.error(f"プラグインロードエラー: {plugin_info.name} - {e}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """プラグインアンロード"""
        if plugin_name not in self._plugins:
            logger.warning(f"プラグイン未登録: {plugin_name}")
            return False

        try:
            plugin = self._plugins[plugin_name]
            plugin.cleanup()

            del self._plugins[plugin_name]
            del self._plugin_info[plugin_name]

            # イベント発行
            publish_event(
                ExtendedEventType.PLUGIN_UNLOADED,
                "PluginManager",
                {"plugin_name": plugin_name},
            )

            logger.info(f"プラグインアンロード成功: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"プラグインアンロードエラー: {plugin_name} - {e}")
            return False

    def get_plugin(self, plugin_name: str) -> Optional[PluginProtocol]:
        """プラグイン取得"""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[PluginInfo]:
        """プラグイン一覧取得"""
        return list(self._plugin_info.values())

    def _check_dependencies(self, plugin_info: PluginInfo) -> bool:
        """依存関係チェック"""
        if not plugin_info.dependencies:
            return True

        for dep in plugin_info.dependencies:
            if dep not in self._plugins:
                logger.error(f"依存プラグイン未ロード: {dep}")
                return False

        return True

    def _check_plugin_protocol(self, plugin_instance: Any) -> bool:
        """プラグインプロトコル適合性チェック（ダックタイピング）"""
        required_attrs = ["name", "version", "initialize", "cleanup"]

        for attr in required_attrs:
            if not hasattr(plugin_instance, attr):
                logger.error(f"プラグインに必要な属性が不足: {attr}")
                return False

        # プロパティとメソッドの型チェック
        try:
            if not isinstance(plugin_instance.name, str):
                return False
            if not isinstance(plugin_instance.version, str):
                return False
            if not callable(plugin_instance.initialize):
                return False
            if not callable(plugin_instance.cleanup):
                return False
        except (AttributeError, TypeError):
            return False

        return True


# グローバルプラグインマネージャー
_global_plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """グローバルプラグインマネージャー取得"""
    return _global_plugin_manager
