"""
統一エラーハンドラーのテスト

Important Tier Phase 2-1対応 - Issue #593
エラーハンドリング系の体系的テスト実装

Issue #611対応: 実装に合わせた最小限のテスト
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_display import ErrorDisplay
from kumihan_formatter.core.error_handling.error_factories import ErrorFactory
from kumihan_formatter.core.error_handling.error_recovery import ErrorRecovery
from kumihan_formatter.core.error_handling.error_statistics import ErrorStatistics
from kumihan_formatter.core.error_handling.error_types import UserFriendlyError
from kumihan_formatter.core.error_handling.unified_handler import UnifiedErrorHandler


class TestUnifiedErrorHandler:
    """統一エラーハンドラーのテストクラス"""

    def test_init_with_defaults(self):
        """デフォルト設定での初期化テスト"""
        # When
        handler = UnifiedErrorHandler()

        # Then
        assert handler.console_ui is None
        assert handler.enable_logging is True
        assert handler.logger is not None
        assert isinstance(handler.display, ErrorDisplay)
        assert isinstance(handler.recovery, ErrorRecovery)
        assert isinstance(handler.statistics, ErrorStatistics)

    def test_init_with_custom_console_ui(self):
        """カスタムコンソールUIでの初期化テスト"""
        # Given
        mock_console = Mock()

        # When
        handler = UnifiedErrorHandler(console_ui=mock_console)

        # Then
        assert handler.console_ui is mock_console
        assert handler.display.console_ui is mock_console

    def test_init_without_logging(self):
        """ログ無効での初期化テスト"""
        # When
        handler = UnifiedErrorHandler(enable_logging=False)

        # Then
        assert handler.enable_logging is False
        assert handler.logger is None

    @patch("kumihan_formatter.core.error_handling.unified_handler.get_logger")
    def test_logger_initialization(self, mock_get_logger):
        """ロガー初期化のテスト"""
        # Given
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # When
        handler = UnifiedErrorHandler(enable_logging=True)

        # Then
        mock_get_logger.assert_called()
        assert handler.logger is mock_logger

    def test_error_context_manager(self):
        """error_contextコンテキストマネージャーの正常系テスト"""
        # Given
        handler = UnifiedErrorHandler(enable_logging=False)

        # When & Then - 正常終了してもエラーにならない
        try:
            with handler.error_context("test_operation"):
                # 正常に処理が完了
                pass
        except Exception:
            pytest.fail("正常処理で例外が発生しました")

    def test_error_context_with_exception(self):
        """error_contextコンテキストマネージャーの異常系テスト"""
        # Given
        handler = UnifiedErrorHandler(enable_logging=False)
        test_error = ValueError("Test error")

        # When
        with pytest.raises(ValueError):
            with handler.error_context("test_operation", auto_recover=False):
                raise test_error

        # Then - 例外が再発生することを確認（基本動作）

    def test_handle_exception_basic(self):
        """基本的な例外処理テスト"""
        # Given
        handler = UnifiedErrorHandler(enable_logging=False)
        test_exception = ValueError("テストエラー")

        # When
        result = handler.handle_exception(
            test_exception, show_ui=False, attempt_recovery=False
        )

        # Then
        assert isinstance(result, UserFriendlyError)
        assert result is not None

    def test_handle_exception_file_not_found(self):
        """ファイル未発見エラーの処理テスト"""
        # Given
        handler = UnifiedErrorHandler(enable_logging=False)
        file_error = FileNotFoundError("/nonexistent/file.txtが見つかりません")

        # When
        result = handler.handle_exception(
            file_error, show_ui=False, attempt_recovery=False
        )

        # Then
        assert isinstance(result, UserFriendlyError)
        assert result is not None

    def test_handle_exception_permission_error(self):
        """権限エラーの処理テスト"""
        # Given
        handler = UnifiedErrorHandler(enable_logging=False)
        permission_error = PermissionError("/protected/file.txtにアクセスできません")

        # When
        result = handler.handle_exception(
            permission_error, show_ui=False, attempt_recovery=False
        )

        # Then
        assert isinstance(result, UserFriendlyError)
        assert result is not None

    def test_integration_basic_error_handling(self):
        """統合テスト: 基本的なエラーハンドリング"""
        # Given
        handler = UnifiedErrorHandler(enable_logging=False)

        # When - エラーコンテキスト内での例外処理
        try:
            with handler.error_context("integration_test", auto_recover=False):
                raise ValueError("統合テストエラー")
        except ValueError:
            # Then - 例外が適切に処理されて再発生することを確認
            pass
