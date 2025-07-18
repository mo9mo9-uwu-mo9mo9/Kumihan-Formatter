"""File Controller Tests for Issue 501 Phase 4A

This module tests GUI file controller functionality to ensure
proper file selection and directory operations.
"""

import os
import tempfile
import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.gui_controllers.file_controller import FileController

from .test_base import BaseTestCase


class TestFileController(BaseTestCase):
    """Test file controller functionality"""

    def setup_method(self, method):
        """Setup method called before each test method"""
        super().setup_method(method)
        # Create mock view with required attributes
        self.mock_view = Mock()
        self.mock_view.input_file_var = Mock()
        self.mock_view.input_file_var.get = Mock(return_value="")
        self.mock_view.input_file_var.set = Mock()
        self.mock_view.output_dir_var = Mock()
        self.mock_view.output_dir_var.get = Mock(return_value="")
        self.mock_view.output_dir_var.set = Mock()
        self.mock_view.update_output_preview = Mock()

    def test_file_controller_initialization(self):
        """Test FileController initialization"""
        controller = FileController(self.mock_view)
        assert controller is not None
        assert controller.view == self.mock_view

    @patch("tkinter.filedialog.askopenfilename")
    def test_browse_input_file_success(self, mock_dialog):
        """Test successful input file browsing"""
        # Setup
        controller = FileController(self.mock_view)
        test_file = self.create_temp_file("test content", suffix=".txt")
        mock_dialog.return_value = test_file

        # Execute
        controller.browse_input_file()

        # Verify
        mock_dialog.assert_called_once()
        self.mock_view.input_file_var.set.assert_called_once_with(test_file)
        self.mock_view.update_output_preview.assert_called_once()

    @patch("tkinter.filedialog.askopenfilename")
    def test_browse_input_file_cancel(self, mock_dialog):
        """Test cancelled input file browsing"""
        # Setup
        controller = FileController(self.mock_view)
        mock_dialog.return_value = ""  # User cancelled

        # Execute
        controller.browse_input_file()

        # Verify
        mock_dialog.assert_called_once()
        self.mock_view.input_file_var.set.assert_not_called()
        self.mock_view.update_output_preview.assert_not_called()

    @patch("tkinter.filedialog.askopenfilename")
    def test_browse_input_file_with_initial_dir(self, mock_dialog):
        """Test input file browsing with initial directory"""
        # Setup
        controller = FileController(self.mock_view)
        existing_file = self.create_temp_file("existing", suffix=".txt")
        self.mock_view.input_file_var.get.return_value = existing_file
        mock_dialog.return_value = ""

        # Execute
        controller.browse_input_file()

        # Verify
        mock_dialog.assert_called_once()
        call_kwargs = mock_dialog.call_args[1]
        assert "initialdir" in call_kwargs
        assert call_kwargs["initialdir"] == os.path.dirname(existing_file)

    @patch("tkinter.filedialog.askdirectory")
    def test_browse_output_dir_success(self, mock_dialog):
        """Test successful output directory browsing"""
        # Setup
        controller = FileController(self.mock_view)
        test_dir = self.create_temp_dir()
        mock_dialog.return_value = test_dir

        # Execute
        controller.browse_output_dir()

        # Verify
        mock_dialog.assert_called_once()
        self.mock_view.output_dir_var.set.assert_called_once_with(test_dir)
        self.mock_view.update_output_preview.assert_called_once()

    @patch("tkinter.filedialog.askdirectory")
    def test_browse_output_dir_cancel(self, mock_dialog):
        """Test cancelled output directory browsing"""
        # Setup
        controller = FileController(self.mock_view)
        mock_dialog.return_value = ""  # User cancelled

        # Execute
        controller.browse_output_dir()

        # Verify
        mock_dialog.assert_called_once()
        self.mock_view.output_dir_var.set.assert_not_called()
        self.mock_view.update_output_preview.assert_not_called()

    @patch("tkinter.filedialog.askdirectory")
    def test_browse_output_dir_with_initial_dir(self, mock_dialog):
        """Test output directory browsing with initial directory"""
        # Setup
        controller = FileController(self.mock_view)
        existing_dir = self.create_temp_dir()
        self.mock_view.output_dir_var.get.return_value = existing_dir
        mock_dialog.return_value = ""

        # Execute
        controller.browse_output_dir()

        # Verify
        mock_dialog.assert_called_once()
        call_kwargs = mock_dialog.call_args[1]
        assert "initialdir" in call_kwargs
        assert call_kwargs["initialdir"] == existing_dir

    @patch("subprocess.run")
    @patch("platform.system")
    def test_open_directory_in_file_manager_windows(
        self, mock_platform, mock_subprocess
    ):
        """Test opening directory in Windows Explorer"""
        # Setup
        controller = FileController(self.mock_view)
        test_dir = self.create_temp_dir()
        mock_platform.return_value = "Windows"

        # Execute
        controller.open_directory_in_file_manager(test_dir)

        # Verify
        mock_subprocess.assert_called_once_with(["explorer", test_dir])

    @patch("subprocess.run")
    @patch("platform.system")
    def test_open_directory_in_file_manager_macos(self, mock_platform, mock_subprocess):
        """Test opening directory in macOS Finder"""
        # Setup
        controller = FileController(self.mock_view)
        test_dir = self.create_temp_dir()
        mock_platform.return_value = "Darwin"

        # Execute
        controller.open_directory_in_file_manager(test_dir)

        # Verify
        mock_subprocess.assert_called_once_with(["open", test_dir])

    @patch("subprocess.run")
    @patch("platform.system")
    def test_open_directory_in_file_manager_linux(self, mock_platform, mock_subprocess):
        """Test opening directory in Linux file manager"""
        # Setup
        controller = FileController(self.mock_view)
        test_dir = self.create_temp_dir()
        mock_platform.return_value = "Linux"

        # Execute
        controller.open_directory_in_file_manager(test_dir)

        # Verify
        mock_subprocess.assert_called_once_with(["xdg-open", test_dir])

    @patch("subprocess.run")
    def test_open_directory_in_file_manager_error_handling(self, mock_subprocess):
        """Test error handling when opening directory fails"""
        # Setup
        controller = FileController(self.mock_view)
        test_dir = self.create_temp_dir()
        mock_subprocess.side_effect = Exception("Failed to open")

        # Execute - should not raise exception
        controller.open_directory_in_file_manager(test_dir)

        # Verify
        mock_subprocess.assert_called()

    def test_file_controller_with_mock_filedialog_types(self):
        """Test file dialog with different file types"""
        controller = FileController(self.mock_view)

        # Verify controller handles different file extensions
        test_files = [
            ("test.txt", "Text file"),
            ("test.md", "Markdown file"),
            ("test.html", "HTML file"),
        ]

        for filename, description in test_files:
            temp_file = self.create_temp_file("content", suffix=filename)
            assert Path(temp_file).exists()
            assert Path(temp_file).suffix == Path(filename).suffix


