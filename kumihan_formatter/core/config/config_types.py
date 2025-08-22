"""統合設定型定義・モデル

Issue #912対応: 分散していた型定義・Pydanticモデルを統合
- core/config/config_types.py (基本型定義)
- core/unified_config/config_models.py (Pydanticモデル群)
- models/config.py (FormatterConfig系)
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ...core.utilities.logger import get_logger

logger = get_logger(__name__)


# ===== 基本型定義 =====


class ConfigLevel(Enum):
    """設定の優先度レベル"""

    DEFAULT = 1
    SYSTEM = 2
    USER = 3
    PROJECT = 4
    ENVIRONMENT = 5


class ConfigFormat(str, Enum):
    """サポートする設定ファイル形式"""

    YAML = "yaml"
    JSON = "json"
    TOML = "toml"


class LogLevel(str, Enum):
    """ログレベル"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorHandlingLevel(str, Enum):
    """エラー処理レベル"""

    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"
    IGNORE = "ignore"


@dataclass
class ValidationResult:
    """設定検証結果"""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def has_issues(self) -> bool:
        """検証で問題があるかチェック"""
        return len(self.errors) > 0 or len(self.warnings) > 0


# ===== Pydanticモデル群 =====


class ParallelConfig(BaseModel):
    """並列処理設定

    ParallelProcessingConfigの統一版
    """

    # 並列処理しきい値
    parallel_threshold_lines: int = Field(
        default=10000, ge=1000, description="並列処理を開始する行数のしきい値"
    )
    parallel_threshold_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024 * 1024,  # 1MB
        description="並列処理を開始するファイルサイズのしきい値(bytes)",
    )

    # チャンク設定
    min_chunk_size: int = Field(default=50, ge=10, description="最小チャンクサイズ")
    max_chunk_size: int = Field(
        default=2000, le=10000, description="最大チャンクサイズ"
    )
    target_chunks_per_core: int = Field(
        default=2, ge=1, le=10, description="CPUコアあたりのチャンク数"
    )

    # メモリ監視
    memory_warning_threshold_mb: int = Field(
        default=150, ge=50, description="メモリ警告しきい値(MB)"
    )
    memory_critical_threshold_mb: int = Field(
        default=250, ge=100, description="メモリクリティカルしきい値(MB)"
    )
    memory_check_interval: int = Field(
        default=10, ge=1, description="メモリチェック間隔(チャンク数)"
    )

    # タイムアウト設定
    processing_timeout_seconds: int = Field(
        default=300, ge=10, description="処理タイムアウト(秒)"
    )
    chunk_timeout_seconds: int = Field(
        default=30, ge=5, description="チャンクタイムアウト(秒)"
    )

    # パフォーマンス設定
    enable_progress_callbacks: bool = Field(
        default=True, description="プログレスコールバック有効"
    )
    progress_update_interval: int = Field(
        default=100, ge=10, description="プログレス更新間隔(行数)"
    )
    enable_memory_monitoring: bool = Field(default=True, description="メモリ監視有効")
    enable_gc_optimization: bool = Field(default=True, description="GC最適化有効")

    @field_validator("max_chunk_size")
    @classmethod
    def validate_chunk_sizes(cls, v: Any, info: Any) -> Any:
        """チャンクサイズの整合性チェック"""
        if (
            hasattr(info, "data")
            and "min_chunk_size" in info.data
            and v <= info.data["min_chunk_size"]
        ):
            raise ValueError("max_chunk_size must be greater than min_chunk_size")
        return v

    @field_validator("memory_critical_threshold_mb")
    @classmethod
    def validate_memory_thresholds(cls, v: Any, info: Any) -> Any:
        """メモリしきい値の整合性チェック"""
        if (
            hasattr(info, "data")
            and "memory_warning_threshold_mb" in info.data
            and v <= info.data["memory_warning_threshold_mb"]
        ):
            raise ValueError(
                "memory_critical_threshold_mb must be greater than "
                "memory_warning_threshold_mb"
            )
        return v


