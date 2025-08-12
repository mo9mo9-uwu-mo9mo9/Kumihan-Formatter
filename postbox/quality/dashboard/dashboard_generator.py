#!/usr/bin/env python3
"""
Quality Dashboard Generator
品質ダッシュボード生成システム - HTMLダッシュボード・可視化・リアルタイム表示
メトリクス統合・トレンド可視化・アラート表示・インタラクティブUI
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class QualityDashboardGenerator:
    """品質ダッシュボード生成システム"""
    
    def __init__(self):
        self.dashboard_dir = Path("postbox/quality/dashboard")
        self.templates_dir = self.dashboard_dir / "templates"
        self.output_dir = Path("tmp/quality_dashboard")
        
        # ディレクトリ作成
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_path = self.dashboard_dir / "collected_metrics.json"
        
        print("📊 QualityDashboardGenerator 初期化完了")
    
    def generate_dashboard(self, output_format: str = "html") -> str:
        """ダッシュボード生成"""
        
        print(f"📊 品質ダッシュボード生成開始 ({output_format})...")
        
        # メトリクスデータ読み込み
        metrics_data = self._load_metrics_data()
        
        if not metrics_data:
            print("⚠️ メトリクスデータが見つかりません")
            return self._generate_no_data_dashboard()
        
        if output_format == "html":
            return self._generate_html_dashboard(metrics_data)
        elif output_format == "json":
            return self._generate_json_dashboard(metrics_data)
        else:
            raise ValueError(f"サポートされていない出力形式: {output_format}")
    
    def _load_metrics_data(self) -> Optional[Dict[str, Any]]:
        """メトリクスデータ読み込み"""
        
        try:
            if self.metrics_path.exists():
                with open(self.metrics_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️ メトリクスファイルが見つかりません: {self.metrics_path}")
                return None
        except Exception as e:
            print(f"❌ メトリクスデータ読み込みエラー: {e}")
            return None
    
    def _generate_html_dashboard(self, metrics_data: Dict[str, Any]) -> str:
        """HTMLダッシュボード生成"""
        
        dashboard_html = self._create_html_template()
        
        # データ挿入
        dashboard_html = dashboard_html.replace("{{METRICS_DATA}}", json.dumps(metrics_data, ensure_ascii=False, indent=2))
        dashboard_html = dashboard_html.replace("{{GENERATION_TIME}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 各セクションの生成
        dashboard_html = dashboard_html.replace("{{QUALITY_SCORES_SECTION}}", self._generate_quality_scores_section(metrics_data))
        dashboard_html = dashboard_html.replace("{{TREND_ANALYSIS_SECTION}}", self._generate_trend_analysis_section(metrics_data))
        dashboard_html = dashboard_html.replace("{{SYSTEM_PERFORMANCE_SECTION}}", self._generate_system_performance_section(metrics_data))
        dashboard_html = dashboard_html.replace("{{LEARNING_METRICS_SECTION}}", self._generate_learning_metrics_section(metrics_data))
        dashboard_html = dashboard_html.replace("{{GATE_STATISTICS_SECTION}}", self._generate_gate_statistics_section(metrics_data))
        dashboard_html = dashboard_html.replace("{{ALERT_SUMMARY_SECTION}}", self._generate_alert_summary_section(metrics_data))
        
        # ファイル保存
        output_path = self.output_dir / "quality_dashboard.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        print(f"✅ HTMLダッシュボード生成完了: {output_path}")
        
        return str(output_path)
    
    def _create_html_template(self) -> str:
        """HTMLテンプレート作成"""
        
        return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan-Formatter 品質ダッシュボード</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
        }
        
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .metric-label {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .metric-value {
            color: #27ae60;
            font-weight: bold;
        }
        
        .metric-value.warning {
            color: #f39c12;
        }
        
        .metric-value.error {
            color: #e74c3c;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-excellent {
            background: #d4edda;
            color: #155724;
        }
        
        .status-good {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .status-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .alert-item {
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #3498db;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .alert-critical {
            border-left-color: #e74c3c;
            background: #fdf2f2;
        }
        
        .alert-warning {
            border-left-color: #f39c12;
            background: #fffbf2;
        }
        
        .timestamp {
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            margin-top: 20px;
        }
        
        .chart-container {
            height: 200px;
            background: #f8f9fa;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 10px 0;
            color: #7f8c8d;
        }
        
        .no-data {
            text-align: center;
            color: #95a5a6;
            font-style: italic;
            padding: 20px;
        }
        
        .recommendation {
            background: #e8f5e8;
            border: 1px solid #27ae60;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
        }
        
        .recommendation::before {
            content: "💡 ";
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 Kumihan-Formatter 品質ダッシュボード</h1>
            <div class="subtitle">リアルタイム品質監視・分析・予測システム</div>
        </header>
        
        <div class="dashboard-grid">
            {{QUALITY_SCORES_SECTION}}
            {{TREND_ANALYSIS_SECTION}}
            {{SYSTEM_PERFORMANCE_SECTION}}
            {{LEARNING_METRICS_SECTION}}
            {{GATE_STATISTICS_SECTION}}
            {{ALERT_SUMMARY_SECTION}}
        </div>
        
        <div class="timestamp">
            最終更新: {{GENERATION_TIME}}
        </div>
    </div>
    
    <script>
        // メトリクスデータ
        const metricsData = {{METRICS_DATA}};
        
        // ページ読み込み時の処理
        document.addEventListener('DOMContentLoaded', function() {
            console.log('品質ダッシュボード読み込み完了');
            console.log('メトリクスデータ:', metricsData);
            
            // 自動更新（5分間隔）
            setInterval(function() {
                location.reload();
            }, 300000);
        });
        
        // ツールチップ機能
        function showTooltip(element, text) {
            // 簡易ツールチップ実装
            element.title = text;
        }
        
        // メトリクス値のフォーマット
        function formatMetricValue(value, type = 'number') {
            if (type === 'percentage') {
                return (value * 100).toFixed(1) + '%';
            } else if (type === 'score') {
                return value.toFixed(3);
            } else {
                return value.toString();
            }
        }
        
        // ステータス判定
        function getStatusClass(value, thresholds = {good: 0.8, warning: 0.6}) {
            if (value >= thresholds.good) return 'status-excellent';
            if (value >= thresholds.warning) return 'status-warning';
            return 'status-error';
        }
    </script>
</body>
</html>'''
    
    def _generate_quality_scores_section(self, metrics_data: Dict[str, Any]) -> str:
        """品質スコアセクション生成"""
        
        quality_scores = metrics_data.get("quality_scores")
        if not quality_scores:
            return '<div class="card"><h2>📊 品質スコア</h2><div class="no-data">データなし</div></div>'
        
        metrics = quality_scores.get("metrics", {})
        summary = quality_scores.get("summary", {})
        
        html = '''
        <div class="card">
            <h2>📊 品質スコア</h2>
        '''
        
        # 総合品質スコア
        if "comprehensive_score" in metrics:
            score = metrics["comprehensive_score"]
            status_class = self._get_status_class(score)
            html += f'''
            <div class="metric-item">
                <span class="metric-label">総合品質スコア</span>
                <span class="metric-value">
                    <span class="status-badge {status_class}">{score:.3f}</span>
                </span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {score * 100}%"></div>
            </div>
            '''
        
        # カテゴリ別スコア
        if "category_scores" in metrics:
            html += '<h3>カテゴリ別スコア</h3>'
            for category, score in metrics["category_scores"].items():
                html += f'''
                <div class="metric-item">
                    <span class="metric-label">{category}</span>
                    <span class="metric-value">{score:.3f}</span>
                </div>
                '''
        
        # 平均スコア
        if "average_scores" in metrics:
            html += '<h3>平均スコア</h3>'
            for check_type, score in metrics["average_scores"].items():
                html += f'''
                <div class="metric-item">
                    <span class="metric-label">{check_type}</span>
                    <span class="metric-value">{score:.3f}</span>
                </div>
                '''
        
        # リアルタイム情報
        if "realtime_average" in metrics:
            html += f'''
            <div class="metric-item">
                <span class="metric-label">リアルタイム平均</span>
                <span class="metric-value">{metrics["realtime_average"]:.3f}</span>
            </div>
            '''
        
        # ステータス
        quality_status = summary.get("quality_status", "unknown")
        status_class = self._get_status_class_by_name(quality_status)
        html += f'''
        <div class="metric-item">
            <span class="metric-label">品質ステータス</span>
            <span class="status-badge {status_class}">{quality_status}</span>
        </div>
        '''
        
        html += '</div>'
        
        return html
    
    def _generate_trend_analysis_section(self, metrics_data: Dict[str, Any]) -> str:
        """トレンド分析セクション生成"""
        
        trend_analysis = metrics_data.get("trend_analysis")
        if not trend_analysis:
            return '<div class="card"><h2>📈 トレンド分析</h2><div class="no-data">データなし</div></div>'
        
        metrics = trend_analysis.get("metrics", {})
        summary = trend_analysis.get("summary", {})
        
        html = '''
        <div class="card">
            <h2>📈 トレンド分析</h2>
        '''
        
        # 全体トレンド
        overall_trend = summary.get("overall_trend", "unknown")
        html += f'''
        <div class="metric-item">
            <span class="metric-label">全体トレンド</span>
            <span class="metric-value">{self._format_trend(overall_trend)}</span>
        </div>
        '''
        
        # パフォーマンストレンド
        if "performance_trends" in metrics:
            perf_trends = metrics["performance_trends"]
            html += '<h3>パフォーマンストレンド</h3>'
            for key, value in perf_trends.items():
                html += f'''
                <div class="metric-item">
                    <span class="metric-label">{key}</span>
                    <span class="metric-value">{value}</span>
                </div>
                '''
        
        # 学習進化
        if "learning_evolution" in metrics:
            evolution = metrics["learning_evolution"]
            html += '<h3>学習システム進化</h3>'
            html += f'''
            <div class="metric-item">
                <span class="metric-label">進化回数</span>
                <span class="metric-value">{evolution.get("evolution_count", 0)}</span>
            </div>
            '''
        
        # 予測精度
        prediction_accuracy = summary.get("prediction_accuracy", 0)
        html += f'''
        <div class="metric-item">
            <span class="metric-label">予測精度</span>
            <span class="metric-value">{prediction_accuracy:.1%}</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {prediction_accuracy * 100}%"></div>
        </div>
        '''
        
        html += '</div>'
        
        return html
    
    def _generate_system_performance_section(self, metrics_data: Dict[str, Any]) -> str:
        """システムパフォーマンスセクション生成"""
        
        system_performance = metrics_data.get("system_performance")
        if not system_performance:
            return '<div class="card"><h2>⚡ システムパフォーマンス</h2><div class="no-data">データなし</div></div>'
        
        metrics = system_performance.get("metrics", {})
        summary = system_performance.get("summary", {})
        
        html = '''
        <div class="card">
            <h2>⚡ システムパフォーマンス</h2>
        '''
        
        # システム健全性
        system_health = summary.get("overall_health", "unknown")
        health_class = self._get_status_class_by_name(system_health)
        html += f'''
        <div class="metric-item">
            <span class="metric-label">システム健全性</span>
            <span class="status-badge {health_class}">{system_health}</span>
        </div>
        '''
        
        # リアルタイムパフォーマンス
        if "realtime_performance" in metrics:
            rt_perf = metrics["realtime_performance"]
            html += '<h3>リアルタイム監視</h3>'
            
            for key, value in rt_perf.items():
                if isinstance(value, (int, float)):
                    if "time" in key.lower():
                        formatted_value = f"{value:.3f}秒"
                    else:
                        formatted_value = str(value)
                    
                    html += f'''
                    <div class="metric-item">
                        <span class="metric-label">{key}</span>
                        <span class="metric-value">{formatted_value}</span>
                    </div>
                    '''
        
        # ゲートパフォーマンス
        if "gate_performance" in metrics:
            gate_perf = metrics["gate_performance"]
            html += '<h3>品質ゲート</h3>'
            
            for key, value in gate_perf.items():
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.3f}秒" if "time" in key else str(value)
                    html += f'''
                    <div class="metric-item">
                        <span class="metric-label">{key}</span>
                        <span class="metric-value">{formatted_value}</span>
                    </div>
                    '''
        
        # 検証パフォーマンス
        if "validation_performance" in metrics:
            val_perf = metrics["validation_performance"]
            html += '<h3>包括的検証</h3>'
            
            for key, value in val_perf.items():
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.3f}秒" if "time" in key else f"{value:.2f}" if "throughput" in key else str(value)
                    html += f'''
                    <div class="metric-item">
                        <span class="metric-label">{key}</span>
                        <span class="metric-value">{formatted_value}</span>
                    </div>
                    '''
        
        html += '</div>'
        
        return html
    
    def _generate_learning_metrics_section(self, metrics_data: Dict[str, Any]) -> str:
        """学習メトリクスセクション生成"""
        
        learning_metrics = metrics_data.get("learning_metrics")
        if not learning_metrics:
            return '<div class="card"><h2>🧠 学習システム</h2><div class="no-data">データなし</div></div>'
        
        metrics = learning_metrics.get("metrics", {})
        summary = learning_metrics.get("summary", {})
        
        html = '''
        <div class="card">
            <h2>🧠 学習システム</h2>
        '''
        
        # 学習状態
        learning_active = summary.get("learning_active", False)
        learning_quality = summary.get("learning_quality", "unknown")
        
        html += f'''
        <div class="metric-item">
            <span class="metric-label">学習状態</span>
            <span class="status-badge {'status-good' if learning_active else 'status-warning'}">
                {'アクティブ' if learning_active else '非アクティブ'}
            </span>
        </div>
        <div class="metric-item">
            <span class="metric-label">学習品質</span>
            <span class="status-badge {self._get_status_class_by_name(learning_quality)}">{learning_quality}</span>
        </div>
        '''
        
        # 学習効果
        if "learning_effectiveness" in metrics:
            effectiveness = metrics["learning_effectiveness"]
            html += '<h3>学習効果</h3>'
            
            success_rate = effectiveness.get("success_rate", 0)
            html += f'''
            <div class="metric-item">
                <span class="metric-label">成功率</span>
                <span class="metric-value">{success_rate:.1%}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate * 100}%"></div>
            </div>
            '''
            
            for key, value in effectiveness.items():
                if key != "success_rate" and isinstance(value, (int, float)):
                    if "improvement" in key:
                        formatted_value = f"+{value:.3f}" if value > 0 else f"{value:.3f}"
                    else:
                        formatted_value = str(value)
                    
                    html += f'''
                    <div class="metric-item">
                        <span class="metric-label">{key}</span>
                        <span class="metric-value">{formatted_value}</span>
                    </div>
                    '''
        
        # 予測品質
        if "prediction_quality" in metrics:
            pred_quality = metrics["prediction_quality"]
            html += '<h3>予測品質</h3>'
            
            for key, value in pred_quality.items():
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.1%}" if "rate" in key else f"{value:.3f}"
                    html += f'''
                    <div class="metric-item">
                        <span class="metric-label">{key}</span>
                        <span class="metric-value">{formatted_value}</span>
                    </div>
                    '''
        
        # 改善可能性
        improvement_potential = summary.get("improvement_potential", "unknown")
        html += f'''
        <div class="metric-item">
            <span class="metric-label">改善可能性</span>
            <span class="status-badge {self._get_status_class_by_name(improvement_potential)}">{improvement_potential}</span>
        </div>
        '''
        
        html += '</div>'
        
        return html
    
    def _generate_gate_statistics_section(self, metrics_data: Dict[str, Any]) -> str:
        """ゲート統計セクション生成"""
        
        gate_statistics = metrics_data.get("gate_statistics")
        if not gate_statistics:
            return '<div class="card"><h2>🚪 品質ゲート</h2><div class="no-data">データなし</div></div>'
        
        metrics = gate_statistics.get("metrics", {})
        summary = gate_statistics.get("summary", {})
        
        html = '''
        <div class="card">
            <h2>🚪 品質ゲート</h2>
        '''
        
        # ゲート健全性
        gate_health = summary.get("overall_gate_health", "unknown")
        health_class = self._get_status_class_by_name(gate_health)
        html += f'''
        <div class="metric-item">
            <span class="metric-label">ゲート健全性</span>
            <span class="status-badge {health_class}">{gate_health}</span>
        </div>
        '''
        
        # ゲート統計
        if "gate_statistics" in metrics:
            gate_stats = metrics["gate_statistics"]
            html += '<h3>実行統計</h3>'
            
            for key, value in gate_stats.items():
                if isinstance(value, (int, float)):
                    if "rate" in key:
                        formatted_value = f"{value:.1%}"
                        value_class = "metric-value" if value >= 0.8 else "metric-value warning" if value >= 0.6 else "metric-value error"
                    elif "score" in key:
                        formatted_value = f"{value:.3f}"
                        value_class = "metric-value"
                    else:
                        formatted_value = str(int(value))
                        value_class = "metric-value"
                    
                    html += f'''
                    <div class="metric-item">
                        <span class="metric-label">{key}</span>
                        <span class="{value_class}">{formatted_value}</span>
                    </div>
                    '''
                    
                    if "rate" in key:
                        html += f'''
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {value * 100}%"></div>
                        </div>
                        '''
        
        # フェーズ別統計
        if "phase_statistics" in metrics:
            phase_stats = metrics["phase_statistics"]
            html += '<h3>フェーズ別統計</h3>'
            
            for phase, stats in phase_stats.items():
                pass_rate = stats.get("pass_rate", 0)
                executions = stats.get("executions", 0)
                
                html += f'''
                <div class="metric-item">
                    <span class="metric-label">{phase}</span>
                    <span class="metric-value">{pass_rate:.1%} ({executions}回)</span>
                </div>
                '''
        
        # 推奨事項
        recommendations = summary.get("recommendations", [])
        if recommendations:
            html += '<h3>推奨事項</h3>'
            for rec in recommendations:
                html += f'<div class="recommendation">{rec}</div>'
        
        html += '</div>'
        
        return html
    
    def _generate_alert_summary_section(self, metrics_data: Dict[str, Any]) -> str:
        """アラートサマリーセクション生成"""
        
        alert_summary = metrics_data.get("alert_summary")
        if not alert_summary:
            return '<div class="card"><h2>🚨 アラート</h2><div class="no-data">データなし</div></div>'
        
        metrics = alert_summary.get("metrics", {})
        summary = alert_summary.get("summary", {})
        
        html = '''
        <div class="card">
            <h2>🚨 アラート</h2>
        '''
        
        # システムステータス
        system_status = summary.get("system_status", "unknown")
        status_class = self._get_status_class_by_name(system_status)
        html += f'''
        <div class="metric-item">
            <span class="metric-label">システムステータス</span>
            <span class="status-badge {status_class}">{system_status}</span>
        </div>
        '''
        
        # アラート統計
        if "alert_statistics" in metrics:
            alert_stats = metrics["alert_statistics"]
            html += '<h3>アラート統計</h3>'
            
            total_alerts = alert_stats.get("total_alerts", 0)
            html += f'''
            <div class="metric-item">
                <span class="metric-label">総アラート数</span>
                <span class="metric-value">{total_alerts}</span>
            </div>
            '''
            
            # レベル別アラート
            by_level = alert_stats.get("by_level", {})
            if by_level:
                html += '<h4>レベル別</h4>'
                for level, count in by_level.items():
                    alert_class = f"alert-{level}" if level in ["critical", "warning"] else "alert-item"
                    html += f'''
                    <div class="{alert_class}">
                        <span class="metric-label">{level}</span>: {count}件
                    </div>
                    '''
            
            # 解決が必要なアラート
            resolution_needed = alert_stats.get("resolution_needed", 0)
            if resolution_needed > 0:
                html += f'''
                <div class="alert-critical">
                    ⚠️ 解決が必要なアラート: {resolution_needed}件
                </div>
                '''
        
        # システム健全性
        if "system_health" in metrics:
            health = metrics["system_health"]
            html += '<h3>システム健全性</h3>'
            
            monitoring_active = health.get("monitoring_active", False)
            html += f'''
            <div class="metric-item">
                <span class="metric-label">監視状態</span>
                <span class="status-badge {'status-good' if monitoring_active else 'status-error'}">
                    {'稼働中' if monitoring_active else '停止中'}
                </span>
            </div>
            '''
            
            if health.get("last_alert_time"):
                html += f'''
                <div class="metric-item">
                    <span class="metric-label">最終アラート</span>
                    <span class="metric-value">{health["last_alert_time"][:19]}</span>
                </div>
                '''
        
        html += '</div>'
        
        return html
    
    def _generate_json_dashboard(self, metrics_data: Dict[str, Any]) -> str:
        """JSONダッシュボード生成"""
        
        dashboard_data = {
            "dashboard_metadata": {
                "generated_at": datetime.datetime.now().isoformat(),
                "version": "1.0.0",
                "type": "quality_dashboard"
            },
            "metrics": metrics_data,
            "summary": self._generate_overall_summary(metrics_data)
        }
        
        output_path = self.output_dir / "quality_dashboard.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSONダッシュボード生成完了: {output_path}")
        
        return str(output_path)
    
    def _generate_overall_summary(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """全体サマリー生成"""
        
        summary = {
            "total_categories": len(metrics_data),
            "data_completeness": self._calculate_data_completeness(metrics_data),
            "overall_health": self._determine_overall_health(metrics_data),
            "key_insights": self._generate_key_insights(metrics_data)
        }
        
        return summary
    
    def _calculate_data_completeness(self, metrics_data: Dict[str, Any]) -> float:
        """データ完全性計算"""
        
        expected_categories = 6  # 期待されるカテゴリ数
        actual_categories = len(metrics_data)
        
        return min(1.0, actual_categories / expected_categories)
    
    def _determine_overall_health(self, metrics_data: Dict[str, Any]) -> str:
        """全体健全性判定"""
        
        health_scores = []
        
        # 品質スコア健全性
        quality_scores = metrics_data.get("quality_scores")
        if quality_scores:
            comprehensive_score = quality_scores.get("metrics", {}).get("comprehensive_score", 0)
            health_scores.append(comprehensive_score)
        
        # システムパフォーマンス健全性
        system_performance = metrics_data.get("system_performance")
        if system_performance:
            health = system_performance.get("summary", {}).get("overall_health", "unknown")
            if health == "healthy":
                health_scores.append(1.0)
            elif health == "degraded":
                health_scores.append(0.5)
            else:
                health_scores.append(0.0)
        
        if health_scores:
            avg_health = sum(health_scores) / len(health_scores)
            if avg_health >= 0.9:
                return "excellent"
            elif avg_health >= 0.8:
                return "good"
            elif avg_health >= 0.6:
                return "acceptable"
            else:
                return "needs_attention"
        
        return "unknown"
    
    def _generate_key_insights(self, metrics_data: Dict[str, Any]) -> List[str]:
        """主要洞察生成"""
        
        insights = []
        
        # 品質スコア洞察
        quality_scores = metrics_data.get("quality_scores")
        if quality_scores:
            score = quality_scores.get("metrics", {}).get("comprehensive_score", 0)
            if score >= 0.9:
                insights.append("優秀な品質レベルを維持しています")
            elif score < 0.7:
                insights.append("品質改善が急務です")
        
        # 学習システム洞察
        learning_metrics = metrics_data.get("learning_metrics")
        if learning_metrics:
            if learning_metrics.get("summary", {}).get("learning_active", False):
                insights.append("学習システムが活発に稼働しています")
        
        # アラート洞察
        alert_summary = metrics_data.get("alert_summary")
        if alert_summary:
            alert_stats = alert_summary.get("metrics", {}).get("alert_statistics", {})
            critical_rate = alert_stats.get("critical_rate", 0)
            if critical_rate > 0.1:
                insights.append("重要なアラートが多発しています")
        
        return insights
    
    def _generate_no_data_dashboard(self) -> str:
        """データなしダッシュボード生成"""
        
        html = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>品質ダッシュボード - データなし</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .no-data-message { color: #666; font-size: 1.2em; }
    </style>
</head>
<body>
    <h1>🔍 品質ダッシュボード</h1>
    <div class="no-data-message">
        <p>メトリクスデータが見つかりませんでした。</p>
        <p>品質システムを実行してデータを収集してください。</p>
    </div>
</body>
</html>'''
        
        output_path = self.output_dir / "quality_dashboard_no_data.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(output_path)
    
    # ユーティリティメソッド
    def _get_status_class(self, value: float) -> str:
        """ステータスクラス取得"""
        if value >= 0.9:
            return "status-excellent"
        elif value >= 0.8:
            return "status-good"
        elif value >= 0.6:
            return "status-warning"
        else:
            return "status-error"
    
    def _get_status_class_by_name(self, status: str) -> str:
        """名前によるステータスクラス取得"""
        status_mapping = {
            "excellent": "status-excellent",
            "good": "status-good",
            "healthy": "status-good",
            "acceptable": "status-warning",
            "warning": "status-warning",
            "moderate": "status-warning",
            "needs_improvement": "status-error",
            "needs_attention": "status-error",
            "error": "status-error",
            "critical": "status-error",
            "unknown": "status-warning"
        }
        return status_mapping.get(status.lower(), "status-warning")
    
    def _format_trend(self, trend: str) -> str:
        """トレンド表示フォーマット"""
        trend_mapping = {
            "improving": "📈 改善中",
            "declining": "📉 低下中",
            "stable": "📊 安定",
            "unknown": "❓ 不明"
        }
        return trend_mapping.get(trend, trend)

def main():
    """テスト実行"""
    print("🧪 QualityDashboardGenerator テスト開始")
    
    generator = QualityDashboardGenerator()
    
    # HTMLダッシュボード生成テスト
    print("\n=== HTMLダッシュボード生成 ===")
    html_path = generator.generate_dashboard("html")
    print(f"生成されたHTML: {html_path}")
    
    # JSONダッシュボード生成テスト
    print("\n=== JSONダッシュボード生成 ===")
    json_path = generator.generate_dashboard("json")
    print(f"生成されたJSON: {json_path}")
    
    print("✅ QualityDashboardGenerator テスト完了")

if __name__ == "__main__":
    main()