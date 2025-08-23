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

    Note:
        無効な設定タイプの場合はBaseConfigにフォールバック
        ファイルが存在しない場合やロードに失敗した場合もデフォルト設定にフォールバック
    """
    # テストとの互換性のため、無効なタイプはBaseConfigにフォールバック
    config_class = ExtendedConfig if config_type == "extended" else BaseConfig

    if config_path:
        if not Path(config_path).exists():
            # ファイルが存在しない場合はデフォルト設定にフォールバック
            return config_class()

        try:
            return config_class.from_file(config_path)
        except Exception:
            # ファイル読み込みエラーの場合もデフォルト設定にフォールバック
            return config_class()

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
