"""統一ファクトリーパターン実装

Issue #914: 既存ファクトリーの統合と拡張
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast

from ..parsing.base.parser_protocols import BaseParserProtocol
from ..rendering.base.renderer_protocols import BaseRendererProtocol
from ..utilities.logger import get_logger
from .dependency_injection import DIContainer, get_container

logger = get_logger(__name__)

T = TypeVar("T")
FactoryProduct = TypeVar("FactoryProduct")


class AbstractFactory(ABC, Generic[FactoryProduct]):
    """抽象ファクトリー基底クラス

    Generic型パラメータでファクトリー生成物の型を指定
    """

    @abstractmethod
    def create(self, type_name: str, **kwargs: Any) -> FactoryProduct:
        """オブジェクト生成"""
        ...

    @abstractmethod
    def register(self, type_name: str, implementation: Type[Any]) -> None:
        """実装登録"""
        ...

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """対応タイプ一覧取得"""
        ...


class ParserFactory(AbstractFactory[BaseParserProtocol]):
    """統一パーサーファクトリー

    全パーサー生成を一元管理:
    - キーワードパーサー
    - ブロックパーサー
    - リストパーサー
    - Markdownパーサー
    """

    def __init__(self, container: Optional[DIContainer] = None) -> None:
        self.container = container or get_container()
        self._parsers: Dict[str, Type[Any]] = {}
        self._register_default_parsers()

    def _register_default_parsers(self) -> None:
        """標準パーサー登録"""
        try:
            # 既存のパーサーを動的にインポートして登録
            parser_mappings = {
                "keyword": "kumihan_formatter.core.parsing.keyword.keyword_parser.KeywordParser",
                "block": "kumihan_formatter.core.parsing.block.block_parser.BlockParser",
                "list": "kumihan_formatter.core.list_parser.ListParser",
                "markdown": "kumihan_formatter.core.markdown_parser.MarkdownParser",
                "main": "kumihan_formatter.core.parsing.main_parser.MainParser",
            }

            for parser_type, class_path in parser_mappings.items():
                try:
                    module_path, class_name = class_path.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[class_name])
                    parser_class = getattr(module, class_name)
                    self._parsers[parser_type] = parser_class
                    logger.debug(f"Registered parser: {parser_type} -> {class_name}")
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Could not register parser {parser_type}: {e}")

        except Exception as e:
            logger.error(f"Failed to register default parsers: {e}")

    def create(self, type_name: str, **kwargs: Any) -> BaseParserProtocol:
        """パーサー生成"""
        try:
            if type_name not in self._parsers:
                raise ValueError(f"Unknown parser type: {type_name}")

            parser_class = self._parsers[type_name]

            # DIコンテナ経由で生成（依存関係自動解決）
            if self.container:
                try:
                    return cast(
                        BaseParserProtocol, self.container.resolve(parser_class)
                    )
                except Exception as e:
                    logger.warning(
                        f"DI resolution failed for {type_name}, "
                        f"falling back to direct creation: {e}"
                    )

            # 直接生成
            return cast(BaseParserProtocol, parser_class(**kwargs))

        except Exception as e:
            logger.error(f"Parser creation failed: {type_name}, error: {e}")
            raise

    def register(self, type_name: str, implementation: Type[Any]) -> None:
        """カスタムパーサー登録"""
        try:
            self._parsers[type_name] = implementation
            if self.container:
                # 抽象クラスの登録は型チェックのために安全に行う
                # DIContainerの型チェックをスキップして安全に登録
                try:
                    if not getattr(implementation, "__abstractmethods__", set()):
                        self.container.register(
                            cast(Any, BaseParserProtocol), implementation
                        )
                except Exception as reg_error:
                    logger.debug(f"Parser DI registration skipped: {reg_error}")
            logger.debug(f"Custom parser registered: {type_name}")
        except Exception as e:
            logger.error(f"Custom parser registration failed: {type_name}, error: {e}")
            raise

    def get_supported_types(self) -> List[str]:
        """対応パーサータイプ一覧"""
        return list(self._parsers.keys())

    def create_composite_parser(
        self, parser_types: List[str], **kwargs: Any
    ) -> BaseParserProtocol:
        """複合パーサー生成"""
        try:
            # MainParserを使用して複合パーサーを作成
            if "main" in self._parsers:
                main_parser = self.create("main", **kwargs)

                # 指定されたパーサーを追加
                for parser_type in parser_types:
                    if parser_type != "main":  # mainパーサー自身は除く
                        sub_parser = self.create(parser_type)
                        # add_parserメソッドがある場合は追加
                        if hasattr(main_parser, "add_parser"):
                            main_parser.add_parser(sub_parser)

                return main_parser
            else:
                raise ValueError("Main parser not available for composite creation")

        except Exception as e:
            logger.error(
                f"Composite parser creation failed: {parser_types}, error: {e}"
            )
            raise


class RendererFactory(AbstractFactory[BaseRendererProtocol]):
    """統一レンダラーファクトリー

    全レンダラー生成を一元管理:
    - HTMLレンダラー
    - Markdownレンダラー
    - テンプレートレンダラー
    """

    def __init__(self, container: Optional[DIContainer] = None) -> None:
        self.container = container or get_container()
        self._renderers: Dict[str, Type[Any]] = {}
        self._register_default_renderers()

    def _register_default_renderers(self) -> None:
        """標準レンダラー登録"""
        try:
            # 既存のレンダラーを動的にインポートして登録
            renderer_mappings = {
                "html": "kumihan_formatter.core.rendering.html_formatter.HtmlFormatter",
                "markdown": "kumihan_formatter.core.markdown_renderer.MarkdownRenderer",
                "main": "kumihan_formatter.core.rendering.main_renderer.MainRenderer",
            }

            for renderer_type, class_path in renderer_mappings.items():
                try:
                    module_path, class_name = class_path.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[class_name])
                    renderer_class = getattr(module, class_name)
                    self._renderers[renderer_type] = renderer_class
                    logger.debug(
                        f"Registered renderer: {renderer_type} -> {class_name}"
                    )
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Could not register renderer {renderer_type}: {e}")

        except Exception as e:
            logger.error(f"Failed to register default renderers: {e}")

    def create(self, type_name: str, **kwargs: Any) -> BaseRendererProtocol:
        """レンダラー生成"""
        try:
            if type_name not in self._renderers:
                raise ValueError(f"Unknown format type: {type_name}")

            renderer_class = self._renderers[type_name]

            # DIコンテナ経由で生成
            if self.container:
                try:
                    return cast(
                        BaseRendererProtocol, self.container.resolve(renderer_class)
                    )
                except Exception as e:
                    logger.warning(
                        f"DI resolution failed for {type_name}, "
                        f"falling back to direct creation: {e}"
                    )

            # 直接生成
            return cast(BaseRendererProtocol, renderer_class(**kwargs))

        except Exception as e:
            logger.error(f"Renderer creation failed: {type_name}, error: {e}")
            raise

    def register(self, type_name: str, implementation: Type[Any]) -> None:
        """カスタムレンダラー登録"""
        try:
            self._renderers[type_name] = implementation
            if self.container:
                # 抽象クラスの登録は型チェックのために安全に行う
                # DIContainerの型チェックをスキップして安全に登録
                try:
                    if not getattr(implementation, "__abstractmethods__", set()):
                        self.container.register(
                            cast(Any, BaseRendererProtocol), implementation
                        )
                except Exception as reg_error:
                    logger.debug(f"Renderer DI registration skipped: {reg_error}")
            logger.debug(f"Custom renderer registered: {type_name}")
        except Exception as e:
            logger.error(
                f"Custom renderer registration failed: {type_name}, error: {e}"
            )
            raise

    def get_supported_types(self) -> List[str]:
        """対応フォーマット一覧"""
        return list(self._renderers.keys())

    def create_multi_format_renderer(
        self, formats: List[str], **kwargs: Any
    ) -> BaseRendererProtocol:
        """マルチフォーマットレンダラー生成"""
        try:
            # 複数フォーマット対応レンダラーを作成
            # 現時点では最初のフォーマットのレンダラーを返す
            if not formats:
                raise ValueError("At least one format must be specified")

            primary_format = formats[0]
            renderer = self.create(primary_format, **kwargs)

            # 他のフォーマットの情報も保持する場合の拡張ポイント
            # 今後、複数フォーマット対応の複合レンダラーを実装可能

            return renderer

        except Exception as e:
            logger.error(
                f"Multi-format renderer creation failed: {formats}, error: {e}"
            )
            raise


class ServiceFactory:
    """汎用サービスファクトリー - 全ファクトリーの統合管理"""

    def __init__(self, container: Optional[DIContainer] = None) -> None:
        self.container = container or get_container()
        self._factories: Dict[str, AbstractFactory[Any]] = {
            "parser": ParserFactory(container),
            "renderer": RendererFactory(container),
        }

    def get_factory(self, factory_type: str) -> AbstractFactory[Any]:
        """ファクトリー取得"""
        try:
            if factory_type not in self._factories:
                raise ValueError(f"Unknown factory type: {factory_type}")
            return self._factories[factory_type]
        except Exception as e:
            logger.error(f"Factory retrieval failed: {factory_type}, error: {e}")
            raise

    def register_factory(self, name: str, factory: AbstractFactory[Any]) -> None:
        """カスタムファクトリー登録"""
        try:
            self._factories[name] = factory
            logger.debug(f"Custom factory registered: {name}")
        except Exception as e:
            logger.error(f"Custom factory registration failed: {name}, error: {e}")
            raise

    def create(self, factory_type: str, object_type: str, **kwargs: Any) -> Any:
        """オブジェクト生成"""
        try:
            factory = self.get_factory(factory_type)
            return factory.create(object_type, **kwargs)
        except Exception as e:
            logger.error(
                f"Object creation failed: {factory_type}.{object_type}, error: {e}"
            )
            raise


# グローバルファクトリーインスタンス
_service_factory = ServiceFactory()


def get_service_factory() -> ServiceFactory:
    """グローバルサービスファクトリー取得"""
    return _service_factory


# 便利関数
def create_parser(parser_type: str, **kwargs: Any) -> BaseParserProtocol:
    """パーサー生成ショートカット"""
    try:
        return cast(
            BaseParserProtocol, _service_factory.create("parser", parser_type, **kwargs)
        )
    except Exception as e:
        logger.error(f"Parser creation shortcut failed: {parser_type}, error: {e}")
        raise


def create_renderer(format_type: str, **kwargs: Any) -> BaseRendererProtocol:
    """レンダラー生成ショートカット"""
    try:
        return cast(
            BaseRendererProtocol,
            _service_factory.create("renderer", format_type, **kwargs),
        )
    except Exception as e:
        logger.error(f"Renderer creation shortcut failed: {format_type}, error: {e}")
        raise


# 既存ファクトリーとの互換性関数
def get_parser_factory() -> ParserFactory:
    """パーサーファクトリー取得"""
    factory = _service_factory.get_factory("parser")
    assert isinstance(factory, ParserFactory)
    return factory


def get_renderer_factory() -> RendererFactory:
    """レンダラーファクトリー取得"""
    factory = _service_factory.get_factory("renderer")
    assert isinstance(factory, RendererFactory)
    return factory


# ファクトリー初期化関数
def initialize_factories(container: Optional[DIContainer] = None) -> None:
    """ファクトリーシステムの初期化"""
    try:
        global _service_factory
        _service_factory = ServiceFactory(container)
        logger.info("Factory system initialized successfully")
    except Exception as e:
        logger.error(f"Factory system initialization failed: {e}")
        raise
