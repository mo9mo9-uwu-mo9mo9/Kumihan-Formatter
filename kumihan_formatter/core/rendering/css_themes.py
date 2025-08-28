"""
CSSテーマ生成機能
CSSProcessor分割版 - テーマシステム専用モジュール
"""

import logging
from typing import Dict


class CSSThemes:
    """CSS テーマ生成クラス"""

    def __init__(self):
        """CSS テーマ生成初期化"""
        self.logger = logging.getLogger(__name__)

    def get_available_themes(self) -> Dict[str, str]:
        """利用可能なテーマ一覧取得"""
        return {
            "default": "デフォルトテーマ",
            "dark": "ダークテーマ",
            "sepia": "セピアテーマ",
            "minimal": "ミニマルテーマ",
            "academic": "アカデミックテーマ",
        }

    def generate_theme_styles(self, theme_name: str = "default") -> str:
        """指定テーマのスタイル生成"""
        theme_methods = {
            "default": self.generate_default_theme,
            "dark": self.generate_dark_theme,
            "sepia": self.generate_sepia_theme,
            "minimal": self.generate_minimal_theme,
            "academic": self.generate_academic_theme,
        }

        method = theme_methods.get(theme_name, self.generate_default_theme)
        return method()

    def generate_default_theme(self) -> str:
        """デフォルトテーマ"""
        return """
/* Default Theme */
body {
    background-color: #ffffff;
    color: #333333;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.content-heading {
    color: #2c3e50;
}

.content-heading.level-1,
.content-heading.level-2 {
    border-color: #3498db;
}
"""

    def generate_dark_theme(self) -> str:
        """ダークテーマ"""
        return """
/* Dark Theme */
body {
    background-color: #1a1a1a;
    color: #e0e0e0;
}

.content-paragraph {
    color: #e0e0e0;
}

.content-heading {
    color: #ffffff;
}

.content-heading.level-1,
.content-heading.level-2 {
    border-color: #64b5f6;
}

.inline-code {
    background-color: #2d2d2d;
    color: #e0e0e0;
}

.table-of-contents {
    background-color: #2d2d2d;
    border-color: #404040;
}

.error-display {
    background-color: #2d1b1b;
    border-color: #c53030;
    color: #fed7d7;
}
"""

    def generate_sepia_theme(self) -> str:
        """セピアテーマ"""
        return """
/* Sepia Theme */
body {
    background-color: #f4f1ea;
    color: #5c4b37;
}

.content-paragraph {
    color: #5c4b37;
}

.content-heading {
    color: #3d2914;
}

.content-heading.level-1,
.content-heading.level-2 {
    border-color: #8b4513;
}

.inline-code {
    background-color: #ede8db;
    color: #5c4b37;
}

.table-of-contents {
    background-color: #ede8db;
    border-color: #d4c4a8;
}
"""

    def generate_minimal_theme(self) -> str:
        """ミニマルテーマ"""
        return """
/* Minimal Theme */
body {
    background-color: #ffffff;
    color: #000000;
    font-family: 'Times New Roman', serif;
}

.content-paragraph {
    line-height: 1.6;
    margin-bottom: 1em;
}

.content-heading {
    font-weight: normal;
    border: none;
    margin-top: 2em;
}

.content-heading.level-1 {
    font-size: 1.5em;
    text-align: center;
}

.content-heading.level-2 {
    font-size: 1.3em;
}

.table-of-contents {
    background: none;
    border: 1px solid #000;
    padding: 1em;
}
"""

    def generate_academic_theme(self) -> str:
        """アカデミックテーマ"""
        return """
/* Academic Theme */
body {
    background-color: #fdfdfd;
    color: #2c3e50;
    font-family: 'Georgia', 'Times New Roman', serif;
    line-height: 1.7;
}

.content-paragraph {
    text-align: justify;
    text-indent: 1.5em;
}

.content-heading {
    font-family: 'Arial', sans-serif;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.content-heading.level-1 {
    font-size: 1.4em;
    margin-top: 3em;
}

.footnote-section {
    font-size: 0.9em;
    border-top: 2px solid #2c3e50;
}
"""
