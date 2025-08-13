"""基本設定クラス - Issue #400対応

設定管理の統合リファクタリングの一環として作成された基本設定クラス。
シンプルな設定管理機能を提供する。
"""

import json
from pathlib import Path
from typing import Any

import yaml


class BaseConfig:
    """基本設定クラス

    最小限の設定管理機能を提供する。
    環境変数サポートと基本的な設定値検証を含む。
    """

    # デフォルトCSS設定
    DEFAULT_CSS = {
        "max_width": "800px",
        "background_color": "#f9f9f9",
        "container_background": "white",
        "text_color": "#333",
        "line_height": "1.8",
        "font_family": (
            "Hiragino Kaku Gothic ProN, Hiragino Sans, " "Yu Gothic, Meiryo, sans-serif"
        ),
    }

    def __init__(self, config_data: dict[str, Any] | None = None):
        """基本設定を初期化

        Args:
            config_data: 設定データ（指定されない場合はデフォルトを使用）
        """
        self._config = config_data or {}
        self._css_vars = self.DEFAULT_CSS.copy()

        # 設定データからCSS変数を更新
        if "css" in self._config and isinstance(self._config["css"], dict):
            self._css_vars.update(self._config["css"])

    def get_css_variables(self) -> dict[str, str]:
        """CSS変数を取得

        Returns:
            dict[str, str]: CSS変数の辞書
        """
        return self._css_vars.copy()

    def get_theme_name(self) -> str:
        """現在のテーマ名を取得

        Returns:
            str: テーマ名
        """
        return str(self._config.get("theme_name", "デフォルト"))

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            Any: 設定値
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """設定値を設定

        Args:
            key: 設定キー
            value: 設定値
        """
        self._config[key] = value

        # CSS関連の設定値の場合は自動更新
        if key == "css" and isinstance(value, dict):
            self._css_vars.update(value)

    def validate(self) -> bool:
        """設定の妥当性をチェック

        Returns:
            bool: 設定が有効な場合True
        """
        # 基本的な型チェック
        if not isinstance(self._config, dict):
            return False

        # 詳細な設定値検証
        try:
            # 必須設定項目の確認
            required_keys = ["output_dir", "template_dir"]
            for key in required_keys:
                if key not in self._config:
                    return False

            # 出力ディレクトリの妥当性確認
            output_dir = self._config.get("output_dir")
            if output_dir and not isinstance(output_dir, str):
                return False

            # テンプレートディレクトリの妥当性確認
            template_dir = self._config.get("template_dir")
            if template_dir and not isinstance(template_dir, str):
                return False

            # HTML設定の妥当性確認
            if "html" in self._config:
                html_config = self._config["html"]
                if not isinstance(html_config, dict):
                    return False

            # CSS設定の妥当性確認
            if "css" in self._config:
                css_config = self._config["css"]
                if not isinstance(css_config, dict):
                    return False

        except Exception:
            return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """設定を辞書として取得

        Returns:
            dict[str, Any]: 設定辞書
        """
        return self._config.copy()

    @classmethod
    def from_file(cls, config_path: str) -> "BaseConfig":
        """ファイルから設定を読み込み

        Args:
            config_path: 設定ファイルパス

        Returns:
            BaseConfig: 設定オブジェクト

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            ValueError: ファイル形式が不正な場合
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                if config_file.suffix.lower() in [".yaml", ".yml"]:
                    config_data = yaml.safe_load(f)
                elif config_file.suffix.lower() == ".json":
                    config_data = json.load(f)
                else:
                    raise ValueError(f"未対応の設定ファイル形式: {config_file.suffix}")

            if not isinstance(config_data, dict):
                raise ValueError("設定ファイルの形式が正しくありません")

            return cls(config_data)
        except Exception as e:
            raise ValueError(f"設定ファイルの読み込みに失敗しました: {e}")
