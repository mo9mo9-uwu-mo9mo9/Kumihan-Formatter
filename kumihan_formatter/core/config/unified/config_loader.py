"""統一設定ローダー

Issue #771対応: YAML/JSON/TOML設定ファイル対応
環境変数・CLI引数・設定ファイルの優先順位制御
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import tomli

    HAS_TOML = True
except ImportError:
    tomli = None
    HAS_TOML = False

from ...error_handling import handle_error_unified
from ...utilities.logger import get_logger
from .config_models import ConfigFormat, KumihanConfig

__all__ = ["ConfigLoader", "ConfigLoadError", "ConfigFormat"]


class ConfigLoadError(Exception):
    """設定読み込みエラー"""

    pass


class ConfigLoader:
    """統一設定ローダー

    設定の読み込み優先順位:
    1. CLI引数 (最優先)
    2. 環境変数
    3. 設定ファイル
    4. デフォルト値
    """

    def __init__(self, logger_name: str = __name__):
        self.logger = get_logger(logger_name)
        self.supported_formats = self._get_supported_formats()

    def _get_supported_formats(self) -> List[ConfigFormat]:
        """サポートされている設定ファイル形式を取得"""
        formats = [ConfigFormat.JSON]  # JSONは標準ライブラリなので常にサポート

        if HAS_YAML:
            formats.extend([ConfigFormat.YAML])
        if HAS_TOML:
            formats.append(ConfigFormat.TOML)

        return formats

    def load_from_file(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """設定ファイルから設定を読み込み

        Args:
            config_path: 設定ファイルパス

        Returns:
            Dict[str, Any]: 設定データ

        Raises:
            ConfigLoadError: 設定ファイル読み込みエラー
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigLoadError(f"設定ファイルが見つかりません: {config_path}")

        if not config_file.is_file():
            raise ConfigLoadError(f"設定パスがファイルではありません: {config_path}")

        # ファイル形式の判定
        file_format = self._detect_format(config_file)

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                if file_format == ConfigFormat.YAML:
                    if not HAS_YAML:
                        raise ConfigLoadError(
                            "YAML設定ファイルの読み込みにはPyYAMLが必要です"
                        )
                    config_data = yaml.safe_load(f)

                elif file_format == ConfigFormat.JSON:
                    config_data = json.load(f)

                elif file_format == ConfigFormat.TOML:
                    if not HAS_TOML:
                        raise ConfigLoadError(
                            "TOML設定ファイルの読み込みにはtomliが必要です"
                        )
                    # TOMLはバイナリモードで読む必要がある
                    f.close()
                    with open(config_file, "rb") as fb:
                        config_data = tomli.load(fb)

                else:
                    raise ConfigLoadError(
                        f"未サポートの設定ファイル形式: {file_format}"
                    )

            if not isinstance(config_data, dict):
                raise ConfigLoadError("設定ファイルは辞書形式である必要があります")

            self.logger.info(
                f"設定ファイル読み込み成功: {config_path} ({file_format.value})"
            )
            return config_data

        except Exception as e:
            # result = handle_error_unified(  # removed - unused variable (F841)
            handle_error_unified(
                e,
                context={
                    "config_path": str(config_path),
                    "file_format": file_format.value,
                    "operation": "config_file_loading",
                },
                operation="load_config_file",
                component_name="ConfigLoader",
            )
            error_msg = f"設定ファイル読み込みエラー: {config_path}"
            raise ConfigLoadError(error_msg) from e

    def _detect_format(self, config_file: Path) -> ConfigFormat:
        """ファイル拡張子から設定ファイル形式を判定

        Args:
            config_file: 設定ファイルパス

        Returns:
            ConfigFormat: 判定された形式

        Raises:
            ConfigLoadError: サポートされていない形式
        """
        suffix = config_file.suffix.lower()

        if suffix in [".yaml", ".yml"]:
            if not HAS_YAML:
                raise ConfigLoadError("YAML形式はサポートされていません (PyYAMLが必要)")
            return ConfigFormat.YAML

        elif suffix == ".json":
            return ConfigFormat.JSON

        elif suffix == ".toml":
            if not HAS_TOML:
                raise ConfigLoadError("TOML形式はサポートされていません (tomliが必要)")
            return ConfigFormat.TOML

        else:
            raise ConfigLoadError(f"サポートされていない設定ファイル形式: {suffix}")

    def load_from_environment(self, prefix: str = "KUMIHAN_") -> Dict[str, Any]:
        """環境変数から設定を読み込み

        Args:
            prefix: 環境変数プレフィックス

        Returns:
            Dict[str, Any]: 環境変数から読み込んだ設定
        """
        config_data: Dict[str, Any] = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # プレフィックスを除去
                config_key = key[len(prefix) :].lower()

                # ネストした設定対応 (例: KUMIHAN_PARALLEL__THRESHOLD_LINES)
                if "__" in config_key:
                    keys = config_key.split("__")
                    self._set_nested_value(
                        config_data, keys, self._convert_env_value(value)
                    )
                else:
                    config_data[config_key] = self._convert_env_value(value)

        if config_data:
            self.logger.debug(f"環境変数から設定読み込み: {len(config_data)}項目")

        return config_data

    def _set_nested_value(
        self, data: Dict[str, Any], keys: List[str], value: Any
    ) -> None:
        """ネストした辞書に値を設定

        Args:
            data: 対象辞書
            keys: キーのリスト
            value: 設定値
        """
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """環境変数値を適切な型に変換

        Args:
            value: 環境変数値

        Returns:
            Union[str, int, float, bool]: 変換された値
        """
        # ブール値の変換
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False

        # 数値の変換
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            # 変換できない場合は文字列のまま返す
            return value

    def find_config_file(
        self,
        search_paths: Optional[List[Union[str, Path]]] = None,
        filename_patterns: Optional[List[str]] = None,
    ) -> Optional[Path]:
        """設定ファイルを検索

        Args:
            search_paths: 検索パスリスト
            filename_patterns: ファイル名パターンリスト

        Returns:
            Optional[Path]: 見つかった設定ファイルパス
        """
        if search_paths is None:
            search_paths = [
                Path.cwd(),  # カレントディレクトリ
                Path.home() / ".kumihan",  # ユーザーホーム/.kumihan
                Path.home() / ".config" / "kumihan",  # XDG Config
                (
                    Path("/etc/kumihan") if sys.platform != "win32" else Path()
                ),  # システム設定
            ]

        if filename_patterns is None:
            filename_patterns = [
                "kumihan.yaml",
                "kumihan.yml",
                "kumihan.json",
                "kumihan.toml",
                ".kumihan.yaml",
                ".kumihan.yml",
                ".kumihan.json",
                ".kumihan.toml",
            ]

        for search_path in search_paths:
            if not isinstance(search_path, Path):
                search_path = Path(search_path)

            if not search_path.exists():
                continue

            for pattern in filename_patterns:
                config_file = search_path / pattern
                if config_file.exists() and config_file.is_file():
                    self.logger.info(f"設定ファイル発見: {config_file}")
                    return config_file

        return None

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """複数の設定を優先順位に従ってマージ

        Args:
            *configs: 設定辞書群 (後の引数ほど優先度が高い)

        Returns:
            Dict[str, Any]: マージされた設定
        """
        merged: Dict[str, Any] = {}

        for config in configs:
            if config:
                merged = self._deep_merge(merged, config)

        return merged

    def _deep_merge(
        self, base: Dict[str, Any], update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """辞書の深いマージ

        Args:
            base: ベース辞書
            update: 更新辞書

        Returns:
            Dict[str, Any]: マージされた辞書
        """
        result = base.copy()

        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def save_config(
        self,
        config: KumihanConfig,
        config_path: Union[str, Path],
        format: Optional[ConfigFormat] = None,
    ) -> None:
        """設定をファイルに保存

        Args:
            config: 保存する設定
            config_path: 保存先パス
            format: 保存形式 (Noneの場合は拡張子から判定)

        Raises:
            ConfigLoadError: 保存エラー
        """
        config_file = Path(config_path)

        if format is None:
            format = self._detect_format(config_file)

        # ディレクトリが存在しない場合は作成
        config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            config_data = config.model_dump(mode="json")

            with open(config_file, "w", encoding="utf-8") as f:
                if format == ConfigFormat.YAML:
                    if not HAS_YAML:
                        raise ConfigLoadError("YAML保存にはPyYAMLが必要です")
                    yaml.dump(
                        config_data, f, default_flow_style=False, allow_unicode=True
                    )

                elif format == ConfigFormat.JSON:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

                elif format == ConfigFormat.TOML:
                    raise ConfigLoadError(
                        "TOML形式での保存は現在サポートされていません"
                    )

                else:
                    raise ConfigLoadError(f"未サポートの保存形式: {format}")

            self.logger.info(f"設定保存完了: {config_path} ({format.value})")

        except Exception as e:
            error_msg = f"設定保存エラー: {config_path}: {e}"
            self.logger.error(error_msg)
            raise ConfigLoadError(error_msg) from e
