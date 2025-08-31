"""ParserProtocols - パーサーインターフェース定義"""

from typing import Any, Dict, Optional, runtime_checkable


@runtime_checkable
class ParserProtocol(Protocol):
    """パーサー基底プロトコル"""

    def parse(self, text: str) -> Dict[str, Any]:
        """テキスト解析"""
        ...


@runtime_checkable
class ParseContext(Protocol):
    """パースコンテキスト情報プロトコル"""

    line_number: int
    file_path: Optional[str]
    parent_context: Optional["ParseContext"]
    metadata: Dict[str, Any]


class ParserProtocols:
    """パーサープロトコル管理クラス"""

    @staticmethod
    def is_valid_parser(parser: Any) -> bool:
        """パーサー妥当性検証"""
        return isinstance(parser, ParserProtocol)
