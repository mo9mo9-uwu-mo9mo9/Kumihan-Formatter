"""統合Parser システム

Issue #912: Parser系統合リファクタリング完了
28個のParserファイル → 8個に統合・重複除去

統合完了:
- MainParser: 全パーサー統括（parser.py + streaming_parser.py + parser_utils.py）
- UnifiedKeywordParser: 3重複KeywordParser統合
- UnifiedListParser: 4重複ListParser統合
- UnifiedBlockParser: 2重複BlockParser統合
- UnifiedMarkdownParser: 2重複MarkdownParser統合

提供機能:
- 統一されたパーサーインターフェース
- プロトコルベース設計による型安全性
- 自動パーサー選択・並列処理
- ストリーミング解析サポート
- 後方互換性維持
"""

import warnings

# 基底クラス・プロトコル
from .base import (
    CachingMixin,
    CompositeMixin,
    ErrorHandlingMixin,
    FormattingMixin,
    PatternMatchingMixin,
    PerformanceMixin,
    UnifiedParserBase,
    ValidationMixin,
)
from .base.parser_protocols import (
    AnyParser,
    BlockParserProtocol,
    CompositeParserProtocol,
    KeywordParserProtocol,
    ListParserProtocol,
    MarkdownParserProtocol,
    ParserProtocol,
    StreamingParserProtocol,
)
from .coordinator import (
    UnifiedParsingCoordinator,
    get_global_coordinator,
    register_default_parsers,
)

# Issue #912: メイン統合パーサー（最優先）
from .main_parser import (
    MainParser,
    Parser,
    StreamingParser,
    parse_file,
    parse_stream,
    parse_text,
)
from .protocols import (
    CoordinatorProtocol,
    FormatterProtocol,
    ParseResult,
    ParserType,
    ProcessorProtocol,
    ValidatorProtocol,
)

# 特化パーサー（Phase 2B完了）
from .specialized import (
    UnifiedBlockParser,
    UnifiedContentParser,
    UnifiedKeywordParser,
    UnifiedListParser,
    UnifiedMarkdownParser,
)

# ユーティリティ（Phase 2Bで実装予定）
# from .utilities import (
#     ParserValidator,
#     ContentFormatter,
#     ParseResultAnalyzer,
# )

__all__ = [
    # === Issue #912: 統合メインパーサー（最優先） ===
    "MainParser",  # 新しい統合パーサー
    "Parser",  # 後方互換性エイリアス
    "StreamingParser",  # ストリーミング機能
    # === ユーティリティ関数 ===
    "parse_text",  # 便利関数
    "parse_file",  # ファイル解析
    "parse_stream",  # ストリーム解析
    # === 統合済み専門パーサー ===
    "UnifiedKeywordParser",  # キーワード解析（3重複統合）
    "UnifiedListParser",  # リスト解析（4重複統合）
    "UnifiedBlockParser",  # ブロック解析（2重複統合）
    "UnifiedMarkdownParser",  # Markdown解析（2重複統合）
    "UnifiedContentParser",  # コンテンツ解析
    # === プロトコル・型定義 ===
    "KeywordParserProtocol",  # キーワード専用
    "ListParserProtocol",  # リスト専用
    "BlockParserProtocol",  # ブロック専用
    "MarkdownParserProtocol",  # Markdown専用
    "StreamingParserProtocol",  # ストリーミング専用
    "CompositeParserProtocol",  # 複合パーサー専用
    "AnyParser",  # 型エイリアス
    "ValidatorProtocol",
    "FormatterProtocol",
    "CoordinatorProtocol",
    "ProcessorProtocol",
    "ParseResult",
    "ParserType",
    # === 基底クラス・Mixin ===
    "UnifiedParserBase",
    "CachingMixin",
    "ValidationMixin",
    "PatternMatchingMixin",
    "FormattingMixin",
    "ErrorHandlingMixin",
    "PerformanceMixin",
    "CompositeMixin",
    # === コーディネーター ===
    "UnifiedParsingCoordinator",
    "get_global_coordinator",
    "register_default_parsers",
]

# バージョン情報
__version__ = "3.0.0"  # Issue #912完了
__phase__ = "Parser統合完了 - 28個→8個統合・重複除去"

# 後方互換性エイリアス（段階的移行用）
KeywordParser = UnifiedKeywordParser  # core.keyword_parser.KeywordParser
ListParser = UnifiedListParser  # core.list_parser.ListParser
BlockParser = UnifiedBlockParser  # core.block_parser.BlockParser
MarkdownParser = UnifiedMarkdownParser  # core.markdown_parser.MarkdownParser
BaseParser = UnifiedParserBase  # 基本パーサー

# 後方互換性サポート追加
__all__.extend(
    [
        "KeywordParser",  # 既存インポート対応
        "ListParser",  # 既存インポート対応
        "BlockParser",  # 既存インポート対応
        "MarkdownParser",  # 既存インポート対応
        "BaseParser",  # 既存インポート対応
    ]
)


# 移行情報
def get_migration_info() -> dict:
    """Parser統合の移行情報を取得"""
    return {
        "version": __version__,
        "phase": __phase__,
        "consolidation": {
            "before": "28個のParserファイル",
            "after": "8個のParserファイル",
            "eliminated_duplicates": [
                "KeywordParser x3 → UnifiedKeywordParser",
                "ListParser x4 → UnifiedListParser",
                "BlockParser x2 → UnifiedBlockParser",
                "MarkdownParser x2 → UnifiedMarkdownParser",
            ],
        },
        "migration_guide": {
            "old_import": "from kumihan_formatter.parser import Parser",
            "new_import": "from kumihan_formatter.core.parsing import Parser",
            "note": "既存のインポートパスも動作します（後方互換性維持）",
        },
        "performance": {
            "parallel_processing": "10K行以上で自動並列化",
            "streaming_support": "大容量ファイル対応",
            "memory_optimized": "メモリ使用量最適化",
        },
    }


# 後方互換性のための警告


def _show_migration_success() -> None:
    """Parser統合完了の通知"""
    warnings.warn(
        f"Parser系統合リファクタリング完了 (Issue #912)\n"
        f"28個のファイル → 8個に統合、重複除去済み\n"
        f"バージョン: {__version__}\n"
        f"詳細は get_migration_info() で確認可能",
        UserWarning,
        stacklevel=3,
    )


# デバッグ用: モジュール読み込み時の情報出力
def _get_module_info() -> dict:
    """モジュール情報の取得（デバッグ用）"""
    return {
        "version": __version__,
        "phase": __phase__,
        "available_protocols": [
            "ParserProtocol",
            "ValidatorProtocol",
            "FormatterProtocol",
            "CoordinatorProtocol",
            "ProcessorProtocol",
        ],
        "base_classes": ["UnifiedParserBase", "CompositeMixin"],
        "coordinator": "UnifiedParsingCoordinator",
    }
