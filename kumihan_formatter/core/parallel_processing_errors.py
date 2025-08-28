"""Parallel Processing Errors - 並列処理エラー専用モジュール

parser.py分割により抽出 (Phase3最適化)
並列処理関連のエラークラスをすべて統合
"""


class ParallelProcessingError(Exception):
    """並列処理に関する一般的なエラー"""

    def __init__(self, message: str, chunk_id: str = None, worker_id: str = None):
        super().__init__(message)
        self.chunk_id = chunk_id
        self.worker_id = worker_id
        self.message = message

    def __str__(self):
        details = []
        if self.chunk_id:
            details.append(f"chunk_id={self.chunk_id}")
        if self.worker_id:
            details.append(f"worker_id={self.worker_id}")

        if details:
            return f"{self.message} ({', '.join(details)})"
        return self.message


class ChunkProcessingError(ParallelProcessingError):
    """チャンク処理に特化したエラー"""

    def __init__(
        self, message: str, chunk_id: str, line_start: int = None, line_end: int = None
    ):
        super().__init__(message, chunk_id=chunk_id)
        self.line_start = line_start
        self.line_end = line_end

    def __str__(self):
        details = [f"chunk_id={self.chunk_id}"]
        if self.line_start is not None and self.line_end is not None:
            details.append(f"lines={self.line_start}-{self.line_end}")

        return f"{self.message} ({', '.join(details)})"


class MemoryMonitoringError(ParallelProcessingError):
    """メモリ監視関連のエラー"""

    def __init__(
        self, message: str, memory_usage: float = None, memory_limit: float = None
    ):
        super().__init__(message)
        self.memory_usage = memory_usage
        self.memory_limit = memory_limit

    def __str__(self):
        details = []
        if self.memory_usage is not None:
            details.append(f"usage={self.memory_usage:.1f}MB")
        if self.memory_limit is not None:
            details.append(f"limit={self.memory_limit:.1f}MB")

        if details:
            return f"{self.message} ({', '.join(details)})"
        return self.message


class WorkerTimeoutError(ParallelProcessingError):
    """ワーカータイムアウトエラー"""

    def __init__(self, message: str, worker_id: str, timeout_seconds: float):
        super().__init__(message, worker_id=worker_id)
        self.timeout_seconds = timeout_seconds

    def __str__(self):
        return f"{self.message} (worker_id={self.worker_id}, timeout={self.timeout_seconds}s)"


class ResourceExhaustionError(ParallelProcessingError):
    """リソース枯渇エラー"""

    def __init__(self, message: str, resource_type: str, current_usage: float = None):
        super().__init__(message)
        self.resource_type = resource_type
        self.current_usage = current_usage

    def __str__(self):
        if self.current_usage is not None:
            return f"{self.message} ({self.resource_type}: {self.current_usage})"
        return f"{self.message} ({self.resource_type})"
