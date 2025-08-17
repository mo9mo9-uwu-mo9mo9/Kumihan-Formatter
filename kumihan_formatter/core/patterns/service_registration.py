"""サービス登録管理

Issue #914 Phase 2: 標準サービスの一元登録
"""

from typing import TYPE_CHECKING

from .dependency_injection import DIContainer, ServiceLifetime

if TYPE_CHECKING:
    pass


def register_default_services(container: DIContainer) -> None:
    """標準サービスをDIコンテナに登録"""

    # パーサー登録
    from ..parsing.main_parser import MainParser
    from ..parsing.specialized.block_parser import UnifiedBlockParser
    from ..parsing.specialized.keyword_parser import UnifiedKeywordParser
    from ..parsing.specialized.list_parser import UnifiedListParser
    from ..parsing.specialized.markdown_parser import UnifiedMarkdownParser

    # プロトコル → 実装クラスの登録
    try:
        from ..parsing.base.parser_protocols import (
            BaseParserProtocol,
            BlockParserProtocol,
            KeywordParserProtocol,
            ListParserProtocol,
            MarkdownParserProtocol,
        )

        container.register(
            KeywordParserProtocol, UnifiedKeywordParser, ServiceLifetime.SINGLETON
        )
        container.register(
            ListParserProtocol, UnifiedListParser, ServiceLifetime.SINGLETON
        )
        container.register(
            BlockParserProtocol, UnifiedBlockParser, ServiceLifetime.SINGLETON
        )
        container.register(
            MarkdownParserProtocol, UnifiedMarkdownParser, ServiceLifetime.SINGLETON
        )
        container.register(BaseParserProtocol, MainParser, ServiceLifetime.SINGLETON)

    except ImportError as e:
        # プロトコルが利用できない場合はスキップ
        print(f"警告: パーサープロトコルが利用できません: {e}")

    # レンダラー登録
    from ..rendering.formatters.html_formatter import HtmlFormatter
    from ..rendering.formatters.markdown_formatter import MarkdownFormatter
    from ..rendering.main_renderer import MainRenderer

    try:
        from ..rendering.base.renderer_protocols import (
            BaseRendererProtocol,
            HtmlRendererProtocol,
            MarkdownRendererProtocol,
        )

        container.register(
            BaseRendererProtocol, MainRenderer, ServiceLifetime.SINGLETON
        )
        container.register(
            HtmlRendererProtocol, HtmlFormatter, ServiceLifetime.SINGLETON
        )
        container.register(
            MarkdownRendererProtocol, MarkdownFormatter, ServiceLifetime.SINGLETON
        )

    except ImportError as e:
        # プロトコルが利用できない場合はスキップ
        print(f"警告: レンダラープロトコルが利用できません: {e}")


def auto_register_services() -> None:
    """アプリケーション起動時の自動登録"""
    from .dependency_injection import get_container

    container = get_container()
    register_default_services(container)
