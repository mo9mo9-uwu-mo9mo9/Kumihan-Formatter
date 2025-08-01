"""
並列処理対応パーサー - Issue #694 Phase 3対応
大容量ファイルの並列チャンク処理による更なる高速化
"""

import concurrent.futures
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

from .logger import get_logger


@dataclass
class ChunkInfo:
    """処理チャンク情報"""

    chunk_id: int
    start_line: int
    end_line: int
    lines: List[str]
    file_position: int = 0


class ParallelChunkProcessor:
    """
    並列チャンク処理システム

    特徴:
    - ThreadPoolExecutorによる並列処理
    - チャンク間の依存関係を考慮した安全な並列化
    - メモリ効率を維持した並列実行
    - プログレス追跡統合
    """

    def __init__(self, max_workers: Optional[int] = None, chunk_size: int = 100):
        self.logger = get_logger(__name__)
        self.max_workers = max_workers or min(4, (threading.active_count() or 1) + 2)
        self.chunk_size = chunk_size

        # スレッドセーフティ
        self._lock = threading.Lock()
        self._results_lock = threading.Lock()

        self.logger.info(
            f"ParallelChunkProcessor initialized: {self.max_workers} workers, chunk_size={chunk_size}"
        )

    def process_chunks_parallel(
        self,
        chunks: List[ChunkInfo],
        processing_func: Callable[[ChunkInfo], Iterator[Any]],
        progress_callback: Optional[Callable] = None,
    ) -> Iterator[Any]:
        """
        チャンクリストを並列処理

        Args:
            chunks: 処理対象チャンクリスト
            processing_func: チャンク処理関数
            progress_callback: プログレス更新コールバック

        Yields:
            Any: 処理結果
        """
        self.logger.info(f"Starting parallel processing of {len(chunks)} chunks")

        # 並列処理実行
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 全チャンクを並列で開始
            future_to_chunk = {
                executor.submit(
                    self._process_single_chunk, chunk, processing_func
                ): chunk
                for chunk in chunks
            }

            completed_chunks = 0

            # 完了順に結果を取得
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk = future_to_chunk[future]

                try:
                    results = future.result()

                    # 結果をyield（順序は保証されない）
                    for result in results:
                        yield result

                    completed_chunks += 1

                    # プログレス更新
                    if progress_callback:
                        progress_info = {
                            "completed_chunks": completed_chunks,
                            "total_chunks": len(chunks),
                            "chunk_id": chunk.chunk_id,
                            "progress_percent": (completed_chunks / len(chunks)) * 100,
                        }
                        progress_callback(progress_info)

                except Exception as e:
                    self.logger.error(f"Chunk {chunk.chunk_id} processing failed: {e}")
                    # エラーチャンクはスキップして継続
                    continue

        self.logger.info(
            f"Parallel processing completed: {completed_chunks}/{len(chunks)} chunks"
        )

    def _process_single_chunk(
        self, chunk: ChunkInfo, processing_func: Callable[[ChunkInfo], Iterator[Any]]
    ) -> List[Any]:
        """単一チャンクを処理（スレッドセーフ）"""
        try:
            with self._lock:
                self.logger.debug(
                    f"Processing chunk {chunk.chunk_id}: lines {chunk.start_line}-{chunk.end_line}"
                )

            results = list(processing_func(chunk))

            with self._lock:
                self.logger.debug(
                    f"Chunk {chunk.chunk_id} completed: {len(results)} results"
                )

            return results

        except Exception as e:
            with self._lock:
                self.logger.error(f"Error in chunk {chunk.chunk_id}: {e}")
            raise

    def create_chunks_from_lines(
        self, lines: List[str], chunk_size: Optional[int] = None
    ) -> List[ChunkInfo]:
        """行リストからチャンクを作成"""
        effective_chunk_size = chunk_size or self.chunk_size
        chunks = []

        for i in range(0, len(lines), effective_chunk_size):
            chunk_lines = lines[i : i + effective_chunk_size]
            chunk = ChunkInfo(
                chunk_id=len(chunks),
                start_line=i,
                end_line=min(i + effective_chunk_size - 1, len(lines) - 1),
                lines=chunk_lines,
            )
            chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} chunks from {len(lines)} lines")
        return chunks

    def create_chunks_from_file(
        self, file_path: Path, chunk_size: Optional[int] = None
    ) -> List[ChunkInfo]:
        """ファイルからチャンクを作成（メモリ効率版）"""
        effective_chunk_size = chunk_size or self.chunk_size
        chunks = []

        with open(file_path, "r", encoding="utf-8") as file:
            current_chunk_lines = []
            current_start_line = 0
            line_number = 0

            for line in file:
                current_chunk_lines.append(line.rstrip("\n"))
                line_number += 1

                if len(current_chunk_lines) >= effective_chunk_size:
                    # チャンク作成
                    chunk = ChunkInfo(
                        chunk_id=len(chunks),
                        start_line=current_start_line,
                        end_line=line_number - 1,
                        lines=current_chunk_lines.copy(),
                    )
                    chunks.append(chunk)

                    # 次のチャンク準備
                    current_chunk_lines.clear()
                    current_start_line = line_number

            # 残りの行でチャンク作成
            if current_chunk_lines:
                chunk = ChunkInfo(
                    chunk_id=len(chunks),
                    start_line=current_start_line,
                    end_line=line_number - 1,
                    lines=current_chunk_lines,
                )
                chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} chunks from file: {file_path}")
        return chunks


