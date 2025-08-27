"""設定管理モジュール - Issue #400対応

統合設定システムへの移行により、既存のConfigクラスは
新しい統合設定管理システムのラッパーとして機能します。

互換性維持のため、既存のAPIは保持されますが、
内部的には新しいExtendedConfigを使用します。
"""

import logging
from typing import Any

from rich.console import Console

# 新しい統合設定システムをインポート
# 統合完了 - より包括的なConfigManagerに移行
from .core.config.config_manager import ConfigManager

console = Console()
logger = logging.getLogger(__name__)


class Config:
    """設定管理クラス（統合設定システムへの互換性ラッパー）

    Issue #400対応: 新しい統合設定システムを内部的に使用しながら、
    既存のAPIとの互換性を維持するラッパークラス。
    """

    # 互換性のためのデフォルト設定（参照用）
    DEFAULT_CONFIG = {
        "markers": {
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
        },
        "theme": "default",
        "font_family": (
            "Hiragino Kaku Gothic ProN, Hiragino Sans, " "Yu Gothic, Meiryo, sans-serif"
        ),
        "css": {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8",
        },
        "themes": {
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
        },
    }

    def __init__(self, config_path: str | None = None):
        """設定管理を初期化（統合設定システムを使用）"""
        # 統合設定管理システムを使用
        self._manager = ConfigManager(config_type="extended", config_path=config_path)

        # 互換性のため、設定辞書も保持
        self.config = self._manager.to_dict()

    def load_config(self, config_path: str) -> bool:
        """設定ファイルを読み込む（統合設定システムに委譲）"""
        try:
            result: bool = self._manager.load_config(config_path)
            if result:
                # 設定辞書を更新
                self.config = self._manager.to_dict()
                console.print(
                    f"[green][完了] 設定ファイルを読み込みました:[/green] {config_path}"
                )
            else:
                console.print(
                    f"[yellow][警告]  設定ファイルが見つかりません:[/yellow] {config_path}"
                )
                console.print("[dim]   デフォルト設定を使用します[/dim]")
            return result
        except Exception as e:
            console.print(f"[red][エラー] 設定読み込み失敗:[/red] {e}")
            return False

    def _merge_config(self, user_config: dict[str, Any]):
        """ユーザー設定をデフォルト設定にマージ（統合設定システムに委譲）"""
        self._manager.merge_config(user_config)
        self.config = self._manager.to_dict()

        # ログ出力（互換性維持）
        if "themes" in user_config and isinstance(user_config["themes"], dict):
            console.print(
                f"[dim]   カスタムテーマ: {len(user_config['themes'])}個[/dim]"
            )
        if "markers" in user_config and isinstance(user_config["markers"], dict):
            console.print(
                f"[dim]   カスタムマーカー: {len(user_config['markers'])}個[/dim]"
            )
        if "theme" in user_config:
            theme_name = self._manager.get_theme_name()
            console.print(f"[dim]   テーマ: {theme_name}[/dim]")
        if "font_family" in user_config:
            console.print(f"[dim]   フォント: {user_config['font_family']}[/dim]")
        if "css" in user_config and isinstance(user_config["css"], dict):
            console.print(f"[dim]   カスタムCSS: {len(user_config['css'])}項目[/dim]")

    def get_markers(self) -> dict[str, dict[str, Any]]:
        """マーカー定義を取得（統合設定システムに委譲）"""
        markers: dict[str, dict[str, Any]] = self._manager.get_markers()
        return markers

    def get_css_variables(self) -> dict[str, str]:
        """CSS変数を取得（統合設定システムに委譲）"""
        variables: dict[str, str] = self._manager.get_css_variables()
        return variables

    def get_theme_name(self) -> str:
        """現在のテーマ名を取得（統合設定システムに委譲）"""
        theme_name: str = self._manager.get_theme_name()
        return theme_name

    def validate_config(self) -> bool:
        """設定の妥当性をチェック（統合設定システムに委譲）"""
        result: bool = self._manager.validate()
        if not result:
            console.print("[red][エラー] 設定検証エラー[/red]")
        return result


def load_config(config_path: str | None = None) -> Config:
    """設定を読み込む便利関数（統合設定システムを使用）"""
    return Config(config_path)
