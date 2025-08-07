"""Error handling and configuration for parser legacy module

Issue #813対応: parser_old.pyから例外クラスと設定クラスを分離
"""

import os


# Issue #759対応: カスタム例外クラス定義
class ParallelProcessingError(Exception):
    """並列処理固有のエラー"""

    pass


class ChunkProcessingError(Exception):
    """チャンク処理でのエラー"""

    pass


class MemoryMonitoringError(Exception):
    """メモリ監視でのエラー"""

    pass


# Issue #759対応: 並列処理設定クラス
class ParallelProcessingConfig:
    """並列処理の設定管理"""

    def __init__(self):
        # 並列処理しきい値設定
        self.parallel_threshold_lines = 10000  # 10K行以上で並列化
        self.parallel_threshold_size = 10 * 1024 * 1024  # 10MB以上で並列化

        # チャンク設定
        self.min_chunk_size = 50
        self.max_chunk_size = 1000
        self.chunk_overlap = 5

        # メモリ監視設定
        self.memory_warning_threshold_mb = 500
        self.memory_critical_threshold_mb = 1000
        self.memory_monitoring_enabled = True

        # タイムアウト設定
        self.processing_timeout_seconds = 300

        # スレッドプール設定
        self.max_workers = min(4, os.cpu_count() or 1)
        self.thread_pool_timeout = 60

        # ストリーミング設定
        self.streaming_enabled = True
        self.streaming_buffer_size = 8192
        self.streaming_chunk_size = 1024

    @classmethod
    def from_environment(cls) -> "ParallelProcessingConfig":
        """環境変数から設定を読み込み"""
        config = cls()

        try:
            # 並列処理しきい値
            if os.getenv("KUMIHAN_PARALLEL_THRESHOLD_LINES"):
                config.parallel_threshold_lines = int(
                    os.getenv("KUMIHAN_PARALLEL_THRESHOLD_LINES")
                )
            if os.getenv("KUMIHAN_PARALLEL_THRESHOLD_SIZE"):
                config.parallel_threshold_size = int(
                    os.getenv("KUMIHAN_PARALLEL_THRESHOLD_SIZE")
                )

            # チャンク設定
            if os.getenv("KUMIHAN_MIN_CHUNK_SIZE"):
                config.min_chunk_size = int(os.getenv("KUMIHAN_MIN_CHUNK_SIZE"))
            if os.getenv("KUMIHAN_MAX_CHUNK_SIZE"):
                config.max_chunk_size = int(os.getenv("KUMIHAN_MAX_CHUNK_SIZE"))

            # メモリ監視設定
            if os.getenv("KUMIHAN_MEMORY_WARNING_THRESHOLD_MB"):
                config.memory_warning_threshold_mb = int(
                    os.getenv("KUMIHAN_MEMORY_WARNING_THRESHOLD_MB")
                )
            if os.getenv("KUMIHAN_MEMORY_CRITICAL_THRESHOLD_MB"):
                config.memory_critical_threshold_mb = int(
                    os.getenv("KUMIHAN_MEMORY_CRITICAL_THRESHOLD_MB")
                )

            # タイムアウト設定
            if os.getenv("KUMIHAN_PROCESSING_TIMEOUT_SECONDS"):
                config.processing_timeout_seconds = int(
                    os.getenv("KUMIHAN_PROCESSING_TIMEOUT_SECONDS")
                )

            # スレッドプール設定
            if os.getenv("KUMIHAN_MAX_WORKERS"):
                config.max_workers = int(os.getenv("KUMIHAN_MAX_WORKERS"))
        except (ValueError, TypeError):
            # 環境変数の解析に失敗した場合はデフォルト値を使用
            pass

        return config

    def validate(self) -> bool:
        """設定値の検証"""
        try:
            assert self.parallel_threshold_lines > 0
            assert self.parallel_threshold_size > 0
            assert self.min_chunk_size > 0
            assert self.max_chunk_size > self.min_chunk_size
            assert self.memory_warning_threshold_mb > 0
            assert self.memory_critical_threshold_mb > self.memory_warning_threshold_mb
            assert self.processing_timeout_seconds > 0
            return True
        except AssertionError:
            return False
