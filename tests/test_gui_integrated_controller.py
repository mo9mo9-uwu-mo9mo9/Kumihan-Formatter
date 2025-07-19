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

                            mock_main_controller_instance = Mock()
                            mock_log_viewer = Mock()
                            mock_main_controller_instance.log_viewer = mock_log_viewer
                            mock_main_controller.return_value = (
                                mock_main_controller_instance
                            )

                            controller = GuiController()
                            result = controller.log_viewer

                            assert result == mock_log_viewer

    def test_log_viewer_property_getter_without_main_controller(self):
        """Test log_viewer property getter without main controller"""
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

                            result = controller.log_viewer
                            assert result is None

    def test_log_viewer_property_setter(self):
        """Test log_viewer property setter"""
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
                            mock_log_viewer = Mock()

                            controller.log_viewer = mock_log_viewer

                            # Should set log_viewer on main_controller
                            assert (
                                mock_main_controller_instance.log_viewer
                                == mock_log_viewer
                            )

    def test_log_viewer_property_setter_without_main_controller(self):
        """Test log_viewer property setter without main controller"""
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

                            mock_log_viewer = Mock()
                            # Should not crash when main_controller is None
                            controller.log_viewer = mock_log_viewer


class TestCreateGuiApplication:
    """Test create_gui_application function"""

    def test_create_gui_application(self):
        """Test create_gui_application function"""
        with patch(
            "kumihan_formatter.gui_controllers.gui_controller.GuiController"
        ) as mock_gui_controller:
            from kumihan_formatter.gui_controllers.gui_controller import (
                create_gui_application,
            )

            mock_controller_instance = Mock()
            mock_gui_controller.return_value = mock_controller_instance

            result = create_gui_application()

            # Should create and return GuiController instance
            mock_gui_controller.assert_called_once()
            assert result == mock_controller_instance

    def test_create_gui_application_integration(self):
        """Test create_gui_application integration"""
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
                                create_gui_application,
                            )

                            result = create_gui_application()

                            # Should return a GuiController instance
                            assert result is not None
                            assert hasattr(result, "run")
                            assert hasattr(result, "log_viewer")


class TestGuiControllerErrorHandling:
    """Test GuiController error handling"""

    def test_gui_controller_initialization_error(self):
        """Test GuiController initialization with component errors"""
        with patch(
            "kumihan_formatter.gui_controllers.gui_controller.StateModel"
        ) as mock_state_model:
            mock_state_model.side_effect = Exception("StateModel error")

            from kumihan_formatter.gui_controllers.gui_controller import (
                GuiController,
            )

            with pytest.raises(Exception, match="StateModel error"):
                GuiController()

    def test_main_window_initialization_error(self):
        """Test GuiController with MainWindow initialization error"""
        with patch("kumihan_formatter.gui_controllers.gui_controller.StateModel"):
            with patch(
                "kumihan_formatter.gui_controllers.gui_controller.MainWindow"
            ) as mock_main_window:
                mock_main_window.side_effect = Exception("MainWindow error")

                from kumihan_formatter.gui_controllers.gui_controller import (
                    GuiController,
                )

                with pytest.raises(Exception, match="MainWindow error"):
                    GuiController()

    def test_controller_initialization_error(self):
        """Test GuiController with sub-controller initialization error"""
        with patch("kumihan_formatter.gui_controllers.gui_controller.StateModel"):
            with patch("kumihan_formatter.gui_controllers.gui_controller.MainWindow"):
                with patch(
                    "kumihan_formatter.gui_controllers.gui_controller.FileController"
                ) as mock_file_controller:
                    mock_file_controller.side_effect = Exception("FileController error")

                    from kumihan_formatter.gui_controllers.gui_controller import (
                        GuiController,
                    )

                    with pytest.raises(Exception, match="FileController error"):
                        GuiController()
