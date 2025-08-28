"""
並列処理対応パーサー - Unified Interface
Issue #694 Phase 3対応 - 分割されたコンポーネントの統合
"""

# 分割されたコンポーネントをインポート
from .processor_core import ChunkInfo, ParallelChunkProcessor
from .streaming_parser import ParallelStreamingParser

# 後方互換性のために元のクラス名をエクスポート
__all__ = ["ChunkInfo", "ParallelChunkProcessor", "ParallelStreamingParser"]
