"""GUI Models for Kumihan-Formatter

Single Responsibility Principle適用: GUI Model層の機能分離と統合
Issue #476 Phase2対応 - gui_models.py分割完了

分割結果:
- config_model.py: 設定・変換状態管理
- file_model.py: ファイル操作管理
- state_model.py: ログ・アプリ状態管理
"""

from .conversion_state import ConversionState

# ファイル管理モデル
from .file_model import FileManager

# 設定・変換状態モデル
from .gui_config import GuiConfig

# ログ・アプリ状態モデル
from .state_model import AppState, LogManager

# 後方互換性のために全クラスをエクスポート
__all__ = [
    # 設定・変換状態
    "GuiConfig",
    "ConversionState",
    # ファイル管理
    "FileManager",
    # ログ・アプリ状態
    "LogManager",
    "AppState",
]
