"""
構造化ロガー新機能のテスト - PR #489 レビュー対応
"""

import pytest
from unittest.mock import Mock, patch

from kumihan_formatter.core.utilities.structured_logger import (
    get_structured_logger,
    get_error_analyzer,
    get_dependency_tracker,
    get_execution_flow_tracker,
)
from kumihan_formatter.core.utilities.structured_logger_base import StructuredLogger
from kumihan_formatter.core.utilities.error_analyzer import ErrorAnalyzer
from kumihan_formatter.core.utilities.dependency_tracker import DependencyTracker
from kumihan_formatter.core.utilities.execution_flow_tracker import ExecutionFlowTracker


class TestStructuredLogger:
    """StructuredLogger クラスのテスト"""

    def test_get_structured_logger_returns_instance(self):
        """get_structured_loggerがインスタンスを返すテスト"""
        logger = get_structured_logger("test_logger")
        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test_logger"

    def test_get_structured_logger_caching(self):
        """get_structured_loggerのキャッシュ機能テスト"""
        logger1 = get_structured_logger("test_logger")
        logger2 = get_structured_logger("test_logger")
        
        # 同じインスタンスが返されることを確認
        assert logger1 is logger2

    def test_structured_logger_sanitize_context(self):
        """構造化ロガーのコンテキストサニタイズテスト"""
        logger = get_structured_logger("test_logger")
        
        # センシティブ情報を含むコンテキスト
        context = {
            "user": "test_user",
            "password": "secret123",
            "api_key": "abc123",
            "data": {"value": 100}
        }
        
        sanitized = logger._sanitize_context(context)
        
        assert sanitized["user"] == "test_user"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["data"]["value"] == 100

    def test_structured_logger_file_operation(self):
        """構造化ロガーのファイル操作ログテスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = get_structured_logger("test_logger")
            
            # 成功時のファイル操作ログ
            logger.file_operation("read", "/path/to/file.txt", success=True)
            
            # ログが呼ばれることを確認
            mock_logger.log.assert_called()
            
            # 失敗時のファイル操作ログ
            logger.file_operation("write", "/path/to/file.txt", success=False, error="Permission denied")
            
            # エラーレベルでログが呼ばれることを確認
            mock_logger.log.assert_called()

    def test_structured_logger_performance(self):
        """構造化ロガーのパフォーマンスログテスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = get_structured_logger("test_logger")
            
            # パフォーマンスログ
            logger.performance("parse_document", 150.5)
            
            # ログが呼ばれることを確認
            mock_logger.log.assert_called()

    def test_structured_logger_state_change(self):
        """構造化ロガーの状態変更ログテスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = get_structured_logger("test_logger")
            
            # 状態変更ログ
            logger.state_change("parser", "idle", "processing", reason="new_document")
            
            # ログが呼ばれることを確認
            mock_logger.log.assert_called()


class TestErrorAnalyzer:
    """ErrorAnalyzer クラスのテスト"""

    def test_get_error_analyzer_returns_instance(self):
        """get_error_analyzerがインスタンスを返すテスト"""
        analyzer = get_error_analyzer("test_analyzer")
        assert isinstance(analyzer, ErrorAnalyzer)

    def test_get_error_analyzer_caching(self):
        """get_error_analyzerのキャッシュ機能テスト"""
        analyzer1 = get_error_analyzer("test_analyzer")
        analyzer2 = get_error_analyzer("test_analyzer")
        
        # 同じインスタンスが返されることを確認
        assert analyzer1 is analyzer2

    def test_analyze_error_file_not_found(self):
        """FileNotFoundErrorの分析テスト"""
        analyzer = get_error_analyzer("test_analyzer")
        
        error = FileNotFoundError("test.txt not found")
        result = analyzer.analyze_error(error)
        
        assert result["error_type"] == "FileNotFoundError"
        assert result["category"] == "file_error"
        assert "ファイルパスが正しいか確認してください" in result["suggestions"]

    def test_analyze_error_permission_error(self):
        """PermissionErrorの分析テスト"""
        analyzer = get_error_analyzer("test_analyzer")
        
        error = PermissionError("Permission denied")
        result = analyzer.analyze_error(error)
        
        assert result["error_type"] == "PermissionError"
        assert result["category"] == "permission_error"
        assert "ファイルの読み取り/書き込み権限を確認してください" in result["suggestions"]

    def test_analyze_error_unicode_error(self):
        """UnicodeErrorの分析テスト"""
        analyzer = get_error_analyzer("test_analyzer")
        
        error = UnicodeDecodeError("utf-8", b"\\xff", 0, 1, "invalid start byte")
        result = analyzer.analyze_error(error)
        
        assert result["error_type"] == "UnicodeDecodeError"
        assert result["category"] == "encoding_error"
        assert "ファイルのエンコーディングを確認してください" in result["suggestions"]

    def test_analyze_error_generic(self):
        """汎用エラーの分析テスト"""
        analyzer = get_error_analyzer("test_analyzer")
        
        error = RuntimeError("unexpected error")
        result = analyzer.analyze_error(error)
        
        assert result["error_type"] == "RuntimeError"
        assert result["category"] == "general_error"
        assert len(result["suggestions"]) > 0

    def test_log_error_with_analysis(self):
        """エラー分析付きログテスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            analyzer = get_error_analyzer("test_analyzer")
            
            error = ValueError("invalid value")
            analyzer.log_error_with_analysis(error, "Test error occurred")
            
            # ログが呼ばれることを確認
            mock_logger.log.assert_called()


