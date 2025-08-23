"""設定管理のユーティリティ関数

ConfigManagerで使用される便利関数とファクトリー関数を提供。
"""

from pathlib import Path
from typing import Any

from .base_config import BaseConfig
from .extended_config import ExtendedConfig


def create_config_instance(
    config_type: str, config_path: str | None
) -> BaseConfig | ExtendedConfig:
    """設定オブジェクトを作成

    Args:
        config_type: 設定タイプ ("base" または "extended")
        config_path: 設定ファイルパス

    Returns:
        BaseConfig | ExtendedConfig: 設定オブジェクト

    Raises:
        FileNotFoundError: 指定されたファイルが存在しない場合
        ValueError: 無効な設定タイプが指定された場合
    """
    # 無効な設定タイプのチェック
    valid_types = {"base", "extended"}
    if config_type not in valid_types:
        raise ValueError(f"無効な設定タイプ: {config_type}. 有効な値: {valid_types}")

    config_class = ExtendedConfig if config_type == "extended" else BaseConfig

    if config_path:
        if not Path(config_path).exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

        try:
            return config_class.from_file(config_path)
        except Exception as e:
            # ファイル読み込みエラーは再発生
            raise e

    return config_class()


def merge_config_data(
    config: BaseConfig | ExtendedConfig, other_config: dict[str, Any]
) -> None:
    """他の設定をマージ

    Args:
        config: マージ先の設定オブジェクト
        other_config: マージする設定辞書
    """
    if hasattr(config, "merge_config"):
        config.merge_config(other_config)
    else:
        # BaseConfigの場合は個別に設定
        for key, value in other_config.items():
            config.set(key, value)


def load_config_file(
    config_type: str, config_path: str, existing_config: BaseConfig | ExtendedConfig
) -> BaseConfig | ExtendedConfig:
    """設定ファイルを読み込み

    Args:
        config_type: 設定タイプ
        config_path: 設定ファイルパス
        existing_config: 既存の設定オブジェクト

    Returns:
        BaseConfig | ExtendedConfig: 新しい設定オブジェクト

    Raises:
        Exception: ファイル読み込みに失敗した場合
    """
    new_config = create_config_instance(config_type, config_path)

    if hasattr(new_config, "merge_config") and hasattr(existing_config, "to_dict"):
        # 既存設定をマージ
        existing_config_dict = existing_config.to_dict()
        new_config.merge_config(existing_config_dict)

    return new_config
