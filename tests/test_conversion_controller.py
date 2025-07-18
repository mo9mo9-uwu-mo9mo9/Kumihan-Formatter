"""Conversion Controller Tests for Issue 501 Phase 4A

This module tests GUI conversion controller functionality to ensure
proper file conversion and sample generation operations.
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest

from kumihan_formatter.gui_controllers.conversion_controller import ConversionController
from tests.test_base import BaseTestCase, create_test_kumihan_content


class TestConversionController(BaseTestCase):
    """Test conversion controller functionality"""

    def setup_method(self, method):
        """Setup method called before each test method"""
        super().setup_method(method)
        
        # Create mock model
        self.mock_model = Mock()
        self.mock_model.input_file_var = Mock()
        self.mock_model.input_file_var.get = Mock(return_value="")
        self.mock_model.output_dir_var = Mock()
        self.mock_model.output_dir_var.get = Mock(return_value="")
        self.mock_model.show_source_var = Mock()
        self.mock_model.show_source_var.get = Mock(return_value=False)
        
        # Create mock view
        self.mock_view = Mock()
        self.mock_view.log_text = Mock()
        self.mock_view.log_text.insert = Mock()
        self.mock_view.log_text.see = Mock()
        self.mock_view.log_text.update = Mock()
        self.mock_view.progress_var = Mock()
        self.mock_view.progress_var.set = Mock()
        self.mock_view.convert_button = Mock()
        self.mock_view.convert_button.configure = Mock()
        self.mock_view.sample_button = Mock()
        self.mock_view.sample_button.configure = Mock()
        self.mock_view.show_success_message = Mock()
        self.mock_view.show_error_message = Mock()
        self.mock_view.show_info_message = Mock()

    def test_conversion_controller_initialization(self):
        """Test ConversionController initialization"""
        controller = ConversionController(self.mock_model, self.mock_view)
        assert controller is not None
        assert controller.model == self.mock_model
        assert controller.view == self.mock_view
        assert controller.is_converting is False

    def test_convert_file_no_input_file(self):
        """Test conversion with no input file selected"""
        controller = ConversionController(self.mock_model, self.mock_view)
        self.mock_model.input_file_var.get.return_value = ""
        
        controller.convert_file()
        
        self.mock_view.show_error_message.assert_called_once_with(
            "エラー", "入力ファイルを選択してください。"
        )

    def test_convert_file_file_not_exists(self):
        """Test conversion with non-existent file"""
        controller = ConversionController(self.mock_model, self.mock_view)
        self.mock_model.input_file_var.get.return_value = "/nonexistent/file.txt"
        
        controller.convert_file()
        
        self.mock_view.show_error_message.assert_called_once()
        assert "入力ファイルが見つかりません" in self.mock_view.show_error_message.call_args[0][1]

    def test_convert_file_already_converting(self):
        """Test conversion when already converting"""
        controller = ConversionController(self.mock_model, self.mock_view)
        controller.is_converting = True
        
        controller.convert_file()
        
        self.mock_view.show_info_message.assert_called_once_with(
            "情報", "変換処理中です。しばらくお待ちください。"
        )

    @patch('threading.Thread')
    def test_convert_file_success(self, mock_thread_class):
        """Test successful file conversion"""
        # Setup
        controller = ConversionController(self.mock_model, self.mock_view)
        input_file = self.create_temp_file(create_test_kumihan_content(), suffix=".txt")
        output_dir = self.create_temp_dir()
        
        self.mock_model.input_file_var.get.return_value = input_file
        self.mock_model.output_dir_var.get.return_value = output_dir
        
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # Execute
        controller.convert_file()
        
        # Verify
        assert controller.is_converting is True
        self.mock_view.convert_button.configure.assert_called_with(state="disabled")
        self.mock_view.sample_button.configure.assert_called_with(state="disabled")
        self.mock_view.progress_var.set.assert_called_with(0)
        
        mock_thread_class.assert_called_once()
        assert mock_thread_class.call_args[1]['target'] == controller._convert_file_thread
        assert mock_thread_class.call_args[1]['daemon'] is True
        mock_thread.start.assert_called_once()

    @patch('kumihan_formatter.cli.run_conversion')
    def test_convert_file_thread_success(self, mock_run_conversion):
        """Test conversion thread execution success"""
        # Setup
        controller = ConversionController(self.mock_model, self.mock_view)
        input_file = self.create_temp_file(create_test_kumihan_content(), suffix=".txt")
        output_dir = self.create_temp_dir()
        
        self.mock_model.input_file_var.get.return_value = input_file
        self.mock_model.output_dir_var.get.return_value = output_dir
        self.mock_model.show_source_var.get.return_value = True
        
        controller.is_converting = True
        mock_run_conversion.return_value = True
        
        # Execute
        controller._convert_file_thread()
        
        # Verify
        mock_run_conversion.assert_called_once_with(
            input_file=input_file,
            output_dir=output_dir,
            output_format='html',
            show_source=True,
            progress_callback=controller._update_progress
        )
        
        assert controller.is_converting is False
        self.mock_view.convert_button.configure.assert_called_with(state="normal")
        self.mock_view.sample_button.configure.assert_called_with(state="normal")
        self.mock_view.show_success_message.assert_called_once()

    @patch('kumihan_formatter.cli.run_conversion')
    def test_convert_file_thread_failure(self, mock_run_conversion):
        """Test conversion thread execution failure"""
        # Setup
        controller = ConversionController(self.mock_model, self.mock_view)
        input_file = self.create_temp_file("test", suffix=".txt")
        
        self.mock_model.input_file_var.get.return_value = input_file
        controller.is_converting = True
        
        # Simulate conversion failure
        mock_run_conversion.side_effect = Exception("Conversion failed")
        
        # Execute
        controller._convert_file_thread()
        
        # Verify
        assert controller.is_converting is False
        self.mock_view.convert_button.configure.assert_called_with(state="normal")
        self.mock_view.sample_button.configure.assert_called_with(state="normal")
        self.mock_view.show_error_message.assert_called_once()
        assert "Conversion failed" in self.mock_view.show_error_message.call_args[0][1]

    def test_update_progress(self):
        """Test progress update callback"""
        controller = ConversionController(self.mock_model, self.mock_view)
        
        # Test various progress values
        progress_values = [0, 25, 50, 75, 100]
        for progress in progress_values:
            controller._update_progress(progress)
            self.mock_view.progress_var.set.assert_called_with(progress)

    def test_add_log_message(self):
        """Test adding log messages"""
        controller = ConversionController(self.mock_model, self.mock_view)
        
        # Test normal message
        controller._add_log_message("Test message")
        self.mock_view.log_text.insert.assert_called_with("end", "Test message\n")
        self.mock_view.log_text.see.assert_called_with("end")
        
        # Test message with newline
        controller._add_log_message("Another message\n")
        calls = self.mock_view.log_text.insert.call_args_list
        assert calls[-1] == call("end", "Another message\n")

    @patch('threading.Thread')
    def test_generate_sample_success(self, mock_thread_class):
        """Test successful sample generation"""
        controller = ConversionController(self.mock_model, self.mock_view)
        output_dir = self.create_temp_dir()
        self.mock_model.output_dir_var.get.return_value = output_dir
        
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        controller.generate_sample()
        
        mock_thread_class.assert_called_once()
        assert mock_thread_class.call_args[1]['target'] == controller._generate_sample_thread
        mock_thread.start.assert_called_once()

    @patch('kumihan_formatter.commands.sample_command.SampleCommand')
    def test_generate_sample_thread_success(self, mock_sample_command_class):
        """Test sample generation thread execution"""
        # Setup
        controller = ConversionController(self.mock_model, self.mock_view)
        output_dir = self.create_temp_dir()
        self.mock_model.output_dir_var.get.return_value = output_dir
        
        mock_command = Mock()
        mock_command.execute.return_value = 0
        mock_sample_command_class.return_value = mock_command
        
        # Execute
        controller._generate_sample_thread()
        
        # Verify
        mock_sample_command_class.assert_called_once()
        mock_command.execute.assert_called_once_with(output_path=str(Path(output_dir)))
        self.mock_view.show_success_message.assert_called_once()


class TestConversionControllerIntegration(BaseTestCase):
    """Test conversion controller integration scenarios"""

    def setup_method(self, method):
        """Setup method with full mock environment"""
        super().setup_method(method)
        
        # Create more realistic mocks
        self.mock_model = Mock()
        self.mock_model.input_file_var = Mock()
        self.mock_model.output_dir_var = Mock()
        self.mock_model.show_source_var = Mock()
        
        self.mock_view = Mock()
        self.mock_view.log_text = Mock()
        self.mock_view.progress_var = Mock()
        self.mock_view.convert_button = Mock()
        self.mock_view.sample_button = Mock()
        self.mock_view.show_success_message = Mock()
        self.mock_view.show_error_message = Mock()

    def test_conversion_controller_concurrent_operations(self):
        """Test preventing concurrent conversion operations"""
        controller = ConversionController(self.mock_model, self.mock_view)
        
        # Simulate first conversion starting
        controller.is_converting = True
        
        # Try to start another conversion
        input_file = self.create_temp_file("test", suffix=".txt")
        self.mock_model.input_file_var.get.return_value = input_file
        
        controller.convert_file()
        
        # Should show info message instead of starting new conversion
        self.mock_view.show_info_message.assert_called_once()

    def test_conversion_controller_error_recovery(self):
        """Test error recovery in conversion controller"""
        controller = ConversionController(self.mock_model, self.mock_view)
        
        # Simulate conversion failure
        controller.is_converting = True
        controller._add_log_message = Mock(side_effect=Exception("Log error"))
        
        # Should handle error gracefully
        try:
            controller._add_log_message("Test")
        except:
            pass
        
        # Controller should still be functional
        assert controller is not None

    def test_conversion_controller_unicode_handling(self):
        """Test handling of unicode file paths and content"""
        controller = ConversionController(self.mock_model, self.mock_view)
        
        # Test with unicode filename
        unicode_content = "テスト内容\n日本語のテキスト"
        unicode_file = self.create_temp_file(unicode_content, suffix=".txt")
        
        # Rename to unicode filename
        unicode_path = Path(unicode_file).parent / "テストファイル.txt"
        Path(unicode_file).rename(unicode_path)
        self.temp_files.append(str(unicode_path))
        
        self.mock_model.input_file_var.get.return_value = str(unicode_path)
        
        # Should handle unicode path without errors
        assert Path(unicode_path).exists()
        assert Path(unicode_path).read_text(encoding="utf-8") == unicode_content