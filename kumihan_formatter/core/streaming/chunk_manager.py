"""チャンク管理機能"""

import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


@dataclass
class ChunkMetadata:
    """チャンクのメタデータ"""

    index: int
    start_position: int
    end_position: int
    size: int
    has_complete_blocks: bool
    incomplete_block_start: Optional[int] = None
    incomplete_block_end: Optional[int] = None
    line_start: int = 0
    line_end: int = 0


class ChunkManager:
    """チャンク管理クラス"""

    def __init__(self, chunk_size: int = 1024 * 1024):
        self.chunk_size = chunk_size
        self._block_pattern = re.compile(r";;;[^;]*?;;;", re.MULTILINE | re.DOTALL)

    def create_chunks(self, file_path: Path, chunk_size: Optional[int] = None) -> Iterator[Tuple[str, ChunkMetadata]]:
        """ファイルからチャンクを作成"""
        chunk_size = chunk_size or self.chunk_size

        with open(file_path, "r", encoding="utf-8") as f:
            yield from self._create_chunks_from_stream(f, chunk_size)

    def create_chunks_from_stream(
        self, stream: io.TextIOBase, chunk_size: Optional[int] = None
    ) -> Iterator[Tuple[str, ChunkMetadata]]:
        """ストリームからチャンクを作成"""
        chunk_size = chunk_size or self.chunk_size
        yield from self._create_chunks_from_stream(stream, chunk_size)

    def _create_chunks_from_stream(self, stream: io.TextIOBase, chunk_size: int) -> Iterator[Tuple[str, ChunkMetadata]]:
        """ストリームからチャンクを作成（内部実装）"""
        buffer = ""
        chunk_index = 0
        total_position = 0
        line_number = 1

        while True:
            # データを読み込み
            data = stream.read(chunk_size)
            if not data:
                # 最後のチャンクを処理
                if buffer:
                    metadata = ChunkMetadata(
                        index=chunk_index,
                        start_position=total_position - len(buffer),
                        end_position=total_position,
                        size=len(buffer),
                        has_complete_blocks=True,
                        line_start=line_number,
                        line_end=line_number + buffer.count("\\n"),
                    )
                    yield buffer, metadata
                break

            buffer += data

            # ブロック境界でチャンクを分割
            chunk_content, remaining_buffer = self._split_at_block_boundary(buffer, chunk_size)

            if chunk_content:
                chunk_lines = chunk_content.count("\\n")
                metadata = ChunkMetadata(
                    index=chunk_index,
                    start_position=total_position - len(buffer),
                    end_position=total_position - len(remaining_buffer),
                    size=len(chunk_content),
                    has_complete_blocks=self._has_complete_blocks(chunk_content),
                    incomplete_block_start=self._find_incomplete_block_start(chunk_content),
                    incomplete_block_end=self._find_incomplete_block_end(chunk_content),
                    line_start=line_number,
                    line_end=line_number + chunk_lines,
                )

                yield chunk_content, metadata

                chunk_index += 1
                line_number += chunk_lines
                total_position += len(chunk_content)
                buffer = remaining_buffer

    def _split_at_block_boundary(self, content: str, max_size: int) -> Tuple[str, str]:
        """ブロック境界でコンテンツを分割"""
        if len(content) <= max_size:
            return content, ""

        # まず基本サイズで分割
        base_chunk = content[:max_size]
        remaining = content[max_size:]

        # ブロック境界を探す
        split_pos = self._find_safe_split_position(base_chunk, remaining)

        if split_pos is not None:
            return content[:split_pos], content[split_pos:]

        # 安全な分割位置が見つからない場合は行境界で分割
        split_pos = self._find_line_boundary(base_chunk)
        if split_pos is not None:
            return content[:split_pos], content[split_pos:]

        # 最悪の場合は強制分割
        return base_chunk, remaining

    def _find_safe_split_position(self, base_chunk: str, remaining: str) -> Optional[int]:
        """安全な分割位置を探す"""
        # ;;;マーカーのブロック境界を探す

        # base_chunk内で終了している完全なブロックを探す
        blocks = list(self._block_pattern.finditer(base_chunk))
        if blocks:
            # 最後の完全なブロックの終端を使用
            last_block = blocks[-1]
            return last_block.end()

        # ブロック境界が見つからない場合は段落境界を探す
        # 空行（2つ以上の連続する改行）で分割
        paragraph_boundaries = []
        for match in re.finditer(r"\\n\\s*\\n", base_chunk):
            paragraph_boundaries.append(match.end())

        if paragraph_boundaries:
            return paragraph_boundaries[-1]

        return None

    def _find_line_boundary(self, content: str) -> Optional[int]:
        """行境界を探す"""
        last_newline = content.rfind("\\n")
        if last_newline != -1:
            return last_newline + 1
        return None

    def _has_complete_blocks(self, content: str) -> bool:
        """完全なブロックを含むかチェック"""
        return bool(self._block_pattern.search(content))

    def _find_incomplete_block_start(self, content: str) -> Optional[int]:
        """不完全なブロックの開始位置を探す"""
        # ;;;で始まるが対応する終了;;;がない場合
        start_markers = []
        for match in re.finditer(r";;;[^;\\n]*$", content, re.MULTILINE):
            start_markers.append(match.start())

        if start_markers:
            return start_markers[-1]
        return None

    def _find_incomplete_block_end(self, content: str) -> Optional[int]:
        """不完全なブロックの終了位置を探す"""
        # 行頭の;;;のみ（開始マーカーなし）
        if content.strip().startswith(";;;") and not content.strip().endswith(";;;"):
            end_match = re.search(r"^;;;\\s*$", content, re.MULTILINE)
            if end_match:
                return end_match.start()
        return None

    def merge_incomplete_blocks(
        self, previous_chunk: str, current_chunk: str, previous_metadata: ChunkMetadata, current_metadata: ChunkMetadata
    ) -> Tuple[str, str]:
        """不完全なブロックをマージ"""

        # 前のチャンクに不完全な終了がある場合
        if previous_metadata.incomplete_block_start is not None and current_metadata.incomplete_block_end is not None:

            # 前のチャンクの不完全な部分を取得
            incomplete_start = previous_metadata.incomplete_block_start
            incomplete_part = previous_chunk[incomplete_start:]

            # 現在のチャンクの完了部分を取得
            completion_end = current_metadata.incomplete_block_end
            completion_part = current_chunk[:completion_end]

            # マージして完全なブロックを作成
            complete_block = incomplete_part + completion_part

            # チャンクを再構成
            new_previous = previous_chunk[:incomplete_start] + complete_block
            new_current = current_chunk[completion_end:]

            return new_previous, new_current

        return previous_chunk, current_chunk

    def estimate_chunks_count(self, file_path: Path, chunk_size: int) -> int:
        """ファイルのチャンク数を推定"""
        file_size = file_path.stat().st_size
        # テキストファイルの場合、バイト数とほぼ同じ文字数と仮定
        estimated_chunks = (file_size // chunk_size) + 1
        return estimated_chunks

    def get_chunk_preview(self, file_path: Path, chunk_index: int, chunk_size: Optional[int] = None) -> Optional[str]:
        """指定されたチャンクのプレビューを取得"""
        chunk_size = chunk_size or self.chunk_size

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # 指定されたチャンクまでスキップ
                for i, (content, metadata) in enumerate(self._create_chunks_from_stream(f, chunk_size)):
                    if i == chunk_index:
                        # プレビュー用に先頭部分のみ返す
                        preview_length = min(200, len(content))
                        return content[:preview_length]

        except Exception:
            pass

        return None
