"""
変換コマンド - メイン制御

変換コマンドの実行制御とオーケストレーションの責任を担当
Issue #319対応 - convert.py から分離
"""

import sys
import webbrowser

from ...core.error_handling import ErrorHandler as FriendlyErrorHandler
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
        self.friendly_error_handler = FriendlyErrorHandler(console_ui=get_console_ui())
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

        Returns:
            None: プログラム終了時のみ
        """
        self.logger.info(
            f"Starting conversion: input_file='{input_file}', output='{output}'"
        )
        self.logger.debug(
            f"Options: no_preview={no_preview}, watch={watch}, syntax_check={syntax_check}"
        )

        try:
            # 入力ファイルの検証
            self.logger.debug("Validating input file")
            input_path = self.validator.validate_input_file(input_file)  # type: ignore
            self.logger.info(f"Input file validated: {input_path}")

            # ファイルサイズチェック
            if not self.validator.check_file_size(input_path):
                self.logger.info("User cancelled processing due to large file size")
                sys.exit(0)  # ユーザーが処理を中断

            # 設定ファイルは簡素化のため使用しない
            config_obj = None

            get_console_ui().processing_start("読み込み中", str(input_path))
            self.logger.debug(f"Started processing file: {input_path}")

            # 構文チェック（有効な場合）
            if syntax_check:
                self.logger.info("Performing syntax check")
                error_report = self.validator.perform_syntax_check(input_path)

                if error_report.has_errors():
                    # エラーが見つかった場合は変換を中止
                    self.logger.error(
                        f"Syntax errors found: {error_report.error_count} errors"  # type: ignore
                    )
                    get_console_ui().error(
                        "記法エラーが検出されました。変換を中止します。"
                    )
                    get_console_ui().info("\n=== 詳細エラーレポート ===")
                    print(error_report.to_console_output())

                    # エラーレポートファイルを生成
                    self.validator.save_error_report(error_report, input_path, output)
                    self.logger.info("Error report saved")

                    get_console_ui().dim(
                        "--no-syntax-check オプションで記法チェックをスキップできます"
                    )
                    sys.exit(1)

                elif error_report.has_warnings():
                    # 警告のみの場合は続行するが表示
                    self.logger.warning(
                        f"Syntax warnings found: {error_report.warning_count} warnings"  # type: ignore
                    )
                    get_console_ui().warning("記法に関する警告があります:")
                    print(error_report.to_console_output())

            # ファイル変換実行
            self.logger.info("Starting file conversion")
            output_file = self.processor.convert_file(
                input_path,
                output,
                config_obj,
                show_test_cases=show_test_cases,
                template=template_name,
                include_source=include_source,
            )
            self.logger.info(f"Conversion completed: {output_file}")

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

    def _handle_file_error(self, e: FileNotFoundError, input_file: str | None) -> None:
        """ファイル未発見エラーの処理"""
        error = self.friendly_error_handler.handle_exception(
            e, context={"file_path": input_file or ""}
        )
        self.friendly_error_handler.display_error(error, verbose=True)
        sys.exit(1)

    def _handle_encoding_error(
        self, e: UnicodeDecodeError, input_file: str | None
    ) -> None:
        """文字エンコーディングエラーの処理"""
        error = self.friendly_error_handler.handle_exception(
            e, context={"file_path": input_file or ""}
        )
        self.friendly_error_handler.display_error(error, verbose=True)
        sys.exit(1)

    def _handle_permission_error(
        self, e: PermissionError, input_file: str | None
    ) -> None:
        """ファイル権限エラーの処理"""
        error = self.friendly_error_handler.handle_exception(
            e, context={"file_path": input_file or "", "operation": "読み取り"}
        )
        self.friendly_error_handler.display_error(error, verbose=True)
        sys.exit(1)

    def _handle_generic_error(self, e: Exception, input_file: str | None) -> None:
        """一般的なエラーの処理"""
        error = self.friendly_error_handler.handle_exception(
            e, context={"input_file": input_file, "operation": "ファイル変換"}
        )
        self.friendly_error_handler.display_error(error, verbose=True)
        sys.exit(1)
