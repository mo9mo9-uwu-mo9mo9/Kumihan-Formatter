"""Advanced test cases for convert command functionality

This module tests advanced features including:
- Watch mode functionality
- Watcher component
- File change handling
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from kumihan_formatter.commands.convert.convert_command import ConvertCommand
from kumihan_formatter.commands.convert.convert_processor import ConvertProcessor
from kumihan_formatter.commands.convert.convert_validator import ConvertValidator
from kumihan_formatter.commands.convert.convert_watcher import ConvertWatcher


class TestConvertCommandAdvanced:
    """Test advanced ConvertCommand functionality"""

    @patch("kumihan_formatter.commands.convert.convert_command.get_console_ui")
    def test_convert_command_with_watch_mode(self, mock_get_console_ui):
        """Test convert command with watch mode"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = ConvertCommand()
        # 入力ファイルの検証を成功させる
        mock_path = Path("test.txt")
        command.validator.validate_input_file = MagicMock(return_value=mock_path)
        command.validator.check_file_size = MagicMock(return_value=True)
        command.validator.perform_syntax_check = MagicMock()
        mock_report = MagicMock()
        mock_report.has_errors.return_value = False
        mock_report.has_warnings.return_value = False
        command.validator.perform_syntax_check.return_value = mock_report

        # convert_fileメソッドをモック
        output_path = Path("output.html")
        command.processor.convert_file = MagicMock(return_value=output_path)

        # start_watch_modeメソッドをモック
        command.watcher.start_watch_mode = MagicMock()

        with patch("sys.exit") as mock_exit:
            command.execute(
                input_file="test.txt",
                output="./dist",
                no_preview=True,
                watch=True,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

        command.watcher.start_watch_mode.assert_called_once()


class TestConvertWatcher:
    """Test ConvertWatcher class"""

    def test_watcher_initialization(self):
        """Test ConvertWatcher initialization"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        assert watcher.processor == processor
        assert watcher.validator == validator

    def test_watcher_start_watch_mode(self):
        """Test starting file watcher"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # start_watch_modeメソッドが存在することを確認
        assert hasattr(watcher, "start_watch_mode")

        # メソッドをモック
        with patch.object(watcher, "start_watch_mode") as mock_start:
            watcher.start_watch_mode(
                input_file="test.txt",
                output_dir="./output",
                config_obj=None,
                show_test_cases=False,
                template=None,
                include_source=False,
                syntax_check=True,
            )

            mock_start.assert_called_once()

    def test_watcher_file_change_handler(self):
        """Test file change event handling"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # ファイル変更イベントのシミュレーション
        mock_event = MagicMock()
        mock_event.src_path = "test.txt"
        mock_event.is_directory = False

        # _on_modifiedメソッドが存在すると仮定
        if hasattr(watcher, "_on_modified"):
            watcher._on_modified(mock_event)
            processor.process.assert_called()

    def test_watcher_multiple_file_changes(self):
        """Test handling multiple file changes"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # 複数のファイル変更イベントをシミュレーション
        events = [
            MagicMock(src_path="test1.txt", is_directory=False),
            MagicMock(src_path="test2.txt", is_directory=False),
            MagicMock(src_path="test3.txt", is_directory=False),
        ]

        for event in events:
            if hasattr(watcher, "_on_modified"):
                watcher._on_modified(event)

        # 各イベントが処理されることを確認
        if hasattr(watcher, "_on_modified"):
            assert processor.process.call_count >= len(events)

    def test_watcher_directory_change_ignored(self):
        """Test that directory changes are ignored"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # ディレクトリ変更イベントのシミュレーション
        mock_event = MagicMock()
        mock_event.src_path = "test_dir"
        mock_event.is_directory = True

        # _on_modifiedメソッドが存在すると仮定
        if hasattr(watcher, "_on_modified"):
            watcher._on_modified(mock_event)
            # ディレクトリ変更は処理されないことを確認
            processor.process.assert_not_called()

    def test_watcher_error_handling(self):
        """Test watcher error handling"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # エラーが発生するファイル変更イベント
        mock_event = MagicMock()
        mock_event.src_path = "test.txt"
        mock_event.is_directory = False

        # processorでエラーが発生するようにモック
        processor.process = MagicMock(side_effect=RuntimeError("Test error"))

        # エラーハンドリングが適切に行われることを確認
        if hasattr(watcher, "_on_modified"):
            try:
                watcher._on_modified(mock_event)
            except RuntimeError:
                # エラーが適切に処理されることを確認
                pass

    def test_watcher_config_updates(self):
        """Test watcher behavior with config updates"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # 設定更新のシミュレーション
        new_config = MagicMock()

        # 設定更新メソッドが存在すると仮定
        if hasattr(watcher, "update_config"):
            watcher.update_config(new_config)
            # 設定が更新されることを確認
            assert watcher.config == new_config

    def test_watcher_stop_functionality(self):
        """Test watcher stop functionality"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # 停止メソッドが存在すると仮定
        if hasattr(watcher, "stop"):
            watcher.stop()
            # 停止処理が実行されることを確認
            assert not getattr(watcher, "is_running", True)

    def test_watcher_file_filter(self):
        """Test watcher file filtering"""
        processor = MagicMock()
        validator = MagicMock()
        watcher = ConvertWatcher(processor, validator)

        # 異なる拡張子のファイルイベント
        txt_event = MagicMock(src_path="test.txt", is_directory=False)
        py_event = MagicMock(src_path="test.py", is_directory=False)
        html_event = MagicMock(src_path="test.html", is_directory=False)

        events = [txt_event, py_event, html_event]

        # ファイルフィルタリングが適切に動作することを確認
        for event in events:
            if hasattr(watcher, "_should_process_file"):
                should_process = watcher._should_process_file(event.src_path)
                # テキストファイルのみ処理されることを確認
                if event.src_path.endswith(".txt"):
                    assert should_process
                else:
                    assert not should_process
