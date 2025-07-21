#!/usr/bin/env python3
"""GitHub Actions CI/CD監視スクリプト

Issue #559対応: CI/CD実行状況の継続監視
GitHub Actions APIを使用してワークフロー実行状況を監視し、
問題の早期発見・報告を行う

使用方法:
    python scripts/monitor_github_actions.py [--repo REPO] [--branch BRANCH]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests library is required. Install with: pip install requests")
    sys.exit(1)


class GitHubActionsMonitor:
    """GitHub Actions監視クラス"""

    def __init__(self, repo: str, token: Optional[str] = None):
        """初期化

        Args:
            repo: リポジトリ名 (owner/repo形式)
            token: GitHub APIトークン (オプション)
        """
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.headers = {"Accept": "application/vnd.github.v3+json"}

        if token:
            self.headers["Authorization"] = f"token {token}"

    def get_workflow_runs(
        self, branch: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """ワークフロー実行履歴を取得

        Args:
            branch: ブランチ名 (オプション)
            limit: 取得する実行数

        Returns:
            ワークフロー実行情報のリスト
        """
        url = f"{self.api_base}/actions/runs"
        params = {"per_page": limit}

        if branch:
            params["branch"] = branch

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("workflow_runs", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workflow runs: {e}")
            return []

    def analyze_workflow_run(self, run: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフロー実行を分析

        Args:
            run: ワークフロー実行情報

        Returns:
            分析結果
        """
        created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
        duration = updated_at - created_at

        return {
            "id": run["id"],
            "name": run["name"],
            "status": run["status"],
            "conclusion": run["conclusion"],
            "branch": run["head_branch"],
            "commit": run["head_sha"][:7],
            "created_at": created_at,
            "updated_at": updated_at,
            "duration": duration,
            "url": run["html_url"],
        }

    def generate_report(
        self, runs: List[Dict[str, Any]], output_format: str = "text"
    ) -> str:
        """実行状況レポートを生成

        Args:
            runs: ワークフロー実行情報のリスト
            output_format: 出力形式 (text/json/markdown)

        Returns:
            レポート文字列
        """
        analyzed_runs = [self.analyze_workflow_run(run) for run in runs]

        if output_format == "json":
            return json.dumps(analyzed_runs, default=str, indent=2)

        elif output_format == "markdown":
            report = "# GitHub Actions CI/CD実行状況レポート\n\n"
            report += f"**リポジトリ**: {self.repo}\n"
            report += (
                f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            report += "## 最近の実行状況\n\n"
            report += (
                "| 状態 | ワークフロー | ブランチ | 実行時間 | コミット | リンク |\n"
            )
            report += (
                "|------|--------------|----------|----------|----------|--------|\n"
            )

            for run in analyzed_runs:
                status_emoji = self._get_status_emoji(run["status"], run["conclusion"])
                duration_str = str(run["duration"]).split(".")[0]
                report += f"| {status_emoji} | {run['name']} | {run['branch']} | "
                report += f"{duration_str} | {run['commit']} | "
                report += f"[詳細]({run['url']}) |\n"

            return report

        else:  # text format
            report = f"GitHub Actions CI/CD実行状況レポート\n"
            report += f"リポジトリ: {self.repo}\n"
            report += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += "=" * 80 + "\n\n"

            for run in analyzed_runs:
                status_emoji = self._get_status_emoji(run["status"], run["conclusion"])
                report += f"{status_emoji} {run['name']}\n"
                report += f"  ブランチ: {run['branch']}\n"
                report += f"  コミット: {run['commit']}\n"
                report += f"  状態: {run['status']}"
                if run["conclusion"]:
                    report += f" ({run['conclusion']})"
                report += f"\n  実行時間: {run['duration']}\n"
                report += f"  URL: {run['url']}\n\n"

            return report

    def _get_status_emoji(self, status: str, conclusion: Optional[str]) -> str:
        """ステータスに応じた絵文字を返す"""
        if status == "completed":
            if conclusion == "success":
                return "✅"
            elif conclusion == "failure":
                return "❌"
            elif conclusion == "cancelled":
                return "⚫"
            else:
                return "⚠️"
        elif status == "in_progress":
            return "🔄"
        else:
            return "⏸️"

    def check_failures(self, runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """失敗したワークフローを検出

        Args:
            runs: ワークフロー実行情報のリスト

        Returns:
            失敗したワークフローのリスト
        """
        failures = []
        for run in runs:
            if run.get("conclusion") == "failure":
                failures.append(self.analyze_workflow_run(run))
        return failures


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="GitHub Actions CI/CD監視スクリプト")
    parser.add_argument(
        "--repo",
        default="mo9mo9-uwu-mo9mo9/Kumihan-Formatter",
        help="リポジトリ名 (owner/repo形式)",
    )
    parser.add_argument("--branch", help="監視するブランチ名")
    parser.add_argument(
        "--limit", type=int, default=10, help="取得する実行数 (デフォルト: 10)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="出力形式",
    )
    parser.add_argument(
        "--check-failures",
        action="store_true",
        help="失敗したワークフローのみ表示",
    )

    args = parser.parse_args()

    # GitHubトークンを環境変数から取得
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN not set. API rate limits may apply.")

    # モニター初期化
    monitor = GitHubActionsMonitor(args.repo, token)

    # ワークフロー実行情報を取得
    runs = monitor.get_workflow_runs(branch=args.branch, limit=args.limit)

    if not runs:
        print("No workflow runs found.")
        return

    if args.check_failures:
        # 失敗したワークフローのみ表示
        failures = monitor.check_failures(runs)
        if failures:
            print(f"\n⚠️ {len(failures)} failed workflow(s) detected:\n")
            for failure in failures:
                print(
                    f"❌ {failure['name']} - {failure['branch']} ({failure['commit']})"
                )
                print(f"   URL: {failure['url']}\n")
            sys.exit(1)
        else:
            print("✅ No failed workflows detected.")
    else:
        # レポートを生成・表示
        report = monitor.generate_report(runs, output_format=args.format)
        print(report)


if __name__ == "__main__":
    main()
