"""
メッセージカタログのテスト

Important Tier Phase 2-1対応 - Issue #593
メッセージカタログ機能の体系的テスト実装
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_types import (
    ErrorCategory,
    ErrorLevel,
    UserFriendlyError,
)
from kumihan_formatter.core.error_handling.message_catalog import MessageCatalog


class TestMessageCatalog:
    """メッセージカタログのテストクラス"""

    def test_init(self):
        """初期化テスト"""
        # When
        catalog = MessageCatalog()

        # Then
        assert catalog.templates is not None
        assert hasattr(catalog, "FILE_SYSTEM_MESSAGES")
        assert hasattr(catalog, "ENCODING_MESSAGES")
        assert hasattr(catalog, "SYNTAX_MESSAGES")

    def test_backward_compatibility_attributes(self):
        """後方互換性属性のテスト"""
        # Given
        catalog = MessageCatalog()

        # Then
        assert hasattr(catalog, "FILE_SYSTEM_MESSAGES")
        assert hasattr(catalog, "ENCODING_MESSAGES")
        assert hasattr(catalog, "SYNTAX_MESSAGES")
        assert hasattr(catalog, "RENDERING_MESSAGES")
        assert hasattr(catalog, "SYSTEM_MESSAGES")

    def test_get_file_system_error_file_not_found(self):
        """ファイル未発見エラー取得のテスト"""
        # When
        error = MessageCatalog.get_file_system_error(
            "file_not_found", file_path="/path/to/missing.txt"
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.level == ErrorLevel.ERROR
        assert error.category == ErrorCategory.FILE_SYSTEM
        assert "missing.txt" in error.user_message
        assert len(error.solution.detailed_steps) > 0

    def test_get_file_system_error_permission_denied(self):
        """権限拒否エラー取得のテスト"""
        # When
        error = MessageCatalog.get_file_system_error(
            "permission_denied", file_path="/protected/file.txt", operation="write"
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert "file.txt" in error.user_message
        assert error.category == ErrorCategory.FILE_SYSTEM
        assert len(error.solution.detailed_steps) > 0

    def test_get_file_system_error_without_file_path(self):
        """ファイルパスなしでのファイルシステムエラー取得テスト"""
        # When
        error = MessageCatalog.get_file_system_error("file_not_found")

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.FILE_SYSTEM

    def test_get_file_system_error_unknown_type(self):
        """未知のファイルシステムエラータイプのテスト"""
        # When
        error = MessageCatalog.get_file_system_error(
            "unknown_file_error", file_path="test.txt"
        )

        # Then
        # デフォルトのfile_not_foundエラーが返される
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.FILE_SYSTEM

    def test_get_encoding_error(self):
        """エンコーディングエラー取得のテスト"""
        # When
        error = MessageCatalog.get_encoding_error(
            "decode_error",
            encoding="utf-8",
            file_path="japanese.txt",
            suggested_encodings=["shift_jis", "cp932"],
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.ENCODING
        assert "japanese.txt" in error.user_message
        assert len(error.solution.detailed_steps) > 0

    def test_get_encoding_error_with_line_info(self):
        """行情報付きエンコーディングエラー取得のテスト"""
        # When
        error = MessageCatalog.get_encoding_error(
            "decode_error",
            encoding="utf-8",
            file_path="test.txt",
            line_number=42,
            byte_position=128,
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert "test.txt" in error.user_message

    def test_get_syntax_error(self):
        """構文エラー取得のテスト"""
        # When
        error = MessageCatalog.get_syntax_error(
            "invalid_decoration",
            line_number=15,
            content=";;;invalid;;;",
            suggested_fix=";;;太字;;;",
            file_path="test.md",
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.SYNTAX
        assert len(error.solution.detailed_steps) > 0

    def test_get_syntax_error_unclosed_decoration(self):
        """未閉装飾構文エラー取得のテスト"""
        # When
        error = MessageCatalog.get_syntax_error(
            "unclosed_decoration",
            line_number=20,
            content=";;;太字;;テキスト",
            file_path="document.md",
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert len(error.solution.detailed_steps) > 0

    def test_get_rendering_error(self):
        """レンダリングエラー取得のテスト"""
        # When
        error = MessageCatalog.get_rendering_error(
            "template_not_found",
            template_name="custom_template.jinja2",
            template_path="/templates/custom_template.jinja2",
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.RENDERING
        assert len(error.solution.detailed_steps) > 0

    def test_get_rendering_error_with_context(self):
        """コンテキスト付きレンダリングエラー取得のテスト"""
        # When
        error = MessageCatalog.get_rendering_error(
            "template_syntax_error",
            template_name="main.jinja2",
            line_number=10,
            error_details="Undefined variable: missing_var",
            context_vars=["title", "content", "author"],
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert len(error.user_message) > 0

    def test_get_system_error(self):
        """システムエラー取得のテスト"""
        # When
        error = MessageCatalog.get_system_error(
            "memory_error",
            available_memory="512MB",
            required_memory="1GB",
            operation="large_file_processing",
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.SYSTEM
        assert error.level == ErrorLevel.ERROR
        assert len(error.user_message) > 0

    def test_get_system_error_disk_space(self):
        """ディスク容量システムエラー取得のテスト"""
        # When
        error = MessageCatalog.get_system_error(
            "disk_full",
            available_space="100MB",
            required_space="500MB",
            target_path="/tmp",
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert len(error.user_message) > 0

    def test_message_template_inheritance(self):
        """メッセージテンプレート継承のテスト"""
        # Given
        catalog = MessageCatalog()

        # Then
        # クラス属性がテンプレートから継承されている
        assert catalog.FILE_SYSTEM_MESSAGES is not None
        assert catalog.ENCODING_MESSAGES is not None
        assert len(catalog.FILE_SYSTEM_MESSAGES) > 0

    def test_integration_complete_error_creation(self):
        """統合テスト: 完全なエラー作成フロー"""
        # Given
        catalog = MessageCatalog()

        # When - 複雑なファイルエラーシナリオ
        error = catalog.get_file_system_error(
            "permission_denied",
            file_path="/protected/document.md",
            operation="write",
            user="testuser",
            required_permissions="rw-",
            current_permissions="r--",
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.FILE_SYSTEM
        assert error.level == ErrorLevel.ERROR
        assert "document.md" in error.user_message
        assert len(error.solution.detailed_steps) > 0
        assert error.error_code.startswith("E")
