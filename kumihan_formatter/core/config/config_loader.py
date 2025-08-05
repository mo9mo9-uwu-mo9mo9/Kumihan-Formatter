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

    def __init__(self, validator) -> None:  # type: ignore
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
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    if not HAS_YAML:
                        logging.error(
                            "YAML support not available. Install PyYAML to use YAML config files."
                        )
                        return None
                    user_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == ".json":
                    user_config = json.load(f)
                else:
                    logging.error(f"Unsupported config format: {config_path.suffix}")
                    return None

            if not isinstance(user_config, dict):
                logging.error("Configuration file must contain a dictionary")
                return None

            # 読み込み前の検証
            validation_result = self.validator.validate(user_config)
            if not validation_result.is_valid:
                logging.error(
                    f"Configuration validation failed: {validation_result.errors}"
                )
                return None

            # 警告をログ出力
            for warning in validation_result.warnings:
                logging.warning(f"Configuration warning: {warning}")

            logging.info(f"Loaded configuration from: {config_path}")
            return user_config

        except Exception as e:
            logging.error(f"Failed to load configuration from {config_path}: {e}")
            return None

    def load_from_environment(self) -> dict[str, Any]:
        """環境変数から設定を読み込み"""
        env_config = {}
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
                        env_config.setdefault("validation", {})["max_file_size_mb"] = (  # type: ignore
                            int(value)
                        )
                    except ValueError:
                        logging.warning(f"Invalid value for {key}: {value}")
                elif config_key == "strict_mode":
                    env_config.setdefault("validation", {})[  # type: ignore # type: ignore
                        "strict_mode"
                    ] = value.lower() in (
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
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

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
