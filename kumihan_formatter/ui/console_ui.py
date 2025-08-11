"""
コンソールUI 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - console_ui.py分割
"""

from typing import Any, Optional

from rich.console import Console
from rich.progress import Progress

from .console_encoding import ConsoleEncodingSetup
from .console_factory import ConsoleUIFactory
from .console_interaction import ConsoleInteraction
from .console_messaging import ConsoleMessaging
from .console_operations import ConsoleOperations


class ConsoleUI:
    """Console UI management class - backward compatibility wrapper

    Provides unified interface to all console functionality
    while delegating to specialized component classes.
    """

    def __init__(self) -> None:
        """Initialize console UI with proper encoding setup"""
        ConsoleEncodingSetup.setup_encoding()
        self.console = self._create_console()

        # Initialize component classes
        self.messaging = ConsoleMessaging(self.console)
        self.operations = ConsoleOperations(self.console)
        self.interaction = ConsoleInteraction(self.console)

    def _create_console(self) -> Console:
        """Create console instance with safe settings"""
        return ConsoleUIFactory.create_console()

    def processing_start(self, message: str, file_path: Optional[str] = None) -> None:
        self.messaging.processing_start(message, file_path)

    def processing_step(self, step: str) -> None:
        self.messaging.processing_step(step)

    def parsing_status(self) -> None:
        self.messaging.parsing_status()

    def rendering_status(self) -> None:
        self.messaging.rendering_status()

    def success(self, message: str, file_path: Optional[str] = None) -> None:
        self.messaging.success(message, file_path)

    def conversion_complete(self, output_file: str) -> None:
        self.messaging.conversion_complete(output_file)

    def error(self, message: str, details: Optional[str] = None) -> None:
        self.messaging.error(message, details)

    def file_error(
        self, file_path: str, error_type: str = "ファイルが見つかりません"
    ) -> None:
        self.messaging.file_error(file_path, error_type)

    def encoding_error(self, file_path: str) -> None:
        self.messaging.encoding_error(file_path)

    def permission_error(self, error: str) -> None:
        self.messaging.permission_error(error)

    def unexpected_error(self, error: str) -> None:
        self.messaging.unexpected_error(error)

    def warning(self, message: str, details: Optional[str] = None) -> None:
        self.messaging.warning(message, details)

    def validation_warning(self, error_count: int, is_sample: bool = False) -> None:
        self.messaging.validation_warning(error_count, is_sample)

    def info(self, message: str, details: Optional[str] = None) -> None:
        self.messaging.info(message, details)

    def hint(self, message: str, details: Optional[str] = None) -> None:
        self.messaging.hint(message, details)

    def dim(self, message: str) -> None:
        self.messaging.dim(message)

    def browser_opening(self) -> None:
        self.messaging.browser_opening()

    def browser_preview(self) -> None:
        self.messaging.browser_preview()

    def experimental_feature(self, feature_name: str) -> None:
        self.messaging.experimental_feature(feature_name)

    def no_preview_files(self) -> None:
        self.messaging.no_preview_files()

    def large_file_detected(self, size_mb: float, estimated_time: str) -> None:
        self.messaging.large_file_detected(size_mb, estimated_time)

    def large_file_processing_start(self) -> None:
        self.messaging.large_file_processing_start()

    def memory_optimization_info(self, optimization_type: str) -> None:
        self.messaging.memory_optimization_info(optimization_type)

    def performance_warning(self, warning: str) -> None:
        self.messaging.performance_warning(warning)

    def statistics(self, stats: dict[str, Any]) -> None:
        self.messaging.statistics(stats)

    def test_statistics(
        self, stats: dict[str, Any], double_click_mode: bool = False
    ) -> None:
        self.messaging.test_statistics(stats, double_click_mode)

    # From ConsoleOperations
    def file_copied(self, count: int) -> None:
        self.operations.file_copied(count)

    def files_missing(self, files: list[str]) -> None:
        self.operations.files_missing(files)

    def duplicate_files(self, duplicates: dict[str, int]) -> None:
        self.operations.duplicate_files(duplicates)

    def watch_start(self, file_path: str) -> None:
        self.operations.watch_start(file_path)

    def watch_file_changed(self, file_name: str) -> None:
        self.operations.watch_file_changed(file_name)

    def watch_update_complete(self, timestamp: str) -> None:
        self.operations.watch_update_complete(timestamp)

    def watch_update_error(self, error: str) -> None:
        self.operations.watch_update_error(error)

    def watch_stopped(self) -> None:
        self.operations.watch_stopped()

    def sample_generation(self, output_path: str) -> None:
        self.operations.sample_generation(output_path)

    def sample_complete(
        self, output_path: str, txt_name: str, html_name: str, image_count: int
    ) -> None:
        self.operations.sample_complete(output_path, txt_name, html_name, image_count)

    def test_cases_detected(
        self, count: int, cases: list[tuple[int, str, str]]
    ) -> None:
        self.operations.test_cases_detected(count, cases)

    def test_file_generation(self, double_click_mode: bool = False) -> None:
        self.operations.test_file_generation(double_click_mode)

    def test_file_complete(
        self, output_file: str, double_click_mode: bool = False
    ) -> None:
        self.operations.test_file_complete(output_file, double_click_mode)

    def test_conversion_start(self, double_click_mode: bool = False) -> None:
        self.operations.test_conversion_start(double_click_mode)

    def test_conversion_complete(
        self, test_output_file: str, output_file: str, double_click_mode: bool = False
    ) -> None:
        self.operations.test_conversion_complete(
            test_output_file, output_file, double_click_mode
        )

    def test_conversion_error(self, error: str) -> None:
        self.operations.test_conversion_error(error)

    # From ConsoleInteraction
    def input(self, prompt: str) -> str:
        return self.interaction.input(prompt)

    def confirm_source_toggle(self) -> bool:
        return self.interaction.confirm_source_toggle()

    def create_progress(self) -> Progress:
        return self.interaction.create_progress()


def get_console_ui() -> ConsoleUI:
    """Get the global console UI instance (lazy initialization)"""
    global _console_ui_instance
    if _console_ui_instance is None:
        _console_ui_instance = ConsoleUI()
    return _console_ui_instance
