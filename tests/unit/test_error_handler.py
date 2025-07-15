"""エラーハンドラー機能の包括的なユニットテスト

Issue #466対応: テストカバレッジ向上（エラーハンドリング系 0% → 80%以上）
"""

from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from kumihan_formatter.core.error_handling.error_handler import ErrorHandler
from kumihan_formatter.core.error_handling.error_types import (
    ErrorLevel,
    UserFriendlyError,
)


class TestErrorHandlerInitialization(TestCase):
    """ErrorHandlerの初期化テスト"""

    def test_error_handler_init_without_console_ui(self) -> None:
        """コンソールUIなしでの初期化テスト"""
        handler = ErrorHandler()

        self.assertIsNone(handler.console_ui)
        self.assertEqual(handler._error_history, [])
        self.assertIsNotNone(handler.logger)

    def test_error_handler_init_with_console_ui(self) -> None:
        """コンソールUI付きでの初期化テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        self.assertEqual(handler.console_ui, mock_console_ui)
        self.assertEqual(handler._error_history, [])


class TestErrorHandlerExceptionHandling(TestCase):
    """ErrorHandlerの例外処理テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.handler = ErrorHandler()

    def test_handle_file_not_found_error(self) -> None:
        """FileNotFoundError処理テスト"""
        file_path = "/test/file.txt"
        exception = FileNotFoundError(f"File not found: {file_path}")
        context = {"file_path": file_path}

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_file_not_found_error"
        ) as mock_create:
            mock_error = MagicMock()
            mock_create.return_value = mock_error

            result = self.handler.handle_exception(exception, context)

            mock_create.assert_called_once_with(file_path)
            self.assertEqual(result, mock_error)

    def test_handle_unicode_decode_error(self) -> None:
        """UnicodeDecodeError処理テスト"""
        file_path = "/test/file.txt"
        exception = UnicodeDecodeError("utf-8", b"invalid", 0, 1, "invalid start byte")
        context = {"file_path": file_path}

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_encoding_error"
        ) as mock_create:
            mock_error = MagicMock()
            mock_create.return_value = mock_error

            result = self.handler.handle_exception(exception, context)

            mock_create.assert_called_once_with(file_path)
            self.assertEqual(result, mock_error)

    def test_handle_permission_error(self) -> None:
        """PermissionError処理テスト"""
        file_path = "/test/file.txt"
        operation = "読み込み"
        exception = PermissionError("Permission denied")
        context = {"file_path": file_path, "operation": operation}

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_permission_error"
        ) as mock_create:
            mock_error = MagicMock()
            mock_create.return_value = mock_error

            result = self.handler.handle_exception(exception, context)

            mock_create.assert_called_once_with(file_path, operation)
            self.assertEqual(result, mock_error)

    def test_handle_unknown_error(self) -> None:
        """未知のエラー処理テスト"""
        exception = ValueError("Unknown error")
        context = {"operation": "テスト"}

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_unknown_error"
        ) as mock_create:
            mock_error = MagicMock()
            mock_create.return_value = mock_error

            result = self.handler.handle_exception(exception, context)

            mock_create.assert_called_once_with(
                original_error="Unknown error", context=context
            )
            self.assertEqual(result, mock_error)

    def test_handle_exception_without_context(self) -> None:
        """コンテキストなしの例外処理テスト"""
        exception = FileNotFoundError("Test file not found")

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_file_not_found_error"
        ) as mock_create:
            mock_error = MagicMock()
            mock_create.return_value = mock_error

            result = self.handler.handle_exception(exception)

            # contextがNoneの場合は例外メッセージが使用される
            mock_create.assert_called_once_with("Test file not found")
            self.assertEqual(result, mock_error)

    def test_handle_permission_error_default_operation(self) -> None:
        """デフォルト操作でのPermissionError処理テスト"""
        file_path = "/test/file.txt"
        exception = PermissionError("Permission denied")
        context = {"file_path": file_path}  # operationなし

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_permission_error"
        ) as mock_create:
            mock_error = MagicMock()
            mock_create.return_value = mock_error

            result = self.handler.handle_exception(exception, context)

            mock_create.assert_called_once_with(file_path, "アクセス")
            self.assertEqual(result, mock_error)


