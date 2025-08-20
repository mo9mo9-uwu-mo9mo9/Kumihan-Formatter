#!/usr/bin/env python3
"""
CI/CDメトリクスダッシュボード生成 - Issue #971対応

HTMLダッシュボード形式でCI/CDメトリクスを可視化します。
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class CIMetricsDashboard:
    """CI/CDメトリクスダッシュボード生成クラス"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.dashboard_data = {}

    def run_gh_command(self, args: List[str]) -> Dict[str, Any]:
        """GitHub CLIコマンドを実行"""
        try:
            result = subprocess.run(
                ["gh"] + args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                return {"success": True, "data": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr or "No output"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def collect_workflow_metrics(self) -> Dict[str, Any]:
        """ワークフローメトリクス収集"""
        print("📊 ワークフローメトリクスを収集中...")

        # 最近30件の実行履歴を取得
        result = self.run_gh_command([
            "run", "list",
            "--limit", "30",
            "--json", "status,conclusion,workflowName,createdAt,updatedAt,url,event,headBranch"
        ])

        if not result["success"]:
            print(f"❌ メトリクス取得失敗: {result['error']}")
            return {}

        try:
            runs_data = json.loads(result["data"])
        except json.JSONDecodeError:
            print("❌ JSON解析エラー")
            return {}

        metrics = {
            "total_runs": len(runs_data),
            "workflows": {},
            "daily_stats": {},
            "success_trend": [],
            "execution_times": [],
            "failure_patterns": {}
        }

        now = datetime.now()

        for run in runs_data:
            workflow_name = run.get("workflowName", "Unknown")
            conclusion = run.get("conclusion", "unknown")
            event = run.get("event", "unknown")
            created_at_str = run.get("createdAt", "")

            # ワークフロー別統計
            if workflow_name not in metrics["workflows"]:
                metrics["workflows"][workflow_name] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "success_rate": 0,
                    "recent_runs": []
                }

            workflow_stat = metrics["workflows"][workflow_name]
            workflow_stat["total"] += 1

            if conclusion == "success":
                workflow_stat["success"] += 1
            elif conclusion in ["failure", "cancelled"]:
                workflow_stat["failure"] += 1

            # 最近の実行記録
            workflow_stat["recent_runs"].append({
                "conclusion": conclusion,
                "event": event,
                "created_at": created_at_str,
                "url": run.get("url", "")
            })

            # 日別統計
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                date_key = created_at.strftime("%Y-%m-%d")

                if date_key not in metrics["daily_stats"]:
                    metrics["daily_stats"][date_key] = {"total": 0, "success": 0, "failure": 0}

                metrics["daily_stats"][date_key]["total"] += 1
                if conclusion == "success":
                    metrics["daily_stats"][date_key]["success"] += 1
                elif conclusion in ["failure", "cancelled"]:
                    metrics["daily_stats"][date_key]["failure"] += 1

                # 失敗パターン分析
                if conclusion in ["failure", "cancelled"]:
                    branch = run.get("headBranch", "unknown")
                    pattern_key = f"{workflow_name}_{event}_{branch}"
                    if pattern_key not in metrics["failure_patterns"]:
                        metrics["failure_patterns"][pattern_key] = 0
                    metrics["failure_patterns"][pattern_key] += 1

            except:
                pass

        # 成功率計算
        for workflow_name in metrics["workflows"]:
            workflow_stat = metrics["workflows"][workflow_name]
            if workflow_stat["total"] > 0:
                workflow_stat["success_rate"] = (workflow_stat["success"] / workflow_stat["total"]) * 100

        return metrics

    def generate_html_dashboard(self, metrics: Dict[str, Any]) -> str:
        """HTMLダッシュボード生成"""

        # ワークフロー別統計テーブル
        workflow_table_rows = ""
        for workflow_name, stats in metrics["workflows"].items():
            status_class = "success" if stats["success_rate"] >= 90 else "warning" if stats["success_rate"] >= 70 else "danger"
            workflow_table_rows += f"""
            <tr class="{status_class}">
                <td>{workflow_name}</td>
                <td>{stats['total']}</td>
                <td>{stats['success']}</td>
                <td>{stats['failure']}</td>
                <td>{stats['success_rate']:.1f}%</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar bg-{status_class}" style="width: {stats['success_rate']:.1f}%"></div>
                    </div>
                </td>
            </tr>"""

        # 日別統計チャートデータ
        daily_labels = []
        daily_success = []
        daily_failure = []

        # 最近7日間のデータを生成
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_labels.append(date)

            if date in metrics["daily_stats"]:
                daily_success.append(metrics["daily_stats"][date]["success"])
                daily_failure.append(metrics["daily_stats"][date]["failure"])
            else:
                daily_success.append(0)
                daily_failure.append(0)

        # 失敗パターン分析
        failure_patterns_html = ""
        top_failures = sorted(metrics["failure_patterns"].items(), key=lambda x: x[1], reverse=True)[:5]
        for pattern, count in top_failures:
            failure_patterns_html += f"""
            <li class="list-group-item d-flex justify-content-between align-items-center">
                {pattern}
                <span class="badge badge-danger pill">{count}</span>
            </li>"""

        # 全体統計
        total_runs = metrics["total_runs"]
        total_success = sum(stats["success"] for stats in metrics["workflows"].values())
        total_failures = sum(stats["failure"] for stats in metrics["workflows"].values())
        overall_success_rate = (total_success / total_runs * 100) if total_runs > 0 else 0

        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CI/CD メトリクス ダッシュボード</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .dashboard-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
        }}
        .metric-card {{
            border: none;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
        }}
        .progress {{
            height: 10px;
        }}
        .success {{ background-color: #d4edda !important; }}
        .warning {{ background-color: #fff3cd !important; }}
        .danger {{ background-color: #f8d7da !important; }}
        .bg-success {{ background-color: #28a745 !important; }}
        .bg-warning {{ background-color: #ffc107 !important; }}
        .bg-danger {{ background-color: #dc3545 !important; }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container">
            <h1 class="mb-0"><i class="fas fa-chart-line"></i> CI/CD メトリクス ダッシュボード</h1>
            <p class="mb-0">Kumihan-Formatter GitHub Actions 統計</p>
            <small>最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
        </div>
    </div>

    <div class="container mt-4">
        <!-- 全体統計カード -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card text-center">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-play-circle text-primary"></i></h5>
                        <h3 class="text-primary">{total_runs}</h3>
                        <p class="card-text">総実行数</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card text-center">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-check-circle text-success"></i></h5>
                        <h3 class="text-success">{total_success}</h3>
                        <p class="card-text">成功数</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card text-center">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-times-circle text-danger"></i></h5>
                        <h3 class="text-danger">{total_failures}</h3>
                        <p class="card-text">失敗数</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card text-center">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-percentage text-info"></i></h5>
                        <h3 class="text-info">{overall_success_rate:.1f}%</h3>
                        <p class="card-text">成功率</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 日別統計チャート -->
        <div class="row mb-4">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> 7日間実行統計</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="dailyChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-exclamation-triangle"></i> 頻発する失敗パターン</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            {failure_patterns_html or '<li class="list-group-item">失敗パターンなし</li>'}
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- ワークフロー別詳細統計 -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-cogs"></i> ワークフロー別統計</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>ワークフロー名</th>
                                        <th>総実行数</th>
                                        <th>成功数</th>
                                        <th>失敗数</th>
                                        <th>成功率</th>
                                        <th>進捗バー</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {workflow_table_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- フッター -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h6>🚀 Issue #967-970 改善効果</h6>
                        <p class="mb-0">
                            <span class="badge bg-success">Concurrency制御</span>
                            <span class="badge bg-primary">条件付き実行</span>
                            <span class="badge bg-info">並列数制限</span>
                            <span class="badge bg-warning">pytest依存関係修正</span>
                        </p>
                        <small class="text-muted">🤖 Generated by CI Metrics Dashboard - Issue #971</small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 日別統計チャート
        const ctx = document.getElementById('dailyChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(daily_labels)},
                datasets: [{{
                    label: '成功',
                    data: {json.dumps(daily_success)},
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true
                }}, {{
                    label: '失敗',
                    data: {json.dumps(daily_failure)},
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'CI/CD実行トレンド'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        return html_content

    def generate_dashboard(self):
        """ダッシュボード生成メイン処理"""
        print("📊 CI/CDメトリクスダッシュボード生成開始")
        print("=" * 60)

        # メトリクス収集
        metrics = self.collect_workflow_metrics()

        if not metrics:
            print("❌ メトリクス収集に失敗しました")
            return False

        # HTMLダッシュボード生成
        html_content = self.generate_html_dashboard(metrics)

        # ファイル出力
        dashboard_path = self.project_root / "tmp" / f"ci_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        dashboard_path.write_text(html_content, encoding='utf-8')

        print(f"✅ ダッシュボード生成完了: {dashboard_path}")
        print(f"🌐 ブラウザで開いてください: file://{dashboard_path}")

        # サマリー表示
        total_runs = metrics["total_runs"]
        total_success = sum(stats["success"] for stats in metrics["workflows"].values())
        overall_success_rate = (total_success / total_runs * 100) if total_runs > 0 else 0

        print(f"\n📈 メトリクスサマリー:")
        print(f"   総実行数: {total_runs}")
        print(f"   成功率: {overall_success_rate:.1f}%")
        print(f"   ワークフロー数: {len(metrics['workflows'])}")

        return True


def main():
    """メイン実行関数"""
    print("📊 CI/CDメトリクスダッシュボード生成ツール - Issue #971")
    print("GitHubActionsメトリクスをHTMLダッシュボードで可視化します")

    dashboard = CIMetricsDashboard()
    success = dashboard.generate_dashboard()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
