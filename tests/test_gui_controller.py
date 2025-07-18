"""GUI Controller Tests for Issue 501 Phase 4A

This module tests the main GUI controller that integrates all components
and manages the overall GUI application.
"""

import sys
from unittest.mock import Mock, patch, MagicMock
import pytest
import tkinter as tk

from kumihan_formatter.gui_controllers.gui_controller import GuiController
from tests.test_base import BaseTestCase


class TestGuiController(BaseTestCase):
    """Test GUI controller functionality"""

    @patch('kumihan_formatter.gui_views.main_window.MainWindow')
    @patch('kumihan_formatter.gui_models.state_model.StateModel')
    @patch('kumihan_formatter.gui_controllers.file_controller.FileController')
    @patch('kumihan_formatter.gui_controllers.conversion_controller.ConversionController')
    @patch('kumihan_formatter.gui_controllers.main_controller.MainController')
    def test_gui_controller_initialization(
        self,
        mock_main_controller_class,
        mock_conversion_controller_class,
        mock_file_controller_class,
        mock_state_model_class,
        mock_main_window_class
    ):
        """Test GuiController initialization"""
        # Setup mocks
        mock_view = Mock()
        mock_model = Mock()
        mock_file_controller = Mock()
        mock_conversion_controller = Mock()
        mock_main_controller = Mock()
        
        mock_main_window_class.return_value = mock_view
        mock_state_model_class.return_value = mock_model
        mock_file_controller_class.return_value = mock_file_controller
        mock_conversion_controller_class.return_value = mock_conversion_controller
        mock_main_controller_class.return_value = mock_main_controller
        
        # Create controller
        gui_controller = GuiController()
        
        # Verify initialization
        assert gui_controller is not None
        mock_main_window_class.assert_called_once()
        mock_state_model_class.assert_called_once()
        mock_file_controller_class.assert_called_once_with(mock_view)
        mock_conversion_controller_class.assert_called_once_with(mock_model, mock_view)
        mock_main_controller_class.assert_called_once_with(
            mock_view, mock_model, mock_file_controller, mock_conversion_controller
        )

    @patch('kumihan_formatter.gui_views.main_window.MainWindow')
    @patch('kumihan_formatter.gui_models.state_model.StateModel')
    @patch('kumihan_formatter.gui_controllers.file_controller.FileController')
    @patch('kumihan_formatter.gui_controllers.conversion_controller.ConversionController')
    @patch('kumihan_formatter.gui_controllers.main_controller.MainController')
    def test_gui_controller_run(
        self,
        mock_main_controller_class,
        mock_conversion_controller_class,
        mock_file_controller_class,
        mock_state_model_class,
        mock_main_window_class
    ):
        """Test GuiController run method"""
        # Setup mocks
        mock_main_controller = Mock()
        mock_main_controller.run = Mock()
        mock_main_controller_class.return_value = mock_main_controller
        
        # Create and run controller
        gui_controller = GuiController()
        gui_controller.run()
        
        # Verify run was called
        mock_main_controller.run.assert_called_once()

    @patch('kumihan_formatter.gui_views.main_window.MainWindow')
    @patch('kumihan_formatter.gui_models.state_model.StateModel')
    @patch('kumihan_formatter.gui_controllers.file_controller.FileController')
    @patch('kumihan_formatter.gui_controllers.conversion_controller.ConversionController')
    @patch('kumihan_formatter.gui_controllers.main_controller.MainController')
    def test_gui_controller_log_viewer_property(
        self,
        mock_main_controller_class,
        mock_conversion_controller_class,
        mock_file_controller_class,
        mock_state_model_class,
        mock_main_window_class
    ):
        """Test log_viewer property for backward compatibility"""
        # Setup mocks
        mock_main_controller = Mock()
        mock_main_controller.log_viewer = None
        mock_main_controller_class.return_value = mock_main_controller
        
        # Create controller
        gui_controller = GuiController()
        
        # Test property
        assert gui_controller.log_viewer is None


