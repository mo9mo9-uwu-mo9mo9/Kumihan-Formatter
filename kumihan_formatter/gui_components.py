"""
GUI UI構築コンポーネント
gui_pyqt6.py分割版 - UI構築・スタイル適用専用モジュール
"""

from pathlib import Path
from typing import Tuple, Optional
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QProgressBar,
)
from PyQt6.QtCore import Qt


class GUIComponents:
    """GUI構築コンポーネントクラス"""

    def __init__(self, main_window: QMainWindow):
        """GUI コンポーネント初期化"""
        self.main_window = main_window
        self.file_listbox: Optional[QListWidget] = None
        self.output_label: Optional[QLabel] = None
        self.convert_btn: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.status_label: Optional[QLabel] = None

    def build_modern_ui(self) -> None:
        """モダンUIレイアウト構築"""
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 各セクション構築
        self.build_header()
        self.build_file_section()
        self.build_output_section()
        self.build_convert_section()
        self.build_status_section()

        # スタイル適用
        self.apply_modern_style()

    def build_header(self) -> None:
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

        self.main_window.centralWidget().layout().addLayout(header_layout)

    def build_file_section(self) -> None:
        """ファイル選択セクション構築"""
        # セクションタイトル
        file_label = QLabel("📁 入力ファイル選択")
        file_label.setObjectName("sectionTitle")

        # ボタンレイアウト
        btn_layout = QHBoxLayout()

        select_btn = QPushButton("ファイル選択")
        select_btn.setObjectName("primaryBtn")

        clear_btn = QPushButton("クリア")
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

        self.main_window.centralWidget().layout().addLayout(file_section)

        # ボタンのイベントは外部で接続（main_windowのメソッド）
        return select_btn, clear_btn

    def build_output_section(self) -> None:
        """出力設定セクション構築"""
        # セクションタイトル
        output_title = QLabel("📤 出力設定")
        output_title.setObjectName("sectionTitle")

        # 出力ディレクトリ選択
        output_layout = QHBoxLayout()

        select_dir_btn = QPushButton("出力フォルダ選択")
        select_dir_btn.setObjectName("secondaryBtn")

        self.output_label = QLabel("出力先: 入力ファイルと同じ場所")
        self.output_label.setObjectName("pathLabel")

        output_layout.addWidget(select_dir_btn)
        output_layout.addWidget(self.output_label)
        output_layout.addStretch()

        # レイアウトに追加
        self.main_window.centralWidget().layout().addWidget(output_title)
        self.main_window.centralWidget().layout().addLayout(output_layout)

        # ボタンのイベントは外部で接続
        return select_dir_btn

    def build_convert_section(self) -> None:
        """変換セクション構築"""
        # 変換ボタン
        self.convert_btn = QPushButton("🚀 変換開始")
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.setMinimumHeight(50)

        # 中央配置
        convert_layout = QHBoxLayout()
        convert_layout.addStretch()
        convert_layout.addWidget(self.convert_btn)
        convert_layout.addStretch()

        self.main_window.centralWidget().layout().addLayout(convert_layout)

        # ボタンのイベントは外部で接続
        return self.convert_btn

    def build_status_section(self) -> None:
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
        self.main_window.centralWidget().layout().addWidget(status_title)
        self.main_window.centralWidget().layout().addWidget(self.progress_bar)
        self.main_window.centralWidget().layout().addWidget(self.status_label)

    def apply_modern_style(self) -> None:
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

        self.main_window.setStyleSheet(style)

    def get_widgets(self) -> dict:
        """作成したウィジェット取得"""
        return {
            "file_listbox": self.file_listbox,
            "output_label": self.output_label,
            "convert_btn": self.convert_btn,
            "progress_bar": self.progress_bar,
            "status_label": self.status_label,
        }

    def setup_complete_ui(
        self,
    ) -> Tuple[QPushButton, QPushButton, QPushButton, QPushButton]:
        """完全なUI構築とイベントボタン返却"""
        self.build_modern_ui()

        # ボタンを再取得（build内で作成されるため）
        select_btn, clear_btn = self.build_file_section()
        select_dir_btn = self.build_output_section()
        convert_btn = self.build_convert_section()

        return select_btn, clear_btn, select_dir_btn, convert_btn
