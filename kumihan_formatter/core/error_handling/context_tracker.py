"""
エラーコンテキスト追跡・管理 - Issue #401対応

エラー発生時のコンテキスト情報を追跡し、
スタック形式で管理するシステム。
"""

from contextlib import contextmanager
from threading import Lock
from typing import Any, Generator

from ..utilities.logger import get_logger
from .context_models import FileContext, OperationContext, SystemContext


class ContextTracker:
    """エラーコンテキスト追跡・管理クラス

    スレッドセーフなコンテキスト情報の管理を提供
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self._context_stack: list[OperationContext] = []
        self._current_line: int | None = None
        self._current_column: int | None = None
        self._current_user_input: str | None = None
        self._lock = Lock()
        self._system_context: SystemContext | None = None
        self._file_contexts: dict[str, FileContext] = {}

    @contextmanager
    def operation_context(
        self,
        operation_name: str,
        component: str,
        file_path: str | None = None,
        **metadata: Any,
    ) -> Generator[OperationContext, None, None]:
        """操作コンテキストマネージャー

        Args:
            operation_name: 操作名
            component: コンポーネント名
            file_path: ファイルパス
            **metadata: 追加メタデータ

        Yields:
            OperationContext: 操作コンテキスト
        """
        context = OperationContext(
            operation_name=operation_name,
            component=component,
            file_path=file_path,
            line_number=self._current_line,
            column_number=self._current_column,
            user_input=self._current_user_input,
            metadata=metadata,
        )

        with self._lock:
            self._context_stack.append(context)

        self.logger.debug(
            f"コンテキスト開始: {operation_name} in {component} "
            f"(stack depth: {len(self._context_stack)})"
        )

        try:
            yield context
        finally:
            with self._lock:
                if self._context_stack and self._context_stack[-1] == context:
                    self._context_stack.pop()
                    self.logger.debug(
                        f"コンテキスト終了: {operation_name} "
                        f"(stack depth: {len(self._context_stack)})"
                    )

    def set_line_position(self, line: int, column: int | None = None) -> None:
        """現在の行・列位置を設定

        Args:
            line: 行番号
            column: 列番号（オプション）
        """
        with self._lock:
            self._current_line = line
            self._current_column = column

    def set_user_input(self, user_input: str) -> None:
        """現在のユーザー入力を設定

        Args:
            user_input: ユーザー入力文字列
        """
        with self._lock:
            self._current_user_input = user_input

    def get_current_context(self) -> OperationContext | None:
        """現在のコンテキストを取得

        Returns:
            現在のOperationContext、なければNone
        """
        with self._lock:
            return self._context_stack[-1] if self._context_stack else None

    def get_context_stack(self) -> list[OperationContext]:
        """コンテキストスタック全体を取得

        Returns:
            コンテキストスタックのコピー
        """
        with self._lock:
            return self._context_stack.copy()

    def get_system_context(self) -> SystemContext:
        """システムコンテキストを取得

        Returns:
            SystemContext: システム情報
        """
        if self._system_context is None:
            self._system_context = SystemContext()
        return self._system_context

    def get_file_context(self, file_path: str) -> FileContext:
        """ファイルコンテキストを取得

        Args:
            file_path: ファイルパス

        Returns:
            FileContext: ファイル情報
        """
        if file_path not in self._file_contexts:
            self._file_contexts[file_path] = FileContext(file_path=file_path)
        return self._file_contexts[file_path]

    def get_error_location_info(self) -> dict[str, Any]:
        """エラー位置情報を取得

        Returns:
            エラー位置情報の辞書
        """
        current_context = self.get_current_context()
        location_info = {
            "line": self._current_line,
            "column": self._current_column,
            "user_input": self._current_user_input,
            "operation": current_context.operation_name if current_context else None,
            "component": current_context.component if current_context else None,
            "file_path": current_context.file_path if current_context else None,
        }

        return location_info

    def clear_contexts(self) -> None:
        """全てのコンテキストをクリア"""
        with self._lock:
            self._context_stack.clear()
            self._current_line = None
            self._current_column = None
            self._current_user_input = None
            self._file_contexts.clear()
            self._system_context = None

        self.logger.debug("全コンテキストをクリアしました")

    def get_context_summary(self) -> dict[str, Any]:
        """コンテキスト情報の要約を取得

        Returns:
            コンテキスト要約の辞書
        """
        current_context = self.get_current_context()
        system_context = self.get_system_context()

        summary = {
            "timestamp": (
                current_context.started_at.isoformat() if current_context else None
            ),
            "operation_stack": [
                {
                    "operation": ctx.operation_name,
                    "component": ctx.component,
                    "file_path": ctx.file_path,
                }
                for ctx in self.get_context_stack()
            ],
            "current_position": {
                "line": self._current_line,
                "column": self._current_column,
            },
            "system_info": {
                "platform": system_context.platform,
                "python_version": system_context.python_version,
                "working_directory": system_context.working_directory,
                "memory_usage": system_context.memory_usage,
            },
        }

        if current_context and current_context.file_path:
            file_context = self.get_file_context(current_context.file_path)
            summary["file_info"] = file_context.to_dict()

        return summary

    def export_context_log(self) -> str:
        """コンテキスト情報をログ形式で出力

        Returns:
            フォーマットされたコンテキストログ
        """
        summary = self.get_context_summary()
        lines = []

        lines.append("=== Error Context Log ===")
        if summary["timestamp"]:
            lines.append(f"Timestamp: {summary['timestamp']}")

        if summary["operation_stack"]:
            lines.append("\nOperation Stack:")
            for i, op in enumerate(summary["operation_stack"]):
                indent = "  " * i
                lines.append(f"{indent}→ {op['operation']} ({op['component']})")
                if op["file_path"]:
                    lines.append(f"{indent}  File: {op['file_path']}")

        if summary["current_position"]["line"]:
            lines.append(
                f"\nCurrent Position: Line {summary['current_position']['line']}"
            )
            if summary["current_position"]["column"]:
                lines.append(f", Column {summary['current_position']['column']}")

        lines.append(f"\nSystem Info:")
        sys_info = summary["system_info"]
        lines.append(f"  Platform: {sys_info['platform']}")
        lines.append(f"  Python: {sys_info['python_version']}")
        lines.append(f"  Working Directory: {sys_info['working_directory']}")
        if sys_info["memory_usage"]:
            lines.append(
                f"  Memory Usage: {sys_info['memory_usage'] / 1024 / 1024:.1f} MB"
            )

        if "file_info" in summary:
            file_info = summary["file_info"]
            lines.append(f"\nFile Info:")
            lines.append(f"  Path: {file_info['file_path']}")
            if file_info["file_size"]:
                lines.append(f"  Size: {file_info['file_size']} bytes")
            if file_info["encoding"]:
                lines.append(f"  Encoding: {file_info['encoding']}")

        return "\n".join(lines)
