"""
japanese_messages.py分割のためのテスト

TDD: 分割後の新しいモジュール構造のテスト
Issue #492 Phase 5A - japanese_messages.py分割
"""

from unittest.mock import Mock

import pytest


class TestMessageCatalog:
    """メッセージカタログのテスト"""

    def test_message_catalog_import(self):
        """RED: メッセージカタログモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.message_catalog import (
                MessageCatalog,
            )

    def test_message_catalog_initialization(self):
        """RED: メッセージカタログ初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.message_catalog import (
                MessageCatalog,
            )

            catalog = MessageCatalog()

    def test_get_file_system_error_method(self):
        """RED: ファイルシステムエラー取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.message_catalog import (
                MessageCatalog,
            )

            error = MessageCatalog.get_file_system_error("file_not_found", "test.txt")

    def test_get_encoding_error_method(self):
        """RED: エンコーディングエラー取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.message_catalog import (
                MessageCatalog,
            )

            error = MessageCatalog.get_encoding_error("decode_error", "test.txt")

    def test_get_syntax_error_method(self):
        """RED: 構文エラー取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.message_catalog import (
                MessageCatalog,
            )

            error = MessageCatalog.get_syntax_error("invalid_marker", 10)

    def test_get_rendering_error_method(self):
        """RED: レンダリングエラー取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.message_catalog import (
                MessageCatalog,
            )

            error = MessageCatalog.get_rendering_error("template_not_found", "custom")

    def test_get_system_error_method(self):
        """RED: システムエラー取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.message_catalog import (
                MessageCatalog,
            )

            error = MessageCatalog.get_system_error("memory_error")


class TestErrorMessageTemplates:
    """エラーメッセージテンプレートのテスト"""

    def test_error_message_templates_import(self):
        """RED: エラーメッセージテンプレートモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.error_message_templates import (
                ErrorMessageTemplates,
            )

    def test_error_message_templates_initialization(self):
        """RED: エラーメッセージテンプレート初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.error_message_templates import (
                ErrorMessageTemplates,
            )

            templates = ErrorMessageTemplates()

    def test_file_system_messages(self):
        """RED: ファイルシステムメッセージテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.error_message_templates import (
                ErrorMessageTemplates,
            )

            messages = ErrorMessageTemplates.FILE_SYSTEM_MESSAGES

    def test_encoding_messages(self):
        """RED: エンコーディングメッセージテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.error_message_templates import (
                ErrorMessageTemplates,
            )

            messages = ErrorMessageTemplates.ENCODING_MESSAGES

    def test_syntax_messages(self):
        """RED: 構文メッセージテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.error_message_templates import (
                ErrorMessageTemplates,
            )

            messages = ErrorMessageTemplates.SYNTAX_MESSAGES

    def test_rendering_messages(self):
        """RED: レンダリングメッセージテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.error_message_templates import (
                ErrorMessageTemplates,
            )

            messages = ErrorMessageTemplates.RENDERING_MESSAGES

    def test_system_messages(self):
        """RED: システムメッセージテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.error_message_templates import (
                ErrorMessageTemplates,
            )

            messages = ErrorMessageTemplates.SYSTEM_MESSAGES


class TestUserGuidanceProvider:
    """ユーザーガイダンスプロバイダーのテスト"""

    def test_user_guidance_provider_import(self):
        """RED: ユーザーガイダンスプロバイダーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.user_guidance_provider import (
                UserGuidanceProvider,
            )

    def test_user_guidance_provider_initialization(self):
        """RED: ユーザーガイダンスプロバイダー初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.user_guidance_provider import (
                UserGuidanceProvider,
            )

            provider = UserGuidanceProvider()

    def test_get_guidance_for_error_method(self):
        """RED: エラー用ガイダンス取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.user_guidance_provider import (
                UserGuidanceProvider,
            )

            mock_error = Mock()
            guidance = UserGuidanceProvider.get_guidance_for_error(mock_error)

    def test_get_beginner_tips_method(self):
        """RED: 初心者向けティップス取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.user_guidance_provider import (
                UserGuidanceProvider,
            )

            tips = UserGuidanceProvider.get_beginner_tips("convert")

    def test_common_questions(self):
        """RED: よくある質問テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.user_guidance_provider import (
                UserGuidanceProvider,
            )

            questions = UserGuidanceProvider.COMMON_QUESTIONS

    def test_troubleshooting_steps(self):
        """RED: トラブルシューティング手順テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.user_guidance_provider import (
                UserGuidanceProvider,
            )

            steps = UserGuidanceProvider.TROUBLESHOOTING_STEPS


