"""
エラー統計機能のテスト

Important Tier Phase 2-1対応 - Issue #593
エラー統計・履歴管理機能の体系的テスト実装
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.error_statistics import ErrorStatistics
from kumihan_formatter.core.error_handling.error_types import (
    ErrorCategory,
    ErrorLevel,
    UserFriendlyError,
)


class TestErrorStatistics:
    """エラー統計機能のテストクラス"""

    def test_init_with_defaults(self):
        """デフォルト設定での初期化テスト"""
        # When
        stats = ErrorStatistics()

        # Then
        assert stats.enable_logging is True
        assert stats.logger is not None
        assert len(stats._error_history) == 0
        assert len(stats._error_stats) == 0

    def test_init_without_logging(self):
        """ログ無効での初期化テスト"""
        # When
        stats = ErrorStatistics(enable_logging=False)

        # Then
        assert stats.enable_logging is False
        assert stats.logger is None

    def test_update_error_stats_single_error(self):
        """単一エラーの統計更新テスト"""
        # Given
        stats = ErrorStatistics()
        error = UserFriendlyError(
            message="Test error",
            original_error=ValueError("Original error"),
            category=ErrorCategory.FILE,
        )

        # When
        stats.update_error_stats(error)

        # Then
        assert len(stats._error_history) == 1
        assert stats._error_stats[ErrorCategory.FILE.value] == 1
        assert stats._error_history[0] is error

    def test_update_error_stats_multiple_same_category(self):
        """同一カテゴリの複数エラー統計更新テスト"""
        # Given
        stats = ErrorStatistics()
        errors = [
            UserFriendlyError(
                message="File error 1",
                original_error=FileNotFoundError("File not found"),
                category=ErrorCategory.FILE,
            ),
            UserFriendlyError(
                message="File error 2",
                original_error=PermissionError("Permission denied"),
                category=ErrorCategory.FILE,
            ),
        ]

        # When
        for error in errors:
            stats.update_error_stats(error)

        # Then
        assert len(stats._error_history) == 2
        assert stats._error_stats[ErrorCategory.FILE.value] == 2

    def test_update_error_stats_different_categories(self):
        """異なるカテゴリのエラー統計更新テスト"""
        # Given
        stats = ErrorStatistics()
        errors = [
            UserFriendlyError(
                message="File error",
                original_error=FileNotFoundError(),
                category=ErrorCategory.FILE,
            ),
            UserFriendlyError(
                message="Parse error",
                original_error=ValueError("Parse failed"),
                category=ErrorCategory.PARSE,
            ),
            UserFriendlyError(
                message="Render error",
                original_error=RuntimeError("Render failed"),
                category=ErrorCategory.RENDER,
            ),
        ]

        # When
        for error in errors:
            stats.update_error_stats(error)

        # Then
        assert len(stats._error_history) == 3
        assert stats._error_stats[ErrorCategory.FILE.value] == 1
        assert stats._error_stats[ErrorCategory.PARSE.value] == 1
        assert stats._error_stats[ErrorCategory.RENDER.value] == 1

    def test_record_success(self):
        """成功記録のテスト"""
        # Given
        stats = ErrorStatistics()
        operation_name = "file_parse"

        # When
        stats.record_success(operation_name)

        # Then
        # 成功統計が記録される（現在の実装による）
        assert stats._success_stats[operation_name] == 1

    def test_record_error(self):
        """エラー記録のテスト"""
        # Given
        stats = ErrorStatistics()
        operation_name = "file_read"
        error = ValueError("Test error")

        # When
        stats.record_error(operation_name, error)

        # Then
        # エラー統計が記録される
        assert operation_name in stats._operation_errors
        assert stats._operation_errors[operation_name] == 1

    def test_get_error_counts(self):
        """エラー件数取得テスト"""
        # Given
        stats = ErrorStatistics()
        errors = [
            UserFriendlyError(
                message="Error 1",
                original_error=ValueError(),
                category=ErrorCategory.FILE,
            ),
            UserFriendlyError(
                message="Error 2",
                original_error=RuntimeError(),
                category=ErrorCategory.PARSE,
            ),
            UserFriendlyError(
                message="Error 3",
                original_error=FileNotFoundError(),
                category=ErrorCategory.FILE,
            ),
        ]

        for error in errors:
            stats.update_error_stats(error)

        # When
        counts = stats.get_error_counts()

        # Then
        assert counts[ErrorCategory.FILE.value] == 2
        assert counts[ErrorCategory.PARSE.value] == 1
        assert counts.get(ErrorCategory.RENDER.value, 0) == 0

    def test_get_error_history(self):
        """エラー履歴取得テスト"""
        # Given
        stats = ErrorStatistics()
        error1 = UserFriendlyError(
            message="First error",
            original_error=ValueError("Error 1"),
        )
        error2 = UserFriendlyError(
            message="Second error",
            original_error=RuntimeError("Error 2"),
        )

        stats.update_error_stats(error1)
        stats.update_error_stats(error2)

        # When
        history = stats.get_error_history()

        # Then
        assert len(history) == 2
        assert history[0] is error1
        assert history[1] is error2

    def test_get_error_history_with_limit(self):
        """制限付きエラー履歴取得テスト"""
        # Given
        stats = ErrorStatistics()
        for i in range(10):
            error = UserFriendlyError(
                message=f"Error {i}",
                original_error=ValueError(f"Error {i}"),
            )
            stats.update_error_stats(error)

        # When
        history = stats.get_error_history(limit=5)

        # Then
        assert len(history) == 5
        # 最新の5件が返される（実装による）

    def test_clear_statistics(self):
        """統計クリアテスト"""
        # Given
        stats = ErrorStatistics()
        error = UserFriendlyError(
            message="Test error",
            original_error=ValueError("Error"),
        )
        stats.update_error_stats(error)

        # When
        stats.clear_statistics()

        # Then
        assert len(stats._error_history) == 0
        assert len(stats._error_stats) == 0

    def test_export_statistics_json(self):
        """JSON形式統計エクスポートテスト"""
        # Given
        stats = ErrorStatistics()
        errors = [
            UserFriendlyError(
                message="File error",
                original_error=FileNotFoundError(),
                category=ErrorCategory.FILE,
            ),
            UserFriendlyError(
                message="Parse error",
                original_error=ValueError(),
                category=ErrorCategory.PARSE,
            ),
        ]

        for error in errors:
            stats.update_error_stats(error)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            temp_path = Path(tmp.name)

        try:
            # When
            stats.export_statistics(temp_path, format="json")

            # Then
            assert temp_path.exists()
            with open(temp_path, "r") as f:
                exported_data = json.load(f)

            assert "error_counts" in exported_data
            assert "total_errors" in exported_data
            assert exported_data["total_errors"] == 2
        finally:
            temp_path.unlink()

    def test_export_statistics_csv(self):
        """CSV形式統計エクスポートテスト"""
        # Given
        stats = ErrorStatistics()
        error = UserFriendlyError(
            message="Test error",
            original_error=ValueError(),
            category=ErrorCategory.FILE,
        )
        stats.update_error_stats(error)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            temp_path = Path(tmp.name)

        try:
            # When
            stats.export_statistics(temp_path, format="csv")

            # Then
            assert temp_path.exists()
            content = temp_path.read_text()
            assert "category" in content
            assert "count" in content
        finally:
            temp_path.unlink()

    def test_export_statistics_invalid_format(self):
        """無効な形式での統計エクスポートテスト"""
        # Given
        stats = ErrorStatistics()
        temp_path = Path("test_stats.xml")

        # When/Then
        with pytest.raises(ValueError, match="Unsupported format"):
            stats.export_statistics(temp_path, format="xml")

    def test_get_top_errors(self):
        """上位エラー取得テスト"""
        # Given
        stats = ErrorStatistics()

        # FILE カテゴリのエラーを5回追加
        for _ in range(5):
            stats.update_error_stats(
                UserFriendlyError(
                    message="File error",
                    original_error=FileNotFoundError(),
                    category=ErrorCategory.FILE,
                )
            )

        # PARSE カテゴリのエラーを3回追加
        for _ in range(3):
            stats.update_error_stats(
                UserFriendlyError(
                    message="Parse error",
                    original_error=ValueError(),
                    category=ErrorCategory.PARSE,
                )
            )

        # RENDER カテゴリのエラーを1回追加
        stats.update_error_stats(
            UserFriendlyError(
                message="Render error",
                original_error=RuntimeError(),
                category=ErrorCategory.RENDER,
            )
        )

        # When
        top_errors = stats.get_top_errors(limit=2)

        # Then
        assert len(top_errors) == 2
        assert top_errors[0][0] == ErrorCategory.FILE.value
        assert top_errors[0][1] == 5
        assert top_errors[1][0] == ErrorCategory.PARSE.value
        assert top_errors[1][1] == 3

    def test_get_error_trends(self):
        """エラー傾向取得テスト"""
        # Given
        stats = ErrorStatistics()

        # 時系列でエラーを追加
        with patch("datetime.datetime") as mock_datetime:
            # 異なる時刻でエラーを記録
            timestamps = [
                datetime(2024, 1, 1, 10, 0),
                datetime(2024, 1, 1, 11, 0),
                datetime(2024, 1, 1, 12, 0),
            ]

            for i, timestamp in enumerate(timestamps):
                mock_datetime.now.return_value = timestamp
                error = UserFriendlyError(
                    message=f"Error {i}",
                    original_error=ValueError(f"Error {i}"),
                    category=ErrorCategory.FILE,
                )
                stats.update_error_stats(error)

        # When
        trends = stats.get_error_trends()

        # Then
        assert len(trends) > 0
        # 時系列データが含まれている

    def test_calculate_error_rate(self):
        """エラー率計算テスト"""
        # Given
        stats = ErrorStatistics()

        # 成功とエラーを記録
        for _ in range(7):
            stats.record_success("operation")

        for _ in range(3):
            stats.record_error("operation", ValueError("Error"))

        # When
        error_rate = stats.calculate_error_rate("operation")

        # Then
        assert error_rate == 0.3  # 3 errors out of 10 total operations

    def test_get_summary_statistics(self):
        """サマリー統計取得テスト"""
        # Given
        stats = ErrorStatistics()

        # 各カテゴリのエラーを追加
        categories = [ErrorCategory.FILE, ErrorCategory.PARSE, ErrorCategory.RENDER]
        for category in categories:
            for _ in range(2):
                error = UserFriendlyError(
                    message=f"{category.value} error",
                    original_error=ValueError("Error"),
                    category=category,
                )
                stats.update_error_stats(error)

        # When
        summary = stats.get_summary_statistics()

        # Then
        assert summary["total_errors"] == 6
        assert summary["unique_categories"] == 3
        assert len(summary["category_breakdown"]) == 3

    @patch("kumihan_formatter.core.error_handling.error_statistics.get_logger")
    def test_logging_behavior(self, mock_get_logger):
        """ログ出力動作のテスト"""
        # Given
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        stats = ErrorStatistics(enable_logging=True)

        error = UserFriendlyError(
            message="Test error",
            original_error=ValueError("Error"),
            category=ErrorCategory.FILE,
        )

        # When
        stats.update_error_stats(error)

        # Then
        mock_logger.debug.assert_called()
        assert "Error stats updated" in mock_logger.debug.call_args[0][0]

    def test_error_statistics_thread_safety(self):
        """エラー統計のスレッドセーフティテスト"""
        # Given
        stats = ErrorStatistics()

        def add_errors():
            for _ in range(10):
                error = UserFriendlyError(
                    message="Thread error",
                    original_error=ValueError("Error"),
                    category=ErrorCategory.FILE,
                )
                stats.update_error_stats(error)

        # When
        import threading

        threads = [threading.Thread(target=add_errors) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Then
        assert stats._error_stats[ErrorCategory.FILE.value] == 50
