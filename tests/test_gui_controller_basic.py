"""GUI Integrated Controller Tests

Issue #501 Phase 4 GUIテスト復旧 - GuiController対応
"""

from unittest.mock import Mock, patch

import pytest


class TestGuiController:
    """GuiController comprehensive tests"""

    def test_gui_controller_initialization(self):
        """Test GuiController initialization"""
        with patch(
            "kumihan_formatter.gui_controllers.gui_controller.StateModel"
        ) as mock_state_model:
            with patch(
                "kumihan_formatter.gui_controllers.gui_controller.MainWindow"
            ) as mock_main_window:
                with patch(
                    "kumihan_formatter.gui_controllers.gui_controller.FileController"
                ) as mock_file_controller:
                    with patch(
                        "kumihan_formatter.gui_controllers.gui_controller.ConversionController"
                    ) as mock_conversion_controller:
                        with patch(
                            "kumihan_formatter.gui_controllers.gui_controller.MainController"
                        ) as mock_main_controller:
                            from kumihan_formatter.gui_controllers.gui_controller import (
                                GuiController,
                            )

                            controller = GuiController()

                            # Should create all components
                            assert controller is not None
                            mock_state_model.assert_called_once()
                            mock_main_window.assert_called_once()
                            mock_file_controller.assert_called_once()
                            mock_conversion_controller.assert_called_once()
                            mock_main_controller.assert_called_once()

    def test_gui_controller_component_integration(self):
        """Test component integration in GuiController"""
        with patch(
            "kumihan_formatter.gui_controllers.gui_controller.StateModel"
        ) as mock_state_model:
            with patch(
                "kumihan_formatter.gui_controllers.gui_controller.MainWindow"
            ) as mock_main_window:
                with patch(
                    "kumihan_formatter.gui_controllers.gui_controller.FileController"
                ) as mock_file_controller:
                    with patch(
                        "kumihan_formatter.gui_controllers.gui_controller.ConversionController"
                    ) as mock_conversion_controller:
                        with patch(
                            "kumihan_formatter.gui_controllers.gui_controller.MainController"
                        ) as mock_main_controller:
                            from kumihan_formatter.gui_controllers.gui_controller import (
                                GuiController,
                            )

                            mock_model_instance = Mock()
                            mock_view_instance = Mock()
                            mock_file_controller_instance = Mock()
                            mock_conversion_controller_instance = Mock()
                            mock_main_controller_instance = Mock()

                            mock_state_model.return_value = mock_model_instance
                            mock_main_window.return_value = mock_view_instance
                            mock_file_controller.return_value = (
                                mock_file_controller_instance
                            )
                            mock_conversion_controller.return_value = (
                                mock_conversion_controller_instance
                            )
                            mock_main_controller.return_value = (
                                mock_main_controller_instance
                            )

                            controller = GuiController()

                            # Check proper instantiation order and parameters
                            mock_state_model.assert_called_once_with()
                            mock_main_window.assert_called_once_with(
                                mock_model_instance
                            )
                            mock_file_controller.assert_called_once_with(
                                mock_view_instance
                            )
                            mock_conversion_controller.assert_called_once_with(
                                mock_model_instance, mock_view_instance
                            )
                            mock_main_controller.assert_called_once_with(
                                mock_view_instance,
                                mock_model_instance,
                                mock_file_controller_instance,
                                mock_conversion_controller_instance,
                            )

                            # Check component assignment
                            assert controller.model == mock_model_instance
                            assert controller.view == mock_view_instance
                            assert (
                                controller.file_controller
                                == mock_file_controller_instance
                            )
                            assert (
                                controller.conversion_controller
                                == mock_conversion_controller_instance
                            )
                            assert (
                                controller.main_controller
                                == mock_main_controller_instance
                            )

    def test_gui_controller_run(self):
        """Test GuiController run method"""
        with patch("kumihan_formatter.gui_controllers.gui_controller.StateModel"):
            with patch("kumihan_formatter.gui_controllers.gui_controller.MainWindow"):
                with patch(
                    "kumihan_formatter.gui_controllers.gui_controller.FileController"
                ):
                    with patch(
                        "kumihan_formatter.gui_controllers.gui_controller.ConversionController"
                    ):
                        with patch(
                            "kumihan_formatter.gui_controllers.gui_controller.MainController"
                        ) as mock_main_controller:
                            from kumihan_formatter.gui_controllers.gui_controller import (
                                GuiController,
                            )

                            mock_main_controller_instance = Mock()
                            mock_main_controller.return_value = (
                                mock_main_controller_instance
                            )

                            controller = GuiController()
                            controller.run()

                            # Should call main_controller.run()
                            mock_main_controller_instance.run.assert_called_once()

    def test_gui_controller_run_without_main_controller(self):
        """Test GuiController run method without main controller"""
        with patch("kumihan_formatter.gui_controllers.gui_controller.StateModel"):
            with patch("kumihan_formatter.gui_controllers.gui_controller.MainWindow"):
                with patch(
                    "kumihan_formatter.gui_controllers.gui_controller.FileController"
                ):
                    with patch(
                        "kumihan_formatter.gui_controllers.gui_controller.ConversionController"
                    ):
                        with patch(
                            "kumihan_formatter.gui_controllers.gui_controller.MainController"
                        ):
                            from kumihan_formatter.gui_controllers.gui_controller import (
                                GuiController,
                            )

                            controller = GuiController()
                            controller.main_controller = None

                            # Should not crash when main_controller is None
                            controller.run()

    def test_log_viewer_property_getter(self):
        """Test log_viewer property getter"""
        with patch("kumihan_formatter.gui_controllers.gui_controller.StateModel"):
            with patch("kumihan_formatter.gui_controllers.gui_controller.MainWindow"):
                with patch(
                    "kumihan_formatter.gui_controllers.gui_controller.FileController"
                ):
                    with patch(
                        "kumihan_formatter.gui_controllers.gui_controller.ConversionController"
                    ):
                        with patch(
                            "kumihan_formatter.gui_controllers.gui_controller.MainController"
                        ) as mock_main_controller:
                            from kumihan_formatter.gui_controllers.gui_controller import (
                                GuiController,
                            )
