"""
マークダウン ファクトリー

マークダウン変換器コンポーネントの生成・初期化
Issue #492 Phase 5A - markdown_converter.py分割
"""

from .markdown_parser import MarkdownParser
from .markdown_processor import MarkdownProcessor
from .markdown_renderer import MarkdownRenderer


class MarkdownFactory:
    """Factory for creating markdown converter components"""

    @staticmethod
    def create_parser() -> MarkdownParser:
        """Create markdown parser instance"""
        return MarkdownParser()

    @staticmethod
    def create_processor() -> MarkdownProcessor:
        """Create markdown processor instance"""
        return MarkdownProcessor()

    @staticmethod
    def create_renderer() -> MarkdownRenderer:
        """Create markdown renderer instance"""
        return MarkdownRenderer()


def create_markdown_converter() -> tuple[MarkdownParser, MarkdownProcessor, MarkdownRenderer]:
    """Get all markdown converter components"""
    factory = MarkdownFactory()

    parser = factory.create_parser()
    processor = factory.create_processor()
    renderer = factory.create_renderer()

    return parser, processor, renderer
