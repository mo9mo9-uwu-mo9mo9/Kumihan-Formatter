"""MainRenderer委譲コンポーネント群

Issue #912 Renderer系統合リファクタリング対応
main_renderer.py巨大ファイル分割による委譲コンポーネント
"""

# 明示的な相対インポート（CI環境対応）
try:
    from .content_processor_delegate import ContentProcessorDelegate
    from .element_renderer_delegate import ElementRendererDelegate
    from .output_formatter_delegate import OutputFormatterDelegate
except ImportError:
    # フォールバック: 絶対インポート
    from kumihan_formatter.core.rendering.components.content_processor_delegate import (
        ContentProcessorDelegate,
    )
    from kumihan_formatter.core.rendering.components.element_renderer_delegate import (
        ElementRendererDelegate,
    )
    from kumihan_formatter.core.rendering.components.output_formatter_delegate import (
        OutputFormatterDelegate,
    )

__all__ = [
    "ElementRendererDelegate",
    "ContentProcessorDelegate",
    "OutputFormatterDelegate",
]