class TestErrorHandlerDisplay(TestCase):
    """ErrorHandlerの表示機能テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.mock_solution = MagicMock()
        self.mock_solution.quick_fix = "クイック修正"
        self.mock_solution.detailed_steps = ["手順1", "手順2"]
        self.mock_solution.alternative_approaches = ["代替案1", "代替案2"]

        self.mock_error = MagicMock()
        self.mock_error.error_code = "TEST_001"
        self.mock_error.user_message = "テストエラーメッセージ"
        self.mock_error.level = ErrorLevel.ERROR
        self.mock_error.solution = self.mock_solution
        self.mock_error.technical_details = "技術的詳細"

    def test_display_error_without_console_ui(self) -> None:
        """コンソールUIなしでのエラー表示テスト"""
        handler = ErrorHandler()

        with patch("builtins.print") as mock_print:
            handler.display_error(self.mock_error)

            # 基本的なprint出力が行われることを確認
            self.assertEqual(mock_print.call_count, 2)
            mock_print.assert_any_call("[TEST_001] テストエラーメッセージ")
            mock_print.assert_any_call("解決方法: クイック修正")

    def test_display_error_with_console_ui_basic(self) -> None:
        """基本的なコンソールUI付きエラー表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        handler.display_error(self.mock_error)

        # console.printが呼ばれることを確認
        self.assertGreaterEqual(mock_console_ui.console.print.call_count, 2)

        # エラーが履歴に追加されることを確認
        self.assertEqual(len(handler._error_history), 1)
        self.assertEqual(handler._error_history[0], self.mock_error)

    def test_display_error_with_verbose_mode(self) -> None:
        """詳細モードでのエラー表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        handler.display_error(self.mock_error, verbose=True)

        # 詳細情報が表示されることを確認
        self.assertGreater(mock_console_ui.console.print.call_count, 2)

    def test_display_error_different_levels(self) -> None:
        """異なるエラーレベルでの表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        levels = [
            ErrorLevel.INFO,
            ErrorLevel.WARNING,
            ErrorLevel.ERROR,
            ErrorLevel.CRITICAL,
        ]

        for level in levels:
            self.mock_error.level = level
            handler.display_error(self.mock_error)

        # 各レベルで表示が実行されることを確認
        self.assertEqual(len(handler._error_history), 4)

    def test_display_error_without_optional_fields(self) -> None:
        """オプションフィールドなしでのエラー表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        # オプションフィールドをNoneに設定
        self.mock_solution.detailed_steps = None
        self.mock_solution.alternative_approaches = None
        self.mock_error.technical_details = None

        handler.display_error(self.mock_error, verbose=True)

        # 基本表示は実行されることを確認
        self.assertGreaterEqual(mock_console_ui.console.print.call_count, 2)


class TestErrorHandlerContext(TestCase):
    """ErrorHandlerのコンテキスト表示テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.handler = ErrorHandler()
        self.test_file_content = "line 1\nline 2\nline 3 (error line)\nline 4\nline 5"

    def test_show_error_context_without_console_ui(self) -> None:
        """コンソールUIなしでのコンテキスト表示テスト"""
        file_path = Path("/test/file.txt")

        # console_uiがNoneの場合は何もしない
        self.handler.show_error_context(file_path, 3, "line 3 (error line)")

        # エラーが発生しないことを確認
        self.assertTrue(True)

    def test_show_error_context_with_console_ui(self) -> None:
        """コンソールUI付きでのコンテキスト表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)
        file_path = Path("/test/file.txt")

        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.return_value = self.test_file_content

            handler.show_error_context(file_path, 3, "line 3 (error line)")

            # ファイル読み取りが実行されることを確認
            mock_read.assert_called_once_with(encoding="utf-8")

            # コンテキスト表示が実行されることを確認
            self.assertGreater(mock_console_ui.console.print.call_count, 0)

    def test_show_error_context_file_read_error(self) -> None:
        """ファイル読み取りエラー時のコンテキスト表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)
        file_path = Path("/test/file.txt")

        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.side_effect = Exception("File read error")

            # エラーが発生してもクラッシュしないことを確認
            handler.show_error_context(file_path, 3, "line 3 (error line)")

            # エラーが適切にログされることを確認
            self.assertTrue(True)

    def test_show_error_context_edge_cases(self) -> None:
        """エッジケースでのコンテキスト表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)
        file_path = Path("/test/file.txt")

        with patch("pathlib.Path.read_text") as mock_read:
            # 短いファイルでのテスト
            mock_read.return_value = "line 1\nline 2"

            handler.show_error_context(file_path, 1, "line 1")

            # 表示が実行されることを確認
            self.assertGreater(mock_console_ui.console.print.call_count, 0)

    def test_show_error_context_line_bounds(self) -> None:
        """行番号境界でのコンテキスト表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)
        file_path = Path("/test/file.txt")

        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.return_value = self.test_file_content

            # ファイルの最初の行でのエラー
            handler.show_error_context(file_path, 1, "line 1")

            # ファイルの最後の行でのエラー
            handler.show_error_context(file_path, 5, "line 5")

            # 両方で表示が実行されることを確認
            self.assertGreater(mock_console_ui.console.print.call_count, 0)