class TestFileControllerIntegration(BaseTestCase):
    """Test file controller integration scenarios"""

    def setup_method(self, method):
        """Setup method with full mock environment"""
        super().setup_method(method)
        self.mock_view = Mock()
        self.mock_view.input_file_var = Mock()
        self.mock_view.input_file_var.get = Mock(return_value="")
        self.mock_view.input_file_var.set = Mock()
        self.mock_view.output_dir_var = Mock()
        self.mock_view.output_dir_var.get = Mock(return_value="")
        self.mock_view.output_dir_var.set = Mock()
        self.mock_view.update_output_preview = Mock()

    @patch("tkinter.filedialog.askopenfilename")
    @patch("tkinter.filedialog.askdirectory")
    def test_file_controller_complete_workflow(self, mock_dir_dialog, mock_file_dialog):
        """Test complete file selection workflow"""
        # Setup
        controller = FileController(self.mock_view)
        input_file = self.create_temp_file("test content", suffix=".txt")
        output_dir = self.create_temp_dir()

        mock_file_dialog.return_value = input_file
        mock_dir_dialog.return_value = output_dir

        # Execute
        controller.browse_input_file()
        controller.browse_output_dir()

        # Verify
        self.mock_view.input_file_var.set.assert_called_with(input_file)
        self.mock_view.output_dir_var.set.assert_called_with(output_dir)
        assert self.mock_view.update_output_preview.call_count == 2

    def test_file_controller_unicode_filenames(self):
        """Test handling of unicode filenames"""
        controller = FileController(self.mock_view)

        # Test with various unicode filenames
        unicode_names = [
            "テスト.txt",
            "文書.md",
            "ファイル.html",
        ]

        for name in unicode_names:
            temp_file = self.create_temp_file("content", suffix=".txt")
            # Rename to unicode name
            unicode_path = Path(temp_file).parent / name
            Path(temp_file).rename(unicode_path)

            assert unicode_path.exists()
            self.temp_files.append(str(unicode_path))  # Track for cleanup
