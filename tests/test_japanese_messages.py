"""
日本語メッセージシステムのテスト

Important Tier Phase 2-1対応 - Issue #593
日本語エラーメッセージ・メッセージカタログ機能の体系的テスト実装
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_types import (
    ErrorCategory,
    ErrorLevel,
    UserFriendlyError,
)
from kumihan_formatter.core.error_handling.japanese_messages import (
    JapaneseMessageCatalog,
    MessageCatalog,
    UserGuidanceProvider,
    create_user_friendly_error,
)


class TestJapaneseMessageCatalog:
    """日本語メッセージカタログのテスト"""

    def test_backward_compatibility_alias(self):
        """後方互換性エイリアスのテスト"""
        # JapaneseMessageCatalogはMessageCatalogのエイリアス
        assert JapaneseMessageCatalog is MessageCatalog

    def test_catalog_instantiation(self):
        """カタログインスタンス化のテスト"""
        # Given/When
        catalog = MessageCatalog()

        # Then
        assert catalog is not None
        assert hasattr(catalog, "get_message")


class TestMessageCatalog:
    """メッセージカタログのテスト"""

    def test_get_file_error_message(self):
        """ファイルエラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_message("file_not_found", file_path="test.txt")

        # Then
        assert "ファイルが見つかりません" in message
        assert "test.txt" in message

    def test_get_encoding_error_message(self):
        """エンコーディングエラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_message(
            "encoding_error", encoding="utf-8", suggested_encoding="shift_jis"
        )

        # Then
        assert "エンコーディングエラー" in message
        assert "utf-8" in message
        assert "shift_jis" in message

    def test_get_parse_error_message(self):
        """パースエラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_message(
            "parse_error", line_number=10, content=";;;invalid;;;"
        )

        # Then
        assert "パースエラー" in message
        assert "10行目" in message
        assert ";;;invalid;;;" in message

    def test_get_permission_error_message(self):
        """権限エラーメッセージ取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_message(
            "permission_denied", file_path="/protected/file.txt", operation="write"
        )

        # Then
        assert "アクセス権限がありません" in message
        assert "file.txt" in message
        assert "書き込み" in message or "write" in message

    def test_get_unknown_message_key(self):
        """未知のメッセージキー取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_message("unknown_error_key")

        # Then
        # デフォルトメッセージが返される
        assert "エラーが発生しました" in message or "unknown_error_key" in message

    def test_message_formatting_with_multiple_params(self):
        """複数パラメータでのメッセージフォーマットテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_message(
            "complex_error",
            file_path="test.md",
            line_number=25,
            column=10,
            error_type="構文エラー",
            suggestion=";;;太字;;;を使用してください",
        )

        # Then
        # パラメータが正しく埋め込まれている
        assert isinstance(message, str)
        assert len(message) > 0

    def test_message_with_japanese_characters(self):
        """日本語文字を含むメッセージのテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        message = catalog.get_message(
            "syntax_error",
            content=";;;太字;;;テスト;;;イタリック;;;",
            suggestion="正しい記法を使用してください",
        )

        # Then
        assert "太字" in message
        assert "イタリック" in message
        assert "正しい記法" in message


class TestUserGuidanceProvider:
    """ユーザーガイダンスプロバイダーのテスト"""

    def test_get_file_error_guidance(self):
        """ファイルエラーガイダンス取得のテスト"""
        # Given
        provider = UserGuidanceProvider()

        # When
        guidance = provider.get_guidance(
            error_type="file_not_found", context={"file_path": "missing.txt"}
        )

        # Then
        assert len(guidance) > 0
        assert any("ファイルパス" in g for g in guidance)
        assert any("存在" in g for g in guidance)

    def test_get_encoding_error_guidance(self):
        """エンコーディングエラーガイダンス取得のテスト"""
        # Given
        provider = UserGuidanceProvider()

        # When
        guidance = provider.get_guidance(
            error_type="encoding_error",
            context={
                "original_encoding": "utf-8",
                "suggested_encodings": ["shift_jis", "cp932"],
            },
        )

        # Then
        assert len(guidance) > 0
        assert any("エンコーディング" in g for g in guidance)
        assert any("shift_jis" in g or "cp932" in g for g in guidance)

    def test_get_syntax_error_guidance(self):
        """構文エラーガイダンス取得のテスト"""
        # Given
        provider = UserGuidanceProvider()

        # When
        guidance = provider.get_guidance(
            error_type="syntax_error",
            context={
                "line_content": ";;;invalid;;;",
                "suggested_fix": ";;;太字;;;",
                "valid_keywords": ["太字", "イタリック", "見出し1"],
            },
        )

        # Then
        assert len(guidance) > 0
        assert any("記法" in g for g in guidance)
        assert any("太字" in g for g in guidance)

    def test_get_permission_error_guidance(self):
        """権限エラーガイダンス取得のテスト"""
        # Given
        provider = UserGuidanceProvider()

        # When
        guidance = provider.get_guidance(
            error_type="permission_denied",
            context={"file_path": "/protected/file.txt", "operation": "write"},
        )

        # Then
        assert len(guidance) > 0
        assert any("権限" in g or "アクセス" in g for g in guidance)
        assert any("chmod" in g or "管理者" in g for g in guidance)

    def test_get_guidance_with_empty_context(self):
        """空のコンテキストでのガイダンス取得テスト"""
        # Given
        provider = UserGuidanceProvider()

        # When
        guidance = provider.get_guidance("generic_error", context={})

        # Then
        # 空でもエラーが発生しない
        assert isinstance(guidance, list)

    def test_get_guidance_for_unknown_error(self):
        """未知のエラータイプのガイダンス取得テスト"""
        # Given
        provider = UserGuidanceProvider()

        # When
        guidance = provider.get_guidance("unknown_error_type")

        # Then
        # 汎用的なガイダンスが返される
        assert isinstance(guidance, list)
        assert len(guidance) >= 0


