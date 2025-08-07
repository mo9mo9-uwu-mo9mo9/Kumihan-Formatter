"""Parser Legacy Module

This module provides backward compatibility for parser_old.py by splitting it into
multiple maintainable modules while maintaining 100% API compatibility.

分割構造:
- core_parser.py: コアパーサーロジック
- parallel_processor.py: 並列・ストリーミング処理
- memory_monitor.py: メモリ監視・統計処理
- error_handler.py: エラーハンドリング

Issue #813対応: parser_old.py（2152行）を1000行以下に分割
"""

# パッケージ外向け関数
# 後方互換性のためのインポート統合
from .core_parser import Parser, parse, parse_with_error_config
from .error_handler import (
    ChunkProcessingError,
    MemoryMonitoringError,
    ParallelProcessingConfig,
    ParallelProcessingError,
)

__all__ = [
    "Parser",
    "ParallelProcessingError",
    "ChunkProcessingError",
    "MemoryMonitoringError",
    "ParallelProcessingConfig",
    "parse",
    "parse_with_error_config",
]
