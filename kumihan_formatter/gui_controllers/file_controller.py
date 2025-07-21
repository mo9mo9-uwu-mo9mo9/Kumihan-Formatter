"""File operations controller for Kumihan-Formatter GUI

Single Responsibility Principle適用: ファイル操作制御の分離
Issue #476 Phase2対応 - gui_controller.py分割（1/3）
"""

import platform
import subprocess
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass  # ..gui_models.AppState removed as unused
    # ..gui_views.MainView removed as unused

# デバッグロガーのインポート
try:
    from ..core.debug_logger import (
        debug,
        info,
        log_gui_event,
    )
except ImportError:
    # Fallbacksを定義
    def debug(*args: Any, **kwargs: Any) -> None:
        pass

    def info(*args: Any, **kwargs: Any) -> None:
        pass

    def log_gui_event(*args: Any, **kwargs: Any) -> None:
        pass


class FileController:
    """ファイル操作制御クラス

    ファイル選択・ディレクトリ操作・ファイルマネージャー連携を担当
    """

    def __init__(self, view: Any) -> None:
        """ファイルコントローラーの初期化"""
        self.view = view
        # 後方互換性のため、旧形式もサポート
        if hasattr(view, "app_state"):
            self.app_state = view.app_state
            self.main_view = view
        else:
            # テスト用の単純な view オブジェクト
            self.app_state = None
            self.main_view = view

    def browse_input_file(self) -> None:
        """入力ファイルの参照"""
        log_gui_event("button_click", "browse_input_file")

        filename = filedialog.askopenfilename(
            title="変換するテキストファイルを選択",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
        )

        if filename:
            info(f"Input file selected: {filename}")
            # テスト環境での互換性を確保
            if hasattr(self.view, "input_file_var"):
                self.view.input_file_var.set(filename)
            if hasattr(self.view, "update_output_preview"):
                self.view.update_output_preview()

            # 本来のロジック（app_stateが存在する場合）
            if self.app_state:
                self.app_state.config.set_input_file(filename)
            if hasattr(self.main_view, "log_frame"):
                self.main_view.log_frame.add_message(
                    f"入力ファイル: {Path(filename).name}"
                )
        else:
            debug("Input file selection cancelled")

    def browse_output_dir(self) -> None:
        """出力ディレクトリの参照"""
        log_gui_event("button_click", "browse_output_dir")

        dirname = filedialog.askdirectory(title="出力フォルダを選択")
        if dirname:
            # テスト環境での互換性を確保
            if hasattr(self.view, "output_dir_var"):
                self.view.output_dir_var.set(dirname)
            if hasattr(self.view, "update_output_preview"):
                self.view.update_output_preview()

            # 本来のロジック（app_stateが存在する場合）
            if self.app_state:
                self.app_state.config.set_output_dir(dirname)
            if hasattr(self.main_view, "log_frame"):
                self.main_view.log_frame.add_message(f"出力フォルダ: {dirname}")

    def open_directory_in_file_manager(self, directory_path: Path) -> None:
        """ディレクトリをファイルマネージャーで開く

        Args:
            directory_path: 開くディレクトリのパス
        """
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(directory_path)], check=True)
            elif platform.system() == "Windows":  # Windows
                subprocess.run(["explorer", str(directory_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(directory_path)], check=True)
        except subprocess.CalledProcessError as e:
            debug(f"Failed to open directory in file manager: {e}")
        except FileNotFoundError:
            debug("File manager not found")
