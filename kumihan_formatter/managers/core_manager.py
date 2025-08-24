"""
CoreManager - 統合コア管理システム

統合対象:
- kumihan_formatter/config/config_manager.py
- kumihan_formatter/core/config/config_manager.py  
- kumihan_formatter/core/io/manager.py
- kumihan_formatter/core/template_manager.py
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..core.config.config_manager import ConfigManager as CoreConfigManager
from ..core.io.manager import FileManager
from ..core.template_manager import TemplateManager
from ..core.utilities.logger import get_logger


class CoreManager:
    """統合コア管理システム - 設定・IO・テンプレート管理を統合"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.logger = get_logger(__name__)
        
        # コア機能の統合
        self.config = CoreConfigManager(config_file=config_path)
        self.file_manager = FileManager()
        self.template_manager = TemplateManager()
        
        self.logger.info("CoreManager initialized - unified config, IO, and template management")
    
    # 設定管理メソッド群 (ConfigManager統合)
    def get_config(self, key: str, default: Any = None) -> Any:
        """設定値取得"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any, source: str = "user") -> None:
        """設定値設定"""
        self.config.set(key, value, source)
    
    def validate_config(self) -> bool:
        """設定検証"""
        return self.config.validate()
    
    def reload_config(self) -> None:
        """設定再読み込み"""
        self.config.reload()
    
    # IO管理メソッド群 (FileManager統合)
    def read_file(self, file_path: Union[str, Path]) -> str:
        """ファイル読み込み"""
        return self.file_manager.read_file(file_path)
    
    def write_file(self, file_path: Union[str, Path], content: str) -> None:
        """ファイル書き込み"""
        self.file_manager.write_file(file_path, content)
    
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """ファイル検証"""
        return self.file_manager.validate_file(file_path)
    
    # テンプレート管理メソッド群 (TemplateManager統合)
    def load_template(self, template_name: str) -> Any:
        """テンプレート読み込み"""
        return self.template_manager.load_template(template_name)
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """テンプレート描画"""
        return self.template_manager.render_template(template_name, context)
    
    def get_available_templates(self) -> list:
        """利用可能テンプレート一覧"""
        return self.template_manager.get_available_templates()
    
    # 統合管理メソッド
    def shutdown(self) -> None:
        """リソース解放"""
        try:
            self.config.shutdown()
            self.file_manager.close()
            self.logger.info("CoreManager shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during CoreManager shutdown: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()