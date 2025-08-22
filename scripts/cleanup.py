#!/usr/bin/env python3
"""
ファイル整理システム - 不要ファイル自動削除ツール

このスクリプトは設定可能なパターンに基づいて不要ファイルを検出・削除します。
ドライラン機能、対話モード、設定ファイル対応を含みます。

使用例:
    python scripts/cleanup.py --dry-run        # ドライラン
    python scripts/cleanup.py --interactive    # 対話モード
    python scripts/cleanup.py --auto          # 自動実行
    python scripts/cleanup.py --config custom.yml  # カスタム設定
"""

import argparse
import glob
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Union

import yaml

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class FileCleanup:
    """ファイルクリーンアップシステム"""

    def __init__(self, config_path: str = ".cleanup.yml"):
        """
        初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.deleted_files: List[str] = []
        self.deleted_size = 0

    def _load_config(self) -> Dict:
        """設定ファイルを読み込み"""
        default_config = {
            "cleanup_patterns": [
                # 大容量テストファイル
                "*k_test_file.*",
                "*mb_test_file.*",
                "*gb_test_file.*",
                "large_test_*",
                "huge_test_*",
                "massive_test_*",
                "benchmark_test_*",
                # レポートファイル
                "*_report_*.json",
                "*_report_*.md",
                "*_report_*.txt",
                "*_report_*.html",
                "*_報告書_*.md",
                "*_Final_Report.*",
                "Issue_*_Complete_*.md",
                "behavioral_control_*.json",
                "rule_compliance_*.json",
                "token-usage-report.*",
                # 一時実行ファイル
                "temp_*",
                "tmp_*",
                "test_temp_*",
                "temp_test_*",
                "test_output_*",
                "performance_test_*",
                "benchmark_output_*",
                "debug_output_*",
                # プロファイリングファイル
                "*.prof",
                "*.cprof",
                "profiling_*",
                "memory_profile_*",
                # ログファイル（注意して削除）
                "debug.log",
                "test.log",
                # キャッシュファイル
                "cache_*",
                "*.cache",
                # バックアップファイル
                "*.bak",
                "*.backup",
                "backup_*",
                # 生成されたファイル
                "generated_*",
                "auto_generated_*",
                "*.generated.*",
                "output_*",
                "result_*",
            ],
            "cleanup_directories": [".temp", ".tmp", ".cache", ".backup", "logs"],
            "exclude_patterns": [
                ".git/*",
                ".github/*",
                "node_modules/*",
                "venv/*",
                ".venv/*",
                "*.py",
                "*.md",
                "Makefile",
                "pyproject.toml",
                "*.yml",
                "*.yaml",
            ],
            "safe_mode": True,
            "max_file_size_mb": 100,
            "min_age_days": 1,
        }

        if not os.path.exists(self.config_path):
            logger.info(
                f"設定ファイル {self.config_path} が見つからないため、デフォルト設定を使用"
            )
            return default_config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                # デフォルト設定にユーザー設定をマージ
                default_config.update(user_config)
                return default_config
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return default_config

    def _get_file_age_days(self, file_path: str) -> float:
        """ファイルの作成からの経過日数を取得"""
        try:
            stat = os.stat(file_path)
            age_seconds = time.time() - stat.st_ctime
            return age_seconds / (24 * 3600)
        except OSError:
            return 0

    def _get_file_size_mb(self, file_path: str) -> float:
        """ファイルサイズ（MB）を取得"""
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except OSError:
            return 0

    def _should_exclude(self, file_path: str) -> bool:
        """除外パターンに一致するかチェック"""
        for pattern in self.config.get("exclude_patterns", []):
            if glob.fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _find_cleanup_files(self) -> List[str]:
        """クリーンアップ対象ファイルを検出"""
        cleanup_files = []
        project_root = Path.cwd()

        # パターンマッチングでファイル検出
        for pattern in self.config.get("cleanup_patterns", []):
            matches = glob.glob(str(project_root / pattern), recursive=True)
            for match in matches:
                if os.path.isfile(match) and not self._should_exclude(match):
                    # セーフモードでのチェック
                    if self.config.get("safe_mode", True):
                        file_age = self._get_file_age_days(match)
                        file_size = self._get_file_size_mb(match)
                        min_age = self.config.get("min_age_days", 1)
                        max_size = self.config.get("max_file_size_mb", 100)

                        if file_age >= min_age or file_size <= max_size:
                            cleanup_files.append(match)
                    else:
                        cleanup_files.append(match)

        # ディレクトリ内検索
        for dir_pattern in self.config.get("cleanup_directories", []):
            dir_path = project_root / dir_pattern
            if dir_path.exists() and dir_path.is_dir():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and not self._should_exclude(str(file_path)):
                        cleanup_files.append(str(file_path))

        return list(set(cleanup_files))  # 重複除去

    def _format_size(self, size_bytes: int) -> str:
        """ファイルサイズを人間が読みやすい形式に変換"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def preview_cleanup(self) -> None:
        """クリーンアップ対象をプレビュー"""
        files = self._find_cleanup_files()

        if not files:
            print("🎉 クリーンアップ対象のファイルは見つかりませんでした")
            return

        total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))

        print(f"📋 クリーンアップ対象: {len(files)} ファイル")
        print(f"💾 合計サイズ: {self._format_size(total_size)}")
        print("対象ファイル:")

        for file_path in sorted(files):
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                age_days = self._get_file_age_days(file_path)
                print(f"  📄 {file_path}")
                print(
                    f"      サイズ: {self._format_size(size)}, 作成: {age_days:.1f}日前"
                )

    def interactive_cleanup(self) -> None:
        """対話的クリーンアップ"""
        files = self._find_cleanup_files()

        if not files:
            print("🎉 クリーンアップ対象のファイルは見つかりませんでした")
            return

        print(f"📋 {len(files)} ファイルが見つかりました")

        for file_path in files:
            if not os.path.exists(file_path):
                continue

            size = os.path.getsize(file_path)
            age_days = self._get_file_age_days(file_path)

            print(f"📄 {file_path}")
            print(f"   サイズ: {self._format_size(size)}, 作成: {age_days:.1f}日前")

            while True:
                choice = input("削除しますか? [y/n/q]: ").lower().strip()
                if choice == "y":
                    self._delete_file(file_path)
                    break
                elif choice == "n":
                    print("   スキップしました")
                    break
                elif choice == "q":
                    print("🛑 クリーンアップを中断しました")
                    return
                else:
                    print(
                        "   'y' (削除), 'n' (スキップ), 'q' (終了) を入力してください"
                    )

    def _delete_file(self, file_path: str) -> bool:
        """ファイルを削除"""
        try:
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                os.remove(file_path)
                self.deleted_files.append(file_path)
                self.deleted_size += size
                logger.info(f"削除: {file_path} ({self._format_size(size)})")
                print(f"   ✅ 削除しました")
                return True
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                self.deleted_files.append(file_path)
                logger.info(f"ディレクトリ削除: {file_path}")
                print(f"   ✅ ディレクトリを削除しました")
                return True
        except Exception as e:
            logger.error(f"削除失敗: {file_path} - {e}")
            print(f"   ❌ 削除失敗: {e}")
            return False

    def auto_cleanup(self) -> None:
        """自動クリーンアップ"""
        files = self._find_cleanup_files()

        if not files:
            print("🎉 クリーンアップ対象のファイルは見つかりませんでした")
            return

        print(f"🧹 自動クリーンアップ開始: {len(files)} ファイル")

        for file_path in files:
            if os.path.exists(file_path):
                self._delete_file(file_path)

        self._show_summary()

    def _show_summary(self) -> None:
        """クリーンアップサマリーを表示"""
        if self.deleted_files:
            print("✨ クリーンアップ完了!")
            print(f"📊 削除ファイル数: {len(self.deleted_files)}")
            print(f"💾 解放された容量: {self._format_size(self.deleted_size)}")
        else:
            print("📋 削除されたファイルはありませんでした")

    def _find_tmp_rule_violations(self) -> List[str]:
        """tmp/配下強制ルール違反ファイルを検出"""
        violations = []
        project_root = Path.cwd()
        tmp_config = self.config.get("tmp_enforcement", {})

        if not tmp_config.get("enforce_tmp_directory", False):
            return violations

        temp_patterns = tmp_config.get("temp_file_patterns", [])

        # プロジェクトルート直下の一時ファイルを検出
        for pattern in temp_patterns:
            matches = glob.glob(str(project_root / pattern))
            for match in matches:
                if os.path.isfile(match) and not self._should_exclude(match):
                    # tmp/配下にないファイルを違反として検出
                    relative_path = os.path.relpath(match, project_root)
                    if not relative_path.startswith("tmp/"):
                        violations.append(match)

        return violations

    def check_tmp_rule_violations(self) -> None:
        """tmp/配下強制ルール違反チェック"""
        violations = self._find_tmp_rule_violations()
        tmp_config = self.config.get("tmp_enforcement", {})
        violation_config = tmp_config.get("violation_handling", {})

        if not violations:
            print("✅ tmp/配下強制ルール: 違反なし")
            return

        print(f"🚨 tmp/配下強制ルール違反検出: {len(violations)} ファイル")

        if violation_config.get("show_warning", True):
            warning_msg = violation_config.get(
                "warning_message", "⚠️ 一時ファイルがtmp/配下にありません"
            )
            print(f"{warning_msg}")

        print("違反ファイル:")
        for violation_file in violations:
            size = (
                os.path.getsize(violation_file) if os.path.exists(violation_file) else 0
            )
            print(f"  📄 {violation_file} ({self._format_size(size)})")

        # ログ記録
        if violation_config.get("log_violations", True):
            self._log_tmp_violations(violations)

        # 移動提案
        if violation_config.get("suggest_move", True):
            self._suggest_tmp_moves(violations)

    def _log_tmp_violations(self, violations: List[str]) -> None:
        """tmp/配下強制ルール違反ログ記録"""
        tmp_config = self.config.get("tmp_enforcement", {})
        violation_config = tmp_config.get("violation_handling", {})
        log_file = violation_config.get("violation_log_file", "tmp_rule_violations.log")

        try:
            import datetime

            timestamp = datetime.datetime.now().isoformat()

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] tmp/配下強制ルール違反検出\n")
                for violation in violations:
                    f.write(f"  - {violation}\n")

            logger.info(f"tmp/配下強制ルール違反ログ記録: {log_file}")
        except Exception as e:
            logger.error(f"違反ログ記録失敗: {e}")

    def _suggest_tmp_moves(self, violations: List[str]) -> None:
        """tmp/配下への移動提案"""
        if not violations:
            return

        print(f"💡 解決提案: {len(violations)} ファイルをtmp/配下に移動")
        print("以下のコマンドで自動移動できます:")
        print("make enforce-tmp-rule")

        print("手動移動する場合:")
        project_root = Path.cwd()
        tmp_dir = project_root / "tmp"

        for violation_file in violations:
            file_name = Path(violation_file).name
            print(f"  mv {violation_file} {tmp_dir / file_name}")

    def enforce_tmp_rule(self, interactive: bool = True) -> None:
        """tmp/配下強制ルール適用（ファイル移動）"""
        violations = self._find_tmp_rule_violations()

        if not violations:
            print("✅ tmp/配下強制ルール: 違反なし、移動は不要です")
            return

        print(f"🔧 tmp/配下強制ルール適用: {len(violations)} ファイルを移動")

        project_root = Path.cwd()
        tmp_dir = project_root / "tmp"

        # tmpディレクトリ作成
        if not tmp_dir.exists():
            tmp_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"tmpディレクトリ作成: {tmp_dir}")
            print(f"  📁 tmpディレクトリ作成: {tmp_dir}")

        moved_count = 0
        for violation_file in violations:
            file_path = Path(violation_file)
            target_path = tmp_dir / file_path.name

            # 同名ファイル対応
            counter = 1
            while target_path.exists():
                target_path = tmp_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1

            try:
                if interactive:
                    choice = (
                        input(f"📄 {file_path.name} をtmp/配下に移動しますか? [y/n]: ")
                        .lower()
                        .strip()
                    )
                    if choice != "y":
                        print("   スキップしました")
                        continue

                shutil.move(str(file_path), str(target_path))
                logger.info(f"tmp/配下強制移動: {file_path} → {target_path}")
                print(f"   ✅ 移動完了: {target_path}")
                moved_count += 1

            except Exception as e:
                logger.error(f"tmp/配下移動失敗: {file_path} → {target_path} - {e}")
                print(f"   ❌ 移動失敗: {e}")

        print(
            f"✨ tmp/配下強制ルール適用完了: {moved_count}/{len(violations)} ファイル移動"
        )


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter ファイルクリーンアップツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python scripts/cleanup.py --dry-run        # ドライラン（プレビューのみ）
  python scripts/cleanup.py --interactive    # 対話的削除
  python scripts/cleanup.py --auto          # 自動削除
  python scripts/cleanup.py --config custom.yml  # カスタム設定使用
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="削除せずにプレビューのみ表示"
    )
    parser.add_argument("--interactive", action="store_true", help="対話的に削除確認")
    parser.add_argument("--auto", action="store_true", help="自動削除（確認なし）")
    parser.add_argument(
        "--config",
        default=".cleanup.yml",
        help="設定ファイルパス (デフォルト: .cleanup.yml)",
    )
    parser.add_argument(
        "--check-tmp-rule", action="store_true", help="tmp/配下強制ルール違反チェック"
    )
    parser.add_argument(
        "--enforce-tmp-rule",
        action="store_true",
        help="tmp/配下強制ルール適用（ファイル移動）",
    )
    parser.add_argument(
        "--enforce-tmp-rule-auto",
        action="store_true",
        help="tmp/配下強制ルール適用（自動移動・確認なし）",
    )

    args = parser.parse_args()

    # tmp/配下強制ルール関連のオプション処理
    if args.check_tmp_rule or args.enforce_tmp_rule or args.enforce_tmp_rule_auto:
        cleanup = FileCleanup(args.config)

        if args.check_tmp_rule:
            print("🔍 tmp/配下強制ルール違反チェック")
            cleanup.check_tmp_rule_violations()
            return
        elif args.enforce_tmp_rule:
            print("🔧 tmp/配下強制ルール適用（対話的）")
            cleanup.enforce_tmp_rule(interactive=True)
            return
        elif args.enforce_tmp_rule_auto:
            print("🤖 tmp/配下強制ルール適用（自動）")
            cleanup.enforce_tmp_rule(interactive=False)
            return

    if not any([args.dry_run, args.interactive, args.auto]):
        print(
            "エラー: --dry-run, --interactive, --auto, --check-tmp-rule, "
            "--enforce-tmp-rule, --enforce-tmp-rule-auto のいずれかを指定してください"
        )
        parser.print_help()
        sys.exit(1)

    try:
        cleanup = FileCleanup(args.config)

        if args.dry_run:
            print("🔍 ドライラン: プレビューモード")
            cleanup.preview_cleanup()
        elif args.interactive:
            print("💬 対話モード")
            cleanup.interactive_cleanup()
        elif args.auto:
            print("🤖 自動モード")
            cleanup.auto_cleanup()

    except KeyboardInterrupt:
        print("🛑 ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"クリーンアップエラー: {e}")
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
