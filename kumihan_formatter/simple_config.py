"""簡素化された設定管理

初心者向けに簡素化されたKumihan-Formatterの設定管理。
カスタムマーカーは削除し、固定のCSS設定のみを提供。
"""

from typing import Dict


class SimpleConfig:
    """簡素化された設定クラス

    カスタムマーカーや複雑な設定機能を削除し、
    基本的なCSS設定のみを提供する初心者向け設定。
    """

    # 固定のCSS設定（テーマなし、カスタマイズなし）
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
        """簡素化された設定を初期化"""
        self.css_vars = self.DEFAULT_CSS.copy()

    def get_css_variables(self) -> Dict[str, str]:
        """CSS変数を取得

        Returns:
            Dict[str, str]: CSS変数の辞書
        """
        return self.css_vars.copy()

    def get_theme_name(self) -> str:
        """テーマ名を取得（固定値）

        Returns:
            str: 常に"デフォルト"を返す
        """
        return "デフォルト"


def create_simple_config() -> SimpleConfig:
    """簡素化された設定を作成

    Returns:
        SimpleConfig: 簡素化された設定オブジェクト
    """
    return SimpleConfig()
