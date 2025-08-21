"""MainRenderer委譲コンポーネント群

Issue #912 Renderer系統合リファクタリング対応
main_renderer.py巨大ファイル分割による委譲コンポーネント
"""

# CI環境対応: 絶対インポート優先（相対インポートでのCI失敗対策）
try:
    # 絶対インポート（CI環境での確実性重視）
    from kumihan_formatter.core.rendering.components.content_processor_delegate import (
        ContentProcessorDelegate,
    )
    from kumihan_formatter.core.rendering.components.element_renderer_delegate import (
        ElementRendererDelegate,
    )
    from kumihan_formatter.core.rendering.components.output_formatter_delegate import (
        OutputFormatterDelegate,
    )
except ImportError:
    # フォールバック: 相対インポート
    from .content_processor_delegate import ContentProcessorDelegate
    from .element_renderer_delegate import ElementRendererDelegate
    from .output_formatter_delegate import OutputFormatterDelegate

__all__ = [
    "ElementRendererDelegate",
    "ContentProcessorDelegate",
    "OutputFormatterDelegate",
]
