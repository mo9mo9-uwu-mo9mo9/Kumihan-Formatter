#!/usr/bin/env python3
"""
セキュリティチェックシステム - Issue #1239: 品質保証システム再構築
基本的なセキュリティ脆弱性検出
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List


class SecurityChecker:
    """セキュリティチェッククラス"""

    def __init__(self, src_dir: str = "kumihan_formatter"):
        self.src_dir = Path(src_dir)
        self.security_patterns = {
            "hardcoded_secrets": [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ],
            "dangerous_functions": [
                r"eval\s*\(",
                r"exec\s*\(",
                r"os\.system\s*\(",
                r"subprocess\.call\s*\([^)]*shell\s*=\s*True",
            ],
            "file_operations": [
                r'open\s*\([^)]*["\']w["\']',  # 潜在的な上書きリスク
                r"os\.remove\s*\(",
                r"shutil\.rmtree\s*\(",
            ],
        }

    def run_security_scan(self) -> Dict:
        """セキュリティスキャン実行"""
        print("🔒 セキュリティチェック開始")
        print("=" * 40)

        results = {"total_files": 0, "issues": [], "summary": {}}

        py_files = list(self.src_dir.glob("**/*.py"))
        results["total_files"] = len(py_files)

        for py_file in py_files:
            file_issues = self._check_file(py_file)
            if file_issues:
                results["issues"].extend(file_issues)

        # サマリー生成
        results["summary"] = self._generate_summary(results["issues"])
        self._print_results(results)

        return results

    def _check_file(self, file_path: Path) -> List[Dict]:
        """ファイル単位のセキュリティチェック"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()

            # パターンベースチェック
            for category, patterns in self.security_patterns.items():
                for pattern in patterns:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(
                                {
                                    "file": str(
                                        file_path.relative_to(self.src_dir.parent)
                                    ),
                                    "line": line_num,
                                    "category": category,
                                    "pattern": pattern,
                                    "content": line.strip(),
                                    "severity": self._get_severity(category),
                                }
                            )

        except (UnicodeDecodeError, IOError):
            pass  # ファイル読み込みエラーは無視

        return issues

    def _get_severity(self, category: str) -> str:
        """セキュリティ重要度判定"""
        severity_map = {
            "hardcoded_secrets": "HIGH",
            "dangerous_functions": "MEDIUM",
            "file_operations": "LOW",
        }
        return severity_map.get(category, "LOW")

    def _generate_summary(self, issues: List[Dict]) -> Dict:
        """結果サマリー生成"""
        summary = {
            "total_issues": len(issues),
            "high_severity": len([i for i in issues if i["severity"] == "HIGH"]),
            "medium_severity": len([i for i in issues if i["severity"] == "MEDIUM"]),
            "low_severity": len([i for i in issues if i["severity"] == "LOW"]),
            "categories": {},
        }

        # カテゴリ別集計
        for issue in issues:
            category = issue["category"]
            summary["categories"][category] = summary["categories"].get(category, 0) + 1

        return summary

    def _print_results(self, results: Dict):
        """結果表示"""
        summary = results["summary"]

        print(f"📊 スキャン結果: {results['total_files']} ファイル")
        print(f"🚨 発見された問題: {summary['total_issues']} 件")

        if summary["total_issues"] == 0:
            print("✅ セキュリティ問題は発見されませんでした")
            return

        # 重要度別表示
        print(f"  🔴 HIGH: {summary['high_severity']} 件")
        print(f"  🟡 MEDIUM: {summary['medium_severity']} 件")
        print(f"  🟢 LOW: {summary['low_severity']} 件")

        # 詳細表示（HIGHとMEDIUMのみ）
        high_medium_issues = [
            i for i in results["issues"] if i["severity"] in ["HIGH", "MEDIUM"]
        ]

        if high_medium_issues:
            print("\n🔍 要対応項目:")
            for issue in high_medium_issues[:10]:  # 最初の10件のみ
                severity_icon = "🔴" if issue["severity"] == "HIGH" else "🟡"
                print(f"  {severity_icon} {issue['file']}:{issue['line']}")
                print(f"    カテゴリ: {issue['category']}")
                print(f"    内容: {issue['content']}")
                print()

        # 推奨事項
        if summary["high_severity"] > 0:
            print("💡 推奨事項:")
            print("  - HIGHレベルの問題を優先的に修正してください")
            print("  - ハードコードされた秘密情報は環境変数に移動してください")


def main():
    """メイン処理"""
    checker = SecurityChecker()
    results = checker.run_security_scan()

    # 終了コード: HIGHがあれば1、なければ0
    exit_code = 1 if results["summary"]["high_severity"] > 0 else 0
    exit(exit_code)


if __name__ == "__main__":
    main()
