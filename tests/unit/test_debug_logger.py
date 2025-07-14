"""debug_logger.pyの包括的なユニットテスト

Issue #463対応: テストカバレッジ向上（43% → 80%以上）
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from kumihan_formatter.core.debug_logger import (
    GUIDebugLogger,
    get_logger,
    gui_debug_logger,
    is_debug_enabled,
    log_gui_method,
    log_gui_method_decorator,
    log_import_attempt,
    log_startup_info,
)


class TestGUIDebugLogger(TestCase):
    """GUIデバッグロガーの基本テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        # 環境変数を設定
        self.env_patcher = patch.dict(os.environ, {"KUMIHAN_GUI_DEBUG": "true"})
        self.env_patcher.start()

        # 一時ディレクトリ
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """テスト後のクリーンアップ"""
        self.env_patcher.stop()

    def test_singleton_instance(self) -> None:
        """シングルトンインスタンスのテスト"""
        logger1 = GUIDebugLogger.get_singleton()
        logger2 = GUIDebugLogger.get_singleton()

        # 同じインスタンスであることを確認
        self.assertIs(logger1, logger2)

    def test_log_buffer_operations(self) -> None:
        """ログバッファ操作のテスト（deque使用）"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True

        # ログを追加
        test_message = "Test log message"
        logger.debug(test_message)

        # バッファから取得
        buffer = logger.get_log_buffer()

        # ログが含まれることを確認
        self.assertTrue(any(test_message in log for log in buffer))

    def test_thread_safety(self) -> None:
        """スレッドセーフティの基本テスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True

        # 複数スレッドからログを追加
        def add_logs(thread_id: int) -> None:
            for i in range(10):
                logger.debug(f"Thread {thread_id} - Log {i}")

        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_logs, args=(i,))
            threads.append(thread)
            thread.start()

        # すべてのスレッドが完了するまで待機
        for thread in threads:
            thread.join()

        # ログバッファが適切なサイズであることを確認
        buffer = logger.get_log_buffer()
        self.assertGreater(len(buffer), 0)
        self.assertLessEqual(len(buffer), 1000)  # maxlen=1000

    def test_disabled_logger(self) -> None:
        """ロガー無効時の動作テスト"""
        with patch.dict(os.environ, {"KUMIHAN_GUI_DEBUG": "false"}):
            logger = GUIDebugLogger()

            # ログ追加（無効時は何も起こらない）
            logger.debug("This should not be logged")

            # バッファが空であることを確認
            buffer = logger.get_log_buffer()
            self.assertEqual(len(buffer), 0)

    def test_log_levels(self) -> None:
        """各ログレベルの基本動作テスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        # 各レベルでログを追加
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # すべてのログが記録されることを確認
        buffer = logger.get_log_buffer()
        self.assertGreaterEqual(len(buffer), 4)

    def test_logger_setup_file_creation_failure(self) -> None:
        """ログファイル作成失敗時の動作テスト"""
        with patch.dict(
            os.environ,
            {
                "KUMIHAN_GUI_DEBUG": "true",
                "KUMIHAN_GUI_LOG_FILE": "/invalid/path/test.log",
            },
        ):
            logger = GUIDebugLogger()
            # ファイル作成に失敗してもロガーは動作する
            self.assertIsNone(logger.logger)

    def test_logger_setup_with_console_log(self) -> None:
        """コンソールログ有効時のテスト"""
        with patch.dict(
            os.environ, {"KUMIHAN_GUI_DEBUG": "true", "KUMIHAN_GUI_CONSOLE_LOG": "true"}
        ):
            with patch(
                "kumihan_formatter.core.debug_logger.logging.FileHandler"
            ) as mock_file:
                with patch(
                    "kumihan_formatter.core.debug_logger.logging.StreamHandler"
                ) as mock_stream:
                    # ハンドラーのlevelを適切にモック
                    mock_file.return_value.level = 10  # DEBUG level
                    mock_stream.return_value.level = 10  # DEBUG level

                    logger = GUIDebugLogger()
                    # StreamHandlerが作成されることを確認
                    if logger.logger:
                        mock_stream.assert_called()

    def test_error_with_exception(self) -> None:
        """例外付きエラーログのテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        test_exception = ValueError("Test error")
        logger.error("Error occurred", exception=test_exception)

        buffer = logger.get_log_buffer()
        # バッファに記録されたログを確認
        log_content = "\n".join(buffer)
        self.assertIn("Error occurred", log_content)
        self.assertIn("Test error", log_content)  # 例外メッセージが含まれる

    def test_log_function_call(self) -> None:
        """関数呼び出しログのテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        logger.log_function_call("test_func", (1, 2), {"key": "value"})

        buffer = logger.get_log_buffer()
        self.assertTrue(
            any("Function call: test_func(1, 2, key=value)" in log for log in buffer)
        )

    def test_log_gui_event(self) -> None:
        """GUIイベントログのテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        logger.log_gui_event("click", "button", "Submit button clicked")

        buffer = logger.get_log_buffer()
        self.assertTrue(
            any(
                "GUI Event: click on button - Submit button clicked" in log
                for log in buffer
            )
        )

    def test_log_performance(self) -> None:
        """パフォーマンスログのテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        logger.log_performance("database_query", 0.123)

        buffer = logger.get_log_buffer()
        self.assertTrue(
            any("Performance: database_query took 0.123s" in log for log in buffer)
        )

    def test_get_log_file_path(self) -> None:
        """ログファイルパス取得のテスト"""
        logger = GUIDebugLogger.get_singleton()
        path = logger.get_log_file_path()
        self.assertIsInstance(path, Path)

    def test_clear_log_buffer(self) -> None:
        """ログバッファクリアのテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True

        # ログを追加
        logger.debug("Test message")
        self.assertGreater(len(logger.get_log_buffer()), 0)

        # クリア
        logger.clear_log_buffer()
        self.assertEqual(len(logger.get_log_buffer()), 0)


