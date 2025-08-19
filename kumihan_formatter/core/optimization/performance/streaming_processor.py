"""
ストリーミング処理最適化システム - Issue #922 Phase 4-6対応
大型ファイル・メモリ効率重視のストリーミング処理システム
"""

import asyncio
import mmap
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from queue import Empty, Queue
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Protocol,
    TypeVar,
)

from kumihan_formatter.core.utilities.logger import get_logger

T = TypeVar("T")
R = TypeVar("R")


class StreamingMode(Enum):
    """ストリーミングモード"""

    LINE_BY_LINE = auto()  # 行単位処理
    CHUNK_BASED = auto()  # チャンク単位処理
    MEMORY_MAPPED = auto()  # メモリマップ処理
    BUFFERED = auto()  # バッファ処理
    ADAPTIVE = auto()  # 適応的処理


class BackpressureStrategy(Enum):
    """バックプレッシャー戦略"""

    DROP_OLDEST = auto()  # 最古のデータを破棄
    DROP_NEWEST = auto()  # 最新のデータを破棄
    BLOCK = auto()  # ブロック
    EXPAND_BUFFER = auto()  # バッファ拡張


@dataclass
class StreamMetrics:
    """ストリーム統計情報"""

    bytes_processed: int = 0
    items_processed: int = 0
    processing_time: float = 0.0
    memory_usage: int = 0  # バイト
    buffer_overflows: int = 0
    backpressure_events: int = 0
    error_count: int = 0
    throughput_bps: float = 0.0  # bytes per second
    throughput_ips: float = 0.0  # items per second


@dataclass
class StreamConfig:
    """ストリーム設定"""

    buffer_size: int = 8192  # バイト
    max_buffer_items: int = 1000
    chunk_size: int = 1024 * 1024  # 1MB
    memory_limit: int = 100 * 1024 * 1024  # 100MB
    backpressure_strategy: BackpressureStrategy = BackpressureStrategy.BLOCK
    enable_compression: bool = False
    enable_statistics: bool = True
    timeout_seconds: float = 30.0


class StreamProcessor(Protocol):
    """ストリーム処理プロトコル"""

    def process_item(self, item: T) -> Optional[R]:
        """単一アイテム処理"""
        ...

    def process_batch(self, items: List[T]) -> List[R]:
        """バッチ処理"""
        ...


