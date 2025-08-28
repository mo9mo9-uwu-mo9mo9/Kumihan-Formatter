"""
Kumihan Formatter PyQt6 GUI - 軽量化版
GUIワーカーとコンポーネントを分離した最適化バージョン
"""

import sys
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

# 分離されたモジュール
from .gui_worker import ConversionWorker
from .gui_components import GUIComponents


class KumihanFormatterPyQt6GUI(QMainWindow):
    """Kumihan Formatter PyQt6 GUI - 軽量版"""

    def __init__(self):
        super().__init__()

        # 状態管理
        self.selected_files: List[Path] = []
        self.output_dir: Optional[Path] = None
        self.converting: bool = False
        self.worker: Optional[ConversionWorker] = None

        # GUI構築システム初期化
        self.components = GUIComponents(self)

        # ウィンドウ基本設定
        self._setup_window()

        # UI構築とイベント接続
        self._build_complete_ui()

    def _setup_window(self) -> None:
        """ウィンドウ基本設定"""
        self.setWindowTitle("Kumihan Formatter - PyQt6版")
        self.setFixedSize(600, 500)

    def _build_complete_ui(self) -> None:
        """完全なUI構築とイベント接続"""
        # GUIComponentsでUI構築
        self.components.build_modern_ui()

        # ウィジェット参照取得
        widgets = self.components.get_widgets()
        self.file_listbox = widgets["file_listbox"]
        self.output_label = widgets["output_label"]
        self.convert_btn = widgets["convert_btn"]
        self.progress_bar = widgets["progress_bar"]
        self.status_label = widgets["status_label"]

        # イベント接続（手動でボタンを取得して接続）
        self._connect_events()

    def _connect_events(self) -> None:
        """イベントハンドラー接続"""
        # ボタンを検索して接続
        select_btns = self.findChildren(type(self.components.convert_btn))

        for btn in select_btns:
            if btn.text() == "ファイル選択":
                btn.clicked.connect(self._select_files)
            elif btn.text() == "クリア":
                btn.clicked.connect(self._clear_files)
            elif btn.text() == "出力フォルダ選択":
                btn.clicked.connect(self._select_output_dir)
            elif "変換開始" in btn.text():
                btn.clicked.connect(self._start_conversion)

    # ===== イベントハンドラー群 =====

    def _select_files(self) -> None:
        """ファイル選択"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "変換するファイルを選択",
            "",
            "テキストファイル (*.txt *.md *.kumihan);;すべてのファイル (*)",
        )

        if files:
            self.selected_files = [Path(f) for f in files]
            self._update_file_list()

    def _update_file_list(self) -> None:
        """ファイルリスト更新"""
        self.file_listbox.clear()
        for file_path in self.selected_files:
            self.file_listbox.addItem(str(file_path))

    def _clear_files(self) -> None:
        """ファイルリストクリア"""
        self.selected_files.clear()
        self.file_listbox.clear()

    def _select_output_dir(self) -> None:
        """出力ディレクトリ選択"""
        directory = QFileDialog.getExistingDirectory(self, "出力フォルダを選択")
        if directory:
            self.output_dir = Path(directory)
            self.output_label.setText(f"出力先: {directory}")

    def _start_conversion(self) -> None:
        """変換開始"""
        if not self.selected_files:
            return

        self.converting = True
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        # ワーカースレッド開始
        self.worker = ConversionWorker(self.selected_files, self.output_dir)
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.conversion_finished.connect(self._conversion_complete)
        self.worker.conversion_error.connect(self._conversion_error)
        self.worker.start()

    def _update_progress(self, progress: int, status: str) -> None:
        """進捗更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)

    def _conversion_complete(self, success_count: int, total_count: int) -> None:
        """変換完了"""
        self.converting = False
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(
            f"変換完了: {success_count}/{total_count} ファイル成功"
        )

        QMessageBox.information(
            self,
            "変換完了",
            f"変換が完了しました。\n成功: {success_count}/{total_count} ファイル",
        )

    def _conversion_error(self, error_message: str) -> None:
        """変換エラー"""
        self.converting = False
        self.convert_btn.setEnabled(True)
        self.status_label.setText("エラーが発生しました")

        QMessageBox.critical(
            self, "エラー", f"変換中にエラーが発生しました:\n{error_message}"
        )


def main() -> None:
    """メインエントリーポイント"""
    app = QApplication(sys.argv)

    # アプリケーション設定
    app.setApplicationName("Kumihan Formatter")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Kumihan Project")

    # メインウィンドウ表示
    window = KumihanFormatterPyQt6GUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
