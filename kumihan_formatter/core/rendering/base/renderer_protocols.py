"""統一レンダラープロトコル定義 - Issue #914 Phase 1

2025年Pythonベストプラクティスに基づく統一レンダリングインターフェース実装
全Rendererが実装すべき統一プロトコルとエラーハンドリングを定義
"""

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Protocol,
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


# 統一レンダリングデータ構造定義
@dataclass
class RenderContext:
    """統一レンダリングコンテキスト - 全レンダラー共通入力情報"""

    output_format: str = "html"
    options: Dict[str, Any] = None
    theme: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        """初期化後処理 - デフォルト値設定"""
        if self.options is None:
            self.options = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RenderResult:
    """統一レンダリング結果 - 全レンダラー共通戻り値"""

    success: bool
    content: str
    metadata: Dict[str, Any]
    warnings: List[str]

    def __post_init__(self) -> None:
        """初期化後処理 - デフォルト値設定"""
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []

    def add_warning(self, warning: str) -> None:
        """警告を追加"""
        self.warnings.append(warning)

    def has_warnings(self) -> bool:
        """警告があるかチェック"""
        return bool(self.warnings)


class RenderError(Exception):
    """統一レンダリングエラー - ノード情報付きエラー"""

    def __init__(self, message: str, node: Optional[Node] = None) -> None:
        super().__init__(message)
        self.message = message
        self.node = node

    def __str__(self) -> str:
        if self.node:
            node_info = f" (node type: {self.node.type})"
            return f"{self.message}{node_info}"
        return self.message


