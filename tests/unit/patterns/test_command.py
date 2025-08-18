"""コマンドパターンのテスト

コマンド実行システムの包括的なテスト。
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Any, Dict

from kumihan_formatter.core.patterns.command import (
    Command,
    CommandStatus,
    CommandResult,
    ParseCommand,
    RenderCommand,
    CommandProcessor,
    CommandQueue,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


# テスト用モッククラス
class MockParser:
    """テスト用パーサー"""

    def __init__(self, name="mock_parser", parse_duration=0.0):
        self.name = name
        self.parse_duration = parse_duration
        self.parse_calls = []

    def parse(self, content: str, context: Dict[str, Any]) -> str:
        """パース処理"""
        self.parse_calls.append((content, context))
        if self.parse_duration > 0:
            time.sleep(self.parse_duration)
        if "error" in content:
            raise ValueError(f"Parse error in {content}")
        return f"parsed_{self.name}:{content}"


class MockRenderer:
    """テスト用レンダラー"""

    def __init__(self, name="mock_renderer", render_duration=0.0):
        self.name = name
        self.render_duration = render_duration
        self.render_calls = []

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        """レンダリング処理"""
        self.render_calls.append((data, context))
        if self.render_duration > 0:
            time.sleep(self.render_duration)
        if "error" in str(data):
            raise ValueError(f"Render error in {data}")
        return f"rendered_{self.name}:{data}"


class TestCommand(Command):
    """テスト用コマンド"""

    def __init__(self, action: str = "test", should_fail: bool = False, execution_time: float = 0.0):
        super().__init__()
        self.action = action
        self.should_fail = should_fail
        self.execution_time = execution_time
        self.execution_count = 0

    def execute(self) -> CommandResult:
        """コマンド実行"""
        try:
            self.status = CommandStatus.RUNNING
            self.started_at = datetime.now()
            self.execution_count += 1

            start_time = time.time()
            if self.execution_time > 0:
                time.sleep(self.execution_time)

            if self.should_fail:
                raise ValueError(f"Test failure in {self.action}")

            result = f"executed_{self.action}"
            execution_time = time.time() - start_time

            self.status = CommandStatus.COMPLETED
            self.completed_at = datetime.now()

            return CommandResult(
                success=True,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            self.status = CommandStatus.FAILED
            self.completed_at = datetime.now()
            return CommandResult(
                success=False,
                error=e,
                execution_time=time.time() - start_time if hasattr(self, 'started_at') else 0.0
            )


class UndoableTestCommand(TestCommand):
    """アンドゥ可能なテスト用コマンド"""

    def __init__(self, action: str = "undoable", should_fail: bool = False):
        super().__init__(action, should_fail)
        self.undo_count = 0

    def can_undo(self) -> bool:
        """アンドゥ可能性判定"""
        return True

    def undo(self) -> CommandResult:
        """アンドゥ実行"""
        self.undo_count += 1
        return CommandResult(
            success=True,
            result=f"undone_{self.action}",
            metadata={"undo_count": self.undo_count}
        )


class TestCommandStatus:
    """コマンドステータス列挙型のテスト"""

    def test_正常系_ステータス値確認(self):
        """正常系: ステータスの値確認"""
        # Given/When/Then: 各ステータスの値が正しい
        assert CommandStatus.PENDING.value == "pending"
        assert CommandStatus.RUNNING.value == "running"
        assert CommandStatus.COMPLETED.value == "completed"
        assert CommandStatus.FAILED.value == "failed"
        assert CommandStatus.CANCELLED.value == "cancelled"


class TestCommandResult:
    """コマンド結果クラスのテスト"""

    def test_正常系_成功結果作成(self):
        """正常系: 成功結果の作成確認"""
        # Given: 成功結果のデータ
        result_data = "test_result"
        execution_time = 0.5
        metadata = {"key": "value"}

        # When: 成功結果を作成
        result = CommandResult(
            success=True,
            result=result_data,
            execution_time=execution_time,
            metadata=metadata
        )

        # Then: 正しく作成される
        assert result.success is True
        assert result.result == result_data
        assert result.error is None
        assert result.execution_time == execution_time
        assert result.metadata == metadata

    def test_正常系_失敗結果作成(self):
        """正常系: 失敗結果の作成確認"""
        # Given: 失敗結果のデータ
        error = ValueError("Test error")
        execution_time = 0.2

        # When: 失敗結果を作成
        result = CommandResult(
            success=False,
            error=error,
            execution_time=execution_time
        )

        # Then: 正しく作成される
        assert result.success is False
        assert result.result is None
        assert result.error is error
        assert result.execution_time == execution_time


class TestCommandBase:
    """コマンド基底クラスのテスト"""

    def test_正常系_コマンド初期化(self):
        """正常系: コマンド初期化の確認"""
        # Given: コマンドクラス
        # When: コマンドを初期化
        command = TestCommand("init_test")

        # Then: 正しく初期化される
        assert command.status == CommandStatus.PENDING
        assert isinstance(command.command_id, str)
        assert len(command.command_id) > 0
        assert isinstance(command.created_at, datetime)
        assert command.started_at is None
        assert command.completed_at is None

    def test_正常系_カスタムコマンドID(self):
        """正常系: カスタムコマンドIDの確認"""
        # Given: カスタムコマンドID
        custom_id = "custom_command_123"

        # When: カスタムIDでコマンドを作成
        command = TestCommand("action")
        command.command_id = custom_id

        # Then: カスタムIDが設定される
        assert command.command_id == custom_id

    def test_正常系_コマンド説明取得(self):
        """正常系: コマンド説明取得の確認"""
        # Given: コマンド
        command = TestCommand("description_test")

        # When: 説明を取得
        description = command.get_description()

        # Then: 適切な説明が返される
        assert "TestCommand" in description
        assert command.command_id[:8] in description

    def test_正常系_成功実行(self):
        """正常系: 成功実行の確認"""
        # Given: 正常なコマンド
        command = TestCommand("success")

        # When: コマンドを実行
        result = command.execute()

        # Then: 成功結果が返される
        assert result.success is True
        assert result.result == "executed_success"
        assert command.status == CommandStatus.COMPLETED
        assert command.started_at is not None
        assert command.completed_at is not None
        assert command.execution_count == 1

    def test_正常系_失敗実行(self):
        """正常系: 失敗実行の確認"""
        # Given: 失敗するコマンド
        command = TestCommand("failure", should_fail=True)

        # When: コマンドを実行
        result = command.execute()

        # Then: 失敗結果が返される
        assert result.success is False
        assert isinstance(result.error, ValueError)
        assert "Test failure in failure" in str(result.error)
        assert command.status == CommandStatus.FAILED
        assert command.completed_at is not None

    def test_正常系_アンドゥ不可判定(self):
        """正常系: アンドゥ不可判定の確認"""
        # Given: 基本コマンド
        command = TestCommand("no_undo")

        # When: アンドゥ可能性を確認
        can_undo = command.can_undo()

        # Then: アンドゥ不可
        assert can_undo is False

    def test_異常系_アンドゥ実行エラー(self):
        """異常系: アンドゥ実行エラーの確認"""
        # Given: アンドゥ不対応のコマンド
        command = TestCommand("no_undo")

        # When: アンドゥを実行しようとする
        # Then: NotImplementedErrorが発生
        with pytest.raises(NotImplementedError, match="Undo not supported"):
            command.undo()


class TestParseCommand:
    """パースコマンドのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.parser = MockParser("test_parser")

    def test_正常系_パースコマンド作成(self):
        """正常系: パースコマンド作成の確認"""
        # Given: パースコマンドの引数
        content = "test content"
        context = {"format": "test"}

        # When: パースコマンドを作成
        command = ParseCommand(content, self.parser, context)

        # Then: 正しく作成される
        assert command.content == content
        assert command.parser is self.parser
        assert command.context == context
        assert command.status == CommandStatus.PENDING

    def test_正常系_パースコマンド実行(self):
        """正常系: パースコマンド実行の確認"""
        # Given: パースコマンド
        command = ParseCommand("test content", self.parser, {"key": "value"})

        # When: コマンドを実行
        result = command.execute()

        # Then: パース処理が実行される
        assert result.success is True
        assert result.result == "parsed_test_parser:test content"
        assert command.status == CommandStatus.COMPLETED
        assert len(self.parser.parse_calls) == 1
        assert self.parser.parse_calls[0] == ("test content", {"key": "value"})

    def test_正常系_パースコマンド実行時間計測(self):
        """正常系: パースコマンド実行時間計測の確認"""
        # Given: 処理時間のかかるパーサー
        slow_parser = MockParser("slow", parse_duration=0.01)
        command = ParseCommand("slow content", slow_parser)

        # When: コマンドを実行
        result = command.execute()

        # Then: 実行時間が計測される
        assert result.success is True
        assert result.execution_time > 0.0
        assert result.execution_time >= 0.01

    def test_異常系_パースエラー処理(self):
        """異常系: パースエラー処理の確認"""
        # Given: エラーを発生させるコンテンツ
        command = ParseCommand("error content", self.parser)

        # When: コマンドを実行
        result = command.execute()

        # Then: エラーが適切に処理される
        assert result.success is False
        assert isinstance(result.error, ValueError)
        assert "Parse error in error content" in str(result.error)
        assert command.status == CommandStatus.FAILED


