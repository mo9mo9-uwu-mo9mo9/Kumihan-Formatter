#!/usr/bin/env python3
"""Test protection guard for Kumihan-Formatter

テスト大量削除防止機能:
- コミット前にテストファイルの削除チェック
- 意図しないテスト削除をブロック
- 安全なテスト変更のみ許可

Usage:
    python scripts/test_guard.py --check-staged
    python scripts/test_guard.py --backup-tests
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class TestGuard:
    """テスト保護クラス"""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path.cwd()
        self.tests_dir = self.repo_root / "tests"
        self.backup_dir = self.repo_root / ".test_backups"
        self.guard_log = self.repo_root / ".test_guard.log"

        # テスト保護設定
        self.protection_config: Dict[str, Any] = {
            "max_deletions_allowed": 3,
            "min_test_files_required": 20,
            "protected_patterns": [
                "test_config_manager.py",
                "test_error_handling.py",
                "test_conversion_controller.py",
                "test_file_controller.py",
                "test_gui_controller.py",
            ],
            "deletion_warning_threshold": 1,
        }

    def log_action(self, action: str, details: str = "") -> None:
        """ガード動作ログ"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {action}: {details}\n"

        with open(self.guard_log, "a", encoding="utf-8") as f:
            f.write(log_entry)

        print(f"🛡️  {action}: {details}")

    def get_staged_test_files(self) -> Tuple[List[str], List[str], List[str]]:
        """ステージングされたテストファイルの変更を取得"""
        try:
            # ステージングされた変更を取得
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-status"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )

            if result.returncode != 0:
                self.log_action("ERROR", f"git diff failed: {result.stderr}")
                return [], [], []

            added = []
            modified = []
            deleted = []

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                # スペースまたはタブで分割（git diff --name-statusの出力形式対応）
                parts = line.split(None, 1)  # 最大1回分割
                if len(parts) != 2:
                    continue

                status, filepath = parts

                # テストファイルのみ処理
                if not filepath.startswith("tests/") or not filepath.endswith(".py"):
                    continue

                if status.startswith("A"):
                    added.append(filepath)
                elif status.startswith("M"):
                    modified.append(filepath)
                elif status.startswith("D"):
                    deleted.append(filepath)

            return added, modified, deleted

        except Exception as e:
            self.log_action("ERROR", f"Failed to get staged files: {e}")
            return [], [], []

    def check_protected_files(self, deleted_files: List[str]) -> List[str]:
        """保護対象ファイルの削除チェック"""
        protected_violations = []

        for deleted_file in deleted_files:
            filename = Path(deleted_file).name

            for pattern in self.protection_config["protected_patterns"]:
                if pattern in filename:
                    protected_violations.append(deleted_file)
                    break

        return protected_violations

    def validate_test_deletion(self, deleted_files: List[str]) -> Tuple[bool, str]:
        """テスト削除の妥当性チェック"""
        if not deleted_files:
            return True, "No test deletions detected"

        deletion_count = len(deleted_files)
        max_allowed = self.protection_config["max_deletions_allowed"]

        # 大量削除チェック
        if deletion_count > max_allowed:
            return False, f"Too many test deletions: {deletion_count} > {max_allowed}"

        # 保護ファイルチェック
        protected_violations = self.check_protected_files(deleted_files)
        if protected_violations:
            return False, f"Protected files cannot be deleted: {protected_violations}"

        # 最小ファイル数チェック
        current_test_count = len(list(self.tests_dir.glob("test_*.py")))
        after_deletion = current_test_count - deletion_count
        min_required = self.protection_config["min_test_files_required"]

        if after_deletion < min_required:
            return (
                False,
                f"Would reduce test files below minimum: {after_deletion} < {min_required}",
            )

        # 警告レベルの削除
        warning_threshold = self.protection_config["deletion_warning_threshold"]
        if deletion_count >= warning_threshold:
            return (
                True,
                f"WARNING: {deletion_count} test files will be deleted: {deleted_files}",
            )

        return True, f"Test deletion approved: {deletion_count} files"

    def backup_tests(self) -> bool:
        """テストファイルのバックアップ"""
        try:
            if not self.tests_dir.exists():
                self.log_action("ERROR", "Tests directory not found")
                return False

            # バックアップディレクトリ作成
            self.backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backup_dir / f"backup_{timestamp}"
            backup_subdir.mkdir()

            # テストファイルをコピー
            test_files = list(self.tests_dir.glob("test_*.py"))

            for test_file in test_files:
                backup_file = backup_subdir / test_file.name
                backup_file.write_text(
                    test_file.read_text(encoding="utf-8"), encoding="utf-8"
                )

            # バックアップ情報保存
            backup_info = {
                "timestamp": timestamp,
                "file_count": len(test_files),
                "files": [f.name for f in test_files],
                "git_commit": self.get_current_commit(),
            }

            info_file = backup_subdir / "backup_info.json"
            info_file.write_text(json.dumps(backup_info, indent=2), encoding="utf-8")

            self.log_action(
                "BACKUP",
                f"Created backup with {len(test_files)} files in {backup_subdir}",
            )
            return True

        except Exception as e:
            self.log_action("ERROR", f"Backup failed: {e}")
            return False

    def get_current_commit(self) -> str:
        """現在のコミットハッシュ取得"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    def check_staged_changes(self) -> bool:
        """ステージングされた変更のチェック"""
        self.log_action("CHECK", "Starting staged changes validation")

        added, modified, deleted = self.get_staged_test_files()

        self.log_action(
            "ANALYSIS",
            f"Added: {len(added)}, Modified: {len(modified)}, Deleted: {len(deleted)}",
        )

        if added:
            self.log_action("INFO", f"Test files added: {added}")

        if modified:
            self.log_action("INFO", f"Test files modified: {modified}")

        if deleted:
            self.log_action("WARNING", f"Test files to be deleted: {deleted}")

            # 削除妥当性チェック
            is_valid, message = self.validate_test_deletion(deleted)
            self.log_action("VALIDATION", message)

            if not is_valid:
                self.log_action(
                    "BLOCKED", "Commit blocked due to test deletion policy violation"
                )
                print("\n❌ COMMIT BLOCKED:")
                print(f"   {message}")
                print("\nTo fix this:")
                print("1. Restore accidentally deleted test files")
                print("2. If deletion is intentional, update protection config")
                print("3. Contact maintainer for protected file changes")
                return False

            elif "WARNING" in message:
                print(f"\n⚠️  {message}")
                print("Proceeding with caution...")

        self.log_action("APPROVED", "Staged changes approved")
        return True

    def show_status(self) -> None:
        """現在の保護状況表示"""
        current_tests = list(self.tests_dir.glob("test_*.py"))

        print(f"\n🛡️  Test Guard Status:")
        print(f"   Current test files: {len(current_tests)}")
        print(
            f"   Minimum required: {self.protection_config['min_test_files_required']}"
        )
        print(
            f"   Max deletions allowed: {self.protection_config['max_deletions_allowed']}"
        )
        print(
            f"   Protected patterns: {len(self.protection_config['protected_patterns'])}"
        )

        if self.backup_dir.exists():
            backups = list(self.backup_dir.glob("backup_*"))
            print(f"   Available backups: {len(backups)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test Guard - Prevent accidental test deletion"
    )
    parser.add_argument(
        "--check-staged", action="store_true", help="Check staged changes"
    )
    parser.add_argument(
        "--backup-tests", action="store_true", help="Backup current tests"
    )
    parser.add_argument("--status", action="store_true", help="Show protection status")

    args = parser.parse_args()

    guard = TestGuard()

    if args.backup_tests:
        success = guard.backup_tests()
        sys.exit(0 if success else 1)

    elif args.check_staged:
        success = guard.check_staged_changes()
        sys.exit(0 if success else 1)

    elif args.status:
        guard.show_status()
        sys.exit(0)

    else:
        print("Use --help for usage information")
        guard.show_status()
        sys.exit(0)


if __name__ == "__main__":
    main()