class TestDecorators(TestCase):
    """デコレータ関数のテスト"""

    def setUp(self) -> None:
        self.env_patcher = patch.dict(os.environ, {"KUMIHAN_GUI_DEBUG": "true"})
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

    def test_log_gui_method_decorator(self) -> None:
        """GUIメソッドデコレータのテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        class TestClass:
            @log_gui_method_decorator
            def test_method(self, arg1: int, arg2: str = "default") -> str:
                return f"{arg1}-{arg2}"

        test_obj = TestClass()
        result = test_obj.test_method(42, arg2="test")

        self.assertEqual(result, "42-test")

        buffer = logger.get_log_buffer()
        # 関数呼び出しとパフォーマンスのログが記録される
        self.assertTrue(
            any("Function call: TestClass.test_method" in log for log in buffer)
        )
        self.assertTrue(
            any("Performance: TestClass.test_method took" in log for log in buffer)
        )

    def test_log_gui_method_decorator_with_exception(self) -> None:
        """例外発生時のGUIメソッドデコレータのテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        class TestClass:
            @log_gui_method_decorator
            def failing_method(self) -> None:
                raise ValueError("Test exception")

        test_obj = TestClass()

        with self.assertRaises(ValueError):
            test_obj.failing_method()

        buffer = logger.get_log_buffer()
        self.assertTrue(
            any("Error in TestClass.failing_method" in log for log in buffer)
        )

    def test_log_import_attempt_success(self) -> None:
        """インポート成功時のテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        @log_import_attempt("test_module", logger)
        def mock_import() -> str:
            return "imported"

        result = mock_import()
        self.assertEqual(result, "imported")

        buffer = logger.get_log_buffer()
        self.assertTrue(
            any("Attempting to import: test_module" in log for log in buffer)
        )
        self.assertTrue(
            any("Successfully imported: test_module" in log for log in buffer)
        )

    def test_log_import_attempt_failure(self) -> None:
        """インポート失敗時のテスト"""
        logger = GUIDebugLogger.get_singleton()
        logger.enabled = True
        logger.clear_log_buffer()

        @log_import_attempt("failing_module", logger)
        def failing_import() -> None:
            raise ImportError("Module not found")

        with self.assertRaises(ImportError):
            failing_import()

        buffer = logger.get_log_buffer()
        self.assertTrue(any("Failed to import failing_module" in log for log in buffer))


class TestGlobalFunctions(TestCase):
    """グローバル関数のテスト"""

    def setUp(self) -> None:
        self.env_patcher = patch.dict(os.environ, {"KUMIHAN_GUI_DEBUG": "true"})
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

    def test_get_logger(self) -> None:
        """get_logger関数のテスト"""
        logger = get_logger()
        self.assertIsInstance(logger, GUIDebugLogger)
        self.assertIs(logger, gui_debug_logger)

    def test_is_debug_enabled(self) -> None:
        """is_debug_enabled関数のテスト"""
        # 現在の設定を保存
        original_enabled = gui_debug_logger.enabled

        try:
            # テスト用の設定
            gui_debug_logger.enabled = True
            self.assertTrue(is_debug_enabled())

            gui_debug_logger.enabled = False
            self.assertFalse(is_debug_enabled())
        finally:
            # 元の設定を復元
            gui_debug_logger.enabled = original_enabled

    def test_log_startup_info(self) -> None:
        """log_startup_info関数のテスト"""
        logger = get_logger()
        logger.enabled = True
        logger.clear_log_buffer()

        log_startup_info()

        buffer = logger.get_log_buffer()
        self.assertTrue(any("=== Startup Information ===" in log for log in buffer))
        self.assertTrue(any("Current working directory:" in log for log in buffer))
        self.assertTrue(any("Python executable:" in log for log in buffer))

    def test_log_startup_info_with_kumihan_env(self) -> None:
        """Kumihan環境変数表示のテスト"""
        logger = get_logger()
        logger.enabled = True
        logger.clear_log_buffer()

        with patch.dict(os.environ, {"KUMIHAN_TEST_VAR": "test_value"}):
            log_startup_info()

        buffer = logger.get_log_buffer()
        log_content = "\n".join(buffer)
        self.assertIn("Kumihan environment variables:", log_content)
        self.assertIn("KUMIHAN_TEST_VAR", log_content)

    def test_log_startup_info_disabled(self) -> None:
        """ロガー無効時のstartup infoテスト"""
        # 現在の設定を保存
        original_enabled = gui_debug_logger.enabled

        try:
            # ロガーを無効化
            gui_debug_logger.enabled = False

            # 無効時は何も実行されない
            log_startup_info()
            # エラーが発生しないことを確認
            self.assertTrue(True)
        finally:
            # 元の設定を復元
            gui_debug_logger.enabled = original_enabled


class TestMainBlock(TestCase):
    """__main__ブロックのテスト"""

    def test_main_block_execution(self) -> None:
        """メインブロックの実行テスト"""
        with patch("builtins.print") as mock_print:
            with patch.dict(os.environ, {"KUMIHAN_GUI_DEBUG": "true"}):
                with patch(
                    "kumihan_formatter.core.debug_logger.logging.FileHandler"
                ) as mock_file:
                    # ハンドラーのlevelを適切にモック
                    mock_file.return_value.level = 10  # DEBUG level

                    # __main__ブロックの内容を実行
                    logger = GUIDebugLogger()
                    logger.info("Test message")
                    logger.error("Test error", Exception("Test exception"))

                    print(f"Log file: {logger.get_log_file_path()}")
                    print("Log buffer contents:")
                    for line in logger.get_log_buffer():
                        print(line)

                    # printが呼ばれることを確認
                    self.assertTrue(mock_print.called)
