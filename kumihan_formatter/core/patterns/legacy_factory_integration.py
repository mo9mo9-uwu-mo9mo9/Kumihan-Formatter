"""既存ファクトリーの統合アダプター

Issue #914: 既存ファクトリーファイルを新DIシステムに統合
後方互換性を維持しながら段階的な移行を支援
"""

from typing import Optional, TypeVar

from ..utilities.logger import get_logger
from .dependency_injection import DIContainer, get_container
from .factories import get_service_factory

logger = get_logger(__name__)

T = TypeVar("T")


class LegacyFactoryAdapter:
    """レガシーファクトリー統合アダプター

    既存のファクトリー関数・クラスを新DIシステムに統合
    """

    def __init__(self, container: Optional[DIContainer] = None) -> None:
        self.container = container or get_container()
        self.service_factory = get_service_factory()
        self._register_legacy_services()

    def _register_legacy_services(self) -> None:
        """レガシーサービスをDIコンテナに登録"""
        try:
            # ファイル操作関連の統合
            self._register_file_operations()

            # マークダウン関連の統合
            self._register_markdown_services()

            # リストパーサー関連の統合
            self._register_list_parser_services()

            logger.info("Legacy factory services registered successfully")

        except Exception as e:
            logger.error(f"Legacy factory registration failed: {e}")

    def _register_file_operations(self) -> None:
        """ファイル操作関連サービスの登録"""
        try:
            from ..file_io_handler import FileIOHandler
            from ..file_operations_core import FileOperationsCore
            from ..file_operations_factory import (
                FileOperationsComponents,
                create_file_io_handler,
                create_file_operations,
                create_file_path_utilities,
            )
            from ..file_path_utilities import FilePathUtilities

            # ファクトリー関数を使用してDIコンテナに登録
            def file_operations_factory(container: DIContainer) -> FileOperationsCore:
                return create_file_operations()

            def file_path_utilities_factory(
                container: DIContainer,
            ) -> FilePathUtilities:
                return create_file_path_utilities()

            def file_io_handler_factory(container: DIContainer) -> FileIOHandler:
                return create_file_io_handler()

            def file_operations_components_factory(
                container: DIContainer,
            ) -> FileOperationsComponents:
                return FileOperationsComponents()

            # DIコンテナへの登録
            self.container.register_factory(FileOperationsCore, file_operations_factory)
            self.container.register_factory(
                FilePathUtilities, file_path_utilities_factory
            )
            self.container.register_factory(FileIOHandler, file_io_handler_factory)
            self.container.register_factory(
                FileOperationsComponents, file_operations_components_factory
            )

            logger.debug("File operations services registered")

        except ImportError as e:
            logger.warning(f"Could not register file operations services: {e}")
        except Exception as e:
            logger.error(f"File operations registration failed: {e}")

    def _register_markdown_services(self) -> None:
        """マークダウン関連サービスの登録"""
        try:
            from ..markdown_factory import MarkdownFactory
            from ..markdown_parser import MarkdownParser
            from ..markdown_processor import MarkdownProcessor
            from ..markdown_renderer import MarkdownRenderer

            # ファクトリー関数を使用してDIコンテナに登録
            def markdown_parser_factory(container: DIContainer) -> MarkdownParser:
                return MarkdownFactory.create_parser()

            def markdown_processor_factory(container: DIContainer) -> MarkdownProcessor:
                return MarkdownFactory.create_processor()

            def markdown_renderer_factory(container: DIContainer) -> MarkdownRenderer:
                return MarkdownFactory.create_renderer()

            # DIコンテナへの登録
            self.container.register_factory(MarkdownParser, markdown_parser_factory)
            self.container.register_factory(
                MarkdownProcessor, markdown_processor_factory
            )
            self.container.register_factory(MarkdownRenderer, markdown_renderer_factory)

            logger.debug("Markdown services registered")

        except ImportError as e:
            logger.warning(f"Could not register markdown services: {e}")
        except Exception as e:
            logger.error(f"Markdown services registration failed: {e}")

    def _register_list_parser_services(self) -> None:
        """リストパーサー関連サービスの登録"""
        try:
            from ..list_parser_core import ListParserCore
            from ..list_parser_factory import (
                ListParserComponents,
                create_list_parser,
                create_list_validator,
                create_nested_list_parser,
            )
            from ..list_validator import ListValidator
            from ..nested_list_parser import NestedListParser
            from ..parsing.keyword.keyword_parser import KeywordParser

            # 依存関係を考慮したファクトリー関数
            def list_parser_factory(container: DIContainer) -> ListParserCore:
                keyword_parser = container.resolve(KeywordParser)
                return create_list_parser(keyword_parser)

            def nested_list_parser_factory(container: DIContainer) -> NestedListParser:
                keyword_parser = container.resolve(KeywordParser)
                return create_nested_list_parser(keyword_parser)

            def list_validator_factory(container: DIContainer) -> ListValidator:
                keyword_parser = container.resolve(KeywordParser)
                return create_list_validator(keyword_parser)

            def list_parser_components_factory(
                container: DIContainer,
            ) -> ListParserComponents:
                keyword_parser = container.resolve(KeywordParser)
                return ListParserComponents(keyword_parser)

            # DIコンテナへの登録
            self.container.register_factory(ListParserCore, list_parser_factory)
            self.container.register_factory(
                NestedListParser, nested_list_parser_factory
            )
            self.container.register_factory(ListValidator, list_validator_factory)
            self.container.register_factory(
                ListParserComponents, list_parser_components_factory
            )

            logger.debug("List parser services registered")

        except ImportError as e:
            logger.warning(f"Could not register list parser services: {e}")
        except Exception as e:
            logger.error(f"List parser services registration failed: {e}")


