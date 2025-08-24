"""ParserProtocols - パーサーインターフェース定義"""

from typing import Any, Dict, Protocol, runtime_checkable

@runtime_checkable
class ParserProtocol(Protocol):
    """パーサー基底プロトコル"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """テキスト解析"""
        ...

class ParserProtocols:
    """パーサープロトコル管理クラス"""
    
    @staticmethod
    def is_valid_parser(parser: Any) -> bool:
        """パーサー妥当性検証"""
        return isinstance(parser, ParserProtocol)