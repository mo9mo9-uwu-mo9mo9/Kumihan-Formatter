#!/usr/bin/env python3
"""
GUI Launcher for Kumihan Formatter
macOS/Windows共通のGUIラッパー
"""
import logging
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kumihan_formatter.config.config_loader import ConfigLoader
from kumihan_formatter.config.settings import Settings
from kumihan_formatter.core.converter import Converter


class KumihanFormatterGUI:
    """Kumihan Formatter GUI Application"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Kumihan Formatter v1.0")
        self.root.geometry("800x600")

        # macOS固有の設定
        if sys.platform == "darwin":
            self.root.createcommand("tk::mac::ShowPreferences", self.show_preferences)

        # 設定とコンバーターの初期化
        self.settings = Settings()
        self.config_loader = ConfigLoader()
        self.converter = None

        # 処理キュー
        self.queue = queue.Queue()

        # UIの構築
        self.setup_ui()

        # ログ設定
        self.setup_logging()

    def setup_ui(self):
        """UIコンポーネントの設定"""
        # メニューバー
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="ファイルを選択...", command=self.select_files)
        file_menu.add_command(label="フォルダを選択...", command=self.select_folder)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit)

        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(
            label="Kumihan Formatterについて", command=self.show_about
        )

        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ファイルリスト
        list_label = ttk.Label(main_frame, text="変換対象ファイル:")
        list_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        # リストボックスとスクロールバー
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )

        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=10)
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview
        )
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="ファイル追加", command=self.select_files).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="選択を削除", command=self.remove_selected).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="すべてクリア", command=self.clear_all).pack(
            side=tk.LEFT, padx=5
        )

        # テンプレート選択
        template_label = ttk.Label(main_frame, text="テンプレート:")
        template_label.grid(row=3, column=0, sticky=tk.W, pady=5)

        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            main_frame, textvariable=self.template_var, state="readonly"
        )
        self.template_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        self.load_templates()

        # 進捗バー
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, variable=self.progress_var, mode="determinate"
        )
        self.progress_bar.grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )

        # ログエリア
        log_label = ttk.Label(main_frame, text="ログ:")
        log_label.grid(row=5, column=0, sticky=tk.W, pady=5)

        log_frame = ttk.Frame(main_frame)
        log_frame.grid(
            row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )

        self.log_text = tk.Text(log_frame, height=8, width=70)
        log_scrollbar = ttk.Scrollbar(
            log_frame, orient=tk.VERTICAL, command=self.log_text.yview
        )
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 変換ボタン
        self.convert_button = ttk.Button(
            main_frame, text="変換開始", command=self.start_conversion
        )
        self.convert_button.grid(row=7, column=0, columnspan=3, pady=20)

        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def setup_logging(self):
        """ログ設定"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # GUIハンドラー
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget, queue):
                super().__init__()
                self.text_widget = text_widget
                self.queue = queue

            def emit(self, record):
                msg = self.format(record)
                self.queue.put(("log", msg))

        handler = GUILogHandler(self.log_text, self.queue)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def load_templates(self):
        """テンプレートの読み込み"""
        templates_dir = Path(__file__).parent.parent / "templates"
        templates = []

        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                templates.append(template_file.stem)

        self.template_combo["values"] = templates
        if templates:
            self.template_combo.current(0)

    def select_files(self):
        """ファイル選択ダイアログ"""
        files = filedialog.askopenfilenames(
            title="変換するファイルを選択",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
        )

        for file in files:
            if file not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, file)

    def select_folder(self):
        """フォルダ選択ダイアログ"""
        folder = filedialog.askdirectory(title="フォルダを選択")
        if folder:
            # フォルダ内のすべての.txtファイルを追加
            folder_path = Path(folder)
            for txt_file in folder_path.glob("**/*.txt"):
                if str(txt_file) not in self.file_listbox.get(0, tk.END):
                    self.file_listbox.insert(tk.END, str(txt_file))

    def remove_selected(self):
        """選択したファイルを削除"""
        selected = self.file_listbox.curselection()
        for index in reversed(selected):
            self.file_listbox.delete(index)

    def clear_all(self):
        """すべてのファイルをクリア"""
        self.file_listbox.delete(0, tk.END)

    def show_about(self):
        """バージョン情報の表示"""
        messagebox.showinfo(
            "Kumihan Formatterについて",
            "Kumihan Formatter v1.0\\n\\n"
            "台本フォーマット変換ツール\\n\\n"
            "Copyright (c) 2024",
        )

    def show_preferences(self):
        """設定画面の表示"""
        # TODO: 設定画面の実装
        messagebox.showinfo("設定", "設定画面は現在開発中です。")

    def start_conversion(self):
        """変換処理の開始"""
        files = list(self.file_listbox.get(0, tk.END))
        if not files:
            messagebox.showwarning("警告", "変換するファイルを選択してください。")
            return

        template = self.template_var.get()
        if not template:
            messagebox.showwarning("警告", "テンプレートを選択してください。")
            return

        # UIを無効化
        self.convert_button.config(state="disabled")

        # 変換スレッドを開始
        thread = threading.Thread(target=self.convert_files, args=(files, template))
        thread.daemon = True
        thread.start()

        # キュー監視を開始
        self.root.after(100, self.process_queue)

    def convert_files(self, files: List[str], template: str):
        """ファイル変換処理（別スレッド）"""
        try:
            # テンプレート設定を読み込み
            template_path = (
                Path(__file__).parent.parent / "templates" / f"{template}.json"
            )
            config = self.config_loader.load_config(str(template_path))
            self.converter = Converter(config)

            total_files = len(files)
            self.queue.put(("progress_max", total_files))

            for i, file_path in enumerate(files):
                self.queue.put(("log", f"変換中: {os.path.basename(file_path)}"))

                try:
                    # ファイルを変換
                    output_path = Path(file_path).with_suffix(".html")
                    self.converter.convert_file(file_path, str(output_path))
                    self.queue.put(("log", f"完了: {os.path.basename(output_path)}"))
                except Exception as e:
                    self.queue.put(
                        ("log", f"エラー: {os.path.basename(file_path)} - {str(e)}")
                    )

                self.queue.put(("progress", i + 1))

            self.queue.put(("done", None))
            self.queue.put(("log", "すべての変換が完了しました。"))

        except Exception as e:
            self.queue.put(("error", str(e)))

    def process_queue(self):
        """キューの処理"""
        try:
            while True:
                msg_type, msg_data = self.queue.get_nowait()

                if msg_type == "log":
                    self.log_text.insert(tk.END, msg_data + "\\n")
                    self.log_text.see(tk.END)
                elif msg_type == "progress":
                    self.progress_var.set(msg_data)
                elif msg_type == "progress_max":
                    self.progress_bar.config(maximum=msg_data)
                elif msg_type == "done":
                    self.convert_button.config(state="normal")
                    messagebox.showinfo("完了", "変換が完了しました。")
                elif msg_type == "error":
                    self.convert_button.config(state="normal")
                    messagebox.showerror(
                        "エラー", f"変換中にエラーが発生しました:\\n{msg_data}"
                    )

        except queue.Empty:
            pass

        # 100ms後に再度チェック
        if self.convert_button["state"] == "disabled":
            self.root.after(100, self.process_queue)

    def run(self):
        """アプリケーションの実行"""
        self.root.mainloop()


def main():
    """メインエントリーポイント"""
    app = KumihanFormatterGUI()
    app.run()


if __name__ == "__main__":
    main()
