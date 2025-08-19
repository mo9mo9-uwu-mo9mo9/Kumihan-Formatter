"""
品質ダッシュボード Web UI

Flask ベースのリアルタイム品質監視
ダッシュボードシステム
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template_string, request

from kumihan_formatter.core.utilities.logger import get_logger

from .metrics_collector import MetricsCollector
from .report_generator import ReportGenerator

logger = get_logger(__name__)


class QualityDashboard:
    """品質ダッシュボード管理"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.app = Flask(__name__)
        self.metrics_collector = MetricsCollector(project_root)
        self.report_generator = ReportGenerator(project_root)
        self._setup_routes()

    def _setup_routes(self) -> None:
        """ルート設定"""

        @self.app.route("/")
        def dashboard_home():
            """ダッシュボードホーム"""
            return render_template_string(self._get_dashboard_template())

        @self.app.route("/api/metrics/current")
        def get_current_metrics():
            """現在の品質メトリクス取得"""
            metrics = self.metrics_collector.collect_comprehensive_metrics()
            return jsonify(metrics)

        @self.app.route("/api/metrics/history")
        def get_metrics_history():
            """メトリクス履歴取得"""
            days = request.args.get("days", 7, type=int)
            history = self.metrics_collector.get_metrics_history(days)
            return jsonify(history)

        @self.app.route("/api/coverage/details")
        def get_coverage_details():
            """カバレッジ詳細取得"""
            coverage_metrics = self.metrics_collector.collect_coverage_metrics()
            return jsonify(coverage_metrics)

        @self.app.route("/api/performance/details")
        def get_performance_details():
            """パフォーマンス詳細取得"""
            performance_metrics = self.metrics_collector.collect_performance_metrics()
            return jsonify(performance_metrics)

        @self.app.route("/api/quality-gate/status")
        def get_quality_gate_status():
            """品質ゲートステータス取得"""
            metrics = self.metrics_collector.collect_comprehensive_metrics()
            quality_score = metrics.get("quality_score", {})

            # 品質ゲート判定
            score = quality_score.get("score", 0)
            if score >= 90:
                status = "EXCELLENT"
                color = "#10B981"  # green
            elif score >= 75:
                status = "GOOD"
                color = "#3B82F6"  # blue
            elif score >= 60:
                status = "WARNING"
                color = "#F59E0B"  # yellow
            else:
                status = "CRITICAL"
                color = "#EF4444"  # red

            return jsonify(
                {
                    "status": status,
                    "score": score,
                    "grade": quality_score.get("grade", "N/A"),
                    "color": color,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.route("/api/reports/generate")
        def generate_report():
            """品質レポート生成"""
            report_type = request.args.get("type", "html")
            report_path = self.report_generator.generate_comprehensive_report(
                format=report_type
            )
            return jsonify(
                {
                    "status": "success",
                    "report_path": str(report_path),
                    "download_url": f"/api/reports/download?path={report_path.name}",
                }
            )

        @self.app.route("/api/trends/quality-score")
        def get_quality_score_trend():
            """品質スコア推移取得"""
            days = request.args.get("days", 7, type=int)
            history = self.metrics_collector.get_metrics_history(days)

            trend_data = []
            for entry in history:
                quality_score = entry.get("quality_score", {})
                trend_data.append(
                    {
                        "timestamp": entry.get("collection_timestamp"),
                        "score": quality_score.get("score", 0),
                        "grade": quality_score.get("grade", "N/A"),
                    }
                )

            return jsonify(trend_data)

        @self.app.route("/health")
        def health_check():
            """ヘルスチェック"""
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0",
                }
            )

    def _get_dashboard_template(self) -> str:
        """ダッシュボードHTMLテンプレート"""
        return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan-Formatter 品質ダッシュボード</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Arial', sans-serif; background: #f8fafc; color: #1a202c; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2d3748; color: white; padding: 20px; margin-bottom: 30px; border-radius: 8px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .header p { opacity: 0.8; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 15px; color: #2d3748; }
        .metric-value { font-size: 2rem; font-weight: bold; margin-bottom: 10px; }
        .metric-status { padding: 4px 12px; border-radius: 20px; font-size: 0.9rem; font-weight: bold; }
        .status-pass { background: #10B981; color: white; }
        .status-warning { background: #F59E0B; color: white; }
        .status-fail { background: #EF4444; color: white; }
        .charts-section { margin-top: 30px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .loading { text-align: center; padding: 40px; color: #64748b; }
        .refresh-btn { background: #3B82F6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-left: 10px; }
        .refresh-btn:hover { background: #2563EB; }
        .last-updated { font-size: 0.9rem; color: #64748b; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Kumihan-Formatter 品質ダッシュボード</h1>
            <p>Enterprise級品質監視・分析システム - Phase 4-3</p>
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 更新</button>
        </div>

        <div id="qualityGate" class="metric-card" style="margin-bottom: 20px;">
            <div class="metric-title">🎯 品質ゲートステータス</div>
            <div class="loading">読み込み中...</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">📊 テストカバレッジ</div>
                <div id="coverageMetric" class="loading">読み込み中...</div>
            </div>

            <div class="metric-card">
                <div class="metric-title">🔍 複雑度</div>
                <div id="complexityMetric" class="loading">読み込み中...</div>
            </div>

            <div class="metric-card">
                <div class="metric-title">⚡ パフォーマンス</div>
                <div id="performanceMetric" class="loading">読み込み中...</div>
            </div>

            <div class="metric-card">
                <div class="metric-title">✨ コード品質</div>
                <div id="lintMetric" class="loading">読み込み中...</div>
            </div>
        </div>

        <div class="charts-section">
            <div class="chart-container">
                <h3>📈 品質スコア推移 (過去7日間)</h3>
                <canvas id="qualityTrendChart" width="400" height="200"></canvas>
            </div>

            <div class="chart-container">
                <h3>📊 カバレッジ推移</h3>
                <canvas id="coverageTrendChart" width="400" height="200"></canvas>
            </div>
        </div>

        <div id="lastUpdated" class="last-updated"></div>
    </div>

    <script>
        let qualityTrendChart;
        let coverageTrendChart;

        async function loadDashboardData() {
            try {
                // 品質ゲートステータス
                const gateResponse = await fetch('/api/quality-gate/status');
                const gateData = await gateResponse.json();
                updateQualityGate(gateData);

                // 現在のメトリクス
                const metricsResponse = await fetch('/api/metrics/current');
                const metricsData = await metricsResponse.json();
                updateMetrics(metricsData);

                // 品質トレンド
                const trendResponse = await fetch('/api/trends/quality-score?days=7');
                const trendData = await trendResponse.json();
                updateQualityTrendChart(trendData);

                // カバレッジ履歴
                const historyResponse = await fetch('/api/metrics/history?days=7');
                const historyData = await historyResponse.json();
                updateCoverageTrendChart(historyData);

                document.getElementById('lastUpdated').textContent =
                    `最終更新: ${new Date().toLocaleString('ja-JP')}`;

            } catch (error) {
                console.error('データ読み込みエラー:', error);
            }
        }

        function updateQualityGate(data) {
            const element = document.getElementById('qualityGate');
            element.innerHTML = `
                <div class="metric-title">🎯 品質ゲートステータス</div>
                <div class="metric-value" style="color: ${data.color};">${data.score}/100</div>
                <div class="metric-status status-${data.status.toLowerCase()}">${data.status} (${data.grade})</div>
            `;
        }

        function updateMetrics(data) {
            // カバレッジ
            const coverage = data.coverage || {};
            document.getElementById('coverageMetric').innerHTML = `
                <div class="metric-value">${(coverage.total_coverage || 0).toFixed(1)}%</div>
                <div class="metric-status status-${coverage.status?.toLowerCase() || 'unknown'}">${coverage.status || 'UNKNOWN'}</div>
                <div style="font-size: 0.9rem; margin-top: 10px;">
                    ${coverage.lines_covered || 0} / ${coverage.lines_total || 0} 行
                </div>
            `;

            // 複雑度
            const complexity = data.complexity || {};
            document.getElementById('complexityMetric').innerHTML = `
                <div class="metric-value">${(complexity.average_complexity || 0).toFixed(1)}</div>
                <div class="metric-status status-${complexity.status?.toLowerCase() || 'unknown'}">${complexity.status || 'UNKNOWN'}</div>
                <div style="font-size: 0.9rem; margin-top: 10px;">
                    高複雑度: ${complexity.high_complexity_count || 0} 関数
                </div>
            `;

            // パフォーマンス
            const performance = data.performance || {};
            document.getElementById('performanceMetric').innerHTML = `
                <div class="metric-value">${(performance.startup_time_ms || 0).toFixed(0)}ms</div>
                <div class="metric-status status-${performance.overall_status?.toLowerCase() || 'unknown'}">${performance.overall_status || 'UNKNOWN'}</div>
                <div style="font-size: 0.9rem; margin-top: 10px;">
                    メモリ: ${(performance.memory_usage_mb || 0).toFixed(1)}MB
                </div>
            `;

            // Lint
            const lint = data.lint || {};
            document.getElementById('lintMetric').innerHTML = `
                <div class="metric-value">${lint.total_issues || 0}</div>
                <div class="metric-status status-${lint.status?.toLowerCase() || 'unknown'}">${lint.status || 'UNKNOWN'}</div>
                <div style="font-size: 0.9rem; margin-top: 10px;">
                    エラー: ${lint.error_count || 0} / 警告: ${lint.warning_count || 0}
                </div>
            `;
        }

        function updateQualityTrendChart(data) {
            const ctx = document.getElementById('qualityTrendChart').getContext('2d');

            if (qualityTrendChart) {
                qualityTrendChart.destroy();
            }

            const labels = data.map(d => new Date(d.timestamp).toLocaleDateString('ja-JP'));
            const scores = data.map(d => d.score);

            qualityTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '品質スコア',
                        data: scores,
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });
        }

        function updateCoverageTrendChart(data) {
            const ctx = document.getElementById('coverageTrendChart').getContext('2d');

            if (coverageTrendChart) {
                coverageTrendChart.destroy();
            }

            const labels = data.map(d => new Date(d.collection_timestamp).toLocaleDateString('ja-JP'));
            const coverage = data.map(d => d.coverage?.total_coverage || 0);

            coverageTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'カバレッジ (%)',
                        data: coverage,
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });
        }

        function refreshDashboard() {
            loadDashboardData();
        }

        // 初期読み込み
        loadDashboardData();

        // 30秒毎に自動更新
        setInterval(loadDashboardData, 30000);
    </script>
</body>
</html>
        """

    def run(
        self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False
    ) -> None:
        """ダッシュボード起動"""
        logger.info(f"Starting quality dashboard at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

    def get_app(self) -> Flask:
        """Flaskアプリケーション取得"""
        return self.app


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    args = parser.parse_args()

    dashboard = QualityDashboard()
    dashboard.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
