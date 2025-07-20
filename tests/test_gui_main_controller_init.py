"""GUI Main Controller Initialization Tests

Issue #501 Phase 4 GUIテスト復旧 - MainController初期化対応
"""

from unittest.mock import Mock, patch

import pytest


class TestMainControllerInit:
    """MainController initialization tests"""

    def test_main_controller_initialization(self):
        """Test MainController initialization"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_model = Mock()

        controller = MainController(mock_view, mock_model)

        assert controller is not None
        assert controller.view == mock_view
        assert controller.model == mock_model
        assert controller.log_viewer is None

    def test_main_controller_with_app_state(self):
        """Test MainController with AppState-like view"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        # Mock view with app_state
        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state

        # Mock required attributes for event setup
        mock_view.log_frame = Mock()

        controller = MainController(mock_view)

        assert controller.app_state == mock_app_state
        assert controller.main_view == mock_view
        # Should create sub-controllers
        assert controller.file_controller is not None
        assert controller.conversion_controller is not None

    def test_main_controller_without_app_state(self):
        """Test MainController without AppState (test environment)"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_model = Mock()

        # Remove app_state if exists
        if hasattr(mock_view, "app_state"):
            del mock_view.app_state

        controller = MainController(mock_view, mock_model)

        assert controller.app_state is None
        assert controller.main_view == mock_view
        # Should not create sub-controllers
        assert controller.file_controller is None
        assert controller.conversion_controller is None

    def test_main_controller_with_injected_controllers(self):
        """Test MainController with injected sub-controllers"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_model = Mock()
        mock_file_controller = Mock()
        mock_conversion_controller = Mock()

        controller = MainController(
            mock_view, mock_model, mock_file_controller, mock_conversion_controller
        )

        assert controller.file_controller == mock_file_controller
        assert controller.conversion_controller == mock_conversion_controller

    def test_setup_event_handlers(self):
        """Test event handlers setup"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        # Mock view with required frames
        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state

        # Mock required frames
        mock_view.file_selection_frame = Mock()
        mock_view.options_frame = Mock()
        mock_view.action_button_frame = Mock()
        mock_view.log_frame = Mock()

        controller = MainController(mock_view)

        # Should set up event handlers
        mock_view.file_selection_frame.set_input_browse_command.assert_called()
        mock_view.file_selection_frame.set_output_browse_command.assert_called()
        mock_view.options_frame.set_source_toggle_command.assert_called()
        mock_view.action_button_frame.set_convert_command.assert_called()
        mock_view.action_button_frame.set_sample_command.assert_called()
        mock_view.action_button_frame.set_help_command.assert_called()
        mock_view.action_button_frame.set_exit_command.assert_called()

    def test_setup_event_handlers_debug_mode(self):
        """Test event handlers setup in debug mode"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        # Mock view with debug mode
        mock_view = Mock()
        mock_app_state = Mock()
        mock_app_state.debug_mode = True
        mock_view.app_state = mock_app_state

        # Mock required frames
        mock_view.file_selection_frame = Mock()
        mock_view.options_frame = Mock()
        mock_view.action_button_frame = Mock()
        mock_view.log_frame = Mock()

        controller = MainController(mock_view)

        # Should set up log command in debug mode
        mock_view.action_button_frame.set_log_command.assert_called()

    def test_add_startup_messages(self):
        """Test startup messages addition"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state
        mock_view.log_frame = Mock()

        controller = MainController(mock_view)

        # Should add startup messages
        expected_calls = [
            (("Kumihan-Formatter GUI が起動しました",),),
            (("使い方がわからない場合は「ヘルプ」ボタンをクリックしてください",),),
        ]
        mock_view.log_frame.add_message.assert_has_calls(expected_calls)
