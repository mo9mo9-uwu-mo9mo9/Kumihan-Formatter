#!/usr/bin/env python3
"""
Claude Code 品質ゲートスクリプト

このスクリプトはClaude Codeが実装作業を行う前に必須品質チェックを実行し、
品質基準を満たさない場合は作業を停止させます。
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class QualityGate:
    """品質ゲートチェッカー"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.failed_checks: List[str] = []
        self.warnings: List[str] = []

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行して結果を返す"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5分タイムアウト
            )

            if result.returncode == 0:
                print(f"✅ {description}")
                return True, result.stdout
            else:
                print(f"❌ {description}")
                print(f"   Error: {result.stderr}")
                return False, result.stderr

        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - Timeout")
            return False, "Command timed out"
        except Exception as e:
            print(f"💥 {description} - Exception: {e}")
            return False, str(e)

    def check_linting(self) -> bool:
        """リントチェック"""
        print("🔍 Running linting checks...")

        # Black formatting check
        success, output = self.run_command(
            ["python3", "-m", "black", "--check", "kumihan_formatter/"],
            "Black formatting check",
        )
        if not success:
            self.failed_checks.append("Black formatting")

        # isort check
        success, output = self.run_command(
            ["python3", "-m", "isort", "--check-only", "kumihan_formatter/"],
            "isort import sorting check",
        )
        if not success:
            self.failed_checks.append("isort import sorting")

        # flake8 check
        success, output = self.run_command(
            ["python3", "-m", "flake8", "kumihan_formatter/", "--select=E9,F63,F7,F82"],
            "flake8 syntax check",
        )
        if not success:
            self.failed_checks.append("flake8 syntax")

        return len(self.failed_checks) == 0

    def check_typing(self) -> bool:
        """型チェック（mypy strict mode）- 段階的採用"""
        print("🔍 Running type checking with staged adoption...")

        # 段階的採用：既存の技術的負債ファイルを除外
        legacy_files_path = self.project_root / "technical_debt_legacy_files.txt"
        excluded_files = []

        if legacy_files_path.exists():
            with open(legacy_files_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        excluded_files.append(line)

        # 新規ファイルのみ厳格チェック
        if excluded_files:
            print(
                f"   📋 Excluding {len(excluded_files)} legacy files from strict checking"
            )
            # 除外ファイルをmypy設定で指定
            mypy_cmd = [
                "python3",
                "-m",
                "mypy",
                "--strict",
                "kumihan_formatter/",
            ]
            for excluded_file in excluded_files:
                mypy_cmd.extend(["--exclude", excluded_file])
        else:
            mypy_cmd = ["python3", "-m", "mypy", "--strict", "kumihan_formatter/"]

        success, output = self.run_command(
            mypy_cmd,
            "mypy strict mode type checking (staged adoption)",
        )

        if not success:
            self.failed_checks.append("mypy strict mode")
            print("🚨 Type checking failed!")
            print("   This is a BLOCKING error for Claude Code.")
            print("   Note: Legacy files are temporarily excluded from strict checks.")
            print(
                "   Please fix all type errors in new/modified files before proceeding."
            )

        return success

    def check_tests(self) -> bool:
        """テストチェック"""
        print("🧪 Running tests...")

        # Quick test run
        success, output = self.run_command(
            ["python3", "-m", "pytest", "tests/", "-v", "--tb=short", "-x"],
            "Quick test run (fail-fast)",
        )

        if not success:
            self.failed_checks.append("Tests")
            print("🚨 Tests failed!")
            print("   Please fix failing tests before proceeding.")

        return success

    def check_tdd_compliance(self) -> bool:
        """TDD準拠チェック"""
        print("🧪 Checking TDD compliance...")

        success, output = self.run_command(
            ["python3", "scripts/enforce_tdd.py", "kumihan_formatter/"],
            "TDD compliance check",
        )

        if not success:
            self.failed_checks.append("TDD compliance")
            print("🚨 TDD compliance failed!")
            print("   Please create tests before implementing functionality.")

        return success

    def check_architecture(self) -> bool:
        """アーキテクチャチェック"""
        print("🏗️ Checking architecture compliance...")

        # File size check
        success, output = self.run_command(
            ["python3", "scripts/check_file_size.py", "--max-lines=300"],
            "File size check (300 lines max)",
        )

        if not success:
            self.warnings.append("File size limits")
            print("⚠️  File size warning - some files exceed 300 lines")

        return True  # Non-blocking for now

    def run_full_check(self) -> bool:
        """完全な品質チェックを実行"""
        print("🚀 Claude Code Quality Gate")
        print("=" * 50)

        # 必須チェック（失敗するとブロック）
        mandatory_checks = [
            ("Linting", self.check_linting),
            ("Type Checking", self.check_typing),
            ("Tests", self.check_tests),
        ]

        # 推奨チェック（警告のみ）
        optional_checks = [
            ("TDD Compliance", self.check_tdd_compliance),
            ("Architecture", self.check_architecture),
        ]

        # 必須チェック実行
        all_passed = True
        for check_name, check_func in mandatory_checks:
            if not check_func():
                all_passed = False

        # 推奨チェック実行
        for check_name, check_func in optional_checks:
            check_func()

        print("\n" + "=" * 50)

        if all_passed:
            print("🎉 All quality checks passed!")
            print("✅ You may proceed with implementation.")

            if self.warnings:
                print("\n⚠️  Warnings:")
                for warning in self.warnings:
                    print(f"   - {warning}")

            return True
        else:
            print("🚨 Quality gate FAILED!")
            print("❌ The following checks failed:")
            for failed in self.failed_checks:
                print(f"   - {failed}")

            print("\n🛑 IMPLEMENTATION BLOCKED")
            print("   Please fix all issues before proceeding.")
            print("   Run 'make pre-commit' to fix most issues automatically.")

            return False


def main() -> None:
    """メイン処理"""
    project_root = Path(__file__).parent.parent

    print("🤖 Claude Code Quality Gate")
    print("   Ensuring code quality before implementation")
    print()

    quality_gate = QualityGate(project_root)

    if quality_gate.run_full_check():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
