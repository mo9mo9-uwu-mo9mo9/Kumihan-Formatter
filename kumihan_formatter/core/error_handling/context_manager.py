"""
エラーコンテキスト管理 - Issue #401対応

エラー発生時のコンテキスト情報を管理し、
より詳細で有用なエラー情報を提供するシステム。
"""

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utilities.logger import get_logger


@dataclass
class OperationContext:
    """操作コンテキスト情報"""

    operation_name: str
    component: str  # Parser, Renderer, FileOps等
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    user_input: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemContext:
    """システム環境コンテキスト"""

    platform: str = field(default_factory=lambda: sys.platform)
    python_version: str = field(default_factory=lambda: sys.version)
    working_directory: str = field(default_factory=lambda: os.getcwd())
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    disk_space: Optional[int] = None

    def __post_init__(self):
        """システム情報を自動収集"""
        try:
            import psutil

            process = psutil.Process()
            self.memory_usage = process.memory_info().rss
            self.cpu_usage = process.cpu_percent()

            # ディスク使用量
            disk_usage = psutil.disk_usage(self.working_directory)
            self.disk_space = disk_usage.free

        except ImportError:
            # psutil が利用できない場合はスキップ
            pass
        except Exception:
            # その他のエラーも無視
            pass


@dataclass
class FileContext:
    """ファイル操作コンテキスト"""

    file_path: str
    file_size: Optional[int] = None
    encoding: Optional[str] = None
    line_count: Optional[int] = None
    modification_time: Optional[datetime] = None
    checksum: Optional[str] = None

    def __post_init__(self):
        """ファイル情報を自動収集"""
        try:
            path = Path(self.file_path)
            if path.exists():
                stat = path.stat()
                self.file_size = stat.st_size
                self.modification_time = datetime.fromtimestamp(stat.st_mtime)

                # エンコーディング検出を試行
                try:
                    with open(path, "rb") as f:
                        raw_data = f.read(1024)  # 最初の1KBを読み取り

                    # 簡易エンコーディング検出
                    try:
                        raw_data.decode("utf-8")
                        self.encoding = "utf-8"
                    except UnicodeDecodeError:
                        try:
                            raw_data.decode("shift_jis")
                            self.encoding = "shift_jis"
                        except UnicodeDecodeError:
                            self.encoding = "unknown"

                    # 行数カウント
                    if self.encoding != "unknown":
                        with open(path, "r", encoding=self.encoding) as f:
                            self.line_count = sum(1 for _ in f)

                except Exception:
                    # ファイル読み取りエラーは無視
                    pass

        except Exception:
            # ファイル情報取得エラーは無視
            pass


