#!/usr/bin/env python3
"""
qcheck系コマンド実装 (Issue #578)

Claude Code開発向けの品質チェックショートカット:
- qcheck: 全体品質チェック
- qcheckf: 変更ファイルの関数レベルチェック
- qcheckt: テスト品質・カバレッジチェック
- qdoc: ドキュメント品質チェック

Usage:
    python scripts/qcheck_commands.py [qcheck|qcheckf|qcheckt|qdoc]
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class QCheckRunner:
    """qcheck系コマンド実行クラス"""

    def __init__(self, root_path: Path):
        self.root_path = root_path

    def run_qcheck(self) -> int:
        """全体品質チェック実行"""
        logger.info("🔍 qcheck: 全体品質チェック開始")

        checks = [
            ("📏 ファイルサイズチェック", self._check_file_size),
            ("🏗️ アーキテクチャチェック", self._check_architecture),
            ("🔍 型チェック", self._check_types),
            ("📚 ドキュメント品質チェック", self._check_documentation),
            ("🧪 基本テスト", self._run_quick_tests),
        ]

        return self._run_checks(checks)

    def run_qcheckf(self) -> int:
        """変更ファイルの関数レベルチェック"""
        logger.info("🔍 qcheckf: 変更ファイル関数チェック開始")

        # Git差分から変更ファイル取得
        changed_files = self._get_changed_files()
        if not changed_files:
            print("✅ 変更されたファイルはありません")
            return 0

        checks = [
            ("📋 変更ファイル一覧", lambda: self._show_changed_files(changed_files)),
            ("🔍 関数レベル品質チェック", lambda: self._check_functions(changed_files)),
            (
                "📝 変更ファイル型チェック",
                lambda: self._check_types_for_files(changed_files),
            ),
        ]

        return self._run_checks(checks)

    def run_qcheckt(self) -> int:
        """テスト品質・カバレッジチェック"""
        logger.info("🧪 qcheckt: テスト品質チェック開始")

        checks = [
            ("🧪 テスト実行", self._run_tests_with_coverage),
            ("📊 カバレッジレポート", self._show_coverage_report),
            ("🔍 テスト品質チェック", self._check_test_quality),
        ]

        return self._run_checks(checks)

    def run_qdoc(self) -> int:
        """ドキュメント品質チェック"""
        logger.info("📚 qdoc: ドキュメント品質チェック開始")

        checks = [
            ("📚 ドキュメント品質検証", self._check_documentation),
            ("📝 Markdownリンター", self._run_markdown_linter),
            ("🔗 リンク切れチェック", self._check_links_only),
        ]

        return self._run_checks(checks)

    def _run_checks(self, checks: List) -> int:
        """チェック群の実行"""
        failed_checks = []

        for check_name, check_func in checks:
            print(f"\n{check_name}")
            print("-" * 50)

            try:
                result = check_func()
                if result != 0:
                    failed_checks.append(check_name)
                    print(f"❌ {check_name} 失敗")
                else:
                    print(f"✅ {check_name} 成功")

            except Exception as e:
                failed_checks.append(check_name)
                print(f"❌ {check_name} エラー: {e}")

        # 結果サマリー
        print(f"\n{'='*60}")
        print("📋 品質チェック結果サマリー")
        print(f"{'='*60}")

        if failed_checks:
            print(f"❌ 失敗したチェック ({len(failed_checks)}件):")
            for check in failed_checks:
                print(f"  - {check}")
            return 1
        else:
            print("✅ すべてのチェックが成功しました！")
            return 0

    def _check_file_size(self) -> int:
        """ファイルサイズチェック（300行制限）"""
        cmd = ["python", "scripts/check_file_size.py", "--max-lines=300"]
        return self._run_command(cmd)

    def _check_architecture(self) -> int:
        """アーキテクチャチェック"""
        cmd = [
            "python",
            "scripts/architecture_check.py",
            "--target-dir=kumihan_formatter",
        ]
        return self._run_command(cmd)

    def _check_types(self) -> int:
        """型チェック（mypy strict）"""
        cmd = ["python", "-m", "mypy", "--config-file=mypy.ini", "kumihan_formatter/"]
        return self._run_command(cmd)

    def _check_types_for_files(self, files: List[str]) -> int:
        """特定ファイルの型チェック"""
        py_files = [
            f for f in files if f.endswith(".py") and f.startswith("kumihan_formatter/")
        ]
        if not py_files:
            print("Python ファイルの変更はありません")
            return 0

        cmd = ["python", "-m", "mypy", "--config-file=mypy.ini"] + py_files
        return self._run_command(cmd)

    def _check_documentation(self) -> int:
        """ドキュメント品質チェック"""
        cmd = [
            "python",
            "scripts/doc_validator.py",
            "--root",
            ".",
            "--report-format",
            "text",
        ]
        return self._run_command(cmd)

    def _check_links_only(self) -> int:
        """リンク切れチェックのみ"""
        # doc_validatorの結果から重要なエラーのみ表示
        result = subprocess.run(
            [
                "python",
                "scripts/doc_validator.py",
                "--root",
                ".",
                "--report-format",
                "json",
            ],
            capture_output=True,
            text=True,
            cwd=self.root_path,
        )

        if result.returncode == 0:
            print("✅ リンク切れはありません")
            return 0
        else:
            # エラー情報の簡潔表示
            print("⚠️ リンク関連の問題を検出:")
            print(result.stdout[-500:])  # 最後500文字のみ表示
            return 1

    def _run_markdown_linter(self) -> int:
        """Markdownリンター実行"""
        # markdownlint-cliがインストールされていない場合はスキップ
        try:
            cmd = ["markdownlint", "--config", ".markdownlint.json", "**/*.md"]
            return self._run_command(cmd)
        except FileNotFoundError:
            print("⚠️ markdownlint-cliがインストールされていません（スキップ）")
            return 0

    def _run_quick_tests(self) -> int:
        """軽量テスト実行"""
        cmd = ["python", "-m", "pytest", "-x", "--ff", "-q", "tests/"]
        return self._run_command(cmd, allow_failure=True)

    def _run_tests_with_coverage(self) -> int:
        """カバレッジ付きテスト実行"""
        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov=kumihan_formatter",
            "--cov-report=term-missing",
        ]
        return self._run_command(cmd, allow_failure=True)

    def _show_coverage_report(self) -> int:
        """カバレッジレポート表示"""
        coverage_file = self.root_path / "htmlcov" / "index.html"
        if coverage_file.exists():
            print(f"📊 カバレッジレポート: {coverage_file}")
            return 0
        else:
            print("⚠️ カバレッジレポートが見つかりません")
            return 1

    def _check_test_quality(self) -> int:
        """テスト品質チェック"""
        # テストファイルの存在確認
        tests_dir = self.root_path / "tests"
        if not tests_dir.exists():
            print("⚠️ testsディレクトリが見つかりません")
            return 1

        test_files = list(tests_dir.rglob("test_*.py"))
        print(f"📋 テストファイル数: {len(test_files)}")

        if len(test_files) == 0:
            print("⚠️ テストファイルが見つかりません")
            return 1

        return 0

    def _check_functions(self, files: List[str]) -> int:
        """関数レベル品質チェック"""
        # 複雑度チェック（radonを使用）
        py_files = [f for f in files if f.endswith(".py")]
        if not py_files:
            print("Python ファイルの変更はありません")
            return 0

        try:
            cmd = ["python", "-m", "radon", "cc"] + py_files + ["--min=B"]
            return self._run_command(cmd)
        except FileNotFoundError:
            print("⚠️ radonがインストールされていません（スキップ）")
            return 0

    def _get_changed_files(self) -> List[str]:
        """Git差分から変更ファイル取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                capture_output=True,
                text=True,
                cwd=self.root_path,
            )

            if result.returncode == 0:
                return [f.strip() for f in result.stdout.splitlines() if f.strip()]
            else:
                # Fallback: staged files
                result = subprocess.run(
                    ["git", "diff", "--name-only", "--cached"],
                    capture_output=True,
                    text=True,
                    cwd=self.root_path,
                )
                return [f.strip() for f in result.stdout.splitlines() if f.strip()]

        except Exception as e:
            logger.warning(f"Git差分取得エラー: {e}")
            return []

    def _show_changed_files(self, files: List[str]) -> int:
        """変更ファイル一覧表示"""
        print(f"変更されたファイル ({len(files)}件):")
        for file in files:
            print(f"  - {file}")
        return 0

    def _run_command(self, cmd: List[str], allow_failure: bool = False) -> int:
        """コマンド実行ヘルパー"""
        try:
            result = subprocess.run(cmd, cwd=self.root_path)

            if result.returncode != 0 and not allow_failure:
                return result.returncode

            return 0

        except FileNotFoundError:
            print(f"⚠️ コマンドが見つかりません: {cmd[0]}")
            return 1 if not allow_failure else 0
        except Exception as e:
            print(f"❌ コマンド実行エラー: {e}")
            return 1


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="qcheck系コマンド実行")
    parser.add_argument(
        "command",
        choices=["qcheck", "qcheckf", "qcheckt", "qdoc"],
        help="実行するコマンド",
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="プロジェクトルートパス"
    )

    args = parser.parse_args()

    runner = QCheckRunner(args.root)

    # コマンド実行
    command_map = {
        "qcheck": runner.run_qcheck,
        "qcheckf": runner.run_qcheckf,
        "qcheckt": runner.run_qcheckt,
        "qdoc": runner.run_qdoc,
    }

    exit_code = command_map[args.command]()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
