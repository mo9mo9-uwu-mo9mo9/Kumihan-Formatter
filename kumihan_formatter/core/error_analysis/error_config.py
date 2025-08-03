"""
Phase3: エラー処理設定システム
Issue #700対応 - 設定可能なエラー処理レベル

柔軟なエラー処理設定とカスタマイズ機能
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utilities.logger import get_logger

# Optional dependencies for config file support
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

try:
    import toml

    HAS_TOML = True
except ImportError:
    HAS_TOML = False
    toml = None


class ErrorHandlingLevel(Enum):
    """エラー処理レベル定義"""

    STRICT = "strict"  # 最初のエラーで停止
    NORMAL = "normal"  # デフォルト動作（エラーログ出力、処理継続）
    LENIENT = "lenient"  # 警告レベルで表示、処理継続
    IGNORE = "ignore"  # エラーを無視


class ErrorHandlingStrategy(Enum):
    """エラー処理戦略"""

    STOP = "stop"  # 処理停止
    CONTINUE = "continue"  # 処理継続
    SKIP = "skip"  # 該当箇所をスキップ
    RECOVER = "recover"  # 自動回復を試行
    CUSTOM = "custom"  # カスタムハンドラー使用


@dataclass
class ErrorTypeConfig:
    """エラータイプ別設定"""

    error_type: str
    handling_level: ErrorHandlingLevel = ErrorHandlingLevel.NORMAL
    strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.CONTINUE
    max_occurrences: int = -1  # -1: 無制限
    custom_handler: Optional[str] = None  # カスタムハンドラー名


@dataclass
class ErrorHandlingConfig:
    """エラー処理設定"""

    # グローバル設定
    default_level: ErrorHandlingLevel = ErrorHandlingLevel.NORMAL
    graceful_errors: bool = False
    continue_on_error: bool = False
    show_suggestions: bool = True
    show_statistics: bool = True

    # エラー表示設定
    error_display_limit: int = 100  # 表示するエラーの最大数
    show_context_lines: int = 3  # エラー箇所の前後行数
    highlight_errors: bool = True  # エラーハイライト表示

    # 統計設定
    save_error_report: bool = False
    error_report_path: Optional[Path] = None
    include_source_in_report: bool = False

    # エラータイプ別設定
    error_type_configs: Dict[str, ErrorTypeConfig] = field(default_factory=dict)

    # カスタムハンドラー
    custom_handlers: Dict[str, Any] = field(default_factory=dict)


class ErrorConfigManager:
    """
    エラー処理設定管理システム

    優先順位:
    1. CLIオプション
    2. 環境変数
    3. 設定ファイル（kumihan.toml/kumihan.yaml）
    4. デフォルト設定
    """

    # 環境変数プレフィックス
    ENV_PREFIX = "KUMIHAN_ERROR_"

    # サポートする設定ファイル名
    CONFIG_FILES = [
        "kumihan.toml",
        "kumihan.yaml",
        "kumihan.yml",
        ".kumihan.toml",
        ".kumihan.yaml",
    ]

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = get_logger(__name__)
        self.config_dir = config_dir or Path.cwd()
        self.config = ErrorHandlingConfig()

        # 設定を読み込み
        self._load_configuration()

    def _load_configuration(self) -> None:
        """設定を優先順位に従って読み込み"""
        # 1. デフォルト設定（既に初期化済み）

        # 2. 設定ファイルから読み込み
        config_file = self._find_config_file()
        if config_file:
            self._load_from_file(config_file)

        # 3. 環境変数から読み込み
        self._load_from_environment()

        self.logger.info(
            f"Error handling configuration loaded: level={self.config.default_level.value}"
        )

    def _find_config_file(self) -> Optional[Path]:
        """設定ファイルを検索"""
        for filename in self.CONFIG_FILES:
            config_path = self.config_dir / filename
            if config_path.exists():
                self.logger.debug(f"Found config file: {config_path}")
                return config_path

        # 親ディレクトリも検索
        parent_dir = self.config_dir.parent
        if parent_dir != self.config_dir:
            for filename in self.CONFIG_FILES:
                config_path = parent_dir / filename
                if config_path.exists():
                    self.logger.debug(f"Found config file in parent: {config_path}")
                    return config_path

        return None

    def _load_from_file(self, config_file: Path) -> None:
        """設定ファイルから読み込み"""
        try:
            if config_file.suffix in [".toml"]:
                if not HAS_TOML:
                    self.logger.warning(
                        f"TOML support not available. Skipping {config_file}"
                    )
                    return
                with open(config_file, "r", encoding="utf-8") as f:
                    data = toml.load(f)
            else:  # YAML
                if not HAS_YAML:
                    self.logger.warning(
                        f"YAML support not available. Skipping {config_file}"
                    )
                    return
                with open(config_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

            # エラー処理セクションを取得
            error_config = data.get("error_handling", {})

            # 基本設定を適用
            if "default_level" in error_config:
                self.config.default_level = ErrorHandlingLevel(
                    error_config["default_level"]
                )

            if "graceful_errors" in error_config:
                self.config.graceful_errors = error_config["graceful_errors"]

            if "continue_on_error" in error_config:
                self.config.continue_on_error = error_config["continue_on_error"]

            if "show_suggestions" in error_config:
                self.config.show_suggestions = error_config["show_suggestions"]

            if "show_statistics" in error_config:
                self.config.show_statistics = error_config["show_statistics"]

            # 表示設定
            display_config = error_config.get("display", {})
            if "error_limit" in display_config:
                self.config.error_display_limit = display_config["error_limit"]

            if "context_lines" in display_config:
                self.config.show_context_lines = display_config["context_lines"]

            if "highlight" in display_config:
                self.config.highlight_errors = display_config["highlight"]

            # エラータイプ別設定
            type_configs = error_config.get("type_configs", {})
            for error_type, type_config in type_configs.items():
                self.config.error_type_configs[error_type] = ErrorTypeConfig(
                    error_type=error_type,
                    handling_level=ErrorHandlingLevel(
                        type_config.get("level", "normal")
                    ),
                    strategy=ErrorHandlingStrategy(
                        type_config.get("strategy", "continue")
                    ),
                    max_occurrences=type_config.get("max_occurrences", -1),
                    custom_handler=type_config.get("custom_handler"),
                )

            self.logger.info(f"Loaded configuration from {config_file}")

        except Exception as e:
            self.logger.warning(f"Failed to load config file {config_file}: {e}")

    def _load_from_environment(self) -> None:
        """環境変数から設定を読み込み"""
        # KUMIHAN_ERROR_LEVEL
        if level_str := os.getenv(f"{self.ENV_PREFIX}LEVEL"):
            try:
                self.config.default_level = ErrorHandlingLevel(level_str.lower())
                self.logger.debug(f"Set error level from env: {level_str}")
            except ValueError:
                self.logger.warning(f"Invalid error level in env: {level_str}")

        # KUMIHAN_ERROR_GRACEFUL
        if graceful_str := os.getenv(f"{self.ENV_PREFIX}GRACEFUL"):
            self.config.graceful_errors = graceful_str.lower() in ["true", "1", "yes"]

        # KUMIHAN_ERROR_CONTINUE
        if continue_str := os.getenv(f"{self.ENV_PREFIX}CONTINUE"):
            self.config.continue_on_error = continue_str.lower() in ["true", "1", "yes"]

        # KUMIHAN_ERROR_SUGGESTIONS
        if suggestions_str := os.getenv(f"{self.ENV_PREFIX}SUGGESTIONS"):
            self.config.show_suggestions = suggestions_str.lower() in [
                "true",
                "1",
                "yes",
            ]

        # KUMIHAN_ERROR_STATISTICS
        if stats_str := os.getenv(f"{self.ENV_PREFIX}STATISTICS"):
            self.config.show_statistics = stats_str.lower() in ["true", "1", "yes"]

        # KUMIHAN_ERROR_LIMIT
        if limit_str := os.getenv(f"{self.ENV_PREFIX}LIMIT"):
            try:
                self.config.error_display_limit = int(limit_str)
            except ValueError:
                self.logger.warning(f"Invalid error limit in env: {limit_str}")

    def apply_cli_options(self, **kwargs) -> None:
        """CLIオプションを適用（最高優先度）"""
        if "error_level" in kwargs:
            self.config.default_level = ErrorHandlingLevel(kwargs["error_level"])

        if "graceful_errors" in kwargs:
            self.config.graceful_errors = kwargs["graceful_errors"]

        if "continue_on_error" in kwargs:
            self.config.continue_on_error = kwargs["continue_on_error"]

        if "show_suggestions" in kwargs:
            self.config.show_suggestions = kwargs["show_suggestions"]

        if "show_statistics" in kwargs:
            self.config.show_statistics = kwargs["show_statistics"]

        self.logger.debug("Applied CLI options to error config")

    def get_handling_strategy(self, error_type: str) -> ErrorHandlingStrategy:
        """特定のエラータイプの処理戦略を取得"""
        if error_type in self.config.error_type_configs:
            return self.config.error_type_configs[error_type].strategy

        # デフォルトレベルに基づく戦略
        if self.config.default_level == ErrorHandlingLevel.STRICT:
            return ErrorHandlingStrategy.STOP
        elif self.config.default_level == ErrorHandlingLevel.IGNORE:
            return ErrorHandlingStrategy.SKIP
        else:
            return ErrorHandlingStrategy.CONTINUE

    def should_continue_on_error(
        self, error_type: str, occurrence_count: int = 1
    ) -> bool:
        """エラー発生時に処理を継続すべきかを判定"""
        # グローバル設定チェック
        if self.config.default_level == ErrorHandlingLevel.STRICT:
            return False

        if self.config.default_level == ErrorHandlingLevel.IGNORE:
            return True

        # エラータイプ別設定チェック
        if error_type in self.config.error_type_configs:
            type_config = self.config.error_type_configs[error_type]

            # 発生回数制限チェック
            if (
                type_config.max_occurrences > 0
                and occurrence_count > type_config.max_occurrences
            ):
                return False

            # レベルチェック
            if type_config.handling_level == ErrorHandlingLevel.STRICT:
                return False

        return self.config.continue_on_error or self.config.graceful_errors

    def get_error_severity(self, error_type: str) -> str:
        """エラータイプに基づく重要度を取得"""
        if self.config.default_level == ErrorHandlingLevel.LENIENT:
            return "warning"

        if error_type in self.config.error_type_configs:
            type_config = self.config.error_type_configs[error_type]
            if type_config.handling_level == ErrorHandlingLevel.LENIENT:
                return "warning"
            elif type_config.handling_level == ErrorHandlingLevel.IGNORE:
                return "info"

        return "error"

    def save_config_template(self, output_path: Path) -> None:
        """設定テンプレートを保存"""
        template = {
            "error_handling": {
                "default_level": "normal",
                "graceful_errors": True,
                "continue_on_error": False,
                "show_suggestions": True,
                "show_statistics": True,
                "display": {"error_limit": 100, "context_lines": 3, "highlight": True},
                "report": {
                    "save_report": False,
                    "report_path": "error_report.json",
                    "include_source": False,
                },
                "type_configs": {
                    "marker_mismatch": {
                        "level": "normal",
                        "strategy": "recover",
                        "max_occurrences": -1,
                    },
                    "incomplete_marker": {
                        "level": "lenient",
                        "strategy": "recover",
                        "max_occurrences": 10,
                    },
                    "invalid_syntax": {
                        "level": "strict",
                        "strategy": "stop",
                        "max_occurrences": 1,
                    },
                },
            }
        }

        if output_path.suffix == ".toml":
            if not HAS_TOML:
                self.logger.error(
                    "TOML support not available. Cannot save config template."
                )
                raise ImportError("toml module not available")
            with open(output_path, "w", encoding="utf-8") as f:
                toml.dump(template, f)
        else:  # YAML
            if not HAS_YAML:
                self.logger.error(
                    "YAML support not available. Cannot save config template."
                )
                raise ImportError("yaml module not available")
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(template, f, default_flow_style=False, allow_unicode=True)

        self.logger.info(f"Saved config template to {output_path}")
