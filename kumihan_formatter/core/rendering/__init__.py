"""統合レンダリングシステム

Issue #1215対応完了版：15個のRenderingコンポーネントを統合管理
HTML・CSS・テンプレート処理の統合API提供
"""

from typing import Any, Dict, List, Optional

# 統合レンダリングシステム（推奨）

# 個別コンポーネント（必要時直接アクセス用）

__all__ = [
    "MainRenderer",
    "HtmlFormatter",
    "CSSProcessor",
    "HTMLUtilities",
    "CSSUtilities",
]


# 便利な統合関数
def render(
    nodes: List[Any],
    context: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """統合レンダリング関数（簡易アクセス）"""
    main_renderer = MainRenderer(config)
    return main_renderer.render(nodes, context)
