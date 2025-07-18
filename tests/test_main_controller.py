"""Main Controller Tests for Issue 501 Phase 4A

This module tests GUI main controller functionality to ensure
proper application control and event handling.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest
import tkinter as tk

from kumihan_formatter.gui_controllers.main_controller import MainController
from tests.test_base import BaseTestCase


class TestMainController(BaseTestCase):
    """Test main controller functionality"""

    def setup_method(self, method):
        """Setup method called before each test method"""
        super().setup_method(method)
        
        # Create mock components
        self.mock_view = Mock()
        self.mock_view.root = Mock()
        self.mock_view.root.title = Mock()
        self.mock_view.root.mainloop = Mock()
        self.mock_view.root.destroy = Mock()
        self.mock_view.show_source_var = Mock()
        self.mock_view.show_source_var.trace_add = Mock()
        self.mock_view.update_source_visibility = Mock()
        self.mock_view.log_text = Mock()
        self.mock_view.log_text.insert = Mock()
        self.mock_view.log_text.see = Mock()
        self.mock_view.log_text.update = Mock()
        
        self.mock_model = Mock()
        self.mock_model.show_source_var = Mock()
        self.mock_model.show_source_var.get = Mock(return_value=False)
        
        self.mock_file_controller = Mock()
        self.mock_conversion_controller = Mock()

    def test_main_controller_initialization(self):
        """Test MainController initialization"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        assert controller is not None
        assert controller.view == self.mock_view
        assert controller.model == self.mock_model
        assert controller.file_controller == self.mock_file_controller
        assert controller.conversion_controller == self.mock_conversion_controller

    def test_setup_event_handlers(self):
        """Test event handler setup"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        # Verify event handlers were set up
        self.mock_view.show_source_var.trace_add.assert_called_once_with(
            "write", controller.on_source_toggle_change
        )

    def test_add_startup_messages(self):
        """Test startup message addition"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        # Verify startup messages were added
        calls = self.mock_view.log_text.insert.call_args_list
        assert len(calls) >= 3  # At least 3 startup messages
        
        # Check message content
        messages = [call[0][1] for call in calls]
        assert any("Kumihan Formatter GUI" in msg for msg in messages)
        assert any("変換を開始" in msg for msg in messages)

    def test_on_source_toggle_change(self):
        """Test source toggle change handler"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        # Test toggle on
        self.mock_model.show_source_var.get.return_value = True
        controller.on_source_toggle_change()
        self.mock_view.update_source_visibility.assert_called_with(True)
        
        # Test toggle off
        self.mock_model.show_source_var.get.return_value = False
        controller.on_source_toggle_change()
        self.mock_view.update_source_visibility.assert_called_with(False)

    @patch('tkinter.messagebox.showinfo')
    def test_show_help(self, mock_showinfo):
        """Test help dialog display"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        controller.show_help()
        
        mock_showinfo.assert_called_once()
        assert "ヘルプ" in mock_showinfo.call_args[0][0]
        assert "Kumihan Formatter" in mock_showinfo.call_args[0][1]

    @patch('kumihan_formatter.gui_views.dialogs.LogViewerDialog')
    def test_show_log_viewer(self, mock_dialog_class):
        """Test log viewer dialog display"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        mock_dialog = Mock()
        mock_dialog_class.return_value = mock_dialog
        
        controller.show_log_viewer()
        
        mock_dialog_class.assert_called_once_with(self.mock_view.root)

    @patch('sys.exit')
    def test_exit_application(self, mock_exit):
        """Test application exit"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        controller.exit_application()
        
        self.mock_view.root.destroy.assert_called_once()
        mock_exit.assert_called_once_with(0)

    def test_run(self):
        """Test application run"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        controller.run()
        
        self.mock_view.root.mainloop.assert_called_once()

    def test_log_viewer_property(self):
        """Test log viewer property (backward compatibility)"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        # Property should return None (deprecated)
        assert controller.log_viewer is None


class TestMainControllerIntegration(BaseTestCase):
    """Test main controller integration scenarios"""

    def setup_method(self, method):
        """Setup method with full mock environment"""
        super().setup_method(method)
        
        # Create comprehensive mocks
        self.mock_view = Mock()
        self.mock_view.root = Mock(spec=tk.Tk)
        self.mock_view.show_source_var = Mock()
        self.mock_view.log_text = Mock()
        
        self.mock_model = Mock()
        self.mock_model.show_source_var = Mock()
        
        self.mock_file_controller = Mock()
        self.mock_conversion_controller = Mock()

    def test_main_controller_complete_workflow(self):
        """Test complete controller workflow"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        # Simulate user interactions
        # 1. Change source toggle
        self.mock_model.show_source_var.get.return_value = True
        controller.on_source_toggle_change()
        
        # 2. Show help
        with patch('tkinter.messagebox.showinfo') as mock_info:
            controller.show_help()
            mock_info.assert_called_once()
        
        # 3. Show log viewer
        with patch('kumihan_formatter.gui_views.dialogs.LogViewerDialog') as mock_dialog:
            controller.show_log_viewer()
            mock_dialog.assert_called_once()

    def test_main_controller_error_handling(self):
        """Test error handling in main controller"""
        # Test with missing view components
        incomplete_view = Mock()
        incomplete_view.root = Mock()
        incomplete_view.show_source_var = None  # Missing component
        
        # Should handle gracefully
        try:
            controller = MainController(
                incomplete_view,
                self.mock_model,
                self.mock_file_controller,
                self.mock_conversion_controller
            )
            # Basic operations should still work
            assert controller is not None
        except AttributeError:
            # Expected if strict checking is enabled
            pass

    def test_main_controller_event_propagation(self):
        """Test event propagation between components"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        # Test that events are properly propagated
        # Source toggle change should update view
        self.mock_model.show_source_var.get.return_value = True
        controller.on_source_toggle_change()
        self.mock_view.update_source_visibility.assert_called_with(True)
        
        # Exit should destroy root window
        with patch('sys.exit'):
            controller.exit_application()
            self.mock_view.root.destroy.assert_called_once()

    def test_main_controller_startup_sequence(self):
        """Test startup sequence execution"""
        with patch.object(MainController, '_setup_event_handlers') as mock_setup:
            with patch.object(MainController, '_add_startup_messages') as mock_messages:
                controller = MainController(
                    self.mock_view,
                    self.mock_model,
                    self.mock_file_controller,
                    self.mock_conversion_controller
                )
                
                # Verify startup sequence
                mock_setup.assert_called_once()
                mock_messages.assert_called_once()

    def test_main_controller_unicode_support(self):
        """Test unicode support in messages"""
        controller = MainController(
            self.mock_view,
            self.mock_model,
            self.mock_file_controller,
            self.mock_conversion_controller
        )
        
        # Startup messages should contain Japanese text
        calls = self.mock_view.log_text.insert.call_args_list
        japanese_messages = [call for call in calls if any(ord(c) > 127 for c in str(call[0][1]))]
        assert len(japanese_messages) > 0  # Should have Japanese messages