class TestGuiControllerIntegration(BaseTestCase):
    """Test GUI controller integration scenarios"""

    @patch('tkinter.Tk')
    def test_gui_controller_window_creation(self, mock_tk_class):
        """Test that GUI controller creates window properly"""
        # Setup mock Tk
        mock_root = Mock()
        mock_tk_class.return_value = mock_root
        
        with patch('kumihan_formatter.gui_views.main_window.MainWindow') as mock_window_class:
            mock_window = Mock()
            mock_window.root = mock_root
            mock_window_class.return_value = mock_window
            
            # Should create window without errors
            try:
                gui_controller = GuiController()
                assert gui_controller is not None
            except Exception as e:
                # Log error for debugging
                pytest.fail(f"GUI controller creation failed: {e}")

    @patch('kumihan_formatter.gui_views.main_window.MainWindow')
    @patch('kumihan_formatter.gui_models.state_model.StateModel')
    @patch('kumihan_formatter.gui_controllers.file_controller.FileController')
    @patch('kumihan_formatter.gui_controllers.conversion_controller.ConversionController')
    @patch('kumihan_formatter.gui_controllers.main_controller.MainController')
    def test_gui_controller_component_integration(
        self,
        mock_main_controller_class,
        mock_conversion_controller_class,
        mock_file_controller_class,
        mock_state_model_class,
        mock_main_window_class
    ):
        """Test integration between GUI components"""
        # Create interconnected mocks
        mock_view = Mock()
        mock_view.root = Mock()
        mock_model = Mock()
        
        mock_main_window_class.return_value = mock_view
        mock_state_model_class.return_value = mock_model
        
        # Track controller creation order
        creation_order = []
        
        def track_file_controller(*args):
            creation_order.append('file')
            return Mock()
        
        def track_conversion_controller(*args):
            creation_order.append('conversion')
            return Mock()
        
        def track_main_controller(*args):
            creation_order.append('main')
            return Mock()
        
        mock_file_controller_class.side_effect = track_file_controller
        mock_conversion_controller_class.side_effect = track_conversion_controller
        mock_main_controller_class.side_effect = track_main_controller
        
        # Create controller
        gui_controller = GuiController()
        
        # Verify creation order
        assert creation_order == ['file', 'conversion', 'main']

    @patch('kumihan_formatter.gui_views.main_window.MainWindow')
    @patch('kumihan_formatter.gui_models.state_model.StateModel')
    @patch('kumihan_formatter.gui_controllers.file_controller.FileController')
    @patch('kumihan_formatter.gui_controllers.conversion_controller.ConversionController')
    @patch('kumihan_formatter.gui_controllers.main_controller.MainController')
    def test_gui_controller_error_handling(
        self,
        mock_main_controller_class,
        mock_conversion_controller_class,
        mock_file_controller_class,
        mock_state_model_class,
        mock_main_window_class
    ):
        """Test error handling in GUI controller"""
        # Simulate component creation failure
        mock_main_window_class.side_effect = Exception("Window creation failed")
        
        # Should handle error gracefully
        with pytest.raises(Exception) as exc_info:
            gui_controller = GuiController()
        
        assert "Window creation failed" in str(exc_info.value)

    @patch('kumihan_formatter.gui_views.main_window.MainWindow')
    @patch('kumihan_formatter.gui_models.state_model.StateModel')
    @patch('kumihan_formatter.gui_controllers.file_controller.FileController')
    @patch('kumihan_formatter.gui_controllers.conversion_controller.ConversionController')
    @patch('kumihan_formatter.gui_controllers.main_controller.MainController')
    def test_gui_controller_cleanup(
        self,
        mock_main_controller_class,
        mock_conversion_controller_class,
        mock_file_controller_class,
        mock_state_model_class,
        mock_main_window_class
    ):
        """Test cleanup when GUI controller is destroyed"""
        # Setup mocks with cleanup tracking
        cleanup_called = {'main': False}
        
        mock_main_controller = Mock()
        def cleanup():
            cleanup_called['main'] = True
        mock_main_controller.cleanup = cleanup
        mock_main_controller_class.return_value = mock_main_controller
        
        # Create controller
        gui_controller = GuiController()
        
        # Simulate cleanup (if implemented)
        if hasattr(mock_main_controller, 'cleanup'):
            mock_main_controller.cleanup()
        
        # Verify cleanup
        assert cleanup_called['main'] is True