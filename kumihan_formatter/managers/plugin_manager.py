"""
PluginManager - 統合プラグイン管理システム

統合対象:
- kumihan_formatter/core/plugins/plugin_manager.py
"""

from typing import Any, Dict, List, Optional
from ..core.plugins.plugin_manager import PluginManager as CorePluginManager
from ..core.utilities.logger import get_logger


class PluginManager:
    """統合プラグイン管理システム"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # コアプラグインマネージャー統合
        self.core_plugin_manager = CorePluginManager()
        
        self.logger.info("PluginManager initialized - unified plugin system")
    
    def load_plugin(self, plugin_name: str, plugin_path: Optional[str] = None) -> bool:
        """プラグイン読み込み"""
        try:
            return self.core_plugin_manager.load_plugin(plugin_name, plugin_path)
        except Exception as e:
            self.logger.error(f"Plugin loading error for {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """プラグイン解除"""
        try:
            return self.core_plugin_manager.unload_plugin(plugin_name)
        except Exception as e:
            self.logger.error(f"Plugin unloading error for {plugin_name}: {e}")
            return False
    
    def get_loaded_plugins(self) -> List[str]:
        """読み込み済みプラグイン一覧"""
        return self.core_plugin_manager.get_loaded_plugins()
    
    def get_available_plugins(self) -> List[str]:
        """利用可能プラグイン一覧"""
        return self.core_plugin_manager.get_available_plugins()
    
    def execute_plugin(self, plugin_name: str, method: str, *args, **kwargs) -> Any:
        """プラグイン実行"""
        try:
            return self.core_plugin_manager.execute_plugin(plugin_name, method, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Plugin execution error for {plugin_name}.{method}: {e}")
            raise
    
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """プラグイン情報取得"""
        return self.core_plugin_manager.get_plugin_info(plugin_name)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """プラグイン読み込み状態確認"""
        return plugin_name in self.get_loaded_plugins()