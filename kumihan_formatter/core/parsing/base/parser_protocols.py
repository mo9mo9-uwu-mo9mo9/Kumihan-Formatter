"""統一パーサープロトコル定義 - Issue #914 Phase 1

2025年Pythonベストプラクティスに基づく統一インターフェース実装
全Parser/Rendererが実装すべき統一プロトコルとエラーハンドリングを定義
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

if TYPE_CHECKING:
    from ...ast_nodes.node import Node
else:
    try:
        from ...ast_nodes.node import Node
    except ImportError:
        from ...ast_nodes import Node


# 統一データ構造定義
@dataclass
class ParseResult:
    """統一パース結果オブジェクト - 全パーサー共通戻り値"""

    success: bool
    nodes: List[Node]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        """初期化後処理 - デフォルト値設定"""
        if self.metadata is None:
            self.metadata = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.nodes is None:
            self.nodes = []

    def add_error(self, error: str) -> None:
        """エラーを追加"""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """警告を追加"""
        self.warnings.append(warning)

    def has_issues(self) -> bool:
        """エラーまたは警告があるかチェック"""
        return bool(self.errors or self.warnings)


@dataclass
class ParseContext:
    """統一パースコンテキスト - 全パーサー共通入力情報"""

    source_file: Optional[str] = None
    line_number: int = 1
    column_number: int = 1
    parser_state: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """初期化後処理 - デフォルト値設定"""
        if self.parser_state is None:
            self.parser_state = {}
        if self.config is None:
            self.config = {}


class ParseError(Exception):
    """統一パーシングエラー - 位置情報付きエラー"""

    def __init__(
        self, message: str, line: int = 0, column: int = 0, source: str = ""
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.source = source

    def __str__(self) -> str:
        if self.line > 0:
            return f"{self.message} (line {self.line}, column {self.column})"
        return self.message


# 統一基底プロトコル
@runtime_checkable
class BaseParserProtocol(Protocol):
    """基底パーサープロトコル - 全パーサーの共通基盤

    2025年ベストプラクティス:
    - runtime_checkable による実行時型チェック
    - 統一されたエラーハンドリング
    - 明示的な型注釈
    - 前方互換性維持
    """

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース

        Args:
            content: パース対象のコンテンツ
            context: パースコンテキスト（オプション）

        Returns:
            ParseResult: 統一パース結果

        Raises:
            ParseError: パース処理中の致命的エラー
        """
        ...

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション - エラーリスト返却

        Args:
            content: 検証対象のコンテンツ
            context: 検証コンテキスト（オプション）

        Returns:
            List[str]: エラーメッセージリスト（空リストは成功）
        """
        ...

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得

        Returns:
            Dict[str, Any]: パーサーメタデータ
                - name: パーサー名
                - version: バージョン
                - supported_formats: 対応フォーマットリスト
                - capabilities: 機能リスト
        """
        ...

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定

        Args:
            format_hint: フォーマットヒント文字列

        Returns:
            bool: 対応可能かどうか
        """
        ...


# 特化型プロトコル
@runtime_checkable
class BlockParserProtocol(BaseParserProtocol, Protocol):
    """ブロックパーサープロトコル - ブロック要素特化

    統一インターフェースを継承し、ブロック解析に特化した機能を追加
    """

    def parse_block(self, block: str, context: Optional[ParseContext] = None) -> Node:
        """単一ブロックをパース

        Args:
            block: パース対象のブロック
            context: パースコンテキスト（オプション）

        Returns:
            Node: パース結果のノード

        Raises:
            ParseError: ブロックパース中のエラー
        """
        ...

    def extract_blocks(
        self, text: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """テキストからブロックを抽出

        Args:
            text: 抽出対象のテキスト
            context: 抽出コンテキスト（オプション）

        Returns:
            List[str]: 抽出されたブロックのリスト
        """
        ...

    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出

        Args:
            block: 検査対象のブロック

        Returns:
            Optional[str]: 検出されたブロックタイプ（None=未検出）
        """
        ...