class TestRenderCommand:
    """レンダリングコマンドのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.renderer = MockRenderer("test_renderer")

    def test_正常系_レンダリングコマンド作成(self):
        """正常系: レンダリングコマンド作成の確認"""
        # Given: レンダリングコマンドの引数
        data = {"title": "test", "content": "data"}
        context = {"format": "html"}

        # When: レンダリングコマンドを作成
        command = RenderCommand(data, self.renderer, context)

        # Then: 正しく作成される
        assert command.data == data
        assert command.renderer is self.renderer
        assert command.context == context

    def test_正常系_レンダリングコマンド実行(self):
        """正常系: レンダリングコマンド実行の確認"""
        # Given: レンダリングコマンド
        data = "test data"
        command = RenderCommand(data, self.renderer, {"format": "html"})

        # When: コマンドを実行
        result = command.execute()

        # Then: レンダリング処理が実行される
        assert result.success is True
        assert result.result == "rendered_test_renderer:test data"
        assert command.status == CommandStatus.COMPLETED
        assert len(self.renderer.render_calls) == 1
        assert self.renderer.render_calls[0] == (data, {"format": "html"})

    def test_異常系_レンダリングエラー処理(self):
        """異常系: レンダリングエラー処理の確認"""
        # Given: エラーを発生させるデータ
        command = RenderCommand("error data", self.renderer)

        # When: コマンドを実行
        result = command.execute()

        # Then: エラーが適切に処理される
        assert result.success is False
        assert isinstance(result.error, ValueError)
        assert "Render error in error data" in str(result.error)
        assert command.status == CommandStatus.FAILED


class TestCommandProcessor:
    """コマンドプロセッサーのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.processor = CommandProcessor()

    def test_正常系_プロセッサー初期化(self):
        """正常系: プロセッサー初期化の確認"""
        # Given: CommandProcessorクラス
        # When: プロセッサーを初期化
        processor = CommandProcessor()

        # Then: 正しく初期化される
        assert len(processor._command_history) == 0
        assert processor._max_history == 1000

    def test_正常系_コマンド実行(self):
        """正常系: コマンド実行の確認"""
        # Given: テストコマンド
        command = TestCommand("processor_test")

        # When: プロセッサーでコマンドを実行
        result = self.processor.execute_command(command)

        # Then: コマンドが実行され、履歴に記録される
        assert result.success is True
        assert result.result == "executed_processor_test"
        
        history = self.processor.get_command_history()
        assert len(history) == 1
        assert history[0] is command

    def test_正常系_複数コマンド実行(self):
        """正常系: 複数コマンド実行の確認"""
        # Given: 複数のテストコマンド
        commands = [
            TestCommand("first"),
            TestCommand("second"),
            TestCommand("third")
        ]

        # When: 複数のコマンドを実行
        results = []
        for command in commands:
            result = self.processor.execute_command(command)
            results.append(result)

        # Then: 全てのコマンドが実行され、履歴に記録される
        assert len(results) == 3
        assert all(result.success for result in results)
        
        history = self.processor.get_command_history()
        assert len(history) == 3
        for i, command in enumerate(commands):
            assert history[i] is command

    def test_正常系_バッチ実行(self):
        """正常系: バッチ実行の確認"""
        # Given: バッチ実行用コマンド
        commands = [
            TestCommand("batch1"),
            TestCommand("batch2"),
            TestCommand("batch3")
        ]

        # When: バッチでコマンドを実行
        results = self.processor.execute_batch(commands)

        # Then: 全てのコマンドが実行される
        assert len(results) == 3
        assert all(result.success for result in results)
        
        # 履歴確認
        history = self.processor.get_command_history()
        assert len(history) == 3

    def test_正常系_バッチ実行_一部失敗(self):
        """正常系: バッチ実行での一部失敗処理確認"""
        # Given: 成功・失敗混在のコマンド
        commands = [
            TestCommand("batch_success1"),
            TestCommand("batch_failure", should_fail=True),
            TestCommand("batch_success2")
        ]

        # When: バッチでコマンドを実行
        results = self.processor.execute_batch(commands)

        # Then: 全てのコマンドが実行される（失敗しても継続）
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True

    def test_正常系_アンドゥ実行(self):
        """正常系: アンドゥ実行の確認"""
        # Given: アンドゥ可能なコマンド
        command = UndoableTestCommand("undoable")
        self.processor.execute_command(command)

        # When: アンドゥを実行
        undo_result = self.processor.undo_last()

        # Then: アンドゥが実行される
        assert undo_result is not None
        assert undo_result.success is True
        assert undo_result.result == "undone_undoable"
        assert command.undo_count == 1

    def test_正常系_アンドゥ対象なし(self):
        """正常系: アンドゥ対象がない場合の確認"""
        # Given: アンドゥ不可のコマンドのみ
        command = TestCommand("not_undoable")
        self.processor.execute_command(command)

        # When: アンドゥを実行
        undo_result = self.processor.undo_last()

        # Then: Noneが返される
        assert undo_result is None

    def test_正常系_履歴取得_制限あり(self):
        """正常系: 履歴取得の制限機能確認"""
        # Given: 複数のコマンド実行
        for i in range(10):
            command = TestCommand(f"history_{i}")
            self.processor.execute_command(command)

        # When: 制限付きで履歴を取得
        limited_history = self.processor.get_command_history(limit=3)

        # Then: 制限された数の履歴が返される（最新から）
        assert len(limited_history) == 3
        assert limited_history[0].action == "history_7"  # 最新から3番目
        assert limited_history[1].action == "history_8"  # 最新から2番目
        assert limited_history[2].action == "history_9"  # 最新

    def test_正常系_履歴クリア(self):
        """正常系: 履歴クリアの確認"""
        # Given: 履歴のあるプロセッサー
        command = TestCommand("to_be_cleared")
        self.processor.execute_command(command)
        assert len(self.processor.get_command_history()) == 1

        # When: 履歴をクリア
        self.processor.clear_history()

        # Then: 履歴が空になる
        assert len(self.processor.get_command_history()) == 0

    def test_境界値_履歴最大数到達(self):
        """境界値: 履歴最大数到達時の動作確認"""
        # Given: 履歴最大数を小さく設定
        self.processor._max_history = 3

        # When: 最大数を超えるコマンドを実行
        commands = []
        for i in range(5):
            command = TestCommand(f"max_history_{i}")
            commands.append(command)
            self.processor.execute_command(command)

        # Then: 最大数分のみ履歴が保持される
        history = self.processor.get_command_history()
        assert len(history) == 3
        # 最新の3件が保持されている
        assert history[0] is commands[2]  # max_history_2
        assert history[1] is commands[3]  # max_history_3
        assert history[2] is commands[4]  # max_history_4


