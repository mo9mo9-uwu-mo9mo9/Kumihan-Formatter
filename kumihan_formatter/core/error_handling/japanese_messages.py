"""
日本語エラーメッセージ 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - japanese_messages.py分割
"""

from .japanese_messages_factory import create_user_friendly_error

# 分割されたモジュールからインポート
from .message_catalog import MessageCatalog
from .user_guidance_provider import UserGuidanceProvider

# 後方互換性のためのエイリアス
JapaneseMessageCatalog = MessageCatalog

# モジュールレベルのエクスポート
__all__ = [
    "JapaneseMessageCatalog",
    "MessageCatalog",
    "UserGuidanceProvider",
    "create_user_friendly_error",
]
