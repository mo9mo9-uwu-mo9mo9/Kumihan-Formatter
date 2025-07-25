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
        assert error.category == ErrorCategory.FILE
        assert "missing.txt" in error.message
        assert len(error.solutions) > 0

    def test_get_file_system_error_permission_denied(self):
        """権限拒否エラー取得のテスト"""
        # When
        error = MessageCatalog.get_file_system_error(
            "permission_denied", file_path="/protected/file.txt", operation="write"
        )

        # Then
        assert isinstance(error, UserFriendlyError)
        assert "file.txt" in error.message
        assert error.category == ErrorCategory.FILE
        assert any("権限" in str(solution) for solution in error.solutions)

    def test_get_file_system_error_without_file_path(self):
        """ファイルパスなしでのファイルシステムエラー取得テスト"""
        # When
        error = MessageCatalog.get_file_system_error("file_not_found")

        # Then
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.FILE

    def test_get_file_system_error_unknown_type(self):
        """未知のファイルシステムエラータイプのテスト"""
        # When
        error = MessageCatalog.get_file_system_error(
            "unknown_file_error", file_path="test.txt"
        )

        # Then
        # デフォルトのfile_not_foundエラーが返される
        assert isinstance(error, UserFriendlyError)
        assert error.category == ErrorCategory.FILE

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
        assert "utf-8" in error.message
        assert "japanese.txt" in error.message
        assert any("shift_jis" in str(solution) for solution in error.solutions)

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
        assert "42行目" in error.message
        assert "128" in error.message or "byte" in error.message.lower()

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
        assert "15行目" in error.message
        assert ";;;invalid;;;" in error.message
        assert any("太字" in str(solution) for solution in error.solutions)

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
        assert "20行目" in error.message
        assert ";;;太字;;テキスト" in error.message
        assert any(";;;" in str(solution) for solution in error.solutions)

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
        assert error.category == ErrorCategory.RENDER
        assert "custom_template.jinja2" in error.message
        assert len(error.solutions) > 0

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
        assert "main.jinja2" in error.message
        assert "10行目" in error.message
        assert "missing_var" in error.message

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
        assert error.level == ErrorLevel.CRITICAL
        assert "512MB" in error.message
        assert "1GB" in error.message

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
        assert "100MB" in error.message
        assert "500MB" in error.message
        assert "/tmp" in error.message

    def test_get_message_generic(self):
        """汎用メッセージ取得のテスト"""
        # When
        message = MessageCatalog().get_message("file_not_found", file_path="test.txt")

        # Then
        assert isinstance(message, str)
        assert "test.txt" in message
        assert len(message) > 0

    def test_get_message_with_formatting(self):
        """フォーマット付きメッセージ取得のテスト"""
        # When
        message = MessageCatalog().get_message(
            "encoding_error",
            encoding="utf-8",
            file_path="document.txt",
            line_number=25,
            suggestion="shift_jisを試してください",
        )

        # Then
        assert "utf-8" in message
        assert "document.txt" in message
        assert "25" in message
        assert "shift_jis" in message

    def test_format_error_with_solutions(self):
        """解決策付きエラーフォーマットのテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        formatted = catalog.format_error_with_solutions(
            message="テストエラーが発生しました",
            solutions=[
                "解決策1: ファイルパスを確認してください",
                "解決策2: エンコーディングを変更してください",
                "解決策3: 権限を確認してください",
            ],
        )

        # Then
        assert "テストエラーが発生しました" in formatted
        assert "解決策1" in formatted
        assert "解決策2" in formatted
        assert "解決策3" in formatted

    def test_create_error_with_custom_code(self):
        """カスタムコード付きエラー作成のテスト"""
        # When
        error = MessageCatalog.create_error_with_code(
            error_code="E001",
            message="カスタムエラーメッセージ",
            category=ErrorCategory.PARSE,
            level=ErrorLevel.WARNING,
            solutions=["カスタム解決策"],
        )

        # Then
        assert error.error_code == "E001"
        assert error.message == "カスタムエラーメッセージ"
        assert error.category == ErrorCategory.PARSE
        assert error.level == ErrorLevel.WARNING
        assert "カスタム解決策" in [str(s) for s in error.solutions]

    def test_localize_message(self):
        """メッセージローカライゼーションのテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        localized = catalog.localize_message(
            "File {file_path} not found at line {line_number}",
            file_path="テスト.txt",
            line_number=10,
        )

        # Then
        assert "テスト.txt" in localized
        assert "10" in localized

    def test_get_error_category_display_name(self):
        """エラーカテゴリ表示名取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When/Then
        assert catalog.get_category_display_name(ErrorCategory.FILE) == "ファイル"
        assert (
            catalog.get_category_display_name(ErrorCategory.ENCODING)
            == "エンコーディング"
        )
        assert catalog.get_category_display_name(ErrorCategory.SYNTAX) == "構文"
        assert catalog.get_category_display_name(ErrorCategory.RENDER) == "レンダリング"
        assert catalog.get_category_display_name(ErrorCategory.SYSTEM) == "システム"

    def test_get_error_level_display_name(self):
        """エラーレベル表示名取得のテスト"""
        # Given
        catalog = MessageCatalog()

        # When/Then
        assert catalog.get_level_display_name(ErrorLevel.INFO) == "情報"
        assert catalog.get_level_display_name(ErrorLevel.WARNING) == "警告"
        assert catalog.get_level_display_name(ErrorLevel.ERROR) == "エラー"
        assert catalog.get_level_display_name(ErrorLevel.CRITICAL) == "重大"

    def test_message_template_inheritance(self):
        """メッセージテンプレート継承のテスト"""
        # Given
        catalog = MessageCatalog()

        # Then
        # クラス属性がテンプレートから継承されている
        assert catalog.FILE_SYSTEM_MESSAGES is not None
        assert catalog.ENCODING_MESSAGES is not None
        assert len(catalog.FILE_SYSTEM_MESSAGES) > 0

    def test_error_code_generation(self):
        """エラーコード生成のテスト"""
        # Given
        catalog = MessageCatalog()

        # When
        code1 = catalog.generate_error_code("file_not_found")
        code2 = catalog.generate_error_code("encoding_error")
        code3 = catalog.generate_error_code("file_not_found")  # 同じタイプ

        # Then
        assert code1.startswith("E")
        assert code2.startswith("E")
        assert code1 == code3  # 同じエラータイプは同じコード

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
        assert error.category == ErrorCategory.FILE
        assert error.level == ErrorLevel.ERROR
        assert "document.md" in error.message
        assert "write" in error.message or "書き込み" in error.message
        assert len(error.solutions) > 0
        assert error.error_code.startswith("E")

        # 解決策が適切に含まれている
        solutions_text = " ".join(str(s) for s in error.solutions)
        assert "chmod" in solutions_text or "権限" in solutions_text