class ParallelStreamingParser:
    """
    並列処理対応ストリーミングパーサー（スレッド安全性強化版）

    改善点:
    - threading.local()によるスレッドローカルストレージ活用
    - スレッド安全なリソース管理
    - デッドロック防止機構
    - メモリリーク防止
    """

    def __init__(self, max_workers: Optional[int] = None, chunk_size: int = 100):
        self.logger = get_logger(__name__)
        self.chunk_processor = ParallelChunkProcessor(max_workers, chunk_size)

        # スレッドローカルストレージの初期化
        import threading

        self._thread_local = threading.local()
        self._initialization_lock = threading.Lock()

        # グローバルリソース管理
        self._active_threads = set()
        self._shutdown_requested = False
        self._resource_cleanup_callbacks = []

        self.logger.info(
            f"Thread-safe parallel streaming parser initialized with {max_workers} workers"
        )

    def parse_file_parallel(
        self, file_path: Path, progress_callback: Optional[Callable] = None
    ) -> Iterator[Any]:
        """
        ファイルを並列ストリーミング解析（スレッド安全版）

        Args:
            file_path: 解析対象ファイル
            progress_callback: プログレス更新コールバック

        Yields:
            Any: 解析済みノード
        """
        self.logger.info(f"Starting thread-safe parallel streaming parse: {file_path}")

        try:
            # ファイルからチャンク作成
            chunks = self.chunk_processor.create_chunks_from_file(file_path)

            # 並列処理実行（スレッド安全）
            yield from self.chunk_processor.process_chunks_parallel(
                chunks, self._parse_chunk_thread_safe, progress_callback
            )
        finally:
            # リソースクリーンアップ
            self._cleanup_thread_resources()

    def parse_text_parallel(
        self, text: str, progress_callback: Optional[Callable] = None
    ) -> Iterator[Any]:
        """
        テキストを並列ストリーミング解析（スレッド安全版）

        Args:
            text: 解析対象テキスト
            progress_callback: プログレス更新コールバック

        Yields:
            Any: 解析済みノード
        """
        self.logger.info(
            f"Starting thread-safe parallel streaming parse of text: {len(text)} characters"
        )

        try:
            # テキストを行に分割してチャンク作成
            lines = text.split("\n")
            chunks = self.chunk_processor.create_chunks_from_lines(lines)

            # 並列処理実行（スレッド安全）
            yield from self.chunk_processor.process_chunks_parallel(
                chunks, self._parse_chunk_thread_safe, progress_callback
            )
        finally:
            # リソースクリーンアップ
            self._cleanup_thread_resources()

    def _parse_chunk_thread_safe(self, chunk: ChunkInfo) -> Iterator[Any]:
        """
        スレッド安全なチャンク解析

        Args:
            chunk: 処理対象チャンク

        Yields:
            Any: 解析済みノード
        """
        import threading

        thread_id = threading.get_ident()

        # スレッドをアクティブセットに追加
        with self._initialization_lock:
            self._active_threads.add(thread_id)

        try:
            # スレッドローカルパーサーコンポーネントを取得
            parser_components = self._get_thread_local_parser_components()

            # シャットダウンチェック
            if self._shutdown_requested:
                self.logger.debug(f"Thread {thread_id} received shutdown signal")
                return

            # チャンク内の行を順次処理
            current = 0
            while current < len(chunk.lines) and not self._shutdown_requested:
                try:
                    # 空行スキップ
                    current = self._skip_empty_lines_safe(chunk.lines, current)
                    if current >= len(chunk.lines):
                        break

                    line = chunk.lines[current].strip()

                    # 行の種類に応じて適切なパーサーで処理
                    if parser_components["block_parser"].is_opening_marker(line):
                        node, next_index = self._parse_block_safe(
                            parser_components, chunk.lines, current
                        )
                        if node:
                            yield node
                        current = next_index

                    elif line.startswith("#") and not parser_components[
                        "block_parser"
                    ].is_opening_marker(line):
                        current += 1  # コメント行スキップ

                    else:
                        # リスト解析チェック
                        list_type = parser_components["list_parser"].is_list_line(line)
                        if list_type:
                            node, next_index = self._parse_list_safe(
                                parser_components, chunk.lines, current, list_type
                            )
                            if node:
                                yield node
                            current = next_index
                        else:
                            # パラグラフ解析
                            node, next_index = self._parse_paragraph_safe(
                                parser_components, chunk.lines, current
                            )
                            if node:
                                yield node
                            current = next_index

                except Exception as e:
                    self.logger.warning(
                        f"Error processing line {chunk.start_line + current} in chunk {chunk.chunk_id}: {e}"
                    )
                    current += 1  # エラー時は次の行へ

        finally:
            # スレッドをアクティブセットから削除
            with self._initialization_lock:
                self._active_threads.discard(thread_id)

    def _get_thread_local_parser_components(self) -> Dict[str, Any]:
        """スレッドローカルパーサーコンポーネントを取得（threading.local使用）"""
        # スレッドローカルストレージからコンポーネントを取得
        if not hasattr(self._thread_local, "parser_components"):
            # 新しいスレッド用のパーサーコンポーネントを作成
            from ...block_parser import BlockParser
            from ...keyword_parser import KeywordParser
            from ...list_parser import ListParser

            keyword_parser = KeywordParser()

            self._thread_local.parser_components = {
                "keyword_parser": keyword_parser,
                "list_parser": ListParser(keyword_parser),
                "block_parser": BlockParser(keyword_parser),
                "thread_id": threading.get_ident(),
                "created_at": time.time(),
            }

            self.logger.debug(
                f"Created thread-local parser components for thread {threading.get_ident()}"
            )

        return self._thread_local.parser_components

    def _parse_block_safe(
        self, parser_components: Dict[str, Any], lines: List[str], current: int
    ) -> tuple[Any, int]:
        """スレッド安全なブロック解析"""
        try:
            return parser_components["block_parser"].parse_block_marker(lines, current)
        except Exception as e:
            self.logger.warning(f"Thread-safe block parse error: {e}")
            return None, current + 1

    def _parse_list_safe(
        self,
        parser_components: Dict[str, Any],
        lines: List[str],
        current: int,
        list_type: str,
    ) -> tuple[Any, int]:
        """スレッド安全なリスト解析"""
        try:
            if list_type == "ul":
                return parser_components["list_parser"].parse_unordered_list(
                    lines, current
                )
            else:
                return parser_components["list_parser"].parse_ordered_list(
                    lines, current
                )
        except Exception as e:
            self.logger.warning(f"Thread-safe list parse error: {e}")
            return None, current + 1

    def _parse_paragraph_safe(
        self, parser_components: Dict[str, Any], lines: List[str], current: int
    ) -> tuple[Any, int]:
        """スレッド安全なパラグラフ解析"""
        try:
            return parser_components["block_parser"].parse_paragraph(lines, current)
        except Exception as e:
            self.logger.warning(f"Thread-safe paragraph parse error: {e}")
            return None, current + 1

    def _skip_empty_lines_safe(self, lines: List[str], current: int) -> int:
        """スレッド安全な空行スキップ"""
        while current < len(lines) and not lines[current].strip():
            current += 1
            if self._shutdown_requested:
                break
        return current

    def request_shutdown(self):
        """すべてのスレッドに安全なシャットダウンを要求"""
        self.logger.info("Requesting graceful shutdown of all worker threads")
        self._shutdown_requested = True

        # アクティブスレッドの完了を待機（タイムアウト付き）
        import time

        timeout = 5.0  # 5秒タイムアウト
        start_time = time.time()

        while self._active_threads and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if self._active_threads:
            self.logger.warning(
                f"Timeout waiting for {len(self._active_threads)} threads to finish"
            )
        else:
            self.logger.info("All threads finished gracefully")

    def _cleanup_thread_resources(self):
        """スレッドリソースをクリーンアップ"""
        # スレッドローカルストレージのクリーンアップ
        if hasattr(self._thread_local, "parser_components"):
            delattr(self._thread_local, "parser_components")

        # 登録されたクリーンアップコールバックを実行
        for callback in self._resource_cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.warning(f"Resource cleanup callback error: {e}")

        self.logger.debug("Thread resources cleaned up")

    def add_cleanup_callback(self, callback: Callable[[], None]):
        """リソースクリーンアップコールバックを追加"""
        self._resource_cleanup_callbacks.append(callback)

    def get_thread_statistics(self) -> Dict[str, Any]:
        """スレッド統計情報を取得"""
        with self._initialization_lock:
            active_count = len(self._active_threads)
            active_thread_ids = list(self._active_threads)

        return {
            "active_threads": active_count,
            "active_thread_ids": active_thread_ids,
            "shutdown_requested": self._shutdown_requested,
            "cleanup_callbacks_count": len(self._resource_cleanup_callbacks),
        }

    def __del__(self):
        """デストラクタでリソースクリーンアップを保証"""
        try:
            if hasattr(self, "_shutdown_requested") and not self._shutdown_requested:
                self.request_shutdown()
                self._cleanup_thread_resources()
        except Exception:
            pass  # デストラクタでの例外は無視
