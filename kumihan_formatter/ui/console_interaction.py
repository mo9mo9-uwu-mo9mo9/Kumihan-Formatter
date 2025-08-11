"""
コンソール インタラクション

ユーザー入力・確認・プログレス表示等の相互作用機能
Issue #492 Phase 5A - console_ui.py分割
"""

from typing import Any

from rich.progress import Progress


class ConsoleInteraction:
    """Console interaction functionality

    Handles user input, confirmations, progress displays,
    and other interactive console operations.
    """

    def __init__(self, console: Any) -> None:
        """Initialize with a Rich Console instance"""
        self.console = console

    # User input
    def input(self, prompt: str) -> str:
        """Get user input with styled prompt"""
        result = self.console.input(prompt)
        return str(result)

    def confirm_source_toggle(self) -> bool:
        """Confirm source toggle feature usage"""
        from .console_messaging import ConsoleMessaging

        messaging = ConsoleMessaging(self.console)

        messaging.hint(
            "記法と結果を切り替えて表示する機能があります",
            "改行処理などの動作を実際に確認しながら記法を学習できます",
        )
        response = self.input("[yellow]この機能を使用しますか？ (Y/n): [/yellow]")
        return response.lower() in ["y", "yes", ""]

    def create_progress(self) -> Progress:
        """Create a progress instance"""
        return Progress()
