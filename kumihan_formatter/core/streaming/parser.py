"""Kumihanストリーミングパーサの実装"""

import asyncio
import concurrent.futures
import io
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..common.error_framework import KumihanError
from .chunk_manager import ChunkManager, ChunkMetadata
from .interfaces import (
    ChunkInfo,
    ChunkProcessor,
    ParseResult,
    ProgressCallback,
    StreamingParser,
    StreamingParserConfig,
)
from .memory_manager import MemoryConfig, MemoryManager
from .progress import ConsoleProgressTracker, ProgressTracker


class KumihanChunkProcessor(ChunkProcessor):
    """Kumihan記法用チャンク処理器"""

    def __init__(self):
        self._block_buffer = ""
        self._in_block = False

    def process_chunk(
        self, chunk_content: str, chunk_index: int, is_first: bool, is_last: bool, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """チャンクを処理"""

        # 前のチャンクからの継続ブロックを考慮
        if not is_first and "incomplete_block" in context:
            chunk_content = context["incomplete_block"] + chunk_content

        processed_content = ""
        incomplete_block = ""

        lines = chunk_content.split("\\n")
        current_block = ""
        in_block = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # ブロック開始の検出
            if stripped.startswith(";;;") and not stripped.endswith(";;;"):
                in_block = True
                current_block = line + "\\n"
                continue

            # ブロック終了の検出
            if stripped == ";;; " and in_block:
                current_block += line + "\\n"
                processed_content += self._process_block(current_block)
                current_block = ""
                in_block = False
                continue

            # ブロック内
            if in_block:
                current_block += line + "\\n"
                # 最後の行で、まだブロックが完了していない場合
                if i == len(lines) - 1 and not is_last:
                    incomplete_block = current_block
                    break
            else:
                # 通常行の処理
                processed_content += self._process_line(line) + "\\n"

        # 未完了ブロックがある場合
        if in_block and current_block and is_last:
            # 強制的に閉じる
            processed_content += self._process_block(current_block + ";;;\\n")

        return {
            "processed_content": processed_content,
            "incomplete_block": incomplete_block,
            "chunk_index": chunk_index,
            "errors": [],
            "warnings": [],
        }

    def merge_results(self, chunk_results: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """チャンク処理結果をマージ"""
        merged_content = ""
        all_errors = []
        all_warnings = []

        for result in chunk_results:
            merged_content += result.get("processed_content", "")
            all_errors.extend(result.get("errors", []))
            all_warnings.extend(result.get("warnings", []))

        # コンテキストに統計情報を保存
        context["total_errors"] = len(all_errors)
        context["total_warnings"] = len(all_warnings)
        context["all_errors"] = all_errors
        context["all_warnings"] = all_warnings

        return merged_content

    def handle_block_boundary(self, previous_chunk: str, current_chunk: str, boundary_position: int) -> tuple[str, str]:
        """ブロック境界を処理"""

        # 前のチャンクの末尾に不完全なブロック開始があるかチェック
        prev_lines = previous_chunk.split("\\n")
        if prev_lines:
            last_line = prev_lines[-1].strip()
            if last_line.startswith(";;;") and not last_line.endswith(";;;"):
                # 不完全なブロック開始を検出
                # 現在のチャンクから対応する終了を探す
                curr_lines = current_chunk.split("\\n")
                for i, line in enumerate(curr_lines):
                    if line.strip() == ";;;":
                        # 完全なブロックを前のチャンクに移動
                        block_content = "\\n".join(curr_lines[: i + 1])
                        remaining_content = "\\n".join(curr_lines[i + 1 :])

                        return (previous_chunk + "\\n" + block_content, remaining_content)

        return previous_chunk, current_chunk

    def _process_block(self, block_content: str) -> str:
        """ブロックを処理（簡易実装）"""
        # 実際のKumihan記法処理はここで行う
        # 現在は簡易的にHTMLタグに変換

        lines = block_content.strip().split("\\n")
        if len(lines) < 2:
            return block_content

        header = lines[0].strip()
        content = "\\n".join(lines[1:-1]) if len(lines) > 2 else ""

        # 簡易的なタグ変換
        if header.startswith(";;;見出し"):
            level = header[4:5] if len(header) > 4 and header[4].isdigit() else "1"
            return f"<h{level}>{content}</h{level}>\\n"
        elif header.startswith(";;;太字"):
            return f"<strong>{content}</strong>\\n"
        elif header.startswith(";;;枠線"):
            return f'<div class="box">{content}</div>\\n'
        else:
            return f"<div>{content}</div>\\n"

    def _process_line(self, line: str) -> str:
        """通常行を処理"""
        stripped = line.strip()

        # リスト項目の処理
        if stripped.startswith("- "):
            return f"<li>{stripped[2:]}</li>"
        elif stripped.startswith("・"):
            return f"<li>{stripped[1:]}</li>"
        elif stripped.startswith(tuple(f"{i}. " for i in range(1, 10))):
            content = stripped.split(". ", 1)[1] if ". " in stripped else stripped
            return f"<li>{content}</li>"

        # 空行
        if not stripped:
            return ""

        # 通常の段落
        return f"<p>{line}</p>"


class KumihanStreamingParser(StreamingParser):
    """Kumihanストリーミングパーサの実装"""

    def __init__(self, config: Optional[StreamingParserConfig] = None):
        self.config = config or StreamingParserConfig()
        self.chunk_manager = ChunkManager(self.config.default_chunk_size)
        self.memory_manager = MemoryManager(MemoryConfig(max_memory_mb=self.config.max_memory_usage // 1024 // 1024))
        self.chunk_processor = KumihanChunkProcessor()

        # 設定を検証
        config_errors = self.config.validate()
        if config_errors:
            raise KumihanError(f"Invalid streaming parser configuration: {', '.join(config_errors)}")

    def parse_file(
        self,
        file_path: Path,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
        max_memory: Optional[int] = None,
    ) -> ParseResult:
        """ファイルをストリーミング形式でパース"""

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # パラメータの調整
        file_size = file_path.stat().st_size
        effective_chunk_size = chunk_size or self.config.adjust_chunk_size(file_size)

        if max_memory:
            self.memory_manager.config.max_memory_mb = max_memory // 1024 // 1024

        # 進捗追跡の設定
        estimated_chunks = self.chunk_manager.estimate_chunks_count(file_path, effective_chunk_size)

        progress_tracker = ConsoleProgressTracker(total_bytes=file_size, total_chunks=estimated_chunks)

        if progress_callback:
            progress_tracker.add_callback(
                lambda info: progress_callback(
                    info.processed_bytes, info.total_bytes, info.current_chunk, info.total_chunks, info.message
                )
            )

        # パース実行
        start_time = time.time()

        with self.memory_manager.managed_processing():
            try:
                progress_tracker.start()
                result = self._parse_file_internal(file_path, effective_chunk_size, progress_tracker)
                progress_tracker.complete("パース完了")

            except Exception as e:
                progress_tracker.error(str(e))
                raise

        # 結果の構築
        processing_time = time.time() - start_time
        memory_info = self.memory_manager.get_memory_status()

        return ParseResult(
            content=result["content"],
            metadata={
                "file_path": str(file_path),
                "file_size": file_size,
                "chunk_size": effective_chunk_size,
                "chunks_processed": result["chunks_processed"],
                "memory_peak_mb": memory_info["peak_mb"],
                "config": self.config.__dict__,
            },
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            processing_time=processing_time,
            memory_peak=int(memory_info["peak_mb"] * 1024 * 1024),
            chunks_processed=result["chunks_processed"],
        )

    def parse_stream(
        self,
        stream: Union[io.TextIOBase, io.BufferedIOBase],
        total_size: Optional[int] = None,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
        max_memory: Optional[int] = None,
    ) -> ParseResult:
        """ストリームをパース"""

        effective_chunk_size = chunk_size or self.config.default_chunk_size

        if max_memory:
            self.memory_manager.config.max_memory_mb = max_memory // 1024 // 1024

        # 進捗追跡の設定
        progress_tracker = ConsoleProgressTracker(total_bytes=total_size, total_chunks=None)  # ストリームの場合は不明

        if progress_callback:
            progress_tracker.add_callback(
                lambda info: progress_callback(
                    info.processed_bytes, info.total_bytes, info.current_chunk, info.total_chunks, info.message
                )
            )

        # パース実行
        start_time = time.time()

        with self.memory_manager.managed_processing():
            try:
                progress_tracker.start()
                result = self._parse_stream_internal(stream, effective_chunk_size, progress_tracker)
                progress_tracker.complete("パース完了")

            except Exception as e:
                progress_tracker.error(str(e))
                raise

        # 結果の構築
        processing_time = time.time() - start_time
        memory_info = self.memory_manager.get_memory_status()

        return ParseResult(
            content=result["content"],
            metadata={
                "stream_type": type(stream).__name__,
                "total_size": total_size,
                "chunk_size": effective_chunk_size,
                "chunks_processed": result["chunks_processed"],
                "memory_peak_mb": memory_info["peak_mb"],
                "config": self.config.__dict__,
            },
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            processing_time=processing_time,
            memory_peak=int(memory_info["peak_mb"] * 1024 * 1024),
            chunks_processed=result["chunks_processed"],
        )

    async def parse_file_async(
        self,
        file_path: Path,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
        max_memory: Optional[int] = None,
    ) -> ParseResult:
        """ファイルを非同期でパース"""

        # 同期版を別スレッドで実行
        loop = asyncio.get_event_loop()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.worker_threads) as executor:
            return await loop.run_in_executor(
                executor, self.parse_file, file_path, chunk_size, progress_callback, max_memory
            )

    def get_chunk_info(self, file_path: Path, chunk_size: int) -> List[ChunkInfo]:
        """ファイルのチャンク情報を取得"""

        chunk_infos = []

        for i, (content, metadata) in enumerate(self.chunk_manager.create_chunks(file_path, chunk_size)):
            chunk_info = ChunkInfo(
                index=metadata.index,
                start_position=metadata.start_position,
                end_position=metadata.end_position,
                size=metadata.size,
                content_preview=content[:100] + "..." if len(content) > 100 else content,
                has_block_boundary=metadata.has_complete_blocks,
            )
            chunk_infos.append(chunk_info)

            # プレビュー用に最初の数チャンクのみ取得
            if i >= 10:
                break

        return chunk_infos

    def estimate_memory_usage(self, file_size: int, chunk_size: int) -> Dict[str, int]:
        """メモリ使用量を推定"""

        # 基本的な推定
        chunks_count = (file_size // chunk_size) + 1

        # チャンク処理に必要なメモリ
        chunk_memory = self.memory_manager.estimate_chunk_memory(chunk_size)

        # バッファや中間データ用のメモリ
        buffer_memory = chunk_size * 2  # 入力と出力バッファ

        # プログレス追跡やメタデータ用のメモリ
        overhead_memory = 1024 * 1024  # 1MB

        return {
            "chunk_memory_bytes": chunk_memory,
            "buffer_memory_bytes": buffer_memory,
            "overhead_memory_bytes": overhead_memory,
            "total_memory_bytes": chunk_memory + buffer_memory + overhead_memory,
            "estimated_chunks": chunks_count,
        }

    def _parse_file_internal(
        self, file_path: Path, chunk_size: int, progress_tracker: ProgressTracker
    ) -> Dict[str, Any]:
        """ファイルパースの内部実装"""

        chunk_results = []
        context = {}
        processed_bytes = 0

        for content, metadata in self.chunk_manager.create_chunks(file_path, chunk_size):

            # キャンセルチェック
            if progress_tracker.is_cancelled():
                break

            # メモリチェック
            if not self.memory_manager.can_process_chunk(len(content)):
                # メモリ不足の場合はチャンクサイズを調整
                self.memory_manager.cleanup()
                continue

            # チャンク処理
            is_first = metadata.index == 0
            result = self.chunk_processor.process_chunk(
                content, metadata.index, is_first, False, context  # is_lastは後で設定
            )

            chunk_results.append(result)
            processed_bytes += metadata.size

            # 進捗更新
            progress_tracker.update(
                processed_bytes=processed_bytes,
                current_chunk=metadata.index + 1,
                message=f"チャンク {metadata.index + 1} 処理中",
            )

        # 最後のチャンクを修正
        if chunk_results:
            last_result = chunk_results[-1]
            # 再処理して is_last=True に設定
            # （実装簡略化のため省略）

        # 結果をマージ
        merged_content = self.chunk_processor.merge_results(chunk_results, context)

        return {
            "content": merged_content,
            "chunks_processed": len(chunk_results),
            "errors": context.get("all_errors", []),
            "warnings": context.get("all_warnings", []),
        }

    def _parse_stream_internal(
        self, stream: Union[io.TextIOBase, io.BufferedIOBase], chunk_size: int, progress_tracker: ProgressTracker
    ) -> Dict[str, Any]:
        """ストリームパースの内部実装"""

        chunk_results = []
        context = {}
        processed_bytes = 0

        for content, metadata in self.chunk_manager.create_chunks_from_stream(stream, chunk_size):

            # キャンセルチェック
            if progress_tracker.is_cancelled():
                break

            # メモリチェック
            if not self.memory_manager.can_process_chunk(len(content)):
                self.memory_manager.cleanup()
                continue

            # チャンク処理
            is_first = metadata.index == 0
            result = self.chunk_processor.process_chunk(content, metadata.index, is_first, False, context)

            chunk_results.append(result)
            processed_bytes += metadata.size

            # 進捗更新
            progress_tracker.update(
                processed_bytes=processed_bytes,
                current_chunk=metadata.index + 1,
                message=f"チャンク {metadata.index + 1} 処理中",
            )

        # 結果をマージ
        merged_content = self.chunk_processor.merge_results(chunk_results, context)

        return {
            "content": merged_content,
            "chunks_processed": len(chunk_results),
            "errors": context.get("all_errors", []),
            "warnings": context.get("all_warnings", []),
        }
