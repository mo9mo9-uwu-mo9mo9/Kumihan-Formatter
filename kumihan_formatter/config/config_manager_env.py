"""環境変数による設定管理機能

ConfigManagerの環境変数サポート機能を切り出したモジュール。
"""

import os
from typing import Any

from .base_config import BaseConfig
from .extended_config import ExtendedConfig


class ConfigEnvironmentHandler:
    """環境変数による設定管理

    環境変数から設定を読み込み、設定オブジェクトに適用する機能を提供。
    """

    def __init__(self, env_prefix: str = "KUMIHAN_"):
        """環境変数ハンドラーを初期化

        Args:
            env_prefix: 環境変数のプレフィックス
        """
        self.env_prefix = env_prefix

    def load_from_env(self, config: BaseConfig | ExtendedConfig) -> None:
        """環境変数から設定を読み込み

        Args:
            config: 設定オブジェクト
        """
        env_config = self._extract_env_config()

        # 設定をマージ
        if env_config and hasattr(config, "merge_config"):
            config.merge_config(env_config)
        elif env_config:
            for key, value in env_config.items():
                config.set(key, value)

    def _extract_env_config(self) -> dict[str, Any]:
        """環境変数から設定を抽出

        Returns:
            dict[str, Any]: 環境変数から抽出された設定
        """
        env_config = {}

        # CSS関連の環境変数
        css_vars = self._extract_css_vars()
        if css_vars:
            env_config["css"] = css_vars

        # テーマ設定
        theme = os.environ.get(f"{self.env_prefix}THEME")
        if theme:
            env_config["theme"] = theme  # type: ignore

        return env_config

    def _extract_css_vars(self) -> dict[str, str]:
        """CSS関連の環境変数を抽出

        Returns:
            dict[str, str]: CSS変数の辞書
        """
        css_vars = {}
        for key, value in os.environ.items():
            if key.startswith(f"{self.env_prefix}CSS_"):
                css_key = key[len(f"{self.env_prefix}CSS_") :].lower()
                css_vars[css_key] = value
        return css_vars
