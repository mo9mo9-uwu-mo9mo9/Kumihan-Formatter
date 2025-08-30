"""
PluginManager - プラグイン機能統合管理クラス
拡張機能・カスタムパーサー・フィルターの統合管理
"""

import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Union, Callable, Type
from pathlib import Path
from dataclasses import dataclass

from kumihan_formatter.core.ast_nodes.node import Node


@dataclass
class PluginInfo:
    """プラグイン情報"""

    name: str
    version: str
    description: str
    plugin_type: str
    enabled: bool
    module_path: str


class PluginManager:
    """プラグイン機能統合管理クラス - 拡張機能・カスタマイゼーションAPI"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        PluginManager初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # プラグイン管理設定
        self.plugin_dir = Path(self.config.get("plugin_dir", "plugins"))
        self.enable_plugins = self.config.get("enable_plugins", True)

        # 登録されたプラグイン
        self._registered_plugins: Dict[str, PluginInfo] = {}
        self._parser_plugins: Dict[str, Callable] = {}
        self._filter_plugins: Dict[str, Callable] = {}
        self._renderer_plugins: Dict[str, Callable] = {}

    # ========== プラグイン登録機能 ==========

    def register_parser_plugin(
        self, name: str, parser_func: Callable, description: str = ""
    ) -> bool:
        """
        カスタムパーサープラグインの登録

        Args:
            name: パーサー名
            parser_func: パーサー関数
            description: 説明

        Returns:
            登録成功時True
        """
        try:
            if not self.enable_plugins:
                self.logger.warning("プラグイン機能が無効化されています")
                return False

            # 関数シグネチャの基本検証
            sig = inspect.signature(parser_func)
            if len(sig.parameters) == 0:
                self.logger.error(f"パーサー関数が無効です: {name}")
                return False

            self._parser_plugins[name] = parser_func

            # プラグイン情報登録
            plugin_info = PluginInfo(
                name=name,
                version="1.0.0",
                description=description or f"Custom parser: {name}",
                plugin_type="parser",
                enabled=True,
                module_path=parser_func.__module__,
            )
            self._registered_plugins[name] = plugin_info

            self.logger.info(f"パーサープラグイン登録完了: {name}")
            return True

        except Exception as e:
            self.logger.error(f"パーサープラグイン登録中にエラー: {name}, {e}")
            return False

    def register_filter_plugin(
        self, name: str, filter_func: Callable, description: str = ""
    ) -> bool:
        """
        コンテンツフィルタープラグインの登録

        Args:
            name: フィルター名
            filter_func: フィルター関数
            description: 説明

        Returns:
            登録成功時True
        """
        try:
            if not self.enable_plugins:
                return False

            self._filter_plugins[name] = filter_func

            # プラグイン情報登録
            plugin_info = PluginInfo(
                name=name,
                version="1.0.0",
                description=description or f"Custom filter: {name}",
                plugin_type="filter",
                enabled=True,
                module_path=filter_func.__module__,
            )
            self._registered_plugins[name] = plugin_info

            self.logger.info(f"フィルタープラグイン登録完了: {name}")
            return True

        except Exception as e:
            self.logger.error(f"フィルタープラグイン登録中にエラー: {name}, {e}")
            return False

    def register_renderer_plugin(
        self, name: str, renderer_func: Callable, description: str = ""
    ) -> bool:
        """
        カスタムレンダラープラグインの登録

        Args:
            name: レンダラー名
            renderer_func: レンダラー関数
            description: 説明

        Returns:
            登録成功時True
        """
        try:
            if not self.enable_plugins:
                return False

            self._renderer_plugins[name] = renderer_func

            # プラグイン情報登録
            plugin_info = PluginInfo(
                name=name,
                version="1.0.0",
                description=description or f"Custom renderer: {name}",
                plugin_type="renderer",
                enabled=True,
                module_path=renderer_func.__module__,
            )
            self._registered_plugins[name] = plugin_info

            self.logger.info(f"レンダラープラグイン登録完了: {name}")
            return True

        except Exception as e:
            self.logger.error(f"レンダラープラグイン登録中にエラー: {name}, {e}")
            return False

    # ========== プラグイン実行機能 ==========

    def execute_parser_plugin(
        self, plugin_name: str, content: Union[str, List[str]]
    ) -> Optional[Node]:
        """
        パーサープラグインの実行

        Args:
            plugin_name: プラグイン名
            content: 解析対象コンテンツ

        Returns:
            解析結果ノード、エラー時はNone
        """
        try:
            if plugin_name not in self._parser_plugins:
                self.logger.error(f"未登録のパーサープラグイン: {plugin_name}")
                return None

            parser_func = self._parser_plugins[plugin_name]
            return parser_func(content)

        except Exception as e:
            self.logger.error(f"パーサープラグイン実行中にエラー: {plugin_name}, {e}")
            return None

    def execute_filter_plugin(
        self, plugin_name: str, content: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        フィルタープラグインの実行

        Args:
            plugin_name: プラグイン名
            content: フィルター対象コンテンツ
            context: フィルターコンテキスト

        Returns:
            フィルター適用結果、エラー時はNone
        """
        try:
            if plugin_name not in self._filter_plugins:
                self.logger.error(f"未登録のフィルタープラグイン: {plugin_name}")
                return None

            filter_func = self._filter_plugins[plugin_name]

            # 関数シグネチャに応じて実行
            sig = inspect.signature(filter_func)
            if len(sig.parameters) == 1:
                return filter_func(content)
            else:
                return filter_func(content, context or {})

        except Exception as e:
            self.logger.error(f"フィルタープラグイン実行中にエラー: {plugin_name}, {e}")
            return None

    # ========== プラグイン管理 ==========

    def load_plugins_from_directory(
        self, plugin_dir: Optional[Path] = None
    ) -> Dict[str, bool]:
        """
        ディレクトリからプラグインを自動読み込み

        Args:
            plugin_dir: プラグインディレクトリ

        Returns:
            読み込み結果（プラグイン名: 成功フラグ）
        """
        try:
            if not self.enable_plugins:
                return {}

            plugin_path = plugin_dir or self.plugin_dir
            if not plugin_path.exists():
                self.logger.info(f"プラグインディレクトリが存在しません: {plugin_path}")
                return {}

            load_results = {}

            for plugin_file in plugin_path.glob("*.py"):
                if plugin_file.name.startswith("__"):
                    continue

                plugin_name = plugin_file.stem
                try:
                    # プラグインモジュール読み込み
                    spec = importlib.util.spec_from_file_location(
                        plugin_name, plugin_file
                    )
                    if spec is None or spec.loader is None:
                        self.logger.warning(
                            f"プラグイン {plugin_name} の読み込みに失敗: spec/loader is None"
                        )
                        load_results[plugin_name] = False
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # プラグイン登録関数の実行
                    if hasattr(module, "register_plugin"):
                        success = module.register_plugin(self)
                        load_results[plugin_name] = success

                        if success:
                            self.logger.info(f"プラグイン読み込み成功: {plugin_name}")
                        else:
                            self.logger.warning(f"プラグイン登録失敗: {plugin_name}")
                    else:
                        self.logger.warning(
                            f"register_plugin関数が見つかりません: {plugin_name}"
                        )
                        load_results[plugin_name] = False

                except Exception as e:
                    self.logger.error(f"プラグイン読み込みエラー {plugin_name}: {e}")
                    load_results[plugin_name] = False

            return load_results

        except Exception as e:
            self.logger.error(f"プラグインディレクトリ読み込み中にエラー: {e}")
            return {}

    def get_registered_plugins(self) -> List[PluginInfo]:
        """登録済みプラグイン一覧を取得"""
        return list(self._registered_plugins.values())

    def get_available_parsers(self) -> List[str]:
        """利用可能なカスタムパーサー一覧を取得"""
        return list(self._parser_plugins.keys())

    def get_available_filters(self) -> List[str]:
        """利用可能なフィルター一覧を取得"""
        return list(self._filter_plugins.keys())

    def enable_plugin(self, plugin_name: str) -> bool:
        """プラグインを有効化"""
        if plugin_name in self._registered_plugins:
            self._registered_plugins[plugin_name].enabled = True
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """プラグインを無効化"""
        if plugin_name in self._registered_plugins:
            self._registered_plugins[plugin_name].enabled = False
            return True
        return False

    def get_plugin_statistics(self) -> Dict[str, Any]:
        """プラグイン統計情報を取得"""
        enabled_count = sum(1 for p in self._registered_plugins.values() if p.enabled)

        return {
            "total_plugins": len(self._registered_plugins),
            "enabled_plugins": enabled_count,
            "parser_plugins": len(self._parser_plugins),
            "filter_plugins": len(self._filter_plugins),
            "renderer_plugins": len(self._renderer_plugins),
            "plugins_enabled": self.enable_plugins,
        }
