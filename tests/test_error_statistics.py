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
    ErrorSolution,
    UserFriendlyError,
)


class TestErrorStatistics:
    """エラー統計機能のテストクラス"""

    def test_init_with_defaults(self):
        """デフォルト設定での初期化テスト"""
        # When
        stats = ErrorStatistics()

        # Then
        assert stats._error_stats == {}
        assert stats._error_history == []
        assert stats.enable_logging is True

    def test_init_without_logging(self):
        """ログなし初期化テスト"""
        # When
        stats = ErrorStatistics(enable_logging=False)

        # Then
        assert stats.enable_logging is False
        assert stats.logger is None

    def test_update_error_stats_single_error(self):
        """単一エラー統計更新テスト"""
        # Given
        stats = ErrorStatistics()
        error = UserFriendlyError(
            error_code="TEST_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message="Test error",
            solution=ErrorSolution(quick_fix="Test fix", detailed_steps=["Step 1"]),
        )

        # When
        stats.update_error_stats(error)

        # Then
        assert len(stats._error_history) == 1
        assert stats._error_stats[ErrorCategory.FILE_SYSTEM.value] == 1
        assert stats._error_history[0] is error

    def test_update_error_stats_multiple_same_category(self):
        """同一カテゴリの複数エラー統計更新テスト"""
        # Given
        stats = ErrorStatistics()
        errors = [
            UserFriendlyError(
                error_code="FILE_ERROR_1",
                level=ErrorLevel.ERROR,
                category=ErrorCategory.FILE_SYSTEM,
                user_message="File error 1",
                solution=ErrorSolution(
                    quick_fix="File fix 1", detailed_steps=["Step 1"]
                ),
            ),
            UserFriendlyError(
                error_code="FILE_ERROR_2",
                level=ErrorLevel.ERROR,
                category=ErrorCategory.FILE_SYSTEM,
                user_message="File error 2",
                solution=ErrorSolution(
                    quick_fix="File fix 2", detailed_steps=["Step 1"]
                ),
            ),
        ]

        # When
        for error in errors:
            stats.update_error_stats(error)

        # Then
        assert len(stats._error_history) == 2
        assert stats._error_stats[ErrorCategory.FILE_SYSTEM.value] == 2

    def test_get_error_statistics_empty(self):
        """エラー統計取得テスト（空の場合）"""
        # Given
        stats = ErrorStatistics()

        # When
        statistics = stats.get_error_statistics()

        # Then
        assert statistics["total_errors"] == 0
        assert statistics["error_categories"] == {}
        assert statistics["summary"] == "No errors recorded"

    def test_get_error_statistics_with_data(self):
        """エラー統計取得テスト（データありの場合）"""
        # Given
        stats = ErrorStatistics()
        error = UserFriendlyError(
            error_code="TEST_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message="Test error",
            solution=ErrorSolution(quick_fix="Test fix", detailed_steps=["Step 1"]),
        )
        stats.update_error_stats(error)

        # When
        statistics = stats.get_error_statistics()

        # Then
        assert statistics["total_errors"] == 1
        assert statistics["error_categories"][ErrorCategory.FILE_SYSTEM.value] == 1
        assert "file_system" in statistics["summary"]

    def test_clear_error_history(self):
        """エラー履歴クリアテスト"""
        # Given
        stats = ErrorStatistics()
        error = UserFriendlyError(
            error_code="TEST_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message="Test error",
            solution=ErrorSolution(quick_fix="Test fix", detailed_steps=["Step 1"]),
        )
        stats.update_error_stats(error)

        # When
        stats.clear_error_history()

        # Then
        assert stats._error_stats == {}
        assert stats._error_history == []

    def test_export_error_log(self):
        """エラーログエクスポートテスト"""
        # Given
        stats = ErrorStatistics()
        error = UserFriendlyError(
            error_code="TEST_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message="Test error",
            solution=ErrorSolution(quick_fix="Test fix", detailed_steps=["Step 1"]),
        )
        stats.update_error_stats(error)

        # When
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            output_path = Path(tmp.name)
            result = stats.export_error_log(output_path)

        # Then
        assert result is True
        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "total_errors" in data
            assert data["total_errors"] == 1

    def test_get_error_trends_empty(self):
        """エラー傾向取得テスト（空の場合）"""
        # Given
        stats = ErrorStatistics()

        # When
        trends = stats.get_error_trends()

        # Then
        assert trends["trends"] == "No error data available"

    def test_get_error_trends_basic_structure(self):
        """エラー傾向の基本構造テスト"""
        # Given
        stats = ErrorStatistics()

        # When - エラー履歴が空でもメソッド実行可能
        trends = stats.get_error_trends()

        # Then - 基本構造は常に含まれる
        assert "daily_error_counts" in trends or "trends" in trends

    def test_multiple_categories(self):
        """複数カテゴリのテスト"""
        # Given
        stats = ErrorStatistics()
        errors = [
            UserFriendlyError(
                error_code="FILE_ERROR",
                level=ErrorLevel.ERROR,
                category=ErrorCategory.FILE_SYSTEM,
                user_message="File error",
                solution=ErrorSolution(quick_fix="File fix", detailed_steps=["Step 1"]),
            ),
            UserFriendlyError(
                error_code="SYNTAX_ERROR",
                level=ErrorLevel.ERROR,
                category=ErrorCategory.SYNTAX,
                user_message="Syntax error",
                solution=ErrorSolution(
                    quick_fix="Syntax fix", detailed_steps=["Step 1"]
                ),
            ),
        ]

        # When
        for error in errors:
            stats.update_error_stats(error)

        # Then
        statistics = stats.get_error_statistics()
        assert statistics["total_errors"] == 2
        assert statistics["error_categories"][ErrorCategory.FILE_SYSTEM.value] == 1
        assert statistics["error_categories"][ErrorCategory.SYNTAX.value] == 1

    def test_error_levels_tracking(self):
        """エラーレベル追跡テスト"""
        # Given
        stats = ErrorStatistics()
        errors = [
            UserFriendlyError(
                error_code="ERROR_ERROR",
                level=ErrorLevel.ERROR,
                category=ErrorCategory.UNKNOWN,
                user_message="Error level",
                solution=ErrorSolution(
                    quick_fix="Error fix", detailed_steps=["Step 1"]
                ),
            ),
            UserFriendlyError(
                error_code="WARNING_ERROR",
                level=ErrorLevel.WARNING,
                category=ErrorCategory.UNKNOWN,
                user_message="Warning level",
                solution=ErrorSolution(
                    quick_fix="Warning fix", detailed_steps=["Step 1"]
                ),
            ),
        ]

        # When
        for error in errors:
            stats.update_error_stats(error)

        # Then
        statistics = stats.get_error_statistics()
        assert statistics["error_levels"][ErrorLevel.ERROR.value] == 1
        assert statistics["error_levels"][ErrorLevel.WARNING.value] == 1

    def test_recent_errors_limit(self):
        """最近のエラー制限テスト（最新5件まで）"""
        # Given
        stats = ErrorStatistics()

        # When - 7個のエラーを追加
        for i in range(7):
            error = UserFriendlyError(
                error_code=f"ERROR_{i}",
                level=ErrorLevel.ERROR,
                category=ErrorCategory.UNKNOWN,
                user_message=f"Error {i}",
                solution=ErrorSolution(quick_fix=f"Fix {i}", detailed_steps=["Step 1"]),
            )
            stats.update_error_stats(error)

        # Then
        statistics = stats.get_error_statistics()
        assert len(statistics["recent_errors"]) == 5  # 最新5件のみ

    @patch("kumihan_formatter.core.error_handling.error_statistics.get_logger")
    def test_logging_behavior(self, mock_get_logger):
        """ログ出力動作のテスト"""
        # Given
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        stats = ErrorStatistics(enable_logging=True)
        error = UserFriendlyError(
            error_code="LOG_ERROR",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.UNKNOWN,
            user_message="Test error",
            solution=ErrorSolution(quick_fix="Log fix", detailed_steps=["Step 1"]),
        )

        # When
        stats.update_error_stats(error)

        # Then
        mock_get_logger.assert_called_once()
