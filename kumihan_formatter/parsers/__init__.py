"""Parser Module - 統合パーサーシステム

Issue #1215対応完了版：11個のParserを統合管理
"""

from typing import Optional, Union

# 統合パーサーシステム
from .main_parser import MainParser

# 個別パーサー（必要時直接アクセス用）

# プロトコル・ユーティリティ

__all__ = [
    "MainParser",
    "UnifiedListParser",
    "UnifiedKeywordParser",
    "UnifiedMarkdownParser",
    "ParserProtocol",
]


# 便利な統合関数
def parse(
    content: Union[str, List[str]],
    parser_type: str = "auto",
    config: Optional[Dict[str, Any]] = None,
) -> Optional[Union[Any, Dict[str, Any]]]:
    """統合パーシング関数（簡易アクセス）"""
    main_parser = MainParser(config)
    return main_parser.parse(content, parser_type)
