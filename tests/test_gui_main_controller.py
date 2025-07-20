"""GUI Main Controller Tests

Issue #501 Phase 4 GUIテスト復旧 - MainController対応
"""

from unittest.mock import Mock, patch

import pytest


class TestMainController:
    """MainController comprehensive tests"""

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

    def test_on_source_toggle_change_with_app_state(self):
        """Test source toggle change with AppState"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state
        mock_view.log_frame = Mock()

        # Mock config methods
        mock_app_state.config.get_include_source.return_value = True

        controller = MainController(mock_view)
        controller.on_source_toggle_change()

        # Should set template and add message
        mock_app_state.config.set_template.assert_called_with(
            "base-with-source-toggle.html.j2"
        )
        mock_view.log_frame.add_message.assert_called_with(
            "ソース表示機能が有効になりました"
        )

    def test_on_source_toggle_change_disable_source(self):
        """Test source toggle change to disable source"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state
        mock_view.log_frame = Mock()

        # Mock config methods - disable source
        mock_app_state.config.get_include_source.return_value = False

        controller = MainController(mock_view)
        controller.on_source_toggle_change()

        # Should set base template
        mock_app_state.config.set_template.assert_called_with("base.html.j2")
        mock_view.log_frame.add_message.assert_called_with(
            "ソース表示機能が無効になりました"
        )

    def test_on_source_toggle_change_without_app_state(self):
        """Test source toggle change without AppState"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_model = Mock()
        mock_model.show_source_var = Mock()
        mock_model.show_source_var.get.return_value = True

        if hasattr(mock_view, "app_state"):
            del mock_view.app_state

        controller = MainController(mock_view, mock_model)
        # Should not crash
        controller.on_source_toggle_change()

    def test_show_help(self):
        """Test show help method"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_view.help_dialog = Mock()

        controller = MainController(mock_view)
        controller.show_help()

        # Should show help dialog
        mock_view.help_dialog.show.assert_called_once()

    def test_show_log_viewer_new(self):
        """Test show log viewer when not open"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_view.root = Mock()

        controller = MainController(mock_view)

        with patch(
            "kumihan_formatter.core.log_viewer.LogViewerWindow"
        ) as mock_log_viewer_class:
            mock_log_viewer = Mock()
            mock_log_viewer_class.return_value = mock_log_viewer
            controller.log_viewer = None

            controller.show_log_viewer()

            # Should create new log viewer
            mock_log_viewer_class.assert_called_once_with(mock_view.root)
            mock_log_viewer.show.assert_called_once()

    def test_show_log_viewer_already_open(self):
        """Test show log viewer when already open"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        controller = MainController(mock_view)

        # Mock existing log viewer
        mock_log_viewer = Mock()
        mock_log_viewer.is_open.return_value = True
        mock_log_viewer.window = Mock()
        controller.log_viewer = mock_log_viewer

        controller.show_log_viewer()

        # Should bring existing window to front
        mock_log_viewer.window.lift.assert_called_once()
        mock_log_viewer.window.focus_force.assert_called_once()

    def test_show_log_viewer_error_handling(self):
        """Test show log viewer error handling"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_view.root = Mock()

        controller = MainController(mock_view)

        with patch(
            "kumihan_formatter.core.log_viewer.LogViewerWindow"
        ) as mock_log_viewer_class:
            mock_log_viewer_class.side_effect = Exception("Test error")

            with patch("tkinter.messagebox.showerror") as mock_error:
                controller.show_log_viewer()

                # Should show error message
                mock_error.assert_called_once()

    def test_exit_application(self):
        """Test exit application method"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_view.root = Mock()

        controller = MainController(mock_view)
        controller.exit_application()

        # Should quit main loop
        mock_view.root.quit.assert_called_once()

    def test_run(self):
        """Test run method"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_view.root = Mock()

        controller = MainController(mock_view)
        controller.run()

        # Should start main loop
        mock_view.root.mainloop.assert_called_once()

    def test_run_error_handling(self):
        """Test run method error handling"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_view.root = Mock()
        mock_view.root.mainloop.side_effect = Exception("Test error")

        controller = MainController(mock_view)

        with pytest.raises(Exception, match="Test error"):
            controller.run()

    def test_log_viewer_property(self):
        """Test log viewer property"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        controller = MainController(mock_view)

        mock_log_viewer = Mock()
        controller.log_viewer = mock_log_viewer

        assert controller.log_viewer_property == mock_log_viewer

    def test_logging_integration(self):
        """Test logging integration"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        with patch(
            "kumihan_formatter.gui_controllers.main_controller.log_gui_event"
        ) as mock_log:
            mock_view = Mock()
            mock_view.help_dialog = Mock()

            controller = MainController(mock_view)
            controller.show_help()

            # Should log button click
            mock_log.assert_called_with("button_click", "show_help")

    def test_fallback_logging_functions(self):
        """Test fallback logging functions when debug_logger unavailable"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        # Test that fallback functions don't crash
        mock_view = Mock()
        controller = MainController(mock_view)

        # These should work even if debug_logger is not available
        controller.exit_application()  # Should use log_gui_event fallback

    def test_setup_event_handlers_missing_frames(self):
        """Test setup event handlers when frames are missing"""
        from kumihan_formatter.gui_controllers.main_controller import MainController

        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state

        # Mock log_frame but not other frames
        mock_view.log_frame = Mock()

        # Remove frame attributes
        if hasattr(mock_view, "file_selection_frame"):
            del mock_view.file_selection_frame
        if hasattr(mock_view, "options_frame"):
            del mock_view.options_frame
        if hasattr(mock_view, "action_button_frame"):
            del mock_view.action_button_frame

        # Should not crash when frames are missing
        controller = MainController(mock_view)
