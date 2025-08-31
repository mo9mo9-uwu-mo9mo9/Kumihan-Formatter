"""
CSS・スタイル処理機能
HTMLFormatterの分割版 - CSS処理モジュール
"""

import logging
from typing import Any, Dict, List, Optional, Union


class CSSProcessor:
    """CSS・スタイル処理クラス - 軽量化版"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """CSS プロセッサー初期化"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.custom_styles: Dict[str, str] = {}
        self.css_classes: Dict[str, List[str]] = {}

        # 分離されたモジュールのインスタンス化
        from .css_themes import CSSThemes
        from .css_utilities import CSSUtilities

        self.themes = CSSThemes()
        self.utilities = CSSUtilities()

    def get_css_classes(self) -> Dict[str, List[str]]:
        """CSSクラス一覧取得（委譲）"""
        return self.utilities.get_css_classes_reference()

    def generate_base_styles(self) -> str:
        """基本スタイル生成"""
        return """
/* Base Styles */
body {
    font-family: 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', 'Meiryo', sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 2em;
    max-width: 800px;
    margin: 0 auto;
}

/* Typography */
.content-paragraph {
    margin: 1em 0;
    text-align: justify;
}

.content-heading {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: bold;
}

.content-heading.level-1 {
    font-size: 2em;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.3em;
}

.content-heading.level-2 {
    font-size: 1.5em;
    border-left: 4px solid #3498db;
    padding-left: 1em;
}

.content-heading.level-3 {
    font-size: 1.3em;
    color: #2c3e50;
}

/* Text Formatting */
.text-bold {
    font-weight: bold;
}

.text-italic {
    font-style: italic;
}

.inline-code {
    background-color: #f8f8f8;
    border: 1px solid #e0e0e0;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.9em;
}

/* Lists */
.content-list {
    margin: 1em 0;
    padding-left: 2em;
}

.structured-list li {
    margin: 0.5em 0;
}

/* Special Elements */
.table-of-contents {
    background-color: #f9f9f9;
    border: 1px solid #e0e0e0;
    padding: 1.5em;
    margin: 2em 0;
    border-radius: 5px;
}

.footnote-section {
    margin-top: 3em;
    padding-top: 1em;
    border-top: 1px solid #e0e0e0;
    font-size: 0.9em;
    color: #666;
}

.error-display {
    background-color: #fee;
    border: 1px solid #fcc;
    padding: 1em;
    margin: 1em 0;
    border-radius: 5px;
    color: #c00;
}

/* Layout */
.content-section {
    margin: 2em 0;
}

.document-part {
    page-break-before: always;
}
"""

    def generate_theme_styles(self, theme_name: str = "default") -> str:
        """テーマスタイル生成（委譲）"""
        return self.themes.generate_theme_styles(theme_name)

    def process_custom_styles(self, custom_css: Union[str, Dict[str, str]]) -> str:
        """カスタムスタイル処理（委譲）"""
        return self.utilities.process_custom_styles(custom_css)

    def generate_responsive_styles(self) -> str:
        """レスポンシブスタイル生成（委譲）"""
        return self.utilities.generate_responsive_styles()

    def minify_css(self, css: str) -> str:
        """CSS最小化（委譲）"""
        return self.utilities.minify_css(css)

    def validate_css(self, css: str) -> List[str]:
        """CSS検証（委譲）"""
        return self.utilities.validate_css(css)

    def apply_css_classes(
        self, element_type: str, additional_classes: Optional[List[str]] = None
    ) -> str:
        """CSSクラス適用（委譲）"""
        return self.utilities.apply_css_classes(element_type, additional_classes)

    def get_inline_styles(
        self, element_type: str, custom_props: Optional[Dict[str, str]] = None
    ) -> str:
        """インラインスタイル取得（委譲）"""
        return self.utilities.get_inline_styles(element_type, custom_props)

    def generate_complete_css(
        self,
        theme: str = "default",
        include_responsive: bool = True,
        custom_styles: Optional[Union[str, Dict[str, str]]] = None,
        minify: bool = False,
    ) -> str:
        """完全なCSS生成（統合メソッド）"""
        css_parts = []

        # 基本スタイル
        css_parts.append(self.generate_base_styles())

        # テーマスタイル
        css_parts.append(self.generate_theme_styles(theme))

        # レスポンシブスタイル
        if include_responsive:
            css_parts.append(self.generate_responsive_styles())

        # カスタムスタイル
        if custom_styles:
            css_parts.append(self.process_custom_styles(custom_styles))

        # 結合
        complete_css = "\n\n".join(css_parts)

        # 最小化
        if minify:
            complete_css = self.minify_css(complete_css)

        return complete_css

    def get_available_themes(self) -> Dict[str, str]:
        """利用可能テーマ取得（委譲）"""
        return self.themes.get_available_themes()