# 後方互換性のための便利関数
def create_legacy_file_operations(ui=None):
    """レガシー互換: ファイル操作コンポーネント作成"""
    try:
        adapter = LegacyFactoryAdapter()
        from ..file_operations_core import FileOperationsCore

        return adapter.container.resolve(FileOperationsCore)
    except Exception as e:
        logger.warning(
            f"Legacy file operations creation failed, falling back to direct creation: {e}"
        )
        from ..file_operations_factory import create_file_operations

        return create_file_operations(ui)


def create_legacy_markdown_converter():
    """レガシー互換: マークダウンコンバーター作成"""
    try:
        adapter = LegacyFactoryAdapter()
        from ..markdown_parser import MarkdownParser
        from ..markdown_processor import MarkdownProcessor
        from ..markdown_renderer import MarkdownRenderer

        parser = adapter.container.resolve(MarkdownParser)
        processor = adapter.container.resolve(MarkdownProcessor)
        renderer = adapter.container.resolve(MarkdownRenderer)

        return parser, processor, renderer
    except Exception as e:
        logger.warning(
            f"Legacy markdown converter creation failed, falling back to direct creation: {e}"
        )
        from ..markdown_factory import create_markdown_converter

        return create_markdown_converter()


def create_legacy_list_parser(keyword_parser):
    """レガシー互換: リストパーサー作成"""
    try:
        adapter = LegacyFactoryAdapter()
        from ..list_parser_core import ListParserCore

        return adapter.container.resolve(ListParserCore)
    except Exception as e:
        logger.warning(
            f"Legacy list parser creation failed, falling back to direct creation: {e}"
        )
        from ..list_parser_factory import create_list_parser

        return create_list_parser(keyword_parser)


# グローバル統合アダプター
_legacy_adapter: Optional[LegacyFactoryAdapter] = None


def get_legacy_adapter() -> LegacyFactoryAdapter:
    """グローバル統合アダプター取得"""
    global _legacy_adapter
    if _legacy_adapter is None:
        _legacy_adapter = LegacyFactoryAdapter()
    return _legacy_adapter


def initialize_legacy_integration(container: Optional[DIContainer] = None) -> None:
    """レガシー統合システムの初期化"""
    try:
        global _legacy_adapter
        _legacy_adapter = LegacyFactoryAdapter(container)
        logger.info("Legacy integration system initialized successfully")
    except Exception as e:
        logger.error(f"Legacy integration initialization failed: {e}")
        raise
