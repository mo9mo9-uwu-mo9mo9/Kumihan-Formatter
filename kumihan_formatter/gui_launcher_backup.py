"""GUI Launcher for Kumihan-Formatter
Windows向けexe形式パッケージング用のGUIランチャー

This module provides a user-friendly GUI interface for non-technical users
to use Kumihan-Formatter without command line knowledge.
"""

import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from .core.log_viewer import LogViewerWindow

# Debug logger (環境変数KUMIHAN_GUI_DEBUG=trueで有効化)
try:
    from .core.debug_logger import (
        debug,
        error,
        get_logger,
        info,
        is_debug_enabled,
        log_gui_event,
        log_gui_method,
        log_startup_info,
        warning,
    )
except ImportError:
    # Fallback for direct execution
    try:
        from kumihan_formatter.core.debug_logger import (
            debug,
            error,
            get_logger,
            info,
            is_debug_enabled,
            log_gui_event,
            log_gui_method,
            log_startup_info,
            warning,
        )
    except ImportError:
        # No-op fallbacks if debug logger is not available

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

        def log_gui_method(func: Callable[..., Any]) -> Callable[..., Any]:  # type: ignore[misc]
            return func

        def log_startup_info() -> None:
            pass

        def is_debug_enabled() -> bool:
            return False

        def get_logger() -> Any:  # type: ignore[misc]
            return None


# Log startup information
log_startup_info()
info("GUI Launcher module loading...")

# Add the parent directory to sys.path to import kumihan_formatter modules
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Try relative imports first (for package execution)
info("Attempting to import required modules...")
try:
    debug("Trying relative imports...")
    from .commands.convert.convert_command import ConvertCommand
    from .commands.sample import SampleCommand
    from .core.config.config_manager import EnhancedConfig
    from .ui.console_ui import get_console_ui

    info("Relative imports successful")
except ImportError as relative_error:
    warning(f"Relative imports failed: {relative_error}")
    # Try absolute imports (for direct execution)
    try:
        debug("Trying absolute imports...")
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand
        from kumihan_formatter.commands.sample import SampleCommand
        from kumihan_formatter.core.config.config_manager import EnhancedConfig
        from kumihan_formatter.ui.console_ui import get_console_ui

        info("Absolute imports successful")
    except ImportError as absolute_error:
        # If both fail, show detailed error and exit
        import sys

        error_msg = f"インポートエラー: 必要なモジュールが見つかりません"
        error(error_msg)
        error(f"相対インポートエラー: {relative_error}")
        error(f"絶対インポートエラー: {absolute_error}")
        error(f"現在のPythonパス: {sys.path}")

        print(error_msg, file=sys.stderr)
        print(f"相対インポートエラー: {relative_error}", file=sys.stderr)
        print(f"絶対インポートエラー: {absolute_error}", file=sys.stderr)
        print(f"現在のPythonパス: {sys.path}", file=sys.stderr)
        if is_debug_enabled():
            print(
                f"デバッグログファイル: {get_logger().get_log_file_path()}",
                file=sys.stderr,
            )
        sys.exit(1)


