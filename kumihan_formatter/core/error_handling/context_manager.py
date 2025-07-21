"""
エラーコンテキスト管理 - 統合インターface

分割されたコンテキスト管理機能を統合し、
後方互換性を維持しながら統一インターフェースを提供。
"""

from contextlib import contextmanager
from typing import Any, Generator

from ..utilities.logger import get_logger
from .context_analyzer import ContextAnalyzer
from .context_models import OperationContext
from .context_tracker import ContextTracker


class ErrorContextManager:
    """エラーコンテキスト管理の統合インターフェース

    分割された機能を統合し、従来のAPIとの互換性を保持
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self._tracker = ContextTracker()
        self._analyzer = ContextAnalyzer()

    @contextmanager
    def operation_context(
        self,
        operation_name: str,
        component: str,
        file_path: str | None = None,
        **metadata: Any,
    ) -> Generator[OperationContext, None, None]:
        """操作コンテキストマネージャー（後方互換性）"""
        with self._tracker.operation_context(
            operation_name, component, file_path, **metadata
        ) as context:
            yield context

    def set_line_position(self, line: int, column: int | None = None) -> None:
        """現在の行・列位置を設定"""
        self._tracker.set_line_position(line, column)

    def set_user_input(self, user_input: str) -> None:
        """現在のユーザー入力を設定"""
        self._tracker.set_user_input(user_input)

    def get_current_context(self) -> OperationContext | None:
        """現在のコンテキストを取得"""
        return self._tracker.get_current_context()

    def get_error_location_info(self) -> dict[str, Any]:
        """エラー位置情報を取得"""
        return self._tracker.get_error_location_info()

    def create_error_summary(self, error: Exception) -> dict[str, Any]:
        """エラーサマリーを作成"""
        context_stack = self._tracker.get_context_stack()
        system_context = self._tracker.get_system_context()
        file_contexts = {
            path: self._tracker.get_file_context(path)
            for ctx in context_stack
            if ctx.file_path
            for path in [ctx.file_path]
        }

        return self._analyzer.create_error_summary(
            error, context_stack, system_context, file_contexts
        )

    def suggest_probable_cause(self, error: Exception) -> str:
        """エラーの推定原因を提案"""
        context_stack = self._tracker.get_context_stack()
        system_context = self._tracker.get_system_context()
        result = self._analyzer.suggest_probable_cause(
            error, context_stack, system_context
        )
        # dict結果から文字列に変換
        if isinstance(result, dict):
            cause = result.get("probable_cause", "原因不明")
            return str(cause)
        return str(result)

    def get_context_breadcrumb(self) -> str:
        """コンテキストのパンくずリストを生成"""
        context_stack = self._tracker.get_context_stack()
        return self._analyzer.get_context_breadcrumb(context_stack)

    def clear_contexts(self) -> None:
        """全てのコンテキストをクリア"""
        self._tracker.clear_contexts()

    def export_context_log(self) -> str:
        """コンテキスト情報をログ形式で出力"""
        return self._tracker.export_context_log()

    def generate_detailed_report(self, error: Exception) -> str:
        """詳細なエラーレポートを生成"""
        context_stack = self._tracker.get_context_stack()
        system_context = self._tracker.get_system_context()
        file_contexts = {
            path: self._tracker.get_file_context(path)
            for ctx in context_stack
            if ctx.file_path
            for path in [ctx.file_path]
        }

        result = self._analyzer.generate_detailed_report(
            error, context_stack, system_context, file_contexts
        )
        # dict結果から文字列に変換
        if isinstance(result, dict):
            report = result.get("detailed_report", str(result))
            return str(report)
        return str(result)

    def export_context_as_json(
        self, error: Exception, output_file: str | None = None
    ) -> str:
        """コンテキスト情報をJSONとしてエクスポート"""
        context_stack = self._tracker.get_context_stack()
        system_context = self._tracker.get_system_context()
        file_contexts = {
            path: self._tracker.get_file_context(path)
            for ctx in context_stack
            if ctx.file_path
            for path in [ctx.file_path]
        }

        from pathlib import Path

        output_path = Path(output_file) if output_file else None
        return self._analyzer.export_context_as_json(
            context_stack, system_context, file_contexts, output_path
        )


# グローバルインスタンス - 後方互換性のため
_global_context_manager: ErrorContextManager | None = None


def get_context_manager() -> ErrorContextManager:
    """グローバルコンテキストマネージャーを取得

    Returns:
        ErrorContextManager: グローバルインスタンス
    """
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = ErrorContextManager()
    return _global_context_manager


# 便利関数 - 後方互換性のため
@contextmanager
def operation_context(
    operation_name: str, component: str, file_path: str | None = None, **metadata: Any
) -> Generator[OperationContext, None, None]:
    """グローバル操作コンテキストマネージャー"""
    manager = get_context_manager()
    with manager.operation_context(
        operation_name, component, file_path, **metadata
    ) as ctx:
        yield ctx


def set_line_position(line: int, column: int | None = None) -> None:
    """グローバル行位置設定"""
    manager = get_context_manager()
    manager.set_line_position(line, column)


def set_user_input(user_input: str) -> None:
    """グローバルユーザー入力設定"""
    manager = get_context_manager()
    manager.set_user_input(user_input)


def get_current_context() -> OperationContext | None:
    """グローバル現在コンテキスト取得"""
    manager = get_context_manager()
    return manager.get_current_context()


def clear_contexts() -> None:
    """グローバルコンテキストクリア"""
    manager = get_context_manager()
    manager.clear_contexts()
