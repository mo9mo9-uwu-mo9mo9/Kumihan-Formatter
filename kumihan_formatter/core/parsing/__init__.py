"""統一パーサーモジュール

Issue #880 Phase 2: パーサー階層整理
既存の分散したパーサー機能を統合した新しいアーキテクチャ

このモジュールは以下を提供します:
- 統一されたパーサーインターフェース
- プロトコルベース設計による型安全性
- 自動パーサー選択機能
- フォールバック機能付き解析
- パフォーマンス監視・キャッシング
"""

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
from .coordinator import (
    UnifiedParsingCoordinator,
    get_global_coordinator,
    register_default_parsers,
)
from .protocols import (
    CoordinatorProtocol,
    FormatterProtocol,
    ParseResult,
    ParserProtocol,
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
    # プロトコル・型定義
    "ParserProtocol",
    "ValidatorProtocol",
    "FormatterProtocol",
    "CoordinatorProtocol",
    "ProcessorProtocol",
    "ParseResult",
    "ParserType",
    # 基底クラス・Mixin
    "UnifiedParserBase",
    "CachingMixin",
    "ValidationMixin",
    "PatternMatchingMixin",
    "FormattingMixin",
    "ErrorHandlingMixin",
    "PerformanceMixin",
    "CompositeMixin",
    # コーディネーター
    "UnifiedParsingCoordinator",
    "get_global_coordinator",
    "register_default_parsers",
    # 特化パーサー（Phase 2B完了）
    "UnifiedBlockParser",
    "UnifiedKeywordParser",
    "UnifiedListParser",
    "UnifiedMarkdownParser",
    "UnifiedContentParser",
    # ユーティリティ（Phase 2Bで追加予定）
    # "ParserValidator",
    # "ContentFormatter",
    # "ParseResultAnalyzer",
]

# バージョン情報
__version__ = "2.0.0"
__phase__ = "2A - Base Infrastructure"

# 後方互換性のための警告
import warnings


def _show_migration_warning() -> None:
    """既存パーサーから新統一パーサーへの移行警告"""
    warnings.warn(
        "Kumihan-Formatter パーサーが新しい統一アーキテクチャに移行されました。\n"
        "既存のパーサーインポートは Phase 2C で非推奨になります。\n"
        "新しい kumihan_formatter.core.parsing モジュールの使用を推奨します。",
        FutureWarning,
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