class KumihanGUI:
    """Main GUI application class for Kumihan-Formatter"""

    @log_gui_method  # type: ignore
    def __init__(self) -> None:
        info("Initializing KumihanGUI...")
        try:
            debug("Creating root Tk window...")
            self.root = Tk()
            self.root.title("Kumihan-Formatter v1.0 - 美しい組版を、誰でも簡単に")
            self.root.geometry("800x600")
            self.root.resizable(True, True)
            info("Root Tk window created successfully")
        except Exception as e:
            error("Failed to create root Tk window", e)
            raise

        # Configure style
        try:
            debug("Configuring ttk style...")
            self.style = ttk.Style()
            self.style.theme_use("clam")
            info("ttk style configured successfully")
        except Exception as e:
            error("Failed to configure ttk style", e)
            raise

        # Variables
        self.input_file_var = StringVar()
        self.output_dir_var = StringVar(value="./dist")
        self.template_var = StringVar(value="base.html.j2")
        self.include_source_var = BooleanVar(value=False)
        self.no_preview_var = BooleanVar(value=False)

        # Progress tracking
        self.progress_var = DoubleVar()
        self.status_var = StringVar(value="準備完了")

        try:
            debug("Setting up UI components...")
            self.setup_ui()
            info("UI components setup completed")

            debug("Centering window...")
            self.center_window()
            info("Window centered")

            info("KumihanGUI initialization completed successfully")
        except Exception as e:
            error("Failed during GUI initialization", e)
            raise

    def setup_ui(self) -> None:
        """Setup the main UI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="WENS")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="Kumihan-Formatter", font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        subtitle_label = ttk.Label(
            main_frame,
            text="美しい組版を、誰でも簡単に。テキストファイルをワンクリックでHTMLに変換",
            font=("Arial", 10),
        )
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))

        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="ファイル選択", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, sticky="WE", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="入力ファイル:").grid(
            row=0, column=0, sticky=W, padx=(0, 10)
        )
        ttk.Entry(file_frame, textvariable=self.input_file_var, width=50).grid(
            row=0, column=1, sticky="WE", padx=(0, 10)
        )
        ttk.Button(file_frame, text="参照", command=self.browse_input_file).grid(  # type: ignore[misc]
            row=0, column=2
        )

        ttk.Label(file_frame, text="出力フォルダ:").grid(
            row=1, column=0, sticky=W, padx=(0, 10), pady=(10, 0)
        )
        ttk.Entry(file_frame, textvariable=self.output_dir_var, width=50).grid(
            row=1, column=1, sticky="WE", padx=(0, 10), pady=(10, 0)
        )
        ttk.Button(file_frame, text="参照", command=self.browse_output_dir).grid(
            row=1, column=2, pady=(10, 0)
        )

        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="変換オプション", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky="WE", pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="テンプレート:").grid(
            row=0, column=0, sticky=W, padx=(0, 10)
        )
        template_combo = ttk.Combobox(
            options_frame,
            textvariable=self.template_var,
            values=["base.html.j2", "base-with-source-toggle.html.j2"],
            state="readonly",
        )
        template_combo.grid(row=0, column=1, sticky="WE", padx=(0, 10))

        ttk.Checkbutton(
            options_frame,
            text="ソース表示機能を含める",
            variable=self.include_source_var,
            command=self.on_source_toggle_change,
        ).grid(row=1, column=0, columnspan=2, sticky=W, pady=(10, 0))

        ttk.Checkbutton(
            options_frame,
            text="変換後のプレビューをスキップ",
            variable=self.no_preview_var,
        ).grid(row=2, column=0, columnspan=2, sticky=W, pady=(5, 0))

        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)

        ttk.Button(
            button_frame,
            text="変換実行",
            command=self.convert_file,
            style="Accent.TButton",
        ).pack(side=LEFT, padx=(0, 10))

        ttk.Button(
            button_frame, text="サンプル生成", command=self.generate_sample
        ).pack(side=LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="ヘルプ", command=self.show_help).pack(
            side=LEFT, padx=(0, 10)
        )

        # デバッグモードの時のみログビューアーボタンを表示
        if is_debug_enabled():
            ttk.Button(button_frame, text="ログ", command=self.show_log_viewer).pack(  # type: ignore[misc]
                side=LEFT, padx=(0, 10)
            )

        ttk.Button(button_frame, text="終了", command=self.root.quit).pack(side=LEFT)

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="進行状況", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky="WE", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky="WE", pady=(0, 5))

        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, sticky=W)

        # ログビューアーの参照を保持
        self.log_viewer: Optional["LogViewerWindow"] = None

        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky="WENS", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

        self.log_text = Text(log_frame, height=8, wrap=WORD, state=DISABLED)
        log_scrollbar = ttk.Scrollbar(
            log_frame, orient=VERTICAL, command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky="WENS")
        log_scrollbar.grid(row=0, column=1, sticky="NS")

    def center_window(self) -> None:
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        pos_x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        pos_y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    @log_gui_method  # type: ignore
    def browse_input_file(self) -> None:
        """Browse for input file"""
        log_gui_event("button_click", "browse_input_file")
        filename = filedialog.askopenfilename(
            title="変換するテキストファイルを選択",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
        )
        if filename:
            info(f"Input file selected: {filename}")
            self.input_file_var.set(filename)
        else:
            debug("Input file selection cancelled")

    def browse_output_dir(self) -> None:
        """Browse for output directory"""
        dirname = filedialog.askdirectory(title="出力フォルダを選択")
        if dirname:
            self.output_dir_var.set(dirname)

    def on_source_toggle_change(self) -> None:
        """Handle source toggle checkbox change"""
        if self.include_source_var.get():
            self.template_var.set("base-with-source-toggle.html.j2")
        else:
            self.template_var.set("base.html.j2")

    def log_message(self, message: str, level: str = "info") -> None:
        """Add message to log"""
        self.log_text.config(state=NORMAL)
        timestamp = __import__("datetime").datetime.now().strftime("%H:%M:%S")

        if level == "error":
            prefix = "❌"
        elif level == "success":
            prefix = "✅"
        elif level == "warning":
            prefix = "⚠️"
        else:
            prefix = "ℹ️"

        self.log_text.insert(END, f"[{timestamp}] {prefix} {message}\n")
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)
        self.root.update_idletasks()

    def update_progress(self, value: float, status: str = "") -> None:
        """Update progress bar and status"""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.root.update_idletasks()

    def convert_file(self) -> None:
        """Execute file conversion in separate thread"""
        input_file = self.input_file_var.get().strip()
        if not input_file:
            messagebox.showerror("エラー", "入力ファイルを選択してください。")
            return

        if not Path(input_file).exists():
            messagebox.showerror("エラー", "指定されたファイルが見つかりません。")
            return

        # Disable UI elements during conversion
        self.set_ui_enabled(False)

        # Start conversion in separate thread
        thread = threading.Thread(target=self._convert_file_thread)
        thread.daemon = True
        thread.start()

    def _convert_file_thread(self) -> None:
        """File conversion thread"""
        try:
            self.log_message("変換を開始します...")
            self.update_progress(0, "変換準備中...")

            input_file = self.input_file_var.get()
            output_dir = self.output_dir_var.get()
            template = self.template_var.get()
            include_source = self.include_source_var.get()
            no_preview = self.no_preview_var.get()

            self.update_progress(20, "設定を読み込み中...")

            # Execute conversion
            try:
                convert_command = ConvertCommand()
                self.update_progress(40, "ファイルを変換中...")

                # Execute conversion with GUI-friendly parameters
                convert_command.execute(
                    input_file=input_file,
                    output=output_dir,
                    no_preview=no_preview,
                    watch=False,
                    config=None,
                    show_test_cases=False,
                    template_name=template,
                    include_source=include_source,
                    syntax_check=True,
                )

                self.update_progress(90, "変換完了...")

                # Success message
                output_path = Path(output_dir) / f"{Path(input_file).stem}.html"
                self.log_message(f"変換が完了しました: {output_path}", "success")

                if not no_preview and output_path.exists():
                    self.log_message("ブラウザでプレビューを開いています...")
                    webbrowser.open(output_path.resolve().as_uri())

                self.update_progress(100, "完了")

                # Show success dialog
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "変換完了",
                        f"ファイルの変換が完了しました。\n\n出力先: {output_path}",
                    ),
                )

            except Exception as e:
                self.log_message(f"変換エラー: {str(e)}", "error")
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "変換エラー", f"変換中にエラーが発生しました:\n\n{str(e)}"
                    ),
                )

        except Exception as e:
            self.log_message(f"予期しないエラー: {str(e)}", "error")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "エラー", f"予期しないエラーが発生しました:\n\n{str(e)}"
                ),
            )

        finally:
            # Re-enable UI
            self.root.after(0, lambda: self.set_ui_enabled(True))
            self.update_progress(0, "準備完了")

    def generate_sample(self) -> None:
        """Generate sample files in separate thread"""
        # Disable UI elements during generation
        self.set_ui_enabled(False)

        # Start generation in separate thread
        thread = threading.Thread(target=self._generate_sample_thread)
        thread.daemon = True
        thread.start()

    def _generate_sample_thread(self) -> None:
        """Sample generation thread"""
        try:
            self.log_message("サンプルファイルの生成を開始します...")
            self.update_progress(0, "サンプル生成準備中...")

            use_source_toggle = self.include_source_var.get()

            self.update_progress(30, "サンプルファイルを作成中...")

            # Execute sample generation
            try:
                sample_command = SampleCommand()
            except Exception as init_error:
                self.log_message(
                    f"SampleCommandの初期化エラー: {str(init_error)}", "error"
                )
                raise init_error

            output_path = sample_command.execute(
                output_dir="kumihan_sample", use_source_toggle=use_source_toggle
            )

            self.update_progress(80, "サンプル生成完了...")

            self.log_message(
                f"サンプルファイルが生成されました: {output_path.absolute()}", "success"
            )

            # Open sample HTML
            sample_html = output_path / "showcase.html"
            if sample_html.exists():
                self.log_message("ブラウザでサンプルを開いています...")
                webbrowser.open(sample_html.resolve().as_uri())

            # Open directory in Finder (macOS)
            import platform
            import subprocess

            if platform.system() == "Darwin":  # macOS
                self.log_message("Finderでフォルダを開いています...")
                subprocess.run(["open", str(output_path.absolute())])

            self.update_progress(100, "完了")

            # Show success dialog with more detail
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "サンプル生成完了",
                    f"サンプルファイルの生成が完了しました。\n\n"
                    f"出力先: {output_path.absolute()}\n\n"
                    f"生成されたファイル:\n"
                    f"• showcase.html (メインHTML)\n"
                    f"• showcase.txt (ソーステキスト)\n"
                    f"• images/ (サンプル画像)\n\n"
                    f"Finderでフォルダを開きました。",
                ),
            )

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            self.log_message(f"サンプル生成エラー: {str(e)}", "error")
            self.log_message(f"詳細: {error_details}", "error")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "サンプル生成エラー",
                    f"サンプル生成中にエラーが発生しました:\n\n{str(e)}\n\n詳細はログを確認してください。",
                ),
            )

        finally:
            # Re-enable UI
            self.root.after(0, lambda: self.set_ui_enabled(True))
            self.update_progress(0, "準備完了")

    def set_ui_enabled(self, enabled: bool) -> None:
        """Enable/disable UI elements"""
        state = NORMAL if enabled else DISABLED

        # Find all widgets and update their state
        def update_widget_state(widget) -> None:  # type: ignore
            try:
                if isinstance(
                    widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)
                ):
                    widget.configure(state=state)
            except:
                pass

            for child in widget.winfo_children():
                update_widget_state(child)

        update_widget_state(self.root)

    def show_help(self) -> None:
        """Show help dialog"""
        help_text = """Kumihan-Formatter GUI ヘルプ

