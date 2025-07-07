"""
設定管理 - メイン管理クラス

拡張設定管理のメイン制御とインターフェース
Issue #319対応 - config_manager.py から分離
"""

import logging
from pathlib import Path
from typing import Any, Dict, Union

from ..utilities.logger import get_logger
from .config_loader import ConfigLoader
from .config_types import ConfigLevel
from .config_validator import ConfigValidator


class EnhancedConfig:
    """
    拡張設定管理（複数設定ソース統合・環境別設定）

    設計ドキュメント:
    - 仕様: /SPEC.md#出力形式オプション
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 設定詳細: /docs/configuration.md

    関連クラス:
    - ConfigValidator: 設定値の検証
    - ConfigLoader: ファイル・環境変数読み込み
    - Parser: 設定を使用する主要クラス
    - Renderer: 設定に基づくHTML生成

    責務:
    - 設定ファイルの読み込み・マージ
    - 環境変数による設定上書き
    - デフォルト値の提供
    - 設定値へのアクセスインターフェース
    """

    # デフォルト設定
    DEFAULT_CONFIG = {
        "markers": {
            "太字": {"tag": "strong"},
            "イタリック": {"tag": "em"},
            "枠線": {"tag": "div", "class": "box"},
            "ハイライト": {"tag": "div", "class": "highlight"},
            "見出し1": {"tag": "h1"},
            "見出し2": {"tag": "h2"},
            "見出し3": {"tag": "h3"},
            "見出し4": {"tag": "h4"},
            "見出し5": {"tag": "h5"},
            "折りたたみ": {"tag": "details", "summary": "詳細を表示"},
            "ネタバレ": {"tag": "details", "summary": "ネタバレを表示"},
        },
        "theme": "default",
        "font_family": "Hiragino Kaku Gothic ProN, Hiragino Sans, Yu Gothic, Meiryo, sans-serif",
        "css": {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8",
        },
        "themes": {
            "default": {
                "name": "デフォルト",
                "css": {
                    "background_color": "#f9f9f9",
                    "container_background": "white",
                    "text_color": "#333",
                },
            },
            "dark": {
                "name": "ダーク",
                "css": {
                    "background_color": "#1a1a1a",
                    "container_background": "#2d2d2d",
                    "text_color": "#e0e0e0",
                },
            },
            "sepia": {
                "name": "セピア",
                "css": {
                    "background_color": "#f4f1ea",
                    "container_background": "#fdf6e3",
                    "text_color": "#5c4b37",
                },
            },
            "high-contrast": {
                "name": "ハイコントラスト",
                "css": {
                    "background_color": "#000000",
                    "container_background": "#ffffff",
                    "text_color": "#000000",
                },
            },
        },
        "performance": {
            "max_recursion_depth": 50,
            "max_nodes": 10000,
            "cache_templates": True,
        },
        "validation": {
            "strict_mode": False,
            "warn_unknown_keywords": True,
            "max_file_size_mb": 10,
        },
    }

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.config = {}  # type: ignore
        self.config_sources: Dict[str, str] = {}  # 各設定値の出典を追跡
        self.validator = ConfigValidator()
        self.loader = ConfigLoader(self.validator)
        self._load_defaults()
        self.logger.debug("EnhancedConfig initialized with default settings")

    def _load_defaults(self) -> None:
        """デフォルト設定を読み込み"""
        self.config = self.loader._deep_copy(self.DEFAULT_CONFIG)
        self._mark_source("default", self.config)
        self.logger.debug("Loaded default configuration")

    def _mark_source(self, source: str, obj: Any, path: str = ""):  # type: ignore
        """設定ソースをマーク（追跡用）"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                self.config_sources[current_path] = source
                self._mark_source(source, value, current_path)

    def load_from_file(
        self, config_path: Union[str, Path], level: ConfigLevel = ConfigLevel.USER
    ) -> bool:
        """ファイルから設定を読み込み"""
        self.logger.info(f"Loading configuration from file: {config_path}")
        user_config = self.loader.load_from_file(config_path)
        if user_config:
            self._merge_config(user_config, str(config_path))
            self.logger.info(f"Successfully loaded configuration from {config_path}")
            return True
        self.logger.warning(f"Failed to load configuration from {config_path}")
        return False

    def load_from_environment(self) -> bool:
        """環境変数から設定を読み込み"""
        self.logger.debug("Loading configuration from environment variables")
        env_config = self.loader.load_from_environment()
        if env_config:
            self._merge_config(env_config, "environment")
            self.logger.info("Loaded configuration from environment variables")
            return True
        self.logger.debug("No configuration found in environment variables")
        return False

    def _merge_config(self, user_config: Dict[str, Any], source: str):  # type: ignore
        """設定をマージ"""
        self.logger.debug(f"Merging configuration from source: {source}")
        self.config = self.loader.merge_configs(self.config, user_config)
        self._mark_source(source, user_config)

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        keys = key.split(".")
        current = self.config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                self.logger.debug(
                    f"Configuration key not found: {key}, using default: {default}"
                )
                return default

        return current

    def set(self, key: str, value: Any, source: str = "runtime"):  # type: ignore
        """設定値を設定"""
        keys = key.split(".")
        current = self.config

        # ネストした辞書を作成
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        self.config_sources[key] = source
        self.logger.debug(f"Set configuration {key} = {value} from {source}")

    def get_markers(self) -> Dict[str, Dict[str, str]]:
        """マーカー設定を取得"""
        return dict(self.get("markers", {}))

    def get_theme(self) -> str:
        """テーマ名を取得"""
        return str(self.get("theme", "default"))

    def get_css_config(self) -> Dict[str, str]:
        """CSS設定を取得"""
        return dict(self.get("css", {}))

    def get_performance_config(self) -> Dict[str, Any]:
        """パフォーマンス設定を取得"""
        return dict(self.get("performance", {}))

    def get_validation_config(self) -> Dict[str, Any]:
        """バリデーション設定を取得"""
        return dict(self.get("validation", {}))

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書として取得"""
        return self.loader._deep_copy(self.config)  # type: ignore

    def get_config_source(self, key: str) -> str:
        """設定値のソースを取得"""
        return self.config_sources.get(key, "unknown")
