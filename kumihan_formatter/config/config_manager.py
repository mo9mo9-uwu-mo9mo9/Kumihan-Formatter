"""統合設定管理クラス - Issue #400対応

設定管理の統合リファクタリングの一環として作成された統合インターフェース。
BaseConfig、ExtendedConfig、既存の設定クラスを統一的に管理する。
"""

from typing import Any

from .base_config import BaseConfig
from .config_manager_env import ConfigEnvironmentHandler
from .config_manager_utils import (
    create_config_instance,
    load_config_file,
    merge_config_data,
)
from .extended_config import ExtendedConfig


class ConfigManager:
    """統合設定管理クラス

    異なる設定クラスを統一的に管理し、
    環境変数サポート、設定の階層化、互換性維持を提供する。
    """

    def __init__(
        self,
        config_type: str = "extended",
        config_path: str | None = None,
        env_prefix: str = "KUMIHAN_",
    ):
        """統合設定管理を初期化

        Args:
            config_type: 設定タイプ ("base" または "extended")
            config_path: 設定ファイルパス
            env_prefix: 環境変数のプレフィックス
        """
        self.config_type = config_type
        self.env_prefix = env_prefix
        self._config: BaseConfig | ExtendedConfig = create_config_instance(
            config_type, config_path
        )
        self._env_handler = ConfigEnvironmentHandler(env_prefix)

        # 環境変数から設定を読み込み
        self._env_handler.load_from_env(self._config)

    # BaseConfigインターフェースの委譲
    def get_css_variables(self) -> dict[str, str]:
        """CSS変数を取得"""
        return self._config.get_css_variables()

    def get_theme_name(self) -> str:
        """現在のテーマ名を取得"""
        return self._config.get_theme_name()

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """設定値を設定"""
        self._config.set(key, value)

    def validate(self) -> bool:
        """設定の妥当性をチェック"""
        return self._config.validate()

    def to_dict(self) -> dict[str, Any]:
        """設定を辞書として取得"""
        return self._config.to_dict()

    def get_markers(self) -> dict[str, dict[str, Any]]:
        """マーカー定義を取得（ExtendedConfigのみ）"""
        if hasattr(self._config, "get_markers"):
            return self._config.get_markers()  # type: ignore

    def add_marker(self, name: str, definition: dict[str, Any]) -> None:
        """マーカーを追加（ExtendedConfigのみ）"""
        if hasattr(self._config, "add_marker"):
            self._config.add_marker(name, definition)

    def remove_marker(self, name: str) -> bool:
        """マーカーを削除（ExtendedConfigのみ）"""
        if hasattr(self._config, "remove_marker"):
            return self._config.remove_marker(name)  # type: ignore

    def get_themes(self) -> dict[str, dict[str, Any]]:
        """テーマ定義を取得（ExtendedConfigのみ）"""
        if hasattr(self._config, "get_themes"):
            return self._config.get_themes()  # type: ignore

    def add_theme(self, theme_id: str, theme_data: dict[str, Any]) -> None:
        """テーマを追加（ExtendedConfigのみ）"""
        if hasattr(self._config, "add_theme"):
            self._config.add_theme(theme_id, theme_data)

    def set_theme(self, theme_id: str) -> bool:
        """テーマを設定（ExtendedConfigのみ）"""
        if hasattr(self._config, "set_theme"):
            return self._config.set_theme(theme_id)  # type: ignore

    def get_current_theme(self) -> str:
        """現在のテーマIDを取得（ExtendedConfigのみ）"""
        if hasattr(self._config, "get_current_theme"):
            return self._config.get_current_theme()  # type: ignore

    def load_config(self, config_path: str) -> bool:
        """設定ファイルを読み込み（互換性用）

        Args:
            config_path: 設定ファイルパス

        Returns:
            bool: 読み込みに成功した場合True
        """
        try:
            self._config = load_config_file(self.config_type, config_path, self._config)
            self._env_handler.load_from_env(self._config)  # 環境変数を再適用
            return True
        except Exception as e:
            self.logger.error(f"Failed to load config file: {e}")
            return False

    def merge_config(self, other_config: dict[str, Any]) -> None:
        """他の設定をマージ

        Args:
            other_config: マージする設定辞書
        """
        merge_config_data(self._config, other_config)

    @property
    def config(self) -> BaseConfig | ExtendedConfig:
        """内部設定オブジェクトを取得（下位互換性用）"""
        return self._config


def create_config_manager(
    config_type: str = "extended",
    config_path: str | None = None,
    env_prefix: str = "KUMIHAN_",
) -> ConfigManager:
    """ConfigManager インスタンスを作成

    Args:
        config_type: 設定タイプ ("base" または "extended")
        config_path: 設定ファイルパス
        env_prefix: 環境変数のプレフィックス

    Returns:
        ConfigManager: 設定管理インスタンス
    """
    return ConfigManager(
        config_type=config_type, config_path=config_path, env_prefix=env_prefix
    )


def load_config(config_path: str | None = None) -> ConfigManager:
    """設定を読み込む便利関数（既存コードとの互換性用）

    Args:
        config_path: 設定ファイルパス

    Returns:
        ConfigManager: 設定管理オブジェクト
    """
    return create_config_manager(config_path=config_path)
