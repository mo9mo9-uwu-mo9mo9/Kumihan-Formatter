"""GUI Controller for Kumihan-Formatter

Controller層: イベント制御とビジネスロジック調整
MVCパターンでのController部分を担当し、ModelとViewの橋渡しを行う
"""

import platform
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Any, Optional

from .gui_models import AppState
from .gui_views import MainView

if TYPE_CHECKING:
    from .core.log_viewer import LogViewerWindow

# デバッグロガーのインポート
try:
    from .core.debug_logger import (
        debug,
        error,
        info,
        is_debug_enabled,
        log_gui_event,
        log_gui_method,
        warning,
    )
except ImportError:
    # Fallbacksを定義
    def debug(*args: Any, **kwargs: Any) -> None:
        pass

    def info(*args: Any, **kwargs: Any) -> None:
        pass

    def warning(*args: Any, **kwargs: Any) -> None:
        pass

    def error(*args: Any, **kwargs: Any) -> None:
        pass

    def log_gui_event(*args: Any, **kwargs: Any) -> None:
        pass

    def log_gui_method(func: Any) -> Any:  # type: ignore[misc]
        return func

    def is_debug_enabled() -> bool:
        return False


# コマンドクラスのインポート
try:
    from .commands.convert.convert_command import ConvertCommand
    from .commands.sample import SampleCommand
except ImportError:
    try:
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand
        from kumihan_formatter.commands.sample import SampleCommand
    except ImportError as e:
        error(f"Failed to import command classes: {e}")
        ConvertCommand = None  # type: ignore
        SampleCommand = None  # type: ignore


