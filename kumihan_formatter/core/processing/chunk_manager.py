"""チャンク管理モジュール

Issue #1217対応: ディレクトリ構造最適化によるチャンク管理機能
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from kumihan_formatter.core.utilities.logger import get_logger
from ..types import ChunkInfo


class ChunkManager:
    """チャンク管理クラス - 軽量版"""

    def __init__(self, chunk_size: int = 1000):
        """
        ChunkManager初期化

        Args:
            chunk_size: デフォルトチャンクサイズ
        """
        self.logger = get_logger(__name__)
        self.chunk_size = chunk_size

    def create_chunks_from_lines(
        self, lines: List[str], chunk_size: Optional[int] = None
    ) -> List[ChunkInfo]:
        """行リストからチャンクを作成"""
        chunk_size = chunk_size or self.chunk_size
        chunks: List[ChunkInfo] = []

        for i in range(0, len(lines), chunk_size):
            end_idx = min(i + chunk_size, len(lines))
            chunk = ChunkInfo(
                chunk_id=len(chunks),
                start_line=i,
                end_line=end_idx,
                lines=lines[i:end_idx],
                file_position=i,
            )
            chunks.append(chunk)

        self.logger.debug(f"Created {len(chunks)} chunks from {len(lines)} lines")
        return chunks

    def create_chunks_adaptive(
        self, lines: List[str], target_chunk_count: int
    ) -> List[ChunkInfo]:
        """適応的チャンク作成"""
        if target_chunk_count <= 0:
            target_chunk_count = 1

        chunk_size = max(1, len(lines) // target_chunk_count)
        return self.create_chunks_from_lines(lines, chunk_size)

    def create_chunks_from_file(
        self, file_path: Path, encoding: str = "utf-8"
    ) -> List[ChunkInfo]:
        """ファイルからチャンクを作成"""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = f.readlines()
            return self.create_chunks_from_lines(lines)
        except Exception as e:
            self.logger.error(f"Failed to create chunks from file {file_path}: {e}")
            return []

    def merge_chunks(self, chunks: List[ChunkInfo]) -> ChunkInfo:
        """チャンクをマージ"""
        if not chunks:
            return ChunkInfo(0, 0, 0, [], 0)

        all_lines = []
        for chunk in chunks:
            all_lines.extend(chunk.lines)

        return ChunkInfo(
            chunk_id=0,
            start_line=chunks[0].start_line,
            end_line=chunks[-1].end_line,
            lines=all_lines,
            file_position=chunks[0].file_position,
        )

    def get_chunk_info(self, chunks: List[ChunkInfo]) -> Dict[str, Any]:
        """チャンク情報を取得"""
        return {
            "chunk_count": len(chunks),
            "total_lines": sum(len(chunk.lines) for chunk in chunks),
            "chunk_sizes": [len(chunk.lines) for chunk in chunks],
        }

    def validate_chunks(self, chunks: List[ChunkInfo]) -> bool:
        """チャンクを検証"""
        if not chunks:
            return True

        # 基本的な検証
        for i, chunk in enumerate(chunks):
            if chunk.chunk_id != i:
                self.logger.warning(
                    f"Chunk ID mismatch: expected {i}, got {chunk.chunk_id}"
                )
                return False
            if chunk.start_line >= chunk.end_line:
                self.logger.warning(
                    f"Invalid chunk range: {chunk.start_line} >= {chunk.end_line}"
                )
                return False

        return True

    def _get_cpu_count(self) -> int:
        """CPU数を取得"""
        return os.cpu_count() or 1