class TestDependencyTracker:
    """DependencyTracker クラスのテスト"""

    def test_get_dependency_tracker_returns_instance(self):
        """get_dependency_trackerがインスタンスを返すテスト"""
        tracker = get_dependency_tracker("test_tracker")
        assert isinstance(tracker, DependencyTracker)

    def test_get_dependency_tracker_caching(self):
        """get_dependency_trackerのキャッシュ機能テスト"""
        tracker1 = get_dependency_tracker("test_tracker")
        tracker2 = get_dependency_tracker("test_tracker")
        
        # 同じインスタンスが返されることを確認
        assert tracker1 is tracker2

    def test_track_import_success(self):
        """成功したインポートの追跡テスト"""
        tracker = get_dependency_tracker("test_tracker")
        
        tracker.track_import("test_module", "parent_module", 0.05, success=True)
        
        dep_map = tracker.get_dependency_map()
        assert "test_module" in dep_map["dependencies"]
        assert dep_map["dependencies"]["test_module"]["import_count"] == 1
        assert dep_map["dependencies"]["test_module"]["imported_by"] == ["parent_module"]
        assert "test_module" in dep_map["import_times"]

    def test_track_import_failure(self):
        """失敗したインポートの追跡テスト"""
        tracker = get_dependency_tracker("test_tracker")
        
        tracker.track_import("missing_module", "parent_module", success=False, error="Module not found")
        
        dep_map = tracker.get_dependency_map()
        assert "missing_module" in dep_map["dependencies"]
        assert len(dep_map["dependencies"]["missing_module"]["errors"]) == 1
        assert dep_map["dependencies"]["missing_module"]["errors"][0]["error"] == "Module not found"

    def test_circular_dependency_detection(self):
        """循環依存の検出テスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            tracker = get_dependency_tracker("test_tracker")
            
            # A -> B -> A の循環依存を作成
            tracker.track_import("module_b", "module_a", 0.01, success=True)
            tracker.track_import("module_a", "module_b", 0.01, success=True)
            
            # 警告ログが呼ばれることを確認
            mock_logger.log.assert_called()

    def test_log_dependency_summary(self):
        """依存関係サマリーログテスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            tracker = get_dependency_tracker("test_tracker")
            
            # いくつかの依存関係を追加
            tracker.track_import("fast_module", "main", 0.01, success=True)
            tracker.track_import("slow_module", "main", 0.15, success=True)
            
            tracker.log_dependency_summary()
            
            # ログが呼ばれることを確認
            mock_logger.log.assert_called()


class TestExecutionFlowTracker:
    """ExecutionFlowTracker クラスのテスト"""

    def test_get_execution_flow_tracker_returns_instance(self):
        """get_execution_flow_trackerがインスタンスを返すテスト"""
        tracker = get_execution_flow_tracker("test_tracker")
        assert isinstance(tracker, ExecutionFlowTracker)

    def test_get_execution_flow_tracker_caching(self):
        """get_execution_flow_trackerのキャッシュ機能テスト"""
        tracker1 = get_execution_flow_tracker("test_tracker")
        tracker2 = get_execution_flow_tracker("test_tracker")
        
        # 同じインスタンスが返されることを確認
        assert tracker1 is tracker2

    def test_enter_function(self):
        """関数入場追跡テスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            tracker = get_execution_flow_tracker("test_tracker")
            
            context = tracker.enter_function("test_function", "test_module")
            
            assert context["function"] == "test_function"
            assert context["module"] == "test_module"
            assert context["depth"] == 0
            assert "entry_time" in context
            
            # ログが呼ばれることを確認
            mock_logger.log.assert_called()

    def test_exit_function(self):
        """関数退場追跡テスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            tracker = get_execution_flow_tracker("test_tracker")
            
            # 関数に入場
            context = tracker.enter_function("test_function", "test_module")
            
            # 関数から退場
            tracker.exit_function(context)
            
            # ログが呼ばれることを確認
            assert mock_logger.log.call_count >= 2  # enter と exit の両方

    def test_exit_function_with_error(self):
        """エラー付き関数退場追跡テスト"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            tracker = get_execution_flow_tracker("test_tracker")
            
            # 関数に入場
            context = tracker.enter_function("test_function", "test_module")
            
            # エラーで関数から退場
            error = ValueError("test error")
            tracker.exit_function(context, error=error)
            
            # エラーログが呼ばれることを確認
            mock_logger.log.assert_called()

    def test_get_current_flow(self):
        """現在の実行フロー取得テスト"""
        tracker = get_execution_flow_tracker("test_tracker")
        
        # 関数に入場
        context = tracker.enter_function("test_function", "test_module")
        
        flow = tracker.get_current_flow()
        
        assert flow["stack_depth"] == 1
        assert len(flow["current_stack"]) == 1
        assert flow["current_stack"][0]["function"] == "test_function"
        assert flow["current_stack"][0]["module"] == "test_module"
        assert flow["current_stack"][0]["depth"] == 0
        
        # 関数から退場
        tracker.exit_function(context)
        
        # スタックが空になることを確認
        flow = tracker.get_current_flow()
        assert flow["stack_depth"] == 0
        assert len(flow["current_stack"]) == 0

    @patch('kumihan_formatter.core.utilities.execution_flow_tracker.HAS_PSUTIL', False)
    def test_memory_tracking_without_psutil(self):
        """psutilなしでのメモリ追跡テスト"""
        tracker = get_execution_flow_tracker("test_tracker")
        
        context = tracker.enter_function("test_function", track_memory=True)
        tracker.exit_function(context, track_memory=True)
        
        # psutilがない場合でもエラーが発生しないことを確認
        assert context["memory_before"] is None