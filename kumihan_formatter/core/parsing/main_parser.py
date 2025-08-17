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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

from ..ast_nodes import Node, create_node, error_node
from ..utilities.logger import get_logger
from .base import UnifiedParserBase
from .base.parser_protocols import (
    CompositeParserProtocol,
    ParserProtocol,
    StreamingParserProtocol,
)
from .specialized import (
    UnifiedBlockParser,
    UnifiedKeywordParser,
    UnifiedListParser,
    UnifiedMarkdownParser,
)


class MainParser(UnifiedParserBase):
    """統合メインパーサー

    全ての専門パーサーを統括し、効率的な解析を提供:
    - 自動パーサー選択
    - 並列処理サポート
    - ストリーミング処理
    - パフォーマンス最適化
    - エラー耐性
    """

    def __init__(self, config: Optional[Any] = None) -> None:
        super().__init__(parser_type="main")

        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # 専門パーサーの初期化
        self._initialize_parsers()

        # 並列処理設定
        self._setup_parallel_processing()

        # ストリーミング設定
        self._setup_streaming()

        # パフォーマンス監視
        self._setup_performance_monitoring()

    def _initialize_parsers(self) -> None:
        """専門パーサーの初期化"""
        try:
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
        self.parallel_errors = []

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

    def parse(self, text: str, **kwargs: Any) -> List[Node]:
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

    def _parse_sequential(self, text: str, **kwargs: Any) -> List[Node]:
        """順次パース処理"""
        results = []

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

    def _parse_parallel(self, text: str, **kwargs: Any) -> List[Node]:
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

    def _parse_chunk(self, chunk: str, **kwargs: Any) -> List[Node]:
        """チャンク単位のパース処理"""
        return self._parse_sequential(chunk, **kwargs)

    def parse_streaming(self, stream: Iterator[str]) -> Iterator[Node]:
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

    def _select_parsers(self, text: str) -> List[tuple[str, ParserProtocol]]:
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

    def _split_into_chunks(self, text: str) -> List[str]:
        """テキストをチャンクに分割"""
        lines = text.split("\n")
        chunks = []

        current_chunk = []
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

    def _extract_complete_elements(self, buffer: str) -> tuple[List[str], str]:
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

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        return self.performance_stats.copy()

    def get_parser_info(self) -> Dict[str, Any]:
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


# 後方互換性エイリアス
Parser = MainParser
StreamingParser = MainParser  # ストリーミング機能は統合済み


# ユーティリティ関数（parser_utils.py からの統合）
def parse_text(text: str, config: Optional[Any] = None) -> List[Node]:
    """テキストを解析する便利関数"""
    parser = MainParser(config)
    return parser.parse(text)


def parse_file(file_path: str, config: Optional[Any] = None) -> List[Node]:
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
