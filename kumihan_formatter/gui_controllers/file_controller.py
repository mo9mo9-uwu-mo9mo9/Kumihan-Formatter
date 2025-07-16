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
    from ..gui_models import AppState
    from ..gui_views import MainView

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

    def __init__(self, app_state: "AppState", main_view: "MainView") -> None:
        """ファイルコントローラーの初期化"""
        self.app_state = app_state
        self.main_view = main_view

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