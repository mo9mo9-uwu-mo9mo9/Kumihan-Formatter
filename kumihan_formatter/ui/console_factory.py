"""
コンソール ファクトリー

コンソールUIコンポーネントの生成・初期化
Issue #492 Phase 5A - console_ui.py分割
"""

import sys
from typing import Tuple

from rich.console import Console

from .console_encoding import ConsoleEncodingSetup
from .console_interaction import ConsoleInteraction
from .console_messaging import ConsoleMessaging
from .console_operations import ConsoleOperations


class ConsoleUIFactory:
    """Factory for creating console UI components"""

    @staticmethod
    def create_console() -> Console:
        """Create console instance with safe settings"""
        try:
            # For Windows, use specific settings
            if sys.platform == "win32":
                return Console(
                    force_terminal=True,
                    legacy_windows=True,
                    color_system="windows",
                    # Ensure proper width detection
                    width=None,
                )
            else:
                return Console(force_terminal=True)
        except Exception:
            # Fallback to basic console if configuration fails
            return Console()

    @staticmethod
    def setup_encoding() -> None:
        """Setup console encoding"""
        ConsoleEncodingSetup.setup_encoding()


def get_console_ui_components() -> (
    Tuple[ConsoleMessaging, ConsoleOperations, ConsoleInteraction]
):
    """Get all console UI components with shared console instance"""
    factory = ConsoleUIFactory()
    factory.setup_encoding()
    console = factory.create_console()

    messaging = ConsoleMessaging(console)
    operations = ConsoleOperations(console)
    interaction = ConsoleInteraction(console)

    return messaging, operations, interaction
