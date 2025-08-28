"""Kumihan-Formatter - テキストファイルをHTMLに自動組版するCLIツール

最小限実装版 - 基本インポートのみ対応
"""

__version__ = "0.9.0-minimal"

# 基本API公開
from .unified_api import KumihanFormatter, quick_convert, quick_parse

__all__ = [
    "KumihanFormatter",
    "quick_convert",
    "quick_parse",
]
