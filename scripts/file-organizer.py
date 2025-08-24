#!/usr/bin/env python3
"""
ファイル整理システム - ファイル自動分類・整理ツール

このスクリプトはファイルタイプに基づいてファイルを適切なディレクトリに分類・移動し、
重複ファイルの検出・処理を行います。

使用例:
    python scripts/file-organizer.py --scan        # スキャンのみ
    python scripts/file-organizer.py --organize    # 自動整理
    python scripts/file-organizer.py --duplicates  # 重複ファイル検出
    python scripts/file-organizer.py --interactive # 対話的整理
"""

import argparse
import hashlib
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class FileOrganizer:
    """ファイル整理システム"""

    def __init__(self):
        """初期化"""
        self.project_root = Path.cwd()
        self.moved_files: List[Tuple[str, str]] = []
        self.duplicate_files: Dict[str, List[str]] = {}

        # ファイル分類ルール
        self.classification_rules = {
            "documents": {
                "extensions": [".md", ".txt", ".pdf", ".doc", ".docx", ".rtf"],
                "patterns": ["README*", "CHANGELOG*", "LICENSE*", "CONTRIBUTING*"],
                "target_dir": "docs/files",
            },
            "test_files": {
                "extensions": [".kumihan"],
                "patterns": ["test_*", "*_test.*", "sample_*", "*_sample.*"],
                "target_dir": "tests/sample_files",
            },
            "scripts": {
                "extensions": [".py", ".sh", ".bat"],
                "patterns": ["*script*", "*tool*"],
                "exclude_dirs": ["kumihan_formatter", "tests"],
                "target_dir": "scripts/utilities",
            },
            "reports": {
                "extensions": [".json", ".html"],
                "patterns": ["*_report_*", "*_Final_Report.*", "Issue_*_Complete_*"],
                "target_dir": "reports",
            },
            "data_files": {
                "extensions": [".csv", ".json", ".xml", ".yaml", ".yml"],
                "patterns": ["config_*", "data_*", "*_config.*", "*_data.*"],
                "target_dir": "data",
            },
            "media": {
                "extensions": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"],
                "patterns": ["screenshot_*", "diagram_*", "image_*"],
                "target_dir": "assets/images",
            },
            "archives": {
                "extensions": [".zip", ".tar", ".gz", ".7z", ".rar"],
                "patterns": ["backup_*", "archive_*"],
                "target_dir": "archives",
            },
            "temp_files": {
                "extensions": [".tmp", ".cache", ".log"],
                "patterns": ["temp_*", "tmp_*", "debug_*", "cache_*"],
                "target_dir": "tmp",
            },
        }

        # 除外ディレクトリ
        self.exclude_dirs = {
            ".git",
            ".github",
            "node_modules",
            "venv",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "build",
            "dist",
            "kumihan_formatter",
            "tests",
            "docs",
            "scripts",
        }

        # 除外ファイル
        self.exclude_files = {
            "Makefile",
            "pyproject.toml",
            ".gitignore",
            "LICENSE",
            "README.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "SPEC.md",
            ".pre-commit-config.yaml",
        }

    def _should_exclude_path(self, path: Path) -> bool:
        """パスを除外すべきかチェック"""
        # 除外ディレクトリに含まれているかチェック
        for part in path.parts:
            if part in self.exclude_dirs:
                return True

        # 除外ファイルかチェック
        if path.name in self.exclude_files:
            return True

        # 隠しファイル・ディレクトリ（.で始まる）はスキップ（設定ファイル以外）
        if path.name.startswith(".") and not path.name.endswith(
            (".yml", ".yaml", ".json")
        ):
            return True

        return False

    def _classify_file(self, file_path: Path) -> str:
        """ファイルを分類"""
        file_ext = file_path.suffix.lower()
        file_name = file_path.name

        for category, rules in self.classification_rules.items():
            # 拡張子チェック
            if file_ext in rules.get("extensions", []):
                # 除外ディレクトリチェック
                exclude_dirs = rules.get("exclude_dirs", [])
                if any(exclude_dir in str(file_path) for exclude_dir in exclude_dirs):
                    continue
                return category

            # パターンチェック
            patterns = rules.get("patterns", [])
            for pattern in patterns:
                if self._match_pattern(file_name, pattern):
                    return category

        return "misc"

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """パターンマッチング（簡易版）"""
        import fnmatch

        return fnmatch.fnmatch(filename.lower(), pattern.lower())

    def _get_target_directory(self, category: str) -> Path:
        """カテゴリに応じた移動先ディレクトリを取得"""
        if category in self.classification_rules:
            target_dir = self.classification_rules[category]["target_dir"]
        else:
            target_dir = "misc"

        return self.project_root / target_dir

    def _create_directory_if_not_exists(self, directory: Path) -> None:
        """ディレクトリが存在しない場合は作成"""
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"ディレクトリ作成: {directory}")

    def _move_file(self, source: Path, target_dir: Path) -> bool:
        """ファイルを移動"""
        try:
            self._create_directory_if_not_exists(target_dir)
            target_path = target_dir / source.name

            # 同名ファイルが存在する場合は番号を付加
            counter = 1
            while target_path.exists():
                name_parts = source.stem, counter, source.suffix
                target_path = (
                    target_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                )
                counter += 1

            shutil.move(str(source), str(target_path))
            self.moved_files.append((str(source), str(target_path)))
            logger.info(f"移動: {source} → {target_path}")
            return True

        except Exception as e:
            logger.error(f"ファイル移動失敗: {source} → {target_dir} - {e}")
            return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのハッシュ値を計算"""
        try:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"ハッシュ計算失敗: {file_path} - {e}")
            return ""

    def scan_files(self) -> Dict[str, List[Path]]:
        """ファイルをスキャンして分類"""
        categorized_files = defaultdict(list)

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_exclude_path(file_path):
                # プロジェクト内の相対パスで判断
                relative_path = file_path.relative_to(self.project_root)
                if not self._should_exclude_path(relative_path):
                    category = self._classify_file(file_path)
                    categorized_files[category].append(file_path)

        return dict(categorized_files)

    def find_duplicates(self) -> Dict[str, List[Path]]:
        """重複ファイルを検出"""
        hash_map = defaultdict(list)
        duplicates = {}

        print("🔍 重複ファイル検索中...")

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_exclude_path(file_path):
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    hash_map[file_hash].append(file_path)

        # 重複ファイル（ハッシュが同じで複数存在）を抽出
        for file_hash, file_list in hash_map.items():
            if len(file_list) > 1:
                # サイズでソート（大きいファイルを優先的に表示）
                file_list.sort(key=lambda p: p.stat().st_size, reverse=True)
                duplicates[file_hash] = file_list

        self.duplicate_files = duplicates
        return duplicates

    def show_scan_results(self, categorized_files: Dict[str, List[Path]]) -> None:
        """スキャン結果を表示"""
        total_files = sum(len(files) for files in categorized_files.values())
        print(f"\n📊 ファイルスキャン結果: {total_files} ファイル")

        for category, files in categorized_files.items():
            if files:
                target_dir = self._get_target_directory(category)
                print(f"\n📁 {category.upper()} ({len(files)} ファイル)")
                print(f"   移動先: {target_dir}")

                for file_path in files[:5]:  # 最初の5ファイルのみ表示
                    size = file_path.stat().st_size
                    print(f"   📄 {file_path.name} ({self._format_size(size)})")

                if len(files) > 5:
                    print(f"   ... その他 {len(files) - 5} ファイル")

    def show_duplicate_results(self, duplicates: Dict[str, List[Path]]) -> None:
        """重複ファイル結果を表示"""
        if not duplicates:
            print("🎉 重複ファイルは見つかりませんでした")
            return

        total_duplicates = sum(len(files) - 1 for files in duplicates.values())
        total_wasted_space = 0

        print(
            f"\n🔍 重複ファイル検出結果: {len(duplicates)} グループ、{total_duplicates} 個の重複"
        )

        for i, (file_hash, file_list) in enumerate(duplicates.items(), 1):
            original_size = file_list[0].stat().st_size
            wasted_space = original_size * (len(file_list) - 1)
            total_wasted_space += wasted_space

            print(f"\n📦 グループ {i} (ハッシュ: {file_hash[:8]}...)")
            print(f"   ファイルサイズ: {self._format_size(original_size)}")
            print(f"   重複による無駄な容量: {self._format_size(wasted_space)}")

            for j, file_path in enumerate(file_list):
                status = "🔵 オリジナル" if j == 0 else "🔴 重複"
                print(f"   {status} {file_path}")

        print(f"\n💾 総無駄容量: {self._format_size(total_wasted_space)}")

    def organize_files_interactive(
        self, categorized_files: Dict[str, List[Path]]
    ) -> None:
        """対話的ファイル整理"""
        print("\n💬 対話的ファイル整理モード")

        for category, files in categorized_files.items():
            if not files:
                continue

            target_dir = self._get_target_directory(category)
            print(f"\n📁 {category.upper()} - {len(files)} ファイル")
            print(f"移動先: {target_dir}")

            while True:
                choice = (
                    input("このカテゴリのファイルを移動しますか? [y/n/s/q]: ")
                    .lower()
                    .strip()
                )
                if choice == "y":
                    self._organize_category(category, files)
                    break
                elif choice == "n":
                    print("   スキップしました")
                    break
                elif choice == "s":
                    self._show_files_in_category(files)
                elif choice == "q":
                    print("🛑 整理を中断しました")
                    return
                else:
                    print(
                        "   'y' (移動), 'n' (スキップ), 's' (ファイル表示), 'q' (終了)"
                    )

    def organize_files_auto(self, categorized_files: Dict[str, List[Path]]) -> None:
        """自動ファイル整理"""
        print("\n🤖 自動ファイル整理モード")

        for category, files in categorized_files.items():
            if files:
                self._organize_category(category, files)

        self._show_organize_summary()

    def _organize_category(self, category: str, files: List[Path]) -> None:
        """カテゴリのファイルを整理"""
        target_dir = self._get_target_directory(category)
        success_count = 0

        for file_path in files:
            if self._move_file(file_path, target_dir):
                success_count += 1

        print(f"   ✅ {category}: {success_count}/{len(files)} ファイル移動完了")

    def _show_files_in_category(self, files: List[Path]) -> None:
        """カテゴリ内ファイルを表示"""
        print("\n   📋 ファイル一覧:")
        for file_path in files:
            size = file_path.stat().st_size
            print(f"      📄 {file_path.name} ({self._format_size(size)})")

    def _show_organize_summary(self) -> None:
        """整理サマリーを表示"""
        if self.moved_files:
            print("\n✨ ファイル整理完了!")
            print(f"📊 移動ファイル数: {len(self.moved_files)}")
            print("\n移動済みファイル:")
            for source, target in self.moved_files:
                print(f"   📄 {Path(source).name} → {Path(target).parent}")
        else:
            print("\n📋 移動されたファイルはありませんでした")

    def handle_duplicates_interactive(self, duplicates: Dict[str, List[Path]]) -> None:
        """対話的重複ファイル処理"""
        if not duplicates:
            print("🎉 重複ファイルは見つかりませんでした")
            return

        print("\n💬 対話的重複ファイル処理モード")

        for i, (file_hash, file_list) in enumerate(duplicates.items(), 1):
            print(f"\n📦 グループ {i}/{len(duplicates)}")
            for j, file_path in enumerate(file_list):
                status = "🔵 オリジナル" if j == 0 else f"🔴 重複 {j}"
                size = file_path.stat().st_size
                print(f"   {status} {file_path} ({self._format_size(size)})")

            while True:
                choice = input("重複ファイルを削除しますか? [y/n/q]: ").lower().strip()
                if choice == "y":
                    self._remove_duplicates(file_list[1:])  # オリジナル以外を削除
                    break
                elif choice == "n":
                    print("   スキップしました")
                    break
                elif choice == "q":
                    print("🛑 重複処理を中断しました")
                    return
                else:
                    print("   'y' (削除), 'n' (スキップ), 'q' (終了)")

    def _remove_duplicates(self, duplicate_files: List[Path]) -> None:
        """重複ファイルを削除"""
        success_count = 0
        for file_path in duplicate_files:
            try:
                file_path.unlink()
                logger.info(f"重複ファイル削除: {file_path}")
                success_count += 1
            except Exception as e:
                logger.error(f"重複ファイル削除失敗: {file_path} - {e}")

        print(f"   ✅ {success_count}/{len(duplicate_files)} 重複ファイル削除完了")

    def _format_size(self, size_bytes: int) -> str:
        """ファイルサイズを人間が読みやすい形式に変換"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def detect_tmp_rule_violations(self) -> List[Path]:
        """tmp/配下強制ルール違反ファイルを検出"""
        violations = []

        # 一時ファイルパターン（.cleanup.ymlと同様）
        temp_patterns = [
            "temp_*",
            "tmp_*",
            "test_temp_*",
            "temp_test_*",
            "test_output_*",
            "debug_output_*",
            "benchmark_output_*",
            "performance_test_*",
            "output_*",
            "result_*",
            "generated_*",
            "auto_generated_*",
            "*.generated.*",
            "cache_*",
            "*.cache",
            "profiling_*",
            "memory_profile_*",
            "*.prof",
            "*.cprof",
            "*_report_*.json",
            "*_report_*.txt",
            "*_report_*.html",
            "behavioral_control_*.json",
            "rule_compliance_*.json",
        ]

        # プロジェクトルート直下の一時ファイルを検出
        for pattern in temp_patterns:
            matches = list(self.project_root.glob(pattern))
            for match in matches:
                if match.is_file() and not self._should_exclude_path(match):
                    # tmp/配下にないファイルを違反として検出
                    relative_path = match.relative_to(self.project_root)
                    if not str(relative_path).startswith("tmp/"):
                        violations.append(match)

        return violations

    def enforce_tmp_rule(self, interactive: bool = True) -> None:
        """tmp/配下強制ルール適用（ファイル移動）"""
        violations = self.detect_tmp_rule_violations()

        if not violations:
            print("✅ tmp/配下強制ルール: 違反なし、移動は不要です")
            return

        print(f"🔧 tmp/配下強制ルール適用: {len(violations)} ファイルを移動")

        tmp_dir = self.project_root / "tmp"

        # tmpディレクトリ作成
        if not tmp_dir.exists():
            tmp_dir.mkdir(parents=True, exist_ok=True)
            print(f"  📁 tmpディレクトリ作成: {tmp_dir}")

        moved_count = 0
        for violation_file in violations:
            target_path = tmp_dir / violation_file.name

            # 同名ファイル対応
            counter = 1
            while target_path.exists():
                target_path = (
                    tmp_dir / f"{violation_file.stem}_{counter}{violation_file.suffix}"
                )
                counter += 1

            try:
                if interactive:
                    print(f"\n📄 {violation_file.name}")
                    print(
                        f"   サイズ: {self._format_size(violation_file.stat().st_size)}"
                    )
                    choice = input("tmp/配下に移動しますか? [y/n]: ").lower().strip()
                    if choice != "y":
                        print("   スキップしました")
                        continue

                violation_file.rename(target_path)
                self.moved_files.append((str(violation_file), str(target_path)))
                logger.info(f"tmp/配下強制移動: {violation_file} → {target_path}")
                print(f"   ✅ 移動完了: {target_path}")
                moved_count += 1

            except Exception as e:
                logger.error(
                    f"tmp/配下移動失敗: {violation_file} → {target_path} - {e}"
                )
                print(f"   ❌ 移動失敗: {e}")

        print(
            f"\n✨ tmp/配下強制ルール適用完了: {moved_count}/{len(violations)} ファイル移動"
        )


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter ファイル整理ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python scripts/file-organizer.py --scan        # ファイルスキャンのみ
  python scripts/file-organizer.py --organize    # 自動ファイル整理
  python scripts/file-organizer.py --interactive # 対話的ファイル整理
  python scripts/file-organizer.py --duplicates  # 重複ファイル検出・処理
        """,
    )

    parser.add_argument("--scan", action="store_true", help="ファイルスキャンのみ実行")
    parser.add_argument("--organize", action="store_true", help="自動ファイル整理")
    parser.add_argument("--interactive", action="store_true", help="対話的ファイル整理")
    parser.add_argument(
        "--duplicates", action="store_true", help="重複ファイル検出・処理"
    )
    parser.add_argument(
        "--enforce-tmp-rule",
        action="store_true",
        help="tmp/配下強制ルール適用（ファイル移動）",
    )

    args = parser.parse_args()

    if not any(
        [
            args.scan,
            args.organize,
            args.interactive,
            args.duplicates,
            args.enforce_tmp_rule,
        ]
    ):
        print(
            "エラー: --scan, --organize, --interactive, --duplicates, --enforce-tmp-rule のいずれかを指定してください"
        )
        parser.print_help()
        sys.exit(1)

    try:
        organizer = FileOrganizer()

        if args.scan:
            print("🔍 ファイルスキャンモード")
            categorized_files = organizer.scan_files()
            organizer.show_scan_results(categorized_files)

        elif args.organize:
            print("🤖 自動整理モード")
            categorized_files = organizer.scan_files()
            organizer.organize_files_auto(categorized_files)

        elif args.interactive:
            print("💬 対話的整理モード")
            categorized_files = organizer.scan_files()
            organizer.organize_files_interactive(categorized_files)

        elif args.duplicates:
            print("🔍 重複ファイル検出モード")
            duplicates = organizer.find_duplicates()
            organizer.show_duplicate_results(duplicates)

            if duplicates:
                while True:
                    choice = (
                        input("\n重複ファイルを対話的に処理しますか? [y/n]: ")
                        .lower()
                        .strip()
                    )
                    if choice == "y":
                        organizer.handle_duplicates_interactive(duplicates)
                        break
                    elif choice == "n":
                        break
                    else:
                        print("'y' または 'n' を入力してください")

        elif args.enforce_tmp_rule:
            print("🔧 tmp/配下強制ルール適用モード")
            organizer.enforce_tmp_rule(interactive=True)

    except KeyboardInterrupt:
        print("\n🛑 ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"ファイル整理エラー: {e}")
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
