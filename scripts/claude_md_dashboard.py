#!/usr/bin/env python3
"""
CLAUDE.md 監視ダッシュボード
Issue #686 Phase 3: サイズ推移グラフ・セクション別分析・最適化推奨提案
"""

import os
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd


class CLAUDEmdDashboard:
    """CLAUDE.md監視ダッシュボード"""

    def __init__(self, claude_md_path: str = "CLAUDE.md"):
        self.claude_md_path = claude_md_path
        self.history_file = Path(".claude_md_history.json")
        self.output_dir = Path("dashboard_output")
        self.output_dir.mkdir(exist_ok=True)

    def generate_dashboard(self) -> Dict:
        """包括的ダッシュボード生成"""
        print("📊 CLAUDE.md監視ダッシュボード生成中...")

        dashboard_data = {
            "generation_time": datetime.now().isoformat(),
            "current_status": self._get_current_status(),
            "size_trends": self._analyze_size_trends(),
            "section_analysis": self._analyze_sections(),
            "quality_metrics": self._calculate_quality_metrics(),
            "recommendations": self._generate_recommendations()
        }

        # グラフ生成
        self._generate_size_trend_chart()
        self._generate_section_distribution_chart()
        self._generate_quality_overview_chart()

        # HTMLダッシュボード生成
        self._generate_html_dashboard(dashboard_data)

        return dashboard_data

    def _get_current_status(self) -> Dict:
        """現在のステータス取得"""
        if not os.path.exists(self.claude_md_path):
            return {"error": "CLAUDE.md not found"}

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.splitlines()
        return {
            "lines": len(lines),
            "bytes": len(content.encode('utf-8')),
            "kb_size": len(content.encode('utf-8')) / 1024,
            "sections": content.count('#'),
            "deep_nesting": content.count('####'),
            "last_modified": datetime.fromtimestamp(
                os.path.getmtime(self.claude_md_path)
            ).isoformat()
        }

    def _analyze_size_trends(self) -> Dict:
        """サイズ推移分析"""
        if not self.history_file.exists():
            return {"error": "No history data available"}

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            return {"error": "Failed to load history"}

        if not history:
            return {"error": "Empty history"}

        # 過去30日のデータ
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_history = [
            entry for entry in history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
        ]

        if not recent_history:
            return {"error": "No recent history"}

        # トレンド計算
        sizes = [entry["bytes"] for entry in recent_history]
        line_counts = [entry["lines"] for entry in recent_history]

        return {
            "data_points": len(recent_history),
            "size_trend": {
                "current": sizes[-1] if sizes else 0,
                "average": sum(sizes) / len(sizes) if sizes else 0,
                "min": min(sizes) if sizes else 0,
                "max": max(sizes) if sizes else 0,
                "trend_direction": "increasing" if len(sizes) > 1 and sizes[-1] > sizes[0] else "stable"
            },
            "line_trend": {
                "current": line_counts[-1] if line_counts else 0,
                "average": sum(line_counts) / len(line_counts) if line_counts else 0,
                "min": min(line_counts) if line_counts else 0,
                "max": max(line_counts) if line_counts else 0
            }
        }

    def _analyze_sections(self) -> Dict:
        """セクション別分析"""
        if not os.path.exists(self.claude_md_path):
            return {"error": "CLAUDE.md not found"}

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # セクション分割・分析
        import re
        sections = re.split(r'^(#+\s.*)', content, flags=re.MULTILINE)

        section_stats = []
        for i in range(1, len(sections), 2):
            if i+1 < len(sections):
                title = sections[i].strip()
                body = sections[i+1]

                # ヘッダーレベル判定
                level = len(re.match(r'^#+', title).group()) if re.match(r'^#+', title) else 0

                section_stats.append({
                    "title": title,
                    "level": level,
                    "lines": len(body.splitlines()),
                    "bytes": len(body.encode('utf-8')),
                    "words": len(body.split()),
                    "has_code": "```" in body,
                    "has_links": "[" in body and "]" in body
                })

        # セクション統計
        total_lines = sum(s["lines"] for s in section_stats)

        return {
            "total_sections": len(section_stats),
            "by_level": {
                f"level_{i}": len([s for s in section_stats if s["level"] == i])
                for i in range(1, 6)
            },
            "largest_sections": sorted(
                section_stats, key=lambda x: x["lines"], reverse=True
            )[:5],
            "average_section_size": total_lines / len(section_stats) if section_stats else 0,
            "sections_over_20_lines": len([s for s in section_stats if s["lines"] > 20])
        }

    def _calculate_quality_metrics(self) -> Dict:
        """品質メトリクス計算"""
        if not os.path.exists(self.claude_md_path):
            return {"error": "CLAUDE.md not found"}

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.splitlines()

        # 品質指標計算
        metrics = {
            "duplication_ratio": self._calculate_duplication_ratio(lines),
            "information_density": self._calculate_information_density(content),
            "structure_quality": self._calculate_structure_quality(content),
            "maintenance_score": self._calculate_maintenance_score(content)
        }

        # 総合品質スコア (0-100)
        metrics["overall_quality"] = (
            metrics["duplication_ratio"] * 0.2 +
            metrics["information_density"] * 0.3 +
            metrics["structure_quality"] * 0.3 +
            metrics["maintenance_score"] * 0.2
        ) * 100

        return metrics

    def _calculate_duplication_ratio(self, lines: List[str]) -> float:
        """重複率計算"""
        non_empty_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        if not non_empty_lines:
            return 1.0

        unique_lines = set(non_empty_lines)
        return len(unique_lines) / len(non_empty_lines)

    def _calculate_information_density(self, content: str) -> float:
        """情報密度計算"""
        # 文字数に対する実質情報量の比率
        total_chars = len(content)
        if total_chars == 0:
            return 0.0

        # マークダウン記号、空白を除いた実質文字数
        import re
        clean_content = re.sub(r'[#*\-`\[\](){}\s]', '', content)
        info_chars = len(clean_content)

        return min(info_chars / total_chars, 1.0)

    def _calculate_structure_quality(self, content: str) -> float:
        """構造品質計算"""
        # ヘッダー階層の論理性、セクション長のバランス等
        header_count = content.count('#')
        deep_nesting = content.count('####')

        if header_count == 0:
            return 0.5

        # 深いネストが少ないほど良い構造
        nesting_score = max(0, 1 - (deep_nesting / header_count))

        # セクション長のバランス
        sections = content.split('\n#')
        if len(sections) > 1:
            section_lengths = [len(section) for section in sections]
            avg_length = sum(section_lengths) / len(section_lengths)
            variance = sum((l - avg_length) ** 2 for l in section_lengths) / len(section_lengths)
            balance_score = max(0, 1 - (variance / (avg_length ** 2)) if avg_length > 0 else 0)
        else:
            balance_score = 0.5

        return (nesting_score + balance_score) / 2

    def _calculate_maintenance_score(self, content: str) -> float:
        """メンテナンス性スコア計算"""
        # TODO, FIXME等の古いマーカーの少なさ
        outdated_markers = ['TODO', 'FIXME', 'alpha-', 'beta-', 'v1.']
        penalty_count = sum(content.count(marker) for marker in outdated_markers)

        total_lines = len(content.splitlines())
        if total_lines == 0:
            return 1.0

        return max(0, 1 - (penalty_count / total_lines))

    def _generate_recommendations(self) -> List[str]:
        """最適化推奨提案生成"""
        recommendations = []

        current_status = self._get_current_status()
        if "error" in current_status:
            return ["CLAUDE.md file not accessible"]

        # サイズベース推奨
        if current_status["lines"] > 200:
            recommendations.append("🚨 CRITICAL: ファイルサイズが200行を超過。即座の削減が必要")
        elif current_status["lines"] > 150:
            recommendations.append("⚠️ WARNING: ファイルサイズが推奨限界に接近。削減を検討")

        if current_status["kb_size"] > 10:
            recommendations.append("🚨 CRITICAL: ファイルサイズが10KBを超過。内容圧縮が必要")
        elif current_status["kb_size"] > 8:
            recommendations.append("⚠️ WARNING: ファイルサイズが8KBを超過。最適化を推奨")

        # 構造ベース推奨
        if current_status["deep_nesting"] > 10:
            recommendations.append("📋 構造最適化: 深いネスト(####以下)が多すぎます。階層を見直してください")

        # セクション分析ベース推奨
        section_analysis = self._analyze_sections()
        if "sections_over_20_lines" in section_analysis and section_analysis["sections_over_20_lines"] > 3:
            recommendations.append("✂️ セクション分割: 20行を超える長大セクションが複数あります")

        # 品質メトリクスベース推奨
        quality_metrics = self._calculate_quality_metrics()
        if "overall_quality" in quality_metrics and quality_metrics["overall_quality"] < 70:
            recommendations.append("🔧 品質改善: 総合品質スコアが70%未満。重複削除・構造改善が必要")

        if not recommendations:
            recommendations.append("✅ 現在の状態は良好です。定期的な監視を継続してください")

        return recommendations

    def _generate_size_trend_chart(self):
        """サイズ推移チャート生成"""
        from pathlib import Path

        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            return

        if len(history) < 2:
            return

        # tmp/配下に出力ディレクトリを確保
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        # output_dirをtmp/配下に設定
        self.output_dir = tmp_dir / "dashboard_output"
        self.output_dir.mkdir(exist_ok=True)

        # データ準備
        dates = [datetime.fromisoformat(entry["timestamp"]) for entry in history]
        sizes = [entry["bytes"] / 1024 for entry in history]  # KB変換
        lines = [entry["lines"] for entry in history]

        # グラフ作成
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # サイズ推移
        ax1.plot(dates, sizes, 'b-', marker='o', linewidth=2, markersize=4)
        ax1.axhline(y=8, color='orange', linestyle='--', alpha=0.7, label='推奨限界 (8KB)')
        ax1.axhline(y=10, color='red', linestyle='--', alpha=0.7, label='警告限界 (10KB)')
        ax1.set_ylabel('ファイルサイズ (KB)')
        ax1.set_title('CLAUDE.md サイズ推移')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 行数推移
        ax2.plot(dates, lines, 'g-', marker='s', linewidth=2, markersize=4)
        ax2.axhline(y=150, color='orange', linestyle='--', alpha=0.7, label='推奨限界 (150行)')
        ax2.axhline(y=200, color='red', linestyle='--', alpha=0.7, label='警告限界 (200行)')
        ax2.set_ylabel('行数')
        ax2.set_xlabel('日時')
        ax2.set_title('CLAUDE.md 行数推移')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 日付軸フォーマット
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'size_trends.png', dpi=150, bbox_inches='tight')
        plt.close()

    def _generate_section_distribution_chart(self):
        """セクション分布チャート生成"""
        from pathlib import Path

        section_analysis = self._analyze_sections()
        if "error" in section_analysis:
            return

        # tmp/配下に出力ディレクトリを確保
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        # output_dirをtmp/配下に設定
        self.output_dir = tmp_dir / "dashboard_output"
        self.output_dir.mkdir(exist_ok=True)

        # セクションレベル分布
        level_data = section_analysis["by_level"]
        levels = list(level_data.keys())
        counts = list(level_data.values())

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # レベル別分布
        ax1.bar(levels, counts, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        ax1.set_title('セクションレベル分布')
        ax1.set_xlabel('ヘッダーレベル')
        ax1.set_ylabel('セクション数')

        # 大きなセクション TOP5
        if section_analysis["largest_sections"]:
            top_sections = section_analysis["largest_sections"]
            section_names = [s["title"][:20] + "..." if len(s["title"]) > 20 else s["title"]
                           for s in top_sections]
            section_sizes = [s["lines"] for s in top_sections]

            ax2.barh(range(len(section_names)), section_sizes, color='skyblue')
            ax2.set_yticks(range(len(section_names)))
            ax2.set_yticklabels(section_names)
            ax2.set_title('最大セクション TOP5')
            ax2.set_xlabel('行数')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'section_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()

    def _generate_quality_overview_chart(self):
        """品質概要チャート生成"""
        from pathlib import Path

        quality_metrics = self._calculate_quality_metrics()
        if "error" in quality_metrics:
            return

        # tmp/配下に出力ディレクトリを確保
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        # output_dirをtmp/配下に設定
        self.output_dir = tmp_dir / "dashboard_output"
        self.output_dir.mkdir(exist_ok=True)

        # レーダーチャート
        categories = ['重複排除', '情報密度', '構造品質', 'メンテナンス性']
        values = [
            quality_metrics["duplication_ratio"] * 100,
            quality_metrics["information_density"] * 100,
            quality_metrics["structure_quality"] * 100,
            quality_metrics["maintenance_score"] * 100
        ]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        # レーダーチャート描画
        angles = [i * 2 * 3.14159 / len(categories) for i in range(len(categories))]
        angles += angles[:1]  # 閉じるため
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2)
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_title('CLAUDE.md 品質メトリクス', pad=20)

        plt.savefig(self.output_dir / 'quality_overview.png', dpi=150, bbox_inches='tight')
        plt.close()

    def _generate_html_dashboard(self, dashboard_data: Dict):
        """HTMLダッシュボード生成"""
        from pathlib import Path

        # tmp/配下に出力ディレクトリを確保
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        # output_dirをtmp/配下に設定
        self.output_dir = tmp_dir / "dashboard_output"
        self.output_dir.mkdir(exist_ok=True)

        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLAUDE.md 監視ダッシュボード</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .status-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .status-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0; }}
        .chart-section {{ margin: 30px 0; }}
        .chart-section img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
        .alert-critical {{ color: #dc3545; font-weight: bold; }}
        .alert-warning {{ color: #fd7e14; font-weight: bold; }}
        .alert-good {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 CLAUDE.md 監視ダッシュボード</h1>
            <p>生成日時: {dashboard_data['generation_time']}</p>
        </div>

        <div class="status-grid">
            <div class="status-card">
                <div class="status-value">{dashboard_data['current_status'].get('lines', 'N/A')}</div>
                <div>総行数</div>
            </div>
            <div class="status-card">
                <div class="status-value">{dashboard_data['current_status'].get('kb_size', 0):.1f}KB</div>
                <div>ファイルサイズ</div>
            </div>
            <div class="status-card">
                <div class="status-value">{dashboard_data['current_status'].get('sections', 'N/A')}</div>
                <div>セクション数</div>
            </div>
            <div class="status-card">
                <div class="status-value">{dashboard_data.get('quality_metrics', {}).get('overall_quality', 0):.0f}%</div>
                <div>品質スコア</div>
            </div>
        </div>

        <div class="recommendations">
            <h3>💡 最適化推奨事項</h3>
            <ul>
        """

        for rec in dashboard_data.get('recommendations', []):
            css_class = "alert-critical" if "🚨" in rec else "alert-warning" if "⚠️" in rec else "alert-good"
            html_content += f'<li class="{css_class}">{rec}</li>'

        html_content += """
            </ul>
        </div>

        <div class="chart-section">
            <h3>📈 サイズ推移</h3>
            <img src="size_trends.png" alt="サイズ推移チャート">
        </div>

        <div class="chart-section">
            <h3>📋 セクション分析</h3>
            <img src="section_distribution.png" alt="セクション分布チャート">
        </div>

        <div class="chart-section">
            <h3>🔍 品質メトリクス</h3>
            <img src="quality_overview.png" alt="品質概要チャート">
        </div>
    </div>
</body>
</html>
        """

        with open(self.output_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="CLAUDE.md Dashboard Generator")
    parser.add_argument("--output-dir", default="dashboard_output", help="出力ディレクトリ")
    parser.add_argument("--claude-md", default="CLAUDE.md", help="CLAUDE.mdファイルパス")

    args = parser.parse_args()

    dashboard = CLAUDEmdDashboard(args.claude_md)
    dashboard.output_dir = Path(args.output_dir)

    try:
        result = dashboard.generate_dashboard()

        print("✅ ダッシュボード生成完了")
        print(f"📁 出力先: {dashboard.output_dir}/dashboard.html")
        print(f"📊 品質スコア: {result.get('quality_metrics', {}).get('overall_quality', 0):.1f}%")

        # 推奨事項表示
        print("\n💡 推奨事項:")
        for rec in result.get('recommendations', []):
            print(f"   {rec}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # 依存関係チェック
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as e:
        print(f"❌ 必要なライブラリが不足: {e}")
        print("💡 インストール: pip install matplotlib pandas")
        sys.exit(1)

    main()
