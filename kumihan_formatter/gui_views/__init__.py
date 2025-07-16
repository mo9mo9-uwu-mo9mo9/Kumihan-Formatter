"""GUI Views for Kumihan-Formatter

Single Responsibility Principle適用: GUI View層の機能分離と統合
Issue #476 Phase2対応 - gui_views.py分割完了

分割結果:
- main_window.py: メインウィンドウ管理
- widgets.py: 基本ウィジェット（ヘッダー、ファイル選択、オプション）
- controls.py: コントロール（ボタン、進捗、ログ）
- dialogs.py: ダイアログウィンドウ
- main_view.py: 統合ビュー管理
"""

# コントロール
from .controls import ActionButtonFrame, LogFrame, ProgressFrame

# ダイアログ
from .dialogs import HelpDialog

# 統合ビュー
from .main_view import MainView

# メインウィンドウ
from .main_window import MainWindow

# 基本ウィジェット
from .widgets import FileSelectionFrame, HeaderFrame, OptionsFrame

# 後方互換性のために全クラスをエクスポート
__all__ = [
    # メインウィンドウ
    "MainWindow",
    # 基本ウィジェット
    "HeaderFrame",
    "FileSelectionFrame",
    "OptionsFrame",
    # コントロール
    "ActionButtonFrame",
    "ProgressFrame",
    "LogFrame",
    # ダイアログ
    "HelpDialog",
    # 統合ビュー
    "MainView",
]
