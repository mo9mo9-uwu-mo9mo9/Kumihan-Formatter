"""統合設定管理マネージャー

Issue #912対応: 複数のConfigManagerを統合
- core/unified_config/unified_config_manager.py (UnifiedConfigManager - 最も包括的)
- core/config/config_manager.py (EnhancedConfig - 拡張機能)
- config/config_manager.py (ConfigManager - 基本機能)
- その他の基本設定クラス群
"""

import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ...core.utilities.logger import get_logger
from .config_loader import ConfigLoader, ConfigLoadError
from .config_types import ConfigFormat, ConfigLevel, KumihanConfig
from .config_validator import ConfigValidator

logger = get_logger(__name__)

# グローバル変数宣言
_global_config_manager: "ConfigManager | None" = None


class ConfigManager:
    """統合設定管理マネージャー

    全設定の一元管理を提供:
    - 設定読み込み (環境変数・ファイル・デフォルト)
    - 設定検証・自動修正
    - ホットリロード機能
    - 既存設定クラスとの互換性
    - 複数設定ソース統合・環境別設定
    """

    # デフォルト設定（EnhancedConfigから継承）
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
            "max_file_size_mb": 100,
            "allowed_extensions": [".md", ".txt", ".kumihan"],
        },
    }

    def __init__(
        self,
        config_file: Optional[Union[str, Path]] = None,
        auto_reload: bool = False,
        validation_enabled: bool = True,
        config_path: Optional[Path] = None,  # 後方互換性
    ):
        """統一設定マネージャー初期化

        Args:
            config_file: 設定ファイルパス
            auto_reload: ホットリロード有効
            validation_enabled: 設定検証有効
            config_path: 設定ファイルパス（後方互換性のため）
        """
        self.logger = get_logger(__name__)

        # 後方互換性: config_pathが指定されていればconfig_fileより優先
        if config_path is not None:
            config_file = config_path

        # コンポーネント初期化
        self.loader = ConfigLoader()
        self.validator = ConfigValidator() if validation_enabled else None

        # 設定管理
        self._config: Optional[KumihanConfig] = None
        self._config_file_path: Optional[Path] = None
        self._last_modified: Optional[float] = None
        self._validation_enabled = validation_enabled

        # ホットリロード設定
        self._auto_reload = auto_reload
        self._reload_thread: Optional[threading.Thread] = None
        self._reload_callbacks: List[Callable[[KumihanConfig], None]] = []
        self._shutdown_event = threading.Event()

        # 設定レベル管理（EnhancedConfigとの互換性）
        self._config_levels: Dict[ConfigLevel, Dict[str, Any]] = {}

        # 初期設定読み込み
        self._load_initial_config(config_file)

        # ホットリロード開始
        if self._auto_reload and self._config_file_path is not None:
            self._start_auto_reload()

    def _load_initial_config(self, config_file: Optional[Union[str, Path]]) -> None:
        """初期設定読み込み

        Args:
            config_file: 指定された設定ファイル
        """
        try:
            # 1. 設定ファイルの決定
            if config_file:
                self._config_file_path = Path(config_file)
                if not self._config_file_path.exists():
                    self.logger.warning(
                        f"指定された設定ファイルが見つかりません: {config_file}"
                    )
                    self._config_file_path = None
            else:
                # 自動検索
                self._config_file_path = self.loader.find_config_file()

            # 2. 設定読み込み・マージ
            self._reload_config()

        except Exception as e:
            self.logger.error(f"初期設定読み込みエラー: {e}")
            # デフォルト設定で初期化
            self._config = self._create_default_config()

    def _reload_config(self) -> None:
        """設定を再読み込み"""
        try:
            # 1. 各ソースから設定読み込み
            configs_to_merge = []

            # デフォルト設定
            configs_to_merge.append(self.DEFAULT_CONFIG)

            # ファイル設定
            if self._config_file_path and self._config_file_path.exists():
                try:
                    file_config = self.loader.load_from_file(self._config_file_path)
                    configs_to_merge.append(file_config)

                    # ファイル更新時刻を記録
                    self._last_modified = self._config_file_path.stat().st_mtime

                except ConfigLoadError as e:
                    self.logger.error(f"設定ファイル読み込みエラー: {e}")

            # 環境変数設定
            env_config = self.loader.load_from_environment()
            if env_config:
                configs_to_merge.append(env_config)

            # 設定レベル別設定の統合
            for level in [
                ConfigLevel.DEFAULT,
                ConfigLevel.SYSTEM,
                ConfigLevel.USER,
                ConfigLevel.PROJECT,
                ConfigLevel.ENVIRONMENT,
            ]:
                if level in self._config_levels:
                    configs_to_merge.append(self._config_levels[level])

            # 2. 設定マージ
            merged_config = self.loader.merge_configs(*configs_to_merge)

            # 3. 新設定として統一Configオブジェクト作成
            try:
                new_config = KumihanConfig(**merged_config)
            except Exception as e:
                self.logger.warning(f"KumihanConfig作成失敗、デフォルト設定を使用: {e}")
                new_config = self._create_default_config()

            # 4. 設定検証
            if self.validator:
                result = self.validator.validate_config(merged_config, auto_fix=True)

                if not result.is_valid:
                    self.logger.warning(
                        f"設定検証で問題発見: {len(result.errors)}エラー, "
                        f"{len(result.warnings)}警告"
                    )

                    # 修正済み設定があれば使用
                    if result.fixed_config:
                        new_config = result.fixed_config

            # 5. 設定更新
            old_config = self._config
            self._config = new_config

            # 6. 更新時刻設定
            self._config.last_updated = datetime.now().isoformat()

            # 7. リロードコールバック実行
            if old_config != new_config:
                self._notify_reload_callbacks()

            self.logger.info("設定読み込み完了")

        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
            if self._config is None:
                self._config = self._create_default_config()

    def _create_default_config(self) -> KumihanConfig:
        """デフォルト設定でKumihanConfigを作成"""
        try:
            return KumihanConfig()
        except Exception as e:
            self.logger.error(f"デフォルト設定作成エラー: {e}")
            # 最小限の設定で再作成
            return KumihanConfig(
                config_version="1.0", environment="production", debug_mode=False
            )

    def _start_auto_reload(self) -> None:
        """ホットリロード開始"""
        if self._reload_thread is not None:
            return

        self._shutdown_event.clear()
        self._reload_thread = threading.Thread(
            target=self._auto_reload_worker, daemon=True, name="ConfigAutoReload"
        )
        self._reload_thread.start()
        self.logger.info("設定ホットリロード開始")

    def _auto_reload_worker(self) -> None:
        """ホットリロードワーカー"""
        while not self._shutdown_event.wait(1.0):  # 1秒間隔でチェック
            try:
                if (
                    self._config_file_path
                    and self._config_file_path.exists()
                    and self._last_modified
                ):

                    current_mtime = self._config_file_path.stat().st_mtime
                    if current_mtime > self._last_modified:
                        self.logger.info("設定ファイル変更を検出、リロード中...")
                        self._reload_config()

            except Exception as e:
                self.logger.error(f"ホットリロードエラー: {e}")

    def _notify_reload_callbacks(self) -> None:
        """リロードコールバック通知"""
        if not self._config:
            return

        for callback in self._reload_callbacks:
            try:
                callback(self._config)
            except Exception as e:
                self.logger.error(f"リロードコールバックエラー: {e}")

    def add_reload_callback(self, callback: Callable[[KumihanConfig], None]) -> None:
        """リロードコールバック追加"""
        self._reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: Callable[[KumihanConfig], None]) -> None:
        """リロードコールバック削除"""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)

    def set_config_level(self, level: ConfigLevel, config: Dict[str, Any]) -> None:
        """設定レベル別の設定を設定"""
        self._config_levels[level] = config
        self._reload_config()

    def get_config_level(self, level: ConfigLevel) -> Dict[str, Any]:
        """設定レベル別の設定を取得"""
        return self._config_levels.get(level, {})

    def load_from_env(self) -> Dict[str, Any]:
        """環境変数から設定を読み込み（後方互換性）"""
        return self.loader.load_from_environment()

    def load_config(self, path: Path) -> Dict[str, Any]:
        """ファイルから設定を読み込み（後方互換性）"""
        return self.loader.load_from_file(path)

    def validate(self, config: Dict[str, Any]) -> bool:
        """設定を検証（後方互換性）"""
        if not self.validator:
            return True

        result = self.validator.validate(config)
        return result.is_valid

    def get_adapter(self, adapter_type: str) -> Any:
        """アダプター取得（config_adapters.pyからの機能統合）"""
        # 基本的なアダプター機能を提供
        if adapter_type == "logging":
            return self._config.logging if self._config else None
        elif adapter_type == "error":
            return self._config.error if self._config else None
        elif adapter_type == "parallel":
            return self._config.parallel if self._config else None
        elif adapter_type == "rendering":
            return self._config.rendering if self._config else None
        elif adapter_type == "ui":
            return self._config.ui if self._config else None
        else:
            return None

    @property
    def config(self) -> KumihanConfig:
        """現在の設定を取得"""
        if self._config is None:
            self._config = self._create_default_config()
        return self._config

    @property
    def is_valid(self) -> bool:
        """設定が有効かチェック"""
        if not self.validator or not self._config:
            return True

        result = self.validator.validate_config(self._config.model_dump())
        return result.is_valid

    def save_config(
        self,
        config_path: Optional[Union[str, Path]] = None,
        format: Optional[Union[str, ConfigFormat]] = None,
    ) -> None:
        """設定をファイルに保存"""
        if not self._config:
            raise ValueError("保存する設定がありません")

        path = config_path or self._config_file_path
        if not path:
            raise ValueError("保存先パスが指定されていません")

        # 文字列の場合はConfigFormatに変換
        config_format = None
        if format is not None:
            if isinstance(format, str):
                try:
                    config_format = ConfigFormat(format)
                except ValueError:
                    config_format = None
            else:
                config_format = format

        self.loader.save_config(self._config, path, config_format)

    def reload(self) -> None:
        """設定を手動でリロード"""
        self._reload_config()

    def shutdown(self) -> None:
        """マネージャーをシャットダウン"""
        if self._auto_reload and self._reload_thread:
            self._shutdown_event.set()
            self._reload_thread.join(timeout=5.0)
            self._reload_thread = None

        self.logger.info("設定マネージャーをシャットダウンしました")

    def __enter__(self) -> "ConfigManager":
        """コンテキストマネージャー対応"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """コンテキストマネージャー対応"""
        self.shutdown()


# ===== グローバル設定管理 =====


def get_global_config_manager() -> ConfigManager:
    """グローバル設定マネージャーを取得"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def set_global_config_manager(manager: ConfigManager) -> None:
    """グローバル設定マネージャーを設定"""
    global _global_config_manager
    _global_config_manager = manager


def reset_global_config_manager() -> None:
    """グローバル設定マネージャーをリセット"""
    global _global_config_manager
    if _global_config_manager:
        _global_config_manager.shutdown()
    _global_config_manager = None


# ===== 後方互換性エイリアス =====

# 既存のクラス名との互換性を保つためのエイリアス
UnifiedConfigManager = ConfigManager  # 統一後のConfigManagerへのエイリアス
EnhancedConfig = ConfigManager  # core.config.config_manager.EnhancedConfig の代替