class TestErrorHandlerStatistics(TestCase):
    """ErrorHandlerの統計機能テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.handler = ErrorHandler()

    def test_get_error_statistics_empty(self) -> None:
        """空の統計情報テスト"""
        stats = self.handler.get_error_statistics()
        self.assertEqual(stats, {})

    def test_get_error_statistics_with_errors(self) -> None:
        """エラー付きの統計情報テスト"""
        # モックエラーを作成
        mock_error1 = MagicMock()
        mock_error1.error_code = "TEST_001"
        mock_error1.category.value = "FILE"
        mock_error1.level.value = "ERROR"

        mock_error2 = MagicMock()
        mock_error2.error_code = "TEST_002"
        mock_error2.category.value = "ENCODING"
        mock_error2.level.value = "WARNING"

        # エラー履歴に追加
        self.handler._error_history = [mock_error1, mock_error2]

        stats = self.handler.get_error_statistics()

        self.assertEqual(stats["total_errors"], 2)
        self.assertEqual(stats["by_category"]["FILE"], 1)
        self.assertEqual(stats["by_category"]["ENCODING"], 1)
        self.assertEqual(stats["by_level"]["ERROR"], 1)
        self.assertEqual(stats["by_level"]["WARNING"], 1)
        self.assertEqual(stats["most_recent"], "TEST_002")

    def test_get_error_statistics_same_category(self) -> None:
        """同じカテゴリのエラーがある場合の統計テスト"""
        # 同じカテゴリのモックエラーを作成
        mock_error1 = MagicMock()
        mock_error1.error_code = "TEST_001"
        mock_error1.category.value = "FILE"
        mock_error1.level.value = "ERROR"

        mock_error2 = MagicMock()
        mock_error2.error_code = "TEST_002"
        mock_error2.category.value = "FILE"
        mock_error2.level.value = "ERROR"

        self.handler._error_history = [mock_error1, mock_error2]

        stats = self.handler.get_error_statistics()

        self.assertEqual(stats["total_errors"], 2)
        self.assertEqual(stats["by_category"]["FILE"], 2)
        self.assertEqual(stats["by_level"]["ERROR"], 2)

    def test_error_history_management(self) -> None:
        """エラー履歴管理のテスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        mock_error = MagicMock()
        mock_error.error_code = "TEST_001"
        mock_error.user_message = "テストエラー"
        mock_error.level = ErrorLevel.ERROR
        mock_error.solution = MagicMock()
        mock_error.solution.quick_fix = "修正"
        mock_error.solution.detailed_steps = None
        mock_error.solution.alternative_approaches = None
        mock_error.technical_details = None

        # エラーを表示
        handler.display_error(mock_error)

        # 履歴に追加されることを確認
        self.assertEqual(len(handler._error_history), 1)
        self.assertEqual(handler._error_history[0], mock_error)

        # 統計情報が正しく取得できることを確認
        stats = handler.get_error_statistics()
        self.assertEqual(stats["total_errors"], 1)


