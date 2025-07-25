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
            memory_available=8589934592,
            disk_available=107374182400,
        )

        # When
        summary = analyzer.create_error_summary(error, context_stack, system_context)

        # Then
        assert summary["error_type"] == "ValueError"
        assert summary["error_message"] == "Test error"
        assert summary["timestamp"] is not None
        assert summary["context_stack_depth"] == 1
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
                modified_time=datetime.now(),
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

    def test_analyze_error_patterns_file_errors(self):
        """ファイルエラーパターン分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = FileNotFoundError("No such file or directory: test.txt")
        context_stack = [
            OperationContext(
                operation_type="file_read",
                description="Read input file",
                metadata={"file_path": "test.txt"},
            )
        ]

        # When
        patterns = analyzer.analyze_error_patterns(error, context_stack)

        # Then
        assert "file_not_found" in patterns
        assert patterns["file_not_found"]["confidence"] >= 0.8
        assert "file_path" in patterns["file_not_found"]

    def test_analyze_error_patterns_encoding_errors(self):
        """エンコーディングエラーパターン分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = UnicodeDecodeError("utf-8", b"\x80\x81", 0, 2, "invalid start byte")
        context_stack = [
            OperationContext(
                operation_type="parse",
                description="Parse content",
                metadata={"encoding": "utf-8"},
            )
        ]

        # When
        patterns = analyzer.analyze_error_patterns(error, context_stack)

        # Then
        assert "encoding_error" in patterns
        assert patterns["encoding_error"]["confidence"] >= 0.9
        assert patterns["encoding_error"]["detected_encoding"] == "utf-8"

    def test_analyze_error_patterns_permission_errors(self):
        """権限エラーパターン分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = PermissionError("Permission denied")
        context_stack = [
            OperationContext(
                operation_type="file_write",
                description="Write output file",
                metadata={"file_path": "/protected/file.txt"},
            )
        ]

        # When
        patterns = analyzer.analyze_error_patterns(error, context_stack)

        # Then
        assert "permission_denied" in patterns
        assert patterns["permission_denied"]["confidence"] >= 0.9
        assert patterns["permission_denied"]["operation"] == "file_write"

    def test_analyze_error_patterns_syntax_errors(self):
        """構文エラーパターン分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = ValueError("Invalid syntax at line 10")
        context_stack = [
            OperationContext(
                operation_type="parse",
                description="Parse markdown syntax",
                metadata={"line_number": 10, "content": ";;;invalid;;;"},
            )
        ]

        # When
        patterns = analyzer.analyze_error_patterns(error, context_stack)

        # Then
        assert any("syntax" in key for key in patterns)

    def test_get_root_cause_estimation_file_operation(self):
        """根本原因推定: ファイル操作エラー"""
        # Given
        analyzer = ContextAnalyzer()
        patterns = {
            "file_not_found": {
                "confidence": 0.9,
                "file_path": "/nonexistent/file.txt",
            }
        }
        context_stack = [
            OperationContext(
                operation_type="file_read",
                description="Read configuration file",
            )
        ]

        # When
        estimation = analyzer.get_root_cause_estimation(patterns, context_stack)

        # Then
        assert estimation["most_likely_cause"] == "file_not_found"
        assert estimation["confidence"] >= 0.8
        assert "ファイルが存在しない" in estimation["description"]

    def test_get_root_cause_estimation_encoding(self):
        """根本原因推定: エンコーディングエラー"""
        # Given
        analyzer = ContextAnalyzer()
        patterns = {
            "encoding_error": {
                "confidence": 0.95,
                "detected_encoding": "utf-8",
                "suggested_encodings": ["shift_jis", "cp932"],
            }
        }
        context_stack = []

        # When
        estimation = analyzer.get_root_cause_estimation(patterns, context_stack)

        # Then
        assert estimation["most_likely_cause"] == "encoding_error"
        assert "エンコーディング" in estimation["description"]
        assert len(estimation["suggestions"]) > 0

    def test_generate_diagnostic_report(self):
        """診断レポート生成テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = ValueError("Test error")
        summary = {
            "error_type": "ValueError",
            "error_message": "Test error",
            "timestamp": datetime.now().isoformat(),
        }
        patterns = {"test_pattern": {"confidence": 0.8}}
        root_cause = {
            "most_likely_cause": "test_cause",
            "confidence": 0.8,
            "description": "Test description",
        }

        # When
        report = analyzer.generate_diagnostic_report(
            error, summary, patterns, root_cause
        )

        # Then
        assert "エラー診断レポート" in report
        assert "ValueError" in report
        assert "Test error" in report
        assert "推定原因" in report
        assert "test_cause" in report

    def test_format_context_stack(self):
        """コンテキストスタックのフォーマットテスト"""
        # Given
        analyzer = ContextAnalyzer()
        context_stack = [
            OperationContext(
                operation_type="file_read",
                description="Read input file",
                start_time=datetime.now(),
            ),
            OperationContext(
                operation_type="parse",
                description="Parse content",
                start_time=datetime.now(),
                metadata={"line_count": 100},
            ),
        ]

        # When
        formatted = analyzer._format_context_stack(context_stack)

        # Then
        assert len(formatted) == 2
        assert formatted[0]["operation_type"] == "file_read"
        assert formatted[1]["metadata"]["line_count"] == 100

    def test_format_file_contexts(self):
        """ファイルコンテキストのフォーマットテスト"""
        # Given
        analyzer = ContextAnalyzer()
        file_contexts = {
            "test.txt": FileContext(
                file_path="test.txt",
                file_size=1024,
                encoding="utf-8",
                modified_time=datetime.now(),
                permissions="rw-r--r--",
            )
        }

        # When
        formatted = analyzer._format_file_contexts(file_contexts)

        # Then
        assert "test.txt" in formatted
        assert formatted["test.txt"]["file_size"] == 1024
        assert formatted["test.txt"]["encoding"] == "utf-8"
        assert formatted["test.txt"]["permissions"] == "rw-r--r--"

    def test_export_report_json(self):
        """JSON形式レポートエクスポートテスト"""
        # Given
        analyzer = ContextAnalyzer()
        report_data = {
            "error_type": "TestError",
            "timestamp": datetime.now().isoformat(),
            "patterns": {"test": {"confidence": 0.9}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            temp_path = Path(tmp.name)

        try:
            # When
            analyzer.export_report(report_data, temp_path, format="json")

            # Then
            assert temp_path.exists()
            with open(temp_path, "r") as f:
                loaded = json.load(f)
            assert loaded["error_type"] == "TestError"
            assert "patterns" in loaded
        finally:
            temp_path.unlink()

    def test_export_report_text(self):
        """テキスト形式レポートエクスポートテスト"""
        # Given
        analyzer = ContextAnalyzer()
        report_data = {
            "error_type": "TestError",
            "diagnostic_report": "Test diagnostic report\nLine 2\nLine 3",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            temp_path = Path(tmp.name)

        try:
            # When
            analyzer.export_report(report_data, temp_path, format="text")

            # Then
            assert temp_path.exists()
            content = temp_path.read_text(encoding="utf-8")
            assert "Test diagnostic report" in content
        finally:
            temp_path.unlink()

    def test_export_report_invalid_format(self):
        """無効な形式でのレポートエクスポートテスト"""
        # Given
        analyzer = ContextAnalyzer()
        report_data = {"error_type": "TestError"}
        temp_path = Path("test_report.xml")

        # When/Then
        with pytest.raises(ValueError, match="Unsupported format"):
            analyzer.export_report(report_data, temp_path, format="xml")

    def test_pattern_analysis_multiple_errors(self):
        """複数エラーパターンの分析テスト"""
        # Given
        analyzer = ContextAnalyzer()
        error = OSError("Multiple issues")
        context_stack = [
            OperationContext(
                operation_type="file_write",
                description="Write to disk",
                metadata={
                    "file_path": "/full/disk/file.txt",
                    "disk_space": 0,
                    "permissions": "r--r--r--",
                },
            )
        ]

        # When
        patterns = analyzer.analyze_error_patterns(error, context_stack)

        # Then
        # 複数のパターンが検出される可能性
        assert len(patterns) >= 1
        # 少なくとも1つのパターンが検出される
        assert any(p.get("confidence", 0) > 0 for p in patterns.values())

    def test_integration_full_analysis_flow(self):
        """統合テスト: 完全な分析フロー"""
        # Given
        analyzer = ContextAnalyzer()
        error = FileNotFoundError("Cannot find config.yaml")

        # Setup contexts
        operation_context = OperationContext(
            operation_type="config_load",
            description="Load configuration file",
            start_time=datetime.now(),
            metadata={"config_path": "config.yaml", "cwd": "/app"},
        )
        system_context = SystemContext(
            python_version="3.12.0",
            platform="darwin",
            memory_available=8589934592,
        )

        # When
        # 1. Create error summary
        summary = analyzer.create_error_summary(
            error, [operation_context], system_context
        )

        # 2. Analyze patterns
        patterns = analyzer.analyze_error_patterns(error, [operation_context])

        # 3. Estimate root cause
        root_cause = analyzer.get_root_cause_estimation(patterns, [operation_context])

        # 4. Generate report
        report = analyzer.generate_diagnostic_report(
            error, summary, patterns, root_cause
        )

        # Then
        assert summary["error_type"] == "FileNotFoundError"
        assert "file_not_found" in patterns
        assert root_cause["most_likely_cause"] == "file_not_found"
        assert "config.yaml" in report
        assert "推定原因" in report

    @patch("kumihan_formatter.core.error_handling.context_analyzer.get_logger")
    def test_logging_behavior(self, mock_get_logger):
        """ログ出力の動作テスト"""
        # Given
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        analyzer = ContextAnalyzer()

        # When
        analyzer.create_error_summary(ValueError("Test"), [], SystemContext())

        # Then
        mock_logger.debug.assert_called()
        assert "エラーサマリー作成開始" in mock_logger.debug.call_args[0][0]
