#!/usr/bin/env python3
"""Kumihan-Formatter GUI - PyQt6版（モダンUI・テーマ対応）"""

import sys
import subprocess
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
import threading
import traceback

if TYPE_CHECKING:
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QListWidget,
        QProgressBar,
        QFrame,
        QFileDialog,
        QMessageBox,
        QGroupBox,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QPalette, QColor
else:
    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QMainWindow,
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QListWidget,
            QProgressBar,
            QFrame,
            QFileDialog,
            QMessageBox,
            QGroupBox,
        )
        from PyQt6.QtCore import Qt, QThread, pyqtSignal
        from PyQt6.QtGui import QFont, QPalette, QColor
    except ImportError:
        print("PyQt6 not installed. Install with: pip install PyQt6")
        sys.exit(1)


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


class KumihanFormatterPyQt6GUI(QMainWindow):
    """PyQt6版モダンGUI"""

    def __init__(self) -> None:
        super().__init__()

        # ログ用
        Path("tmp").mkdir(exist_ok=True)

        # 変数
        self.selected_files: List[Path] = []
        self.output_dir: Optional[Path] = None
        self.converting = False
        self.worker: Optional[ConversionWorker] = None

        self._setup_window()
        self._build_modern_ui()
        self._apply_modern_style()

    def _setup_window(self) -> None:
        """ウィンドウ設定"""
        self.setWindowTitle("Kumihan Formatter - PyQt6 GUI")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)

    def _build_modern_ui(self) -> None:
        """モダンUIレイアウト構築"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 各セクション構築
        self._build_header()
        self._build_file_section()
        self._build_output_section()
        self._build_convert_section()
        self._build_status_section()

        # スタイル適用
        self._apply_modern_style()

    def _build_header(self) -> None:
        """ヘッダーセクション構築"""
        # タイトル
        title = QLabel("🎨 Kumihan Formatter")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # サブタイトル
        subtitle = QLabel("日本語文書整形ツール - PyQt6版")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # レイアウトに追加
        header_layout = QVBoxLayout()
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        self.centralWidget().layout().addLayout(header_layout)

    def _build_file_section(self) -> None:
        """ファイル選択セクション構築"""
        # セクションタイトル
        file_label = QLabel("📁 入力ファイル選択")
        file_label.setObjectName("sectionTitle")

        # ボタンレイアウト
        btn_layout = QHBoxLayout()

        select_btn = QPushButton("ファイル選択")
        select_btn.clicked.connect(self._select_files)
        select_btn.setObjectName("primaryBtn")

        clear_btn = QPushButton("クリア")
        clear_btn.clicked.connect(self._clear_files)
        clear_btn.setObjectName("secondaryBtn")

        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()

        # ファイルリスト
        self.file_listbox = QListWidget()
        self.file_listbox.setMaximumHeight(120)

        # レイアウトに追加
        file_section = QVBoxLayout()
        file_section.addWidget(file_label)
        file_section.addLayout(btn_layout)
        file_section.addWidget(self.file_listbox)

        self.centralWidget().layout().addLayout(file_section)

    def _build_output_section(self) -> None:
        """出力設定セクション構築"""
        # セクションタイトル
        output_title = QLabel("📤 出力設定")
        output_title.setObjectName("sectionTitle")

        # 出力ディレクトリ選択
        output_layout = QHBoxLayout()

        select_dir_btn = QPushButton("出力フォルダ選択")
        select_dir_btn.clicked.connect(self._select_output_dir)
        select_dir_btn.setObjectName("secondaryBtn")

        self.output_label = QLabel("出力先: 入力ファイルと同じ場所")
        self.output_label.setObjectName("pathLabel")

        output_layout.addWidget(select_dir_btn)
        output_layout.addWidget(self.output_label)
        output_layout.addStretch()

        # レイアウトに追加
        self.centralWidget().layout().addWidget(output_title)
        self.centralWidget().layout().addLayout(output_layout)

    def _build_convert_section(self) -> None:
        """変換セクション構築"""
        # 変換ボタン
        self.convert_btn = QPushButton("🚀 変換開始")
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.setMinimumHeight(50)

        # 中央配置
        convert_layout = QHBoxLayout()
        convert_layout.addStretch()
        convert_layout.addWidget(self.convert_btn)
        convert_layout.addStretch()

        self.centralWidget().layout().addLayout(convert_layout)

    def _build_status_section(self) -> None:
        """ステータスセクション構築"""
        # ステータスタイトル
        status_title = QLabel("📊 変換状況")
        status_title.setObjectName("sectionTitle")

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setObjectName("progressBar")

        # ステータスラベル
        self.status_label = QLabel("準備完了")
        self.status_label.setObjectName("statusLabel")

        # レイアウトに追加
        self.centralWidget().layout().addWidget(status_title)
        self.centralWidget().layout().addWidget(self.progress_bar)
        self.centralWidget().layout().addWidget(self.status_label)

    def _apply_modern_style(self) -> None:
        """モダンスタイル適用"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        #title {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        #subtitle {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 20px;
        }
        
        #sectionTitle {
            font-size: 16px;
            font-weight: bold;
            color: #34495e;
            margin: 15px 0 10px 0;
        }
        
        #primaryBtn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        
        #primaryBtn:hover {
            background-color: #2980b9;
        }
        
        #secondaryBtn {
            background-color: #95a5a6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
        }
        
        #secondaryBtn:hover {
            background-color: #7f8c8d;
        }
        
        #convertBtn {
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
        }
        
        #convertBtn:hover {
            background-color: #229954;
        }
        
        #convertBtn:disabled {
            background-color: #bdc3c7;
        }
        
        #pathLabel {
            color: #7f8c8d;
            font-style: italic;
            margin-left: 10px;
        }
        
        #progressBar {
            height: 20px;
            border-radius: 10px;
            background-color: #ecf0f1;
            text-align: center;
        }
        
        #progressBar::chunk {
            background-color: #3498db;
            border-radius: 10px;
        }
        
        #statusLabel {
            color: #34495e;
            font-weight: bold;
            margin: 10px 0;
        }
        
        QListWidget {
            background-color: white;
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
        }
        """

        self.setStyleSheet(style)

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
        self.selected_files = []
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

    def _update_progress(self, value: int, status: str) -> None:
        """プログレス更新"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)

    def _conversion_complete(self, success_count: int, total_count: int) -> None:
        """変換完了処理"""
        self.converting = False
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(100)

        if success_count == total_count:
            self.status_label.setText(f"✅ 変換完了！ ({success_count}/{total_count})")
        else:
            self.status_label.setText(f"⚠️ 部分完了 ({success_count}/{total_count})")

        self.worker = None

    def _conversion_error(self, error_message: str) -> None:
        """変換エラー処理"""
        self.converting = False
        self.convert_btn.setEnabled(True)
        self.status_label.setText(f"❌ エラー: {error_message}")
        self.worker = None


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
