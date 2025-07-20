"""GUI File Controller Tests

Issue #501 Phase 4 GUIテスト復旧 - FileController対応
"""

import platform
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestFileController:
    """FileController comprehensive tests"""

    def test_file_controller_initialization(self):
        """Test FileController initialization"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        controller = FileController(mock_view)

        assert controller is not None
        assert controller.view == mock_view
        assert controller.main_view == mock_view

    def test_file_controller_with_app_state(self):
        """Test FileController with AppState-like view"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        # Mock view with app_state attribute
        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state

        controller = FileController(mock_view)

        assert controller.app_state == mock_app_state
        assert controller.main_view == mock_view

    def test_file_controller_without_app_state(self):
        """Test FileController without AppState (test environment)"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        # Mock view without app_state
        mock_view = Mock()
        del mock_view.app_state  # Remove if exists

        controller = FileController(mock_view)

        assert controller.app_state is None
        assert controller.main_view == mock_view

    def test_browse_input_file_success(self):
        """Test browse_input_file with file selection"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        mock_view.input_file_var = Mock()
        mock_view.update_output_preview = Mock()

        with patch("tkinter.filedialog.askopenfilename") as mock_dialog:
            mock_dialog.return_value = "/path/to/test.txt"

            controller = FileController(mock_view)
            controller.browse_input_file()

            # Should set input file
            mock_view.input_file_var.set.assert_called_once_with("/path/to/test.txt")
            mock_view.update_output_preview.assert_called_once()

            # Dialog should be called with correct parameters
            mock_dialog.assert_called_once_with(
                title="変換するテキストファイルを選択",
                filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
            )

    def test_browse_input_file_with_app_state(self):
        """Test browse_input_file with AppState"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state
        mock_view.input_file_var = Mock()
        mock_view.update_output_preview = Mock()

        # Mock log_frame
        mock_log_frame = Mock()
        mock_view.log_frame = mock_log_frame

        with patch("tkinter.filedialog.askopenfilename") as mock_dialog:
            mock_dialog.return_value = "/path/to/test.txt"

            controller = FileController(mock_view)
            controller.browse_input_file()

            # Should call app_state methods
            mock_app_state.config.set_input_file.assert_called_once_with(
                "/path/to/test.txt"
            )
            mock_log_frame.add_message.assert_called_once_with("入力ファイル: test.txt")

    def test_browse_input_file_cancelled(self):
        """Test browse_input_file when cancelled"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        mock_view.input_file_var = Mock()

        with patch("tkinter.filedialog.askopenfilename") as mock_dialog:
            mock_dialog.return_value = ""  # Cancelled

            controller = FileController(mock_view)
            controller.browse_input_file()

            # Should not set input file
            mock_view.input_file_var.set.assert_not_called()

    def test_browse_output_dir_success(self):
        """Test browse_output_dir with directory selection"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        mock_view.output_dir_var = Mock()
        mock_view.update_output_preview = Mock()

        with patch("tkinter.filedialog.askdirectory") as mock_dialog:
            mock_dialog.return_value = "/path/to/output"

            controller = FileController(mock_view)
            controller.browse_output_dir()

            # Should set output directory
            mock_view.output_dir_var.set.assert_called_once_with("/path/to/output")
            mock_view.update_output_preview.assert_called_once()

            # Dialog should be called with correct parameters
            mock_dialog.assert_called_once_with(title="出力フォルダを選択")

    def test_browse_output_dir_with_app_state(self):
        """Test browse_output_dir with AppState"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        mock_app_state = Mock()
        mock_view.app_state = mock_app_state
        mock_view.output_dir_var = Mock()
        mock_view.update_output_preview = Mock()

        # Mock log_frame
        mock_log_frame = Mock()
        mock_view.log_frame = mock_log_frame

        with patch("tkinter.filedialog.askdirectory") as mock_dialog:
            mock_dialog.return_value = "/path/to/output"

            controller = FileController(mock_view)
            controller.browse_output_dir()

            # Should call app_state methods
            mock_app_state.config.set_output_dir.assert_called_once_with(
                "/path/to/output"
            )
            mock_log_frame.add_message.assert_called_once_with(
                "出力フォルダ: /path/to/output"
            )

    def test_browse_output_dir_cancelled(self):
        """Test browse_output_dir when cancelled"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        mock_view.output_dir_var = Mock()

        with patch("tkinter.filedialog.askdirectory") as mock_dialog:
            mock_dialog.return_value = ""  # Cancelled

            controller = FileController(mock_view)
            controller.browse_output_dir()

            # Should not set output directory
            mock_view.output_dir_var.set.assert_not_called()

    def test_open_directory_macos(self):
        """Test open_directory_in_file_manager on macOS"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        controller = FileController(mock_view)

        test_path = Path("/test/directory")

        with patch("platform.system") as mock_platform:
            with patch("subprocess.run") as mock_run:
                mock_platform.return_value = "Darwin"

                controller.open_directory_in_file_manager(test_path)

                # Should call 'open' command on macOS
                mock_run.assert_called_once_with(["open", str(test_path)], check=True)

    def test_open_directory_windows(self):
        """Test open_directory_in_file_manager on Windows"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        controller = FileController(mock_view)

        test_path = Path("/test/directory")

        with patch("platform.system") as mock_platform:
            with patch("subprocess.run") as mock_run:
                mock_platform.return_value = "Windows"

                controller.open_directory_in_file_manager(test_path)

                # Should call 'explorer' command on Windows
                mock_run.assert_called_once_with(
                    ["explorer", str(test_path)], check=True
                )

    def test_open_directory_linux(self):
        """Test open_directory_in_file_manager on Linux"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        controller = FileController(mock_view)

        test_path = Path("/test/directory")

        with patch("platform.system") as mock_platform:
            with patch("subprocess.run") as mock_run:
                mock_platform.return_value = "Linux"

                controller.open_directory_in_file_manager(test_path)

                # Should call 'xdg-open' command on Linux
                mock_run.assert_called_once_with(
                    ["xdg-open", str(test_path)], check=True
                )

    def test_open_directory_error_handling(self):
        """Test open_directory_in_file_manager error handling"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        controller = FileController(mock_view)

        test_path = Path("/test/directory")

        with patch("platform.system") as mock_platform:
            with patch("subprocess.run") as mock_run:
                mock_platform.return_value = "Darwin"
                mock_run.side_effect = subprocess.CalledProcessError(1, "open")

                # Should handle exception gracefully
                controller.open_directory_in_file_manager(test_path)

    def test_open_directory_file_not_found(self):
        """Test open_directory_in_file_manager when file manager not found"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        mock_view = Mock()
        controller = FileController(mock_view)

        test_path = Path("/test/directory")

        with patch("platform.system") as mock_platform:
            with patch("subprocess.run") as mock_run:
                mock_platform.return_value = "Darwin"
                mock_run.side_effect = FileNotFoundError()

                # Should handle exception gracefully
                controller.open_directory_in_file_manager(test_path)

    def test_logging_integration(self):
        """Test logging integration"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        with patch(
            "kumihan_formatter.gui_controllers.file_controller.log_gui_event"
        ) as mock_log:
            mock_view = Mock()
            mock_view.input_file_var = Mock()

            with patch("tkinter.filedialog.askopenfilename") as mock_dialog:
                mock_dialog.return_value = "/path/to/test.txt"

                controller = FileController(mock_view)
                controller.browse_input_file()

                # Should log button click
                mock_log.assert_called_with("button_click", "browse_input_file")

    def test_view_without_required_attributes(self):
        """Test behavior when view doesn't have required attributes"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        # Mock view without required attributes
        mock_view = Mock()
        if hasattr(mock_view, "input_file_var"):
            del mock_view.input_file_var
        if hasattr(mock_view, "update_output_preview"):
            del mock_view.update_output_preview

        with patch("tkinter.filedialog.askopenfilename") as mock_dialog:
            mock_dialog.return_value = "/path/to/test.txt"

            controller = FileController(mock_view)
            # Should not crash when attributes are missing
            controller.browse_input_file()

    def test_fallback_logging_functions(self):
        """Test fallback logging functions when debug_logger unavailable"""
        from kumihan_formatter.gui_controllers.file_controller import FileController

        # Test that fallback functions don't crash
        mock_view = Mock()
        controller = FileController(mock_view)

        # These should work even if debug_logger is not available
        with patch("tkinter.filedialog.askopenfilename") as mock_dialog:
            mock_dialog.return_value = ""  # Cancelled

            controller.browse_input_file()  # Should use debug() fallback
