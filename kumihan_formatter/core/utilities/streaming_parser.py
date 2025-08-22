"""
並列処理対応ストリーミングパーサー - Issue #694 Phase 3対応
スレッド安全性強化版の並列ストリーミング解析システム
"""

import threading
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, cast

from .logger import get_logger
from .processor_core import ChunkInfo, ParallelChunkProcessor


class ParallelStreamingParser:
    """
    並列処理対応ストリーミングパーサー（スレッド安全性強化版）

    改善点:
    - threading.local()によるスレッドローカルストレージ活用
    - スレッド安全なリソース管理
    - デッドロック防止機構
    - メモリリーク防止
    """

    def __init__(
        self, max_workers: Optional[int] = None, chunk_size: int = 100
    ) -> None:
        self.logger = get_logger(__name__)
        self.chunk_processor = ParallelChunkProcessor(max_workers, chunk_size)

        # スレッドローカルストレージの初期化
        import threading

        self._thread_local = threading.local()
        self._initialization_lock = threading.Lock()

        # グローバルリソース管理
        self._active_threads: set[threading.Thread] = set()
        self._shutdown_requested = False
        self._resource_cleanup_callbacks: list[Callable[[], None]] = []

        self.logger.info(
            f"Thread-safe parallel streaming parser initialized with "
            f"{max_workers} workers"
        )

    def parse_file_parallel(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
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
        self,
        text: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
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
            f"Starting thread-safe parallel streaming parse of text: "
            f"{len(text)} characters"
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
        current_thread = threading.current_thread()
        with self._initialization_lock:
            self._active_threads.add(current_thread)

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
                        f"Error processing line {chunk.start_line + current} "
                        f"in chunk {chunk.chunk_id}: {e}"
                    )
                    current += 1  # エラー時は次の行へ

        finally:
            # スレッドをアクティブセットから削除
            with self._initialization_lock:
                self._active_threads.discard(current_thread)

    def _get_thread_local_parser_components(self) -> dict[str, Any]:
        """スレッドローカルなパーサーコンポーネントを取得"""
        with self._initialization_lock:
            # すでにスレッドローカルコンポーネントが存在するかチェック
            if hasattr(self._thread_local, "parser_components"):
                return cast(dict[str, Any], self._thread_local.parser_components)

            # 新しいコンポーネントを作成
            # TODO: クラス循環参照解決後に実装予定 (Issue #922で対応予定)
            # 現在のアーキテクチャでは循環参照のリスクがあるため、構造改善後に実装
            components = {
                "parser": None,  # KumihanParser(),
                "block_handler": None,  # BlockHandler(),
                "inline_handler": None,  # InlineHandler(),
                "html_renderer": None,  # HTMLRenderer(),
                "block_parser": self._create_mock_block_parser(),
                "list_parser": self._create_mock_list_parser(),
            }

            # スレッドローカルに保存
            self._thread_local.parser_components = components

            # アクティブスレッド追跡
            current_thread = threading.current_thread()
            thread_id = current_thread.ident
            if thread_id:
                self._active_threads.add(current_thread)

            self.logger.debug(f"Initialized parser components for thread {thread_id}")
            return components

    def _create_mock_block_parser(self) -> Any:
        """モック用ブロックパーサーを作成"""

        class MockBlockParser:
            def is_opening_marker(self, line: str) -> bool:
                return line.startswith("#")

            def parse_block_marker(
                self, lines: List[str], current: int
            ) -> tuple[Any, int]:
                # 簡易実装
                return {"type": "block", "content": lines[current]}, current + 1

            def parse_paragraph(
                self, lines: List[str], current: int
            ) -> tuple[Any, int]:
                # 簡易実装
                return {"type": "paragraph", "content": lines[current]}, current + 1

        return MockBlockParser()

    def _create_mock_list_parser(self) -> Any:
        """モック用リストパーサーを作成"""

        class MockListParser:
            def is_list_line(self, line: str) -> Optional[str]:
                if line.strip().startswith("-"):
                    return "ul"
                elif line.strip().startswith("1."):
                    return "ol"
                return None

            def parse_unordered_list(
                self, lines: List[str], current: int
            ) -> tuple[Any, int]:
                # 簡易実装
                return {"type": "ul", "content": lines[current]}, current + 1

            def parse_ordered_list(
                self, lines: List[str], current: int
            ) -> tuple[Any, int]:
                # 簡易実装
                return {"type": "ol", "content": lines[current]}, current + 1

        return MockListParser()

    def _parse_block_safe(
        self, parser_components: Dict[str, Any], lines: List[str], current: int
    ) -> tuple[Any, int]:
        """スレッド安全なブロック解析"""
        try:
            return cast(
                tuple[Any, int],
                parser_components["block_parser"].parse_block_marker(lines, current),
            )
        except Exception as e:
            self.logger.error(f"Error in block parsing: {e}")
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
                return cast(
                    tuple[Any, int],
                    parser_components["list_parser"].parse_unordered_list(
                        lines, current
                    ),
                )
            else:  # ol
                return cast(
                    tuple[Any, int],
                    parser_components["list_parser"].parse_ordered_list(lines, current),
                )
        except Exception as e:
            self.logger.error(f"Error in list parsing: {e}")
            return None, current + 1

    def _parse_paragraph_safe(
        self, parser_components: Dict[str, Any], lines: List[str], current: int
    ) -> tuple[Any, int]:
        """スレッド安全なパラグラフ解析"""
        try:
            return cast(
                tuple[Any, int],
                parser_components["block_parser"].parse_paragraph(lines, current),
            )
        except Exception as e:
            self.logger.error(f"Error in paragraph parsing: {e}")
            return None, current + 1

    def _skip_empty_lines_safe(self, lines: List[str], current: int) -> int:
        """スレッド安全な空行スキップ"""
        while current < len(lines) and not lines[current].strip():
            current += 1
            if self._shutdown_requested:
                break
        return current

    def request_shutdown(self) -> None:
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

    def _cleanup_thread_resources(self) -> None:
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

    def add_cleanup_callback(self, callback: Callable[[], None]) -> None:
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

    def __del__(self) -> None:
        """デストラクタでリソースクリーンアップを保証"""
        try:
            if hasattr(self, "_shutdown_requested") and not self._shutdown_requested:
                self.request_shutdown()
                self._cleanup_thread_resources()
        except Exception:
            pass  # デストラクタでの例外は無視
