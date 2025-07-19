"""GUI Conversion Controller Tests

Issue #501 Phase 4 GUIテスト復旧 - ConversionController対応
"""

import threading
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestConversionController:
    """ConversionController comprehensive tests"""

    def test_conversion_controller_initialization(self):
        """Test ConversionController initialization"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Test with mock model and view
        mock_model = Mock()
        mock_view = Mock()

        controller = ConversionController(mock_model, mock_view)
        assert controller is not None
        assert controller.model == mock_model
        assert controller.view == mock_view
        assert controller.is_converting is False

    def test_conversion_controller_with_app_state(self):
        """Test ConversionController with AppState-like model"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock model with config attribute (AppState-like)
        mock_app_state = Mock()
        mock_app_state.config = Mock()
        mock_app_state.is_ready_for_conversion.return_value = (True, "Ready")

        mock_view = Mock()

        controller = ConversionController(mock_app_state, mock_view)
        assert controller.app_state == mock_app_state
        assert controller.main_view == mock_view

    def test_conversion_controller_thread_handler_injection(self):
        """Test thread handler dependency injection"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        mock_model = Mock()
        mock_view = Mock()
        mock_thread_handler = Mock()

        controller = ConversionController(mock_model, mock_view, mock_thread_handler)
        assert controller.threads == mock_thread_handler

    def test_convert_file_without_app_state(self):
        """Test convert_file method without AppState (test environment)"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock model without config (test environment)
        mock_model = Mock()
        mock_model.input_file_var = Mock()
        mock_model.input_file_var.get.return_value = "test_file.txt"

        mock_view = Mock()
        # Mock hasattr to return True for show_success_message
        with patch("builtins.hasattr") as mock_hasattr:
            mock_hasattr.side_effect = lambda obj, attr: attr in [
                "show_success_message",
                "input_file_var",
            ]
            mock_view.show_success_message = Mock()

            mock_thread_handler = Mock()

            controller = ConversionController(
                mock_model, mock_view, mock_thread_handler
            )
            controller.convert_file()

            # Should show success message in test environment
            mock_view.show_success_message.assert_called_once_with(
                "成功", "変換が完了しました。"
            )

    def test_convert_file_without_input_file(self):
        """Test convert_file method without input file"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock model without input file
        mock_model = Mock()
        mock_model.input_file_var = Mock()
        mock_model.input_file_var.get.return_value = ""

        mock_view = Mock()
        # Mock hasattr to return True for show_error_message
        with patch("builtins.hasattr") as mock_hasattr:
            mock_hasattr.side_effect = lambda obj, attr: attr in [
                "show_error_message",
                "input_file_var",
            ]
            mock_view.show_error_message = Mock()

            controller = ConversionController(mock_model, mock_view)
            controller.convert_file()

            # Should show error message
            mock_view.show_error_message.assert_called_once_with(
                "エラー", "入力ファイルを選択してください。"
            )

    def test_convert_file_with_app_state(self):
        """Test convert_file method with AppState"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock AppState model
        mock_app_state = Mock()
        mock_app_state.config = Mock()
        mock_app_state.is_ready_for_conversion.return_value = (True, "Ready")

        mock_view = Mock()
        mock_view.set_ui_enabled = Mock()

        mock_thread_handler = Mock()

        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            controller = ConversionController(
                mock_app_state, mock_view, mock_thread_handler
            )
            controller.convert_file()

            # Should disable UI and start thread
            mock_view.set_ui_enabled.assert_called_with(False)
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            assert controller.is_converting is True

    def test_convert_file_not_ready(self):
        """Test convert_file when not ready for conversion"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock AppState model not ready
        mock_app_state = Mock()
        mock_app_state.config = Mock()
        mock_app_state.is_ready_for_conversion.return_value = (False, "Not ready")

        mock_view = Mock()

        with patch("tkinter.messagebox.showerror") as mock_error:
            controller = ConversionController(mock_app_state, mock_view)
            controller.convert_file()

            # Should show error message
            mock_error.assert_called_once_with("エラー", "Not ready")

    def test_generate_sample_without_app_state(self):
        """Test generate_sample method without AppState"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        mock_model = Mock()
        mock_view = Mock()

        # Mock hasattr to return True for show_success_message
        with patch("builtins.hasattr") as mock_hasattr:
            mock_hasattr.side_effect = lambda obj, attr: attr == "show_success_message"
            mock_view.show_success_message = Mock()

            mock_thread_handler = Mock()

            controller = ConversionController(
                mock_model, mock_view, mock_thread_handler
            )
            controller.generate_sample()

            # Should show success message in test environment
            mock_view.show_success_message.assert_called_once_with(
                "成功", "サンプルが生成されました。"
            )

    def test_generate_sample_with_app_state(self):
        """Test generate_sample method with AppState"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock AppState model
        mock_app_state = Mock()
        mock_app_state.config = Mock()

        mock_view = Mock()
        mock_view.set_ui_enabled = Mock()

        mock_thread_handler = Mock()

        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            controller = ConversionController(
                mock_app_state, mock_view, mock_thread_handler
            )
            controller.generate_sample()

            # Should disable UI and start thread
            mock_view.set_ui_enabled.assert_called_with(False)
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()

    def test_convert_file_error_handling(self):
        """Test convert_file error handling"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock model that raises exception
        mock_model = Mock()
        mock_model.input_file_var.get.side_effect = Exception("Test error")

        mock_view = Mock()
        mock_thread_handler = Mock()

        controller = ConversionController(mock_model, mock_view, mock_thread_handler)

        # Should handle exception gracefully
        controller.convert_file()
        assert controller.is_converting is False

    def test_generate_sample_error_handling(self):
        """Test generate_sample error handling"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock model that raises exception during initialization
        mock_model = Mock()
        mock_view = Mock()

        controller = ConversionController(mock_model, mock_view)
        controller.threads = None  # Simulate initialization error

        # Should handle exception gracefully
        controller.generate_sample()

    def test_initialization_error_handling(self):
        """Test initialization error handling"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        # Mock model that raises exception during hasattr check
        mock_model = Mock()
        # Remove config attribute to simulate test environment
        if hasattr(mock_model, "config"):
            del mock_model.config

        mock_view = Mock()

        # Should handle initialization without crashing
        controller = ConversionController(mock_model, mock_view)
        assert controller is not None

    def test_threads_none_handling(self):
        """Test handling when threads is None"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        mock_model = Mock()
        mock_view = Mock()

        controller = ConversionController(mock_model, mock_view)
        controller.threads = None

        # Should handle None threads gracefully
        controller.convert_file()  # Should not crash
        controller.generate_sample()  # Should not crash

    def test_logging_integration(self):
        """Test logging integration"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        with patch(
            "kumihan_formatter.gui_controllers.conversion_controller.log_gui_event"
        ) as mock_log:
            mock_model = Mock()
            mock_view = Mock()
            mock_view.show_success_message = Mock()

            controller = ConversionController(mock_model, mock_view)
            controller.convert_file()

            # Should log button click
            mock_log.assert_called()

    def test_daemon_thread_configuration(self):
        """Test that threads are configured as daemon threads"""
        from kumihan_formatter.gui_controllers.conversion_controller import (
            ConversionController,
        )

        mock_app_state = Mock()
        mock_app_state.config = Mock()
        mock_app_state.is_ready_for_conversion.return_value = (True, "Ready")

        mock_view = Mock()
        mock_view.set_ui_enabled = Mock()

        mock_thread_handler = Mock()

        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            controller = ConversionController(
                mock_app_state, mock_view, mock_thread_handler
            )
            controller.convert_file()

            # Should set daemon = True
            assert mock_thread_instance.daemon is True
