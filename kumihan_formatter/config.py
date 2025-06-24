"""設定管理モジュール"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


class Config:
    """設定管理クラス"""
    
    # デフォルト設定
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
        "font_family": "Hiragino Kaku Gothic ProN, Hiragino Sans, Yu Gothic, Meiryo, sans-serif",
        "css": {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8"
        },
        "themes": {
            "default": {
                "name": "デフォルト",
                "css": {
                    "background_color": "#f9f9f9",
                    "container_background": "white",
                    "text_color": "#333"
                }
            },
            "dark": {
                "name": "ダーク",
                "css": {
                    "background_color": "#1a1a1a",
                    "container_background": "#2d2d2d",
                    "text_color": "#e0e0e0"
                }
            },
            "sepia": {
                "name": "セピア",
                "css": {
                    "background_color": "#f4f1ea",
                    "container_background": "#fdf6e3",
                    "text_color": "#5c4b37"
                }
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self.load_config(config_path)
        
        # テーマが指定されている場合、CSSを更新
        if "theme" in self.config and self.config["theme"] in self.config["themes"]:
            theme_css = self.config["themes"][self.config["theme"]]["css"]
            self.config["css"].update(theme_css)
    
    def load_config(self, config_path: str) -> bool:
        """設定ファイルを読み込む"""
        try:
            config_file = Path(config_path)
            
            if not config_file.exists():
                console.print(f"[yellow][警告]  設定ファイルが見つかりません:[/yellow] {config_path}")
                console.print("[dim]   デフォルト設定を使用します[/dim]")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    user_config = yaml.safe_load(f)
                elif config_file.suffix.lower() == '.json':
                    user_config = json.load(f)
                else:
                    console.print(f"[red][エラー] 未対応の設定ファイル形式:[/red] {config_file.suffix}")
                    console.print("[dim]   .yaml, .yml, .json のみサポートしています[/dim]")
                    return False
            
            if not isinstance(user_config, dict):
                console.print("[red][エラー] 設定ファイルの形式が正しくありません[/red]")
                return False
            
            # 設定をマージ
            self._merge_config(user_config)
            console.print(f"[green][完了] 設定ファイルを読み込みました:[/green] {config_path}")
            
            return True
            
        except yaml.YAMLError as e:
            console.print(f"[red][エラー] YAML解析エラー:[/red] {e}")
            return False
        except json.JSONDecodeError as e:
            console.print(f"[red][エラー] JSON解析エラー:[/red] {e}")
            return False
        except Exception as e:
            console.print(f"[red][エラー] 設定ファイル読み込みエラー:[/red] {e}")
            return False
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """ユーザー設定をデフォルト設定にマージ"""
        # カスタムテーマの追加（テーマ設定より先に処理）
        if "themes" in user_config and isinstance(user_config["themes"], dict):
            self.config["themes"].update(user_config["themes"])
            console.print(f"[dim]   カスタムテーマ: {len(user_config['themes'])}個[/dim]")
        
        # マーカーの追加・上書き
        if "markers" in user_config:
            if isinstance(user_config["markers"], dict):
                self.config["markers"].update(user_config["markers"])
                console.print(f"[dim]   カスタムマーカー: {len(user_config['markers'])}個[/dim]")
        
        # テーマ設定
        if "theme" in user_config:
            if user_config["theme"] in self.config["themes"]:
                self.config["theme"] = user_config["theme"]
                console.print(f"[dim]   テーマ: {self.config['themes'][user_config['theme']]['name']}[/dim]")
            else:
                console.print(f"[yellow][警告]  未知のテーマ:[/yellow] {user_config['theme']}")
        
        # フォント設定
        if "font_family" in user_config:
            self.config["font_family"] = user_config["font_family"]
            console.print(f"[dim]   フォント: {user_config['font_family']}[/dim]")
        
        # CSS設定の上書き
        if "css" in user_config and isinstance(user_config["css"], dict):
            self.config["css"].update(user_config["css"])
            console.print(f"[dim]   カスタムCSS: {len(user_config['css'])}項目[/dim]")
    
    def get_markers(self) -> Dict[str, Dict[str, Any]]:
        """マーカー定義を取得"""
        return self.config["markers"]
    
    def get_css_variables(self) -> Dict[str, str]:
        """CSS変数を取得"""
        css_vars = self.config["css"].copy()
        css_vars["font_family"] = self.config["font_family"]
        return css_vars
    
    def get_theme_name(self) -> str:
        """現在のテーマ名を取得"""
        theme_key = self.config.get("theme", "default")
        return self.config["themes"].get(theme_key, {}).get("name", "不明")
    
    def validate_config(self) -> bool:
        """設定の妥当性をチェック"""
        errors = []
        
        # マーカー定義の検証
        if "markers" not in self.config:
            errors.append("markers設定が見つかりません")
        else:
            for name, marker in self.config["markers"].items():
                if not isinstance(marker, dict):
                    errors.append(f"マーカー '{name}' の設定が辞書形式ではありません")
                elif "tag" not in marker:
                    errors.append(f"マーカー '{name}' にtagが指定されていません")
        
        # テーマの検証
        current_theme = self.config.get("theme", "default")
        if current_theme not in self.config["themes"]:
            errors.append(f"テーマ '{current_theme}' が定義されていません")
        
        if errors:
            console.print("[red][エラー] 設定検証エラー:[/red]")
            for error in errors:
                console.print(f"[red]   - {error}[/red]")
            return False
        
        return True


def load_config(config_path: Optional[str] = None) -> Config:
    """設定を読み込む便利関数"""
    return Config(config_path)