"""統合設定管理クラス - Issue #400対応

統合完了: core.config.config_manager.ConfigManagerへの統合
=========================================================

統合理由:
- core.config.config_manager.ConfigManagerがより包括的（551行 vs 208行）
- 環境変数サポート、ホットリロード、グローバル管理を完備
- BaseConfig/ExtendedConfig機能も内包
- スレッドセーフティ対応

互換性維持のためのエイリアス提供
"""

from typing import Any, Union
from pathlib import Path

# 統合完了 - より包括的な実装への統合
from ..core.config.config_manager import ConfigManager as CoreConfigManager

# 後方互換性のためのラッパークラス
class ConfigManager(CoreConfigManager):
    """統合設定管理クラス (互換性ラッパー)
    
    core.config.config_manager.ConfigManagerへの統合完了版
    既存APIとの互換性を完全に維持
    """
    
    def __init__(
        self,
        config_type: str = "extended",
        config_path: Union[str, Path, None] = None,
        env_prefix: str = "KUMIHAN_",
    ):
        # 新しい統合実装の初期化
        super().__init__(config_path=config_path)
        self.config_type = config_type
        self.env_prefix = env_prefix
    
    # テスト互換性エイリアス
    def get_config(self, key: str, default: Any = None) -> Any:
        """設定値を取得（テスト互換用エイリアス）"""
        return self.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """設定値を設定（テスト互換用エイリアス）"""
        self.set(key, value)


def create_config_manager(
    config_type: str = "extended",
    config_path: Union[str, Path, None] = None,
    env_prefix: str = "KUMIHAN_",
) -> ConfigManager:
    """ConfigManager インスタンスを作成"""
    return ConfigManager(
        config_type=config_type, config_path=config_path, env_prefix=env_prefix
    )


def load_config(
    config_path: Union[str, Path, None] = None, config_type: str = "extended"
) -> ConfigManager:
    """設定を読み込む便利関数（既存コードとの互換性用）"""
    return create_config_manager(config_type=config_type, config_path=config_path)


__all__ = ["ConfigManager", "create_config_manager", "load_config"]