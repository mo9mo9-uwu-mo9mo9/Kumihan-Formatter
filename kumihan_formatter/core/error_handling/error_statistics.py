"""Error statistics and history management

Single Responsibility Principle適用: エラー統計機能の分離
Issue #476 Phase5対応 - unified_handler.py分割
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..utilities.logger import get_logger
from .error_types import ErrorCategory, ErrorLevel, UserFriendlyError


class ErrorStatistics:
    """Error statistics and history management

    Handles:
    - Error history tracking
    - Error statistics calculation
    - Error log export
    """

    def __init__(self, enable_logging: bool = True):
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__) if enable_logging else None
        self._error_history: list[UserFriendlyError] = []
        self._error_stats: dict[str, int] = {}

    def update_error_stats(self, error: UserFriendlyError) -> None:
        """エラー統計を更新

        Args:
            error: 統計に追加するエラー
        """
        category = (
            error.category.value
            if hasattr(error.category, "value")
            else str(error.category)
        )
        self._error_stats[category] = self._error_stats.get(category, 0) + 1
        self._error_history.append(error)

        if self.logger:
            self.logger.debug(
                f"Error stats updated: {category} count is now {self._error_stats[category]}"
            )

    def get_error_statistics(self) -> dict[str, Any]:
        """エラー統計情報を取得

        Returns:
            エラー統計情報の辞書
        """
        total_errors = len(self._error_history)

        if total_errors == 0:
            return {
                "total_errors": 0,
                "error_categories": {},
                "error_levels": {},
                "recent_errors": [],
                "summary": "No errors recorded",
            }

        # カテゴリー別統計
        category_stats = {}
        level_stats = {}

        for error in self._error_history:
            category = (
                error.category.value
                if hasattr(error.category, "value")
                else str(error.category)
            )
            level = (
                error.level.value if hasattr(error.level, "value") else str(error.level)
            )

            category_stats[category] = category_stats.get(category, 0) + 1
            level_stats[level] = level_stats.get(level, 0) + 1

        # 最近のエラー（最新5件）
        recent_errors = []
        for error in self._error_history[-5:]:
            recent_errors.append(
                {
                    "message": error.message,
                    "category": (
                        error.category.value
                        if hasattr(error.category, "value")
                        else str(error.category)
                    ),
                    "level": (
                        error.level.value
                        if hasattr(error.level, "value")
                        else str(error.level)
                    ),
                    "timestamp": (
                        error.timestamp.isoformat()
                        if hasattr(error, "timestamp")
                        else None
                    ),
                }
            )

        # サマリー生成
        most_common_category = max(category_stats, key=category_stats.get)
        most_common_level = max(level_stats, key=level_stats.get)

        summary = (
            f"Total: {total_errors} errors. "
            f"Most common: {most_common_category} ({category_stats[most_common_category]} times), "
            f"Severity: {most_common_level} ({level_stats[most_common_level]} times)"
        )

        return {
            "total_errors": total_errors,
            "error_categories": category_stats,
            "error_levels": level_stats,
            "recent_errors": recent_errors,
            "summary": summary,
            "statistics_generated_at": datetime.now().isoformat(),
        }

    def clear_error_history(self) -> None:
        """エラー履歴をクリア"""
        cleared_count = len(self._error_history)
        self._error_history.clear()
        self._error_stats.clear()

        if self.logger:
            self.logger.info(f"Error history cleared. Removed {cleared_count} entries.")

    def export_error_log(self, file_path: Path) -> bool:
        """エラーログをファイルにエクスポート

        Args:
            file_path: エクスポート先のファイルパス

        Returns:
            エクスポート成功時True
        """
        try:
            # エラーログデータの構築
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_errors": len(self._error_history),
                "statistics": self.get_error_statistics(),
                "error_history": [],
            }

            # エラー履歴をシリアライズ可能な形式に変換
            for error in self._error_history:
                error_data = {
                    "message": error.message,
                    "category": (
                        error.category.value
                        if hasattr(error.category, "value")
                        else str(error.category)
                    ),
                    "level": (
                        error.level.value
                        if hasattr(error.level, "value")
                        else str(error.level)
                    ),
                    "timestamp": (
                        error.timestamp.isoformat()
                        if hasattr(error, "timestamp")
                        else None
                    ),
                    "details": error.details if hasattr(error, "details") else None,
                    "suggestions": (
                        error.suggestions if hasattr(error, "suggestions") else []
                    ),
                    "context": error.context if hasattr(error, "context") else {},
                }
                export_data["error_history"].append(error_data)

            # ファイルに保存
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            if self.logger:
                self.logger.info(f"Error log exported to {file_path}")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to export error log: {str(e)}")
            return False

    def get_error_trends(self, days: int = 7) -> dict[str, Any]:
        """エラー傾向の分析

        Args:
            days: 分析対象の日数

        Returns:
            エラー傾向の分析結果
        """
        if not self._error_history:
            return {"trends": "No error data available"}

        # 日付別エラー数の集計
        daily_counts = {}
        category_trends = {}

        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for error in self._error_history:
            if hasattr(error, "timestamp") and error.timestamp:
                error_date = error.timestamp.date()
                date_str = error_date.isoformat()

                # 日別カウント
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

                # カテゴリー別トレンド
                category = (
                    error.category.value
                    if hasattr(error.category, "value")
                    else str(error.category)
                )
                if category not in category_trends:
                    category_trends[category] = {}
                category_trends[category][date_str] = (
                    category_trends[category].get(date_str, 0) + 1
                )

        return {
            "daily_error_counts": daily_counts,
            "category_trends": category_trends,
            "analysis_period_days": days,
            "trend_analysis_at": datetime.now().isoformat(),
        }
