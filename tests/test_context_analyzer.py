"""
コンテキスト分析器のテスト

Important Tier Phase 2-1対応 - Issue #593
エラーコンテキスト分析・診断機能の体系的テスト実装
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.context_analyzer import ContextAnalyzer
from kumihan_formatter.core.error_handling.context_models import (
    FileContext,
    OperationContext,
    SystemContext,
)


class TestContextAnalyzer:
    """コンテキスト分析器のテストクラス"""

    def test_init(self):
        """初期化テスト"""
        # When
        analyzer = ContextAnalyzer()

        # Then
        assert analyzer.logger is not None

    def test_create_error_summary_basic(self):
        """基本的なエラーサマリー作成テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = ValueError("Test error")
        context_stack = [
            OperationContext(
                operation_name="parse",
                component="markdown_parser",
                started_at=datetime.now(),
            )
        ]
        system_context = SystemContext(
            python_version="3.12.0",
            platform="darwin",
            memory_usage=8589934592,
            disk_space=107374182400,
        )

        # When
        summary = analyzer.create_error_summary(error, context_stack, system_context)

        # Then
        assert summary["error_type"] == "ValueError"
        assert summary["error_message"] == "Test error"
        assert summary["timestamp"] is not None
        assert len(summary["operation_chain"]) == 1
        assert summary["system_info"]["python_version"] == "3.12.0"

    def test_create_error_summary_with_file_contexts(self):
        """ファイルコンテキスト付きエラーサマリー作成テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = FileNotFoundError("File not found")
        context_stack = []
        system_context = SystemContext()
        file_contexts = {
            "test.txt": FileContext(
                file_path="test.txt",
                file_size=1024,
                encoding="utf-8",
                last_modified=datetime.now(),
            )
        }

        # When
        summary = analyzer.create_error_summary(
            error, context_stack, system_context, file_contexts
        )

        # Then
        assert summary["error_type"] == "FileNotFoundError"
        assert "file_contexts" in summary
        assert "test.txt" in summary["file_contexts"]

    def test_suggest_probable_cause_basic(self):
        """基本的な推定原因分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = FileNotFoundError("No such file or directory: test.txt")
        context_stack = [
            OperationContext(
                operation_name="file_read",
                component="file_reader",
                metadata={"file_path": "test.txt"},
            )
        ]
        system_context = SystemContext()

        # When
        probable_cause = analyzer.suggest_probable_cause(
            error, context_stack, system_context
        )

        # Then
        assert probable_cause["primary_cause"] is not None
        assert probable_cause["confidence"] > 0

    def test_suggest_probable_cause_encoding_error(self):
        """エンコーディングエラー推定原因分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = UnicodeDecodeError("utf-8", b"\x80\x81", 0, 2, "invalid start byte")
        context_stack = [
            OperationContext(
                operation_name="parse",
                component="parser",
                metadata={"encoding": "utf-8"},
            )
        ]
        system_context = SystemContext()

        # When
        probable_cause = analyzer.suggest_probable_cause(
            error, context_stack, system_context
        )

        # Then
        assert probable_cause["primary_cause"] is not None
        assert probable_cause["confidence"] > 0

    def test_suggest_probable_cause_permission_error(self):
        """権限エラー推定原因分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = PermissionError("Permission denied")
        context_stack = [
            OperationContext(
                operation_name="file_write",
                component="file_writer",
                metadata={"file_path": "/protected/file.txt"},
            )
        ]
        system_context = SystemContext()

        # When
        probable_cause = analyzer.suggest_probable_cause(
            error, context_stack, system_context
        )

        # Then
        assert probable_cause["primary_cause"] is not None
        assert probable_cause["confidence"] > 0

    def test_get_context_breadcrumb(self):
        """コンテキストブレッドクラム取得テスト"""
        # Given
        analyzer = ContextAnalyzer()
        context_stack = [
            OperationContext(
                operation_name="file_read",
                component="file_reader",
                started_at=datetime.now(),
            ),
            OperationContext(
                operation_name="parse",
                component="parser",
                started_at=datetime.now(),
                metadata={"line_count": 100},
            ),
        ]

        # When
        breadcrumb = analyzer.get_context_breadcrumb(context_stack)

        # Then
        assert isinstance(breadcrumb, str)
        assert "file_read" in breadcrumb
        assert "parse" in breadcrumb

    def test_generate_detailed_report(self):
        """詳細レポート生成テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = ValueError("Test error")
        context_stack = [
            OperationContext(
                operation_name="parse",
                component="parser",
                started_at=datetime.now(),
            )
        ]
        system_context = SystemContext()

        # When
        report = analyzer.generate_detailed_report(error, context_stack, system_context)

        # Then
        assert isinstance(report, dict)
        assert "error_analysis" in report
        assert report["error_analysis"]["error_type"] == "ValueError"

    def test_export_context_as_json(self):
        """JSON形式コンテキストエクスポートテスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = ValueError("Test error")
        context_stack = [
            OperationContext(
                operation_name="parse",
                component="parser",
                started_at=datetime.now(),
            )
        ]
        system_context = SystemContext()

        # When
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            output_path = Path(tmp.name)
            analyzer.export_context_as_json(
                context_stack, system_context, output_path=output_path
            )

        # Then - ファイルが作成されたことを確認
        assert output_path.exists()
