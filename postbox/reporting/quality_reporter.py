#!/usr/bin/env python3
"""
品質レポート生成システム
Claude ↔ Gemini協業での包括的品質レポート生成・分析
"""

import os
import json
import datetime
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
# Matplotlibをオプショナル依存として扱う
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from io import BytesIO
    import base64
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

@dataclass
class ReportSection:
    """レポートセクション"""
    title: str
    content: str
    data: Dict[str, Any]
    charts: List[str] = None  # Base64エンコードされたチャート画像

class QualityReporter:
    """品質レポート生成システム"""

    def __init__(self):
        self.reports_dir = Path("tmp/quality_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # データパス
        self.history_path = Path("postbox/monitoring/quality_history.json")
        self.alerts_path = Path("postbox/monitoring/quality_alerts.json")
        self.trends_path = Path("postbox/monitoring/quality_trends.json")
        self.cost_path = Path("postbox/monitoring/cost_tracking.json")

        print("📊 QualityReporter 初期化完了")

    def generate_comprehensive_report(self, format_type: str = "html") -> str:
        """包括的品質レポート生成"""

        print(f"📋 包括的品質レポート生成開始 (形式: {format_type})")

        # データ収集
        quality_data = self._load_quality_data()
        alert_data = self._load_alert_data()
        trend_data = self._load_trend_data()
        cost_data = self._load_cost_data()

        # レポートセクション生成
        sections = []

        # 1. エグゼクティブサマリー
        sections.append(self._generate_executive_summary(quality_data, alert_data, cost_data))

        # 2. 品質メトリクス詳細
        sections.append(self._generate_quality_metrics(quality_data))

        # 3. 傾向分析
        sections.append(self._generate_trend_analysis(quality_data, trend_data))

        # 4. アラート分析
        sections.append(self._generate_alert_analysis(alert_data))

        # 5. AI協業効率性
        sections.append(self._generate_ai_collaboration_analysis(quality_data, cost_data))

        # 6. 改善提案
        sections.append(self._generate_improvement_recommendations(quality_data, alert_data, trend_data))

        # 7. 技術的詳細
        sections.append(self._generate_technical_details(quality_data))

        # レポート形式別出力
        if format_type == "html":
            report_content = self._generate_html_report(sections)
            output_path = self.reports_dir / f"quality_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        elif format_type == "json":
            report_content = self._generate_json_report(sections)
            output_path = self.reports_dir / f"quality_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        elif format_type == "markdown":
            report_content = self._generate_markdown_report(sections)
            output_path = self.reports_dir / f"quality_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        else:
            raise ValueError(f"未対応の形式: {format_type}")

        # ファイル出力
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"✅ レポート生成完了: {output_path}")
        return str(output_path)

    def _load_quality_data(self) -> List[Dict]:
        """品質データ読み込み"""
        if not self.history_path.exists():
            return []

        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _load_alert_data(self) -> List[Dict]:
        """アラートデータ読み込み"""
        if not self.alerts_path.exists():
            return []

        try:
            with open(self.alerts_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _load_trend_data(self) -> Dict[str, Any]:
        """傾向データ読み込み"""
        if not self.trends_path.exists():
            return {}

        try:
            with open(self.trends_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def _load_cost_data(self) -> Dict[str, Any]:
        """コストデータ読み込み"""
        if not self.cost_path.exists():
            return {}

        try:
            with open(self.cost_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def _generate_executive_summary(self, quality_data: List[Dict],
                                  alert_data: List[Dict], cost_data: Dict) -> ReportSection:
        """エグゼクティブサマリー生成"""

        if not quality_data:
            return ReportSection(
                title="エグゼクティブサマリー",
                content="品質データが不足しています。",
                data={}
            )

        latest = quality_data[-1]
        recent = quality_data[-7:] if len(quality_data) >= 7 else quality_data

        # 主要指標
        current_score = latest["metrics"]["overall_score"]
        avg_recent_score = sum(q["metrics"]["overall_score"] for q in recent) / len(recent)
        total_errors = latest["metrics"]["error_count"]
        total_cost = cost_data.get("total_cost", 0)

        # 傾向
        if len(recent) >= 3:
            scores = [q["metrics"]["overall_score"] for q in recent[-3:]]
            trend = "上昇" if scores[-1] > scores[0] else "下降" if scores[-1] < scores[0] else "安定"
        else:
            trend = "不明"

        # アラート統計
        recent_alerts = [a for a in alert_data if self._is_recent(a.get("timestamp", ""), days=7)]
        critical_alerts = [a for a in recent_alerts if a.get("level") == "critical"]

        content = f"""
## 品質概要

**現在の品質スコア**: {current_score:.3f} ({self._get_quality_level(current_score)})
**7日間平均**: {avg_recent_score:.3f}
**品質傾向**: {trend}

## 主要指標

- **エラー数**: {total_errors}件
- **重要アラート**: {len(critical_alerts)}件 (7日間)
- **総コスト**: ${total_cost:.4f}
- **監視対象AI**: Claude, Gemini

## ステータス

{self._generate_status_summary(current_score, total_errors, len(critical_alerts))}
        """

        return ReportSection(
            title="エグゼクティブサマリー",
            content=content.strip(),
            data={
                "current_score": current_score,
                "avg_recent_score": avg_recent_score,
                "total_errors": total_errors,
                "total_cost": total_cost,
                "trend": trend,
                "critical_alerts": len(critical_alerts)
            }
        )

    def _generate_quality_metrics(self, quality_data: List[Dict]) -> ReportSection:
        """品質メトリクス詳細生成"""

        if not quality_data:
            return ReportSection(title="品質メトリクス", content="データなし", data={})

        latest = quality_data[-1]
        scores = latest["metrics"]["scores"]

        # チャート生成
        chart_data = self._create_quality_metrics_chart(scores)

        content = f"""
## 各品質指標詳細

| 指標 | スコア | 評価 |
|------|--------|------|
| 構文品質 | {scores.get('syntax', 0):.3f} | {self._get_score_rating(scores.get('syntax', 0))} |
| 型チェック | {scores.get('type_check', 0):.3f} | {self._get_score_rating(scores.get('type_check', 0))} |
| リント | {scores.get('lint', 0):.3f} | {self._get_score_rating(scores.get('lint', 0))} |
| フォーマット | {scores.get('format', 0):.3f} | {self._get_score_rating(scores.get('format', 0))} |
| セキュリティ | {scores.get('security', 0):.3f} | {self._get_score_rating(scores.get('security', 0))} |
| パフォーマンス | {scores.get('performance', 0):.3f} | {self._get_score_rating(scores.get('performance', 0))} |
| テスト | {scores.get('test', 0):.3f} | {self._get_score_rating(scores.get('test', 0))} |

## 品質基準達成状況

{self._generate_standards_compliance(scores)}
        """

        return ReportSection(
            title="品質メトリクス",
            content=content.strip(),
            data=scores,
            charts=[chart_data] if chart_data else None
        )

    def _generate_standards_compliance(self, scores: Dict[str, float]) -> str:
        """品質基準達成状況生成"""

        standards = {
            "syntax": 0.9,
            "type_check": 0.8,
            "lint": 0.8,
            "format": 0.9,
            "security": 0.9,
            "performance": 0.7,
            "test": 0.5
        }

        compliance_text = ""
        passed_count = 0

        for metric, threshold in standards.items():
            current_score = scores.get(metric, 0)
            if current_score >= threshold:
                status = "✅ 達成"
                passed_count += 1
            else:
                status = "❌ 未達成"

            compliance_text += f"- **{metric}**: {current_score:.3f} (基準: {threshold:.1f}) {status}\n"

        overall_compliance = f"\n**達成率**: {passed_count}/{len(standards)} ({passed_count/len(standards)*100:.1f}%)\n"

        return compliance_text + overall_compliance

    def _generate_period_analysis(self, trend_data: Dict) -> str:
        """期間別分析生成"""

        if not trend_data:
            return "期間別データがありません。"

        analysis_text = ""

        for period_name, data in [("daily", "日次"), ("weekly", "週次"), ("monthly", "月次")]:
            period_data = trend_data.get(period_name)
            if period_data:
                analysis_text += f"### {data}傾向\n"
                analysis_text += f"- 平均スコア: {period_data.get('average_score', 0):.3f}\n"
                analysis_text += f"- エラー率: {period_data.get('error_rate', 0):.1f}\n"
                analysis_text += f"- 改善率: {period_data.get('improvement_rate', 0):+.1%}\n"
                analysis_text += f"- 回帰回数: {period_data.get('regression_count', 0)}回\n\n"

        return analysis_text if analysis_text else "期間別分析データがありません。"

    def _format_recent_critical_alerts(self, recent_alerts: List[Dict]) -> str:
        """最近の重要アラート形式化"""

        critical_alerts = [a for a in recent_alerts if a.get("level") == "critical"]

        if not critical_alerts:
            return "重要アラートはありません。"

        alert_text = "| 時刻 | メッセージ | 影響ファイル |\n|------|------------|------------|\n"

        for alert in critical_alerts[-5:]:  # 最新5件
            timestamp = alert.get("timestamp", "不明")[:16]  # YYYY-MM-DD HH:MM
            message = alert.get("message", "詳細不明")
            files = alert.get("affected_files", [])
            files_str = ", ".join(files[:2]) + ("..." if len(files) > 2 else "")

            alert_text += f"| {timestamp} | {message} | {files_str} |\n"

        return alert_text

    def _analyze_collaboration_effectiveness(self, claude_sessions: List[Dict],
                                          gemini_sessions: List[Dict]) -> str:
        """協業効果分析"""

        if not claude_sessions and not gemini_sessions:
            return "協業データがありません。"

        analysis = ""

        # 効率性比較
        if claude_sessions and gemini_sessions:
            claude_avg_time = sum(s.get("execution_time", 0) for s in claude_sessions) / len(claude_sessions)
            gemini_avg_time = sum(s.get("execution_time", 0) for s in gemini_sessions) / len(gemini_sessions)

            if gemini_avg_time > 0:
                efficiency_ratio = claude_avg_time / gemini_avg_time
                analysis += f"- **処理効率**: Geminiは{efficiency_ratio:.1f}x効率的\n"

        # 品質効果
        total_sessions = len(claude_sessions) + len(gemini_sessions)
        analysis += f"- **協業率**: {len(gemini_sessions)}/{total_sessions} ({len(gemini_sessions)/total_sessions*100:.1f}%)\n"

        # 推奨事項
        if len(gemini_sessions) / total_sessions < 0.5:
            analysis += "- **推奨**: Gemini活用率向上の余地あり\n"
        else:
            analysis += "- **評価**: 適切な協業バランス\n"

        return analysis

    def _generate_trend_analysis(self, quality_data: List[Dict], trend_data: Dict) -> ReportSection:
        """傾向分析生成"""

        if len(quality_data) < 5:
            return ReportSection(
                title="傾向分析",
                content="傾向分析には最低5回のデータが必要です。",
                data={}
            )

        # 時系列チャート生成
        chart_data = self._create_trend_chart(quality_data)

        # 統計計算
        scores = [q["metrics"]["overall_score"] for q in quality_data]
        error_counts = [q["metrics"]["error_count"] for q in quality_data]

        # 改善率計算
        if len(scores) >= 10:
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            improvement = (sum(second_half)/len(second_half) - sum(first_half)/len(first_half)) / (sum(first_half)/len(first_half)) * 100
        else:
            improvement = 0

        content = f"""
## 品質傾向分析

### 全期間統計
- **平均品質スコア**: {sum(scores)/len(scores):.3f}
- **最高スコア**: {max(scores):.3f}
- **最低スコア**: {min(scores):.3f}
- **改善率**: {improvement:+.1f}%

### エラー傾向
- **平均エラー数**: {sum(error_counts)/len(error_counts):.1f}件
- **最大エラー数**: {max(error_counts)}件
- **最小エラー数**: {min(error_counts)}件

### 期間別分析
{self._generate_period_analysis(trend_data)}
        """

        return ReportSection(
            title="傾向分析",
            content=content.strip(),
            data={
                "average_score": sum(scores)/len(scores),
                "improvement_rate": improvement,
                "average_errors": sum(error_counts)/len(error_counts)
            },
            charts=[chart_data] if chart_data else None
        )

    def _generate_alert_analysis(self, alert_data: List[Dict]) -> ReportSection:
        """アラート分析生成"""

        if not alert_data:
            return ReportSection(
                title="アラート分析",
                content="アラートデータがありません。",
                data={}
            )

        # 期間別アラート
        recent_alerts = [a for a in alert_data if self._is_recent(a.get("timestamp", ""), days=30)]

        # レベル別統計
        level_counts = {}
        category_counts = {}

        for alert in recent_alerts:
            level = alert.get("level", "unknown")
            category = alert.get("category", "unknown")
            level_counts[level] = level_counts.get(level, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1

        content = f"""
## アラート分析 (30日間)

### 総アラート数: {len(recent_alerts)}件

### レベル別統計
{self._format_counts_table(level_counts)}

### カテゴリ別統計
{self._format_counts_table(category_counts, limit=10)}

### 最新の重要アラート
{self._format_recent_critical_alerts(recent_alerts)}
        """

        return ReportSection(
            title="アラート分析",
            content=content.strip(),
            data={
                "total_alerts": len(recent_alerts),
                "by_level": level_counts,
                "by_category": category_counts
            }
        )

    def _generate_ai_collaboration_analysis(self, quality_data: List[Dict],
                                          cost_data: Dict) -> ReportSection:
        """AI協業効率性分析生成"""

        # AI別統計
        claude_sessions = [q for q in quality_data if q.get("ai_agent") == "claude"]
        gemini_sessions = [q for q in quality_data if q.get("ai_agent") == "gemini"]

        # コスト効率
        total_cost = cost_data.get("total_cost", 0)
        total_tasks = len(cost_data.get("tasks", []))
        avg_cost_per_task = total_cost / total_tasks if total_tasks > 0 else 0

        # 品質比較
        claude_avg = sum(q["metrics"]["overall_score"] for q in claude_sessions) / len(claude_sessions) if claude_sessions else 0
        gemini_avg = sum(q["metrics"]["overall_score"] for q in gemini_sessions) / len(gemini_sessions) if gemini_sessions else 0

        content = f"""
## AI協業効率性分析

### セッション統計
- **Claude セッション**: {len(claude_sessions)}回 (平均品質: {claude_avg:.3f})
- **Gemini セッション**: {len(gemini_sessions)}回 (平均品質: {gemini_avg:.3f})

### コスト効率性
- **総コスト**: ${total_cost:.4f}
- **タスク数**: {total_tasks}件
- **タスク単価**: ${avg_cost_per_task:.4f}

### 協業効果
{self._analyze_collaboration_effectiveness(claude_sessions, gemini_sessions)}
        """

        return ReportSection(
            title="AI協業効率性",
            content=content.strip(),
            data={
                "claude_sessions": len(claude_sessions),
                "gemini_sessions": len(gemini_sessions),
                "claude_avg_quality": claude_avg,
                "gemini_avg_quality": gemini_avg,
                "total_cost": total_cost,
                "avg_cost_per_task": avg_cost_per_task
            }
        )

    def _generate_improvement_recommendations(self, quality_data: List[Dict],
                                            alert_data: List[Dict], trend_data: Dict) -> ReportSection:
        """改善提案生成"""

        recommendations = []

        if not quality_data:
            recommendations.append("📊 品質データの蓄積を開始してください")
            return ReportSection(
                title="改善提案",
                content="\n".join(recommendations),
                data={}
            )

        latest = quality_data[-1]
        scores = latest["metrics"]["scores"]

        # スコア別改善提案
        if scores.get("type_check", 1) < 0.8:
            recommendations.append("📝 型注釈の追加・改善を優先的に実施してください")

        if scores.get("lint", 1) < 0.8:
            recommendations.append("🎯 コード品質改善 (flake8) を実施してください")

        if scores.get("security", 1) < 0.9:
            recommendations.append("🔒 セキュリティレビューを実施してください")

        if scores.get("test", 1) < 0.5:
            recommendations.append("🧪 テストカバレッジの向上が急務です")

        # アラート分析による提案
        recent_alerts = [a for a in alert_data if self._is_recent(a.get("timestamp", ""), days=7)]
        critical_alerts = [a for a in recent_alerts if a.get("level") == "critical"]

        if len(critical_alerts) > 3:
            recommendations.append("🚨 重要アラートが多発しています。緊急対応が必要です")

        # 傾向分析による提案
        if len(quality_data) >= 5:
            recent_scores = [q["metrics"]["overall_score"] for q in quality_data[-5:]]
            if all(recent_scores[i] >= recent_scores[i+1] for i in range(len(recent_scores)-1)):
                recommendations.append("📉 品質が継続的に低下しています。根本原因の調査が必要です")

        # 一般的な提案
        recommendations.extend([
            "⚙️ 定期的な品質監視の継続",
            "🤖 AI協業システムの最適化",
            "📈 品質メトリクスの可視化強化"
        ])

        content = "\n".join(f"- {rec}" for rec in recommendations)

        return ReportSection(
            title="改善提案",
            content=content,
            data={"recommendations": recommendations}
        )

    def _generate_technical_details(self, quality_data: List[Dict]) -> ReportSection:
        """技術的詳細生成"""

        if not quality_data:
            return ReportSection(title="技術的詳細", content="データなし", data={})

        latest = quality_data[-1]

        content = f"""
## 技術的詳細

### 最新チェック情報
- **実行時刻**: {latest.get('timestamp', 'N/A')}
- **AI エージェント**: {latest.get('ai_agent', 'N/A')}
- **実行時間**: {latest.get('execution_time', 'N/A')}秒
- **対象ファイル数**: {len(latest.get('target_files', []))}件

### 対象ファイル
{self._format_file_list(latest.get('target_files', []))}

### システム情報
- **監視間隔**: 5分
- **データ保持期間**: 最新50件
- **アラート保持期間**: 最新100件
        """

        return ReportSection(
            title="技術的詳細",
            content=content.strip(),
            data=latest
        )

    def _create_quality_metrics_chart(self, scores: Dict[str, float]) -> str:
        """品質メトリクスチャート生成"""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            import numpy as np

            categories = list(scores.keys())
            values = list(scores.values())

            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(categories, values, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#F4B942', '#5E8B73', '#8E44AD'])

            ax.set_ylabel('Score')
            ax.set_title('Quality Metrics by Category')
            ax.set_ylim(0, 1)

            # 値ラベル追加
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.2f}', ha='center', va='bottom')

            plt.xticks(rotation=45)
            plt.tight_layout()

            # Base64エンコード
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150)
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()

            return chart_data

        except Exception as e:
            print(f"⚠️ チャート生成エラー: {e}")
            return None

    def _create_trend_chart(self, quality_data: List[Dict]) -> str:
        """傾向チャート生成"""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            from datetime import datetime

            # データ準備
            timestamps = []
            scores = []

            for data in quality_data[-30:]:  # 最新30件
                try:
                    timestamp = datetime.fromisoformat(data["timestamp"])
                    score = data["metrics"]["overall_score"]
                    timestamps.append(timestamp)
                    scores.append(score)
                except:
                    continue

            if len(timestamps) < 2:
                return None

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(timestamps, scores, marker='o', linewidth=2, markersize=4)

            ax.set_ylabel('Quality Score')
            ax.set_title('Quality Score Trend')
            ax.grid(True, alpha=0.3)

            # 日付フォーマット
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(timestamps)//10)))

            plt.xticks(rotation=45)
            plt.tight_layout()

            # Base64エンコード
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150)
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()

            return chart_data

        except Exception as e:
            print(f"⚠️ トレンドチャート生成エラー: {e}")
            return None

    def _generate_html_report(self, sections: List[ReportSection]) -> str:
        """HTMLレポート生成"""

        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>品質レポート - Kumihan Formatter</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .metric-excellent {{ color: #27ae60; font-weight: bold; }}
        .metric-good {{ color: #f39c12; font-weight: bold; }}
        .metric-poor {{ color: #e74c3c; font-weight: bold; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        .chart img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .alert {{ padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .alert-info {{ background-color: #d1ecf1; border-left: 4px solid #bee5eb; }}
        .alert-warning {{ background-color: #fff3cd; border-left: 4px solid #ffeaa7; }}
        .alert-error {{ background-color: #f8d7da; border-left: 4px solid #f5c6cb; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
        pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Kumihan Formatter 品質レポート</h1>
        <p><strong>生成日時:</strong> {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>

        {self._format_html_sections(sections)}

        <div class="footer">
            <p>🤖 Generated by Claude ↔ Gemini Collaboration Quality System</p>
        </div>
    </div>
</body>
</html>
        """

        return html_content

    def _generate_json_report(self, sections: List[ReportSection]) -> str:
        """JSONレポート生成"""

        report_data = {
            "generated_at": datetime.datetime.now().isoformat(),
            "generator": "Claude ↔ Gemini Quality Reporter",
            "version": "1.0.0",
            "sections": [asdict(section) for section in sections]
        }

        return json.dumps(report_data, indent=2, ensure_ascii=False)

    def _generate_markdown_report(self, sections: List[ReportSection]) -> str:
        """Markdownレポート生成"""

        content = f"""# 🔍 Kumihan Formatter 品質レポート

**生成日時**: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
**生成システム**: Claude ↔ Gemini Collaboration Quality System

---

"""

        for section in sections:
            content += f"# {section.title}\n\n"
            content += section.content + "\n\n"

            if section.charts:
                content += "## チャート\n\n"
                for i, chart in enumerate(section.charts):
                    content += f"![Chart {i+1}](data:image/png;base64,{chart})\n\n"

            content += "---\n\n"

        return content

    # ヘルパーメソッド

    def _is_recent(self, timestamp_str: str, days: int = 7) -> bool:
        """最近のデータかチェック"""
        try:
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
            cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
            return timestamp >= cutoff
        except:
            return False

    def _get_quality_level(self, score: float) -> str:
        """品質レベル取得"""
        if score >= 0.95:
            return "優秀"
        elif score >= 0.80:
            return "良好"
        elif score >= 0.60:
            return "許容"
        elif score >= 0.40:
            return "不良"
        else:
            return "重大"

    def _get_score_rating(self, score: float) -> str:
        """スコア評価取得"""
        if score >= 0.9:
            return "🟢 優秀"
        elif score >= 0.7:
            return "🟡 良好"
        else:
            return "🔴 要改善"

    def _generate_status_summary(self, score: float, errors: int, critical_alerts: int) -> str:
        """ステータスサマリー生成"""
        if critical_alerts > 0:
            return "🚨 **重要な問題が検出されています。緊急対応が必要です。**"
        elif score < 0.7:
            return "⚠️ **品質基準を下回っています。改善が必要です。**"
        elif errors > 10:
            return "📝 **エラーが多めです。定期的なメンテナンスを推奨します。**"
        else:
            return "✅ **品質基準を満たしています。現在の品質を維持してください。**"

    def _format_html_sections(self, sections: List[ReportSection]) -> str:
        """HTMLセクション形式化"""
        html = ""
        for section in sections:
            html += f"<h2>{section.title}</h2>\n"

            # MarkdownをシンプルなHTMLに変換
            content = section.content.replace('\n## ', '\n<h3>').replace('</h3>', '</h3>')
            content = content.replace('\n### ', '\n<h4>').replace('</h4>', '</h4>')
            content = content.replace('**', '<strong>').replace('**', '</strong>')
            content = content.replace('\n- ', '\n<li>').replace('\n', '<br>\n')

            html += f"<div>{content}</div>\n"

            if section.charts:
                for chart in section.charts:
                    html += f'<div class="chart"><img src="data:image/png;base64,{chart}" alt="Chart"></div>\n'

        return html

    def _format_counts_table(self, counts: Dict[str, int], limit: int = None) -> str:
        """カウントテーブル形式化"""
        if not counts:
            return "データなし"

        items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        if limit:
            items = items[:limit]

        table = "| 項目 | 件数 |\n|------|------|\n"
        for item, count in items:
            table += f"| {item} | {count} |\n"

        return table

    def _format_file_list(self, files: List[str], limit: int = 10) -> str:
        """ファイルリスト形式化"""
        if not files:
            return "対象ファイルなし"

        display_files = files[:limit]
        result = "\n".join(f"- {file}" for file in display_files)

        if len(files) > limit:
            result += f"\n... 他 {len(files) - limit} ファイル"

        return result

def main():
    """テスト実行"""
    reporter = QualityReporter()

    # HTML レポート生成
    html_path = reporter.generate_comprehensive_report("html")
    print(f"📊 HTMLレポート: {html_path}")

    # JSON レポート生成
    json_path = reporter.generate_comprehensive_report("json")
    print(f"📋 JSONレポート: {json_path}")

    # Markdown レポート生成
    md_path = reporter.generate_comprehensive_report("markdown")
    print(f"📝 Markdownレポート: {md_path}")

if __name__ == "__main__":
    main()
