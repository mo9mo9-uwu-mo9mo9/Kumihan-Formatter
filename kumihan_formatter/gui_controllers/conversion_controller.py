"""Conversion operations controller for Kumihan-Formatter GUI

Single Responsibility Principle適用: 変換処理制御の分離
Issue #476 Phase2対応 - gui_controller.py分割（2/3）
"""

import threading
import webbrowser
from pathlib import Path
from tkinter import messagebox
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..gui_models import AppState
    from ..gui_views import MainView

# デバッグロガーのインポート
try:
    from ..core.debug_logger import (
        error,
        info,
        log_gui_event,
    )
except ImportError:
    # Fallbacksを定義
    def error(*args: Any, **kwargs: Any) -> None:
        pass

    def info(*args: Any, **kwargs: Any) -> None:
        pass

    def log_gui_event(*args: Any, **kwargs: Any) -> None:
        pass


# コマンドクラスのインポート
try:
    from ..commands.convert.convert_command import ConvertCommand
    from ..commands.sample import SampleCommand
except ImportError:
    try:
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand
        from kumihan_formatter.commands.sample import SampleCommand
    except ImportError as e:
        error(f"Failed to import command classes: {e}")
        ConvertCommand = None  # type: ignore
        SampleCommand = None  # type: ignore


class ConversionController:
    """変換処理制御クラス

    ファイル変換・サンプル生成・プレビュー処理を担当
    """

    def __init__(self, app_state: "AppState", main_view: "MainView") -> None:
        """変換コントローラーの初期化"""
        self.app_state = app_state
        self.main_view = main_view

    def convert_file(self) -> None:
        """ファイル変換の実行"""
        log_gui_event("button_click", "convert_file")

        # 変換準備チェック
        is_ready, message = self.app_state.is_ready_for_conversion()
        if not is_ready:
            messagebox.showerror("エラー", message)
            return

        # UI無効化
        self.main_view.set_ui_enabled(False)

        # 変換スレッド開始
        thread = threading.Thread(target=self._convert_file_thread)
        thread.daemon = True
        thread.start()

    def _convert_file_thread(self) -> None:
        """ファイル変換スレッド"""
        try:
            self.main_view.log_frame.add_message("変換を開始します...")
            self.app_state.conversion_state.update_progress(0, "変換準備中...")

            # 変換パラメータ取得
            params = self.app_state.config.get_conversion_params()
            self.app_state.conversion_state.update_progress(20, "設定を読み込み中...")

            # 変換実行
            if ConvertCommand is None:
                raise ImportError("ConvertCommand が利用できません")

            convert_command = ConvertCommand()
            self.app_state.conversion_state.update_progress(40, "ファイルを変換中...")

            convert_command.execute(**params)
            self.app_state.conversion_state.update_progress(80, "変換完了...")

            # 出力パスはparamsから取得
            from pathlib import Path

            output_path = Path(params.get("output", "output"))
            self.main_view.log_frame.add_message(
                f"変換が完了しました: {output_path.absolute()}", "success"
            )

            # プレビューオプションチェック
            if not self.app_state.config.get_no_preview():
                output_html = output_path / "index.html"
                if output_html.exists():
                    self.main_view.log_frame.add_message(
                        "ブラウザでプレビューを開いています..."
                    )
                    webbrowser.open(output_html.resolve().as_uri())

            # ファイルマネージャーで開く
            from .file_controller import FileController

            file_controller = FileController(self.app_state, self.main_view)
            file_controller.open_directory_in_file_manager(output_path)

            self.app_state.conversion_state.update_progress(100, "完了")

            # 成功ダイアログ
            self.main_view.root.after(
                0,
                lambda: messagebox.showinfo(
                    "変換完了",
                    f"ファイルの変換が完了しました。\n\n"
                    f"出力先: {output_path.absolute()}\n\n"
                    f"生成されたファイル:\n"
                    f"• index.html (メインHTML)\n"
                    f"• ソースファイル\n"
                    f"• 画像・CSSファイル等",
                ),
            )

        except Exception as e:
            error_msg = f"変換中にエラーが発生しました: {str(e)}"
            error(error_msg)
            self.main_view.log_frame.add_message(error_msg, "error")
            self.app_state.conversion_state.update_progress(0, "エラー")

            # エラーダイアログ
            self.main_view.root.after(
                0, lambda: messagebox.showerror("変換エラー", error_msg)
            )

        finally:
            # UI再有効化
            self.main_view.root.after(0, lambda: self.main_view.set_ui_enabled(True))

    def generate_sample(self) -> None:
        """サンプルファイルの生成"""
        log_gui_event("button_click", "generate_sample")

        # UI無効化
        self.main_view.set_ui_enabled(False)

        # サンプル生成スレッド開始
        thread = threading.Thread(target=self._generate_sample_thread)
        thread.daemon = True
        thread.start()

    def _generate_sample_thread(self) -> None:
        """サンプル生成スレッド"""
        try:
            self.main_view.log_frame.add_message(
                "サンプルファイルの生成を開始します..."
            )
            self.app_state.conversion_state.update_progress(0, "サンプル生成準備中...")

            use_source_toggle = self.app_state.config.get_include_source()
            self.app_state.conversion_state.update_progress(
                30, "サンプルファイルを作成中..."
            )

            # サンプル生成実行
            if SampleCommand is None:
                raise ImportError("SampleCommand が利用できません")

            sample_command = SampleCommand()
            output_path = sample_command.execute(
                output_dir="kumihan_sample", use_source_toggle=use_source_toggle
            )

            self.app_state.conversion_state.update_progress(80, "サンプル生成完了...")

            self.main_view.log_frame.add_message(
                f"サンプルファイルが生成されました: {output_path.absolute()}", "success"
            )

            # サンプルHTMLを開く
            sample_html = output_path / "showcase.html"
            if sample_html.exists():
                self.main_view.log_frame.add_message(
                    "ブラウザでサンプルを開いています..."
                )
                webbrowser.open(sample_html.resolve().as_uri())

            # ファイルマネージャーで開く
            from .file_controller import FileController

            file_controller = FileController(self.app_state, self.main_view)
            file_controller.open_directory_in_file_manager(output_path)

            self.app_state.conversion_state.update_progress(100, "完了")

            # 成功ダイアログ
            self.main_view.root.after(
                0,
                lambda: messagebox.showinfo(
                    "サンプル生成完了",
                    f"サンプルファイルの生成が完了しました。\n\n"
                    f"出力先: {output_path.absolute()}\n\n"
                    f"生成されたファイル:\n"
                    f"• showcase.html (メインHTML)\n"
                    f"• showcase.txt (ソーステキスト)\n"
                    f"• images/ (サンプル画像)\n\n"
                    f"生成されたHTMLをブラウザで確認してください。",
                ),
            )

        except Exception as e:
            error_msg = f"サンプル生成中にエラーが発生しました: {str(e)}"
            error(error_msg)
            self.main_view.log_frame.add_message(error_msg, "error")
            self.app_state.conversion_state.update_progress(0, "エラー")

            # エラーダイアログ
            self.main_view.root.after(
                0, lambda: messagebox.showerror("サンプル生成エラー", error_msg)
            )

        finally:
            # UI再有効化
            self.main_view.root.after(0, lambda: self.main_view.set_ui_enabled(True))
