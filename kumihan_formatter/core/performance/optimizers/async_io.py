"""
非同期I/O最適化システム
Issue #813対応 - performance_metrics.pyから分離
"""

from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

from ...utilities.logger import get_logger


class AsyncIOOptimizer:
    """
    非同期I/O最適化システム

    特徴:
    - aiofilesによる非同期ファイル読み込み
    - 並列ファイル処理
    - プリフェッチとバッファリング
    - 大容量ファイルのストリーミング読み込み
    """

    def __init__(self, buffer_size: int = 64 * 1024):
        self.logger = get_logger(__name__)
        self.buffer_size = buffer_size
        self._aiofiles_available = self._check_aiofiles_availability()

        if self._aiofiles_available:
            self.logger.info(
                f"AsyncIO optimizer initialized with buffer size: {buffer_size}"
            )
        else:
            self.logger.warning("aiofiles not available, using synchronous I/O")

    def _check_aiofiles_availability(self) -> bool:
        """aiofiles利用可能性をチェック"""
        try:
            import aiofiles  # noqa: F401

            return True
        except ImportError:
            return False

    async def async_read_file_chunked(
        self, file_path: Path, chunk_size: int = 64 * 1024
    ) -> AsyncIterator[str]:
        """
        非同期チャンク読み込み

        Args:
            file_path: ファイルパス
            chunk_size: チャンクサイズ

        Yields:
            str: ファイルチャンク
        """
        if not self._aiofiles_available:
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            return

        import aiofiles

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            self.logger.error(f"Async file read failed: {e}")
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

    async def async_read_lines_batched(
        self, file_path: Path, batch_size: int = 1000
    ) -> AsyncIterator[List[str]]:
        """
        非同期バッチ行読み込み

        Args:
            file_path: ファイルパス
            batch_size: バッチサイズ

        Yields:
            List[str]: 行のバッチ
        """
        if not self._aiofiles_available:
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                batch = []
                for line in f:
                    batch.append(line.rstrip("\n"))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                if batch:
                    yield batch
            return

        import aiofiles

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                batch = []
                async for line in f:
                    batch.append(line.rstrip("\n"))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                if batch:
                    yield batch
        except Exception as e:
            self.logger.error(f"Async batch read failed: {e}")
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                batch = []
                for line in f:
                    batch.append(line.rstrip("\n"))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                if batch:
                    yield batch

    async def async_write_results_streaming(
        self, file_path: Path, results_generator: AsyncIterator[str]
    ):
        """
        非同期ストリーミング結果書き込み

        Args:
            file_path: 出力ファイルパス
            results_generator: 結果ジェネレータ
        """
        if not self._aiofiles_available:
            # 同期フォールバック
            with open(file_path, "w", encoding="utf-8") as f:
                async for result in results_generator:
                    f.write(result)
            return

        import aiofiles

        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                async for result in results_generator:
                    await f.write(result)
        except Exception as e:
            self.logger.error(f"Async write failed: {e}")
            # 同期フォールバック
            with open(file_path, "w", encoding="utf-8") as f:
                async for result in results_generator:
                    f.write(result)

    def get_async_metrics(self) -> Dict[str, Any]:
        """非同期I/Oメトリクスを取得"""
        return {
            "aiofiles_available": self._aiofiles_available,
            "buffer_size": self.buffer_size,
            "optimization_level": "async" if self._aiofiles_available else "sync",
        }
