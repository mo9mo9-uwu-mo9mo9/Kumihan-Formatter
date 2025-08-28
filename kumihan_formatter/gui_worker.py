"""
GUI バックグラウンド処理ワーカー
gui_pyqt6.py分割版 - ConversionWorker専用モジュール
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal


class ConversionWorker(QThread):
    """変換処理ワーカー（別スレッド）"""

    progress_updated = pyqtSignal(int, str)  # progress, status
    conversion_finished = pyqtSignal(int, int)  # success_count, total_count
    conversion_error = pyqtSignal(str)  # error_message

    def __init__(self, files: List[Path], output_dir: Optional[Path]):
        super().__init__()
        self.files = files
        self.output_dir = output_dir

    def run(self) -> None:
        """変換実行"""
        try:
            success_count = 0
            total = len(self.files)

            for i, file_path in enumerate(self.files):
                # 進捗通知
                progress = int((i / total) * 100)
                self.progress_updated.emit(
                    progress, f"変換中: {file_path.name} ({i+1}/{total})"
                )

                # 出力ディレクトリ決定
                output_dir = (
                    str(self.output_dir) if self.output_dir else str(file_path.parent)
                )

                # CLI経由で変換
                try:
                    cmd = [
                        sys.executable,
                        "-m",
                        "kumihan_formatter.cli",
                        "convert",
                        str(file_path),
                        "--output-dir",
                        output_dir,
                        "--quiet",
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)
                    success_count += 1
                except subprocess.CalledProcessError:
                    pass  # エラーでも続行

            self.conversion_finished.emit(success_count, total)

        except Exception as e:
            self.conversion_error.emit(str(e))
