"""GUI Models for Kumihan-Formatter

Legacy wrapper - このファイルは後方互換性のために維持されています。
新しいアーキテクチャでは gui_models/ モジュールの分離されたコンポーネントを使用してください。

⚠️ Deprecated: 今後のバージョンでは削除予定です。
新しいインポートパス: from kumihan_formatter.gui_models import AppState
"""

import warnings

# 新しいモジュールからすべてをインポート
from .gui_models import *  # noqa: F403, F401

# 非推奨警告
warnings.warn(
    "gui_models.py is deprecated. Use 'from kumihan_formatter.gui_models import AppState' instead.",
    DeprecationWarning,
    stacklevel=2
)