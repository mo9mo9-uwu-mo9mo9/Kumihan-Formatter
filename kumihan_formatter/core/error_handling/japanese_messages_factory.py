"""
日本語メッセージ ファクトリー

エラーメッセージ・ガイダンス生成の統合インターフェース
Issue #492 Phase 5A - japanese_messages.py分割
"""

from typing import Any

from .error_types import UserFriendlyError
from .message_catalog import MessageCatalog


def create_user_friendly_error(
    category: str, error_type: str, **context: Any
) -> UserFriendlyError:
    """ユーザーフレンドリーエラーを作成する便利関数"""

    if category == "file_system":
        return MessageCatalog.get_file_system_error(error_type, **context)
    elif category == "encoding":
        return MessageCatalog.get_encoding_error(error_type, **context)
    elif category == "syntax":
        return MessageCatalog.get_syntax_error(error_type, **context)
    elif category == "rendering":
        return MessageCatalog.get_rendering_error(error_type, **context)
    elif category == "system":
        return MessageCatalog.get_system_error(error_type, **context)
    else:
        return MessageCatalog.get_system_error("unexpected_error", **context)


class JapaneseMessagesFactory:
    """日本語メッセージ作成のためのファクトリークラス

    新しいコンポーネントの統合インターフェースを提供
    """

    @staticmethod
    def create_file_system_error(error_type: str, **context: Any) -> UserFriendlyError:
        """ファイルシステムエラーを作成"""
        return MessageCatalog.get_file_system_error(error_type, **context)

    @staticmethod
    def create_encoding_error(error_type: str, **context: Any) -> UserFriendlyError:
        """エンコーディングエラーを作成"""
        return MessageCatalog.get_encoding_error(error_type, **context)

    @staticmethod
    def create_syntax_error(error_type: str, **context: Any) -> UserFriendlyError:
        """構文エラーを作成"""
        return MessageCatalog.get_syntax_error(error_type, **context)

    @staticmethod
    def create_rendering_error(error_type: str, **context: Any) -> UserFriendlyError:
        """レンダリングエラーを作成"""
        return MessageCatalog.get_rendering_error(error_type, **context)

    @staticmethod
    def create_system_error(error_type: str, **context: Any) -> UserFriendlyError:
        """システムエラーを作成"""
        return MessageCatalog.get_system_error(error_type, **context)