class GuiController:
    """GUIコントローラークラス

    ユーザーインタラクション、イベント処理、ビジネスロジックを管理
    """

    def __init__(self) -> None:
        """コントローラーの初期化"""
        self.app_state = AppState()
        self.main_view = MainView(self.app_state)
        self.log_viewer: Optional["LogViewerWindow"] = None

        # イベントハンドラーの設定
        self._setup_event_handlers()

        # 初期ログメッセージ
        self._add_startup_messages()

    def _setup_event_handlers(self) -> None:
        """イベントハンドラーの設定"""
        # ファイル選択イベント
        self.main_view.file_selection_frame.set_input_browse_command(
            self.browse_input_file
        )
        self.main_view.file_selection_frame.set_output_browse_command(
            self.browse_output_dir
        )

        # オプション変更イベント
        self.main_view.options_frame.set_source_toggle_command(
            self.on_source_toggle_change
        )

        # アクションボタンイベント
        self.main_view.action_button_frame.set_convert_command(self.convert_file)
        self.main_view.action_button_frame.set_sample_command(self.generate_sample)
        self.main_view.action_button_frame.set_help_command(self.show_help)
        self.main_view.action_button_frame.set_exit_command(self.exit_application)

        # デバッグモード時のログボタン
        if self.app_state.debug_mode:
            self.main_view.action_button_frame.set_log_command(self.show_log_viewer)

    def _add_startup_messages(self) -> None:
        """起動時のメッセージを追加"""
        self.main_view.log_frame.add_message("Kumihan-Formatter GUI が起動しました")
        self.main_view.log_frame.add_message(
            "使い方がわからない場合は「ヘルプ」ボタンをクリックしてください"
        )

    def browse_input_file(self) -> None:
        """入力ファイルの参照"""
        log_gui_event("button_click", "browse_input_file")

        filename = filedialog.askopenfilename(
            title="変換するテキストファイルを選択",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
        )

        if filename:
            info(f"Input file selected: {filename}")
            self.app_state.config.set_input_file(filename)
            self.main_view.log_frame.add_message(f"入力ファイル: {Path(filename).name}")
        else:
            debug("Input file selection cancelled")

    def browse_output_dir(self) -> None:
        """出力ディレクトリの参照"""
        log_gui_event("button_click", "browse_output_dir")

        dirname = filedialog.askdirectory(title="出力フォルダを選択")
        if dirname:
            self.app_state.config.set_output_dir(dirname)
            self.main_view.log_frame.add_message(f"出力フォルダ: {dirname}")

    def on_source_toggle_change(self) -> None:
        """ソース表示オプションの変更処理"""
        include_source = self.app_state.config.get_include_source()

        # テンプレートの自動切り替え
        if include_source:
            self.app_state.config.set_template("base-with-source-toggle.html.j2")
            self.main_view.log_frame.add_message("ソース表示機能が有効になりました")
        else:
            self.app_state.config.set_template("base.html.j2")
            self.main_view.log_frame.add_message("ソース表示機能が無効になりました")

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
            self.app_state.conversion_state.update_progress(90, "変換完了...")

            # 成功処理
            output_path = self.app_state.get_output_file_path()
            if output_path:
                self.main_view.log_frame.add_message(
                    f"変換が完了しました: {output_path}", "success"
                )

                # プレビュー表示
                if not self.app_state.config.get_no_preview() and output_path.exists():
                    self.main_view.log_frame.add_message(
                        "ブラウザでプレビューを開いています..."
                    )
                    webbrowser.open(output_path.resolve().as_uri())

            self.app_state.conversion_state.update_progress(100, "完了")

            # 成功ダイアログ
            self.main_view.root.after(
                0,
                lambda: messagebox.showinfo(
                    "変換完了",
                    f"ファイルの変換が完了しました。\n\n出力先: {output_path}",
                ),
            )

        except Exception as e:
            error_msg = str(e)
            self.main_view.log_frame.add_message(f"変換エラー: {error_msg}", "error")
            self.main_view.root.after(
                0,
                lambda: messagebox.showerror(
                    "変換エラー", f"変換中にエラーが発生しました:\n\n{error_msg}"
                ),
            )

        finally:
            # UI有効化
            self.main_view.root.after(0, lambda: self.main_view.set_ui_enabled(True))
            self.app_state.conversion_state.reset()

    def generate_sample(self) -> None:
        """サンプル生成の実行"""
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

            # Finder/Explorerで開く
            self._open_directory_in_file_manager(output_path)

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
                    f"ファイルマネージャーでフォルダを開きました。",
                ),
            )

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            error_msg = str(e)
            self.main_view.log_frame.add_message(
                f"サンプル生成エラー: {error_msg}", "error"
            )
            self.main_view.log_frame.add_message(f"詳細: {error_details}", "error")
            self.main_view.root.after(
                0,
                lambda: messagebox.showerror(
                    "サンプル生成エラー",
                    f"サンプル生成中にエラーが発生しました:\n\n{error_msg}\n\n詳細はログを確認してください。",
                ),
            )

        finally:
            # UI有効化
            self.main_view.root.after(0, lambda: self.main_view.set_ui_enabled(True))
            self.app_state.conversion_state.reset()

    def _open_directory_in_file_manager(self, directory_path: Path) -> None:
        """ファイルマネージャーでディレクトリを開く"""
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                self.main_view.log_frame.add_message(
                    "Finderでフォルダを開いています..."
                )
                subprocess.run(["open", str(directory_path.absolute())])
            elif system == "Windows":
                self.main_view.log_frame.add_message(
                    "エクスプローラーでフォルダを開いています..."
                )
                subprocess.run(["explorer", str(directory_path.absolute())])
            elif system == "Linux":
                self.main_view.log_frame.add_message(
                    "ファイルマネージャーでフォルダを開いています..."
                )
                subprocess.run(["xdg-open", str(directory_path.absolute())])
        except Exception as e:
            warning(f"Failed to open directory in file manager: {e}")

    def show_help(self) -> None:
        """ヘルプダイアログの表示"""
        log_gui_event("button_click", "show_help")
        self.main_view.help_dialog.show()

    def show_log_viewer(self) -> None:
        """ログビューアーの表示（デバッグモード時のみ）"""
        log_gui_event("button_click", "show_log_viewer")

        try:
            if self.log_viewer and self.log_viewer.is_open():
                # 既に開いている場合は前面に表示
                if hasattr(self.log_viewer, "window") and self.log_viewer.window:
                    self.log_viewer.window.lift()
                    self.log_viewer.window.focus_force()
            else:
                # 新しいログビューアーを開く
                from .core.log_viewer import LogViewerWindow

                self.log_viewer = LogViewerWindow(self.main_view.root)
                self.log_viewer.show()
                info("Log viewer window opened")
        except Exception as e:
            error("Failed to open log viewer", e)
            messagebox.showerror(
                "エラー", f"ログビューアーの表示に失敗しました:\n\n{str(e)}"
            )

    def exit_application(self) -> None:
        """アプリケーションの終了"""
        log_gui_event("button_click", "exit_application")
        self.main_view.root.quit()

    def run(self) -> None:
        """GUIアプリケーションの実行"""
        try:
            info("Starting GUI main loop...")
            self.main_view.start_mainloop()
        except Exception as e:
            error(f"GUI main loop error: {e}")
            raise


def create_gui_application() -> GuiController:
    """GUIアプリケーションの作成

    Returns:
        設定済みのGUIコントローラー
    """
    return GuiController()
