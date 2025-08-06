"""統一設定管理マネージャー

Issue #771対応: 分散した設定管理を統合し、
一元的な設定読み込み・管理・ホットリロード機能を提供

統一設定管理の中核クラス
"""

# import os  # removed - unused import (F401)
import threading

# import time  # removed - unused import (F401)
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..error_handling import handle_error_unified
from ..utilities.logger import get_logger
from .config_loader import ConfigLoader, ConfigLoadError
from .config_models import (
    ConfigFormat,
    ErrorConfig,
    KumihanConfig,
    LoggingConfig,
    LogLevel,
    ParallelConfig,
    RenderingConfig,
    UIConfig,
)
from .config_validator import (  # ValidationResult removed - unused import (F401)
    ConfigValidator,
)


class UnifiedConfigManager:
    """統一設定管理マネージャー

    全設定の一元管理を提供:
    - 設定読み込み (環境変数・ファイル・デフォルト)
    - 設定検証・自動修正
    - ホットリロード機能
    - 既存設定クラスとの互換性
    """

    def __init__(
        self,
        config_file: Optional[Union[str, Path]] = None,
        auto_reload: bool = False,
        validation_enabled: bool = True,
    ):
        """統一設定マネージャー初期化

        Args:
            config_file: 設定ファイルパス
            auto_reload: ホットリロード有効
            validation_enabled: 設定検証有効
        """
        self.logger = get_logger(__name__)

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

        # 初期設定読み込み
        self._load_initial_config(config_file)

        # ホットリロード開始
        if self._auto_reload and self._config_file_path:
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
                self._config_file_path = self.loader.find_config_file()

            # 2. 設定データの収集・マージ
            config_data = self._collect_config_data()

            # 3. 設定の作成・検証
            self._config = self._create_and_validate_config(config_data)

            # 4. ファイル監視情報の更新
            if self._config_file_path and self._config_file_path.exists():
                self._last_modified = self._config_file_path.stat().st_mtime
                self._config.config_file_path = self._config_file_path

            self._config.last_updated = datetime.now().isoformat()

            self.logger.info("統一設定管理システム初期化完了")
            if self._config_file_path:
                self.logger.info(f"設定ファイル: {self._config_file_path}")

        except Exception as e:
            self.logger.error(f"設定初期化エラー: {e}", exc_info=True)

            # エラー時はデフォルト設定を使用
            self._config = KumihanConfig()
            self.logger.info("デフォルト設定を使用します")

            # 統一エラーハンドリング
            try:
                handle_error_unified(
                    e,
                    context={"config_file": str(config_file) if config_file else None},
                    operation="config_initialization",
                    component_name="UnifiedConfigManager",
                )
            except Exception:
                pass  # エラーハンドリング自体のエラーは無視

    def _collect_config_data(self) -> Dict[str, Any]:
        """設定データの収集・マージ

        優先順位: 環境変数 > 設定ファイル > デフォルト

        Returns:
            Dict[str, Any]: マージされた設定データ
        """
        configs = []

        # 1. 設定ファイルからの読み込み
        if self._config_file_path and self._config_file_path.exists():
            try:
                file_config = self.loader.load_from_file(self._config_file_path)
                configs.append(file_config)
                self.logger.debug(f"設定ファイル読み込み: {len(file_config)}項目")

            except ConfigLoadError as e:
                self.logger.error(f"設定ファイル読み込みエラー: {e}")

        # 2. 環境変数からの読み込み
        env_config = self.loader.load_from_environment()
        if env_config:
            configs.append(env_config)
            self.logger.debug(f"環境変数読み込み: {len(env_config)}項目")

        # 3. 設定のマージ
        merged_config = self.loader.merge_configs(*configs)

        return merged_config

    def _create_and_validate_config(self, config_data: Dict[str, Any]) -> KumihanConfig:
        """設定の作成・検証

        Args:
            config_data: 設定データ

        Returns:
            KumihanConfig: 検証済み設定
        """
        if self.validator:
            # 設定検証実行
            validation_result = self.validator.validate_config(
                config_data, auto_fix=True
            )

            if validation_result.errors:
                self.logger.error("設定検証エラー:")
                for error in validation_result.errors:
                    self.logger.error(f"  - {error}")

            if validation_result.warnings:
                self.logger.warning("設定検証警告:")
                for warning in validation_result.warnings:
                    self.logger.warning(f"  - {warning}")

            if validation_result.suggestions:
                self.logger.info("設定改善提案:")
                for suggestion in validation_result.suggestions:
                    self.logger.info(f"  - {suggestion}")

            # 修正された設定を使用
            if validation_result.fixed_config:
                return validation_result.fixed_config

        # 検証なしまたは検証失敗時は基本作成
        try:
            # 無効なフィールド（extra="forbid"対応）を除去して再試行
            cleaned_config_data = self._clean_config_data(config_data)
            return KumihanConfig(**cleaned_config_data)
        except Exception as e:
            self.logger.error(f"設定作成エラー: {e}")
            # 最後の手段：有効なフィールドのみでデフォルト設定作成
            return self._create_fallback_config(config_data)

    def _clean_config_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """無効なフィールドを除去した設定データを作成"""
        # KumihanConfigで有効なフィールドのリスト
        valid_fields = {
            "parallel",
            "logging",
            "error",
            "rendering",
            "ui",
            "config_version",
            "config_file_path",
            "last_updated",
            "environment",
            "debug_mode",
        }

        cleaned_data = {}
        for key, value in config_data.items():
            if key in valid_fields:
                cleaned_data[key] = value
            else:
                self.logger.warning(f"無効なフィールドをスキップ: {key}")

        return cleaned_data

    def _create_fallback_config(self, config_data: Dict[str, Any]) -> KumihanConfig:
        """フォールバック設定を作成（有効な値のみを適用）"""
        config = KumihanConfig()  # デフォルト設定で開始

        # 有効な設定のみを適用
        try:
            if "debug_mode" in config_data:
                config.debug_mode = config_data["debug_mode"]
            if "environment" in config_data:
                config.environment = config_data["environment"]
            if "parallel" in config_data:
                for key, value in config_data["parallel"].items():
                    if hasattr(config.parallel, key):
                        setattr(config.parallel, key, value)
            if "logging" in config_data:
                for key, value in config_data["logging"].items():
                    if hasattr(config.logging, key):
                        if key == "log_level":
                            # 文字列をLogLevelに変換
                            config.logging.log_level = (
                                LogLevel(value) if isinstance(value, str) else value
                            )
                        else:
                            setattr(config.logging, key, value)
        except Exception as e:
            self.logger.warning(f"フォールバック設定作成中の警告: {e}")

        return config  # デフォルト設定

    def get_config(self) -> KumihanConfig:
        """現在の統一設定を取得

        Returns:
            KumihanConfig: 現在の設定
        """
        if self._config is None:
            self.logger.warning("設定が初期化されていません、デフォルト設定を返します")
            return KumihanConfig()

        return self._config

    def reload_config(self, force: bool = False) -> bool:
        """設定の再読み込み

        Args:
            force: 強制再読み込み

        Returns:
            bool: 再読み込み成功
        """
        try:
            # ファイル更新チェック
            if not force and self._config_file_path and self._config_file_path.exists():
                current_mtime = self._config_file_path.stat().st_mtime
                if self._last_modified and current_mtime <= self._last_modified:
                    return False  # 更新なし

            self.logger.info("設定を再読み込みしています...")

            # 設定データの再収集
            config_data = self._collect_config_data()

            # 新しい設定の作成・検証
            new_config = self._create_and_validate_config(config_data)

            # 設定の更新
            # old_config = self._config  # removed - unused variable (F841)
            self._config = new_config

            # ファイル監視情報の更新
            if self._config_file_path and self._config_file_path.exists():
                self._last_modified = self._config_file_path.stat().st_mtime
                self._config.config_file_path = self._config_file_path

            self._config.last_updated = datetime.now().isoformat()

            # コールバック実行
            self._execute_reload_callbacks(self._config)

            self.logger.info("設定再読み込み完了")
            return True

        except Exception as e:
            self.logger.error(f"設定再読み込みエラー: {e}", exc_info=True)

            # 統一エラーハンドリング
            try:
                handle_error_unified(
                    e,
                    context={
                        "config_file": (
                            str(self._config_file_path)
                            if self._config_file_path
                            else None
                        )
                    },
                    operation="config_reload",
                    component_name="UnifiedConfigManager",
                )
            except Exception:
                pass

            return False

    def save_config(
        self,
        config_path: Optional[Union[str, Path]] = None,
        format: Optional[ConfigFormat] = None,
    ) -> bool:
        """設定をファイルに保存

        Args:
            config_path: 保存先パス (Noneの場合は現在のファイル)
            format: 保存形式

        Returns:
            bool: 保存成功
        """
        if self._config is None:
            self.logger.error("保存する設定がありません")
            return False

        try:
            save_path = Path(config_path) if config_path else self._config_file_path

            if save_path is None:
                save_path = Path.home() / ".kumihan" / "kumihan.yaml"
                self.logger.info(
                    f"保存先が指定されていないため、デフォルトパスを使用: {save_path}"
                )

            self.loader.save_config(self._config, save_path, format)

            # 保存したファイルを監視対象に設定
            if not self._config_file_path:
                self._config_file_path = save_path
                if self._auto_reload:
                    self._start_auto_reload()

            self.logger.info(f"設定保存完了: {save_path}")
            return True

        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}", exc_info=True)
            return False

    def add_reload_callback(self, callback: Callable[[KumihanConfig], None]) -> None:
        """設定再読み込み時のコールバックを追加

        Args:
            callback: コールバック関数
        """
        self._reload_callbacks.append(callback)
        self.logger.debug(f"リロードコールバック追加: {len(self._reload_callbacks)}個")

    def _execute_reload_callbacks(self, new_config: KumihanConfig) -> None:
        """リロードコールバックを実行

        Args:
            new_config: 新しい設定
        """
        for callback in self._reload_callbacks:
            try:
                callback(new_config)
            except Exception as e:
                self.logger.error(f"リロードコールバック実行エラー: {e}", exc_info=True)

    def _start_auto_reload(self) -> None:
        """ホットリロード開始"""
        if self._reload_thread and self._reload_thread.is_alive():
            return  # 既に実行中

        self._shutdown_event.clear()
        self._reload_thread = threading.Thread(
            target=self._auto_reload_worker, name="ConfigAutoReload", daemon=True
        )
        self._reload_thread.start()

        self.logger.info("設定ホットリロード開始")

    def _auto_reload_worker(self) -> None:
        """ホットリロードワーカー"""
        while not self._shutdown_event.is_set():
            try:
                if self.reload_config():
                    self.logger.debug("設定ファイル更新検出・再読み込み完了")

                # 1秒間隔でチェック
                self._shutdown_event.wait(1.0)

            except Exception as e:
                self.logger.error(f"ホットリロードエラー: {e}", exc_info=True)
                self._shutdown_event.wait(5.0)  # エラー時は5秒待機

    def shutdown(self) -> None:
        """統一設定管理システムのシャットダウン"""
        self.logger.info("統一設定管理システムをシャットダウンしています...")

        # ホットリロード停止
        if self._reload_thread and self._reload_thread.is_alive():
            self._shutdown_event.set()
            self._reload_thread.join(timeout=5.0)

        self.logger.info("統一設定管理システムシャットダウン完了")

    def __del__(self):
        """デストラクタ"""
        try:
            self.shutdown()
        except Exception:
            pass  # デストラクタでのエラーは無視

    # 既存設定クラス互換メソッド

    def get_parallel_config(self) -> ParallelConfig:
        """並列処理設定を取得 (ParallelProcessingConfig互換)

        Returns:
            ParallelConfig: 並列処理設定
        """
        return self.get_config().parallel

    def get_logging_config(self) -> LoggingConfig:
        """ログ設定を取得

        Returns:
            LoggingConfig: ログ設定
        """
        return self.get_config().logging

    def get_error_config(self) -> ErrorConfig:
        """エラー処理設定を取得 (ErrorConfigManager互換)

        Returns:
            ErrorConfig: エラー処理設定
        """
        return self.get_config().error

    def get_rendering_config(self) -> RenderingConfig:
        """レンダリング設定を取得 (BaseConfig互換)

        Returns:
            RenderingConfig: レンダリング設定
        """
        return self.get_config().rendering

    def get_ui_config(self) -> UIConfig:
        """UI設定を取得

        Returns:
            UIConfig: UI設定
        """
        return self.get_config().ui


# グローバル統一設定マネージャー
_global_config_manager: Optional[UnifiedConfigManager] = None
_config_lock = threading.Lock()


def get_unified_config_manager(
    config_file: Optional[Union[str, Path]] = None,
    auto_reload: bool = False,
    force_reload: bool = False,
) -> UnifiedConfigManager:
    """グローバル統一設定マネージャーを取得

    Args:
        config_file: 設定ファイルパス
        auto_reload: ホットリロード有効
        force_reload: 強制再作成

    Returns:
        UnifiedConfigManager: 統一設定マネージャー
    """
    global _global_config_manager

    with _config_lock:
        if _global_config_manager is None or force_reload:
            _global_config_manager = UnifiedConfigManager(
                config_file=config_file, auto_reload=auto_reload
            )

        return _global_config_manager


def get_unified_config() -> KumihanConfig:
    """グローバル統一設定を取得

    Returns:
        KumihanConfig: 統一設定
    """
    return get_unified_config_manager().get_config()


def reload_unified_config() -> bool:
    """グローバル統一設定を再読み込み

    Returns:
        bool: 再読み込み成功
    """
    return get_unified_config_manager().reload_config(force=True)
