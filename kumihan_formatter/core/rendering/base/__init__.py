"""Rendering base package initialization - Issue #914 Phase 1

統一レンダラープロトコルとベースクラスパッケージ
"""

from .renderer_protocols import (
    AnyRenderer,
    BaseRendererProtocol,
    CompositeRendererProtocol,
    HtmlRendererProtocol,
    MarkdownRendererProtocol,
    RenderContext,
    RendererResult,
    RenderError,
    RenderResult,
    StreamingRendererProtocol,
    create_render_context,
    create_render_result,
    is_renderer_protocol_compatible,
    validate_renderer_implementation,
)

__all__ = [
    "BaseRendererProtocol",
    "RenderContext",
    "RenderResult",
    "RenderError",
    "HtmlRendererProtocol",
    "MarkdownRendererProtocol",
    "StreamingRendererProtocol",
    "CompositeRendererProtocol",
    "AnyRenderer",
    "RendererResult",
    "create_render_context",
    "create_render_result",
    "is_renderer_protocol_compatible",
    "validate_renderer_implementation",
]
