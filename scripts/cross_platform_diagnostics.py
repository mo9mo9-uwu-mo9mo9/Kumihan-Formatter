#!/usr/bin/env python3
"""
クロスプラットフォームテスト失敗診断スクリプト - Issue #610対応
macOS/Windows環境でのテスト失敗原因を調査・修正
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


class CrossPlatformDiagnostics:
    """クロスプラットフォーム問題診断クラス"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.platform_info = self._get_platform_info()
        self.known_issues = self._load_known_issues()

    def _get_platform_info(self) -> Dict[str, str]:
        """プラットフォーム情報取得"""
        return {
            "system": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "encoding": sys.getdefaultencoding(),
            "filesystem_encoding": sys.getfilesystemencoding(),
        }

    def _load_known_issues(self) -> Dict[str, List[str]]:
        """既知のプラットフォーム問題"""
        return {
            "Windows": [
                "パス区切り文字（\\\\）の問題",
                "ファイルパーミッション制限",
                "改行コード（CRLF）の違い",
                "大文字小文字の区別",
                "長いパス名制限",
                "プロセス起動方法の違い",
            ],
            "Darwin": [  # macOS
                "ファイルシステムの大文字小文字設定",
                "一時ディレクトリパスの違い",
                "プロセス制限の違い",
                "Unicode正規化の違い",
                "隠しファイル処理",
            ],
        }

    def diagnose_test_failures(
        self, test_pattern: Optional[str] = None
    ) -> Dict[str, any]:
        """テスト失敗の診断実行"""
        # Windows環境で絵文字エラーを避けるため、ASCII文字を使用
        try:
            print(f"🔍 プラットフォーム診断開始: {self.platform_info['system']}")
        except UnicodeEncodeError:
            print(
                f"[DEBUG] Platform diagnostics starting: {self.platform_info['system']}"
            )

        results = {
            "platform": self.platform_info,
            "test_results": {},
            "file_system_issues": [],
            "encoding_issues": [],
            "path_issues": [],
            "recommendations": [],
        }

        # 1. ファイルシステム問題の検査
        results["file_system_issues"] = self._check_filesystem_issues()

        # 2. エンコーディング問題の検査
        results["encoding_issues"] = self._check_encoding_issues()

        # 3. パス問題の検査
        results["path_issues"] = self._check_path_issues()

        # 4. 問題のあるテストの特定
        results["test_results"] = self._identify_problematic_tests(test_pattern)

        # 5. 推奨対応策
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _check_filesystem_issues(self) -> List[Dict[str, str]]:
        """ファイルシステム問題チェック"""
        issues = []

        # 大文字小文字の区別チェック
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                test_file1 = Path(tmp_dir) / "TEST.txt"
                test_file2 = Path(tmp_dir) / "test.txt"

                test_file1.write_text("upper")
                test_file2.write_text("lower")

                if test_file1.read_text() == test_file2.read_text():
                    issues.append(
                        {
                            "type": "case_insensitive_filesystem",
                            "description": "ファイルシステムが大文字小文字を区別しない",
                            "impact": "同名の大文字小文字ファイルが競合する可能性",
                        }
                    )
        except Exception as e:
            issues.append(
                {
                    "type": "filesystem_test_error",
                    "description": f"ファイルシステムテストエラー: {e}",
                    "impact": "ファイル操作に問題がある可能性",
                }
            )

        # 長いパス名チェック（Windows）
        if self.platform_info["system"] == "Windows":
            try:
                long_path = "a" * 250
                long_file = Path(tempfile.gettempdir()) / f"{long_path}.txt"
                long_file.write_text("test")
                long_file.unlink()
            except Exception:
                issues.append(
                    {
                        "type": "long_path_limitation",
                        "description": "Windowsの長いパス名制限",
                        "impact": "深い階層のテストファイルでエラーが発生する可能性",
                    }
                )

        return issues

    def _check_encoding_issues(self) -> List[Dict[str, str]]:
        """エンコーディング問題チェック"""
        issues = []

        # 日本語ファイル名チェック
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                japanese_file = Path(tmp_dir) / "テスト.txt"
                japanese_file.write_text("日本語コンテンツ", encoding="utf-8")
                content = japanese_file.read_text(encoding="utf-8")

                if content != "日本語コンテンツ":
                    issues.append(
                        {
                            "type": "japanese_encoding_issue",
                            "description": "日本語エンコーディング問題",
                            "impact": "日本語を含むテストでエラーが発生する可能性",
                        }
                    )
        except Exception as e:
            issues.append(
                {
                    "type": "encoding_test_error",
                    "description": f"エンコーディングテストエラー: {e}",
                    "impact": "文字エンコーディングに問題がある可能性",
                }
            )

        return issues

    def _check_path_issues(self) -> List[Dict[str, str]]:
        """パス問題チェック"""
        issues = []

        # パス区切り文字チェック
        if self.platform_info["system"] == "Windows":
            test_path = "kumihan_formatter/core/parser.py"
            if "\\" not in str(Path(test_path)):
                issues.append(
                    {
                        "type": "path_separator_issue",
                        "description": "パス区切り文字の不一致",
                        "impact": "Windowsでのパス処理でエラーが発生する可能性",
                    }
                )

        return issues

    def _identify_problematic_tests(
        self, test_pattern: Optional[str] = None
    ) -> Dict[str, any]:
        """問題のあるテストの特定"""
        print("🧪 問題テストの特定中...")

        # プラットフォーム固有で失敗しやすいテストパターン
        platform_sensitive_patterns = [
            "**/test_*file*",  # ファイル操作テスト
            "**/test_*path*",  # パス処理テスト
            "**/test_*io*",  # IO操作テスト
            "**/test_*temp*",  # 一時ファイルテスト
        ]

        results = {}

        for pattern in platform_sensitive_patterns:
            try:
                # 該当テストの収集
                cmd = [
                    "python",
                    "-m",
                    "pytest",
                    "--collect-only",
                    "-q",
                    "--ignore=tests/gui/",  # GUI tests skip
                    pattern,
                ]

                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    test_count = len(
                        [
                            line
                            for line in result.stdout.split("\n")
                            if "test session starts" not in line and line.strip()
                        ]
                    )
                    results[pattern] = {"test_count": test_count, "status": "collected"}
                else:
                    results[pattern] = {
                        "error": result.stderr,
                        "status": "collection_failed",
                    }

            except subprocess.TimeoutExpired:
                results[pattern] = {"error": "Collection timeout", "status": "timeout"}
            except Exception as e:
                results[pattern] = {"error": str(e), "status": "error"}

        return results

    def _generate_recommendations(self, results: Dict[str, any]) -> List[str]:
        """推奨対応策生成"""
        recommendations = []

        # プラットフォーム固有の推奨事項
        if self.platform_info["system"] in self.known_issues:
            recommendations.append(
                f"{self.platform_info['system']}固有の既知問題を確認してください"
            )

        # ファイルシステム問題の対応
        if results["file_system_issues"]:
            recommendations.extend(
                [
                    "テストでのファイル操作をPathlib使用に統一",
                    "一時ファイル作成はtempfileモジュール使用",
                    "プラットフォーム固有のテストはマーカーで分離",
                ]
            )

        # エンコーディング問題の対応
        if results["encoding_issues"]:
            recommendations.extend(
                [
                    "ファイル操作時は明示的にencoding='utf-8'指定",
                    "日本語を含むテストケースの見直し",
                ]
            )

        # パス問題の対応
        if results["path_issues"]:
            recommendations.extend(
                ["os.path使用をpathlibに移行", "パス区切り文字をPATH.joinpath()で統一"]
            )

        return recommendations

    def generate_platform_markers(self) -> str:
        """プラットフォーム別テストマーカー設定生成"""
        return """
# プラットフォーム別テストマーカー - Issue #610対応
markers = [
    "unit: Unit tests - fast, isolated tests",
    "integration: Integration tests - tests component interactions",
    "e2e: End-to-end tests - full system tests",
    "slow: Slow running tests (>1s)",
    "performance: Performance benchmark tests",
    "gui: GUI-related tests requiring display",
    "skip_ci: Tests to skip in CI environment",
    # プラットフォーム固有マーカー
    "windows_only: Tests that only run on Windows",
    "macos_only: Tests that only run on macOS",
    "linux_only: Tests that only run on Linux",
    "unix_like: Tests for Unix-like systems (macOS/Linux)",
    "file_sensitive: Tests sensitive to filesystem differences",
    "encoding_sensitive: Tests sensitive to encoding differences",
    "path_sensitive: Tests sensitive to path handling differences",
]
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description="クロスプラットフォーム問題診断")
    parser.add_argument("--test-pattern", help="診断対象のテストパターン")
    parser.add_argument("--output", help="結果出力ファイル（JSON）")

    args = parser.parse_args()

    diagnostics = CrossPlatformDiagnostics()
    results = diagnostics.diagnose_test_failures(args.test_pattern)

    # 結果表示
    print("\n📊 診断結果:")
    print(f"プラットフォーム: {results['platform']['system']}")
    print(f"ファイルシステム問題: {len(results['file_system_issues'])}件")
    print(f"エンコーディング問題: {len(results['encoding_issues'])}件")
    print(f"パス問題: {len(results['path_issues'])}件")

    print("\n💡 推奨対応策:")
    for rec in results["recommendations"]:
        print(f"  - {rec}")

    # JSON出力
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 詳細結果を {args.output} に出力しました")

    # プラットフォームマーカー設定出力
    print("\n🏷️ 推奨pytest.ini追加設定:")
    print(diagnostics.generate_platform_markers())


if __name__ == "__main__":
    main()