class ErrorContextManager:
    """
    エラーコンテキスト管理システム

    設計ドキュメント:
    - Issue #401: エラーハンドリングの強化と統合
    - コンテキスト情報の自動収集と管理
    - エラー発生時の詳細情報提供

    機能:
    - 操作コンテキストの階層管理
    - ファイル・システム情報の自動収集
    - エラー発生地点の特定
    - デバッグ情報の構造化
    """

    def __init__(self, enable_logging: bool = True):
        """コンテキストマネージャーを初期化

        Args:
            enable_logging: ログ出力を有効にするか
        """
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__) if enable_logging else None

        # コンテキストスタック
        self._operation_stack: List[OperationContext] = []
        self._system_context = SystemContext()
        self._file_contexts: Dict[str, FileContext] = {}

        # デバッグ情報
        self._debug_info: Dict[str, Any] = {}

        if self.logger:
            self.logger.debug("ErrorContextManager initialized")

    @contextmanager
    def operation_context(
        self,
        operation_name: str,
        component: str,
        file_path: Optional[str] = None,
        **metadata,
    ):
        """操作コンテキストマネージャー

        Args:
            operation_name: 操作名
            component: コンポーネント名
            file_path: 対象ファイルパス
            **metadata: 追加のメタデータ
        """
        context = OperationContext(
            operation_name=operation_name,
            component=component,
            file_path=file_path,
            metadata=metadata,
        )

        self._operation_stack.append(context)

        # ファイルコンテキストを作成
        if file_path:
            self._ensure_file_context(file_path)

        try:
            if self.logger:
                self.logger.debug(f"Starting operation: {component}.{operation_name}")
            yield context

        finally:
            self._operation_stack.pop()
            if self.logger:
                elapsed = (datetime.now() - context.started_at).total_seconds()
                self.logger.debug(
                    f"Completed operation: {component}.{operation_name} "
                    f"({elapsed:.3f}s)"
                )

    def _ensure_file_context(self, file_path: str) -> None:
        """ファイルコンテキストが存在しない場合作成"""
        if file_path not in self._file_contexts:
            self._file_contexts[file_path] = FileContext(file_path)

    def set_line_position(
        self, line_number: int, column_number: Optional[int] = None
    ) -> None:
        """現在の行位置を設定

        Args:
            line_number: 行番号
            column_number: 列番号（オプション）
        """
        if self._operation_stack:
            current_context = self._operation_stack[-1]
            current_context.line_number = line_number
            current_context.column_number = column_number

    def set_user_input(self, user_input: str) -> None:
        """ユーザー入力を設定

        Args:
            user_input: ユーザーからの入力
        """
        if self._operation_stack:
            current_context = self._operation_stack[-1]
            current_context.user_input = user_input

    def add_debug_info(self, key: str, value: Any) -> None:
        """デバッグ情報を追加

        Args:
            key: 情報のキー
            value: 情報の値
        """
        self._debug_info[key] = value

    def get_current_context(self) -> Dict[str, Any]:
        """現在のコンテキスト情報を取得

        Returns:
            Dict[str, Any]: 統合されたコンテキスト情報
        """
        context = {
            "system": self._system_context.__dict__,
            "debug_info": self._debug_info.copy(),
        }

        # 現在の操作コンテキスト
        if self._operation_stack:
            current_operation = self._operation_stack[-1]
            context["current_operation"] = current_operation.__dict__

            # ファイルコンテキスト
            if (
                current_operation.file_path
                and current_operation.file_path in self._file_contexts
            ):
                context["file"] = self._file_contexts[
                    current_operation.file_path
                ].__dict__

        # 操作スタック
        context["operation_stack"] = [
            {
                "operation": op.operation_name,
                "component": op.component,
                "started_at": op.started_at.isoformat(),
                "file_path": op.file_path,
            }
            for op in self._operation_stack
        ]

        return context

    def get_error_location_info(self) -> Dict[str, Any]:
        """エラー発生場所の詳細情報を取得

        Returns:
            Dict[str, Any]: エラー発生場所の情報
        """
        if not self._operation_stack:
            return {}

        current_context = self._operation_stack[-1]
        location_info = {
            "operation": current_context.operation_name,
            "component": current_context.component,
            "file_path": current_context.file_path,
            "line_number": current_context.line_number,
            "column_number": current_context.column_number,
        }

        # ファイル情報を追加
        if (
            current_context.file_path
            and current_context.file_path in self._file_contexts
        ):
            file_context = self._file_contexts[current_context.file_path]
            location_info.update(
                {
                    "file_size": file_context.file_size,
                    "file_encoding": file_context.encoding,
                    "total_lines": file_context.line_count,
                }
            )

        return location_info

    def get_context_breadcrumb(self) -> str:
        """コンテキストの階層パス（パンくずリスト）を取得

        Returns:
            str: 階層化された操作パス
        """
        if not self._operation_stack:
            return "システム"

        breadcrumb_parts = []
        for context in self._operation_stack:
            part = f"{context.component}.{context.operation_name}"
            if context.file_path:
                file_name = Path(context.file_path).name
                part += f"({file_name})"
            breadcrumb_parts.append(part)

        return " → ".join(breadcrumb_parts)

    def create_error_summary(self, exception: Exception) -> Dict[str, Any]:
        """例外に対する包括的なエラーサマリーを作成

        Args:
            exception: 発生した例外

        Returns:
            Dict[str, Any]: エラーサマリー情報
        """
        import traceback

        summary = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "context_breadcrumb": self.get_context_breadcrumb(),
            "location_info": self.get_error_location_info(),
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
        }

        # 現在のコンテキストを追加
        summary["full_context"] = self.get_current_context()

        return summary

    def suggest_probable_cause(self, exception: Exception) -> List[str]:
        """例外とコンテキストから推定される原因を提案

        Args:
            exception: 発生した例外

        Returns:
            List[str]: 推定される原因のリスト
        """
        suggestions = []

        current_context = self.get_current_context()

        # ファイル関連の原因
        if isinstance(exception, FileNotFoundError):
            suggestions.extend(
                [
                    "指定されたファイルが存在しない",
                    "ファイルパスに誤りがある",
                    "ファイルが移動または削除された",
                ]
            )

            # ファイルコンテキストから追加情報
            if "file" in current_context:
                file_info = current_context["file"]
                if file_info.get("file_size") == 0:
                    suggestions.append("ファイルが空の可能性")

        # エンコーディング関連の原因
        elif isinstance(exception, UnicodeDecodeError):
            suggestions.extend(
                [
                    "ファイルの文字エンコーディングが不正",
                    "UTF-8以外のエンコーディングで保存されている",
                ]
            )

            if "file" in current_context:
                file_info = current_context["file"]
                if file_info.get("encoding") == "unknown":
                    suggestions.append("サポートされていない文字エンコーディング")

        # 権限関連の原因
        elif isinstance(exception, PermissionError):
            suggestions.extend(
                [
                    "ファイルへのアクセス権限がない",
                    "ファイルが他のアプリケーションで使用中",
                    "読み取り専用ファイルへの書き込み試行",
                ]
            )

        # 値エラー関連の原因
        elif isinstance(exception, ValueError):
            if "current_operation" in current_context:
                operation = current_context["current_operation"]
                if "parse" in operation.get("operation_name", "").lower():
                    suggestions.extend(
                        [
                            "構文エラーまたは記法の間違い",
                            "サポートされていない記法の使用",
                            "記法の組み合わせが不正",
                        ]
                    )

        # システムリソース関連
        system_info = current_context.get("system", {})
        if system_info.get("memory_usage", 0) > 1024 * 1024 * 1024:  # 1GB以上
            suggestions.append("メモリ使用量が高い可能性")

        if system_info.get("disk_space", float("inf")) < 100 * 1024 * 1024:  # 100MB未満
            suggestions.append("ディスク容量不足の可能性")

        return suggestions

    def clear_contexts(self) -> None:
        """すべてのコンテキスト情報をクリア"""
        self._operation_stack.clear()
        self._file_contexts.clear()
        self._debug_info.clear()

        if self.logger:
            self.logger.debug("All contexts cleared")

    def export_context_log(self, file_path: Path) -> bool:
        """コンテキスト情報をファイルにエクスポート

        Args:
            file_path: エクスポート先ファイルパス

        Returns:
            bool: エクスポート成功時True
        """
        try:
            import json

            export_data = {
                "exported_at": datetime.now().isoformat(),
                "system_context": self._system_context.__dict__,
                "file_contexts": {
                    path: context.__dict__
                    for path, context in self._file_contexts.items()
                },
                "debug_info": self._debug_info,
                "current_operation_stack": [
                    op.__dict__ for op in self._operation_stack
                ],
            }

            # datetime オブジェクトを文字列に変換
            def datetime_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            file_path.write_text(
                json.dumps(
                    export_data,
                    ensure_ascii=False,
                    indent=2,
                    default=datetime_serializer,
                ),
                encoding="utf-8",
            )

            if self.logger:
                self.logger.info(f"Context log exported to {file_path}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to export context log: {e}")
            return False


# グローバルインスタンス
_global_context_manager: Optional[ErrorContextManager] = None


def get_global_context_manager() -> ErrorContextManager:
    """グローバルコンテキストマネージャーを取得（遅延初期化）"""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = ErrorContextManager()
    return _global_context_manager


def set_global_context_manager(manager: ErrorContextManager) -> None:
    """グローバルコンテキストマネージャーを設定"""
    global _global_context_manager
    _global_context_manager = manager
