"""ストリーミングパーサのインターフェース定義"""

from abc import ABC, abstractmethod
from typing import (
    Iterator, AsyncIterator, Optional, List, Dict, Any, 
    Union, Callable, TypeVar, Generic, Protocol
)
from dataclasses import dataclass
from pathlib import Path
import io


T = TypeVar('T')


class ProgressCallback(Protocol):
    """進捗コールバックの型定義"""
    
    def __call__(
        self, 
        processed_bytes: int, 
        total_bytes: Optional[int] = None,
        current_chunk: int = 0,
        total_chunks: Optional[int] = None,
        message: Optional[str] = None
    ) -> None:
        """進捗情報を受け取る"""
        ...


@dataclass
class ParseResult:
    """パース結果"""
    content: str
    metadata: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    processing_time: float
    memory_peak: int
    chunks_processed: int


@dataclass
class ChunkInfo:
    """チャンク情報"""
    index: int
    start_position: int
    end_position: int
    size: int
    content_preview: str
    has_block_boundary: bool


class StreamingParser(ABC):
    """ストリーミングパーサの抽象基底クラス"""
    
    @abstractmethod
    def parse_file(
        self, 
        file_path: Path,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
        max_memory: Optional[int] = None
    ) -> ParseResult:
        """ファイルをストリーミング形式でパース"""
        pass
    
    @abstractmethod
    def parse_stream(
        self,
        stream: Union[io.TextIOBase, io.BufferedIOBase],
        total_size: Optional[int] = None,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
        max_memory: Optional[int] = None
    ) -> ParseResult:
        """ストリームをパース"""
        pass
    
    @abstractmethod
    async def parse_file_async(
        self,
        file_path: Path,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None,
        max_memory: Optional[int] = None
    ) -> ParseResult:
        """ファイルを非同期でパース"""
        pass
    
    @abstractmethod
    def get_chunk_info(
        self,
        file_path: Path,
        chunk_size: int
    ) -> List[ChunkInfo]:
        """ファイルのチャンク情報を取得"""
        pass
    
    @abstractmethod
    def estimate_memory_usage(
        self,
        file_size: int,
        chunk_size: int
    ) -> Dict[str, int]:
        """メモリ使用量を推定"""
        pass


class ChunkProcessor(ABC):
    """チャンク処理の抽象基底クラス"""
    
    @abstractmethod
    def process_chunk(
        self,
        chunk_content: str,
        chunk_index: int,
        is_first: bool,
        is_last: bool,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """チャンクを処理"""
        pass
    
    @abstractmethod
    def merge_results(
        self,
        chunk_results: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """チャンク処理結果をマージ"""
        pass
    
    @abstractmethod
    def handle_block_boundary(
        self,
        previous_chunk: str,
        current_chunk: str,
        boundary_position: int
    ) -> tuple[str, str]:
        """ブロック境界を処理"""
        pass


class CacheableResult(Generic[T]):
    """キャッシュ可能な結果"""
    
    def __init__(self, value: T, cache_key: str, ttl: Optional[float] = None):
        self.value = value
        self.cache_key = cache_key
        self.ttl = ttl
        self.created_at = self._get_current_time()
    
    def _get_current_time(self) -> float:
        import time
        return time.time()
    
    def is_expired(self) -> bool:
        """キャッシュが期限切れかチェック"""
        if self.ttl is None:
            return False
        return (self._get_current_time() - self.created_at) > self.ttl


class StreamingParserConfig:
    """ストリーミングパーサの設定"""
    
    def __init__(
        self,
        default_chunk_size: int = 1024 * 1024,  # 1MB
        max_chunk_size: int = 10 * 1024 * 1024,  # 10MB
        min_chunk_size: int = 64 * 1024,         # 64KB
        max_memory_usage: int = 50 * 1024 * 1024,  # 50MB
        enable_caching: bool = True,
        cache_ttl: Optional[float] = 300.0,      # 5分
        enable_compression: bool = False,
        compression_threshold: int = 1024 * 1024,  # 1MB
        progress_update_interval: float = 0.1,   # 100ms
        enable_async: bool = True,
        worker_threads: int = 2
    ):
        self.default_chunk_size = default_chunk_size
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_memory_usage = max_memory_usage
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.progress_update_interval = progress_update_interval
        self.enable_async = enable_async
        self.worker_threads = worker_threads
    
    def adjust_chunk_size(self, file_size: int) -> int:
        """ファイルサイズに基づいてチャンクサイズを調整"""
        # ファイルサイズに応じた適応的チャンクサイズ
        if file_size < 10 * 1024 * 1024:  # 10MB未満
            return min(self.default_chunk_size, file_size // 10)
        elif file_size < 100 * 1024 * 1024:  # 100MB未満
            return self.default_chunk_size
        else:  # 100MB以上
            return min(self.max_chunk_size, file_size // 100)
    
    def validate(self) -> List[str]:
        """設定を検証"""
        errors = []
        
        if self.min_chunk_size > self.max_chunk_size:
            errors.append("min_chunk_size must be <= max_chunk_size")
        
        if self.default_chunk_size < self.min_chunk_size:
            errors.append("default_chunk_size must be >= min_chunk_size")
        
        if self.default_chunk_size > self.max_chunk_size:
            errors.append("default_chunk_size must be <= max_chunk_size")
        
        if self.max_memory_usage < self.max_chunk_size * 2:
            errors.append("max_memory_usage should be at least 2x max_chunk_size")
        
        if self.worker_threads < 1:
            errors.append("worker_threads must be >= 1")
        
        return errors