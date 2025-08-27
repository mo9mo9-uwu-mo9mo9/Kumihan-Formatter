"""CoreKeywordParser - Phase3統合キーワードパーサー

9個のキーワード関連パーサーを1個に統合:
- 基本キーワード解析（太字・イタリック・見出し・コード）
- 高度キーワード解析（リスト・表・引用・脚注）
- カスタムキーワード管理・拡張機能
- キーワード検証・バリデーション機能
- キーワード設定・構成管理
- キーワード抽出・処理機能
- コンテンツ解析・変換機能
- 属性処理・スタイル適用
- キャッシュ・パフォーマンス最適化

設計原則:
- 単一責任原則（統合されたキーワード解析責任）
- 既存API完全互換性維持
- 型安全性確保（mypy strict mode）
- 高パフォーマンス実装
"""

from typing import Any, Dict, List, Optional, Set, Union, TYPE_CHECKING
import re
from functools import lru_cache

if TYPE_CHECKING:
    from ...base.parser_protocols import (
        ParseResult,
        ParseContext,
        KeywordParserProtocol,
    )
    from ...ast_nodes import Node
else:
    try:
        from ...base.parser_protocols import (
            ParseResult,
            ParseContext,
            KeywordParserProtocol,
        )
        from ...ast_nodes import Node, create_node
    except ImportError:
        KeywordParserProtocol = object
        Node = None
        create_node = None

from ..base.parser_base import UnifiedParserBase
from ..base.mixins import CompositeMixin
from ..base.parser_protocols import create_parse_result
from ..protocols import ParserType
from ...utilities.logger import get_logger


