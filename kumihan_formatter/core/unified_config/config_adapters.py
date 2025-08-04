"""統一設定アダプター

Issue #771対応: 既存設定クラスとの互換性を保つアダプター群
統一設定システムへの移行期間中に旧コードが正常動作するよう支援
"""

import warnings
from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..utilities.logger import get_logger
from .config_models import KumihanConfig, ParallelConfig, LoggingConfig, ErrorConfig, RenderingConfig
from .unified_config_manager import get_unified_config_manager


class ParallelProcessingConfigAdapter:
    """ParallelProcessingConfig互換アダプター

    既存のParallelProcessingConfigクラスの代替として機能
    統一設定システムから並列処理設定を取得し、旧API形式で提供
    """

    def __init__(self, config_manager: Optional[Any] = None):
        """アダプター初期化

        Args:
            config_manager: 統一設定マネージャー (Noneの場合はグローバルを使用)
        """
        self.logger = get_logger(__name__)
        self._config_manager = config_manager or get_unified_config_manager()

        # 互換性警告の表示
        warnings.warn(
            "ParallelProcessingConfigは統一設定システムに統合されました。"
            "新しいコードではUnifiedConfigManager.get_parallel_config()を使用してください。",
            DeprecationWarning,
            stacklevel=2
        )

    @property
    def config(self) -> ParallelConfig:
        """統一設定から並列処理設定を取得"""
        return self._config_manager.get_parallel_config()

    # 旧API互換プロパティ
    @property
    def threshold_lines(self) -> int:
        """並列処理しきい値行数 (旧API互換)"""
        return self.config.parallel_threshold_lines

    @property
    def threshold_size(self) -> int:
        """並列処理しきい値サイズ (旧API互換)"""
        return self.config.parallel_threshold_size

    @property
    def min_chunk_size(self) -> int:
        """最小チャンクサイズ"""
        return self.config.min_chunk_size

    @property
    def max_chunk_size(self) -> int:
        """最大チャンクサイズ"""
        return self.config.max_chunk_size

    @property
    def target_chunks_per_core(self) -> int:
        """CPUコアあたりのチャンク数"""
        return self.config.target_chunks_per_core

    @property
    def memory_warning_threshold_mb(self) -> int:
        """メモリ警告しきい値(MB)"""
        return self.config.memory_warning_threshold_mb

    @property
    def memory_critical_threshold_mb(self) -> int:
        """メモリクリティカルしきい値(MB)"""
        return self.config.memory_critical_threshold_mb

    @property
    def processing_timeout_seconds(self) -> int:
        """処理タイムアウト(秒)"""
        return self.config.processing_timeout_seconds

    # 旧API互換メソッド
    def should_use_parallel_processing(self, line_count: int, file_size: int) -> bool:
        """並列処理が必要かチェック (旧API互換)

        Args:
            line_count: 行数
            file_size: ファイルサイズ

        Returns:
            bool: 並列処理使用可否
        """
        return (line_count >= self.threshold_lines or
                file_size >= self.threshold_size)

    def calculate_chunk_count(self, line_count: int) -> int:
        """チャンク数計算 (旧API互換)

        Args:
            line_count: 総行数

        Returns:
            int: 推奨チャンク数
        """
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()

        # 基本チャンク数
        base_chunks = max(1, line_count // self.max_chunk_size)

        # CPUコア数ベースの調整
        target_chunks = cpu_count * self.target_chunks_per_core

        return min(base_chunks, target_chunks)

    def get_chunk_size(self, line_count: int, chunk_count: int) -> int:
        """チャンクサイズ計算 (旧API互換)

        Args:
            line_count: 総行数
            chunk_count: チャンク数

        Returns:
            int: チャンクサイズ
        """
        calculated_size = max(1, line_count // chunk_count)
        return max(self.min_chunk_size,
                  min(self.max_chunk_size, calculated_size))

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す (旧API互換)"""
        return self.config.dict()


class ErrorConfigManagerAdapter:
    """ErrorConfigManager互換アダプター

    既存のErrorConfigManagerクラスの代替として機能
    統一設定システムからエラー処理設定を取得し、旧API形式で提供
    """

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """アダプター初期化

        Args:
            config_file: 設定ファイルパス (互換性のため、実際は統一設定を使用)
        """
        self.logger = get_logger(__name__)
        self._config_manager = get_unified_config_manager()

        # 互換性警告の表示
        warnings.warn(
            "ErrorConfigManagerは統一設定システムに統合されました。"
            "新しいコードではUnifiedConfigManager.get_error_config()を使用してください。",
            DeprecationWarning,
            stacklevel=2
        )

        # 指定されたconfig_fileは無視（統一設定で管理）
        if config_file:
            self.logger.info(f"設定ファイル'{config_file}'は統一設定システムで管理されます")

    @property
    def config(self) -> ErrorConfig:
        """統一設定からエラー処理設定を取得"""
        return self._config_manager.get_error_config()

    # 旧API互換プロパティ
    @property
    def graceful_errors(self) -> bool:
        """グレースフルエラー有効"""
        return self.config.graceful_errors

    @property
    def continue_on_error(self) -> bool:
        """エラー時処理継続"""
        return self.config.continue_on_error

    @property
    def show_suggestions(self) -> bool:
        """エラー修正提案表示"""
        return self.config.show_suggestions

    @property
    def show_statistics(self) -> bool:
        """エラー統計表示"""
        return self.config.show_statistics

    @property
    def error_display_limit(self) -> int:
        """表示エラー数制限"""
        return self.config.error_display_limit

    @property
    def max_error_context_lines(self) -> int:
        """エラーコンテキスト行数"""
        return self.config.max_error_context_lines

    # 旧API互換メソッド
    def get_error_handling_level(self, category: str = "default") -> str:
        """エラー処理レベル取得 (旧API互換)

        Args:
            category: エラーカテゴリ

        Returns:
            str: エラー処理レベル
        """
        category_settings = self.config.category_settings.get(category, {})
        return category_settings.get("level", self.config.default_level.value)

    def should_continue_on_error(self, category: str = "default") -> bool:
        """エラー時継続判定 (旧API互換)

        Args:
            category: エラーカテゴリ

        Returns:
            bool: 継続するかどうか
        """
        if category in self.config.category_settings:
            return self.config.category_settings[category].get(
                "continue_on_error", self.config.continue_on_error
            )
        return self.config.continue_on_error

    def get_category_settings(self, category: str) -> Dict[str, Any]:
        """カテゴリ別設定取得 (旧API互換)

        Args:
            category: エラーカテゴリ

        Returns:
            Dict[str, Any]: カテゴリ設定
        """
        return self.config.category_settings.get(category, {})

    def update_category_settings(self, category: str, settings: Dict[str, Any]) -> None:
        """カテゴリ別設定更新 (旧API互換)

        Args:
            category: エラーカテゴリ
            settings: 新しい設定
        """
        # 統一設定システムでは実際の更新は行わず、警告のみ表示
        self.logger.warning(
            f"カテゴリ'{category}'の設定更新は統一設定システムで行ってください。"
            "実行時の動的更新はサポートされません。"
        )

    def save_config(self) -> bool:
        """設定保存 (旧API互換)

        Returns:
            bool: 保存成功フラグ
        """
        # 統一設定システムを通じて保存
        try:
            return self._config_manager.save_config()
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す (旧API互換)"""
        return self.config.dict()


class BaseConfigAdapter:
    """BaseConfig互換アダプター

    既存のBaseConfigクラスの代替として機能
    統一設定システムからレンダリング設定を取得し、旧API形式で提供
    """

    def __init__(self):
        """アダプター初期化"""
        self.logger = get_logger(__name__)
        self._config_manager = get_unified_config_manager()

        # 互換性警告の表示
        warnings.warn(
            "BaseConfigは統一設定システムに統合されました。"
            "新しいコードではUnifiedConfigManager.get_rendering_config()を使用してください。",
            DeprecationWarning,
            stacklevel=2
        )

    @property
    def config(self) -> RenderingConfig:
        """統一設定からレンダリング設定を取得"""
        return self._config_manager.get_rendering_config()

    # 旧API互換プロパティ
    @property
    def max_width(self) -> str:
        """最大幅"""
        return self.config.max_width

    @property
    def background_color(self) -> str:
        """背景色"""
        return self.config.background_color

    @property
    def container_background(self) -> str:
        """コンテナ背景色"""
        return self.config.container_background

    @property
    def text_color(self) -> str:
        """テキスト色"""
        return self.config.text_color

    @property
    def line_height(self) -> str:
        """行の高さ"""
        return self.config.line_height

    @property
    def font_family(self) -> str:
        """フォントファミリー"""
        return self.config.font_family

    @property
    def theme_name(self) -> str:
        """テーマ名"""
        return self.config.theme_name

    @property
    def custom_css(self) -> Dict[str, str]:
        """カスタムCSS"""
        return self.config.custom_css

    @property
    def include_source(self) -> bool:
        """ソース表示機能"""
        return self.config.include_source

    @property
    def enable_syntax_highlighting(self) -> bool:
        """構文ハイライト有効"""
        return self.config.enable_syntax_highlighting

    # 旧API互換メソッド
    def get_css_style(self) -> str:
        """CSS文字列生成 (旧API互換)

        Returns:
            str: CSS文字列
        """
        css_parts = [
            f"max-width: {self.max_width};",
            f"background-color: {self.background_color};",
            f"color: {self.text_color};",
            f"line-height: {self.line_height};",
            f"font-family: {self.font_family};"
        ]

        # カスタムCSSの追加
        for selector, styles in self.custom_css.items():
            css_parts.append(f"{selector} {{ {styles} }}")

        return " ".join(css_parts)

    def get_container_style(self) -> str:
        """コンテナスタイル取得 (旧API互換)

        Returns:
            str: コンテナCSS文字列
        """
        return f"background-color: {self.container_background}; max-width: {self.max_width};"

    def update_theme(self, theme_name: str, theme_settings: Dict[str, str]) -> None:
        """テーマ更新 (旧API互換)

        Args:
            theme_name: テーマ名
            theme_settings: テーマ設定
        """
        # 統一設定システムでは動的更新は制限される
        self.logger.warning(
            f"テーマ'{theme_name}'の更新は統一設定システムで行ってください。"
            "実行時の動的更新はサポートされません。"
        )

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す (旧API互換)"""
        return self.config.dict()


# 互換性ヘルパー関数群

def create_parallel_processing_config(*args, **kwargs) -> ParallelProcessingConfigAdapter:
    """ParallelProcessingConfig作成ヘルパー (旧API互換)

    Returns:
        ParallelProcessingConfigAdapter: アダプターインスタンス
    """
    return ParallelProcessingConfigAdapter()


def create_error_config_manager(config_file: Optional[Union[str, Path]] = None) -> ErrorConfigManagerAdapter:
    """ErrorConfigManager作成ヘルパー (旧API互換)

    Args:
        config_file: 設定ファイルパス

    Returns:
        ErrorConfigManagerAdapter: アダプターインスタンス
    """
    return ErrorConfigManagerAdapter(config_file)


def create_base_config() -> BaseConfigAdapter:
    """BaseConfig作成ヘルパー (旧API互換)

    Returns:
        BaseConfigAdapter: アダプターインスタンス
    """
    return BaseConfigAdapter()


# 移行支援関数

def migrate_config_usage(old_config_type: str) -> str:
    """設定クラス移行ガイダンス

    Args:
        old_config_type: 旧設定クラス名

    Returns:
        str: 移行ガイド文字列
    """
    migration_guides = {
        "ParallelProcessingConfig": (
            "# 旧コード:\n"
            "config = ParallelProcessingConfig()\n"
            "threshold = config.threshold_lines\n\n"
            "# 新コード:\n"
            "from kumihan_formatter.core.unified_config import get_unified_config_manager\n"
            "manager = get_unified_config_manager()\n"
            "threshold = manager.get_parallel_config().parallel_threshold_lines"
        ),
        "ErrorConfigManager": (
            "# 旧コード:\n"
            "manager = ErrorConfigManager('config.yaml')\n"
            "graceful = manager.graceful_errors\n\n"
            "# 新コード:\n"
            "from kumihan_formatter.core.unified_config import get_unified_config_manager\n"
            "manager = get_unified_config_manager()\n"
            "graceful = manager.get_error_config().graceful_errors"
        ),
        "BaseConfig": (
            "# 旧コード:\n"
            "config = BaseConfig()\n"
            "width = config.max_width\n\n"
            "# 新コード:\n"
            "from kumihan_formatter.core.unified_config import get_unified_config_manager\n"
            "manager = get_unified_config_manager()\n"
            "width = manager.get_rendering_config().max_width"
        )
    }

    return migration_guides.get(old_config_type, "該当する移行ガイドが見つかりません")


def check_config_compatibility() -> Dict[str, bool]:
    """設定互換性チェック

    Returns:
        Dict[str, bool]: 各設定クラスの互換性状況
    """
    compatibility_status = {}

    try:
        # 統一設定マネージャーの動作確認
        manager = get_unified_config_manager()
        config = manager.get_config()

        compatibility_status["unified_config"] = True
        compatibility_status["parallel_config"] = bool(config.parallel)
        compatibility_status["logging_config"] = bool(config.logging)
        compatibility_status["error_config"] = bool(config.error)
        compatibility_status["rendering_config"] = bool(config.rendering)
        compatibility_status["ui_config"] = bool(config.ui)

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"設定互換性チェックエラー: {e}")
        compatibility_status["error"] = str(e)

    return compatibility_status
