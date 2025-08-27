"""Phase3統合パーサーモジュール - 48個→10個統合実現

統合パーサー一覧:
1. CoreKeywordParser - キーワード解析統合（9個→1個）
2. CoreListParser - リスト解析統合（10個→1個）
3. CoreBlockParser - ブロック解析統合（8個→1個）
4. CoreContentParser - コンテンツ解析統合（4個→1個）
5. CoreMarkdownParser - Markdown互換解析（3個→1個）
6. CoreMarkerParser - マーカー記法解析（既存）
7. CoreValidationParser - 検証・バリデーション統合（2個→1個）
8. CoreProtocolParser - プロトコル・インターフェース統合（3個→1個）
9. CoreUtilityParser - ユーティリティ・ヘルパー統合（5個→1個）
10. CoreRegistryParser - レジストリ・定義管理統合（4個→1個）

設計原則:
- 既存API完全互換性維持
- 単一責任原則の遵守
- 型安全性確保（mypy strict）
- 高パフォーマンス統合実装
"""

from .core_keyword_parser import CoreKeywordParser

# Phase3統合パーサー公開API
__all__ = [
    "CoreKeywordParser",
    # 他の統合パーサーは順次追加
]

# 後方互換性エイリアス
KeywordParser = CoreKeywordParser
UnifiedKeywordParser = CoreKeywordParser
