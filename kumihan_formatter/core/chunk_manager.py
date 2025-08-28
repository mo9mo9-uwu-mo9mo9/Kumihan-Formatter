"""
チャンク管理機能
processor_core.py分割版 - チャンク作成・管理専用モジュール
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ChunkInfo:
    """処理チャンク情報"""

    chunk_id: int
    start_line: int
    end_line: int
    lines: List[str]
    file_position: int = 0


class ChunkManager:
    """チャンク管理クラス"""

    def __init__(self, chunk_size: int = 1000):
        """チャンク管理初期化"""
        self.logger = logging.getLogger(__name__)
        self.chunk_size = chunk_size

    def create_chunks_from_lines(
        self, lines: List[str], chunk_size: int = None
    ) -> List[ChunkInfo]:
        """行リストからチャンク作成"""
        if chunk_size is None:
            chunk_size = self.chunk_size

        chunks = []
        total_lines = len(lines)

        for i in range(0, total_lines, chunk_size):
            end_index = min(i + chunk_size, total_lines)
            chunk_lines = lines[i:end_index]

            chunk = ChunkInfo(
                chunk_id=len(chunks),
                start_line=i + 1,  # 1-based line numbering
                end_line=end_index,
                lines=chunk_lines,
                file_position=i,
            )
            chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} chunks from {total_lines} lines")
        return chunks

    def create_chunks_adaptive(
        self, lines: List[str], target_chunk_count: int = None
    ) -> List[ChunkInfo]:
        """
        適応的チャンク作成（処理量に応じてサイズ調整）

        Args:
            lines: 対象行リスト
            target_chunk_count: 目標チャンク数（Noneなら自動計算）

        Returns:
            List[ChunkInfo]: 最適化されたチャンクリスト
        """

        total_lines = len(lines)
        if total_lines == 0:
            return []

        # チャンクサイズの決定
        cpu_count = self._get_cpu_count()
        if total_lines <= 100:
            target_chunk_count = 1
        elif total_lines <= 1000:
            target_chunk_count = min(4, cpu_count)
        else:
            target_chunk_count = min(cpu_count * 2, 16)  # 最大16チャンク

        # 適応的チャンクサイズ計算
        adaptive_chunk_size = max(1, total_lines // target_chunk_count)

        self.logger.info(
            f"Adaptive chunking: {total_lines} lines → {target_chunk_count} chunks "
            f"(size: ~{adaptive_chunk_size})"
        )

        return self.create_chunks_from_lines(lines, adaptive_chunk_size)

    def create_chunks_from_file(
        self, file_path: Path, encoding: str = "utf-8"
    ) -> List[ChunkInfo]:
        """
        ファイルからチャンク作成（メモリ効率版）

        Args:
            file_path: 対象ファイルパス
            encoding: ファイルエンコーディング

        Returns:
            List[ChunkInfo]: 作成されたチャンクリスト
        """
        try:
            self.logger.info(f"Creating chunks from file: {file_path}")

            # ファイル全体を読み込み（メモリ効率化は後で対応）
            with open(file_path, "r", encoding=encoding) as file:
                lines = file.readlines()

            # 行末の改行コードを除去
            lines = [line.rstrip("\n\r") for line in lines]

            # 適応的チャンク作成
            chunks = self.create_chunks_adaptive(lines)

            # ファイル位置情報を更新
            for chunk in chunks:
                chunk.file_position = (
                    chunk.start_line - 1
                )  # 0-based for file operations

            self.logger.info(
                f"File chunking completed: {len(chunks)} chunks "
                f"from {len(lines)} lines in {file_path.name}"
            )

            return chunks

        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error reading {file_path}: {e}")
            raise
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating chunks from file {file_path}: {e}")
            raise

    def merge_chunks(self, chunks: List[ChunkInfo]) -> List[str]:
        """チャンクリストを行リストにマージ"""
        merged_lines = []

        for chunk in sorted(chunks, key=lambda c: c.chunk_id):
            merged_lines.extend(chunk.lines)

        self.logger.info(f"Merged {len(chunks)} chunks into {len(merged_lines)} lines")
        return merged_lines

    def get_chunk_info(self, chunks: List[ChunkInfo]) -> dict:
        """チャンク情報統計取得"""
        if not chunks:
            return {"total_chunks": 0, "total_lines": 0, "avg_chunk_size": 0}

        total_lines = sum(len(chunk.lines) for chunk in chunks)
        avg_chunk_size = total_lines / len(chunks)

        return {
            "total_chunks": len(chunks),
            "total_lines": total_lines,
            "avg_chunk_size": avg_chunk_size,
            "min_chunk_size": min(len(chunk.lines) for chunk in chunks),
            "max_chunk_size": max(len(chunk.lines) for chunk in chunks),
        }

    def validate_chunks(self, chunks: List[ChunkInfo]) -> List[str]:
        """チャンク整合性検証"""
        errors = []

        # チャンクID重複チェック
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        if len(chunk_ids) != len(set(chunk_ids)):
            errors.append("Duplicate chunk IDs detected")

        # 行番号連続性チェック
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_id)
        for i, chunk in enumerate(sorted_chunks):
            if i > 0 and chunk.start_line != sorted_chunks[i - 1].end_line + 1:
                errors.append(
                    f"Line number gap between chunk {sorted_chunks[i-1].chunk_id} and {chunk.chunk_id}"
                )

        # 空チャンクチェック
        empty_chunks = [chunk.chunk_id for chunk in chunks if not chunk.lines]
        if empty_chunks:
            errors.append(f"Empty chunks detected: {empty_chunks}")

        return errors

    def _get_cpu_count(self) -> int:
        """CPU数取得（フォールバック付き）"""
        try:
            return os.cpu_count() or 1
        except Exception:
            return 1
