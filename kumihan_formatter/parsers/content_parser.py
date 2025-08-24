"""Content Parser - 統合コンテンツ解析エンジン（レガシー版）

⚠️ 廃止予定 - このファイルはcontent/パッケージに移行されました
新しい場所: kumihan_formatter.parsers.content.UnifiedContentParser

責任分離による改善:
- content/content_parser.py: メインクラス
- content/content_handlers.py: 処理ロジック
- content/content_utils.py: ユーティリティ関数
"""

# 後方互換性のためのインポート（新しい場所から）
from .content.content_parser import UnifiedContentParser

# エイリアス
ContentParser = UnifiedContentParser

__all__ = ["UnifiedContentParser", "ContentParser"]
