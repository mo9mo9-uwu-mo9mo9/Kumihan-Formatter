"""GUI Controllers for Kumihan-Formatter

Single Responsibility Principle適用: GUI Controller層の機能分離と統合
Issue #476対応 - gui_controller.py分割完了

分割結果:
- main_controller.py: メインコントローラー統合管理
- file_controller.py: ファイル操作制御
- conversion_controller.py: 変換・サンプル生成制御
- gui_controller.py: 統合GUIコントローラー（後方互換性）
"""

from .conversion_controller import ConversionController

# サブコントローラー
from .file_controller import FileController

# 統合コントローラー
from .gui_controller import GuiController, create_gui_application
from .main_controller import MainController

# 後方互換性のために全クラスをエクスポート
__all__ = [
    # サブコントローラー
    "FileController",
    "ConversionController",
    "MainController",
    # 統合コントローラー
    "GuiController",
    "create_gui_application",
]
