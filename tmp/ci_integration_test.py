#!/usr/bin/env python3
"""
CI/CD統合テストスクリプト - Issue #971対応

GitHub Actionsワークフローの動作確認と統計収集を行います。
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class CIIntegrationTester:
    """CI/CD統合テスト・モニタリングクラス"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.workflows = [
            "Branch Name Validation",
            "Quality Gate",
            "Test Coverage and Quality",
            "Security Scan",
            "Optimized CI Pipeline",
            "CLAUDE.md Management System"
        ]
        self.results = {}

    def run_gh_command(self, args: List[str]) -> Dict[str, Any]:
        """GitHub CLIコマンドを実行し、結果を返す"""
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

    def get_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """最近のワークフロー実行履歴を取得"""
        print("📊 最近のワークフロー実行履歴を収集中...")

        result = self.run_gh_command([
            "run", "list",
            "--limit", str(limit),
            "--json", "status,conclusion,workflowName,createdAt,updatedAt,url,event"
        ])

        if not result["success"]:
            print(f"❌ ワークフロー履歴取得失敗: {result['error']}")
            return []

        try:
            runs_data = json.loads(result["data"])
            return runs_data
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e}")
            return []

    def analyze_workflow_performance(self, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ワークフロー性能分析"""
        print("🔍 ワークフロー性能を分析中...")

        stats = {
            "total_runs": len(runs),
            "success_rate": 0,
            "failure_count": 0,
            "workflow_stats": {},
            "recent_24h": 0,
            "avg_duration_minutes": 0
        }

        successful_runs = 0
        total_duration = 0
        duration_count = 0
        now = datetime.now()

        for run in runs:
            # 基本統計
            workflow_name = run.get("workflowName", "Unknown")
            status = run.get("status", "unknown")
            conclusion = run.get("conclusion", "unknown")

            # ワークフロー別統計の初期化
            if workflow_name not in stats["workflow_stats"]:
                stats["workflow_stats"][workflow_name] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "success_rate": 0
                }

            stats["workflow_stats"][workflow_name]["total"] += 1

            # 成功・失敗カウント
            if conclusion == "success":
                successful_runs += 1
                stats["workflow_stats"][workflow_name]["success"] += 1
            elif conclusion in ["failure", "cancelled"]:
                stats["failure_count"] += 1
                stats["workflow_stats"][workflow_name]["failure"] += 1

            # 24時間以内の実行数
            try:
                created_at = datetime.fromisoformat(run.get("createdAt", "").replace("Z", "+00:00"))
                if (now - created_at) < timedelta(hours=24):
                    stats["recent_24h"] += 1
            except:
                pass

            # 実行時間計算（概算）
            try:
                created = datetime.fromisoformat(run.get("createdAt", "").replace("Z", "+00:00"))
                updated = datetime.fromisoformat(run.get("updatedAt", "").replace("Z", "+00:00"))
                duration = (updated - created).total_seconds() / 60  # 分単位
                if duration > 0 and duration < 120:  # 異常値を除く（2時間以内）
                    total_duration += duration
                    duration_count += 1
            except:
                pass

        # 成功率計算
        if len(runs) > 0:
            stats["success_rate"] = (successful_runs / len(runs)) * 100

        # ワークフロー別成功率計算
        for workflow_name in stats["workflow_stats"]:
            workflow_stat = stats["workflow_stats"][workflow_name]
            if workflow_stat["total"] > 0:
                workflow_stat["success_rate"] = (workflow_stat["success"] / workflow_stat["total"]) * 100

        # 平均実行時間
        if duration_count > 0:
            stats["avg_duration_minutes"] = total_duration / duration_count

        return stats

    def check_workflow_health(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフローヘルス評価"""
        print("🏥 ワークフローヘルスチェック実行中...")

        health = {
            "overall_status": "healthy",
            "issues": [],
            "recommendations": [],
            "score": 100
        }

        # 成功率チェック
        if stats["success_rate"] < 95:
            health["overall_status"] = "warning"
            health["issues"].append(f"成功率低下: {stats['success_rate']:.1f}% (目標: >95%)")
            health["score"] -= 20

        if stats["success_rate"] < 80:
            health["overall_status"] = "critical"
            health["score"] -= 30

        # 24時間以内の実行数チェック
        if stats["recent_24h"] > 50:
            health["issues"].append(f"24時間以内の実行数が多い: {stats['recent_24h']}回")
            health["recommendations"].append("不要なワークフロー実行を削減してください")
            health["score"] -= 10

        # 平均実行時間チェック
        if stats["avg_duration_minutes"] > 15:
            health["issues"].append(f"平均実行時間が長い: {stats['avg_duration_minutes']:.1f}分")
            health["recommendations"].append("ワークフロー並列化や最適化を検討してください")
            health["score"] -= 15

        # ワークフロー別問題チェック
        for workflow_name, workflow_stat in stats["workflow_stats"].items():
            if workflow_stat["success_rate"] < 90 and workflow_stat["total"] >= 3:
                health["issues"].append(f"{workflow_name}: 成功率 {workflow_stat['success_rate']:.1f}%")
                health["score"] -= 10

        # スコア調整
        health["score"] = max(0, health["score"])

        return health

    def generate_report(self, stats: Dict[str, Any], health: Dict[str, Any]) -> str:
        """統合レポート生成"""
        report = []
        report.append("="*80)
        report.append("📊 CI/CD統合テスト・モニタリングレポート")
        report.append(f"⏰ 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)

        # 全体サマリー
        report.append("\n🎯 全体サマリー")
        report.append(f"   総実行数: {stats['total_runs']}回")
        report.append(f"   成功率: {stats['success_rate']:.1f}%")
        report.append(f"   失敗数: {stats['failure_count']}回")
        report.append(f"   24時間以内: {stats['recent_24h']}回")
        report.append(f"   平均実行時間: {stats['avg_duration_minutes']:.1f}分")

        # ヘルス状態
        report.append(f"\n🏥 ヘルス状態: {health['overall_status'].upper()}")
        report.append(f"   ヘルススコア: {health['score']}/100")

        if health["issues"]:
            report.append("\n❌ 検出された問題:")
            for issue in health["issues"]:
                report.append(f"   • {issue}")

        if health["recommendations"]:
            report.append("\n💡 推奨事項:")
            for rec in health["recommendations"]:
                report.append(f"   • {rec}")

        # ワークフロー別詳細
        report.append("\n📈 ワークフロー別統計:")
        for workflow_name, workflow_stat in stats["workflow_stats"].items():
            status_icon = "✅" if workflow_stat["success_rate"] >= 90 else "⚠️" if workflow_stat["success_rate"] >= 70 else "❌"
            report.append(f"   {status_icon} {workflow_name}:")
            report.append(f"      実行数: {workflow_stat['total']}, 成功率: {workflow_stat['success_rate']:.1f}%")

        # Issue #967-970の改善効果
        report.append("\n🚀 Issue #967-970改善効果:")
        report.append(f"   • Concurrency制御: 重複実行の排除")
        report.append(f"   • 条件付き実行: 不要実行の削減")
        report.append(f"   • 並列数制限: リソース競合の回避")

        if stats["success_rate"] >= 95:
            report.append("   ✅ 目標成功率 (>95%) 達成!")

        if stats["avg_duration_minutes"] <= 15:
            report.append("   ✅ 目標実行時間 (<15分) 達成!")

        report.append("\n" + "="*80)
        report.append("🤖 Generated by CI Integration Tester")

        return "\n".join(report)

    def run_integration_test(self):
        """統合テスト実行"""
        print("🧪 CI/CD統合テスト開始")
        print("=" * 60)

        # 実行履歴取得
        runs = self.get_recent_runs(30)

        if not runs:
            print("❌ ワークフロー実行履歴を取得できませんでした")
            return False

        # 性能分析
        stats = self.analyze_workflow_performance(runs)

        # ヘルスチェック
        health = self.check_workflow_health(stats)

        # レポート生成
        report = self.generate_report(stats, health)

        # レポート表示
        print(report)

        # ファイル出力
        report_path = self.project_root / "tmp" / f"ci_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path.write_text(report, encoding='utf-8')
        print(f"\n📄 詳細レポート: {report_path}")

        # 結果判定
        success = health["overall_status"] in ["healthy", "warning"]

        if success:
            print("\n✅ CI/CD統合テスト: PASS")
        else:
            print("\n❌ CI/CD統合テスト: FAIL")

        return success


def main():
    """メイン実行関数"""
    print("🧪 CI/CD統合テスト・モニタリングツール - Issue #971")
    print("GitHub Actions統合テストとパフォーマンス測定を実行します")

    tester = CIIntegrationTester()
    success = tester.run_integration_test()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
