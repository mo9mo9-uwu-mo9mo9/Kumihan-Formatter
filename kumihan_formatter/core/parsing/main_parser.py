"""統合メインパーサー

Issue #912: Parser系統合リファクタリング
重複メインパーサーを統合:
- kumihan_formatter/parser.py (746行、メインパーサー)
- kumihan_formatter/streaming_parser.py (ストリーミング処理)
- kumihan_formatter/parser_utils.py (ユーティリティ)

統合機能:
- 全パーサーの統括管理
- 並列処理サポート
- ストリーミング解析
- パフォーマンス監視
- 設定管理
- エラーハンドリング
- 後方互換性維持
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Iterator, Optional, cast

if TYPE_CHECKING:
    from ..patterns.dependency_injection import DIContainer
    from ..patterns.factories import ParserFactory

from ..ast_nodes import Node, create_node, error_node
from ..mixins.event_mixin import EventEmitterMixin, with_events
from ..utilities.logger import get_logger
from .base import UnifiedParserBase
from .base.parser_protocols import (
    BaseParserProtocol,
    CompositeParserProtocol,
    ParseContext,
    ParseResult,
    ParserProtocol,
    StreamingParserProtocol,
    create_parse_result,
)
from .specialized import (
    UnifiedBlockParser,
    UnifiedKeywordParser,
    UnifiedListParser,
    UnifiedMarkdownParser,
)


class MainParser(
    UnifiedParserBase,
    EventEmitterMixin,
    CompositeParserProtocol,
    StreamingParserProtocol,
):
    """統合メインパーサー

    全ての専門パーサーを統括し、効率的な解析を提供:
    - 自動パーサー選択
    - 並列処理サポート
    - ストリーミング処理
    - パフォーマンス最適化
    - エラー耐性
    """

    def __init__(
        self, config: Optional[Any] = None, container: Optional["DIContainer"] = None
    ) -> None:
        super().__init__(parser_type="main")

        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # EventEmitterMixin初期化
        self._source_name = self.__class__.__name__

        # DIコンテナ設定（Issue #914 Phase 2）
        self.container = container
        if self.container is None:
            try:
                from ..patterns.dependency_injection import get_container

                self.container = get_container()
                self.logger.debug("Using global DI container")
            except ImportError:
                self.logger.debug(
                    "DI container not available, using direct instantiation"
                )
                self.container = None

        # ファクトリー設定（Issue #914 Phase 2）
        self.parser_factory: Optional["ParserFactory"] = None
        if self.container is not None:
            try:
                from ..patterns.factories import get_parser_factory

                self.parser_factory = get_parser_factory()
                self.logger.debug("Parser factory initialized with DI support")
            except ImportError:
                self.logger.debug(
                    "Parser factory not available, falling back to direct instantiation"
                )

        # 専門パーサーの初期化
        self._initialize_parsers()

        # 並列処理設定
        self._setup_parallel_processing()

        # ストリーミング設定
        self._setup_streaming()

        # パフォーマンス監視
        self._setup_performance_monitoring()

    def _initialize_parsers(self) -> None:
        """専門パーサーの初期化（DI対応 - Issue #914 Phase 2）"""
        try:
            # DIパターンによる初期化を試行
            if self.parser_factory is not None and self.container is not None:
                self.logger.debug("Initializing parsers using DI pattern")
                self.keyword_parser = self._create_parser_with_fallback("keyword")
                self.list_parser = self._create_parser_with_fallback("list")
                self.block_parser = self._create_parser_with_fallback("block")
                self.markdown_parser = self._create_parser_with_fallback("markdown")
            else:
                # 従来の直接インスタンス化（フォールバック）
                self.logger.debug("Initializing parsers using direct instantiation")
                self.keyword_parser = UnifiedKeywordParser()
                self.list_parser = UnifiedListParser()
                self.block_parser = UnifiedBlockParser()
                self.markdown_parser = UnifiedMarkdownParser()

            # パーサー管理
            self.parsers = {
                "keyword": self.keyword_parser,
                "list": self.list_parser,
                "block": self.block_parser,
                "markdown": self.markdown_parser,
            }

            self.logger.info("All specialized parsers initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize parsers: {e}")
            # フォールバック: 最小限のパーサー
            self._initialize_fallback_parsers()

    def _create_parser_with_fallback(self, parser_type: str) -> Any:
        """DI失敗時のフォールバック付きパーサー生成（Issue #914 Phase 2）"""
        try:
            # 1. DIコンテナ経由で解決を試行
            if self.container is not None:
                try:
                    # 型マッピング
                    parser_class_map = {
                        "keyword": UnifiedKeywordParser,
                        "list": UnifiedListParser,
                        "block": UnifiedBlockParser,
                        "markdown": UnifiedMarkdownParser,
                    }

                    if parser_type in parser_class_map:
                        parser_class = parser_class_map[parser_type]
                        instance = self.container.resolve(parser_class)
                        self.logger.debug(f"DI resolution successful for {parser_type}")
                        return cast(ParserProtocol, instance)
                except Exception as di_error:
                    self.logger.warning(
                        f"DI creation failed for {parser_type}: {di_error}"
                    )

            # 2. ファクトリー経由での生成を試行
            if self.parser_factory is not None:
                try:
                    instance = self.parser_factory.create(parser_type)
                    self.logger.debug(f"Factory creation successful for {parser_type}")
                    return cast(ParserProtocol, instance)
                except Exception as factory_error:
                    self.logger.warning(
                        f"Factory creation failed for {parser_type}: {factory_error}"
                    )

            # 3. 直接インスタンス化（最終フォールバック）
            return self._create_direct_instance(parser_type)

        except Exception as e:
            self.logger.error(
                f"All parser creation methods failed for {parser_type}: {e}"
            )
            return self._create_direct_instance(parser_type)

    def _create_direct_instance(self, parser_type: str) -> Any:
        """直接インスタンス化（最終フォールバック）"""
        try:
            parser_class_map = {
                "keyword": UnifiedKeywordParser,
                "list": UnifiedListParser,
                "block": UnifiedBlockParser,
                "markdown": UnifiedMarkdownParser,
            }

            if parser_type in parser_class_map:
                parser_class = parser_class_map[parser_type]
                instance = parser_class()
                self.logger.debug(f"Direct instantiation successful for {parser_type}")
                return instance
            else:
                raise ValueError(f"Unknown parser type: {parser_type}")

        except Exception as e:
            self.logger.error(f"Direct instantiation failed for {parser_type}: {e}")
            # 最小限の汎用パーサーを返す
            return self._create_minimal_parser()

    def _create_minimal_parser(self) -> Any:
        """最小限の汎用パーサー生成"""

        class MinimalParser:
            def can_parse(self, text: str) -> bool:
                return False

            def parse(self, text: str) -> list[Node]:
                return [create_node("text", content=text)]

        return MinimalParser()

    def _initialize_fallback_parsers(self) -> None:
        """フォールバック用最小限パーサー"""
        self.logger.warning("Using fallback parser initialization")
        self.parsers = {}

    def _setup_parallel_processing(self) -> None:
        """並列処理の設定"""
        # 並列処理閾値
        self.parallel_threshold_lines = 10000
        self.parallel_threshold_chars = 100000

        # 並列処理設定
        self.max_workers = min(4, (self._get_cpu_count() or 1))
        self.chunk_size = 1000

        # エラートラッキング
        self.parallel_errors: list[dict[str, str]] = []

    def _setup_streaming(self) -> None:
        """ストリーミング処理の設定"""
        self.buffer_size = 8192
        self.stream_chunk_size = 1024
        self.stream_timeout = 30.0

    def _setup_performance_monitoring(self) -> None:
        """パフォーマンス監視の設定"""
        self.performance_stats = {
            "total_parses": 0,
            "total_time": 0.0,
            "average_time": 0.0,
            "parallel_parses": 0,
            "streaming_parses": 0,
        }

    @with_events("main_parse")
    def parse(self, text: str, **kwargs: Any) -> list[Node]:
        """メインパース処理

        Args:
            text: パース対象のテキスト
            **kwargs: 追加オプション

        Returns:
            パース結果のノードリスト
        """
        start_time = time.time()

        try:
            # 入力検証
            if not self._validate_input(text):
                return [error_node("Invalid input text")]

            # パフォーマンス統計更新
            self.performance_stats["total_parses"] += 1

            # 並列処理判定
            if self._should_use_parallel_processing(text):
                result = self._parse_parallel(text, **kwargs)
                self.performance_stats["parallel_parses"] += 1
            else:
                result = self._parse_sequential(text, **kwargs)

            # 実行時間記録
            elapsed_time = time.time() - start_time
            self._update_performance_stats(elapsed_time)

            return result

        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return [error_node(f"Parse error: {e}")]

    def _parse_sequential(self, text: str, **kwargs: Any) -> list[Node]:
        """順次パース処理"""
        results: list[Node] = []

        # 適切なパーサーを選択して実行
        selected_parsers = self._select_parsers(text)

        for parser_name, parser in selected_parsers:
            try:
                if hasattr(parser, "can_parse") and parser.can_parse(text):
                    result = parser.parse(text)
                    if isinstance(result, list):
                        results.extend(result)
                    elif isinstance(result, Node):
                        results.append(result)

            except Exception as e:
                self.logger.warning(f"Parser {parser_name} failed: {e}")
                continue

        return results if results else [create_node("document", content=text)]

    def _parse_parallel(self, text: str, **kwargs: Any) -> list[Node]:
        """並列パース処理"""
        try:
            # テキストをチャンクに分割
            chunks = self._split_into_chunks(text)

            results = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # チャンクごとに並列処理
                future_to_chunk = {
                    executor.submit(self._parse_chunk, chunk, **kwargs): chunk
                    for chunk in chunks
                }

                for future in as_completed(future_to_chunk):
                    try:
                        chunk_result = future.result()
                        if chunk_result:
                            results.extend(chunk_result)
                    except Exception as e:
                        chunk = future_to_chunk[future]
                        self.logger.error(f"Chunk parse error: {e}")
                        self.parallel_errors.append(
                            {
                                "chunk": (
                                    chunk[:100] + "..." if len(chunk) > 100 else chunk
                                ),
                                "error": str(e),
                            }
                        )

            return results

        except Exception as e:
            self.logger.error(f"Parallel parsing failed: {e}")
            # フォールバック: 順次処理
            return self._parse_sequential(text, **kwargs)

    def _parse_chunk(self, chunk: str, **kwargs: Any) -> list[Node]:
        """チャンク単位のパース処理"""
        return self._parse_sequential(chunk, **kwargs)

    def parse_streaming(
        self, stream: Iterator[str], context: Optional[ParseContext] = None
    ) -> Iterator[Node]:
        """ストリーミングパース処理

        Args:
            stream: 入力ストリーム

        Yields:
            パース結果のノード
        """
        self.performance_stats["streaming_parses"] += 1

        buffer = ""

        try:
            for chunk in stream:
                buffer += chunk

                # バッファサイズが閾値を超えた場合、部分解析
                if len(buffer) >= self.buffer_size:
                    # 完全な構文要素を抽出
                    complete_elements, remaining = self._extract_complete_elements(
                        buffer
                    )

                    for element in complete_elements:
                        results = self._parse_sequential(element)
                        for result in results:
                            yield result

                    buffer = remaining

            # 残りのバッファを処理
            if buffer.strip():
                results = self._parse_sequential(buffer)
                for result in results:
                    yield result

        except Exception as e:
            self.logger.error(f"Streaming parse error: {e}")
            yield error_node(f"Streaming parse error: {e}")

    def _select_parsers(self, text: str) -> list[tuple[str, ParserProtocol]]:
        """テキストに適したパーサーを選択"""
        selected = []

        for name, parser in self.parsers.items():
            try:
                if hasattr(parser, "can_parse") and parser.can_parse(text):
                    selected.append((name, parser))
            except Exception as e:
                self.logger.warning(f"Parser selection error for {name}: {e}")

        return selected

    def _should_use_parallel_processing(self, text: str) -> bool:
        """並列処理を使用すべきか判定"""
        if not text:
            return False

        line_count = text.count("\n") + 1
        char_count = len(text)

        return (
            line_count >= self.parallel_threshold_lines
            or char_count >= self.parallel_threshold_chars
        )

    def _split_into_chunks(self, text: str) -> list[str]:
        """テキストをチャンクに分割"""
        lines = text.split("\n")
        chunks = []

        current_chunk: list[str] = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > self.chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _extract_complete_elements(self, buffer: str) -> tuple[list[str], str]:
        """バッファから完全な構文要素を抽出"""
        elements = []

        # ブロック要素の抽出（## で終わる）
        parts = buffer.split("##")

        if len(parts) > 1:
            # 最後以外は完全なブロック
            for i in range(len(parts) - 1):
                if i == 0:
                    elements.append(parts[i] + "##")
                else:
                    elements.append("##" + parts[i] + "##")

            remaining = parts[-1]
        else:
            remaining = buffer

        return elements, remaining

    def _update_performance_stats(self, elapsed_time: float) -> None:
        """パフォーマンス統計を更新"""
        self.performance_stats["total_time"] += elapsed_time
        self.performance_stats["average_time"] = (
            self.performance_stats["total_time"]
            / self.performance_stats["total_parses"]
        )

    def _get_cpu_count(self) -> Optional[int]:
        """CPU数を取得"""
        try:
            import os

            return os.cpu_count()
        except Exception:
            return None

    def _validate_input(self, text: str) -> bool:
        """入力の妥当性を検証"""
        return isinstance(text, str) and bool(text.strip())

    def get_performance_stats(self) -> dict[str, Any]:
        """パフォーマンス統計を取得"""
        return self.performance_stats.copy()

    def get_parser_info(self) -> dict[str, Any]:
        """パーサー情報を取得"""
        info = {
            "main_parser": {
                "type": self.parser_type,
                "parallel_threshold_lines": self.parallel_threshold_lines,
                "parallel_threshold_chars": self.parallel_threshold_chars,
                "max_workers": self.max_workers,
            },
            "specialized_parsers": {},
        }

        for name, parser in self.parsers.items():
            try:
                parser_info = {
                    "type": getattr(parser, "parser_type", "unknown"),
                    "available": True,
                }

                if hasattr(parser, "get_keyword_statistics"):
                    parser_info["statistics"] = parser.get_keyword_statistics()
                elif hasattr(parser, "get_list_statistics"):
                    parser_info["statistics"] = parser.get_list_statistics()

                info["specialized_parsers"][name] = parser_info

            except Exception as e:
                info["specialized_parsers"][name] = {
                    "available": False,
                    "error": str(e),
                }

        return info

    def reset_statistics(self) -> None:
        """統計情報をリセット"""
        self.performance_stats = {
            "total_parses": 0,
            "total_time": 0.0,
            "average_time": 0.0,
            "parallel_parses": 0,
            "streaming_parses": 0,
        }
        self.parallel_errors.clear()

    # ==========================================
    # プロトコル準拠メソッド（CompositeParserProtocol & StreamingParserProtocol実装）
    # ==========================================

    def parse_protocol(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース（プロトコル準拠）"""
        try:
            # 既存のparseメソッドを使用
            nodes = self.parse(content)
            return create_parse_result(nodes=nodes, success=True)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"メインパース失敗: {e}")
            return result

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> list[str]:
        """バリデーション実装（プロトコル準拠）"""
        errors = []
        try:
            # 各専門パーサーでバリデーション実行
            for name, parser in self.parsers.items():
                if hasattr(parser, "validate"):
                    parser_errors = parser.validate(content, context)
                    for error in parser_errors:
                        errors.append(f"{name}: {error}")
        except Exception as e:
            errors.append(f"バリデーションエラー: {e}")
        return errors

    def get_parser_info_protocol(self) -> dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "MainParser",
            "version": "2.0.0",
            "supported_formats": ["kumihan", "markdown", "text"],
            "capabilities": ["composite_parsing", "parallel_processing", "streaming"],
            "specialized_parsers": list(self.parsers.keys()),
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
        return format_hint in ["kumihan", "markdown", "text", "auto"]

    def register_parser(self, name: str, parser: ParserProtocol) -> None:
        """パーサーの登録（プロトコル準拠）"""
        self.parsers[name] = parser
        self.logger.info(f"Registered parser: {name}")

    def unregister_parser(self, name: str) -> bool:
        """パーサーの登録解除（プロトコル準拠）"""
        if name in self.parsers:
            del self.parsers[name]
            self.logger.info(f"Unregistered parser: {name}")
            return True
        return False

    def parse_streaming_protocol(
        self, stream: Iterator[str], context: Optional[ParseContext] = None
    ) -> Iterator[ParseResult]:
        """ストリーミングパース（プロトコル準拠）"""
        try:
            for chunk in stream:
                yield self.parse_protocol(chunk, context)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"ストリーミングパース失敗: {e}")
            yield result

    # CompositeParserProtocolの抽象メソッド実装
    def add_parser(self, parser: BaseParserProtocol, priority: int = 0) -> None:
        """パーサーを追加（抽象メソッド実装）"""
        parser_name = f"{parser.__class__.__name__}_{priority}"
        self.parsers[parser_name] = cast(ParserProtocol, parser)
        self.logger.info(f"Added parser: {parser_name} with priority {priority}")

    def remove_parser(self, parser: BaseParserProtocol) -> bool:
        """パーサーを削除（抽象メソッド実装）"""
        for name, registered_parser in list(self.parsers.items()):
            if registered_parser is parser:
                del self.parsers[name]
                self.logger.info(f"Removed parser: {name}")
                return True
        return False

    def get_parsers(self) -> list[BaseParserProtocol]:
        """登録されたパーサーリストを取得（抽象メソッド実装）"""
        return list(self.parsers.values())

    # StreamingParserProtocolの抽象メソッド実装
    def get_chunk_size(self) -> int:
        """チャンクサイズを取得（抽象メソッド実装）"""
        return self.chunk_size

    def process_chunk(
        self, chunk: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """チャンクを処理（拽象メソッド実装）"""
        try:
            nodes = self._parse_sequential(chunk)
            return create_parse_result(nodes=nodes, success=True)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"チャンク処理失敗: {e}")
            return result

    def supports_streaming(self) -> bool:
        """ストリーミング対応判定（抽象メソッド実装）"""
        return True

    def get_parser_count(self) -> int:
        """登録パーサー数を取得（抽象メソッド実装）"""
        return len(self.parsers)

    def clear_parsers(self) -> None:
        """全パーサーをクリア（抽象メソッド実装）"""
        self.parsers.clear()
        self.logger.info("Cleared all parsers")


# 後方互換性エイリアス
Parser = MainParser
StreamingParser = MainParser  # ストリーミング機能は統合済み


# ユーティリティ関数（parser_utils.py からの統合）
def parse_text(text: str, config: Optional[Any] = None) -> list[Node]:
    """テキストを解析する便利関数"""
    parser = MainParser(config)
    return cast(list[Node], parser.parse(text))


def parse_file(file_path: str, config: Optional[Any] = None) -> list[Node]:
    """ファイルを解析する便利関数"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return parse_text(content, config)
    except Exception as e:
        return [error_node(f"File parse error: {e}")]


def parse_stream(stream: Iterator[str], config: Optional[Any] = None) -> Iterator[Node]:
    """ストリームを解析する便利関数"""
    parser = MainParser(config)
    return parser.parse_streaming(stream)
