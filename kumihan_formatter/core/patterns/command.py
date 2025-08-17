"""Command Pattern Implementation"""

import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")


class CommandStatus(Enum):
    """コマンド実行状態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CommandResult:
    """コマンド実行結果"""

    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Command(ABC):
    """コマンド基底クラス"""

    def __init__(self, command_id: Optional[str] = None) -> None:
        self.command_id = command_id or str(uuid.uuid4())
        self.status = CommandStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    @abstractmethod
    def execute(self) -> CommandResult:
        """コマンド実行"""
        pass

    def can_undo(self) -> bool:
        """アンドゥ可能性判定"""
        return False

    def undo(self) -> CommandResult:
        """アンドゥ実行"""
        raise NotImplementedError("Undo not supported")

    def get_description(self) -> str:
        """コマンド説明取得"""
        return f"{self.__class__.__name__}[{self.command_id[:8]}]"


class ParseCommand(Command):
    """パースコマンド"""

    def __init__(
        self, content: str, parser: Any, context: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        self.content = content
        self.parser = parser
        self.context = context or {}

    def execute(self) -> CommandResult:
        """パース実行"""
        try:
            self.status = CommandStatus.RUNNING
            self.started_at = datetime.now()

            start_time = time.time()
            result = self.parser.parse(self.content, self.context)
            execution_time = time.time() - start_time

            self.status = CommandStatus.COMPLETED
            self.completed_at = datetime.now()

            return CommandResult(
                success=True, result=result, execution_time=execution_time
            )
        except Exception as e:
            self.status = CommandStatus.FAILED
            self.completed_at = datetime.now()
            return CommandResult(
                success=False,
                error=e,
                execution_time=time.time() - start_time if self.started_at else 0.0,
            )


class RenderCommand(Command):
    """レンダリングコマンド"""

    def __init__(
        self, data: Any, renderer: Any, context: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        self.data = data
        self.renderer = renderer
        self.context = context or {}

    def execute(self) -> CommandResult:
        """レンダリング実行"""
        try:
            self.status = CommandStatus.RUNNING
            self.started_at = datetime.now()

            start_time = time.time()
            result = self.renderer.render(self.data, self.context)
            execution_time = time.time() - start_time

            self.status = CommandStatus.COMPLETED
            self.completed_at = datetime.now()

            return CommandResult(
                success=True, result=result, execution_time=execution_time
            )
        except Exception as e:
            self.status = CommandStatus.FAILED
            self.completed_at = datetime.now()
            return CommandResult(
                success=False,
                error=e,
                execution_time=time.time() - start_time if self.started_at else 0.0,
            )


class CommandProcessor:
    """コマンド処理システム"""

    def __init__(self) -> None:
        self._command_history: List[Command] = []
        self._max_history = 1000
        self._lock = threading.RLock()

    def execute_command(self, command: Command) -> CommandResult:
        """コマンド実行"""
        with self._lock:
            result = command.execute()

            # 履歴保存
            self._command_history.append(command)
            if len(self._command_history) > self._max_history:
                self._command_history.pop(0)

            return result

    def execute_batch(self, commands: List[Command]) -> List[CommandResult]:
        """バッチコマンド実行"""
        results = []
        for command in commands:
            result = self.execute_command(command)
            results.append(result)
            # 失敗時の処理戦略（継続 or 中断）
            if not result.success:
                # とりあえず継続
                pass
        return results

    def undo_last(self) -> Optional[CommandResult]:
        """最後のコマンドをアンドゥ"""
        with self._lock:
            for command in reversed(self._command_history):
                if command.status == CommandStatus.COMPLETED and command.can_undo():
                    return command.undo()
            return None

    def get_command_history(self, limit: Optional[int] = None) -> List[Command]:
        """コマンド履歴取得"""
        with self._lock:
            history = self._command_history.copy()
            if limit:
                history = history[-limit:]
            return history

    def clear_history(self) -> None:
        """履歴クリア"""
        with self._lock:
            self._command_history.clear()


class CommandQueue:
    """コマンドキュー（非同期実行）"""

    def __init__(self, max_workers: int = 4) -> None:
        self._queue: List[Command] = []
        self._running_commands: Dict[str, Command] = {}
        self._max_workers = max_workers
        self._lock = threading.RLock()
        self._processor = CommandProcessor()

    def enqueue(self, command: Command) -> None:
        """コマンドキューイング"""
        with self._lock:
            self._queue.append(command)

    def process_queue(self) -> None:
        """キュー処理（スレッドプールで実行）"""
        # 実装は簡略化（実際にはThreadPoolExecutorを使用）
        with self._lock:
            while self._queue and len(self._running_commands) < self._max_workers:
                command = self._queue.pop(0)
                self._running_commands[command.command_id] = command
                # スレッドで実行
                threading.Thread(target=self._execute_command, args=(command,)).start()

    def _execute_command(self, command: Command) -> None:
        """コマンド実行（内部）"""
        try:
            self._processor.execute_command(command)
        finally:
            with self._lock:
                self._running_commands.pop(command.command_id, None)
