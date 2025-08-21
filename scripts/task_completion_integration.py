#!/usr/bin/env python3
"""
Issue完了フロー統合スクリプト
Issue #686 Phase 3: 持続可能運用 - Issue完了時のCLAUDE.md自動最適化
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class IssueInfo:
    """Issue情報"""

    number: int
    title: str
    status: str
    completion_date: str


class TaskCompletionIntegrator:
    """Issue完了フロー統合システム"""

    def __init__(self, claude_md_path: str = "CLAUDE.md"):
        self.claude_md_path = claude_md_path

    def process_completed_issue(self, issue_number: int) -> Dict:
        """Issue完了処理"""
        # GitHub CLI でIssue情報取得
        issue_info = self._get_issue_info(issue_number)
        if not issue_info:
            return {"status": "error", "message": f"Issue #{issue_number} not found"}

        results = {}

        # CLAUDE.md内のIssue参照を簡潔化
        results["simplification"] = self._simplify_issue_references(issue_info)

        # 完了したPhase情報を履歴化
        results["archival"] = self._archive_completed_phases(issue_info)

        # 重複・不要情報削除
        results["cleanup"] = self._cleanup_outdated_content(issue_info)

        # サイズ最適化
        results["optimization"] = self._optimize_size()

        return {
            "status": "success",
            "issue": issue_info,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def _get_issue_info(self, issue_number: int) -> Optional[IssueInfo]:
        """GitHub CLI でIssue情報取得"""
        try:
            # gh コマンドでIssue情報取得
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(issue_number),
                    "--json",
                    "number,title,state,closedAt",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            data = json.loads(result.stdout)

            return IssueInfo(
                number=data["number"],
                title=data["title"],
                status=data["state"],
                completion_date=data.get("closedAt", datetime.now().isoformat()),
            )
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            return None

    def _simplify_issue_references(self, issue_info: IssueInfo) -> List[str]:
        """Issue参照の簡潔化"""
        if not os.path.exists(self.claude_md_path):
            return ["CLAUDE.md not found"]

        with open(self.claude_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        changes = []
        original_content = content

        # Issue番号参照パターン
        issue_patterns = [
            f"Issue #{issue_info.number}",
            f"Issue#{issue_info.number}",
            f"#Issue{issue_info.number}",
            f"#{issue_info.number}",
        ]

        for pattern in issue_patterns:
            # 詳細な説明を簡潔な完了記録に変更
            detailed_pattern = rf"{re.escape(pattern)}[^#]*?(?=\n|$)"
            if re.search(detailed_pattern, content, re.MULTILINE | re.DOTALL):
                # 詳細説明を簡潔な完了記録に置換
                completion_note = (
                    f"{pattern} ✅ 完了 ({issue_info.completion_date[:10]})"
                )
                content = re.sub(
                    detailed_pattern,
                    completion_note,
                    content,
                    flags=re.MULTILINE | re.DOTALL,
                )
                changes.append(f"Issue #{issue_info.number} 参照を簡潔化")

        if content != original_content:
            with open(self.claude_md_path, "w", encoding="utf-8") as f:
                f.write(content)

        return changes

    def _archive_completed_phases(self, issue_info: IssueInfo) -> List[str]:
        """完了Phase情報の履歴化"""
        if not os.path.exists(self.claude_md_path):
            return ["CLAUDE.md not found"]

        with open(self.claude_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        changes = []
        original_content = content

        # Phase完了パターン検出
        phase_patterns = [
            r"Phase \d+[^#]*?完了",
            r"Phase \d+[^#]*?実装済み",
            r"Phase \d+[^#]*?対応完了",
        ]

        for pattern in phase_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # 詳細をhistoryセクションに移動（簡略化）
                if "履歴" not in content and "history" not in content.lower():
                    # 履歴セクションがなければ作成
                    history_section = f"\n\n## 📚 実装履歴\n\n- {match} ({datetime.now().strftime('%Y-%m-%d')})\n"
                    content += history_section
                    changes.append("実装履歴セクション作成")

                # 元の詳細説明を削除し、簡潔な参照に置換
                content = content.replace(match, f"{match.split()[0:2]} ✅")
                changes.append(f"{match[:30]}... を履歴化")

        if content != original_content:
            with open(self.claude_md_path, "w", encoding="utf-8") as f:
                f.write(content)

        return changes

    def _cleanup_outdated_content(self, issue_info: IssueInfo) -> List[str]:
        """古い・不要情報の削除"""
        if not os.path.exists(self.claude_md_path):
            return ["CLAUDE.md not found"]

        with open(self.claude_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        changes = []
        original_content = content

        # 削除対象パターン
        cleanup_patterns = [
            r"TODO[^\n]*",
            r"FIXME[^\n]*",
            r"実装予定[^\n]*",
            r"未実装[^\n]*",
            r"検討中[^\n]*",
        ]

        for pattern in cleanup_patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, "", content)
                changes.extend([f"削除: {match[:30]}..." for match in matches])

        # 空行正規化
        content = re.sub(r"\n{3,}", "\n\n", content)

        if content != original_content:
            with open(self.claude_md_path, "w", encoding="utf-8") as f:
                f.write(content)

            if not changes:
                changes.append("空行正規化")

        return changes

    def _optimize_size(self) -> List[str]:
        """サイズ最適化"""
        if not os.path.exists(self.claude_md_path):
            return ["CLAUDE.md not found"]

        try:
            # claude_md_manager.py の最適化機能を使用
            from claude_md_manager import CLAUDEmdManager

            manager = CLAUDEmdManager(self.claude_md_path)
            suggestions = manager.optimize(auto_fix=False)  # 安全性重視で手動確認

            return suggestions
        except ImportError:
            return ["最適化スクリプトが見つかりません"]

    def integrate_with_release_cycle(self, version: str) -> Dict:
        """リリースサイクル統合"""
        results = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "actions": [],
        }

        if not os.path.exists(self.claude_md_path):
            results["actions"].append("CLAUDE.md not found")
            return results

        with open(self.claude_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # バージョン情報更新
        version_pattern = r"バージョン.*?\d+\.\d+\.\d+[^\n]*"
        new_version_line = (
            f"**バージョン**: {version} ({datetime.now().strftime('%Y-%m-%d')})"
        )

        if re.search(version_pattern, content):
            content = re.sub(version_pattern, new_version_line, content)
            results["actions"].append(f"バージョン情報を {version} に更新")

        # 古いバージョンの詳細情報を履歴セクションに移動
        old_version_details = []
        # 実装のため簡略化: 具体的なバージョン履歴移動ロジックは省略

        with open(self.claude_md_path, "w", encoding="utf-8") as f:
            f.write(content)

        return results


def main():
    """CLI エントリーポイント"""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Issue Completion Integration")
    parser.add_argument("command", choices=["process-issue", "release-integration"])
    parser.add_argument("--issue", type=int, help="Issue番号")
    parser.add_argument("--version", help="リリースバージョン")
    parser.add_argument("--output", help="結果出力ファイル")

    args = parser.parse_args()

    integrator = TaskCompletionIntegrator()

    try:
        if args.command == "process-issue":
            if not args.issue:
                print("❌ Issue番号が必要です", file=sys.stderr)
                sys.exit(1)

            result = integrator.process_completed_issue(args.issue)

            if result["status"] == "success":
                print(f"✅ Issue #{args.issue} 処理完了")
                for category, changes in result["results"].items():
                    if changes:
                        print(f"📋 {category.title()}:")
                        for change in changes:
                            print(f"   - {change}")
            else:
                print(f"❌ {result['message']}")
                sys.exit(1)

        elif args.command == "release-integration":
            if not args.version:
                print("❌ バージョンが必要です", file=sys.stderr)
                sys.exit(1)

            result = integrator.integrate_with_release_cycle(args.version)

            print(f"🚀 Release {args.version} 統合完了")
            for action in result["actions"]:
                print(f"   - {action}")

        if args.output:
            # tmp/配下にファイル出力
            tmp_dir = Path("tmp")
            tmp_dir.mkdir(exist_ok=True)
            output_path = tmp_dir / Path(args.output).name

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"📄 結果を {output_path} に保存しました")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