@runtime_checkable
class KeywordParserProtocol(BaseParserProtocol, Protocol):
    """キーワードパーサープロトコル - Kumihanキーワード特化

    統一インターフェースを継承し、キーワード解析に特化した機能を追加
    """

    def parse_keywords(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """コンテンツからキーワードを抽出

        Args:
            content: キーワード抽出対象のコンテンツ
            context: 抽出コンテキスト（オプション）

        Returns:
            List[str]: 抽出されたキーワードのリスト
        """
        ...

    def parse_marker_keywords(
        self, marker_content: str, context: Optional[ParseContext] = None
    ) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """マーカーからキーワードと属性を解析

        Args:
            marker_content: マーカーコンテンツ
            context: 解析コンテキスト（オプション）

        Returns:
            Tuple[List[str], Dict[str, Any], List[str]]:
                (キーワードリスト, 属性辞書, エラーリスト)
        """
        ...

    def validate_keyword(
        self, keyword: str, context: Optional[ParseContext] = None
    ) -> bool:
        """キーワードの妥当性を検証

        Args:
            keyword: 検証対象のキーワード
            context: 検証コンテキスト（オプション）

        Returns:
            bool: 妥当性判定結果
        """
        ...

    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワードを個別キーワードに分割

        Args:
            keyword_content: 分割対象のキーワード文字列

        Returns:
            List[str]: 分割されたキーワードリスト
        """
        ...


@runtime_checkable
class ListParserProtocol(BaseParserProtocol, Protocol):
    """リストパーサープロトコル - リスト要素特化

    統一インターフェースを継承し、リスト解析に特化した機能を追加
    """

    def parse_list_items(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """リストアイテムをパース

        Args:
            content: リストコンテンツ
            context: パースコンテキスト（オプション）

        Returns:
            List[Node]: パースされたリストアイテムのノードリスト
        """
        ...

    def parse_nested_list(
        self, content: str, level: int = 0, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """ネストリストをパース

        Args:
            content: ネストリストコンテンツ
            level: ネストレベル
            context: パースコンテキスト（オプション）

        Returns:
            List[Node]: パースされたネストリストのノードリスト
        """
        ...

    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプを検出

        Args:
            line: 検査対象の行

        Returns:
            Optional[str]: 検出されたリストタイプ (ordered/unordered/None)
        """
        ...

    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得

        Args:
            line: 検査対象の行

        Returns:
            int: ネストレベル（0=ルートレベル）
        """
        ...


@runtime_checkable
class MarkdownParserProtocol(BaseParserProtocol, Protocol):
    """Markdownパーサープロトコル - Markdown要素特化

    統一インターフェースを継承し、Markdown解析に特化した機能を追加
    """

    def parse_markdown_elements(
        self, text: str, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """Markdown要素をパース

        Args:
            text: Markdownテキスト
            context: パースコンテキスト（オプション）

        Returns:
            List[Node]: パースされたMarkdown要素のノードリスト
        """
        ...

    def convert_to_kumihan(
        self, markdown_text: str, context: Optional[ParseContext] = None
    ) -> str:
        """MarkdownをKumihan記法に変換

        Args:
            markdown_text: 変換対象のMarkdownテキスト
            context: 変換コンテキスト（オプション）

        Returns:
            str: 変換されたKumihan記法テキスト
        """
        ...

    def detect_markdown_elements(self, text: str) -> List[str]:
        """Markdown要素を検出

        Args:
            text: 検査対象のテキスト

        Returns:
            List[str]: 検出されたMarkdown要素タイプのリスト
        """
        ...


@runtime_checkable
class StreamingParserProtocol(Protocol):
    """ストリーミングパーサープロトコル - 大容量データ処理特化

    メモリ効率的なストリーミング処理に特化したインターフェース
    """

    def parse_streaming(
        self, stream: Iterator[str], context: Optional[ParseContext] = None
    ) -> Iterator[Node]:
        """ストリーミングパース

        Args:
            stream: 入力ストリーム
            context: パースコンテキスト（オプション）

        Yields:
            Node: パース結果のノード
        """
        ...

    def process_chunk(
        self, chunk: str, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """チャンクを処理

        Args:
            chunk: 処理対象のチャンク
            context: 処理コンテキスト（オプション）

        Returns:
            List[Node]: 処理結果のノードリスト
        """
        ...

    def get_chunk_size(self) -> int:
        """推奨チャンクサイズを取得

        Returns:
            int: 推奨チャンクサイズ（バイト）
        """
        ...

    def supports_streaming(self) -> bool:
        """ストリーミング処理対応確認

        Returns:
            bool: ストリーミング処理可能かどうか
        """
        ...


@runtime_checkable
class CompositeParserProtocol(BaseParserProtocol, Protocol):
    """複合パーサープロトコル - 複数パーサー統合管理

    統一インターフェースを継承し、複数パーサーの組み合わせ機能を追加
    """

    def add_parser(self, parser: BaseParserProtocol, priority: int = 0) -> None:
        """パーサーを追加

        Args:
            parser: 追加するパーサー
            priority: 優先度（数値が大きいほど高優先度）
        """
        ...

    def remove_parser(self, parser: BaseParserProtocol) -> bool:
        """パーサーを削除

        Args:
            parser: 削除するパーサー

        Returns:
            bool: 削除成功の可否
        """
        ...

    def get_parsers(self) -> List[BaseParserProtocol]:
        """登録されたパーサーリストを取得

        Returns:
            List[BaseParserProtocol]: パーサーリスト（優先度順）
        """
        ...

    def get_parser_count(self) -> int:
        """登録パーサー数を取得

        Returns:
            int: 登録されているパーサーの数
        """
        ...

    def clear_parsers(self) -> None:
        """全パーサーをクリア"""
        ...


# ジェネリック型とファクトリー
T = TypeVar("T")
P = TypeVar("P", bound=BaseParserProtocol)


@runtime_checkable
class ParseChain(Generic[T], Protocol):
    """パース処理チェーン - 複数処理の連結

    Generic型を活用した型安全なパース処理チェーン
    """

    def add_processor(self, processor: Callable[[T], T]) -> "ParseChain[T]":
        """処理を追加

        Args:
            processor: 追加する処理関数

        Returns:
            ParseChain[T]: メソッドチェーン用の自身
        """
        ...

    def process(self, input_data: T) -> T:
        """チェーン処理を実行

        Args:
            input_data: 入力データ

        Returns:
            T: 処理結果
        """
        ...


# 統一型エイリアス（後方互換性維持）
AnyParser = Union[
    BaseParserProtocol,
    BlockParserProtocol,
    KeywordParserProtocol,
    ListParserProtocol,
    MarkdownParserProtocol,
    StreamingParserProtocol,
    CompositeParserProtocol,
]

ParserResult = Union[Node, List[Node], Iterator[Node], ParseResult]

# 後方互換性エイリアス
ParserProtocol = BaseParserProtocol


# パーサーファクトリー関数
def create_parse_context(
    source_file: Optional[str] = None,
    line_number: int = 1,
    column_number: int = 1,
    **kwargs: Any,
) -> ParseContext:
    """ParseContextの便利な作成関数

    Args:
        source_file: ソースファイルパス
        line_number: 行番号
        column_number: 列番号
        **kwargs: 追加の設定項目

    Returns:
        ParseContext: 作成されたコンテキスト
    """
    context = ParseContext(
        source_file=source_file, line_number=line_number, column_number=column_number
    )
    context.config.update(kwargs)
    return context


def create_parse_result(
    nodes: Optional[List[Node]] = None, success: bool = True, **kwargs: Any
) -> ParseResult:
    """ParseResultの便利な作成関数

    Args:
        nodes: パース結果ノード
        success: 成功フラグ
        **kwargs: 追加のメタデータ

    Returns:
        ParseResult: 作成された結果
    """
    result = ParseResult(
        success=success, nodes=nodes or [], errors=[], warnings=[], metadata=kwargs
    )
    return result


# プロトコル適合性チェック関数
def is_parser_protocol_compatible(obj: Any) -> bool:
    """オブジェクトがBaseParserProtocolに適合するかチェック

    Args:
        obj: チェック対象のオブジェクト

    Returns:
        bool: プロトコル適合性
    """
    return isinstance(obj, BaseParserProtocol)


def validate_parser_implementation(parser: BaseParserProtocol) -> List[str]:
    """パーサー実装の検証

    Args:
        parser: 検証対象のパーサー

    Returns:
        List[str]: 実装問題のリスト（空=問題なし）
    """
    issues = []

    # 必須メソッドの存在確認
    required_methods = ["parse", "validate", "get_parser_info", "supports_format"]
    for method in required_methods:
        if not hasattr(parser, method) or not callable(getattr(parser, method)):
            issues.append(f"Missing or non-callable method: {method}")

    # get_parser_info の戻り値検証
    try:
        info = parser.get_parser_info()
        if not isinstance(info, dict):
            issues.append("get_parser_info() must return dict")
        else:
            required_keys = ["name", "version", "supported_formats", "capabilities"]
            for key in required_keys:
                if key not in info:
                    issues.append(f"get_parser_info() missing key: {key}")
    except Exception as e:
        issues.append(f"get_parser_info() failed: {e}")

    return issues