class LoggingConfig(BaseModel):
    """ログ設定

    KumihanLoggerの統一版
    """

    log_level: LogLevel = Field(default=LogLevel.INFO, description="ログレベル")
    log_dir: Path = Field(
        default_factory=lambda: Path.home() / ".kumihan" / "logs",
        description="ログディレクトリ",
    )

    # 開発ログ設定
    dev_log_enabled: bool = Field(default=False, description="開発ログ有効")
    dev_log_json: bool = Field(default=False, description="開発ログJSON形式")

    # ファイルローテーション設定
    log_rotation_when: str = Field(
        default="midnight", description="ログローテーション頻度"
    )
    log_rotation_interval: int = Field(
        default=1, ge=1, description="ローテーション間隔"
    )
    log_backup_count: int = Field(
        default=30, ge=1, description="バックアップファイル数"
    )

    # パフォーマンスログ設定
    performance_logging_enabled: bool = Field(
        default=True, description="パフォーマンスログ有効"
    )

    model_config = ConfigDict()


class ErrorConfig(BaseModel):
    """エラー処理設定

    ErrorConfigManagerの統一版
    """

    default_level: ErrorHandlingLevel = Field(
        default=ErrorHandlingLevel.NORMAL, description="デフォルトエラー処理レベル"
    )

    # エラー表示設定
    graceful_errors: bool = Field(default=False, description="エラー情報HTML埋め込み")
    continue_on_error: bool = Field(default=False, description="エラー時処理継続")
    show_suggestions: bool = Field(default=True, description="エラー修正提案表示")
    show_statistics: bool = Field(default=True, description="エラー統計表示")

    # エラー制限設定
    error_display_limit: int = Field(default=10, ge=1, description="表示エラー数制限")
    max_error_context_lines: int = Field(
        default=3, ge=0, description="エラーコンテキスト行数"
    )

    # カテゴリ別設定
    category_settings: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="カテゴリ別エラー設定"
    )

    model_config = ConfigDict()


class RenderingConfig(BaseModel):
    """レンダリング設定

    BaseConfigのCSS設定等を統合
    """

    # CSS設定
    max_width: str = Field(default="800px", description="最大幅")
    background_color: str = Field(default="#f9f9f9", description="背景色")
    container_background: str = Field(default="white", description="コンテナ背景色")
    text_color: str = Field(default="#333", description="テキスト色")
    line_height: str = Field(default="1.8", description="行の高さ")
    font_family: str = Field(
        default=(
            "Hiragino Kaku Gothic ProN, Hiragino Sans, " "Yu Gothic, Meiryo, sans-serif"
        ),
        description="フォントファミリー",
    )

    # テーマ設定
    theme_name: str = Field(default="デフォルト", description="テーマ名")
    custom_css: Dict[str, str] = Field(default_factory=dict, description="カスタムCSS")

    # レンダリング設定
    include_source: bool = Field(default=False, description="ソース表示機能")
    enable_syntax_highlighting: bool = Field(
        default=True, description="構文ハイライト有効"
    )

    model_config = ConfigDict()


class UIConfig(BaseModel):
    """UI設定

    GUI・CLI関連設定の統合
    """

    # プレビュー設定
    auto_preview: bool = Field(default=True, description="自動プレビュー")
    preview_browser: Optional[str] = Field(
        default=None, description="プレビューブラウザ"
    )

    # プログレス表示設定
    progress_level: str = Field(
        default="detailed",
        pattern="^(silent|minimal|detailed|verbose)$",
        description="プログレス表示レベル",
    )
    progress_style: str = Field(
        default="bar",
        pattern="^(bar|spinner|percentage)$",
        description="プログレス表示スタイル",
    )
    show_progress_tooltip: bool = Field(
        default=True, description="プログレスツールチップ表示"
    )
    enable_cancellation: bool = Field(default=True, description="キャンセル機能有効")

    # ファイル監視設定
    watch_enabled: bool = Field(default=False, description="ファイル監視有効")
    watch_interval: float = Field(default=1.0, ge=0.1, description="監視間隔(秒)")

    model_config = ConfigDict()


