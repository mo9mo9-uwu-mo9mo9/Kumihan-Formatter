"""
設定管理 - 読み込み機能

ファイル読み込み・環境変数処理の責任を担当
Issue #319対応 - config_manager.py から分離
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class ConfigLoader:
    """設定読み込みクラス

    責任: ファイル読み込み・環境変数処理・設定マージ
    """

    def __init__(self, validator) -> None:
        """
        Args:
            validator: ConfigValidator インスタンス
        """
        self.validator = validator

    def load_from_file(self, config_path: str | Path) -> dict[str, Any] | None:
        """ファイルから設定を読み込み"""
        config_path = Path(config_path)

        if not config_path.exists():
            logging.warning(f"Configuration file not found: {config_path}")
            return None

        try:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                if not HAS_YAML:
                    logging.error(
                        "YAML support not available. Install PyYAML to use YAML config files."
                    )
                    return None

                with open(config_path, "r", encoding="utf-8") as file:
                    config_data = yaml.safe_load(file)

            elif config_path.suffix.lower() == ".json":
                with open(config_path, "r", encoding="utf-8") as file:
                    config_data = json.load(file)
            else:
                logging.error(f"Unsupported configuration file format: {config_path}")
                return None

            # 設定の検証
            if self.validator and not self.validator.validate(config_data):
                logging.error(f"Configuration validation failed for: {config_path}")
                return None

            logging.info(f"Loaded configuration from: {config_path}")
            return config_data

        except Exception as e:
            logging.error(f"Error loading configuration from {config_path}: {e}")
            return None

    def load_from_environment(self) -> dict[str, Any]:
        """環境変数から設定を読み込み"""
        env_config: dict[str, Any] = {}
        prefix = "KUMIHAN_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()

                # 特定の設定値を環境変数から読み込み
                if config_key == "theme":
                    env_config["theme"] = value
                elif config_key == "font_family":
                    env_config["font_family"] = value
                elif config_key == "max_file_size_mb":
                    try:
                        # validationキーが存在しない場合は辞書で初期化
                        if "validation" not in env_config:
                            env_config["validation"] = {}
                        validation_config = env_config["validation"]
                        if isinstance(validation_config, dict):
                            validation_config["max_file_size_mb"] = int(value)
                    except ValueError:
                        logging.warning(f"Invalid value for {key}: {value}")
                elif config_key == "strict_mode":
                    # validationキーが存在しない場合は辞書で初期化
                    if "validation" not in env_config:
                        env_config["validation"] = {}
                    validation_config = env_config["validation"]
                    if isinstance(validation_config, dict):
                        validation_config["strict_mode"] = value.lower() in (
                            "true",
                            "1",
                            "yes",
                        )

        if env_config:
            logging.info(f"Loaded environment configuration: {list(env_config.keys())}")

        return env_config

    def merge_configs(
        self, base_config: dict[str, Any], override_config: dict[str, Any]
    ) -> dict[str, Any]:
        """設定をマージ（上書き）"""
        result = self._deep_copy(base_config)
        self._merge_dict(result, override_config)
        return dict(result)

    def _deep_copy(self, obj: Any) -> Any:
        """深いコピーユーティリティ"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}

    def _merge_dict(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """辞書を再帰的にマージ"""
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_dict(target[key], value)
            else:
                target[key] = self._deep_copy(value)