class TestCommandQueue:
    """コマンドキューのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.queue = CommandQueue(max_workers=2)

    def test_正常系_キュー初期化(self):
        """正常系: キューの初期化確認"""
        # Given: CommandQueueクラス
        # When: キューを初期化
        queue = CommandQueue(max_workers=3)

        # Then: 正しく初期化される
        assert queue._max_workers == 3
        assert len(queue._queue) == 0
        assert len(queue._running_commands) == 0

    def test_正常系_コマンドキューイング(self):
        """正常系: コマンドキューイングの確認"""
        # Given: テストコマンド
        command = TestCommand("queued")

        # When: コマンドをキューに追加
        self.queue.enqueue(command)

        # Then: キューに追加される
        assert len(self.queue._queue) == 1
        assert self.queue._queue[0] is command

    def test_正常系_キュー処理_単一コマンド(self):
        """正常系: 単一コマンドのキュー処理確認"""
        # Given: キューに追加されたコマンド
        command = TestCommand("queue_process", execution_time=0.01)
        self.queue.enqueue(command)

        # When: キューを処理
        self.queue.process_queue()
        
        # 処理完了を待機
        time.sleep(0.05)

        # Then: コマンドが実行される
        assert len(self.queue._queue) == 0  # キューから削除される
        assert command.status == CommandStatus.COMPLETED

    def test_正常系_キュー処理_複数コマンド(self):
        """正常系: 複数コマンドのキュー処理確認"""
        # Given: 複数のコマンド
        commands = [
            TestCommand("queue1", execution_time=0.01),
            TestCommand("queue2", execution_time=0.01),
            TestCommand("queue3", execution_time=0.01)
        ]
        
        for command in commands:
            self.queue.enqueue(command)

        # When: キューを処理
        self.queue.process_queue()
        
        # 処理完了を待機
        time.sleep(0.1)

        # Then: 全てのコマンドが実行される
        assert len(self.queue._queue) <= 1  # max_workers=2なので、同時実行制限
        for command in commands[:2]:  # 最初の2つは実行される
            assert command.status in [CommandStatus.COMPLETED, CommandStatus.RUNNING]

    def test_境界値_最大ワーカー数制限(self):
        """境界値: 最大ワーカー数制限の確認"""
        # Given: 多数のコマンドとワーカー数制限
        commands = [TestCommand(f"worker_{i}", execution_time=0.02) for i in range(5)]
        
        for command in commands:
            self.queue.enqueue(command)

        # When: キュー処理開始
        self.queue.process_queue()
        
        # 少し待機して実行状況確認
        time.sleep(0.01)

        # Then: 最大ワーカー数分のみ同時実行される
        running_count = len(self.queue._running_commands)
        assert running_count <= self.queue._max_workers

    def test_境界値_空キュー処理(self):
        """境界値: 空キューの処理確認"""
        # Given: 空のキュー
        # When: 空キューを処理
        self.queue.process_queue()

        # Then: エラーなく完了する
        assert len(self.queue._queue) == 0
        assert len(self.queue._running_commands) == 0


class TestThreadSafety:
    """スレッドセーフティのテスト"""

    def test_並行性_プロセッサー同時実行(self):
        """並行性: プロセッサーでの同時実行確認"""
        # Given: コマンドプロセッサーと複数スレッド
        processor = CommandProcessor()
        results = []
        results_lock = threading.Lock()

        def execute_commands(thread_id: int):
            """スレッド内でコマンド実行"""
            thread_results = []
            for i in range(5):
                command = TestCommand(f"thread_{thread_id}_cmd_{i}")
                result = processor.execute_command(command)
                thread_results.append(result)
            
            with results_lock:
                results.extend(thread_results)

        # When: 複数スレッドで同時にコマンド実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=execute_commands, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了を待機
        for thread in threads:
            thread.join()

        # Then: 全てのコマンドが正常に実行される
        assert len(results) == 15  # 3スレッド × 5コマンド
        assert all(result.success for result in results)
        
        # 履歴も正しく記録される
        history = processor.get_command_history()
        assert len(history) == 15

    def test_並行性_キュー同時追加(self):
        """並行性: キューへの同時追加確認"""
        # Given: コマンドキューと複数スレッド
        queue = CommandQueue(max_workers=2)
        commands_added = []
        add_lock = threading.Lock()

        def add_commands(thread_id: int):
            """スレッド内でコマンド追加"""
            for i in range(10):
                command = TestCommand(f"concurrent_{thread_id}_{i}")
                queue.enqueue(command)
                with add_lock:
                    commands_added.append(command)

        # When: 複数スレッドで同時にコマンド追加
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_commands, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了を待機
        for thread in threads:
            thread.join()

        # Then: 全てのコマンドがキューに追加される
        assert len(commands_added) == 30  # 3スレッド × 10コマンド
        assert len(queue._queue) == 30


class TestIntegration:
    """統合テスト"""

    def test_統合_完全なコマンドワークフロー(self):
        """統合: 完全なコマンドワークフローの確認"""
        # Given: パーサー、レンダラー、プロセッサー
        parser = MockParser("workflow_parser")
        renderer = MockRenderer("workflow_renderer")
        processor = CommandProcessor()

        # When: パース→レンダリングのワークフロー実行
        parse_command = ParseCommand("workflow content", parser, {"format": "test"})
        parse_result = processor.execute_command(parse_command)

        render_command = RenderCommand(parse_result.result, renderer, {"format": "html"})
        render_result = processor.execute_command(render_command)

        # Then: 全ワークフローが正常に実行される
        assert parse_result.success is True
        assert render_result.success is True
        assert "parsed_workflow_parser" in parse_result.result
        assert "rendered_workflow_renderer" in render_result.result
        
        # 履歴確認
        history = processor.get_command_history()
        assert len(history) == 2
        assert history[0] is parse_command
        assert history[1] is render_command

    def test_統合_エラー処理とリトライ(self):
        """統合: エラー処理とリトライの確認"""
        # Given: エラーが発生するコマンドとプロセッサー
        processor = CommandProcessor()

        # 最初は失敗、2回目は成功するパーサー
        class FlakeyParser:
            def __init__(self):
                self.call_count = 0

            def parse(self, content: str, context: Dict[str, Any]) -> str:
                self.call_count += 1
                if self.call_count == 1:
                    raise ValueError("First attempt fails")
                return f"parsed_attempt_{self.call_count}:{content}"

        flakey_parser = FlakeyParser()

        # When: 失敗→成功のシーケンスを実行
        first_command = ParseCommand("retry content", flakey_parser)
        first_result = processor.execute_command(first_command)

        second_command = ParseCommand("retry content", flakey_parser)  
        second_result = processor.execute_command(second_command)

        # Then: 最初は失敗、2回目は成功
        assert first_result.success is False
        assert second_result.success is True
        assert "parsed_attempt_2" in second_result.result

    def test_統合_複雑なコマンドチェーン(self):
        """統合: 複雑なコマンドチェーンの確認"""
        # Given: 複数段階の処理チェーン
        processor = CommandProcessor()
        
        # 段階的な処理を行うコマンド群
        commands = [
            TestCommand("step1"),
            TestCommand("step2"),  
            TestCommand("step3"),
            UndoableTestCommand("step4_undoable"),
            TestCommand("step5")
        ]

        # When: 段階的にコマンドを実行
        results = []
        for command in commands:
            result = processor.execute_command(command)
            results.append(result)

        # step4をアンドゥ
        undo_result = processor.undo_last()

        # Then: 全ての処理が正常に実行される
        assert all(result.success for result in results)
        assert undo_result is not None
        assert undo_result.success is True
        
        # 履歴とアンドゥ確認
        history = processor.get_command_history()
        assert len(history) == 5
        assert commands[3].undo_count == 1

    def test_境界値_大量コマンド処理(self):
        """境界値: 大量コマンド処理の確認"""
        # Given: 大量のコマンド
        processor = CommandProcessor()
        commands = [TestCommand(f"mass_{i}") for i in range(1000)]

        # When: バッチで大量コマンドを実行
        results = processor.execute_batch(commands)

        # Then: 全てのコマンドが処理される
        assert len(results) == 1000
        assert all(result.success for result in results)
        
        # 履歴サイズ制限確認
        history = processor.get_command_history()
        assert len(history) == 1000  # デフォルト最大履歴数内