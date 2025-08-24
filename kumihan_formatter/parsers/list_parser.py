"""List Parser - 統合リスト解析エンジン（レガシー版）

⚠️ 廃止予定 - このファイルはlist/パッケージに移行されました
新しい場所: kumihan_formatter.parsers.list.UnifiedListParser

責任分離による改善:
- list/list_parser.py: メインクラス
- list/list_handlers.py: 処理ロジック
- list/list_utils.py: ユーティリティ関数
"""

# 後方互換性のためのインポート（新しい場所から）
from .list.list_parser import UnifiedListParser

# エイリアス
ListParser = UnifiedListParser

__all__ = ["UnifiedListParser", "ListParser"]