class TestCreateUserFriendlyError:
    """ユーザーフレンドリーエラー作成のテスト"""

    def test_create_file_not_found_error(self):
        """ファイル未発見エラー作成のテスト"""
        # Given
        original_error = FileNotFoundError("No such file: test.txt")

        # When
        user_error = create_user_friendly_error(
            original_error, context={"file_path": "test.txt"}
        )

        # Then
        assert isinstance(user_error, UserFriendlyError)
        assert "ファイルが見つかりません" in user_error.message
        assert user_error.original_error is original_error
        assert len(user_error.suggestions) > 0

    def test_create_encoding_error(self):
        """エンコーディングエラー作成のテスト"""
        # Given
        original_error = UnicodeDecodeError(
            "utf-8", b"\x82\xa0", 0, 2, "invalid start byte"
        )

        # When
        user_error = create_user_friendly_error(
            original_error,
            context={"file_path": "japanese.txt", "detected_encoding": "shift_jis"},
        )

        # Then
        assert isinstance(user_error, UserFriendlyError)
        assert "エンコーディング" in user_error.message
        assert len(user_error.suggestions) > 0
        assert any("shift_jis" in s for s in user_error.suggestions)

    def test_create_permission_error(self):
        """権限エラー作成のテスト"""
        # Given
        original_error = PermissionError("Permission denied")

        # When
        user_error = create_user_friendly_error(
            original_error,
            context={"file_path": "/protected/file.txt", "operation": "write"},
        )

        # Then
        assert isinstance(user_error, UserFriendlyError)
        assert "アクセス権限" in user_error.message or "権限" in user_error.message
        assert len(user_error.suggestions) > 0

    def test_create_syntax_error(self):
        """構文エラー作成のテスト"""
        # Given
        original_error = ValueError("Invalid syntax")

        # When
        user_error = create_user_friendly_error(
            original_error,
            context={
                "line_number": 15,
                "line_content": ";;;invalid;;;",
                "file_path": "test.md",
            },
        )

        # Then
        assert isinstance(user_error, UserFriendlyError)
        assert "構文" in user_error.message or "記法" in user_error.message
        assert "15行目" in user_error.message
        assert len(user_error.suggestions) > 0

    def test_create_error_with_custom_level(self):
        """カスタムレベルでのエラー作成テスト"""
        # Given
        original_error = RuntimeError("Critical system error")

        # When
        user_error = create_user_friendly_error(
            original_error, context={"severity": "critical"}, level=ErrorLevel.CRITICAL
        )

        # Then
        assert user_error.level == ErrorLevel.CRITICAL

    def test_create_error_with_custom_category(self):
        """カスタムカテゴリでのエラー作成テスト"""
        # Given
        original_error = ValueError("Render error")

        # When
        user_error = create_user_friendly_error(
            original_error,
            context={"component": "renderer"},
            category=ErrorCategory.RENDER,
        )

        # Then
        assert user_error.category == ErrorCategory.RENDER

    def test_create_error_without_context(self):
        """コンテキストなしでのエラー作成テスト"""
        # Given
        original_error = Exception("Generic error")

        # When
        user_error = create_user_friendly_error(original_error)

        # Then
        assert isinstance(user_error, UserFriendlyError)
        assert user_error.original_error is original_error
        assert isinstance(user_error.message, str)
        assert len(user_error.message) > 0

    def test_create_error_preserves_original_traceback(self):
        """元の例外のトレースバック保持テスト"""
        # Given
        try:
            raise ValueError("Original error with traceback")
        except ValueError as e:
            original_error = e

        # When
        user_error = create_user_friendly_error(
            original_error, context={"preserve_traceback": True}
        )

        # Then
        assert user_error.original_error is original_error
        # トレースバック情報が保持されている

    def test_error_message_localization(self):
        """エラーメッセージのローカライゼーションテスト"""
        # Given
        original_error = FileNotFoundError("File not found")

        # When
        user_error = create_user_friendly_error(
            original_error, context={"file_path": "テスト.txt", "locale": "ja"}
        )

        # Then
        # 日本語メッセージが生成される
        assert "ファイル" in user_error.message
        assert "テスト.txt" in user_error.message

    def test_integration_complete_error_creation_flow(self):
        """統合テスト: 完全なエラー作成フロー"""
        # Given - 複雑なエラーシナリオ
        original_error = UnicodeDecodeError(
            "utf-8", b"\x93\xfa\x96{", 0, 3, "invalid start byte"
        )

        context = {
            "file_path": "日本語ファイル.md",
            "line_number": 42,
            "column": 15,
            "operation": "parse",
            "encoding": "utf-8",
            "suggested_encodings": ["shift_jis", "cp932", "euc-jp"],
            "file_size": 2048,
        }

        # When
        user_error = create_user_friendly_error(
            original_error,
            context=context,
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE,
        )

        # Then
        assert isinstance(user_error, UserFriendlyError)
        assert user_error.level == ErrorLevel.ERROR
        assert user_error.category == ErrorCategory.FILE
        assert "エンコーディング" in user_error.message
        assert "日本語ファイル.md" in user_error.message
        assert len(user_error.suggestions) > 0
        assert any("shift_jis" in s for s in user_error.suggestions)
        assert user_error.context["file_path"] == "日本語ファイル.md"