class FormatterConfig(BaseModel):
    """Kumihan-Formatter設定モデル

    型安全な設定管理のためのpydantic BaseModel
    models/config.pyから統合
    """

    # 基本設定
    input_encoding: str = Field(
        default="utf-8", description="入力ファイルの文字エンコーディング"
    )
    output_encoding: str = Field(
        default="utf-8", description="出力ファイルの文字エンコーディング"
    )

    # テンプレート設定
    template_dir: str | None = Field(
        default=None, description="テンプレートディレクトリのパス"
    )
    template_name: str | None = Field(
        default=None, description="使用するテンプレート名"
    )

    # 変換設定
    strict_mode: bool = Field(default=False, description="厳密モードで実行")
    include_source: bool = Field(default=False, description="ソース表示機能を含める")
    syntax_check: bool = Field(default=True, description="構文チェックを実行")

    # 出力設定
    no_preview: bool = Field(default=False, description="プレビューをスキップ")
    watch_mode: bool = Field(default=False, description="ファイル変更監視モード")

    # CSS設定
    css_variables: dict[str, str] = Field(
        default_factory=lambda: {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8",
            "font_family": (
                "Hiragino Kaku Gothic ProN, Hiragino Sans, "
                "Yu Gothic, Meiryo, sans-serif"
            ),
        },
        description="CSS変数の辞書",
    )

    model_config = ConfigDict(
        extra="forbid",  # 未定義フィールドを禁止
        validate_assignment=True,  # 代入時の検証を有効化
        str_strip_whitespace=True,  # 文字列の前後空白を自動削除
    )


class SimpleFormatterConfig(BaseModel):
    """簡素化された設定モデル

    初心者向けの簡素化された設定
    models/config.pyから統合
    """

    # 基本設定のみ
    template_name: str = Field(default="default", description="テンプレート名")
    include_source: bool = Field(default=False, description="ソース表示機能")

    # 固定CSS設定
    css_variables: dict[str, str] = Field(
        default_factory=lambda: {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8",
            "font_family": (
                "Hiragino Kaku Gothic ProN, Hiragino Sans, "
                "Yu Gothic, Meiryo, sans-serif"
            ),
        },
        description="CSS変数の辞書",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    def get_theme_name(self) -> str:
        """テーマ名を取得"""
        return "デフォルト"


class KumihanConfig(BaseModel):
    """Kumihan-Formatter統一設定

    全設定の最上位コンテナ
    """

    # サブ設定群
    parallel: ParallelConfig = Field(default_factory=ParallelConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    error: ErrorConfig = Field(default_factory=ErrorConfig)
    rendering: RenderingConfig = Field(default_factory=RenderingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    # メタ設定
    config_version: str = Field(default="1.0", description="設定バージョン")
    config_file_path: Optional[Path] = Field(
        default=None, description="設定ファイルパス"
    )
    last_updated: Optional[str] = Field(default=None, description="最終更新日時")

    # 環境情報
    environment: str = Field(default="production", description="実行環境")
    debug_mode: bool = Field(default=False, description="デバッグモード")

    @model_validator(mode="before")
    @classmethod
    def validate_config_consistency(cls, values: Any) -> Any:
        """設定間の整合性チェック"""
        # ログレベルとデバッグモードの整合性
        if values.get("debug_mode") and values.get("logging"):
            logging_data = values["logging"]
            # LoggingConfigインスタンスの場合
            if hasattr(logging_data, "log_level"):
                if logging_data.log_level not in [LogLevel.DEBUG, LogLevel.INFO]:
                    logging_data.log_level = LogLevel.DEBUG
            # 辞書の場合
            elif isinstance(logging_data, dict):
                if logging_data.get("log_level") not in ["DEBUG", "INFO"]:
                    logging_data["log_level"] = "DEBUG"

        return values

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で設定を出力"""
        return self.model_dump(mode="json")

    def get_env_vars(self) -> Dict[str, str]:
        """現在の設定から環境変数を生成"""
        env_vars = {}

        # 各サブ設定から環境変数を抽出
        for field_name, field_value in self.model_dump().items():
            if isinstance(field_value, dict):
                prefix = f"KUMIHAN_{field_name.upper()}_"
                for key, value in field_value.items():
                    env_key = f"{prefix}{key.upper()}"
                    env_vars[env_key] = str(value)

        return env_vars


# ===== 後方互換性エイリアス =====

# 既存のインポートパスとの互換性を保つためのエイリアス
Config = KumihanConfig  # kumihan_formatter.config.Config の代替
BaseConfig = KumihanConfig  # config.base_config.BaseConfig の代替
ExtendedConfig = KumihanConfig  # config.extended_config.ExtendedConfig の代替
EnhancedConfig = KumihanConfig  # core.config.config_manager.EnhancedConfig の代替
