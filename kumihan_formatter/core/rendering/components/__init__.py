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
except ImportError as e:
    # CI環境での詳細デバッグ情報
    import os

    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        import sys

        print(f"[CI DEBUG] 絶対インポート失敗: {e}", file=sys.stderr)
        print(f"[CI DEBUG] sys.path: {sys.path[:3]}", file=sys.stderr)
        print(
            f"[CI DEBUG] PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}",
            file=sys.stderr,
        )

    # フォールバック: 相対インポート
    try:
        from .content_processor_delegate import ContentProcessorDelegate
        from .element_renderer_delegate import ElementRendererDelegate
        from .output_formatter_delegate import OutputFormatterDelegate
    except ImportError as e2:
        if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
            print(f"[CI DEBUG] 相対インポートも失敗: {e2}", file=sys.stderr)
        raise e2

__all__ = [
    "ElementRendererDelegate",
    "ContentProcessorDelegate",
    "OutputFormatterDelegate",
]
