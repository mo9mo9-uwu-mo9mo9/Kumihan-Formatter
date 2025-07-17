"""GUI Views for Kumihan-Formatter

Legacy wrapper - このファイルは後方互換性のために維持されています。
新しいアーキテクチャでは gui_views/ モジュールの分離されたコンポーネントを使用してください。

⚠️ Deprecated: 今後のバージョンでは削除予定です。
新しいインポートパス: from kumihan_formatter.gui_views import MainView
"""

import warnings

# 新しいモジュールからすべてをインポート
from .gui_views import *  # noqa: F403, F401

# 非推奨警告
warnings.warn(
    "gui_views.py is deprecated. Use 'from kumihan_formatter.gui_views import MainView' instead.",
    DeprecationWarning,
    stacklevel=2,
)
