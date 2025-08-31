"""Minimal console UI utilities for commands.

Provides a lightweight, dependency-free console interface so that
`kumihan_formatter.commands.*` can report progress and results without
third-party UI libraries. Intended as a stable API surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConsoleUI:
    """Tiny console UI wrapper with simple methods.

    Methods are intentionally no-op friendly and safe in non-TTY envs.
    """

    def info(self, msg: str, details: str | None = None) -> None:
        if details:
            print(f"[INFO] {msg}: {details}")
        else:
            print(f"[INFO] {msg}")

    def warning(self, msg: str, details: str | None = None) -> None:
        if details:
            print(f"[WARN] {msg}: {details}")
        else:
            print(f"[WARN] {msg}")

    def error(self, msg: str) -> None:
        print(f"[ERROR] {msg}")

    def success(self, title: str, msg: str | None = None) -> None:
        if msg:
            print(f"[OK] {title}: {msg}")
        else:
            print(f"[OK] {title}")

    def dim(self, msg: str) -> None:
        print(f"[..] {msg}")

    # Domain-specific helpers used by commands
    def sample_generation(self, output_path: str) -> None:
        self.info(f"サンプルHTMLを生成します: {output_path}")

    def sample_complete(
        self,
        output_path: str,
        txt_name: str | None = None,
        html_name: str | None = None,
        image_count: int | None = None,
    ) -> None:
        self.success("サンプル生成完了", f"{output_path}")
        if txt_name:
            self.dim(f"テキスト: {txt_name}")
        if html_name:
            self.dim(f"HTML: {html_name}")
        if image_count is not None:
            self.dim(f"画像: {image_count}個")

    def watch_start(self, path: str) -> None:
        self.info(f"監視を開始: {path}")

    def watch_stopped(self) -> None:
        self.warning("監視を停止しました")

    def watch_file_changed(self, path: str) -> None:
        self.info(f"変更を検出: {path}")


_ui_singleton: ConsoleUI | None = None


def get_console_ui() -> ConsoleUI:
    global _ui_singleton
    if _ui_singleton is None:
        _ui_singleton = ConsoleUI()
    return _ui_singleton


__all__ = ["ConsoleUI", "get_console_ui"]
