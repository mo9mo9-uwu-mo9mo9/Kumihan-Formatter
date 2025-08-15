"""統一解析コーディネーター

Issue #880 Phase 2: パーサー階層整理
複数パーサーの統括管理・最適なパーサー選択・解析実行
既存のParsingCoordinatorを強化・統合
"""

from typing import Any, Dict, List, Optional, Union

from ..ast_nodes import error_node
from ..utilities.logger import get_logger
from .base import UnifiedParserBase
from .protocols import ParseResult, ParserProtocol


class UnifiedParsingCoordinator:
    """統一解析コーディネーター

    複数のパーサーを管理し、コンテンツに最適なパーサーを自動選択
    フォールバック機能と詳細な解析結果を提供
    """

    def __init__(self) -> None:
        """コーディネーターの初期化"""
        self.logger = get_logger(__name__)

        # 登録済みパーサーの管理
        self._parsers: Dict[str, ParserProtocol] = {}
        self._parser_priorities: Dict[str, int] = {}
        self._parser_order: List[str] = []

        # 統計情報
        self._parse_stats: Dict[str, int] = {}
        self._fallback_stats: Dict[str, int] = {}

    def register_parser(self, parser: ParserProtocol, priority: int = 0) -> None:
        """パーサーを登録

        Args:
            parser: 登録するパーサー
            priority: 優先度（高い値ほど優先、デフォルト0）
        """
        parser_type = parser.get_parser_type()

        if parser_type in self._parsers:
            self.logger.warning(
                f"Parser {parser_type} is already registered, overwriting"
            )

        self._parsers[parser_type] = parser
        self._parser_priorities[parser_type] = priority

        # 優先度順にソート
        self._parser_order = sorted(
            self._parsers.keys(), key=lambda x: self._parser_priorities[x], reverse=True
        )

        self.logger.info(f"Registered parser: {parser_type} (priority: {priority})")

    def unregister_parser(self, parser_type: str) -> bool:
        """パーサーの登録解除

        Args:
            parser_type: 解除するパーサーの種類

        Returns:
            解除に成功したかどうか
        """
        if parser_type in self._parsers:
            del self._parsers[parser_type]
            del self._parser_priorities[parser_type]
            self._parser_order.remove(parser_type)
            self.logger.info(f"Unregistered parser: {parser_type}")
            return True

        self.logger.warning(f"Parser {parser_type} not found for unregistration")
        return False

    def select_parser(self, content: Union[str, List[str]]) -> Optional[ParserProtocol]:
        """最適なパーサーを選択

        Args:
            content: 解析対象のコンテンツ

        Returns:
            選択されたパーサー、該当なしの場合はNone
        """
        if not content:
            return None

        # 優先度順にパーサーを試行
        for parser_type in self._parser_order:
            parser = self._parsers[parser_type]

            try:
                if parser.can_parse(content):
                    self.logger.debug(f"Selected parser: {parser_type}")
                    return parser
            except Exception as e:
                self.logger.warning(f"Parser {parser_type} selection failed: {e}")
                continue

        self.logger.warning("No suitable parser found for content")
        return None

    def parse_with_fallback(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> ParseResult:
        """フォールバック付きで解析実行

        Args:
            content: 解析対象のコンテンツ
            **kwargs: パーサーに渡す追加パラメータ

        Returns:
            解析結果
        """
        if not content:
            return ParseResult(
                node=error_node("Empty content"),
                parser_type="none",
                errors=["空のコンテンツです"],
            )

        # 最適なパーサーを選択
        primary_parser = self.select_parser(content)

        if primary_parser:
            # プライマリーパーサーで解析を試行
            result = self._try_parse(primary_parser, content, **kwargs)
            if result.is_successful():
                self._update_stats(primary_parser.get_parser_type(), success=True)
                return result
            else:
                self.logger.warning(
                    f"Primary parser {primary_parser.get_parser_type()} failed, "
                    f"trying fallback"
                )
                self._update_stats(primary_parser.get_parser_type(), success=False)

        # フォールバック: すべてのパーサーを試行
        for parser_type in self._parser_order:
            parser = self._parsers[parser_type]

            # プライマリーパーサーは既に試行済みなのでスキップ
            if primary_parser and parser == primary_parser:
                continue

            result = self._try_parse(parser, content, **kwargs)
            if result.is_successful():
                self.logger.info(f"Fallback parser {parser_type} succeeded")
                self._update_fallback_stats(parser_type)
                return result

        # すべてのパーサーが失敗
        self.logger.error("All parsers failed")
        return ParseResult(
            node=error_node("All parsers failed"),
            parser_type="failed",
            errors=["利用可能なパーサーでの解析に失敗しました"],
        )

    def _try_parse(
        self, parser: ParserProtocol, content: Union[str, List[str]], **kwargs: Any
    ) -> ParseResult:
        """パーサーでの解析を試行

        Args:
            parser: 使用するパーサー
            content: 解析対象のコンテンツ
            **kwargs: パーサーに渡す追加パラメータ

        Returns:
            解析結果
        """
        try:
            node = parser.parse(content, **kwargs)

            # パーサーがUnifiedParserBaseベースの場合、詳細な結果を取得
            if isinstance(parser, UnifiedParserBase):
                return parser.create_parse_result(node, **kwargs)
            else:
                # 基本的なParseResultを作成
                return ParseResult(
                    node=node, parser_type=parser.get_parser_type(), metadata=kwargs
                )

        except Exception as e:
            self.logger.error(f"Parse error with {parser.get_parser_type()}: {e}")
            return ParseResult(
                node=error_node(f"Parse error: {e}"),
                parser_type=parser.get_parser_type(),
                errors=[f"解析エラー: {str(e)}"],
            )

    def parse(
        self,
        content: Union[str, List[str]],
        parser_type: Optional[str] = None,
        **kwargs: Any,
    ) -> ParseResult:
        """解析実行（外部API）

        Args:
            content: 解析対象のコンテンツ
            parser_type: 使用するパーサーの種類（Noneの場合は自動選択）
            **kwargs: パーサーに渡す追加パラメータ

        Returns:
            解析結果
        """
        if parser_type and parser_type in self._parsers:
            # 指定されたパーサーで解析
            parser = self._parsers[parser_type]
            return self._try_parse(parser, content, **kwargs)
        else:
            # 自動選択でフォールバック付き解析
            return self.parse_with_fallback(content, **kwargs)

    def _update_stats(self, parser_type: str, success: bool) -> None:
        """解析統計の更新"""
        if parser_type not in self._parse_stats:
            self._parse_stats[parser_type] = 0

        if success:
            self._parse_stats[parser_type] += 1

    def _update_fallback_stats(self, parser_type: str) -> None:
        """フォールバック統計の更新"""
        if parser_type not in self._fallback_stats:
            self._fallback_stats[parser_type] = 0

        self._fallback_stats[parser_type] += 1

    def get_registered_parsers(self) -> Dict[str, int]:
        """登録済みパーサーの情報を取得

        Returns:
            パーサー種類と優先度のマッピング
        """
        return self._parser_priorities.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """解析統計情報を取得

        Returns:
            統計情報のディクショナリ
        """
        return {
            "registered_parsers": len(self._parsers),
            "parser_order": self._parser_order.copy(),
            "parse_success_count": self._parse_stats.copy(),
            "fallback_count": self._fallback_stats.copy(),
        }

    def clear_statistics(self) -> None:
        """統計情報をクリア"""
        self._parse_stats.clear()
        self._fallback_stats.clear()
        self.logger.info("Statistics cleared")

    def validate_parser_compatibility(
        self, content: Union[str, List[str]]
    ) -> Dict[str, bool]:
        """すべてのパーサーの互換性をチェック

        Args:
            content: テスト対象のコンテンツ

        Returns:
            パーサー種類と互換性のマッピング
        """
        compatibility = {}

        for parser_type, parser in self._parsers.items():
            try:
                compatibility[parser_type] = parser.can_parse(content)
            except Exception as e:
                self.logger.warning(
                    f"Compatibility check failed for {parser_type}: {e}"
                )
                compatibility[parser_type] = False

        return compatibility


# グローバルコーディネーターインスタンス（シングルトン的使用）
_global_coordinator = None


def get_global_coordinator() -> UnifiedParsingCoordinator:
    """グローバルコーディネーターを取得

    Returns:
        グローバルコーディネーターインスタンス
    """
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = UnifiedParsingCoordinator()
    return _global_coordinator


def register_default_parsers() -> None:
    """デフォルトパーサーの登録"""
    coordinator = get_global_coordinator()

    # 循環インポート回避のための遅延インポート
    from .specialized import (
        UnifiedBlockParser,
        UnifiedContentParser,
        UnifiedKeywordParser,
        UnifiedListParser,
        UnifiedMarkdownParser,
    )

    # 優先度順でパーサーを登録
    coordinator.register_parser(UnifiedBlockParser(), priority=100)
    coordinator.register_parser(UnifiedKeywordParser(), priority=90)
    coordinator.register_parser(UnifiedMarkdownParser(), priority=80)
    coordinator.register_parser(UnifiedListParser(), priority=70)
    coordinator.register_parser(UnifiedContentParser(), priority=10)  # フォールバック

    coordinator.logger.info("Default parsers registered successfully")
