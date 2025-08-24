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

    # 具象クラス直接登録（Issue #1082: CI DI解決用）
    container.register(
        UnifiedKeywordParser, UnifiedKeywordParser, ServiceLifetime.SINGLETON
    )
    container.register(UnifiedListParser, UnifiedListParser, ServiceLifetime.SINGLETON)
    container.register(
        UnifiedBlockParser, UnifiedBlockParser, ServiceLifetime.SINGLETON
    )
    container.register(
        UnifiedMarkdownParser, UnifiedMarkdownParser, ServiceLifetime.SINGLETON
    )

    # プロトコル → 実装クラスの登録
    try:
        # 必要に応じてプロトコル登録を追加
        pass
        # BaseParserProtocolは拽象クラスのため、具象クラスで登録
        container.register(MainParser, MainParser, ServiceLifetime.SINGLETON)

    except ImportError as e:
        # プロトコルが利用できない場合はスキップ
        print(f"警告: パーサープロトコルが利用できません: {e}")

    # レンダラー登録
    from ..rendering.formatters.html_formatter import HtmlFormatter
    from ..rendering.formatters.markdown_formatter import MarkdownFormatter
    from ..rendering.main_renderer import MainRenderer

    try:
        # レンダラープロトコルの登録は必要に応じて追加
        pass

        # BaseRendererProtocolは拽象クラスのため、具象クラスで登録
        container.register(MainRenderer, MainRenderer, ServiceLifetime.SINGLETON)
        # HtmlRendererProtocolは拽象クラスのため、具象クラスで登録
        container.register(HtmlFormatter, HtmlFormatter, ServiceLifetime.SINGLETON)
        # MarkdownRendererProtocolは拽象クラスのため、具象クラスで登録
        container.register(
            MarkdownFormatter, MarkdownFormatter, ServiceLifetime.SINGLETON
        )

    except ImportError as e:
        # プロトコルが利用できない場合はスキップ
        print(f"警告: レンダラープロトコルが利用できません: {e}")


def auto_register_services() -> None:
    """アプリケーション起動時の自動登録"""
    from .dependency_injection import get_container

    container = get_container()
    register_default_services(container)
