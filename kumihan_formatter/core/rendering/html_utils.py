"""HTML utility functions for Kumihan-Formatter - 統合モジュール

This module provides unified access to HTML processing utilities
while maintaining the 300-line limit through functional separation.

分割されたモジュール:
- html_escaping: HTML エスケープ・属性処理
- html_content_processor: コンテンツ処理・リスト変換
- html_tag_utils: タグ作成・優先度管理
"""

# 分割されたモジュールからインポート
from .html_content_processor import (
    process_block_content,
    process_collapsible_content,
    process_text_content,
)
from .html_escaping import (
    contains_html_tags,
    escape_html,
    render_attributes,
    render_attributes_with_enhancements,
)
from .html_tag_utils import (
    create_self_closing_tag,
    create_simple_tag,
    get_tag_priority,
    sort_keywords_by_nesting_order,
)

# 後方互換性のため、main_renderer.pyで使用される定数を再定義
NESTING_ORDER = [
    "details",  # 折りたたみ, ネタバレ
    "div",  # 枠線, ハイライト
    "h1",  # 見出し
    "h2",
    "h3",
    "h4",
    "h5",
    "strong",  # 太字
    "em",  # イタリック
]

# 後方互換性のため、全ての関数を再エクスポート
__all__ = [
    # HTML エスケープ関連
    "escape_html",
    "render_attributes",
    "render_attributes_with_enhancements",  # Phase 4 追加
    "contains_html_tags",
    # コンテンツ処理関連
    "process_text_content",
    "process_block_content",
    "process_collapsible_content",
    # タグ作成関連
    "create_simple_tag",
    "create_self_closing_tag",
    "get_tag_priority",
    "sort_keywords_by_nesting_order",
    # 定数
    "NESTING_ORDER",
]
