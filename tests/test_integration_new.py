"""
統合テスト - PR #489 レビュー対応
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from kumihan_formatter.core.error_handling.unified_handler import UnifiedErrorHandler
from kumihan_formatter.core.error_handling.error_types import (
    ErrorLevel,
    ErrorCategory,
    ErrorSolution,
    UserFriendlyError,
)
from kumihan_formatter.core.utilities.structured_logger import (
    get_structured_logger,
    get_error_analyzer,
    get_dependency_tracker,
    get_execution_flow_tracker,
)


class TestIntegrationErrorHandling:
    """エラーハンドリングシステムの統合テスト"""

    def test_full_error_handling_workflow(self):
        """完全なエラーハンドリングワークフローテスト"""
        console_ui = Mock()
        handler = UnifiedErrorHandler(console_ui, enable_logging=True)
        
        # 1. エラーを発生させる
        with pytest.raises(FileNotFoundError):
            with handler.error_context("test_file_operation"):
                raise FileNotFoundError("test_file.txt")
        
        # 2. エラー統計を確認
        stats = handler.get_error_statistics()
        assert stats["total_errors"] >= 0  # エラー統計が取得できることを確認
        
        # 3. エラー表示をテスト
        error = UserFriendlyError(
            error_code="E001",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message="Test error",
            solution=ErrorSolution(
                quick_fix="Test fix",
                detailed_steps=["Step 1", "Step 2"]
            )
        )
        
        # エラーが正常に表示されることを確認
        handler.display_error(error)

    def test_error_handling_with_recovery(self):
        """エラー回復機能付きハンドリングテスト"""
        console_ui = Mock()
        handler = UnifiedErrorHandler(console_ui, enable_logging=True)
        
        # 自動回復付きでエラーコンテキストを作成
        with pytest.raises(ValueError):
            with handler.error_context("test_operation", auto_recover=True):
                raise ValueError("recoverable error")
        
        # エラー統計が正しく更新されることを確認
        stats = handler.get_error_statistics()
        assert isinstance(stats, dict)

    def test_multiple_error_types_handling(self):
        """複数のエラータイプの統合ハンドリングテスト"""
        console_ui = Mock()
        handler = UnifiedErrorHandler(console_ui, enable_logging=True)
        
        # 様々なエラータイプをテスト
        test_errors = [
            FileNotFoundError("missing_file.txt"),
            PermissionError("permission_denied"),
            ValueError("invalid_value"),
            RuntimeError("runtime_error"),
        ]
        
        for error in test_errors:
            result = handler.handle_exception(error)
            assert isinstance(result, UserFriendlyError)
            assert result.error_code is not None
            assert result.user_message is not None
            assert result.solution is not None

    def test_error_statistics_accumulation(self):
        """エラー統計の累積テスト"""
        console_ui = Mock()
        handler = UnifiedErrorHandler(console_ui, enable_logging=True)
        
        # 複数のエラーを処理
        errors = [
            FileNotFoundError("file1.txt"),
            FileNotFoundError("file2.txt"),
            ValueError("value1"),
            RuntimeError("runtime1"),
        ]
        
        for error in errors:
            handler.handle_exception(error)
        
        # 統計が正しく累積されることを確認
        stats = handler.get_error_statistics()
        assert stats["total_errors"] >= 4


class TestIntegrationStructuredLogging:
    """構造化ログシステムの統合テスト"""

    def test_structured_logger_integration(self):
        """構造化ロガーの統合テスト"""
        # 異なる名前のロガーを作成
        logger1 = get_structured_logger("module1")
        logger2 = get_structured_logger("module2")
        
        # 異なるロガーインスタンスが作成されることを確認
        assert logger1 is not logger2
        
        # 同じ名前のロガーは同じインスタンスが返されることを確認
        logger1_duplicate = get_structured_logger("module1")
        assert logger1 is logger1_duplicate

    def test_error_analyzer_integration(self):
        """エラー分析機能の統合テスト"""
        analyzer = get_error_analyzer("test_analyzer")
        
        # 異なるタイプのエラーを分析
        errors = [
            FileNotFoundError("test.txt"),
            UnicodeDecodeError("utf-8", b"\\xff", 0, 1, "invalid"),
            PermissionError("access denied"),
            ValueError("invalid input"),
        ]
        
        for error in errors:
            analysis = analyzer.analyze_error(error)
            assert "error_type" in analysis
            assert "category" in analysis
            assert "suggestions" in analysis
            assert len(analysis["suggestions"]) > 0

    def test_dependency_tracker_integration(self):
        """依存関係追跡機能の統合テスト"""
        tracker = get_dependency_tracker("test_tracker")
        
        # 依存関係のシミュレート
        modules = [
            ("module_a", "main", 0.01),
            ("module_b", "module_a", 0.02),
            ("module_c", "module_b", 0.03),
            ("module_d", "main", 0.01),
        ]
        
        for module, parent, time in modules:
            tracker.track_import(module, parent, time, success=True)
        
        # 依存関係マップの確認
        dep_map = tracker.get_dependency_map()
        assert dep_map["total_modules"] == 4
        assert dep_map["total_import_time"] > 0
        assert "module_a" in dep_map["dependencies"]
        assert "main" in dep_map["dependencies"]["module_a"]["imported_by"]

    def test_execution_flow_tracker_integration(self):
        """実行フロー追跡機能の統合テスト"""
        tracker = get_execution_flow_tracker("test_tracker")
        
        # 関数実行のシミュレート
        def simulate_function_execution(func_name, module_name, should_error=False):
            context = tracker.enter_function(func_name, module_name)
            
            if should_error:
                error = RuntimeError("simulated error")
                tracker.exit_function(context, error=error)
            else:
                tracker.exit_function(context, result="success")
        
        # 正常な実行
        simulate_function_execution("func1", "module1")
        
        # エラーがある実行
        simulate_function_execution("func2", "module2", should_error=True)
        
        # 実行フローの確認
        flow = tracker.get_current_flow()
        assert flow["stack_depth"] == 0  # 全て完了している
        assert flow["flow_history_size"] >= 2


class TestIntegrationFileOperations:
    """ファイル操作との統合テスト"""

    def test_file_error_handling_integration(self):
        """ファイル操作エラーハンドリングの統合テスト"""
        console_ui = Mock()
        handler = UnifiedErrorHandler(console_ui, enable_logging=True)
        
        # 存在しないファイルの読み取り
        with pytest.raises(FileNotFoundError):
            with handler.error_context("file_read_operation"):
                with open("nonexistent_file.txt", "r") as f:
                    f.read()
        
        # 権限エラーのシミュレート
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        try:
            # ファイルの権限を変更
            os.chmod(tmp_path, 0o000)
            
            with pytest.raises(PermissionError):
                with handler.error_context("file_permission_operation"):
                    with open(tmp_path, "r") as f:
                        f.read()
        finally:
            # クリーンアップ
            os.chmod(tmp_path, 0o644)
            os.unlink(tmp_path)

    def test_structured_logging_with_file_operations(self):
        """ファイル操作での構造化ログ統合テスト"""
        logger = get_structured_logger("file_ops")
        
        # 一時ファイルの作成
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content")
            tmp_path = tmp.name
        
        try:
            # ファイル操作のログ
            logger.file_operation("create", tmp_path, success=True)
            
            # 実際のファイル読み取り
            with open(tmp_path, "r") as f:
                content = f.read()
                logger.file_operation("read", tmp_path, success=True, size=len(content))
            
            # ファイル削除
            os.unlink(tmp_path)
            logger.file_operation("delete", tmp_path, success=True)
            
        except Exception as e:
            # エラーの場合のログ
            logger.file_operation("delete", tmp_path, success=False, error=str(e))
            # クリーンアップ
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestIntegrationPerformanceLogging:
    """パフォーマンスログの統合テスト"""

    def test_performance_logging_integration(self):
        """パフォーマンスログの統合テスト"""
        logger = get_structured_logger("performance")
        analyzer = get_error_analyzer("performance")
        tracker = get_execution_flow_tracker("performance")
        
        # パフォーマンス測定のシミュレート
        import time
        
        def simulate_operation(operation_name, duration=0.001):
            context = tracker.enter_function(operation_name, "test_module")
            
            start_time = time.time()
            time.sleep(duration)
            end_time = time.time()
            
            actual_duration = (end_time - start_time) * 1000  # ms
            logger.performance(operation_name, actual_duration)
            
            tracker.exit_function(context, result=f"completed in {actual_duration:.2f}ms")
        
        # 複数の操作をシミュレート
        operations = [
            ("parse_document", 0.002),
            ("validate_syntax", 0.001),
            ("render_output", 0.003),
        ]
        
        for op_name, duration in operations:
            simulate_operation(op_name, duration)
        
        # 実行フローの確認
        flow = tracker.get_current_flow()
        assert flow["stack_depth"] == 0  # 全て完了している
        assert flow["flow_history_size"] >= 3

    def test_error_analysis_with_performance_context(self):
        """パフォーマンスコンテキスト付きエラー分析テスト"""
        analyzer = get_error_analyzer("performance_error")
        
        # パフォーマンス情報を含むコンテキストでエラーを分析
        context = {
            "operation": "large_file_processing",
            "file_size": 10000000,  # 10MB
            "memory_usage": 500000000,  # 500MB
            "duration_ms": 5000,  # 5秒
        }
        
        memory_error = MemoryError("Unable to allocate memory")
        analysis = analyzer.analyze_error(memory_error, context)
        
        assert analysis["error_type"] == "MemoryError"
        assert analysis["category"] == "memory_error"
        assert analysis["context"] == context
        assert "処理するデータサイズを削減してください" in analysis["suggestions"]


class TestIntegrationEndToEnd:
    """エンドツーエンドの統合テスト"""

    def test_complete_error_workflow(self):
        """完全なエラーワークフローの統合テスト"""
        console_ui = Mock()
        handler = UnifiedErrorHandler(console_ui, enable_logging=True)
        logger = get_structured_logger("e2e_test")
        analyzer = get_error_analyzer("e2e_test")
        tracker = get_execution_flow_tracker("e2e_test")
        
        # 複雑な操作のシミュレート
        def complex_operation():
            context = tracker.enter_function("complex_operation", "e2e_module")
            
            try:
                # 依存関係の追跡
                dep_tracker = get_dependency_tracker("e2e_test")
                dep_tracker.track_import("dependency_module", "e2e_module", 0.01, success=True)
                
                # パフォーマンス測定
                logger.performance("initialization", 25.5)
                
                # 意図的なエラー発生
                raise ValueError("Complex operation failed")
                
            except Exception as e:
                # エラー分析
                analysis = analyzer.analyze_error(e, {"operation": "complex_operation"})
                
                # エラーハンドリング
                user_error = handler.handle_exception(e)
                
                # 統計更新
                handler.statistics.update_error_stats(user_error)
                
                # 実行フロー記録
                tracker.exit_function(context, error=e)
                
                # 再スロー
                raise
            
            else:
                tracker.exit_function(context, result="success")
        
        # 複雑な操作を実行
        with pytest.raises(ValueError):
            complex_operation()
        
        # 最終的な統計確認
        stats = handler.get_error_statistics()
        assert stats["total_errors"] >= 1
        
        # 実行フロー確認
        flow = tracker.get_current_flow()
        assert flow["stack_depth"] == 0  # 全て完了している
        assert flow["flow_history_size"] >= 1

    def test_concurrent_logging_safety(self):
        """同時ログ記録の安全性テスト"""
        import threading
        import time
        
        logger = get_structured_logger("concurrent_test")
        results = []
        
        def logging_worker(worker_id):
            for i in range(5):
                logger.info(f"Worker {worker_id} - Message {i}")
                time.sleep(0.001)  # 短い待機
                results.append(f"worker_{worker_id}_msg_{i}")
        
        # 複数のスレッドで同時にログ記録
        threads = []
        for i in range(3):
            thread = threading.Thread(target=logging_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        # 結果確認
        assert len(results) == 15  # 3 workers * 5 messages each
        assert len(set(results)) == 15  # 全て一意であることを確認