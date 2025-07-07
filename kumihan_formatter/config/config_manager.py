"""統合設定管理クラス - Issue #400対応

設定管理の統合リファクタリングの一環として作成された統合インターフェース。
BaseConfig、ExtendedConfig、既存の設定クラスを統一的に管理する。
"""

import os
from pathlib import Path
from typing import Any, Optional, Type, Union

from .base_config import BaseConfig
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
        self._config: BaseConfig | ExtendedConfig = self._create_config(config_path)

        # 環境変数から設定を読み込み
        self._load_from_env()

    def _create_config(self, config_path: str | None) -> BaseConfig | ExtendedConfig:
        """設定オブジェクトを作成

        Args:
            config_path: 設定ファイルパス

        Returns:
            BaseConfig | ExtendedConfig: 設定オブジェクト
        """
        config_class = ExtendedConfig if self.config_type == "extended" else BaseConfig

        if config_path and Path(config_path).exists():
            try:
                return config_class.from_file(config_path)
            except (FileNotFoundError, ValueError):
                # ファイル読み込みに失敗した場合はデフォルト設定を使用
                pass

        return config_class()

    def _load_from_env(self) -> None:
        """環境変数から設定を読み込み"""
        env_config = {}

        # CSS関連の環境変数
        css_vars = {}
        for key, value in os.environ.items():
            if key.startswith(f"{self.env_prefix}CSS_"):
                css_key = key[len(f"{self.env_prefix}CSS_") :].lower()
                css_vars[css_key] = value

        if css_vars:
            env_config["css"] = css_vars

        # テーマ設定
        theme = os.environ.get(f"{self.env_prefix}THEME")
        if theme:
            env_config["theme"] = theme  # type: ignore

        # 設定をマージ
        if env_config and hasattr(self._config, "merge_config"):
            self._config.merge_config(env_config)
        elif env_config:
            for key, value in env_config.items():  # type: ignore
                self._config.set(key, value)

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

    # ExtendedConfigインターフェースの委譲（利用可能な場合）
    def get_markers(self) -> dict[str, dict[str, Any]]:
        """マーカー定義を取得（ExtendedConfigのみ）"""
        if hasattr(self._config, "get_markers"):
            return self._config.get_markers()  # type: ignore
        return {}

    def add_marker(self, name: str, definition: dict[str, Any]) -> None:
        """マーカーを追加（ExtendedConfigのみ）"""
        if hasattr(self._config, "add_marker"):
            self._config.add_marker(name, definition)

    def remove_marker(self, name: str) -> bool:
        """マーカーを削除（ExtendedConfigのみ）"""
        if hasattr(self._config, "remove_marker"):
            return self._config.remove_marker(name)  # type: ignore
        return False

    def get_themes(self) -> dict[str, dict[str, Any]]:
        """テーマ定義を取得（ExtendedConfigのみ）"""
        if hasattr(self._config, "get_themes"):
            return self._config.get_themes()  # type: ignore
        return {}

    def add_theme(self, theme_id: str, theme_data: dict[str, Any]) -> None:
        """テーマを追加（ExtendedConfigのみ）"""
        if hasattr(self._config, "add_theme"):
            self._config.add_theme(theme_id, theme_data)

    def set_theme(self, theme_id: str) -> bool:
        """テーマを設定（ExtendedConfigのみ）"""
        if hasattr(self._config, "set_theme"):
            return self._config.set_theme(theme_id)  # type: ignore
        return False

    def get_current_theme(self) -> str:
        """現在のテーマIDを取得（ExtendedConfigのみ）"""
        if hasattr(self._config, "get_current_theme"):
            return self._config.get_current_theme()  # type: ignore
        return "default"

    # 互換性メソッド
    def load_config(self, config_path: str) -> bool:
        """設定ファイルを読み込み（互換性用）

        Args:
            config_path: 設定ファイルパス

        Returns:
            bool: 読み込みに成功した場合True
        """
        try:
            new_config = self._create_config(config_path)
            if hasattr(new_config, "merge_config") and hasattr(self._config, "to_dict"):
                # 既存設定をマージ
                existing_config = self._config.to_dict()
                new_config.merge_config(existing_config)
            self._config = new_config
            self._load_from_env()  # 環境変数を再適用
            return True
        except Exception:
            return False

    def merge_config(self, other_config: dict[str, Any]) -> None:
        """他の設定をマージ

        Args:
            other_config: マージする設定辞書
        """
        if hasattr(self._config, "merge_config"):
            self._config.merge_config(other_config)
        else:
            # BaseConfigの場合は個別に設定
            for key, value in other_config.items():
                self._config.set(key, value)

    @property
    def config(self) -> BaseConfig | ExtendedConfig:
        """内部設定オブジェクトを取得（下位互換性用）"""
        return self._config


# 便利関数
def create_config_manager(
    config_type: str = "extended", config_path: str | None = None
) -> ConfigManager:
    """設定管理を作成

    Args:
        config_type: 設定タイプ ("base" または "extended")
        config_path: 設定ファイルパス

    Returns:
        ConfigManager: 設定管理オブジェクト
    """
    return ConfigManager(config_type=config_type, config_path=config_path)


def load_config(config_path: str | None = None) -> ConfigManager:
    """設定を読み込む便利関数（既存コードとの互換性用）

    Args:
        config_path: 設定ファイルパス

    Returns:
        ConfigManager: 設定管理オブジェクト
    """
    return create_config_manager(config_type="extended", config_path=config_path)
