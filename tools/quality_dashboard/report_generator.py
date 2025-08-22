"""
品質レポート生成システム

HTML/PDF形式での包括的品質レポート生成
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger

from .metrics_collector import MetricsCollector

logger = get_logger(__name__)


class ReportGenerator:
    """品質レポート生成管理"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.metrics_collector = MetricsCollector(project_root)
        os.makedirs("tmp", exist_ok=True)

    def generate_comprehensive_report(self, format: str = "html") -> Path:
        """包括的品質レポート生成"""
        metrics = self.metrics_collector.collect_comprehensive_metrics()
        history = self.metrics_collector.get_metrics_history(30)  # 30日分

        if format.lower() == "html":
            return self._generate_html_report(metrics, history)
        elif format.lower() == "json":
            return self._generate_json_report(metrics, history)
        else:
            logger.warning(f"Unsupported format: {format}, falling back to HTML")
            return self._generate_html_report(metrics, history)

    def _generate_html_report(
        self, metrics: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> Path:
        """HTML形式レポート生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("tmp") / f"quality_report_{timestamp}.html"

        html_content = self._create_html_template(metrics, history)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {output_path}")
        return output_path

    def _generate_json_report(
        self, metrics: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> Path:
        """JSON形式レポート生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("tmp") / f"quality_report_{timestamp}.json"

        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "comprehensive_quality",
                "project": "Kumihan-Formatter",
                "version": "1.0.0",
            },
            "current_metrics": metrics,
            "historical_data": history,
            "summary": self._generate_summary(metrics, history),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON report generated: {output_path}")
        return output_path

    def _generate_summary(
        self, metrics: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """レポートサマリー生成"""
        quality_score = metrics.get("quality_score", {})
        coverage = metrics.get("coverage", {})
        complexity = metrics.get("complexity", {})
        performance = metrics.get("performance", {})
        lint = metrics.get("lint", {})

        # トレンド分析
        trend_analysis = self._analyze_trends(history)

        # 改善提案生成
        improvement_suggestions = self._generate_improvement_suggestions(metrics)

        return {
            "overall_status": {
                "quality_score": quality_score.get("score", 0),
                "quality_grade": quality_score.get("grade", "N/A"),
                "primary_concerns": self._identify_primary_concerns(metrics),
            },
            "key_metrics": {
                "coverage_percentage": coverage.get("total_coverage", 0),
                "high_complexity_functions": complexity.get("high_complexity_count", 0),
                "startup_time_ms": performance.get("startup_time_ms", 0),
                "total_lint_issues": lint.get("total_issues", 0),
            },
            "trend_analysis": trend_analysis,
            "improvement_suggestions": improvement_suggestions,
            "compliance_status": self._check_compliance(metrics),
        }

    def _analyze_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """トレンド分析"""
        if len(history) < 2:
            return {"status": "insufficient_data"}

        # 最新と1週間前の比較
        latest = history[-1] if history else {}
        week_ago = history[0] if history else {}

        latest_score = latest.get("quality_score", {}).get("score", 0)
        week_ago_score = week_ago.get("quality_score", {}).get("score", 0)

        score_trend = latest_score - week_ago_score

        latest_coverage = latest.get("coverage", {}).get("total_coverage", 0)
        week_ago_coverage = week_ago.get("coverage", {}).get("total_coverage", 0)

        coverage_trend = latest_coverage - week_ago_coverage

        return {
            "quality_score_trend": {
                "change": score_trend,
                "direction": (
                    "improving"
                    if score_trend > 0
                    else "declining" if score_trend < 0 else "stable"
                ),
                "percentage_change": (
                    (score_trend / week_ago_score * 100) if week_ago_score > 0 else 0
                ),
            },
            "coverage_trend": {
                "change": coverage_trend,
                "direction": (
                    "improving"
                    if coverage_trend > 0
                    else "declining" if coverage_trend < 0 else "stable"
                ),
                "percentage_change": (
                    (coverage_trend / week_ago_coverage * 100)
                    if week_ago_coverage > 0
                    else 0
                ),
            },
            "analysis_period": f"{len(history)} data points over {len(history)} days",
        }

    def _identify_primary_concerns(self, metrics: Dict[str, Any]) -> List[str]:
        """主要な懸念事項特定"""
        concerns = []

        coverage = metrics.get("coverage", {})
        if coverage.get("total_coverage", 0) < 70:
            concerns.append("テストカバレッジが70%を下回っています")

        complexity = metrics.get("complexity", {})
        if complexity.get("high_complexity_count", 0) > 0:
            concerns.append(
                f"{complexity.get('high_complexity_count', 0)}個の高複雑度関数があります"
            )

        performance = metrics.get("performance", {})
        if performance.get("startup_time_ms", 0) > 1000:
            concerns.append("起動時間が1秒を超えています")

        lint = metrics.get("lint", {})
        if lint.get("error_count", 0) > 0:
            concerns.append(f"{lint.get('error_count', 0)}個のlintエラーがあります")

        return concerns

    def _generate_improvement_suggestions(
        self, metrics: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """改善提案生成"""
        suggestions = []

        coverage = metrics.get("coverage", {})
        if coverage.get("total_coverage", 0) < 80:
            suggestions.append(
                {
                    "category": "テストカバレッジ",
                    "priority": "高",
                    "suggestion": "単体テストを追加してカバレッジを80%以上に向上させてください",
                    "impact": "品質保証の強化",
                }
            )

        complexity = metrics.get("complexity", {})
        if complexity.get("high_complexity_count", 0) > 0:
            suggestions.append(
                {
                    "category": "コード複雑度",
                    "priority": "中",
                    "suggestion": "高複雑度関数をリファクタリングして複雑度を10以下に抑えてください",
                    "impact": "保守性の向上",
                }
            )

        performance = metrics.get("performance", {})
        if performance.get("startup_time_ms", 0) > 600:
            suggestions.append(
                {
                    "category": "パフォーマンス",
                    "priority": "中",
                    "suggestion": "遅延ローディングやキャッシュを導入して起動時間を短縮してください",
                    "impact": "ユーザー体験の向上",
                }
            )

        return suggestions

    def _check_compliance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """コンプライアンス状況確認"""
        compliance_checks = {
            "enterprise_quality_standards": {
                "coverage_minimum_70": metrics.get("coverage", {}).get(
                    "total_coverage", 0
                )
                >= 70,
                "complexity_under_10": metrics.get("complexity", {}).get(
                    "high_complexity_count", 0
                )
                == 0,
                "zero_lint_errors": metrics.get("lint", {}).get("error_count", 0) == 0,
                "performance_under_1s": metrics.get("performance", {}).get(
                    "startup_time_ms", 0
                )
                <= 1000,
            }
        }

        # コンプライアンス率計算
        total_checks = len(compliance_checks["enterprise_quality_standards"])
        passed_checks = sum(
            1
            for passed in compliance_checks["enterprise_quality_standards"].values()
            if passed
        )
        compliance_rate = (
            (passed_checks / total_checks * 100) if total_checks > 0 else 0
        )

        return {
            "compliance_rate": compliance_rate,
            "detailed_checks": compliance_checks,
            "overall_status": (
                "COMPLIANT" if compliance_rate == 100 else "NON_COMPLIANT"
            ),
        }

    def _create_html_template(
        self, metrics: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> str:
        """HTMLテンプレート作成"""
        quality_score = metrics.get("quality_score", {})
        coverage = metrics.get("coverage", {})
        complexity = metrics.get("complexity", {})
        performance = metrics.get("performance", {})
        lint = metrics.get("lint", {})

        summary = self._generate_summary(metrics, history)

        return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan-Formatter 品質レポート</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Arial',
            sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(
            135deg,
            #667eea 0%,
            #764ba2 100%
{indent}); color: white; padding: 40px 20px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1.1rem; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(
            auto-fit,
            minmax(250px,
            1fr)
{indent}); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(
            0,
            0,
            0,
            0.1
{indent}); }}
        .summary-card h3 {{ color: #2c3e50; margin-bottom: 15px; font-size: 1.2rem; }}
        .score-display {{ font-size: 3rem; font-weight: bold; text-align: center; margin: 20px 0; }}
        .grade-a {{ color: #27ae60; }}
        .grade-b {{ color: #3498db; }}
        .grade-c {{ color: #f39c12; }}
        .grade-d {{ color: #e74c3c; }}
        .grade-f {{ color: #c0392b; }}
        .section {{ background: white; margin-bottom: 20px; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(
            0,
            0,
            0,
            0.1
{indent}); }}
        .section h2 {{ color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #ecf0f1; }}
        .metrics-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
.metrics-table th,
            .metrics-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        .metrics-table th {{ background: #f8f9fa; font-weight: bold; }}
        .status-pass {{ color: #27ae60; font-weight: bold; }}
        .status-warning {{ color: #f39c12; font-weight: bold; }}
        .status-fail {{ color: #e74c3c; font-weight: bold; }}
        .suggestions {{ background: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60; }}
        .concerns {{ background: #fdf2e9; padding: 20px; border-radius: 8px; border-left: 4px solid #e67e22; }}
        .trend-indicator {{ font-weight: bold; }}
        .trend-up {{ color: #27ae60; }}
        .trend-down {{ color: #e74c3c; }}
        .trend-stable {{ color: #7f8c8d; }}
        .footer {{ text-align: center; margin-top: 40px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Kumihan-Formatter</h1>
            <p>Enterprise品質レポート - {datetime.now().strftime("%Y年%m月%d日 %H:%M")}</p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>📊 総合品質スコア</h3>
                <div class="score-display grade-{quality_score.get('grade', 'f').lower()}">
                    {quality_score.get('score', 0):.1f}/100
                </div>
                <div style="text-align: center; font-size: 1.5rem; font-weight: bold;">
                    グレード: {quality_score.get('grade', 'N/A')}
                </div>
            </div>

            <div class="summary-card">
                <h3>🎯 カバレッジ</h3>
                <div class="score-display" style="color: {'#27ae60' if coverage.get('total_coverage', 0) >= 70 else '#e74c3c'};">
                    {coverage.get('total_coverage', 0):.1f}%
                </div>
                <div style="text-align: center;">
                    {coverage.get('lines_covered', 0)} / {coverage.get('lines_total', 0)} 行
                </div>
            </div>

            <div class="summary-card">
                <h3>⚡ パフォーマンス</h3>
                <div class="score-display" style="color: {'#27ae60' if performance.get('startup_time_ms', 0) <= 600 else '#e74c3c'};">
                    {performance.get('startup_time_ms', 0):.0f}ms
                </div>
                <div style="text-align: center;">
                    起動時間
                </div>
            </div>

            <div class="summary-card">
                <h3>🔍 コード品質</h3>
                <div class="score-display" style="color: {'#27ae60' if lint.get('total_issues', 0) == 0 else '#e74c3c'};">
                    {lint.get('total_issues', 0)}
                </div>
                <div style="text-align: center;">
                    Lint問題
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📈 トレンド分析</h2>
            <table class="metrics-table">
                <tr>
                    <th>指標</th>
                    <th>変化</th>
                    <th>方向</th>
                    <th>変化率</th>
                </tr>
                <tr>
                    <td>品質スコア</td>
                    <td>{summary['trend_analysis'].get(
                        'quality_score_trend',
                        {}).get('change',
                        0
{indent}):+.1f}</td>
                    <td class="trend-indicator trend-{summary['trend_analysis'].get('quality_score_trend', {}).get('direction', 'stable')}">{summary['trend_analysis'].get('quality_score_trend', {}).get('direction', 'stable')}</td>
                    <td>{summary['trend_analysis'].get(
                        'quality_score_trend',
                        {}).get('percentage_change',
                        0
{indent}):+.1f}%</td>
                </tr>
                <tr>
                    <td>カバレッジ</td>
                    <td>{summary['trend_analysis'].get(
                        'coverage_trend',
                        {}).get('change',
                        0
{indent}):+.1f}%</td>
                    <td class="trend-indicator trend-{summary['trend_analysis'].get('coverage_trend', {}).get('direction', 'stable')}">{summary['trend_analysis'].get('coverage_trend', {}).get('direction', 'stable')}</td>
                    <td>{summary['trend_analysis'].get(
                        'coverage_trend',
                        {}).get('percentage_change',
                        0
{indent}):+.1f}%</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>📋 詳細メトリクス</h2>
            <table class="metrics-table">
                <tr><th>カテゴリ</th><th>指標</th><th>値</th><th>ステータス</th></tr>
                <tr>
                    <td>カバレッジ</td>
                    <td>総合カバレッジ</td>
                    <td>{coverage.get('total_coverage', 0):.1f}%</td>
                    <td class="status-{coverage.get('status', 'unknown').lower()}">{coverage.get('status', 'UNKNOWN')}</td>
                </tr>
                <tr>
                    <td>複雑度</td>
                    <td>平均複雑度</td>
                    <td>{complexity.get('average_complexity', 0):.1f}</td>
                    <td class="status-{complexity.get('status', 'unknown').lower()}">{complexity.get('status', 'UNKNOWN')}</td>
                </tr>
                <tr>
                    <td>複雑度</td>
                    <td>高複雑度関数数</td>
                    <td>{complexity.get('high_complexity_count', 0)}</td>
                    <td class="status-{'pass' if complexity.get('high_complexity_count', 0) == 0 else 'warning'}">{
                        'PASS' if complexity.get('high_complexity_count', 0) == 0 else 'WARNING'
                    }</td>
                </tr>
                <tr>
                    <td>パフォーマンス</td>
                    <td>起動時間</td>
                    <td>{performance.get('startup_time_ms', 0):.0f}ms</td>
                    <td class="status-{performance.get('startup_status', 'unknown').lower()}">{performance.get('startup_status', 'UNKNOWN')}</td>
                </tr>
                <tr>
                    <td>パフォーマンス</td>
                    <td>メモリ使用量</td>
                    <td>{performance.get('memory_usage_mb', 0):.1f}MB</td>
                    <td class="status-{performance.get('memory_status', 'unknown').lower()}">{performance.get('memory_status', 'UNKNOWN')}</td>
                </tr>
                <tr>
                    <td>コード品質</td>
                    <td>Lint問題総数</td>
                    <td>{lint.get('total_issues', 0)}</td>
                    <td class="status-{lint.get('status', 'unknown').lower()}">{lint.get('status', 'UNKNOWN')}</td>
                </tr>
            </table>
        </div>

        {self._generate_concerns_section(summary['overall_status']['primary_concerns'])}

        {self._generate_suggestions_section(summary['improvement_suggestions'])}

        <div class="section">
            <h2>✅ コンプライアンス状況</h2>
            <p><strong>Enterprise品質基準達成率:</strong> {summary['compliance_status']['compliance_rate']:.1f}%</p>
            <table class="metrics-table">
                <tr><th>チェック項目</th><th>ステータス</th></tr>
                <tr>
                    <td>カバレッジ70%以上</td>
                    <td class="status-{'pass' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['coverage_minimum_70'] else 'fail'}">
                        {'✅ PASS' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['coverage_minimum_70'] else '❌ FAIL'}
                    </td>
                </tr>
                <tr>
                    <td>複雑度10以下</td>
                    <td class="status-{'pass' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['complexity_under_10'] else 'fail'}">
                        {'✅ PASS' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['complexity_under_10'] else '❌ FAIL'}
                    </td>
                </tr>
                <tr>
                    <td>Lintエラー0件</td>
                    <td class="status-{'pass' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['zero_lint_errors'] else 'fail'}">
                        {'✅ PASS' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['zero_lint_errors'] else '❌ FAIL'}
                    </td>
                </tr>
                <tr>
                    <td>起動時間1秒以下</td>
                    <td class="status-{'pass' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['performance_under_1s'] else 'fail'}">
                        {'✅ PASS' if summary['compliance_status']['detailed_checks']['enterprise_quality_standards']['performance_under_1s'] else '❌ FAIL'}
                    </td>
                </tr>
            </table>
        </div>

        <div class="footer">
            <p>🤖 Generated with Claude Code Quality Dashboard v1.0.0</p>
            <p>Kumihan-Formatter Enterprise Quality Report</p>
        </div>
    </div>
</body>
</html>
        """

    def _generate_concerns_section(self, concerns: List[str]) -> str:
        """懸念事項セクション生成"""
        if not concerns:
            return """
            <div class="section">
                <h2>✅ 品質状況</h2>
                <div class="suggestions">
                    <p><strong>🎉 素晴らしい!</strong> 重要な品質問題は検出されませんでした。</p>
                </div>
            </div>
            """

        concerns_list = "\n".join([f"<li>{concern}</li>" for concern in concerns])
        return f"""
        <div class="section">
            <h2>⚠️ 懸念事項</h2>
            <div class="concerns">
                <p><strong>以下の問題に注意が必要です:</strong></p>
                <ul>
                    {concerns_list}
                </ul>
            </div>
        </div>
        """

    def _generate_suggestions_section(self, suggestions: List[Dict[str, str]]) -> str:
        """改善提案セクション生成"""
        if not suggestions:
            return """
            <div class="section">
                <h2>🎯 改善提案</h2>
                <div class="suggestions">
                    <p>現在、特別な改善提案はありません。品質を維持し続けてください！</p>
                </div>
            </div>
            """

        suggestions_html = ""
        for suggestion in suggestions:
            priority_color = (
                "#e74c3c"
                if suggestion["priority"] == "高"
                else "#f39c12" if suggestion["priority"] == "中" else "#27ae60"
            )
            suggestions_html += f"""
            <div style="margin-bottom: 15px; padding: 15px; border-left: 4px solid {priority_color}; background: #f8f9fa;">
                <h4 style="color: {priority_color};">【{suggestion['category']}】 優先度: {suggestion['priority']}</h4>
                <p><strong>提案:</strong> {suggestion['suggestion']}</p>
                <p><strong>期待効果:</strong> {suggestion['impact']}</p>
            </div>
            """

        return f"""
        <div class="section">
            <h2>💡 改善提案</h2>
            <div class="suggestions">
                {suggestions_html}
            </div>
        </div>
        """


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality report generator")
    parser.add_argument(
        "--format", choices=["html", "json"], default="html", help="Report format"
    )
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    generator = ReportGenerator()
    report_path = generator.generate_comprehensive_report(format=args.format)

    print(f"Quality report generated: {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
