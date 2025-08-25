#!/usr/bin/env python3
"""Kumihan-Formatter GUI - PyQt6版（モダンUI・テーマ対応）"""

import sys
import subprocess
from pathlib import Path
from typing import List, Optional
import threading
import traceback

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QListWidget, QProgressBar, QFrame,
        QFileDialog, QMessageBox, QGroupBox
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

    def run(self):
        """変換実行"""
        try:
            success_count = 0
            total = len(self.files)
            
            for i, file_path in enumerate(self.files):
                # 進捗通知
                progress = int((i / total) * 100)
                self.progress_updated.emit(progress, f"変換中: {file_path.name} ({i+1}/{total})")
                
                # 出力ディレクトリ決定
                output_dir = str(self.output_dir) if self.output_dir else str(file_path.parent)
                
                # CLI経由で変換
                try:
                    cmd = [sys.executable, "-m", "kumihan_formatter.cli",
                          "convert", str(file_path), "--output-dir", output_dir, "--quiet"]
                    subprocess.run(cmd, check=True, capture_output=True)
                    success_count += 1
                except subprocess.CalledProcessError:
                    pass  # エラーでも続行
                
            self.conversion_finished.emit(success_count, total)
            
        except Exception as e:
            self.conversion_error.emit(str(e))


class KumihanFormatterPyQt6GUI(QMainWindow):
    """PyQt6版モダンGUI"""

    def __init__(self):
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

    def _setup_window(self):
        """ウィンドウ設定"""
        self.setWindowTitle("Kumihan-Formatter v0.9.0-alpha.8 (PyQt6)")
        self.setGeometry(200, 200, 700, 600)
        self.setMinimumSize(600, 500)

    def _build_modern_ui(self):
        """モダンUI構築"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # ヘッダー
        self._build_header(layout)
        
        # ファイル選択セクション
        self._build_file_section(layout)
        
        # 出力設定セクション
        self._build_output_section(layout)
        
        # 変換実行
        self._build_convert_section(layout)
        
        # ステータス
        self._build_status_section(layout)

    def _build_header(self, layout: QVBoxLayout):
        """ヘッダー構築"""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        
        # タイトル
        title_label = QLabel("🎨 Kumihan-Formatter")
        title_label.setFont(QFont("SF Pro Display", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        # バージョン
        version_label = QLabel("v0.9.0-alpha.8 (PyQt6)")
        version_label.setFont(QFont("SF Pro Display", 12))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setObjectName("versionLabel")
        header_layout.addWidget(version_label)
        
        layout.addWidget(header_frame)

    def _build_file_section(self, layout: QVBoxLayout):
        """ファイル選択セクション"""
        file_group = QGroupBox("📁 ファイル選択")
        file_group.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        file_layout = QVBoxLayout(file_group)
        
        # ボタン行
        button_layout = QHBoxLayout()
        
        select_btn = QPushButton("📁 ファイル選択")
        select_btn.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        select_btn.clicked.connect(self._select_files)
        select_btn.setObjectName("primaryButton")
        button_layout.addWidget(select_btn)
        
        button_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ クリア")
        clear_btn.setFont(QFont("SF Pro Display", 12))
        clear_btn.clicked.connect(self._clear_files)
        clear_btn.setObjectName("secondaryButton")
        button_layout.addWidget(clear_btn)
        
        file_layout.addLayout(button_layout)
        
        # ファイルリスト
        self.file_listbox = QListWidget()
        self.file_listbox.setMinimumHeight(150)
        self.file_listbox.setFont(QFont("SF Pro Display", 11))
        file_layout.addWidget(self.file_listbox)
        
        layout.addWidget(file_group)

    def _build_output_section(self, layout: QVBoxLayout):
        """出力設定セクション"""
        output_group = QGroupBox("📤 出力設定")
        output_group.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        output_layout = QHBoxLayout(output_group)
        
        output_btn = QPushButton("📁 出力フォルダ選択")
        output_btn.setFont(QFont("SF Pro Display", 12))
        output_btn.clicked.connect(self._select_output_dir)
        output_btn.setObjectName("secondaryButton")
        output_layout.addWidget(output_btn)
        
        self.output_label = QLabel("デフォルト: 元ファイルと同じ場所")
        self.output_label.setFont(QFont("SF Pro Display", 10))
        output_layout.addWidget(self.output_label)
        
        layout.addWidget(output_group)

    def _build_convert_section(self, layout: QVBoxLayout):
        """変換実行セクション"""
        convert_frame = QFrame()
        convert_layout = QHBoxLayout(convert_frame)
        convert_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.convert_btn = QPushButton("🚀 HTML変換実行")
        self.convert_btn.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setObjectName("primaryButton")
        self.convert_btn.setMinimumHeight(60)
        convert_layout.addWidget(self.convert_btn)
        
        layout.addWidget(convert_frame)

    def _build_status_section(self, layout: QVBoxLayout):
        """ステータスセクション"""
        status_group = QGroupBox("📊 変換状況")
        status_group.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        status_layout = QVBoxLayout(status_group)
        
        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        status_layout.addWidget(self.progress_bar)
        
        # ステータスラベル
        self.status_label = QLabel("待機中...")
        self.status_label.setFont(QFont("SF Pro Display", 11))
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)

    def _apply_modern_style(self):
        """モダンスタイル適用"""
        style = """
        QMainWindow {
            background-color: #FFFFFF;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #E0E0E0;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #FAFAFA;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #424242;
        }
        
        QPushButton#primaryButton {
            background-color: #2E7D32;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px 24px;
            font-weight: bold;
        }
        
        QPushButton#primaryButton:hover {
            background-color: #388E3C;
        }
        
        QPushButton#primaryButton:pressed {
            background-color: #1B5E20;
        }
        
        QPushButton#primaryButton:disabled {
            background-color: #BDBDBD;
        }
        
        QPushButton#secondaryButton {
            background-color: #1976D2;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
        }
        
        QPushButton#secondaryButton:hover {
            background-color: #1E88E5;
        }
        
        QLabel#titleLabel {
            color: #2E7D32;
        }
        
        QLabel#versionLabel {
            color: #757575;
        }
        
        QListWidget {
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            background-color: white;
            selection-background-color: #E8F5E8;
        }
        
        QProgressBar {
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            background-color: #F5F5F5;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(style)

    def _select_files(self):
        """ファイル選択"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Kumihan記法ファイルを選択",
            "",
            "Kumihan記法ファイル (*.kumihan *.txt *.md);;すべてのファイル (*)"
        )
        
        if files:
            self.selected_files = [Path(f) for f in files]
            self._update_file_list()

    def _update_file_list(self):
        """ファイルリスト更新"""
        self.file_listbox.clear()
        for i, file_path in enumerate(self.selected_files):
            self.file_listbox.addItem(f"{i+1}. {file_path.name}")

    def _clear_files(self):
        """ファイルクリア"""
        self.selected_files.clear()
        self.file_listbox.clear()

    def _select_output_dir(self):
        """出力ディレクトリ選択"""
        directory = QFileDialog.getExistingDirectory(self, "出力フォルダを選択")
        if directory:
            self.output_dir = Path(directory)
            self.output_label.setText(f"📁 {self.output_dir.name}")

    def _start_conversion(self):
        """変換開始"""
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "変換するファイルを選択してください。")
            return
            
        self.converting = True
        self.convert_btn.setText("🔄 変換中...")
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # ワーカースレッド開始
        self.worker = ConversionWorker(self.selected_files, self.output_dir)
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.conversion_finished.connect(self._conversion_complete)
        self.worker.conversion_error.connect(self._conversion_error)
        self.worker.start()

    def _update_progress(self, progress: int, status: str):
        """進捗更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)

    def _conversion_complete(self, success_count: int, total_count: int):
        """変換完了"""
        self.converting = False
        self.convert_btn.setText("🚀 HTML変換実行")
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"✅ 変換完了！ {success_count}/{total_count}ファイル")
        
        QMessageBox.information(self, "完了", f"{success_count}/{total_count}ファイルの変換が完了しました！")

    def _conversion_error(self, error_msg: str):
        """変換エラー"""
        self.converting = False
        self.convert_btn.setText("🚀 HTML変換実行")
        self.convert_btn.setEnabled(True)
        self.status_label.setText("❌ 変換エラー")
        
        QMessageBox.critical(self, "エラー", f"変換エラーが発生しました:\n{error_msg}")


def main():
    """メインエントリーポイント"""
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # モダンスタイル
        
        # アプリケーション情報
        app.setApplicationName("Kumihan-Formatter")
        app.setApplicationVersion("v0.9.0-alpha.8")
        
        window = KumihanFormatterPyQt6GUI()
        window.show()
        
        print("🎨 PyQt6 GUI Starting...")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"PyQt6 GUI Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()