class TestJapaneseMessagesFactory:
    """日本語メッセージファクトリーのテスト"""

    def test_japanese_messages_factory_import(self):
        """RED: 日本語メッセージファクトリーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.japanese_messages_factory import (
                create_user_friendly_error,
            )

    def test_create_user_friendly_error_function(self):
        """RED: ユーザーフレンドリーエラー作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.japanese_messages_factory import (
                create_user_friendly_error,
            )

            error = create_user_friendly_error(
                "file_system", "file_not_found", file_path="test.txt"
            )

    def test_create_japanese_message_catalog(self):
        """RED: 日本語メッセージカタログ作成テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.error_handling.japanese_messages_factory import (
                JapaneseMessagesFactory,
            )

            factory = JapaneseMessagesFactory()


class TestOriginalJapaneseMessages:
    """元のjapanese_messagesモジュールとの互換性テスト"""

    def test_original_japanese_messages_still_works(self):
        """元のjapanese_messagesが正常動作することを確認"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            JapaneseMessageCatalog,
            UserGuidanceProvider,
            create_user_friendly_error,
        )

        # 基本クラスが存在することを確認
        assert JapaneseMessageCatalog is not None
        assert UserGuidanceProvider is not None

        # ファクトリー関数が存在することを確認
        assert callable(create_user_friendly_error)

    def test_japanese_message_catalog_initialization(self):
        """元のJapaneseMessageCatalog初期化テスト"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            JapaneseMessageCatalog,
        )

        # クラスメソッドが存在することを確認
        assert hasattr(JapaneseMessageCatalog, "get_file_system_error")
        assert hasattr(JapaneseMessageCatalog, "get_encoding_error")
        assert hasattr(JapaneseMessageCatalog, "get_syntax_error")
        assert hasattr(JapaneseMessageCatalog, "get_rendering_error")
        assert hasattr(JapaneseMessageCatalog, "get_system_error")

    def test_user_guidance_provider_initialization(self):
        """元のUserGuidanceProvider初期化テスト"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            UserGuidanceProvider,
        )

        # クラス属性が存在することを確認
        assert hasattr(UserGuidanceProvider, "COMMON_QUESTIONS")
        assert hasattr(UserGuidanceProvider, "TROUBLESHOOTING_STEPS")

        # クラスメソッドが存在することを確認
        assert hasattr(UserGuidanceProvider, "get_guidance_for_error")
        assert hasattr(UserGuidanceProvider, "get_beginner_tips")

    def test_message_templates_exist(self):
        """メッセージテンプレートが存在することを確認"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            JapaneseMessageCatalog,
        )

        # メッセージテンプレートが存在することを確認
        assert hasattr(JapaneseMessageCatalog, "FILE_SYSTEM_MESSAGES")
        assert hasattr(JapaneseMessageCatalog, "ENCODING_MESSAGES")
        assert hasattr(JapaneseMessageCatalog, "SYNTAX_MESSAGES")
        assert hasattr(JapaneseMessageCatalog, "RENDERING_MESSAGES")
        assert hasattr(JapaneseMessageCatalog, "SYSTEM_MESSAGES")

    def test_create_user_friendly_error_function(self):
        """create_user_friendly_error関数のテスト"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            create_user_friendly_error,
        )

        # 基本的な動作確認
        error = create_user_friendly_error(
            "file_system", "file_not_found", file_path="test.txt"
        )
        assert error is not None
        assert hasattr(error, "user_message")
        assert hasattr(error, "solution")

    def test_file_system_error_creation(self):
        """ファイルシステムエラー作成のテスト"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            JapaneseMessageCatalog,
        )

        error = JapaneseMessageCatalog.get_file_system_error(
            "file_not_found", "test.txt"
        )
        assert error is not None
        assert "ファイルが見つかりません" in error.user_message
        assert error.solution is not None
        assert len(error.solution.detailed_steps) > 0

    def test_encoding_error_creation(self):
        """エンコーディングエラー作成のテスト"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            JapaneseMessageCatalog,
        )

        error = JapaneseMessageCatalog.get_encoding_error("decode_error", "test.txt")
        assert error is not None
        assert "文字化け" in error.user_message
        assert error.solution is not None

    def test_syntax_error_creation(self):
        """構文エラー作成のテスト"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            JapaneseMessageCatalog,
        )

        error = JapaneseMessageCatalog.get_syntax_error("invalid_marker", 10)
        assert error is not None
        assert "記法エラー" in error.user_message
        assert "10行目" in error.user_message

    def test_user_guidance_functionality(self):
        """ユーザーガイダンス機能のテスト"""
        from kumihan_formatter.core.error_handling.japanese_messages import (
            UserGuidanceProvider,
        )

        tips = UserGuidanceProvider.get_beginner_tips("convert")
        assert isinstance(tips, list)
        assert len(tips) > 0

        # よくある質問の確認
        assert "how_to_fix_encoding" in UserGuidanceProvider.COMMON_QUESTIONS
        assert "what_is_kumihan_syntax" in UserGuidanceProvider.COMMON_QUESTIONS
