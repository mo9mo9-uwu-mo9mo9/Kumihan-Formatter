"""統合Renderingシステム - Issue #912 Renderer系統合リファクタリング

統合された機能:
- MainRenderer: 全出力形式統括レンダラー（HTML/Markdown対応）
- HtmlFormatter: HTML出力専用フォーマッター
- MarkdownFormatter: Markdown出力専用フォーマッター
- ElementRenderer: 基本HTML要素（段落、見出し、リスト）
- CompoundElementRenderer: 複合要素（複数キーワード）
- HTMLFormatter: HTMLフォーマット・整形ユーティリティ

後方互換性は完全に維持されています。
"""

# 既存コンポーネント（後方互換性）
from .compound_renderer import CompoundElementRenderer as CompoundRenderer
from .element_renderer import ElementRenderer

# メイン機能
from .formatters.html_formatter import HtmlFormatter
from .formatters.markdown_formatter import MarkdownFormatter
from .html_formatter import HTMLFormatter
from .html_utils import (
    NESTING_ORDER,
    contains_html_tags,
    create_self_closing_tag,
    create_simple_tag,
    escape_html,
    process_text_content,
    render_attributes,
    sort_keywords_by_nesting_order,
)
from .main_renderer import HTMLRenderer, MainRenderer

# 後方互換性エイリアス
Renderer = MainRenderer  # kumihan_formatter.renderer.Renderer の代替
CompoundElementRenderer = CompoundRenderer

__all__ = [
    # 統合メイン機能
    "MainRenderer",
    "HtmlFormatter",
    "MarkdownFormatter",
    # 後方互換性
    "HTMLRenderer",
    "Renderer",
    "CompoundElementRenderer",
    "ElementRenderer",
    "CompoundRenderer",
    "HTMLFormatter",
    # ユーティリティ
    "escape_html",
    "render_attributes",
    "process_text_content",
    "contains_html_tags",
    "create_simple_tag",
    "create_self_closing_tag",
    "sort_keywords_by_nesting_order",
    "NESTING_ORDER",
]
