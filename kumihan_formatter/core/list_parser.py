"""互換性維持のためのリストパーサー再エクスポート"""

# 分割されたlist_parser_main.pyから互換性維持のために再エクスポート
# プロトコルは正しい場所からインポート
from .parsing.base.parser_protocols import ListParserProtocol
from .parsing.list.list_parser_main import ListParser

__all__ = [
    "ListParser",
    "ListParserProtocol",
]
