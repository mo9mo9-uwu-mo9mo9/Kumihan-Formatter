"""統一設定バリデーター

Issue #771対応: 設定値の包括的検証と修正提案
Pydanticの検証機能を拡張し、Kumihan特有の検証ルールを実装
"""

# import re  # Removed: unused import

# import socket  # removed - unused import (F401)
from pathlib import Path
from typing import (  # Tuple, Union removed - unused imports (F401)
    Any,
    Dict,
    List,
    Optional,
)

from pydantic import ValidationError

from ..error_handling import handle_error_unified
from ..utilities.logger import get_logger
from .config_models import ErrorConfig, KumihanConfig, LoggingConfig, ParallelConfig


class ConfigValidationError(Exception):
    """設定検証エラー"""

    pass


class ValidationResult:
    """検証結果"""

    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.fixed_config: Optional[KumihanConfig] = None

    def add_error(self, message: str) -> None:
        """エラーを追加"""
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """警告を追加"""
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """提案を追加"""
        self.suggestions.append(message)

    def has_issues(self) -> bool:
        """何らかの問題があるかチェック"""
        return len(self.errors) > 0 or len(self.warnings) > 0


class ConfigValidator:
    """統一設定バリデーター

    Pydanticの基本検証に加えて、Kumihan特有の検証ルールを実装
    """

    def __init__(self, logger_name: str = __name__):
        self.logger = get_logger(logger_name)

    def validate_config(
        self, config_data: Dict[str, Any], auto_fix: bool = False
    ) -> ValidationResult:
        """設定の包括的検証

        Args:
            config_data: 検証する設定データ
            auto_fix: 自動修正を試行するか

        Returns:
            ValidationResult: 検証結果
        """
        result = ValidationResult()

        try:
            # 1. Pydanticレベルの基本検証
            config = KumihanConfig(**config_data)
            result.fixed_config = config

            # 2. Kumihan特有の検証ルール
            self._validate_parallel_config(config.parallel, result)
            self._validate_logging_config(config.logging, result)
            self._validate_error_config(config.error, result)
            self._validate_rendering_config(config.rendering, result)
            self._validate_ui_config(config.ui, result)

            # 3. 設定間の依存関係検証
            self._validate_config_dependencies(config, result)

            # 4. システム環境との整合性検証
            self._validate_system_compatibility(config, result)

            # 5. 自動修正処理
            if auto_fix and result.has_issues():
                result.fixed_config = self._apply_auto_fixes(config, result)

            if result.is_valid:
                self.logger.info("設定検証完了: 問題なし")
            else:
                self.logger.warning(
                    f"設定検証完了: {len(result.errors)}個のエラー、{len(result.warnings)}個の警告"
                )

        except ValidationError as e:
            # Pydantic検証エラーの処理
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = f"{field_path}: {error['msg']}"
                result.add_error(error_msg)

                # 修正提案の生成
                suggestion = self._generate_validation_suggestion(error)
                if suggestion:
                    result.add_suggestion(suggestion)

            # 統一エラーハンドリングでログ出力
            try:
                handle_error_unified(
                    e,
                    context={"validation_errors": len(e.errors())},
                    operation="config_validation",
                    component_name="ConfigValidator",
                )
            except Exception:
                pass  # エラーハンドリング自体のエラーは無視

        except Exception as e:
            result.add_error(f"設定検証中に予期しないエラー: {e}")
            self.logger.error(f"設定検証エラー: {e}", exc_info=True)

        return result

    def _validate_parallel_config(
        self, config: ParallelConfig, result: ValidationResult
    ) -> None:
        """並列処理設定の検証"""

        # CPUコア数との整合性チェック
        try:
            import multiprocessing

            cpu_count = multiprocessing.cpu_count()

            max_reasonable_chunks = cpu_count * 4  # CPUコア数の4倍まで
            if config.target_chunks_per_core * cpu_count > max_reasonable_chunks:
                result.add_warning(
                    f"チャンク数が多すぎる可能性があります "
                    f"(CPU{cpu_count}コア, {config.target_chunks_per_core}チャンク/コア)"
                )
                result.add_suggestion(
                    f"target_chunks_per_core を {max_reasonable_chunks // cpu_count} 以下に設定することを推奨"
                )

        except Exception:
            pass  # multiprocessing取得失敗は無視

        # メモリ設定の妥当性チェック
        if config.memory_critical_threshold_mb > 1024:  # 1GB
            result.add_warning("メモリクリティカルしきい値が非常に高く設定されています")
            result.add_suggestion("通常は500MB以下の設定を推奨")

        # タイムアウト設定の妥当性
        if config.processing_timeout_seconds < 60:
            result.add_warning("処理タイムアウトが短すぎる可能性があります")
            result.add_suggestion("大きなファイル処理を考慮して300秒以上を推奨")

    def _validate_logging_config(
        self, config: LoggingConfig, result: ValidationResult
    ) -> None:
        """ログ設定の検証"""

        # ログディレクトリの書き込み権限チェック
        try:
            config.log_dir.mkdir(parents=True, exist_ok=True)
            test_file = config.log_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()

        except PermissionError:
            result.add_error(
                f"ログディレクトリに書き込み権限がありません: {config.log_dir}"
            )
            result.add_suggestion(
                "ログディレクトリを書き込み可能な場所に変更してください"
            )

        except Exception as e:
            result.add_warning(f"ログディレクトリ検証でエラー: {e}")

        # バックアップ数の妥当性
        if config.log_backup_count > 365:
            result.add_warning("ログバックアップ数が多すぎます")
            result.add_suggestion("通常は30-90日分のバックアップで十分です")

        # ディスク容量への配慮
        if config.log_backup_count > 100:
            result.add_suggestion("多数のログファイルはディスク容量に注意してください")

    def _validate_error_config(
        self, config: ErrorConfig, result: ValidationResult
    ) -> None:
        """エラー設定の検証"""

        # エラー表示制限の妥当性
        if config.error_display_limit > 100:
            result.add_warning("エラー表示制限が多すぎます")
            result.add_suggestion("通常は10-20個程度の表示で十分です")

        # graceful_errorsとcontinue_on_errorの組み合わせ
        if config.graceful_errors and not config.continue_on_error:
            result.add_suggestion(
                "graceful_errorsを有効にする場合、continue_on_errorも有効にすることを推奨"
            )

        # カテゴリ別設定の検証
        for category, settings in config.category_settings.items():
            # カテゴリ別設定の詳細検証（必要に応じて実装）
            pass

    def _validate_rendering_config(
        self, config: Any, result: ValidationResult  # RenderingConfig
    ) -> None:
        """レンダリング設定の検証"""

        # CSS値の基本的な検証
        if not self._is_valid_css_value(config.max_width):
            result.add_error(f"無効なCSS値: max_width = {config.max_width}")
            result.add_suggestion("例: '800px', '90%', 'auto' など")

        # 色の値の検証
        if not self._is_valid_color(config.background_color):
            result.add_error(
                f"無効な色値: background_color = {config.background_color}"
            )
            result.add_suggestion("例: '#f9f9f9', 'white', 'rgb(255,255,255)' など")

        if not self._is_valid_color(config.container_background):
            result.add_error(
                f"無効な色値: container_background = {config.container_background}"
            )

        if not self._is_valid_color(config.text_color):
            result.add_error(f"無効な色値: text_color = {config.text_color}")

        # フォントファミリーの検証
        if not config.font_family.strip():
            result.add_error("フォントファミリーが空です")
            result.add_suggestion("デフォルトのフォントファミリーを設定してください")

    def _validate_ui_config(
        self, config: Any, result: ValidationResult
    ) -> None:  # UIConfig
        """UI設定の検証"""

        # プレビューブラウザの検証
        if config.preview_browser:
            if not self._is_valid_browser_command(config.preview_browser):
                result.add_warning(
                    f"指定されたブラウザが見つからない可能性があります: {config.preview_browser}"
                )
                result.add_suggestion(
                    "システムにインストールされているブラウザを指定してください"
                )

        # 監視間隔の妥当性
        if config.watch_interval < 0.1:
            result.add_error("ファイル監視間隔が短すぎます")
            result.add_suggestion("0.1秒以上の間隔を設定してください")

        if config.watch_interval > 60:
            result.add_warning("ファイル監視間隔が長すぎます")
            result.add_suggestion("通常は1-5秒程度が適切です")

    def _validate_config_dependencies(
        self, config: KumihanConfig, result: ValidationResult
    ) -> None:
        """設定間の依存関係検証"""

        # デバッグモードとログレベルの整合性
        if config.debug_mode and config.logging.log_level.value not in [
            "DEBUG",
            "INFO",
        ]:
            result.add_suggestion(
                "デバッグモード時はログレベルをDEBUGまたはINFOに設定することを推奨"
            )

        # エラー処理とログ設定の整合性
        if config.error.graceful_errors and config.logging.log_level.value == "ERROR":
            result.add_suggestion(
                "graceful_errorsを使用する場合、詳細なログのためINFOレベルを推奨"
            )

        # 並列処理とメモリ設定の整合性
        estimated_memory_mb = (
            config.parallel.max_chunk_size
            * config.parallel.target_chunks_per_core
            * 4  # 推定メモリ使用量
        ) // 1024

        if estimated_memory_mb > config.parallel.memory_warning_threshold_mb:
            result.add_warning("並列処理設定がメモリ制限を超える可能性があります")
            result.add_suggestion(
                f"メモリしきい値を{estimated_memory_mb}MB以上に設定するか、チャンクサイズを小さくしてください"
            )

    def _validate_system_compatibility(
        self, config: KumihanConfig, result: ValidationResult
    ) -> None:
        """システム環境との整合性검証"""

        # Python版本检证
        import sys

        if sys.version_info < (3, 8):
            result.add_error("Python 3.8以上が必要です")

        # 可用的内存检证
        try:
            import psutil

            available_memory_mb = psutil.virtual_memory().available // (1024 * 1024)

            if config.parallel.memory_critical_threshold_mb > available_memory_mb * 0.8:
                result.add_warning(
                    "メモリクリティカルしきい値がシステムメモリに対して高すぎます"
                )
                result.add_suggestion(
                    f"利用可能メモリ{available_memory_mb}MBに対してより低い値を設定してください"
                )

        except ImportError:
            result.add_suggestion(
                "より正確なメモリ検証のためpsutilのインストールを推奨"
            )

    def _apply_auto_fixes(
        self, config: KumihanConfig, result: ValidationResult
    ) -> KumihanConfig:
        """自動修正を適用

        Args:
            config: 元の設定
            result: 検証結果

        Returns:
            KumihanConfig: 修正された設定
        """
        fixed_config = config.copy(deep=True)

        # ログディレクトリの修正
        if not fixed_config.logging.log_dir.exists():
            try:
                fixed_config.logging.log_dir = Path.home() / ".kumihan" / "logs"
                result.add_suggestion(
                    "ログディレクトリをユーザーホームディレクトリに変更しました"
                )
            except Exception:
                pass

        # メモリしきい値の調整
        if (
            fixed_config.parallel.memory_critical_threshold_mb
            <= fixed_config.parallel.memory_warning_threshold_mb
        ):
            fixed_config.parallel.memory_critical_threshold_mb = (
                fixed_config.parallel.memory_warning_threshold_mb + 50
            )
            result.add_suggestion(
                "メモリクリティカルしきい値を警告しきい値より高く調整しました"
            )

        return fixed_config

    def _is_valid_css_value(self, value: str) -> bool:
        """CSS値の妥当性チェック"""
        if not value or not isinstance(value, str):
            return False

    def _is_valid_color(self, value: str) -> bool:
        """色値の妥当性チェック"""
        if not value or not isinstance(value, str):
            return False

        # 基本的な色名をチェック
        basic_colors = {
            "red",
            "blue",
            "green",
            "yellow",
            "black",
            "white",
            "gray",
            "orange",
            "purple",
            "pink",
            "brown",
        }

        return value in basic_colors

    def _is_valid_browser_command(self, command: str) -> bool:
        """ブラウザコマンドの妥当性チェック"""
        if not command or not isinstance(command, str):
            return False

    def _generate_validation_suggestion(self, error: Any) -> Optional[str]:
        """Pydantic検証エラーから修正提案を生成

        Args:
            error: Pydantic検証エラー情報 (ErrorDetails in Pydantic v2)

        Returns:
            Optional[str]: 修正提案
        """
        error_type = error.get("type", "")
        field = error.get("loc", [""])[-1] if error.get("loc") else ""

        suggestions = {
            "value_error.number.not_ge": f"{field}にはより大きな値を設定してください",
            "value_error.number.not_le": f"{field}にはより小さな値を設定してください",
            "type_error.bool": f"{field}にはtrue/falseを設定してください",
            "type_error.integer": f"{field}には整数を設定してください",
            "type_error.float": f"{field}には数値を設定してください",
            "type_error.str": f"{field}には文字列を設定してください",
            "value_error.missing": f"{field}は必須項目です",
        }

        return suggestions.get(error_type)