# 統一基底レンダラープロトコル
@runtime_checkable
class BaseRendererProtocol(Protocol):
    """基底レンダラープロトコル - 全レンダラーの共通基盤

    2025年ベストプラクティス:
    - runtime_checkable による実行時型チェック
    - 統一されたエラーハンドリング
    - 明示的な型注釈
    - 前方互換性維持
    """

    def render(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> RenderResult:
        """統一レンダリングインターフェース

        Args:
            nodes: レンダリング対象のノードリスト
            context: レンダリングコンテキスト（オプション）

        Returns:
            RenderResult: 統一レンダリング結果

        Raises:
            RenderError: レンダリング処理中の致命的エラー
        """
        ...

    def render_node(self, node: Node, context: Optional[RenderContext] = None) -> str:
        """単一ノードレンダリング

        Args:
            node: レンダリング対象のノード
            context: レンダリングコンテキスト（オプション）

        Returns:
            str: レンダリング結果の文字列

        Raises:
            RenderError: ノードレンダリング中のエラー
        """
        ...

    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧を取得

        Returns:
            List[str]: 対応している出力フォーマットのリスト
        """
        ...

    def validate_options(self, options: Dict[str, Any]) -> List[str]:
        """オプション検証

        Args:
            options: 検証対象のオプション辞書

        Returns:
            List[str]: バリデーションエラーメッセージリスト（空リストは成功）
        """
        ...

    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報取得

        Returns:
            Dict[str, Any]: レンダラーメタデータ
                - name: レンダラー名
                - version: バージョン
                - supported_formats: 対応フォーマットリスト
                - capabilities: 機能リスト
        """
        ...


# 特化型レンダラープロトコル
@runtime_checkable
class HtmlRendererProtocol(BaseRendererProtocol, Protocol):
    """HTMLレンダラープロトコル - HTML出力特化

    統一インターフェースを継承し、HTML出力に特化した機能を追加
    """

    def render_html(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> str:
        """HTML専用レンダリング

        Args:
            nodes: レンダリング対象のノードリスト
            context: レンダリングコンテキスト（オプション）

        Returns:
            str: HTML文字列
        """
        ...

    def render_with_template(
        self,
        nodes: List[Node],
        template_path: str,
        context: Optional[RenderContext] = None,
    ) -> str:
        """テンプレート使用レンダリング

        Args:
            nodes: レンダリング対象のノードリスト
            template_path: テンプレートファイルパス
            context: レンダリングコンテキスト（オプション）

        Returns:
            str: テンプレート適用済みHTML
        """
        ...

    def get_css_classes(self) -> Dict[str, str]:
        """使用可能なCSSクラス一覧を取得

        Returns:
            Dict[str, str]: CSSクラス名と説明の辞書
        """
        ...

    def escape_html(self, text: str) -> str:
        """HTMLエスケープ処理

        Args:
            text: エスケープ対象のテキスト

        Returns:
            str: エスケープ済みテキスト
        """
        ...


@runtime_checkable
class MarkdownRendererProtocol(BaseRendererProtocol, Protocol):
    """Markdownレンダラープロトコル - Markdown出力特化

    統一インターフェースを継承し、Markdown出力に特化した機能を追加
    """

    def render_markdown(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> str:
        """Markdown専用レンダリング

        Args:
            nodes: レンダリング対象のノードリスト
            context: レンダリングコンテキスト（オプション）

        Returns:
            str: Markdown文字列
        """
        ...

    def convert_from_kumihan(
        self, kumihan_text: str, context: Optional[RenderContext] = None
    ) -> str:
        """Kumihan記法からMarkdownに変換

        Args:
            kumihan_text: 変換対象のKumihan記法テキスト
            context: 変換コンテキスト（オプション）

        Returns:
            str: 変換されたMarkdown文字列
        """
        ...

    def get_markdown_extensions(self) -> List[str]:
        """使用可能なMarkdown拡張機能一覧を取得

        Returns:
            List[str]: 対応しているMarkdown拡張機能のリスト
        """
        ...

    def validate_markdown_syntax(self, markdown: str) -> List[str]:
        """Markdown構文検証

        Args:
            markdown: 検証対象のMarkdown文字列

        Returns:
            List[str]: 構文エラーメッセージリスト（空リストは成功）
        """
        ...


@runtime_checkable
class StreamingRendererProtocol(Protocol):
    """ストリーミングレンダラープロトコル - 大容量出力特化

    メモリ効率的なストリーミング出力に特化したインターフェース
    """

    def render_streaming(
        self, nodes: Iterator[Node], context: Optional[RenderContext] = None
    ) -> Iterator[str]:
        """ストリーミングレンダリング

        Args:
            nodes: レンダリング対象のノードストリーム
            context: レンダリングコンテキスト（オプション）

        Yields:
            str: レンダリング結果の文字列チャンク
        """
        ...

    def render_chunk(
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> str:
        """チャンクレンダリング

        Args:
            nodes: レンダリング対象のノードチャンク
            context: レンダリングコンテキスト（オプション）

        Returns:
            str: レンダリング結果の文字列
        """
        ...

    def get_recommended_chunk_size(self) -> int:
        """推奨チャンクサイズを取得

        Returns:
            int: 推奨チャンクサイズ（ノード数）
        """
        ...

    def supports_streaming_output(self) -> bool:
        """ストリーミング出力対応確認

        Returns:
            bool: ストリーミング出力可能かどうか
        """
        ...


@runtime_checkable
class CompositeRendererProtocol(BaseRendererProtocol, Protocol):
    """複合レンダラープロトコル - 複数レンダラー統合管理

    統一インターフェースを継承し、複数レンダラーの組み合わせ機能を追加
    """

    def add_renderer(self, renderer: BaseRendererProtocol, priority: int = 0) -> None:
        """レンダラーを追加

        Args:
            renderer: 追加するレンダラー
            priority: 優先度（数値が大きいほど高優先度）
        """
        ...

    def remove_renderer(self, renderer: BaseRendererProtocol) -> bool:
        """レンダラーを削除

        Args:
            renderer: 削除するレンダラー

        Returns:
            bool: 削除成功の可否
        """
        ...

    def get_renderers(self) -> List[BaseRendererProtocol]:
        """登録されたレンダラーリストを取得

        Returns:
            List[BaseRendererProtocol]: レンダラーリスト（優先度順）
        """
        ...

    def get_renderer_count(self) -> int:
        """登録レンダラー数を取得

        Returns:
            int: 登録されているレンダラーの数
        """
        ...

    def clear_renderers(self) -> None:
        """全レンダラーをクリア"""
        ...

    def get_renderer_by_format(
        self, format_name: str
    ) -> Optional[BaseRendererProtocol]:
        """フォーマット名でレンダラーを取得

        Args:
            format_name: 検索対象のフォーマット名

        Returns:
            Optional[BaseRendererProtocol]: 該当するレンダラー（None=未見つけ）
        """
        ...


# ジェネリック型とファクトリー
R = TypeVar("R", bound=BaseRendererProtocol)


@runtime_checkable
class RenderChain(Generic[R], Protocol):
    """レンダリング処理チェーン - 複数処理の連結

    Generic型を活用した型安全なレンダリング処理チェーン
    """

    def add_processor(self, processor: Any) -> "RenderChain[R]":
        """後処理を追加

        Args:
            processor: 追加する後処理関数

        Returns:
            RenderChain[R]: メソッドチェーン用の自身
        """
        ...

    def process(self, content: str, context: Optional[RenderContext] = None) -> str:
        """チェーン処理を実行

        Args:
            content: 入力コンテンツ
            context: 処理コンテキスト（オプション）

        Returns:
            str: 処理結果
        """
        ...


# 統一型エイリアス（後方互換性維持）
AnyRenderer = Union[
    BaseRendererProtocol,
    HtmlRendererProtocol,
    MarkdownRendererProtocol,
    StreamingRendererProtocol,
    CompositeRendererProtocol,
]

RendererResult = Union[str, RenderResult, Iterator[str]]

# 後方互換性エイリアス
RendererProtocol = BaseRendererProtocol


# レンダラーファクトリー関数
def create_render_context(
    output_format: str = "html", theme: Optional[str] = None, **kwargs: Any
) -> RenderContext:
    """RenderContextの便利な作成関数

    Args:
        output_format: 出力フォーマット
        theme: テーマ名（オプション）
        **kwargs: 追加のオプション

    Returns:
        RenderContext: 作成されたコンテキスト
    """
    context = RenderContext(output_format=output_format, theme=theme)
    context.options.update(kwargs)
    return context


def create_render_result(
    content: str = "", success: bool = True, **kwargs: Any
) -> RenderResult:
    """RenderResultの便利な作成関数

    Args:
        content: レンダリング結果コンテンツ
        success: 成功フラグ
        **kwargs: 追加のメタデータ

    Returns:
        RenderResult: 作成された結果
    """
    result = RenderResult(
        success=success, content=content, metadata=kwargs, warnings=[]
    )
    return result


# プロトコル適合性チェック関数
def is_renderer_protocol_compatible(obj: Any) -> bool:
    """オブジェクトがBaseRendererProtocolに適合するかチェック

    Args:
        obj: チェック対象のオブジェクト

    Returns:
        bool: プロトコル適合性
    """
    return isinstance(obj, BaseRendererProtocol)


def validate_renderer_implementation(renderer: BaseRendererProtocol) -> List[str]:
    """レンダラー実装の検証

    Args:
        renderer: 検証対象のレンダラー

    Returns:
        List[str]: 実装問題のリスト（空=問題なし）
    """
    issues = []

    # 必須メソッドの存在確認
    required_methods = [
        "render",
        "render_node",
        "get_supported_formats",
        "validate_options",
        "get_renderer_info",
    ]
    for method in required_methods:
        if not hasattr(renderer, method) or not callable(getattr(renderer, method)):
            issues.append(f"Missing or non-callable method: {method}")

    # get_renderer_info の戻り値検証
    try:
        info = renderer.get_renderer_info()
        if not isinstance(info, dict):
            issues.append("get_renderer_info() must return dict")
        else:
            required_keys = ["name", "version", "supported_formats", "capabilities"]
            for key in required_keys:
                if key not in info:
                    issues.append(f"get_renderer_info() missing key: {key}")
    except Exception as e:
        issues.append(f"get_renderer_info() failed: {e}")

    # get_supported_formats の戻り値検証
    try:
        formats = renderer.get_supported_formats()
        if not isinstance(formats, list):
            issues.append("get_supported_formats() must return list")
    except Exception as e:
        issues.append(f"get_supported_formats() failed: {e}")

    return issues
