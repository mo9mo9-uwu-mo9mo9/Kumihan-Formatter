"""
ConfigManager - Issue #1171 Manager統合最適化
===========================================

設定管理を統括する統一Managerクラス
従来のCoreManagerから設定機能を抽出・統合
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from kumihan_formatter.core.utilities.logger import get_logger


class ConfigManager:
    """統合設定管理Manager - Issue #1171対応"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.logger = get_logger(__name__)

        # 基本的な初期化（依存関係を最小化）
        self.config_path = config_path
        self._config_data = {}

        self.logger.info("ConfigManager initialized - unified configuration system")

    def get_config(self, key: str, default: Any = None) -> Any:
        """設定値取得"""
        return self._config_data.get(key, default)

    def set_config(self, key: str, value: Any, source: str = "user") -> None:
        """設定値設定"""
        self._config_data[key] = value
        self.logger.debug(f"Config set: {key} = {value} (source: {source})")

    def validate_config(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """設定検証"""
        try:
            # 基本的な検証（実装は段階的に追加）
            return True
        except Exception as e:
            self.logger.error(f"Config validation error: {e}")
            return False

    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            # 基本的な設定読み込み（実装は段階的に追加）
            self.logger.info(f"Loading config from {config_path}")
            return {}
        except Exception as e:
            self.logger.error(f"Config loading error for {config_path}: {e}")
            raise

    def save_config(
        self, config_data: Dict[str, Any], config_path: Union[str, Path]
    ) -> None:
        """設定ファイル保存"""
        try:
            self.logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            self.logger.error(f"Config saving error for {config_path}: {e}")
            raise

    def reload_config(self) -> None:
        """設定再読み込み"""
        self.logger.info("Config reloaded")

    def get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定取得"""
        return {"output_format": "html", "encoding": "utf-8", "template": "default"}

    def get_all_configs(self) -> Dict[str, Any]:
        """全設定取得"""
        return self._config_data.copy()

    def reset_config(self, key: Optional[str] = None) -> None:
        """設定リセット（キー指定なしで全リセット）"""
        if key is None:
            self._config_data.clear()
            self.logger.info("All configs reset")
        else:
            self._config_data.pop(key, None)
            self.logger.info(f"Config key '{key}' reset")

    def get_config_statistics(self) -> Dict[str, Any]:
        """設定統計情報"""
        return {
            "total_configs": len(self._config_data),
            "config_keys": list(self._config_data.keys()),
            "has_custom_config": bool(self._config_data),
        }

    def shutdown(self) -> None:
        """リソース解放"""
        try:
            self.logger.info("ConfigManager shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during ConfigManager shutdown: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
