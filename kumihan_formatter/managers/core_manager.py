from typing import Any, Dict, List, Optional, Union

"""
CoreManager - コア機能統合管理クラス
ResourceManager + ChunkManager の機能を統合
"""

import logging
import os
from pathlib import Path

from kumihan_formatter.core.io.operations import FileOperations, PathOperations
from kumihan_formatter.core.templates.template_context import TemplateContext
from kumihan_formatter.core.templates.template_selector import TemplateSelector
from kumihan_formatter.core.types import ChunkInfo


class CoreManager:
    """コア機能統合管理クラス - IO・キャッシュ・チャンク管理の統合API"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        CoreManager初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 既存コンポーネント初期化
        self.file_ops = FileOperations()
        self.path_ops = PathOperations()
        self.template_context = TemplateContext()
        self.template_selector = TemplateSelector()

        # リソース管理設定
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.template_dir = Path(
            self.config.get("template_dir", "kumihan_formatter/templates")
        )
        self.assets_dir = Path(
            self.config.get("assets_dir", "kumihan_formatter/assets")
        )

        # チャンク管理設定
        self.chunk_size = self.config.get("chunk_size", 1000)

        # シンプルなキャッシュ
        self._file_cache: Dict[str, str] = {}
        self._template_cache: Dict[str, str] = {}

    # ========== ファイルIO機能（旧ResourceManager） ==========

    def read_file(
        self, file_path: Union[str, Path], use_cache: bool = True
    ) -> Optional[str]:
        """
        ファイル読み込み（キャッシュ対応）

        Args:
            file_path: 読み込み対象ファイルパス
            use_cache: キャッシュ使用フラグ

        Returns:
            ファイル内容、エラー時はNone
        """
        try:
            path_str = str(file_path)

            # キャッシュチェック
            if use_cache and self.cache_enabled and path_str in self._file_cache:
                return self._file_cache[path_str]

            # ファイル読み込み
            content = self.file_ops.read_text(Path(file_path))

            # キャッシュ保存
            if use_cache and self.cache_enabled:
                self._file_cache[path_str] = content

            return content

        except Exception as e:
            self.logger.error(f"ファイル読み込み中にエラー: {file_path}, {e}")
            return None

    def write_file(
        self, file_path: Union[str, Path], content: str, ensure_dir: bool = True
    ) -> bool:
        """
        ファイル書き込み

        Args:
            file_path: 書き込み先ファイルパス
            content: 書き込み内容
            ensure_dir: ディレクトリ自動作成フラグ

        Returns:
            成功時True、失敗時False
        """
        try:
            path_obj = Path(file_path)

            # ディレクトリ作成
            if ensure_dir:
                path_obj.parent.mkdir(parents=True, exist_ok=True)

            # ファイル書き込み
            self.file_ops.write_text(Path(file_path), content)
            success = True

            # キャッシュ更新
            if success and self.cache_enabled:
                self._file_cache[str(file_path)] = content

            return success

        except Exception as e:
            self.logger.error(f"ファイル書き込み中にエラー: {file_path}, {e}")
            return False

    # ========== テンプレート機能 ==========

    def load_template(
        self, template_name: str, use_cache: bool = True
    ) -> Optional[str]:
        """
        テンプレート読み込み

        Args:
            template_name: テンプレート名
            use_cache: キャッシュ使用フラグ

        Returns:
            テンプレート内容、エラー時はNone
        """
        try:
            # キャッシュチェック
            if (
                use_cache
                and self.cache_enabled
                and template_name in self._template_cache
            ):
                return self._template_cache[template_name]

            # テンプレートファイルパス生成
            template_path = self.template_dir / template_name

            # テンプレート読み込み
            content = self.read_file(template_path, use_cache=False)

            # キャッシュ保存
            if content and use_cache and self.cache_enabled:
                self._template_cache[template_name] = content

            return content

        except Exception as e:
            self.logger.error(f"テンプレート読み込み中にエラー: {template_name}, {e}")
            return None

    def get_template_context(
        self, context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        テンプレートコンテキスト生成

        Args:
            context_data: 追加コンテキストデータ

        Returns:
            テンプレートコンテキスト辞書
        """
        try:
            base_context = self.template_context.get_context()
            user_context = context_data or {}

            # コンテキスト統合
            merged_context = {**base_context, **user_context}

            return merged_context

        except Exception as e:
            self.logger.error(f"テンプレートコンテキスト生成中にエラー: {e}")
            return context_data or {}

    # ========== チャンク管理機能（旧ChunkManager） ==========

    def create_chunks_from_lines(
        self, lines: List[str], chunk_size: Optional[int] = None
    ) -> List[ChunkInfo]:
        """行リストからチャンク作成"""
        if chunk_size is None:
            chunk_size = self.chunk_size

        chunks: List[ChunkInfo] = []
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
        self, lines: List[str], target_chunk_count: Optional[int] = None
    ) -> List[ChunkInfo]:
        """適応的チャンク作成（処理量に応じてサイズ調整）"""
        total_lines = len(lines)
        if total_lines == 0:
            return []

        # チャンクサイズの決定
        cpu_count = self._get_cpu_count()
        if target_chunk_count is None:
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
        """
        try:
            self.logger.info(f"Creating chunks from file: {file_path}")

            # ファイル全体を読み込み
            with open(file_path, "r", encoding=encoding) as file:
                lines = file.readlines()

            # 行末の改行コードを除去
            lines = [line.rstrip("\n\r") for line in lines]

            # 適応的チャンク作成
            chunks = self.create_chunks_adaptive(lines)

            # ファイル位置情報を更新
            for chunk in chunks:
                chunk.file_position = chunk.start_line - 1

            self.logger.info(
                f"File chunking completed: {len(chunks)} chunks "
                f"from {len(lines)} lines in {file_path.name}"
            )

            return chunks

        except Exception as e:
            self.logger.error(f"Error creating chunks from file {file_path}: {e}")
            raise

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

    def ensure_directory(self, directory_path: Union[str, Path]) -> None:
        """ディレクトリを作成（FileManager機能統合）"""

        path = Path(directory_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory ensured: {path}")
        except Exception as e:
            self.logger.error(f"Failed to ensure directory {path}: {e}")
            raise

    # ========== ユーティリティ機能 ==========

    def ensure_output_directory(self, output_path: Union[str, Path]) -> bool:
        """
        出力ディレクトリの確保

        Args:
            output_path: 出力パス

        Returns:
            成功時True、失敗時False
        """
        try:
            path_obj = Path(output_path)

            # tmpディレクトリ配下への強制（CLAUDE.md準拠）
            if not str(path_obj).startswith("tmp/"):
                path_obj = Path("tmp") / path_obj

            path_obj.mkdir(parents=True, exist_ok=True)
            return True

        except Exception as e:
            self.logger.error(f"ディレクトリ作成中にエラー: {output_path}, {e}")
            return False

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._file_cache.clear()
        self._template_cache.clear()
        self.logger.debug("リソースキャッシュをクリアしました")

    def get_core_statistics(self) -> Dict[str, Any]:
        """コア統計情報を取得"""
        return {
            "file_cache_size": len(self._file_cache),
            "template_cache_size": len(self._template_cache),
            "cache_enabled": self.cache_enabled,
            "template_dir": str(self.template_dir),
            "assets_dir": str(self.assets_dir),
            "chunk_size": self.chunk_size,
        }

    def _get_cpu_count(self) -> int:
        """CPU数取得（フォールバック付き）"""
        try:
            return os.cpu_count() or 1
        except Exception:
            return 1