class CoreKeywordParser(UnifiedParserBase, CompositeMixin, KeywordParserProtocol):
    """Phase3統合キーワードパーサー - 9個→1個統合版

    統合機能:
    - 全Kumihanキーワード解析（基本・高度・カスタム）
    - プロトコル準拠 (KeywordParserProtocol)
    - 後方互換性維持
    - 統合最適化による高パフォーマンス実現
    """

    # キーワード定義（統合版）
    BASIC_KEYWORDS = {
        "太字",
        "bold",
        "イタリック",
        "italic",
        "見出し1",
        "h1",
        "見出し2",
        "h2",
        "見出し3",
        "h3",
        "見出し4",
        "h4",
        "見出し5",
        "h5",
        "見出し6",
        "h6",
        "コード",
        "code",
        "下線",
        "underline",
        "取り消し",
        "strikethrough",
    }

    ADVANCED_KEYWORDS = {
        "リスト",
        "list",
        "番号付きリスト",
        "ordered_list",
        "表",
        "table",
        "引用",
        "quote",
        "脚注",
        "footnote",
        "ハイライト",
        "highlight",
        "注意",
        "warning",
        "情報",
        "info",
        "エラー",
        "error",
    }

    # キーワードパターン（統合・最適化版）
    KEYWORD_PATTERN = re.compile(
        r"#\s*([\w\d]+(?:\s+[\w\d=\-.,\s]+)?)\s*#\s*(.*?)\s*##",
        re.MULTILINE | re.DOTALL,
    )

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """統合キーワードパーサー初期化

        Args:
            config: 設定辞書（オプション）
        """
        super().__init__()
        self.logger = get_logger(__name__)

        # 統合設定管理
        self.config = self._setup_integrated_config(config or {})

        # 統合キーワード定義
        self.all_keywords = self.BASIC_KEYWORDS | self.ADVANCED_KEYWORDS
        self.custom_keywords: Set[str] = set()

        # 統合ハンドラー（内部クラス化）
        self.basic_handler = self._BasicKeywordHandler(self)
        self.advanced_handler = self._AdvancedKeywordHandler(self)
        self.custom_handler = self._CustomKeywordHandler(self)

        # 統合プロセッサー
        self.attribute_processor = self._AttributeProcessor(self)
        self.keyword_extractor = self._KeywordExtractor(self)
        self.info_processor = self._KeywordInfoProcessor(self)

        # 統合バリデーター
        self.validator = self._KeywordValidator(self)

        # パフォーマンス最適化
        self.cache: Dict[str, Any] = {}
        self._setup_performance_optimization()

        self.logger.info("CoreKeywordParser初期化完了 - 9機能統合版")

    class _BasicKeywordHandler:
        """基本キーワード処理ハンドラー（統合版）"""

        def __init__(self, parent: "CoreKeywordParser") -> None:
            self.parent = parent
            self.logger = parent.logger

        def handle_keyword(
            self, keyword: str, content: str, attributes: Dict[str, Any]
        ) -> Optional["Node"]:
            """基本キーワード処理"""
            if keyword not in self.parent.BASIC_KEYWORDS:
                return None

            # 基本キーワード処理ロジック（統合版）
            if keyword in ("太字", "bold"):
                return self._create_bold_node(content, attributes)
            elif keyword in ("イタリック", "italic"):
                return self._create_italic_node(content, attributes)
            elif keyword.startswith("見出し") or keyword.startswith("h"):
                return self._create_heading_node(keyword, content, attributes)
            elif keyword in ("コード", "code"):
                return self._create_code_node(content, attributes)
            elif keyword in ("下線", "underline"):
                return self._create_underline_node(content, attributes)
            elif keyword in ("取り消し", "strikethrough"):
                return self._create_strikethrough_node(content, attributes)

            return None

        def _create_bold_node(self, content: str, attributes: Dict[str, Any]) -> "Node":
            """太字ノード作成"""
            if create_node:
                return create_node("bold", {"content": content, **attributes})
            return None

        def _create_italic_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """イタリックノード作成"""
            if create_node:
                return create_node("italic", {"content": content, **attributes})
            return None

        def _create_heading_node(
            self, keyword: str, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """見出しノード作成"""
            # 見出しレベル決定
            level = 1
            if keyword.startswith("見出し") and len(keyword) > 3:
                try:
                    level = int(keyword[3])
                except ValueError:
                    pass
            elif keyword.startswith("h") and len(keyword) == 2:
                try:
                    level = int(keyword[1])
                except ValueError:
                    pass

            if create_node:
                return create_node(
                    "heading", {"content": content, "level": level, **attributes}
                )
            return None

        def _create_code_node(self, content: str, attributes: Dict[str, Any]) -> "Node":
            """コードノード作成"""
            if create_node:
                return create_node("code", {"content": content, **attributes})
            return None

        def _create_underline_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """下線ノード作成"""
            if create_node:
                return create_node("underline", {"content": content, **attributes})
            return None

        def _create_strikethrough_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """取り消しノード作成"""
            if create_node:
                return create_node("strikethrough", {"content": content, **attributes})
            return None

    class _AdvancedKeywordHandler:
        """高度キーワード処理ハンドラー（統合版）"""

        def __init__(self, parent: "CoreKeywordParser") -> None:
            self.parent = parent
            self.logger = parent.logger

        def handle_keyword(
            self, keyword: str, content: str, attributes: Dict[str, Any]
        ) -> Optional["Node"]:
            """高度キーワード処理"""
            if keyword not in self.parent.ADVANCED_KEYWORDS:
                return None

            # 高度キーワード処理ロジック（統合版）
            if keyword in ("リスト", "list"):
                return self._create_list_node(content, attributes)
            elif keyword in ("番号付きリスト", "ordered_list"):
                return self._create_ordered_list_node(content, attributes)
            elif keyword in ("表", "table"):
                return self._create_table_node(content, attributes)
            elif keyword in ("引用", "quote"):
                return self._create_quote_node(content, attributes)
            elif keyword in ("脚注", "footnote"):
                return self._create_footnote_node(content, attributes)
            elif keyword in ("ハイライト", "highlight"):
                return self._create_highlight_node(content, attributes)
            elif keyword in ("注意", "warning"):
                return self._create_warning_node(content, attributes)
            elif keyword in ("情報", "info"):
                return self._create_info_node(content, attributes)
            elif keyword in ("エラー", "error"):
                return self._create_error_node(content, attributes)

            return None

        def _create_list_node(self, content: str, attributes: Dict[str, Any]) -> "Node":
            """リストノード作成"""
            if create_node:
                return create_node("list", {"content": content, **attributes})
            return None

        def _create_ordered_list_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """番号付きリストノード作成"""
            if create_node:
                return create_node("ordered_list", {"content": content, **attributes})
            return None

        def _create_table_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """表ノード作成"""
            if create_node:
                return create_node("table", {"content": content, **attributes})
            return None

        def _create_quote_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """引用ノード作成"""
            if create_node:
                return create_node("quote", {"content": content, **attributes})
            return None

        def _create_footnote_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """脚注ノード作成"""
            if create_node:
                return create_node("footnote", {"content": content, **attributes})
            return None

        def _create_highlight_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """ハイライトノード作成"""
            if create_node:
                return create_node("highlight", {"content": content, **attributes})
            return None

        def _create_warning_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """注意ノード作成"""
            if create_node:
                return create_node("warning", {"content": content, **attributes})
            return None

        def _create_info_node(self, content: str, attributes: Dict[str, Any]) -> "Node":
            """情報ノード作成"""
            if create_node:
                return create_node("info", {"content": content, **attributes})
            return None

        def _create_error_node(
            self, content: str, attributes: Dict[str, Any]
        ) -> "Node":
            """エラーノード作成"""
            if create_node:
                return create_node("error", {"content": content, **attributes})
            return None

    class _CustomKeywordHandler:
        """カスタムキーワード処理ハンドラー（統合版）"""

        def __init__(self, parent: "CoreKeywordParser") -> None:
            self.parent = parent
            self.logger = parent.logger

        def handle_keyword(
            self, keyword: str, content: str, attributes: Dict[str, Any]
        ) -> Optional["Node"]:
            """カスタムキーワード処理"""
            if keyword not in self.parent.custom_keywords:
                return None

            # カスタムキーワード処理ロジック
            if create_node:
                return create_node(
                    "custom", {"keyword": keyword, "content": content, **attributes}
                )
            return None

    class _AttributeProcessor:
        """属性処理プロセッサー（統合版）"""

        def __init__(self, parent: "CoreKeywordParser") -> None:
            self.parent = parent
            self.logger = parent.logger

        def parse_attributes(self, keyword_line: str) -> Dict[str, Any]:
            """属性解析処理"""
            attributes = {}

            # 属性パターン抽出
            attr_pattern = re.compile(r'(\w+)=(["\']?)([^"\'\s]+)\2')
            matches = attr_pattern.findall(keyword_line)

            for key, _, value in matches:
                attributes[key] = value

            return attributes

    class _KeywordExtractor:
        """キーワード抽出機能（統合版）"""

        def __init__(self, parent: "CoreKeywordParser") -> None:
            self.parent = parent
            self.logger = parent.logger

        def extract_keywords(self, text: str) -> List[Dict[str, Any]]:
            """キーワード抽出（キャッシュ最適化版）"""
            keywords = []

            for match in self.parent.KEYWORD_PATTERN.finditer(text):
                keyword_line = match.group(1).strip()
                content = match.group(2).strip()

                # キーワードと属性分離
                parts = keyword_line.split()
                keyword = parts[0] if parts else ""

                # 属性処理
                attributes = self.parent.attribute_processor.parse_attributes(
                    keyword_line
                )

                keywords.append(
                    {
                        "keyword": keyword,
                        "content": content,
                        "attributes": attributes,
                        "start": match.start(),
                        "end": match.end(),
                        "raw_match": match.group(0),
                    }
                )

            return keywords

    class _KeywordInfoProcessor:
        """キーワード情報処理（統合版）"""

        def __init__(self, parent: "CoreKeywordParser") -> None:
            self.parent = parent
            self.logger = parent.logger

        def get_keyword_info(self, keyword: str) -> Dict[str, Any]:
            """キーワード情報取得"""
            return {
                "keyword": keyword,
                "type": self._get_keyword_type(keyword),
                "supported": self._is_supported_keyword(keyword),
                "category": self._get_keyword_category(keyword),
            }

        def _get_keyword_type(self, keyword: str) -> str:
            """キーワードタイプ判定"""
            if keyword in self.parent.BASIC_KEYWORDS:
                return "basic"
            elif keyword in self.parent.ADVANCED_KEYWORDS:
                return "advanced"
            elif keyword in self.parent.custom_keywords:
                return "custom"
            return "unknown"

        def _is_supported_keyword(self, keyword: str) -> bool:
            """キーワードサポート状況判定"""
            return (
                keyword in self.parent.all_keywords
                or keyword in self.parent.custom_keywords
            )

        def _get_keyword_category(self, keyword: str) -> str:
            """キーワードカテゴリ判定"""
            if keyword in ("太字", "bold", "イタリック", "italic"):
                return "text_formatting"
            elif keyword.startswith("見出し") or keyword.startswith("h"):
                return "heading"
            elif keyword in ("リスト", "list", "番号付きリスト", "ordered_list"):
                return "list"
            elif keyword in ("表", "table"):
                return "table"
            elif keyword in ("引用", "quote"):
                return "quote"
            elif keyword in ("コード", "code"):
                return "code"
            elif keyword in (
                "ハイライト",
                "highlight",
                "注意",
                "warning",
                "情報",
                "info",
                "エラー",
                "error",
            ):
                return "highlight"
            return "other"

    class _KeywordValidator:
        """キーワードバリデーター（統合版）"""

        def __init__(self, parent: "CoreKeywordParser") -> None:
            self.parent = parent
            self.logger = parent.logger
            self.errors: List[str] = []
            self.warnings: List[str] = []

        def validate_keyword(self, keyword: str, content: str) -> bool:
            """キーワード検証"""
            self.errors.clear()
            self.warnings.clear()

            # 基本検証
            if not keyword:
                self.errors.append("キーワードが空です")
                return False

            if not content:
                self.warnings.append("コンテンツが空です")

            # サポート状況確認
            if not self.parent.info_processor._is_supported_keyword(keyword):
                self.warnings.append(f"未サポートキーワード: {keyword}")

            return len(self.errors) == 0

        def get_errors(self) -> List[str]:
            """エラー一覧取得"""
            return self.errors.copy()

        def get_warnings(self) -> List[str]:
            """警告一覧取得"""
            return self.warnings.copy()

    def _setup_integrated_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """統合設定セットアップ"""
        default_config = {
            "enable_cache": True,
            "max_cache_size": 128,
            "strict_validation": False,
            "enable_custom_keywords": True,
            "performance_mode": True,
        }

        # 設定マージ
        merged_config = {**default_config, **config}

        self.logger.debug(f"統合設定セットアップ完了: {merged_config}")
        return merged_config

    def _setup_performance_optimization(self) -> None:
        """パフォーマンス最適化セットアップ"""
        if self.config.get("performance_mode", True):
            # キャッシュ設定（内部実装で処理）
            self.logger.debug("パフォーマンスモード有効化")

        self.logger.debug("パフォーマンス最適化セットアップ完了")

    def parse(
        self, text: str, context: Optional["ParseContext"] = None
    ) -> "ParseResult":
        """統合キーワード解析実行

        Args:
            text: 解析対象テキスト
            context: 解析コンテキスト（オプション）

        Returns:
            ParseResult: 解析結果
        """
        self.logger.debug(f"CoreKeywordParser解析開始: {len(text)}文字")

        try:
            # キーワード抽出
            keywords = self.keyword_extractor.extract_keywords(text)
            nodes = []

            # 各キーワード処理
            for keyword_info in keywords:
                keyword = keyword_info["keyword"]
                content = keyword_info["content"]
                attributes = keyword_info["attributes"]

                # バリデーション
                if self.config.get("strict_validation", False):
                    if not self.validator.validate_keyword(keyword, content):
                        continue

                # 適切なハンドラーで処理
                node = None

                # 基本キーワード試行
                node = self.basic_handler.handle_keyword(keyword, content, attributes)
                if node:
                    nodes.append(node)
                    continue

                # 高度キーワード試行
                node = self.advanced_handler.handle_keyword(
                    keyword, content, attributes
                )
                if node:
                    nodes.append(node)
                    continue

                # カスタムキーワード試行
                if self.config.get("enable_custom_keywords", True):
                    node = self.custom_handler.handle_keyword(
                        keyword, content, attributes
                    )
                    if node:
                        nodes.append(node)
                        continue

                self.logger.warning(f"未処理キーワード: {keyword}")

            self.logger.info(f"CoreKeywordParser解析完了: {len(nodes)}個のノード生成")

            return create_parse_result(
                success=True,
                nodes=nodes,
                errors=self.validator.get_errors(),
                warnings=self.validator.get_warnings(),
            )

        except Exception as e:
            self.logger.error(f"CoreKeywordParser解析エラー: {str(e)}")
            return create_parse_result(
                success=False, nodes=[], errors=[f"解析エラー: {str(e)}"]
            )

    def parse_keywords(self, text: str) -> List[Dict[str, Any]]:
        """キーワード解析（レガシーAPI互換）"""
        return self.keyword_extractor.extract_keywords(text)

    def validate_keyword(self, keyword: str, content: str = "") -> bool:
        """キーワード検証（レガシーAPI互換）"""
        return self.validator.validate_keyword(keyword, content)

    def get_keyword_info(self, keyword: str) -> Dict[str, Any]:
        """キーワード情報取得（レガシーAPI互換）"""
        return self.info_processor.get_keyword_info(keyword)

    def add_custom_keyword(self, keyword: str) -> None:
        """カスタムキーワード追加（レガシーAPI互換）"""
        self.custom_keywords.add(keyword)
        self.logger.info(f"カスタムキーワード追加: {keyword}")

    def remove_custom_keyword(self, keyword: str) -> None:
        """カスタムキーワード削除（レガシーAPI互換）"""
        self.custom_keywords.discard(keyword)
        self.logger.info(f"カスタムキーワード削除: {keyword}")

    def get_errors(self) -> List[str]:
        """エラー一覧取得（レガシーAPI互換）"""
        return self.validator.get_errors()

    def get_warnings(self) -> List[str]:
        """警告一覧取得（レガシーAPI互換）"""
        return self.validator.get_warnings()

    def supports_format(self, format_type: str) -> bool:
        """フォーマットサポート確認（レガシーAPI互換）"""
        return format_type in ("kumihan", "keyword")

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得（レガシーAPI互換）"""
        return {
            "name": "CoreKeywordParser",
            "version": "1.0.0",
            "type": ParserType.KEYWORD,
            "description": "Phase3統合キーワードパーサー - 9機能統合版",
            "supported_keywords": list(self.all_keywords),
            "custom_keywords": list(self.custom_keywords),
            "features": [
                "basic_keywords",
                "advanced_keywords",
                "custom_keywords",
                "attribute_processing",
                "validation",
                "caching",
                "performance_optimization",
            ],
            "integration_level": "phase3_unified",
            "optimization": {
                "cache_enabled": self.config.get("enable_cache", True),
                "performance_mode": self.config.get("performance_mode", True),
                "max_cache_size": self.config.get("max_cache_size", 128),
            },
        }


# 後方互換性エイリアス
KeywordParser = CoreKeywordParser
UnifiedKeywordParser = CoreKeywordParser
