"""
日本語メッセージ機能のテスト

Japanese Error Message Testing
Issue #492 Phase 5A対応 - 日本語エラーメッセージ統一機能の体系的テスト実装
"""

from pathlib import Path

import pytest

from kumihan_formatter.core.error_handling.error_types import UserFriendlyError
from kumihan_formatter.core.error_handling.message_catalog import MessageCatalog


class TestJapaneseMessageCatalog:
    """日本語メッセージカタログ全体のテスト"""

    def test_catalog_availability(self):
        """カタログが利用可能かテスト"""
        # Given/When
        catalog = MessageCatalog()

        # Then
        assert catalog is not None
        assert hasattr(catalog, "templates")

    def test_catalog_instantiation(self):
        """MessageCatalogのインスタンス化テスト"""
        # Given/When
        catalog = MessageCatalog()

        # Then
        assert catalog is not None
        assert hasattr(catalog, "get_file_system_error")


class TestMessageCatalog:
    """メッセージカタログのテスト"""

    def test_get_file_error_message(self):
        """ファイルエラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_file_system_error("file_not_found", file_path="test.txt")

        # Then
        assert isinstance(message, UserFriendlyError)
        assert "test.txt" in message.user_message

    def test_get_encoding_error_message(self):
        """エンコーディングエラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_encoding_error("encoding_mismatch")

        # Then
        assert isinstance(message, UserFriendlyError)

    def test_get_syntax_error_message(self):
        """構文エラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_syntax_error("unclosed_decoration")

        # Then
        assert isinstance(message, UserFriendlyError)

    def test_get_rendering_error_message(self):
        """レンダリングエラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_rendering_error("template_not_found")

        # Then
        assert isinstance(message, UserFriendlyError)

    def test_get_unknown_error_message(self):
        """未知のエラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When - 存在しないエラータイプでもデフォルトが返される
        message = catalog.get_file_system_error("unknown_error_key")

        # Then
        assert isinstance(message, UserFriendlyError)

    def test_message_localization(self):
        """メッセージローカライゼーションのテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_file_system_error("file_not_found")

        # Then
        assert isinstance(message, UserFriendlyError)
        # 日本語メッセージが含まれることを確認
        assert len(message.user_message) > 0

    def test_message_with_context(self):
        """コンテキスト付きメッセージのテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_file_system_error(
            "permission_denied", file_path="/restricted/file.txt"
        )

        # Then
        assert isinstance(message, UserFriendlyError)
        assert "file.txt" in message.user_message

    def test_template_message_constants_availability(self):
        """メッセージテンプレート定数の利用可能性テスト"""
        # When/Then
        assert hasattr(MessageCatalog, "FILE_SYSTEM_MESSAGES")
        assert hasattr(MessageCatalog, "ENCODING_MESSAGES")
        assert hasattr(MessageCatalog, "SYNTAX_MESSAGES")
        assert hasattr(MessageCatalog, "RENDERING_MESSAGES")
        assert hasattr(MessageCatalog, "SYSTEM_MESSAGES")

    def test_error_solution_inclusion(self):
        """エラー解決方法の含有テスト"""
        # Given
        catalog = MessageCatalog()

        # When
        error = catalog.get_file_system_error("file_not_found")

        # Then
        assert hasattr(error, "solution")
        assert error.solution is not None
        assert hasattr(error.solution, "quick_fix")
        assert hasattr(error.solution, "detailed_steps")

    def test_error_categorization(self):
        """エラーカテゴリ化のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        file_error = catalog.get_file_system_error("file_not_found")
        encoding_error = catalog.get_encoding_error("encoding_mismatch")

        # Then
        assert file_error.category.value == "file_system"
        assert encoding_error.category.value == "encoding"

    def test_error_level_assignment(self):
        """エラーレベル割り当てのテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        error = catalog.get_file_system_error("file_not_found")

        # Then
        assert hasattr(error, "level")
        assert error.level is not None

    def test_multiple_error_types(self):
        """複数エラータイプのテスト"""
        # Given
        catalog = MessageCatalog()

        # When/Then - 各エラータイプメソッドが正常に動作する
        file_error = catalog.get_file_system_error("file_not_found")
        encoding_error = catalog.get_encoding_error("encoding_mismatch")
        syntax_error = catalog.get_syntax_error("unclosed_decoration")
        render_error = catalog.get_rendering_error("template_not_found")
        system_error = catalog.get_system_error("memory_error")

        errors = [file_error, encoding_error, syntax_error, render_error, system_error]
        for error in errors:
            assert isinstance(error, UserFriendlyError)
            assert len(error.user_message) > 0
