"""GUI Launcher for Kumihan-Formatter
Windows向けexe形式パッケージング用のGUIランチャー

This module provides a user-friendly GUI interface for non-technical users
to use Kumihan-Formatter without command line knowledge.
"""

import os
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from typing import Optional

# Add the parent directory to sys.path to import kumihan_formatter modules
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from .commands.convert.convert_command import ConvertCommand
    from .commands.sample import SampleCommand
    from .core.config.config_manager import EnhancedConfig
    from .ui.console_ui import ui
except ImportError as e:
    # Fallback for standalone execution
    import warnings

    warnings.warn(f"Import error: {e}. Some features may not work.")


class KumihanGUI:
    """Main GUI application class for Kumihan-Formatter"""

    def __init__(self):
        self.root = Tk()
        self.root.title("Kumihan-Formatter v1.0 - 美しい組版を、誰でも簡単に")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Variables
        self.input_file_var = StringVar()
        self.output_dir_var = StringVar(value="./dist")
        self.template_var = StringVar(value="base.html.j2")
        self.include_source_var = BooleanVar(value=False)
        self.no_preview_var = BooleanVar(value=False)

        # Progress tracking
        self.progress_var = DoubleVar()
        self.status_var = StringVar(value="準備完了")

        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        """Setup the main UI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(W, E, N, S))

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
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="入力ファイル:").grid(
            row=0, column=0, sticky=W, padx=(0, 10)
        )
        ttk.Entry(file_frame, textvariable=self.input_file_var, width=50).grid(
            row=0, column=1, sticky=(W, E), padx=(0, 10)
        )
        ttk.Button(file_frame, text="参照", command=self.browse_input_file).grid(
            row=0, column=2
        )

        ttk.Label(file_frame, text="出力フォルダ:").grid(
            row=1, column=0, sticky=W, padx=(0, 10), pady=(10, 0)
        )
        ttk.Entry(file_frame, textvariable=self.output_dir_var, width=50).grid(
            row=1, column=1, sticky=(W, E), padx=(0, 10), pady=(10, 0)
        )
        ttk.Button(file_frame, text="参照", command=self.browse_output_dir).grid(
            row=1, column=2, pady=(10, 0)
        )

        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="変換オプション", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))
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
        template_combo.grid(row=0, column=1, sticky=(W, E), padx=(0, 10))

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

        ttk.Button(button_frame, text="終了", command=self.root.quit).pack(side=LEFT)

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="進行状況", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky=(W, E), pady=(0, 5))

        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, sticky=W)

        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(W, E, N, S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

        self.log_text = Text(log_frame, height=8, wrap=WORD, state=DISABLED)
        log_scrollbar = ttk.Scrollbar(
            log_frame, orient=VERTICAL, command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(W, E, N, S))
        log_scrollbar.grid(row=0, column=1, sticky=(N, S))

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        pos_x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        pos_y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def browse_input_file(self):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title="変換するテキストファイルを選択",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
        )
        if filename:
            self.input_file_var.set(filename)

    def browse_output_dir(self):
        """Browse for output directory"""
        dirname = filedialog.askdirectory(title="出力フォルダを選択")
        if dirname:
            self.output_dir_var.set(dirname)

    def on_source_toggle_change(self):
        """Handle source toggle checkbox change"""
        if self.include_source_var.get():
            self.template_var.set("base-with-source-toggle.html.j2")
        else:
            self.template_var.set("base.html.j2")

    def log_message(self, message: str, level: str = "info"):
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

    def update_progress(self, value: float, status: str = ""):
        """Update progress bar and status"""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.root.update_idletasks()

    def convert_file(self):
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

    def _convert_file_thread(self):
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

    def generate_sample(self):
        """Generate sample files in separate thread"""
        # Disable UI elements during generation
        self.set_ui_enabled(False)

        # Start generation in separate thread
        thread = threading.Thread(target=self._generate_sample_thread)
        thread.daemon = True
        thread.start()

    def _generate_sample_thread(self):
        """Sample generation thread"""
        try:
            self.log_message("サンプルファイルの生成を開始します...")
            self.update_progress(0, "サンプル生成準備中...")

            use_source_toggle = self.include_source_var.get()

            self.update_progress(30, "サンプルファイルを作成中...")

            # Execute sample generation
            sample_command = SampleCommand()
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

            self.update_progress(100, "完了")

            # Show success dialog
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "サンプル生成完了",
                    f"サンプルファイルの生成が完了しました。\n\n出力先: {output_path.absolute()}\n\nサンプルHTMLがブラウザで開かれます。",
                ),
            )

        except Exception as e:
            self.log_message(f"サンプル生成エラー: {str(e)}", "error")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "サンプル生成エラー",
                    f"サンプル生成中にエラーが発生しました:\n\n{str(e)}",
                ),
            )

        finally:
            # Re-enable UI
            self.root.after(0, lambda: self.set_ui_enabled(True))
            self.update_progress(0, "準備完了")

    def set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements"""
        state = NORMAL if enabled else DISABLED

        # Find all widgets and update their state
        def update_widget_state(widget):
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

    def show_help(self):
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

    def run(self):
        """Start the GUI application"""
        self.log_message("Kumihan-Formatter GUI が起動しました")
        self.log_message(
            "使い方がわからない場合は「ヘルプ」ボタンをクリックしてください"
        )
        self.root.mainloop()


def main():
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