class OptimizedStreamingProcessor:
    """
    最適化ストリーミングプロセッサー

    機能:
    - 大型ファイルのメモリ効率的処理
    - バックプレッシャー制御
    - 適応的バッファリング
    - 非同期ストリーミング処理
    """

    def __init__(self, config: Optional[StreamConfig] = None) -> None:
        """
        ストリーミングプロセッサーの初期化

        Args:
            config: ストリーム設定
        """
        self.logger = get_logger(__name__)
        self.config = config or StreamConfig()

        # 統計情報
        self.metrics = StreamMetrics()
        self._metrics_lock = threading.Lock()

        # バッファ管理
        self._buffer: Queue[Any] = Queue(maxsize=self.config.max_buffer_items)
        self._result_buffer: Queue[Any] = Queue(maxsize=self.config.max_buffer_items)

        # ストリーム状態
        self._streaming = False
        self._paused = False
        self._shutdown_requested = False

        # 同期プリミティブ
        self._stream_lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初期状態は実行可能

        self.logger.info(
            f"Streaming processor initialized: buffer_size={self.config.buffer_size}, "
            f"chunk_size={self.config.chunk_size}, memory_limit={self.config.memory_limit}"
        )

    def stream_file_lines(
        self,
        file_path: Path,
        processor: Callable[[str], Optional[R]],
        encoding: str = "utf-8",
    ) -> Iterator[R]:
        """
        ファイルを行単位でストリーミング処理

        Args:
            file_path: ファイルパス
            processor: 行処理関数
            encoding: ファイルエンコーディング

        Yields:
            R: 処理結果
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.logger.info(f"Starting line-by-line streaming: {file_path}")

        start_time = time.time()
        try:
            with open(
                file_path, "r", encoding=encoding, buffering=self.config.buffer_size
            ) as f:
                for line_no, line in enumerate(f, 1):
                    # 一時停止チェック
                    self._pause_event.wait()

                    # シャットダウンチェック
                    if self._shutdown_requested:
                        self.logger.info("Streaming interrupted by shutdown request")
                        break

                    # 行処理
                    try:
                        result = processor(line.rstrip("\n\r"))
                        if result is not None:
                            yield result

                        # 統計更新
                        self._update_metrics(len(line.encode(encoding)), 1)

                    except Exception as e:
                        self.logger.warning(f"Error processing line {line_no}: {e}")
                        self._update_metrics(0, 0, error=True)

        finally:
            processing_time = time.time() - start_time
            self.logger.info(
                f"Line streaming completed: {self.metrics.items_processed} lines "
                f"in {processing_time:.2f}s"
            )

    def stream_file_chunks(
        self,
        file_path: Path,
        processor: Callable[[str], Optional[R]],
        chunk_size: Optional[int] = None,
        overlap_size: int = 0,
        encoding: str = "utf-8",
    ) -> Iterator[R]:
        """
        ファイルをチャンク単位でストリーミング処理

        Args:
            file_path: ファイルパス
            processor: チャンク処理関数
            chunk_size: チャンクサイズ（バイト）
            overlap_size: オーバーラップサイズ（バイト）
            encoding: ファイルエンコーディング

        Yields:
            R: 処理結果
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        chunk_size = chunk_size or self.config.chunk_size
        self.logger.info(
            f"Starting chunk-based streaming: {file_path} "
            f"(chunk_size={chunk_size}, overlap={overlap_size})"
        )

        start_time = time.time()
        previous_overlap = ""

        try:
            with open(
                file_path, "r", encoding=encoding, buffering=self.config.buffer_size
            ) as f:
                chunk_no = 0
                while True:
                    # 一時停止チェック
                    self._pause_event.wait()

                    # シャットダウンチェック
                    if self._shutdown_requested:
                        break

                    # チャンク読み込み
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # オーバーラップ処理
                    full_chunk = previous_overlap + chunk
                    if overlap_size > 0 and len(chunk) == chunk_size:
                        previous_overlap = chunk[-overlap_size:]
                    else:
                        previous_overlap = ""

                    # チャンク処理
                    try:
                        result = processor(full_chunk)
                        if result is not None:
                            yield result

                        chunk_no += 1
                        self._update_metrics(len(full_chunk.encode(encoding)), 1)

                    except Exception as e:
                        self.logger.warning(f"Error processing chunk {chunk_no}: {e}")
                        self._update_metrics(0, 0, error=True)

        finally:
            processing_time = time.time() - start_time
            self.logger.info(
                f"Chunk streaming completed: {self.metrics.items_processed} chunks "
                f"in {processing_time:.2f}s"
            )

    def stream_memory_mapped(
        self,
        file_path: Path,
        processor: Callable[[str], Optional[R]],
        chunk_size: Optional[int] = None,
    ) -> Iterator[R]:
        """
        メモリマップファイルのストリーミング処理

        Args:
            file_path: ファイルパス
            processor: チャンク処理関数
            chunk_size: チャンクサイズ（バイト）

        Yields:
            R: 処理結果
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        chunk_size = chunk_size or self.config.chunk_size
        self.logger.info(f"Starting memory-mapped streaming: {file_path}")

        start_time = time.time()

        try:
            with open(file_path, "r+b") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    file_size = len(mm)
                    offset = 0
                    chunk_no = 0

                    while offset < file_size:
                        # 一時停止チェック
                        self._pause_event.wait()

                        # シャットダウンチェック
                        if self._shutdown_requested:
                            break

                        # チャンクサイズ調整
                        current_chunk_size = min(chunk_size, file_size - offset)

                        # メモリマップからチャンク取得
                        chunk_bytes = mm[offset : offset + current_chunk_size]
                        chunk_str = chunk_bytes.decode("utf-8", errors="ignore")

                        # チャンク処理
                        try:
                            result = processor(chunk_str)
                            if result is not None:
                                yield result

                            chunk_no += 1
                            offset += current_chunk_size
                            self._update_metrics(current_chunk_size, 1)

                        except Exception as e:
                            self.logger.warning(
                                f"Error processing mmap chunk {chunk_no}: {e}"
                            )
                            offset += current_chunk_size
                            self._update_metrics(0, 0, error=True)

        finally:
            processing_time = time.time() - start_time
            self.logger.info(
                f"Memory-mapped streaming completed: {self.metrics.items_processed} chunks "
                f"in {processing_time:.2f}s"
            )

    async def stream_async(
        self,
        data_source: AsyncIterator[T],
        processor: Callable[[T], Optional[R]],
        batch_size: int = 100,
    ) -> AsyncIterator[R]:
        """
        非同期ストリーミング処理

        Args:
            data_source: 非同期データソース
            processor: 処理関数
            batch_size: バッチサイズ

        Yields:
            R: 処理結果
        """
        self.logger.info("Starting async streaming processing")

        start_time = time.time()
        batch: List[T] = []

        try:
            async for item in data_source:
                # シャットダウンチェック
                if self._shutdown_requested:
                    break

                batch.append(item)

                # バッチ処理
                if len(batch) >= batch_size:
                    for result in await self._process_batch_async(batch, processor):
                        if result is not None:
                            yield result
                    batch.clear()

            # 残りのバッチ処理
            if batch:
                for result in await self._process_batch_async(batch, processor):
                    if result is not None:
                        yield result

        finally:
            processing_time = time.time() - start_time
            self.logger.info(
                f"Async streaming completed: {self.metrics.items_processed} items "
                f"in {processing_time:.2f}s"
            )

    async def _process_batch_async(
        self, batch: List[T], processor: Callable[[T], Optional[R]]
    ) -> List[R]:
        """バッチの非同期処理"""
        tasks = [
            asyncio.create_task(self._process_item_async(item, processor))
            for item in batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results: List[R] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"Async batch item {i} failed: {result}")
                self._update_metrics(0, 0, error=True)
            elif result is not None:
                # 型チェックをパスするために型キャストを使用
                valid_results.append(result)  # type: ignore[arg-type]
                self._update_metrics(0, 1)  # データサイズは不明のため0

        return valid_results

    async def _process_item_async(
        self, item: T, processor: Callable[[T], Optional[R]]
    ) -> Optional[R]:
        """単一アイテムの非同期処理"""
        loop = asyncio.get_event_loop()

        # CPUバウンドな処理を別スレッドで実行
        try:
            result = await loop.run_in_executor(None, processor, item)
            return result
        except Exception as e:
            self.logger.warning(f"Async item processing failed: {e}")
            raise

    def stream_with_backpressure(
        self,
        data_source: Iterator[T],
        processor: Callable[[T], Optional[R]],
        buffer_threshold: float = 0.8,  # バッファ使用率閾値
    ) -> Iterator[R]:
        """
        バックプレッシャー制御付きストリーミング処理

        Args:
            data_source: データソース
            processor: 処理関数
            buffer_threshold: バッファ使用率閾値

        Yields:
            R: 処理結果
        """
        self.logger.info("Starting backpressure-controlled streaming")

        start_time = time.time()

        try:
            for item in data_source:
                # シャットダウンチェック
                if self._shutdown_requested:
                    break

                # バックプレッシャーチェック
                buffer_usage = self._buffer.qsize() / self.config.max_buffer_items

                if buffer_usage > buffer_threshold:
                    self._handle_backpressure()

                # アイテム処理
                try:
                    result = processor(item)
                    if result is not None:
                        # 結果バッファに追加（ブロッキング）
                        try:
                            self._result_buffer.put(
                                result, timeout=self.config.timeout_seconds
                            )
                            yield result
                            self._update_metrics(0, 1)
                        except Exception:
                            # バッファフル時の処理
                            self._handle_backpressure()

                except Exception as e:
                    self.logger.warning(f"Error in backpressure streaming: {e}")
                    self._update_metrics(0, 0, error=True)

        finally:
            processing_time = time.time() - start_time
            self.logger.info(
                f"Backpressure streaming completed: {self.metrics.items_processed} items "
                f"in {processing_time:.2f}s, {self.metrics.backpressure_events} backpressure events"
            )

    def _handle_backpressure(self) -> None:
        """バックプレッシャー処理"""
        with self._metrics_lock:
            self.metrics.backpressure_events += 1

        strategy = self.config.backpressure_strategy

        if strategy == BackpressureStrategy.DROP_OLDEST:
            try:
                self._result_buffer.get_nowait()
            except Empty:
                pass

        elif strategy == BackpressureStrategy.DROP_NEWEST:
            # 新しいアイテムを破棄（何もしない）
            pass

        elif strategy == BackpressureStrategy.BLOCK:
            # 適度な待機
            time.sleep(0.01)

        elif strategy == BackpressureStrategy.EXPAND_BUFFER:
            # バッファサイズを動的に拡張
            self.config.max_buffer_items = min(
                self.config.max_buffer_items * 2, 10000  # 最大制限
            )
            self.logger.info(f"Buffer expanded to {self.config.max_buffer_items}")

    @contextmanager
    def streaming_context(self) -> Generator[None, None, None]:
        """ストリーミングコンテキストマネージャー"""
        self._streaming = True
        self.logger.info("Streaming context started")

        try:
            yield
        finally:
            self._streaming = False
            self.logger.info("Streaming context ended")

    def pause(self) -> None:
        """ストリーミングを一時停止"""
        self._paused = True
        self._pause_event.clear()
        self.logger.info("Streaming paused")

    def resume(self) -> None:
        """ストリーミングを再開"""
        self._paused = False
        self._pause_event.set()
        self.logger.info("Streaming resumed")

    def stop(self) -> None:
        """ストリーミングを停止"""
        self._shutdown_requested = True
        self._pause_event.set()  # 一時停止中なら解除
        self.logger.info("Streaming stop requested")

    def _update_metrics(
        self, bytes_delta: int, items_delta: int, error: bool = False
    ) -> None:
        """統計情報を更新"""
        with self._metrics_lock:
            self.metrics.bytes_processed += bytes_delta
            self.metrics.items_processed += items_delta

            if error:
                self.metrics.error_count += 1

            # スループット計算
            if self.metrics.processing_time > 0:
                self.metrics.throughput_bps = (
                    self.metrics.bytes_processed / self.metrics.processing_time
                )
                self.metrics.throughput_ips = (
                    self.metrics.items_processed / self.metrics.processing_time
                )

    def get_metrics(self) -> StreamMetrics:
        """
        ストリーミング統計情報を取得

        Returns:
            StreamMetrics: 統計情報
        """
        with self._metrics_lock:
            # 処理時間を更新
            current_time = time.time()
            if hasattr(self, "_start_time"):
                self.metrics.processing_time = current_time - self._start_time

            return StreamMetrics(
                bytes_processed=self.metrics.bytes_processed,
                items_processed=self.metrics.items_processed,
                processing_time=self.metrics.processing_time,
                memory_usage=self.metrics.memory_usage,
                buffer_overflows=self.metrics.buffer_overflows,
                backpressure_events=self.metrics.backpressure_events,
                error_count=self.metrics.error_count,
                throughput_bps=self.metrics.throughput_bps,
                throughput_ips=self.metrics.throughput_ips,
            )

    def reset_metrics(self) -> None:
        """統計情報をリセット"""
        with self._metrics_lock:
            self.metrics = StreamMetrics()
            self._start_time = time.time()
        self.logger.info("Metrics reset")

    def get_status(self) -> Dict[str, Any]:
        """
        ストリーミング状態を取得

        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            "streaming": self._streaming,
            "paused": self._paused,
            "shutdown_requested": self._shutdown_requested,
            "buffer_size": self._buffer.qsize(),
            "result_buffer_size": self._result_buffer.qsize(),
            "max_buffer_items": self.config.max_buffer_items,
            "buffer_usage_percent": (
                self._buffer.qsize() / self.config.max_buffer_items * 100
                if self.config.max_buffer_items > 0
                else 0
            ),
            "config": {
                "buffer_size": self.config.buffer_size,
                "chunk_size": self.config.chunk_size,
                "memory_limit": self.config.memory_limit,
                "backpressure_strategy": self.config.backpressure_strategy.name,
                "enable_compression": self.config.enable_compression,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }

    def __del__(self) -> None:
        """デストラクタでリソース解放"""
        try:
            self.stop()
        except Exception:
            pass  # デストラクタでの例外は無視
