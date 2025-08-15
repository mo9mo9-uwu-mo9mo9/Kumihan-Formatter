"""統一パーサープロトコル定義

Issue #880 Phase 2: パーサー階層整理
すべてのパーサーの統一インターフェース定義
"""

from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from ..ast_nodes import Node


@runtime_checkable
class ParserProtocol(Protocol):
    """パーサーの統一プロトコル"""

    def parse(self, content: Union[str, List[str]], **kwargs: Any) -> Node:
        """コンテンツを解析してノードを返す"""
        ...

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """解析可能なコンテンツかどうかを判定"""
        ...

    def get_parser_type(self) -> str:
        """パーサーの種類を返す"""
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """バリデーターの統一プロトコル"""

    def validate(self, content: Union[str, List[str]], **kwargs: Any) -> bool:
        """コンテンツの妥当性を検証"""
        ...

    def get_errors(self) -> List[str]:
        """エラーメッセージを取得"""
        ...

    def get_warnings(self) -> List[str]:
        """警告メッセージを取得"""
        ...


@runtime_checkable
class FormatterProtocol(Protocol):
    """フォーマッターの統一プロトコル"""

    def format(self, node: Node, **kwargs: Any) -> str:
        """ノードを指定形式にフォーマット"""
        ...

    def get_format_type(self) -> str:
        """フォーマット種類を返す"""
        ...


@runtime_checkable
class CoordinatorProtocol(Protocol):
    """コーディネーターの統一プロトコル"""

    def register_parser(self, parser: ParserProtocol, priority: int = 0) -> None:
        """パーサーを登録"""
        ...

    def select_parser(self, content: Union[str, List[str]]) -> Optional[ParserProtocol]:
        """最適なパーサーを選択"""
        ...

    def parse_with_fallback(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """フォールバック付きで解析実行"""
        ...


@runtime_checkable
class ProcessorProtocol(Protocol):
    """プロセッサーの統一プロトコル"""

    def process(self, input_data: Any, **kwargs: Any) -> Any:
        """データを処理"""
        ...

    def can_process(self, input_data: Any) -> bool:
        """処理可能なデータかどうかを判定"""
        ...


# パーサー種別の定数定義
class ParserType:
    """パーサー種別定数"""

    BLOCK = "block"
    KEYWORD = "keyword"
    LIST = "list"
    MARKDOWN = "markdown"
    CONTENT = "content"
    MARKER = "marker"
    IMAGE = "image"
    TEXT = "text"
    SPECIAL = "special"


# 解析結果メタデータの型定義
class ParseResult:
    """解析結果クラス"""

    def __init__(
        self,
        node: Node,
        parser_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.node = node
        self.parser_type = parser_type
        self.metadata = metadata or {}
        self.errors = errors or []
        self.warnings = warnings or []

    def is_successful(self) -> bool:
        """解析が成功したかどうか"""
        return len(self.errors) == 0

    def has_warnings(self) -> bool:
        """警告があるかどうか"""
        return len(self.warnings) > 0
