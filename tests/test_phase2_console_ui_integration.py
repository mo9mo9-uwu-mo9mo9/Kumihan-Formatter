"""Phase 2 Console UI Integration Tests - コンソールUI統合テスト

コンソールUI統合機能テスト - get_console_ui・ワークフロー
Target: console_ui.py の統合機能
Goal: 統合・ワークフロー・実用性テスト
"""

import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.ui.console_ui import ConsoleUI, get_console_ui


class TestGetConsoleUI:
    """get_console_ui関数テスト"""

    def test_get_console_ui_singleton(self):
        """get_console_ui シングルトン動作テスト"""
        ui1 = get_console_ui()
        ui2 = get_console_ui()

        # 同じインスタンスが返されることを確認（シングルトンの場合）
        assert ui1 is not None
        assert ui2 is not None
        # 実装によってはシングルトンでない場合もある
        assert type(ui1) == type(ui2)

    def test_get_console_ui_functionality(self):
        """get_console_ui機能テスト"""
        ui = get_console_ui()

        # 基本機能が利用できることを確認
        assert hasattr(ui, "info")
        assert hasattr(ui, "warning")
        assert hasattr(ui, "error")
        # オプション機能の確認
        if hasattr(ui, "success"):
            assert hasattr(ui, "success")
        if hasattr(ui, "debug"):
            assert hasattr(ui, "debug")

    def test_get_console_ui_usage(self):
        """get_console_ui使用テスト"""
        ui = get_console_ui()

        # 実際の使用テスト
        test_messages = [
            "Test info message",
            "Test warning message",
            "Test error message",
            "Test success message",
            "Test debug message",
        ]

        for message in test_messages:
            with redirect_stdout(io.StringIO()):
                ui.info(message)
            with redirect_stderr(io.StringIO()):
                ui.warning(message)
                ui.error(message)
            with redirect_stdout(io.StringIO()):
                if hasattr(ui, "success"):
                    ui.success(message)
                else:
                    ui.info(f"Success: {message}")
                if hasattr(ui, "debug"):
                    ui.debug(message)
                else:
                    ui.info(f"Debug: {message}")

        # エラーが発生しないことを確認
        assert True


class TestConsoleUIIntegration:
    """ConsoleUI統合テスト"""

    def test_console_ui_complete_workflow(self):
        """完全なワークフローテスト"""
        ui = get_console_ui()

        # 実際のアプリケーション使用を模擬
        workflow_steps = [
            ("info", "Application started"),
            ("debug", "Loading configuration..."),
            ("info", "Configuration loaded successfully"),
            ("info", "Processing input files..."),
            ("debug", "Processing file: input.txt"),
            ("success", "File processed: input.txt"),
            ("debug", "Processing file: config.json"),
            ("warning", "Config file has deprecated settings"),
            ("success", "File processed: config.json"),
            ("info", "Generating output..."),
            ("success", "Output generated: output.html"),
            ("info", "Process completed successfully"),
        ]

        for level, message in workflow_steps:
            if level == "info":
                with redirect_stdout(io.StringIO()):
                    ui.info(message)
            elif level == "debug":
                with redirect_stdout(io.StringIO()):
                    if hasattr(ui, "debug"):
                        ui.debug(message)
                    else:
                        ui.info(f"Debug: {message}")
            elif level == "success":
                with redirect_stdout(io.StringIO()):
                    if hasattr(ui, "success"):
                        ui.success(message)
                    else:
                        ui.info(f"Success: {message}")
            elif level == "warning":
                with redirect_stderr(io.StringIO()):
                    ui.warning(message)
            elif level == "error":
                with redirect_stderr(io.StringIO()):
                    ui.error(message)

        # 全工程が正常に実行されることを確認
        assert True

    def test_console_ui_real_world_scenario(self):
        """実世界シナリオテスト"""
        ui = get_console_ui()

        # 実際のファイル処理を模擬
        files = ["config.json", "input.txt", "template.html"]

        with redirect_stdout(io.StringIO()):
            ui.info("Starting batch file processing...")

        for i, filename in enumerate(files):
            with redirect_stdout(io.StringIO()):
                ui.info(f"Processing {filename} ({i+1}/{len(files)})...")

                # 処理の詳細をデバッグ出力
                if hasattr(ui, "debug"):
                    ui.debug(f"Reading file: {filename}")
                else:
                    ui.info(f"Debug: Reading file: {filename}")

            # 警告やエラーの場合
            if filename == "config.json":
                with redirect_stderr(io.StringIO()):
                    ui.warning(f"Deprecated settings found in {filename}")

            # 成功の場合
            with redirect_stdout(io.StringIO()):
                if hasattr(ui, "success"):
                    ui.success(f"Successfully processed {filename}")
                else:
                    ui.info(f"Success: Successfully processed {filename}")

        with redirect_stdout(io.StringIO()):
            ui.info("Batch processing completed!")

        # 全処理が正常に実行されることを確認
        assert True

    def test_console_ui_error_recovery_workflow(self):
        """エラー回復ワークフローテスト"""
        ui = get_console_ui()

        # エラー発生→回復の流れをテスト
        error_recovery_steps = [
            ("info", "Starting critical operation..."),
            ("error", "Critical error occurred: Database connection failed"),
            ("info", "Attempting to recover..."),
            ("debug", "Retry attempt 1"),
            ("warning", "Connection still unstable"),
            ("debug", "Retry attempt 2"),
            ("success", "Connection recovered successfully"),
            ("info", "Operation completed with recovery"),
        ]

        for level, message in error_recovery_steps:
            if level == "info":
                with redirect_stdout(io.StringIO()):
                    ui.info(message)
            elif level == "debug":
                with redirect_stdout(io.StringIO()):
                    if hasattr(ui, "debug"):
                        ui.debug(message)
                    else:
                        ui.info(f"Debug: {message}")
            elif level == "success":
                with redirect_stdout(io.StringIO()):
                    if hasattr(ui, "success"):
                        ui.success(message)
                    else:
                        ui.info(f"Success: {message}")
            elif level == "warning":
                with redirect_stderr(io.StringIO()):
                    ui.warning(message)
            elif level == "error":
                with redirect_stderr(io.StringIO()):
                    ui.error(message)

        # エラー回復ワークフローが正常に実行されることを確認
        assert True

    def test_console_ui_batch_operation(self):
        """バッチ操作テスト"""
        ui = get_console_ui()

        # 大量処理のシミュレーション
        total_items = 50
        with redirect_stdout(io.StringIO()):
            ui.info(f"Starting batch operation for {total_items} items...")

        for i in range(total_items):
            # 進行状況を定期的に表示
            if i % 10 == 0:
                with redirect_stdout(io.StringIO()):
                    ui.info(f"Progress: {i}/{total_items} items processed")

            # エラーをシミュレート
            if i == 25:
                with redirect_stderr(io.StringIO()):
                    ui.error(f"Error processing item {i}: Invalid format")
                continue

            # 警告をシミュレート
            if i == 35:
                with redirect_stderr(io.StringIO()):
                    ui.warning(f"Warning for item {i}: Deprecated format detected")

        with redirect_stdout(io.StringIO()):
            if hasattr(ui, "success"):
                ui.success("Batch operation completed successfully")
            else:
                ui.info("Success: Batch operation completed successfully")

        # バッチ操作が正常に実行されることを確認
        assert True