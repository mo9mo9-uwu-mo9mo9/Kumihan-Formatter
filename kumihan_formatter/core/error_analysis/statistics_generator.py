"""
エラー統計・分析システム
Issue #700対応 - 高度なエラー表示機能

包括的なエラー分析と統計表示機能
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..common.error_base import GracefulSyntaxError
from ..utilities.logger import get_logger


@dataclass
class ErrorStatistics:
    """エラー統計情報"""

    total_errors: int
    error_by_severity: Dict[str, int]
    error_by_pattern: Dict[str, int]
    error_by_line_range: Dict[str, int]  # 行範囲別（1-10, 11-50, 51-100, 100+）
    most_common_errors: List[Dict[str, Any]]
    suggestions_generated: int
    processing_timestamp: str
    file_path: str = ""


class StatisticsGenerator:
    """
    エラー統計・分析生成システム

    機能:
    - 包括的なエラー統計の生成
    - エラーパターンの分析
    - HTML形式の統計レポート生成
    - エラー傾向の可視化データ作成
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    def generate_statistics(
        self, errors: List[GracefulSyntaxError], file_path: str = ""
    ) -> ErrorStatistics:
        """包括的なエラー統計を生成"""
        if not errors:
            return ErrorStatistics(
                total_errors=0,
                error_by_severity={},
                error_by_pattern={},
                error_by_line_range={},
                most_common_errors=[],
                suggestions_generated=0,
                processing_timestamp=datetime.now().isoformat(),
                file_path=file_path,
            )

        # 基本統計
        total_errors = len(errors)

        # 重要度別集計
        severity_counts = {}
        for error in errors:
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1

        # パターン別集計
        pattern_counts = {}
        for error in errors:
            pattern = error.classify_error_pattern()
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # 行範囲別集計
        line_range_counts = {"1-10": 0, "11-50": 0, "51-100": 0, "100+": 0}
        for error in errors:
            line_num = error.line_number
            if line_num <= 10:
                line_range_counts["1-10"] += 1
            elif line_num <= 50:
                line_range_counts["11-50"] += 1
            elif line_num <= 100:
                line_range_counts["51-100"] += 1
            else:
                line_range_counts["100+"] += 1

        # 最も多いエラーパターンTOP5
        most_common = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]
        most_common_errors = [
            {
                "pattern": pattern,
                "count": count,
                "percentage": (count / total_errors) * 100,
                "example_message": self._get_example_message(errors, pattern),
            }
            for pattern, count in most_common
        ]

        # 提案生成数
        suggestions_generated = sum(
            len(error.correction_suggestions) for error in errors
        )

        statistics = ErrorStatistics(
            total_errors=total_errors,
            error_by_severity=severity_counts,
            error_by_pattern=pattern_counts,
            error_by_line_range=line_range_counts,
            most_common_errors=most_common_errors,
            suggestions_generated=suggestions_generated,
            processing_timestamp=datetime.now().isoformat(),
            file_path=file_path,
        )

        self.logger.info(f"Generated statistics for {total_errors} errors")
        return statistics

    def _get_example_message(
        self, errors: List[GracefulSyntaxError], pattern: str
    ) -> str:
        """特定パターンの例示メッセージを取得"""
        for error in errors:
            if error.classify_error_pattern() == pattern:
                return error.message
        return ""

    def generate_html_report(self, statistics: ErrorStatistics) -> str:
        """HTML形式の統計レポートを生成"""
        if statistics.total_errors == 0:
            return self._generate_no_errors_html()

        html_parts = [
            '<div class="error-statistics-report">',
            "<h3>エラー統計レポート</h3>",
            f'<p class="timestamp">生成日時: {statistics.processing_timestamp}</p>',
            # 概要
            '<div class="stats-overview">',
            f'<div class="stat-item">'
            f'<span class="stat-label">総エラー数:</span> '
            f'<span class="stat-value">{statistics.total_errors}</span>'
            f"</div>",
            f'<div class="stat-item">'
            f'<span class="stat-label">修正提案数:</span> '
            f'<span class="stat-value">{statistics.suggestions_generated}</span>'
            f"</div>",
            "</div>",
            # 重要度別グラフ
            self._generate_severity_chart(statistics.error_by_severity),
            # パターン別分析
            self._generate_pattern_analysis(statistics.most_common_errors),
            # 行範囲別分布
            self._generate_line_range_chart(statistics.error_by_line_range),
            "</div>",
        ]

        return "\n".join(html_parts)

    def _generate_no_errors_html(self) -> str:
        """エラーなしの場合のHTML"""
        return """
        <div class="error-statistics-report no-errors">
            <h3>エラー統計レポート</h3>
            <div class="success-message">
                <span class="success-icon">✅</span>
                エラーは検出されませんでした。
            </div>
        </div>
        """

    def _generate_severity_chart(self, severity_counts: Dict[str, int]) -> str:
        """重要度別チャートHTML生成"""
        if not severity_counts:
            return ""

        total = sum(severity_counts.values())

        chart_html = ['<div class="severity-chart">', "<h4>重要度別分布</h4>"]

        severity_order = ["error", "warning", "info"]
        severity_labels = {"error": "エラー", "warning": "警告", "info": "情報"}
        severity_colors = {"error": "#ff4444", "warning": "#ffaa00", "info": "#4444ff"}

        for severity in severity_order:
            if severity in severity_counts:
                count = severity_counts[severity]
                percentage = (count / total) * 100
                color = severity_colors[severity]
                label = severity_labels[severity]

                chart_html.append(
                    f"""
                <div class="severity-bar">
                    <span class="severity-label">{label}:</span>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {percentage}%; "
                             "background-color: {color};"></div>
                        <span class="bar-value">{count} ({percentage:.1f}%)</span>
                    </div>
                </div>
                """
                )

        chart_html.append("</div>")
        return "\n".join(chart_html)

    def _generate_pattern_analysis(
        self, most_common_errors: List[Dict[str, Any]]
    ) -> str:
        """パターン分析HTML生成"""
        if not most_common_errors:
            return ""

        html_parts = [
            '<div class="pattern-analysis">',
            "<h4>最も多いエラーパターン</h4>",
        ]

        pattern_labels = {
            "marker_mismatch": "マーカー不一致",
            "incomplete_marker": "不完全マーカー",
            "invalid_syntax": "無効な構文",
            "missing_element": "要素不足",
            "invalid_color": "無効な色指定",
            "general_syntax": "一般的な構文エラー",
        }

        for i, error_info in enumerate(most_common_errors, 1):
            pattern = error_info["pattern"]
            count = error_info["count"]
            percentage = error_info["percentage"]
            example = error_info["example_message"]

            label = pattern_labels.get(pattern, pattern)

            html_parts.append(
                f"""
            <div class="pattern-item">
                <div class="pattern-header">
                    <span class="pattern-rank">#{i}</span>
                    <span class="pattern-name">{label}</span>
                    <span class="pattern-stats">{count}件 ({percentage:.1f}%)</span>
                </div>
                <div class="pattern-example">例: {example}</div>
            </div>
            """
            )

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _generate_line_range_chart(self, line_range_counts: Dict[str, int]) -> str:
        """行範囲別チャートHTML生成"""
        if not any(line_range_counts.values()):
            return ""

        total = sum(line_range_counts.values())

        html_parts = ['<div class="line-range-chart">', "<h4>エラー発生行の分布</h4>"]

        for range_name, count in line_range_counts.items():
            if count > 0:
                percentage = (count / total) * 100
                html_parts.append(
                    f"""
                <div class="range-bar">
                    <span class="range-label">行 {range_name}:</span>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {percentage}%; "
                             "background-color: #6699cc;"></div>
                        <span class="bar-value">{count}件 ({percentage:.1f}%)</span>
                    </div>
                </div>
                """
                )

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def save_statistics_json(
        self, statistics: ErrorStatistics, output_path: Path
    ) -> None:
        """統計情報をJSONファイルに保存"""
        try:
            stats_data = {
                "total_errors": statistics.total_errors,
                "error_by_severity": statistics.error_by_severity,
                "error_by_pattern": statistics.error_by_pattern,
                "error_by_line_range": statistics.error_by_line_range,
                "most_common_errors": statistics.most_common_errors,
                "suggestions_generated": statistics.suggestions_generated,
                "processing_timestamp": statistics.processing_timestamp,
                "file_path": statistics.file_path,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Statistics saved to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")

    def generate_summary_text(self, statistics: ErrorStatistics) -> str:
        """テキスト形式の統計サマリーを生成"""
        if statistics.total_errors == 0:
            return "エラーは検出されませんでした。"

        summary_lines = [
            "=== エラー統計サマリー ===",
            f"総エラー数: {statistics.total_errors}",
            f"修正提案数: {statistics.suggestions_generated}",
            "",
        ]

        # 重要度別
        if statistics.error_by_severity:
            summary_lines.append("重要度別:")
            for severity, count in statistics.error_by_severity.items():
                percentage = (count / statistics.total_errors) * 100
                summary_lines.append(f"  {severity}: {count}件 ({percentage:.1f}%)")
            summary_lines.append("")

        # 最も多いパターンTOP3
        if statistics.most_common_errors:
            summary_lines.append("最も多いエラーパターン:")
            for i, error_info in enumerate(statistics.most_common_errors[:3], 1):
                pattern = error_info["pattern"]
                count = error_info["count"]
                percentage = error_info["percentage"]
                summary_lines.append(f"  {i}. {pattern}: {count}件 ({percentage:.1f}%)")

        return "\n".join(summary_lines)