【基本的な使い方】
1. 「参照」ボタンから変換したいテキストファイルを選択
2. 出力フォルダを指定（デフォルト: ./dist）
3. 必要に応じてオプションを設定
4. 「変換実行」ボタンをクリック

【オプション説明】
• テンプレート: 出力HTMLのテンプレートを選択
• ソース表示機能: 原文と変換結果を切り替え表示する機能
• プレビューをスキップ: 変換後にブラウザを自動で開かない

【サンプル生成】
「サンプル生成」ボタンで機能紹介用のサンプルファイルを生成できます。

【サポート】
詳細な使い方やトラブルシューティングは、
プロジェクトのドキュメントを参照してください。

GitHub: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter
"""

        help_window = Toplevel(self.root)
        help_window.title("ヘルプ")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        help_window.grab_set()

        # Center help window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (help_window.winfo_screenheight() // 2) - (500 // 2)
        help_window.geometry(f"600x500+{x}+{y}")

        # Help content
        text_frame = Frame(help_window)
        text_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        help_text_widget = Text(text_frame, wrap=WORD, padx=10, pady=10)
        help_scrollbar = ttk.Scrollbar(
            text_frame, orient=VERTICAL, command=help_text_widget.yview
        )
        help_text_widget.configure(yscrollcommand=help_scrollbar.set)

        help_text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        help_scrollbar.pack(side=RIGHT, fill=Y)

        help_text_widget.insert("1.0", help_text)
        help_text_widget.config(state=DISABLED)

        # Close button
        ttk.Button(help_window, text="閉じる", command=help_window.destroy).pack(
            pady=10
        )

    @log_gui_method  # type: ignore
    def show_log_viewer(self) -> None:
        """Show debug log viewer window"""
        log_gui_event("button_click", "show_log_viewer")
        try:
            if self.log_viewer and self.log_viewer.is_open():
                # 既に開いている場合は前面に表示
                if self.log_viewer.window:
                    self.log_viewer.window.lift()
                    self.log_viewer.window.focus_force()
            else:
                # 新しいログビューアーを開く
                from .core.log_viewer import LogViewerWindow

                self.log_viewer = LogViewerWindow(self.root)
                self.log_viewer.show()
                info("Log viewer window opened")
        except Exception as e:
            error("Failed to open log viewer", e)
            messagebox.showerror(
                "エラー", f"ログビューアーの表示に失敗しました:\n\n{str(e)}"
            )

    def run(self) -> None:
        """Start the GUI application"""
        self.log_message("Kumihan-Formatter GUI が起動しました")
        self.log_message(
            "使い方がわからない場合は「ヘルプ」ボタンをクリックしてください"
        )
        self.root.mainloop()


def main() -> None:
    """Main entry point for GUI launcher"""
    try:
        app = KumihanGUI()
        app.run()
    except Exception as e:
        # Fallback error handling for GUI startup issues
        import tkinter.messagebox as mb

        mb.showerror(
            "起動エラー",
            f"GUIの起動中にエラーが発生しました:\n\n{str(e)}\n\nコマンドライン版の使用をお試しください。",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