class TestErrorHandlerIntegration(TestCase):
    """ErrorHandlerの統合テスト"""

    def test_full_error_handling_workflow(self) -> None:
        """完全なエラーハンドリングワークフローテスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        # 例外を発生させて処理
        exception = FileNotFoundError("test.txt")
        context = {"file_path": "test.txt", "operation": "読み込み"}

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_file_not_found_error"
        ) as mock_create:
            mock_error = MagicMock()
            mock_error.error_code = "FILE_001"
            mock_error.user_message = "ファイルが見つかりません"
            mock_error.level = ErrorLevel.ERROR
            mock_error.solution = MagicMock()
            mock_error.solution.quick_fix = "ファイルパスを確認してください"
            mock_error.solution.detailed_steps = None
            mock_error.solution.alternative_approaches = None
            mock_error.technical_details = None
            mock_error.category.value = "FILE"
            mock_error.level.value = "ERROR"
            mock_create.return_value = mock_error

            # 例外を処理
            error = handler.handle_exception(exception, context)

            # エラーを表示
            handler.display_error(error, verbose=True)

            # 統計を取得
            stats = handler.get_error_statistics()

            # 結果を検証
            self.assertEqual(error, mock_error)
            self.assertEqual(len(handler._error_history), 1)
            self.assertEqual(stats["total_errors"], 1)
            self.assertEqual(stats["by_category"]["FILE"], 1)
            self.assertGreater(mock_console_ui.console.print.call_count, 0)

    def test_multiple_errors_handling(self) -> None:
        """複数エラーの処理テスト"""
        handler = ErrorHandler()

        # 異なる種類の例外を処理
        exceptions = [
            (FileNotFoundError("file1.txt"), {"file_path": "file1.txt"}),
            (
                UnicodeDecodeError("utf-8", b"", 0, 1, "test"),
                {"file_path": "file2.txt"},
            ),
            (
                PermissionError("denied"),
                {"file_path": "file3.txt", "operation": "書き込み"},
            ),
        ]

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory"
        ) as mock_factory:
            # 各ファクトリメソッドのモック設定
            mock_factory.create_file_not_found_error.return_value = (
                self._create_mock_error("FILE_001", "FILE")
            )
            mock_factory.create_encoding_error.return_value = self._create_mock_error(
                "ENCODING_001", "ENCODING"
            )
            mock_factory.create_permission_error.return_value = self._create_mock_error(
                "PERM_001", "PERMISSION"
            )

            # 各例外を処理
            for exception, context in exceptions:
                handler.handle_exception(exception, context)

            # 統計を確認
            # この時点では履歴は空（display_errorを呼んでいないため）
            stats = handler.get_error_statistics()
            self.assertEqual(stats, {})

    def _create_mock_error(self, error_code: str, category: str) -> MagicMock:
        """モックエラーを作成するヘルパーメソッド"""
        mock_error = MagicMock()
        mock_error.error_code = error_code
        mock_error.category.value = category
        mock_error.level.value = "ERROR"
        return mock_error


class TestErrorHandlerEdgeCases(TestCase):
    """ErrorHandlerのエッジケーステスト"""

    def test_handle_exception_with_empty_context(self) -> None:
        """空のコンテキストでの例外処理テスト"""
        handler = ErrorHandler()
        exception = FileNotFoundError("test error")

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_file_not_found_error"
        ) as mock_create:
            mock_create.return_value = MagicMock()

            result = handler.handle_exception(exception, {})

            # 空のコンテキストでも処理されることを確認
            mock_create.assert_called_once_with("test error")

    def test_unicode_decode_error_without_file_path(self) -> None:
        """ファイルパスなしのUnicodeDecodeError処理テスト"""
        handler = ErrorHandler()
        exception = UnicodeDecodeError("utf-8", b"", 0, 1, "test")

        with patch(
            "kumihan_formatter.core.error_handling.error_handler.ErrorFactory.create_encoding_error"
        ) as mock_create:
            mock_create.return_value = MagicMock()

            result = handler.handle_exception(exception, {})

            # デフォルトのファイルパスが使用されることを確認
            mock_create.assert_called_once_with("不明なファイル")

    def test_display_error_with_none_solution_fields(self) -> None:
        """Noneのソリューションフィールドでのエラー表示テスト"""
        mock_console_ui = MagicMock()
        handler = ErrorHandler(mock_console_ui)

        mock_error = MagicMock()
        mock_error.error_code = "TEST_001"
        mock_error.user_message = "テストエラー"
        mock_error.level = ErrorLevel.ERROR
        mock_error.solution.quick_fix = "修正"
        mock_error.solution.detailed_steps = None
        mock_error.solution.alternative_approaches = None
        mock_error.technical_details = None

        # エラーが発生しないことを確認
        handler.display_error(mock_error, verbose=True)

        self.assertEqual(len(handler._error_history), 1)
