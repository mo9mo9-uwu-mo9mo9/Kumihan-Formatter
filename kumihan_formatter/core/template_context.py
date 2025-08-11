"""Template Rendering Context Builder

テンプレートレンダリングコンテキストを構築するビルダークラス
"""

from typing import Any


class RenderContext:
    """Builder for template rendering context"""

    def __init__(self) -> None:
        self._context: dict[str, Any] = (
            {}
        )  # 型アノテーション修正: type: ignore削除  # type: ignore

    def title(self, title: str) -> "RenderContext":
        """Set page title"""
        self._context["title"] = title
        return self

    def body_content(self, content: str) -> "RenderContext":
        """Set main body content"""
        self._context["body_content"] = content
        return self

    def toc_html(self, toc: str) -> "RenderContext":
        """Set table of contents HTML"""
        self._context["toc_html"] = toc
        return self

    def has_toc(self, has_toc: bool) -> "RenderContext":
        """Set whether TOC should be displayed"""
        self._context["has_toc"] = has_toc
        return self

    def source_toggle(self, source_text: str, source_filename: str) -> "RenderContext":
        """Add source toggle functionality"""
        self._context["source_text"] = source_text
        self._context["source_filename"] = source_filename
        self._context["has_source_toggle"] = True
        return self

    def navigation(self, nav_html: str) -> "RenderContext":
        """Add navigation HTML"""
        self._context["navigation_html"] = nav_html
        return self

    def css_vars(self, css_vars: dict[str, str]) -> "RenderContext":
        """Set CSS variables for styling"""
        self._context["css_vars"] = css_vars
        return self

    def custom(self, key: str, value: Any) -> "RenderContext":
        """Add custom context variable"""
        self._context[key] = value
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the context dictionary"""
        return self._context.copy()

    def merge(self, other_context: dict[str, Any]) -> "RenderContext":
        """Merge another context dictionary"""
        self._context.update(other_context)
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context"""
        return self._context.get(key, default)

    def has(self, key: str) -> bool:
        """Check if a key exists in the context"""
        return key in self._context

    def remove(self, key: str) -> "RenderContext":
        """Remove a key from the context"""
        self._context.pop(key, None)
        return self

    def clear(self) -> "RenderContext":
        """Clear all context data"""
        self._context.clear()
        return self

    def keys(self) -> list[str]:
        """Get all context keys"""
        return list(self._context.keys())

    def __len__(self) -> int:
        """Get the number of context items"""
        return len(self._context)

    def __contains__(self, key: str) -> bool:
        """Check if a key is in the context"""
        return key in self._context

    def __getitem__(self, key: str) -> Any:
        """Get a context value by key"""
        return self._context[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a context value by key"""
        self._context[key] = value

    def __repr__(self) -> str:
        """String representation of the context"""
        return f"RenderContext({self._context})"
