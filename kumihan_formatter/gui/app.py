"""Kumihan-Formatter GUI Application

メインGUIアプリケーション - モダンでリッチなインターフェース
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import threading
import queue

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from ..core.utilities.logger import get_logger
from ..commands.convert.convert_processor import ConvertProcessor
from .styles.theme import KumihanTheme
from .components.file_selector import FileDropFrame, FileListDisplay
from .debug_logger import create_gui_logger, safe_import_with_logging


class KumihanFormatterApp:
    """Kumihan-Formatter デスクトップGUIアプリケーション"""

    def __init__(self, verbose_logging: bool = False) -> None:
        # GUI専用ログ初期化
        self.debug_logger = create_gui_logger(verbose=verbose_logging, console_output=True)
        self.logger = get_logger(__name__)
        
        self.debug_logger.log_startup()
        self.logger.info("Kumihan-Formatter GUI アプリケーション開始")

        # テーマ適用
        KumihanTheme.apply_modern_theme()

        # メインウィンドウ初期化（TkinterDnD対応）
        self.root = TkinterDnD.Tk()
        ctk.set_appearance_mode("light")
        self.root.title("Kumihan-Formatter v0.9.0-alpha.8")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # ウィンドウを中央に配置
        self._center_window()

        # 変数初期化
        self.selected_files: List[Path] = []
        self.output_directory: Optional[Path] = None
        self.is_converting: bool = False

        # UI要素の参照（初期化後は非Noneが保証される）
        self.file_drop_frame: FileDropFrame
        self.file_list_display: FileListDisplay  
        self.progress_bar: ctk.CTkProgressBar
        self.status_label: ctk.CTkLabel
        self.convert_button: ctk.CTkButton

        # キューベース進捗更新
        self.progress_queue: queue.Queue = queue.Queue()

        # UI構築
        self._build_ui()

        # 進捗更新の定期チェック
        self._check_progress_queue()

    def _center_window(self) -> None:
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        pos_x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        pos_y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def _build_ui(self) -> None:
        """UI構築"""
        # メインコンテナ
        main_frame = ctk.CTkFrame(self.root, **KumihanTheme.get_frame_style())
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ヘッダー
        self._build_header(main_frame)

        # ファイル選択エリア
        self._build_file_selection_area(main_frame)

        # 出力設定エリア
        self._build_output_settings_area(main_frame)

        # 変換実行エリア
        self._build_convert_area(main_frame)

        # ステータス・進捗エリア
        self._build_status_area(main_frame)

    def _build_header(self, parent: ctk.CTkFrame) -> None:
        """ヘッダー構築"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🎨 Kumihan-Formatter",
            **KumihanTheme.get_label_style("title"),
        )
        title_label.pack(side="left")

        version_label = ctk.CTkLabel(
            header_frame,
            text="v0.9.0-alpha.8",
            **KumihanTheme.get_label_style("secondary"),
        )
        version_label.pack(side="right")

    def _build_file_selection_area(self, parent: ctk.CTkFrame) -> None:
        """ファイル選択エリア構築"""
        # セクションタイトル
        file_section_label = ctk.CTkLabel(
            parent, text="📁 ファイル選択", **KumihanTheme.get_label_style("primary")
        )
        file_section_label.pack(anchor="w", pady=(0, 10))

        # ファイル操作ボタン
        file_button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        file_button_frame.pack(fill="x", pady=(0, 10))

        clear_files_btn = ctk.CTkButton(
            file_button_frame,
            text="🗑️ クリア",
            command=self._clear_files,
            **KumihanTheme.get_button_style("secondary"),
            width=100,
        )
        clear_files_btn.pack(side="right")

        # ドラッグ&ドロップエリア
        self.file_drop_frame = FileDropFrame(
            parent, on_files_selected=self._on_files_selected, height=120
        )
        self.file_drop_frame.pack(fill="x", pady=(0, 10))

        # 選択されたファイルリスト
        self.file_list_display = FileListDisplay(parent, height=150)
        self.file_list_display.pack(fill="x", pady=(0, 20))

    def _build_output_settings_area(self, parent: ctk.CTkFrame) -> None:
        """出力設定エリア構築"""
        output_section_label = ctk.CTkLabel(
            parent, text="📤 出力設定", **KumihanTheme.get_label_style("primary")
        )
        output_section_label.pack(anchor="w", pady=(0, 10))

        output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        output_frame.pack(fill="x", pady=(0, 20))

        output_dir_btn = ctk.CTkButton(
            output_frame,
            text="📁 出力フォルダ選択",
            command=self._select_output_directory,
            **KumihanTheme.get_button_style("secondary"),
        )
        output_dir_btn.pack(side="left")

        self.output_label = ctk.CTkLabel(
            output_frame,
            text="（未選択 - デフォルト: 元ファイルと同じ場所）",
            **KumihanTheme.get_label_style("secondary"),
        )
        self.output_label.pack(side="left", padx=(10, 0))

    def _build_convert_area(self, parent: ctk.CTkFrame) -> None:
        """変換実行エリア構築"""
        convert_frame = ctk.CTkFrame(parent, fg_color="transparent")
        convert_frame.pack(fill="x", pady=(0, 20))

        self.convert_button = ctk.CTkButton(
            convert_frame,
            text="🚀 HTML変換実行",
            command=self._start_conversion,
            **KumihanTheme.get_button_style("primary"),
            width=200,
            height=50,
            font=("Helvetica", 16, "bold"),
        )
        self.convert_button.pack()

    def _build_status_area(self, parent: ctk.CTkFrame) -> None:
        """ステータス・進捗エリア構築"""
        status_section_label = ctk.CTkLabel(
            parent, text="📊 変換状況", **KumihanTheme.get_label_style("primary")
        )
        status_section_label.pack(anchor="w", pady=(0, 10))

        # 進捗バー
        self.progress_bar = ctk.CTkProgressBar(
            parent, progress_color=KumihanTheme.PRIMARY_COLOR, height=20
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))
        self.progress_bar.set(0)

        # ステータスラベル
        self.status_label = ctk.CTkLabel(
            parent, text="待機中...", **KumihanTheme.get_label_style("secondary")
        )
        self.status_label.pack(anchor="w")

    def _on_files_selected(self, files: List[Path]) -> None:
        """ファイル選択コールバック"""
        self.selected_files = files
        self.file_list_display.update_file_list(files)
        
        # 詳細ログ
        self.debug_logger.log_ui_event("file_selection", {
            "file_count": len(files),
            "files": [f.name for f in files],
            "total_size": sum(f.stat().st_size for f in files if f.exists())
        })
        self.logger.info(f"ファイル選択更新: {len(files)}件")

    def _clear_files(self) -> None:
        """ファイルリストをクリア"""
        self.selected_files.clear()
        self.file_drop_frame.clear_selection()
        self.file_list_display.update_file_list([])
        self.logger.info("ファイルリストをクリア")

    def _select_output_directory(self) -> None:
        """出力ディレクトリ選択"""
        directory = filedialog.askdirectory(title="出力フォルダを選択")

        if directory:
            self.output_directory = Path(directory)
            self.output_label.configure(text=f"📁 {self.output_directory}")
            self.logger.info(f"出力ディレクトリ選択: {self.output_directory}")

    def _start_conversion(self) -> None:
        """変換処理開始"""
        if not self.selected_files:
            messagebox.showwarning("警告", "変換するファイルを選択してください。")
            return

        if self.is_converting:
            messagebox.showinfo(
                "情報", "変換処理が実行中です。しばらくお待ちください。"
            )
            return

        # UIを変換中モードに変更
        self._set_converting_mode(True)

        # バックグラウンドで変換実行
        conversion_thread = threading.Thread(target=self._run_conversion)
        conversion_thread.daemon = True
        conversion_thread.start()

    def _run_conversion(self) -> None:
        """バックグラウンド変換処理"""
        import time
        start_time = time.time()
        
        try:
            # 変換開始ログ
            self.debug_logger.log_conversion_start(
                self.selected_files, 
                str(self.output_directory) if self.output_directory else None
            )
            
            self.progress_queue.put(("status", "変換処理を開始しています..."))
            self.progress_queue.put(("progress", 0.1))

            # ConvertProcessorを使用して変換
            processor = ConvertProcessor()

            total_files = len(self.selected_files)
            converted_files = []

            for i, file_path in enumerate(self.selected_files):
                # ファイル別の進捗更新
                base_progress = i / total_files
                self.debug_logger.log_conversion_progress(i+1, total_files, file_path.name)
                self.progress_queue.put(
                    ("status", f"変換中: {file_path.name} ({i+1}/{total_files})")
                )
                self.progress_queue.put(("progress", base_progress))

                # 出力ディレクトリ決定
                if self.output_directory:
                    output_dir = str(self.output_directory)
                else:
                    output_dir = str(file_path.parent)

                # 変換実行（シンプルなプログレス設定）
                try:
                    output_file = processor.convert_file(
                        input_path=file_path,
                        output_dir=output_dir,
                        progress_level="minimal",  # GUI用に簡素化
                        show_progress_tooltip=False,  # GUI内プログレス使用
                        enable_cancellation=False,  # GUI側で制御
                        continue_on_error=True,  # 他ファイルの変換を継続
                        graceful_errors=True,  # エラー情報を収集
                    )
                    converted_files.append(output_file)
                    self.logger.info(
                        f"変換成功: {file_path.name} -> {output_file.name}"
                    )

                except Exception as file_error:
                    self.logger.error(
                        f"ファイル変換エラー {file_path.name}: {file_error}"
                    )
                    # 個別ファイルエラーは記録するが処理を継続
                    self.progress_queue.put(
                        ("warning", f"⚠️ {file_path.name}: {str(file_error)}")
                    )

            # 完了処理とログ
            end_time = time.time()
            duration = end_time - start_time
            
            if converted_files:
                success_count = len(converted_files)
                total_count = len(self.selected_files)
                
                # 結果ログ
                self.debug_logger.log_conversion_result(success_count, total_count, duration)
                
                self.progress_queue.put(("progress", 1.0))
                self.progress_queue.put(
                    (
                        "status",
                        f"✅ 変換完了！ {success_count}/{total_count}ファイル処理完了",
                    )
                )
                self.progress_queue.put(("complete", True))
                self.progress_queue.put(("result_files", converted_files))
            else:
                raise Exception("すべてのファイル変換に失敗しました")

        except Exception as e:
            # エラーログ詳細記録
            self.debug_logger.log_error("conversion_error", str(e), {
                "selected_files": [str(f) for f in self.selected_files],
                "output_directory": str(self.output_directory) if self.output_directory else None,
                "duration": time.time() - start_time
            })
            
            self.logger.error(f"変換エラー: {e}")
            self.progress_queue.put(("error", str(e)))
            self.progress_queue.put(("complete", False))

    def _check_progress_queue(self) -> None:
        """進捗キューの定期チェック"""
        try:
            while True:
                message_type, value = self.progress_queue.get_nowait()

                if message_type == "status":
                    self.status_label.configure(text=value)
                elif message_type == "progress":
                    self.progress_bar.set(value)
                elif message_type == "warning":
                    self.status_label.configure(text=value)
                    # 警告は継続して処理
                elif message_type == "complete":
                    self._set_converting_mode(False)
                    if value:  # 成功
                        messagebox.showinfo("完了", "変換が正常に完了しました！")
                    break
                elif message_type == "error":
                    self._set_converting_mode(False)
                    messagebox.showerror(
                        "エラー", f"変換エラーが発生しました:\n{value}"
                    )
                    break
                elif message_type == "result_files":
                    # 変換完了ファイルの結果表示（将来的に結果ビューアー等で活用）
                    self.logger.info(f"変換完了ファイル: {len(value)}件")

        except queue.Empty:
            pass

        # 100ms後に再チェック
        self.root.after(100, self._check_progress_queue)

    def _set_converting_mode(self, converting: bool) -> None:
        """変換中モードの切り替え"""
        self.is_converting = converting

        if converting:
            self.convert_button.configure(text="🔄 変換中...", state="disabled")
            self.status_label.configure(text="変換処理を準備中...")
            self.progress_bar.set(0)
        else:
            self.convert_button.configure(text="🚀 HTML変換実行", state="normal")
            if not converting:  # エラーでない場合
                self.progress_bar.set(0)

    def run(self) -> None:
        """アプリケーション実行"""
        self.logger.info("GUI アプリケーション起動")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("ユーザーによる停止")
        except Exception as e:
            self.logger.error(f"GUI エラー: {e}")
            messagebox.showerror("致命的エラー", f"アプリケーションエラー:\n{e}")
        finally:
            self.logger.info("GUI アプリケーション終了")


def main() -> None:
    """GUIアプリケーションのメインエントリーポイント"""
    app = KumihanFormatterApp()
    app.run()


if __name__ == "__main__":
    main()
