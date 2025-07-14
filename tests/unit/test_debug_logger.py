"""debug_logger.pyの基本的なユニットテスト

Issue #463で完全なテストカバレッジを実装予定
現在は最小限のスモークテストのみ提供
"""

import os
import tempfile
import threading
from unittest import TestCase
from unittest.mock import patch

from kumihan_formatter.core.debug_logger import GUIDebugLogger, gui_debug_logger


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
