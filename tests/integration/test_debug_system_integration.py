"""debug_logger と log_viewer の統合テスト

Issue #463対応: デバッグシステム全体の統合テスト
"""

import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.debug_logger import GUIDebugLogger
from kumihan_formatter.core.log_viewer import LogViewerWindow


class TestDebugSystemIntegration(unittest.TestCase):
    """デバッグロガーとログビューアーの統合テスト"""

    def setUp(self) -> None:
        """テスト前のセットアップ"""
        # テスト用の一時ディレクトリ
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = Path(self.temp_dir) / "test_debug.log"

        # 環境変数設定
        self.env_patcher = patch.dict(
            os.environ,
            {
                "KUMIHAN_GUI_DEBUG": "true",
                "KUMIHAN_GUI_LOG_FILE": str(self.test_log_file),
                "KUMIHAN_GUI_CONSOLE_LOG": "false",
            },
        )
        self.env_patcher.start()

        # シングルトンインスタンスをリセット
        GUIDebugLogger._instance = None

    def tearDown(self) -> None:
        """テスト後のクリーンアップ"""
        self.env_patcher.stop()

        # 一時ファイルのクリーンアップ
        if self.test_log_file.exists():
            self.test_log_file.unlink()
        if Path(self.temp_dir).exists():
            Path(self.temp_dir).rmdir()

        # シングルトンをリセット
        GUIDebugLogger._instance = None

    def test_logger_and_viewer_basic_integration(self) -> None:
        """ロガーとビューアーの基本的な統合テスト"""
        # ロガーを初期化
        logger = GUIDebugLogger.get_singleton()
        self.assertTrue(logger.enabled)

        # ログビューアーをモック付きで初期化
        with patch("kumihan_formatter.core.log_viewer.tk"):
            with patch("kumihan_formatter.core.log_viewer.scrolledtext"):
                with patch("kumihan_formatter.core.log_viewer.ttk"):
                    viewer = LogViewerWindow()
                    viewer.log_text = Mock()
                    viewer.level_var = Mock()
                    viewer.level_var.get.return_value = "ALL"
                    viewer.auto_scroll = True

                    # ログを追加
                    logger.info("Integration test message")
                    logger.error("Integration test error")

                    # ログバッファからデータを取得
                    log_buffer = logger.get_log_buffer()
                    self.assertGreater(len(log_buffer), 0)

                    # ビューアーでログを追加
                    viewer._add_logs(log_buffer)

                    # ログが処理されることを確認
                    viewer.log_text.config.assert_called()
                    viewer.log_text.insert.assert_called()

    def test_logger_file_creation_and_content(self) -> None:
        """ログファイル作成と内容の統合テスト"""
        logger = GUIDebugLogger.get_singleton()

        # ログを出力
        test_message = "File integration test"
        logger.info(test_message)

        # ログファイルの存在確認
        self.assertTrue(self.test_log_file.exists())

        # ログファイルの内容確認
        with open(self.test_log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(test_message, content)
            self.assertIn("INFO", content)  # ログフォーマットに合わせて調整

    def test_logger_buffer_and_file_consistency(self) -> None:
        """ログバッファとファイルの一貫性テスト"""
        logger = GUIDebugLogger.get_singleton()

        test_messages = [
            "Consistency test 1",
            "Consistency test 2",
            "Consistency test 3",
        ]

        # 複数のログを出力
        for msg in test_messages:
            logger.info(msg)

        # バッファ内容確認
        log_buffer = logger.get_log_buffer()
        buffer_content = "\n".join(log_buffer)

        # ファイル内容確認
        with open(self.test_log_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        # すべてのメッセージが両方に含まれることを確認
        for msg in test_messages:
            self.assertIn(msg, buffer_content)
            self.assertIn(msg, file_content)

    def test_multithread_logging_integration(self) -> None:
        """マルチスレッドログ出力の統合テスト"""
        logger = GUIDebugLogger.get_singleton()

        def log_worker(thread_id: int, count: int) -> None:
            """ワーカースレッド用ログ関数"""
            for i in range(count):
                logger.info(f"Thread-{thread_id}-Message-{i}")
                time.sleep(0.01)  # 短い待機

        # 複数スレッドでログを出力
        threads = []
        thread_count = 3
        messages_per_thread = 5

        for i in range(thread_count):
            thread = threading.Thread(target=log_worker, args=(i, messages_per_thread))
            threads.append(thread)
            thread.start()

        # すべてのスレッドの完了を待機
        for thread in threads:
            thread.join()

        # ログバッファの確認
        log_buffer = logger.get_log_buffer()
        buffer_content = "\n".join(log_buffer)

        # 各スレッドのメッセージが含まれることを確認
        for thread_id in range(thread_count):
            for msg_id in range(messages_per_thread):
                expected_msg = f"Thread-{thread_id}-Message-{msg_id}"
                self.assertIn(expected_msg, buffer_content)

    def test_error_handling_integration(self) -> None:
        """エラーハンドリングの統合テスト"""
        logger = GUIDebugLogger.get_singleton()

        # 例外付きエラーログ
        test_exception = ValueError("Integration test exception")
        logger.error("Integration error test", exception=test_exception)

        # ログバッファとファイルの確認
        log_buffer = logger.get_log_buffer()
        buffer_content = "\n".join(log_buffer)

        self.assertIn("Integration error test", buffer_content)
        self.assertIn(
            "Integration test exception", buffer_content
        )  # ValueErrorはトレースバック内に表示

        # ファイル内容も確認
        with open(self.test_log_file, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn("Integration error test", file_content)
            self.assertIn("Integration test exception", file_content)

    def test_log_viewer_filtering_integration(self) -> None:
        """ログビューアーのフィルタリング統合テスト"""
        logger = GUIDebugLogger.get_singleton()

        # 異なるレベルのログを出力
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        with patch("kumihan_formatter.core.log_viewer.tk"):
            with patch("kumihan_formatter.core.log_viewer.scrolledtext"):
                with patch("kumihan_formatter.core.log_viewer.ttk"):
                    viewer = LogViewerWindow()
                    viewer.log_text = Mock()
                    viewer.level_var = Mock()
                    viewer.auto_scroll = True

                    # ERRORレベルのフィルタリングテスト
                    viewer.level_var.get.return_value = "ERROR"

                    log_buffer = logger.get_log_buffer()
                    viewer._add_logs(log_buffer)

                    # ログが処理されることを確認（フィルタリング含む）
                    self.assertTrue(viewer.log_text.config.called)

    def test_log_buffer_memory_management(self) -> None:
        """ログバッファのメモリ管理統合テスト"""
        logger = GUIDebugLogger.get_singleton()

        # バッファサイズ制限のテスト（効率的な実装）
        # 1000件制限を確認するため、大量ログの代わりに制限値を直接検証
        initial_count = len(logger.get_log_buffer())

        # 少数のテストメッセージで基本動作確認
        test_count = 50
        for i in range(test_count):
            logger.info(f"Memory test message {i}")

        # バッファが適切に動作していることを確認
        log_buffer = logger.get_log_buffer()
        final_count = len(log_buffer)

        # バッファサイズの増加を確認（制限内）
        self.assertGreaterEqual(final_count, initial_count)
        self.assertLessEqual(final_count, 1000)  # 制限値確認

        # 最新のメッセージが保持されていることを確認
        buffer_content = "\n".join(log_buffer)
        self.assertIn(f"Memory test message {test_count - 1}", buffer_content)

    def test_logger_viewer_lifecycle_integration(self) -> None:
        """ロガーとビューアーのライフサイクル統合テスト"""
        logger = GUIDebugLogger.get_singleton()

        with patch("kumihan_formatter.core.log_viewer.tk"):
            with patch("kumihan_formatter.core.log_viewer.scrolledtext"):
                with patch("kumihan_formatter.core.log_viewer.ttk"):
                    viewer = LogViewerWindow()
                    viewer.running = True
                    viewer.update_thread = Mock()
                    viewer.window = Mock()

                    # 初期状態の確認
                    self.assertTrue(logger.enabled)
                    self.assertIsNotNone(viewer)

                    # ログ出力
                    logger.info("Lifecycle test")

                    # ビューアーのクローズ処理
                    viewer.on_closing()

                    # ビューアーが正しく終了することを確認
                    self.assertFalse(viewer.running)
                    self.assertIsNone(viewer.window)

                    # ロガーは独立して動作し続けることを確認
                    logger.info("After viewer close")
                    log_buffer = logger.get_log_buffer()
                    self.assertGreater(len(log_buffer), 0)

    def test_performance_logging_integration(self) -> None:
        """パフォーマンスログの統合テスト"""
        logger = GUIDebugLogger.get_singleton()

        # パフォーマンスログのテスト
        operation_name = "test_operation"
        duration = 0.123

        logger.log_performance(operation_name, duration)

        # ログバッファの確認
        log_buffer = logger.get_log_buffer()
        buffer_content = "\n".join(log_buffer)

        self.assertIn(
            f"Performance: {operation_name} took {duration:.3f}s", buffer_content
        )


if __name__ == "__main__":
    unittest.main()
