"""
変換コマンド - メイン制御

変換コマンドの実行制御とオーケストレーションの責任を担当
Issue #319対応 - convert.py から分離
"""

import sys
import webbrowser

# Error handling removed during cleanup - using basic error handling
from ...core.utilities.logger import get_logger
from ...ui.console_ui import get_console_ui
from .convert_processor import ConvertProcessor
from .convert_validator import ConvertValidator
from .convert_watcher import ConvertWatcher


class ConvertCommand:
    """変換コマンド実行クラス

    責任: 変換処理全体のオーケストレーション・エラーハンドリング
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.validator = ConvertValidator()
        self.processor = ConvertProcessor()
        self.watcher = ConvertWatcher(self.processor, self.validator)
        # Error handler removed during cleanup - using basic error handling
        self.friendly_error_handler = None
        self.logger.debug("ConvertCommand initialized")

    def execute(
        self,
        input_file: str | None,
        output: str,
        no_preview: bool,
        watch: bool,
        config: str | None,
        show_test_cases: bool,
        template_name: str | None,
        include_source: bool,
        syntax_check: bool = True,
        progress_level: str = "detailed",
        show_progress_tooltip: bool = True,
        enable_cancellation: bool = True,
        progress_style: str = "bar",
        progress_log: str | None = None,
        continue_on_error: bool = False,
        graceful_errors: bool = False,
        # Phase3: 設定可能なエラー処理レベル
        error_level: str = "normal",
        no_suggestions: bool = False,
        no_statistics: bool = False,
    ) -> None:
        """
        変換コマンドを実行

        Args:
            input_file: 入力ファイルパス
            output: 出力ディレクトリ
            no_preview: ブラウザプレビューをスキップ
            watch: ファイル監視モードを有効化
            config: 設定ファイルパス（廃止予定 - 無視）
            show_test_cases: テストケースを表示
            template_name: 使用するテンプレート名
            include_source: ソース表示を含める
            syntax_check: 変換前の構文チェックを有効化
            progress_level: プログレス表示レベル (silent/minimal/detailed/verbose)
            show_progress_tooltip: プログレスツールチップ表示を有効化
            enable_cancellation: キャンセル機能を有効化
            progress_style: プログレス表示スタイル (bar/spinner/percentage)
            progress_log: プログレスログ出力先ファイル
            continue_on_error: Issue #700: 記法エラーが発生してもHTML生成を継続
            graceful_errors: Issue #700: エラー情報をHTMLに埋め込んで表示
            error_level: Phase3: エラー処理レベル (strict/normal/lenient/ignore)
            no_suggestions: Phase3: エラー修正提案を非表示
            no_statistics: Phase3: エラー統計を非表示

        Returns:
            None: プログラム終了時のみ
        """
        self.logger.info(
            f"Starting conversion: input_file='{input_file}', output='{output}'"
        )
        self.logger.debug(
            f"Options: no_preview={no_preview}, watch={watch}, "
            f"syntax_check={syntax_check}, continue_on_error={continue_on_error}, "
            f"graceful_errors={graceful_errors}, error_level={error_level}"
        )

        try:
            # エラー処理設定の初期化
            error_config_manager = self._initialize_error_config(
                input_file,
                error_level,
                graceful_errors,
                continue_on_error,
                no_suggestions,
                no_statistics,
            )

            # 入力ファイルの検証
            input_path = self._validate_input_file(input_file)

            # 変換前の構文チェック
            if syntax_check:
                self._perform_syntax_check(
                    input_path, error_config_manager, error_level, output
                )

            # ファイル変換実行
            output_file = self._execute_conversion(
                input_path,
                output,
                show_test_cases,
                template_name,
                include_source,
                progress_level,
                show_progress_tooltip,
                enable_cancellation,
                progress_style,
                progress_log,
                error_config_manager,
            )

            # 後処理（プレビュー・監視モード）
            self._handle_post_processing(
                output_file,
                no_preview,
                watch,
                input_file,
                output,
                None,
                show_test_cases,
                template_name,
                include_source,
                syntax_check,
            )

            # 正常終了
            sys.exit(0)

        except FileNotFoundError as e:
            self.logger.error(f"File not found: {e}")
            self._handle_file_error(e, input_file)
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error: {e}")
            self._handle_encoding_error(e, input_file)
        except PermissionError as e:
            self.logger.error(f"Permission error: {e}")
            self._handle_permission_error(e, input_file)
        except Exception as e:
            self.logger.error(f"Unexpected error during conversion: {e}", exc_info=True)
            self._handle_generic_error(e, input_file)

    def _initialize_error_config(
        self,
        input_file: str | None,
        error_level: str,
        graceful_errors: bool,
        continue_on_error: bool,
        no_suggestions: bool,
        no_statistics: bool,
    ):
        """エラー処理設定の初期化"""
        from pathlib import Path

        from ...core.error_analysis.error_config import ErrorConfigManager

        error_config_manager = ErrorConfigManager(
            config_dir=Path(input_file).parent if input_file else Path.cwd()
        )

        # CLIオプションを設定に適用
        error_config_manager.apply_cli_options(
            error_level=error_level,
            graceful_errors=graceful_errors,
            continue_on_error=continue_on_error,
            show_suggestions=not no_suggestions,
            show_statistics=not no_statistics,
        )

        return error_config_manager

    def _validate_input_file(self, input_file: str | None):
        """入力ファイルの検証"""
        self.logger.debug("Validating input file")
        input_path = self.validator.validate_input_file(input_file)  # type: ignore
        self.logger.info(f"Input file validated: {input_path}")

        # ファイルサイズチェック
        if not self.validator.check_file_size(input_path):
            self.logger.info("User cancelled processing due to large file size")
            sys.exit(0)  # ユーザーが処理を中断

        get_console_ui().processing_start("読み込み中", str(input_path))
        self.logger.debug(f"Started processing file: {input_path}")

        return input_path

    def _perform_syntax_check(
        self, input_path, error_config_manager, error_level: str, output: str
    ):
        """構文チェックの実行"""
        self.logger.info("Performing syntax check")
        error_report = self.validator.perform_syntax_check(input_path)

        if error_report.get("has_errors", False):
            self._handle_syntax_errors(
                error_report, error_config_manager, error_level, input_path, output
            )
        elif error_report.get("has_warnings", False):
            self._handle_syntax_warnings(error_report)

    def _handle_syntax_errors(
        self,
        error_report,
        error_config_manager,
        error_level: str,
        input_path,
        output: str,
    ):
        """構文エラーの処理"""
        errors = error_report.get("errors", [])
        should_continue = error_config_manager.should_continue_on_error(
            "syntax_error", len(errors)
        )

        if should_continue:
            self._handle_continuable_syntax_errors(
                errors, error_config_manager, error_level
            )
        else:
            self._handle_blocking_syntax_errors(
                errors, error_level, input_path, output, error_report
            )

    def _handle_continuable_syntax_errors(
        self, errors, error_config_manager, error_level: str
    ):
        """継続可能な構文エラーの処理"""
        self.logger.warning(
            f"Syntax errors found but continuing (level={error_level}): {len(errors)} errors"
        )
        get_console_ui().warning(
            f"記法エラーが検出されましたが、処理を継続します (レベル: {error_level})。"
        )

        if error_config_manager.config.graceful_errors:
            get_console_ui().info("エラー情報はHTML内に埋め込まれます。")

        # エラー詳細を表示（設定に応じて）
        if error_config_manager.config.show_suggestions:
            self._display_error_details(errors, error_config_manager)

    def _handle_blocking_syntax_errors(
        self, errors, error_level: str, input_path, output: str, error_report
    ):
        """ブロッキング構文エラーの処理"""
        self.logger.error(
            f"Syntax errors found, stopping (level={error_level}): {len(errors)} errors"
        )
        get_console_ui().error(
            f"記法エラーが検出されました。変換を中止します (レベル: {error_level})。"
        )
        get_console_ui().info("\\n=== 詳細エラーレポート ===")
        for error in errors:
            print(f"  エラー: {error.get('message', 'Unknown error')}")

        # エラーレポートファイルを生成
        self.validator.save_error_report(error_report, input_path, output)
        self.logger.info("Error report saved")

        get_console_ui().dim(
            "--error-level lenient または --continue-on-error で"
            "エラーがあっても処理を継続できます"
        )
        sys.exit(1)

    def _display_error_details(self, errors, error_config_manager):
        """エラー詳細の表示"""
        get_console_ui().info("\\n=== 検出されたエラー ===")
        for error in errors:
            severity = error_config_manager.get_error_severity("syntax_error")
            icon = (
                "❌" if severity == "error" else "⚠️" if severity == "warning" else "ℹ️"
            )
            print(f"  {icon} {error.get('message', 'Unknown error')}")

    def _handle_syntax_warnings(self, error_report):
        """構文警告の処理"""
        warnings_count = len(error_report.get("warnings", []))
        self.logger.warning(f"Syntax warnings found: {warnings_count} warnings")
        get_console_ui().warning("記法に関する警告があります:")

        # 警告の詳細表示（警告があれば）
        for warning in error_report.get("warnings", []):
            print(f"  警告: {warning.get('message', 'Unknown warning')}")

    def _execute_conversion(
        self,
        input_path,
        output: str,
        show_test_cases: bool,
        template_name: str | None,
        include_source: bool,
        progress_level: str,
        show_progress_tooltip: bool,
        enable_cancellation: bool,
        progress_style: str,
        progress_log: str | None,
        error_config_manager,
    ):
        """ファイル変換の実行"""
        self.logger.info("Starting file conversion with enhanced progress management")

        # Phase3: エラー設定から実際の値を取得
        effective_continue_on_error = error_config_manager.config.continue_on_error
        effective_graceful_errors = error_config_manager.config.graceful_errors

        output_file = self.processor.convert_file(
            input_path,
            output,
            None,  # config_obj は簡素化のため使用しない
            show_test_cases=show_test_cases,
            template=template_name,
            include_source=include_source,
            progress_level=progress_level,
            show_progress_tooltip=show_progress_tooltip,
            enable_cancellation=enable_cancellation,
            progress_style=progress_style,
            progress_log=progress_log,
            continue_on_error=effective_continue_on_error,
            graceful_errors=effective_graceful_errors,
            # Phase3: エラー設定管理を渡す
            error_config_manager=error_config_manager,
        )
        self.logger.info(f"Conversion completed: {output_file}")
        return output_file

    def _handle_post_processing(
        self,
        output_file,
        no_preview: bool,
        watch: bool,
        input_file: str | None,
        output: str,
        config_obj,
        show_test_cases: bool,
        template_name: str | None,
        include_source: bool,
        syntax_check: bool,
    ):
        """後処理（プレビュー・監視モード）"""
        # ブラウザプレビュー
        if not no_preview:
            self.logger.debug("Opening browser preview")
            get_console_ui().browser_opening()
            webbrowser.open(output_file.resolve().as_uri())

        # ファイル監視モード
        if watch:
            self.logger.info("Starting watch mode")
            self.watcher.start_watch_mode(
                input_file,  # type: ignore
                output,
                config_obj,
                show_test_cases,
                template_name,
                include_source,
                syntax_check,
            )

    def _handle_file_error(self, e: FileNotFoundError, input_file: str | None) -> None:
        """ファイル未発見エラーの処理"""
        # Basic error handling - friendly error handler removed
        self.logger.error(f"File not found: {e}")
        print(f"エラー: ファイルが見つかりません - {input_file or 'Unknown'}")
        sys.exit(1)

    def _handle_encoding_error(
        self, e: UnicodeDecodeError, input_file: str | None
    ) -> None:
        """文字エンコーディングエラーの処理"""
        # Basic error handling - friendly error handler removed
        self.logger.error(f"Encoding error: {e}")
        print(f"エラー: 文字エンコーディングエラー - {input_file or 'Unknown'}")
        sys.exit(1)

    def _handle_permission_error(
        self, e: PermissionError, input_file: str | None
    ) -> None:
        """ファイル権限エラーの処理"""
        # Basic error handling - friendly error handler removed
        self.logger.error(f"Permission error: {e}")
        print(f"エラー: ファイル権限エラー - {input_file or 'Unknown'}")
        sys.exit(1)

    def _handle_generic_error(self, e: Exception, input_file: str | None) -> None:
        """一般的なエラーの処理"""
        # Basic error handling - friendly error handler removed
        self.logger.error(f"Generic error: {e}")
        print(f"エラー: {e}")
        sys.exit(1)
