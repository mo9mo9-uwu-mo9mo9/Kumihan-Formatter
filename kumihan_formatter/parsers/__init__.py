"""Parser Module - 統合パーサーシステム

Issue #1252対応完了版：10個→5個のParser統合最適化完了

統合後の5つのコンポーネント:
1. main_parser.py - メインパーサー（自動判定・振り分け）
2. core_parser.py - コアパーサー（legacy+parser_core統合）
3. specialized_parser.py - 特殊化パーサー（マーカー・フォーマット系統合）
4. parser_protocols.py - プロトコル定義
5. parser_utils.py - ユーティリティ統合
"""

import warnings
from typing import Any, Dict, List, Optional, Union

# Issue #1252統合パーサーシステム（最適化版）
from .main_parser import MainParser
from .core_parser import Parser as CoreParser, ParallelProcessingConfig
from .specialized_parser import SpecializedParser
from .parser_utils import ParserUtils

# 既存統合パーサー（既に最適化済み）
from .unified_list_parser import UnifiedListParser
from .unified_keyword_parser import UnifiedKeywordParser
from .unified_markdown_parser import UnifiedMarkdownParser

# プロトコル・ユーティリティ
from .parser_protocols import ParserProtocol

__all__ = [
    # 統合最適化パーサー（Issue #1252）
    "MainParser",
    "CoreParser",
    "SpecializedParser",
    "ParserUtils",
    # 設定・プロトコル
    "ParallelProcessingConfig",
    "ParserProtocol",
    # 既存統合パーサー
    "UnifiedListParser",
    "UnifiedKeywordParser",
    "UnifiedMarkdownParser",
]


# 統合パーシング関数（最適化版）
def parse(
    content: Union[str, List[str]],
    parser_type: str = "auto",
    config: Optional[Dict[str, Any]] = None,
) -> Optional[Union[Any, Dict[str, Any]]]:
    """統合パーシング関数（Issue #1252最適化版）

    Args:
        content: パース対象コンテンツ
        parser_type: パーサータイプ指定（autoで自動判定）
        config: パーサー設定

    Returns:
        パース結果

    Note:
        10個→5個統合最適化済み
    """
    main_parser = MainParser(config)
    return main_parser.parse(content, parser_type)


# Issue #1252完了通知
warnings.warn(
    "Parser integration optimization completed (Issue #1252). "
    "10 files reduced to 5 files for better maintainability.",
    UserWarning,
    stacklevel=2,
)
