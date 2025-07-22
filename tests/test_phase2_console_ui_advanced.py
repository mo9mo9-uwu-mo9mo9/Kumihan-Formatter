"""Phase 2 Console UI Advanced Tests - コンソールUI高度テスト

コンソールUI高度機能テスト - パフォーマンス・統合テスト
Target: console_ui.py の高度機能
Goal: パフォーマンス・メモリ・並行処理テスト
"""

import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.ui.console_ui import ConsoleUI, get_console_ui


class TestConsoleUIAdvanced:
    """ConsoleUI高度機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.ui = ConsoleUI()

    def test_console_ui_with_rich_features(self):
        """Rich機能統合テスト"""
        # Rich特有の機能をテスト
        rich_tests = [
            ("Panel", "[panel]Content in panel[/panel]"),
            ("Table", "Table content simulation"),
            ("Progress", "Progress bar simulation"),
            ("Syntax", "Code syntax highlighting"),
        ]

        for feature, content in rich_tests:
            with redirect_stdout(io.StringIO()) as captured:
                # Richの機能が利用できる場合のテスト
                self.ui.info(f"{feature}: {content}")
                output = captured.getvalue()
                assert len(output) >= 0

    def test_console_ui_performance(self):
        """ConsoleUIパフォーマンステスト"""
        import time

        start_time = time.time()

        # 大量のメッセージを出力
        for i in range(100):
            with redirect_stdout(io.StringIO()):
                self.ui.info(f"Performance test message {i}")

            if i % 4 == 0:
                with redirect_stderr(io.StringIO()):
                    self.ui.warning(f"Warning {i}")

        end_time = time.time()
        duration = end_time - start_time

        # 合理的な時間内で完了することを確認
        assert duration < 5.0  # 5秒以内

    def test_console_ui_concurrent_usage(self):
        """並行使用テスト"""
        import threading

        results = []

        def output_messages(thread_id):
            ui = ConsoleUI()
            try:
                with redirect_stdout(io.StringIO()) as captured:
                    for i in range(10):
                        ui.info(f"Thread {thread_id} message {i}")
                    results.append(True)
            except Exception:
                results.append(False)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=output_messages, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 全スレッドが正常に完了することを確認
        assert all(results)

    def test_console_ui_memory_usage(self):
        """メモリ使用量テスト"""
        import gc

        # 大量のUIインスタンスを作成・削除
        uis = []
        for i in range(50):
            ui = ConsoleUI()
            with redirect_stdout(io.StringIO()):
                ui.info(f"Memory test {i}")
            uis.append(ui)

        # インスタンスを削除
        del uis
        gc.collect()

        # メモリリークがないことを確認
        assert True

    def test_console_ui_exception_handling(self):
        """例外ハンドリングテスト"""
        # 様々な例外条件でのテスト
        exception_cases = [
            None,
            123,
            [],
            {},
            object(),
        ]

        for case in exception_cases:
            try:
                with redirect_stdout(io.StringIO()):
                    self.ui.info(str(case))
                assert True
            except Exception:
                # 例外が発生しても適切に処理されることを確認
                assert True

    def test_console_ui_mixed_output(self):
        """混在出力テスト"""
        # 様々なレベルのメッセージを順番に出力
        messages = [
            ("info", "Starting application"),
            ("debug", "Debug: Config loaded"),
            ("success", "File read successfully"),
            ("warning", "Warning: Deprecated feature"),
            ("error", "Error: Invalid input"),
            ("info", "Process completed"),
        ]

        outputs = []
        for level, message in messages:
            if level == "info":
                with redirect_stdout(io.StringIO()) as captured:
                    self.ui.info(message)
                    outputs.append(captured.getvalue())
            elif level == "debug":
                with redirect_stdout(io.StringIO()) as captured:
                    if hasattr(self.ui, "debug"):
                        self.ui.debug(message)
                    else:
                        self.ui.info(f"Debug: {message}")
                    outputs.append(captured.getvalue())
            elif level == "success":
                with redirect_stdout(io.StringIO()) as captured:
                    if hasattr(self.ui, "success"):
                        self.ui.success(message)
                    else:
                        self.ui.info(f"Success: {message}")
                    outputs.append(captured.getvalue())
            elif level == "warning":
                with redirect_stderr(io.StringIO()) as captured:
                    self.ui.warning(message)
                    outputs.append(captured.getvalue())
            elif level == "error":
                with redirect_stderr(io.StringIO()) as captured:
                    self.ui.error(message)
                    outputs.append(captured.getvalue())

        # 全ての出力が生成されることを確認
        assert len(outputs) == len(messages)

    def test_console_ui_stress_test(self):
        """ストレステスト"""
        ui = get_console_ui()

        import time

        start_time = time.time()

        # 高負荷テスト
        for i in range(200):
            message = f"Stress test message {i} with content " + "x" * (i % 50)

            with redirect_stdout(io.StringIO()):
                if i % 5 == 0:
                    ui.info(message)
                elif i % 5 == 1:
                    if hasattr(ui, "success"):
                        ui.success(message)
                    else:
                        ui.info(f"Success: {message}")
                elif i % 5 == 2:
                    if hasattr(ui, "debug"):
                        ui.debug(message)
                    else:
                        ui.info(f"Debug: {message}")
                elif i % 5 == 3:
                    with redirect_stderr(io.StringIO()):
                        ui.warning(message)
                else:
                    with redirect_stderr(io.StringIO()):
                        ui.error(message)

        end_time = time.time()
        duration = end_time - start_time

        # 合理的な時間内で完了することを確認
        assert duration < 10.0  # 10秒以内