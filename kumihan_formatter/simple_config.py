"""簡素化された設定管理 - Issue #400対応

初心者向けに簡素化されたKumihan-Formatterの設定管理。
統合設定システムの基本設定を使用し、互換性を維持します。

⚠️  DEPRECATION NOTICE - Issue #880 Phase 3:
このモジュールは非推奨です。新しい統一設定システムをご利用ください:
from kumihan_formatter.core.config.unified import get_unified_config_manager
"""

import warnings

from .config import create_config_manager


class SimpleConfig:
    """簡素化された設定クラス（統合設定システムへの互換性ラッパー）

    Issue #400対応: 統合設定システムの基本設定を使用し、
    既存のAPIとの互換性を維持するラッパークラス。
    """

    # 互換性のためのデフォルトCSS設定（参照用）
    DEFAULT_CSS = {
        "max_width": "800px",
        "background_color": "#f9f9f9",
        "container_background": "white",
        "text_color": "#333",
        "line_height": "1.8",
        "font_family": (
            "Hiragino Kaku Gothic ProN, Hiragino Sans, " "Yu Gothic, Meiryo, sans-serif"
        ),
    }

    def __init__(self) -> None:
        """簡素化された設定を初期化（統合設定システムを使用）"""
        warnings.warn(
            "SimpleConfigは非推奨です。"
            "kumihan_formatter.core.config.unified.get_unified_config_manager()を使用してください。",
            DeprecationWarning,
            stacklevel=2,
        )
        # 統合設定管理システムの基本設定を使用
        self._manager = create_config_manager(config_type="base")

        # 互換性のため、CSS変数も保持
        self.css_vars = self._manager.get_css_variables()

    def get_css_variables(self) -> dict[str, str]:
        """CSS変数を取得（統合設定システムに委譲）

        Returns:
            dict[str, str]: CSS変数の辞書
        """
        return self._manager.get_css_variables()

    def get_theme_name(self) -> str:
        """テーマ名を取得（統合設定システムに委譲）

        Returns:
            str: テーマ名
        """
        return self._manager.get_theme_name()


def create_simple_config() -> SimpleConfig:
    """簡素化された設定を作成（統合設定システムを使用）

    Returns:
        SimpleConfig: 簡素化された設定オブジェクト
    """
    return SimpleConfig()
