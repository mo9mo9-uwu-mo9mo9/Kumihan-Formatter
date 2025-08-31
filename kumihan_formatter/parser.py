"""Parser wrapper - 後方互換性を提供する軽量ラッパー

Issue #1249: 統合API設計統一対応
レガシーparser.pyの機能をcore/parsing/legacy_parser.pyに移行済み。
新しいAPIはunified_api.pyを使用してください。

警告: このモジュールは将来のバージョンで削除される可能性があります。
統合APIまたはManagerシステムの使用を推奨します。
"""

import warnings
from typing import Any

# 後方互換性のためのre-export
from .core.parsing.legacy_parser import (
    ParallelProcessingError,
    ChunkProcessingError,
    MemoryMonitoringError,
    ParallelProcessingConfig,
    Parser,
    parse,
    parse_with_error_config,
    __all__,
)

# 非推奨警告を発行
warnings.warn(
    "kumihan_formatter.parser module is deprecated. "
    "Please use kumihan_formatter.unified_api.KumihanFormatter instead.",
    DeprecationWarning,
    stacklevel=2,
)
