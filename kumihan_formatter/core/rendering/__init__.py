"""統合レンダリングシステム

Issue #1215対応完了版：15個のRenderingコンポーネントを統合管理
HTML・CSS・テンプレート処理の統合API提供
"""

# 統合レンダリングシステム（推奨）
from .main_renderer import MainRenderer

# 個別コンポーネント（必要時直接アクセス用）
from .html_formatter import HtmlFormatter
from .css_processor import CSSProcessor
from .html_utilities import HTMLUtilities
from .css_utilities import CSSUtilities

__all__ = [
    "MainRenderer",
    "HtmlFormatter",
    "CSSProcessor",
    "HTMLUtilities",
    "CSSUtilities",
]


# 便利な統合関数
def render(nodes, context=None, config=None):
    """統合レンダリング関数（簡易アクセス）"""
    main_renderer = MainRenderer(config)
    return main_renderer.render(nodes, context)
