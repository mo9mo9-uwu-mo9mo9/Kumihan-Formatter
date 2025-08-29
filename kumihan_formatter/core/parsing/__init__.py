"""パーサー基底モジュール

Issue #880 Phase 2: 統一パーサー基盤（簡素化後）
削除されたmixins・parser_baseの代わりに、現存する統合パーサーを使用
"""

# 統合最適化後：存在するモジュールのみインポート
from .core_marker_parser import CoreMarkerParser
from .parser_core import Parser

__all__ = [
    "CoreMarkerParser",
    "Parser",
]
