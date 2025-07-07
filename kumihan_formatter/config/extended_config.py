"""拡張設定クラス - Issue #400対応

設定管理の統合リファクタリングの一環として作成された拡張設定クラス。
マーカー、テーマ、高度なCSS設定など、フル機能を提供する。
"""

from typing import Any, Dict, Optional

from .base_config import BaseConfig


class ExtendedConfig(BaseConfig):
    """拡張設定クラス

    BaseConfigを継承し、マーカー定義、テーマシステム、
    高度なCSS設定などの拡張機能を提供する。
    """

    # デフォルトマーカー定義
    DEFAULT_MARKERS = {
        "太字": {"tag": "strong"},
        "イタリック": {"tag": "em"},
        "枠線": {"tag": "div", "class": "box"},
        "ハイライト": {"tag": "div", "class": "highlight"},
        "見出し1": {"tag": "h1"},
        "見出し2": {"tag": "h2"},
        "見出し3": {"tag": "h3"},
        "見出し4": {"tag": "h4"},
        "見出し5": {"tag": "h5"},
        "折りたたみ": {"tag": "details", "summary": "詳細を表示"},
        "ネタバレ": {"tag": "details", "summary": "ネタバレを表示"},
    }

    # デフォルトテーマ定義
    DEFAULT_THEMES = {
        "default": {
            "name": "デフォルト",
            "css": {
                "background_color": "#f9f9f9",
                "container_background": "white",
                "text_color": "#333",
            },
        },
        "dark": {
            "name": "ダーク",
            "css": {
                "background_color": "#1a1a1a",
                "container_background": "#2d2d2d",
                "text_color": "#e0e0e0",
            },
        },
        "sepia": {
            "name": "セピア",
            "css": {
                "background_color": "#f4f1ea",
                "container_background": "#fdf6e3",
                "text_color": "#5c4b37",
            },
        },
    }

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """拡張設定を初期化

        Args:
            config_data: 設定データ
        """
        super().__init__(config_data)

        # マーカー定義の初期化
        self._markers = self.DEFAULT_MARKERS.copy()
        if self._config.get("markers") and isinstance(self._config["markers"], dict):
            self._markers.update(self._config["markers"])

        # テーマ定義の初期化
        self._themes = self.DEFAULT_THEMES.copy()
        if self._config.get("themes") and isinstance(self._config["themes"], dict):
            self._themes.update(self._config["themes"])

        # 現在のテーマ設定
        self._current_theme = self._config.get("theme", "default")

        # テーマ適用
        self._apply_theme()

    def _apply_theme(self) -> None:
        """現在のテーマをCSS変数に適用"""
        if self._current_theme in self._themes:
            theme_css = self._themes[self._current_theme].get("css", {})
            self._css_vars.update(theme_css)

    def get_markers(self) -> Dict[str, Dict[str, Any]]:
        """マーカー定義を取得

        Returns:
            Dict[str, Dict[str, Any]]: マーカー定義辞書
        """
        return self._markers.copy()

    def add_marker(self, name: str, definition: Dict[str, Any]) -> None:
        """マーカーを追加

        Args:
            name: マーカー名
            definition: マーカー定義
        """
        if not isinstance(definition, dict) or "tag" not in definition:
            raise ValueError(f"マーカー定義が不正です: {name}")

        self._markers[name] = definition

    def remove_marker(self, name: str) -> bool:
        """マーカーを削除

        Args:
            name: マーカー名

        Returns:
            bool: 削除に成功した場合True
        """
        if name in self._markers:
            del self._markers[name]
            return True
        return False

    def get_themes(self) -> Dict[str, Dict[str, Any]]:
        """テーマ定義を取得

        Returns:
            Dict[str, Dict[str, Any]]: テーマ定義辞書
        """
        return self._themes.copy()

    def add_theme(self, theme_id: str, theme_data: Dict[str, Any]) -> None:
        """テーマを追加

        Args:
            theme_id: テーマID
            theme_data: テーマデータ
        """
        if not isinstance(theme_data, dict) or "name" not in theme_data:
            raise ValueError(f"テーマ定義が不正です: {theme_id}")

        self._themes[theme_id] = theme_data

    def set_theme(self, theme_id: str) -> bool:
        """テーマを設定

        Args:
            theme_id: テーマID

        Returns:
            bool: 設定に成功した場合True
        """
        if theme_id in self._themes:
            self._current_theme = theme_id
            self._apply_theme()
            return True
        return False

    def get_current_theme(self) -> str:
        """現在のテーマIDを取得

        Returns:
            str: テーマID
        """
        return self._current_theme

    def get_theme_name(self) -> str:
        """現在のテーマ名を取得

        Returns:
            str: テーマ名
        """
        if self._current_theme in self._themes:
            return self._themes[self._current_theme].get("name", "不明")
        return "不明"

    def validate(self) -> bool:
        """設定の妥当性をチェック

        Returns:
            bool: 設定が有効な場合True
        """
        if not super().validate():
            return False

        # マーカー定義の検証
        for name, marker in self._markers.items():
            if not isinstance(marker, dict) or "tag" not in marker:
                return False

        # テーマ定義の検証
        for theme_id, theme_data in self._themes.items():
            if not isinstance(theme_data, dict) or "name" not in theme_data:
                return False

        # 現在のテーマの検証
        if self._current_theme not in self._themes:
            return False

        return True

    def merge_config(self, other_config: Dict[str, Any]) -> None:
        """他の設定をマージ

        Args:
            other_config: マージする設定辞書
        """
        if not isinstance(other_config, dict):
            return

        # マーカーのマージ
        if "markers" in other_config and isinstance(other_config["markers"], dict):
            self._markers.update(other_config["markers"])

        # テーマのマージ
        if "themes" in other_config and isinstance(other_config["themes"], dict):
            self._themes.update(other_config["themes"])

        # CSS設定のマージ
        if "css" in other_config and isinstance(other_config["css"], dict):
            self._css_vars.update(other_config["css"])

        # テーマ設定の更新
        if "theme" in other_config and other_config["theme"] in self._themes:
            self.set_theme(other_config["theme"])

        # その他の設定のマージ
        self._config.update(other_config)

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書として取得

        Returns:
            Dict[str, Any]: 設定辞書
        """
        config_dict = super().to_dict()
        config_dict.update(
            {
                "markers": self._markers,
                "themes": self._themes,
                "theme": self._current_theme,
                "css": self._css_vars,
            }
        )
        return config_dict
