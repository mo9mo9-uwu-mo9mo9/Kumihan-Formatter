#!/usr/bin/env python3
"""
ファイルサイズ制限チェックツール

アーキテクチャ原則: Pythonファイルは300行以下
Issue #319対応 - 定期的リファクタリングを不要にする予防的品質管理
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple


def count_effective_lines(file_path: Path) -> int:
    """有効行数をカウント (空行・コメント専用行を除く)"""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        effective_lines = 0
        in_multiline_string = False
        string_delimiter = None

        for line in lines:
            stripped = line.strip()

            # 空行をスキップ
            if not stripped:
                continue

            # 複数行文字列の処理
            if not in_multiline_string:
                # 複数行文字列の開始をチェック
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    string_delimiter = stripped[:3]
                    in_multiline_string = True
                    # 同じ行で終了する場合
                    if stripped.count(string_delimiter) >= 2:
                        in_multiline_string = False
                    continue

                # 単行コメントをスキップ
                if stripped.startswith("#"):
                    continue

                # 有効行としてカウント
                effective_lines += 1
            else:
                # 複数行文字列内
                if string_delimiter in stripped:
                    in_multiline_string = False
                continue

        return effective_lines

    except Exception as e:
        print(f"ファイル読み込みエラー {file_path}: {e}", file=sys.stderr)
        return 0


def check_file_size(
    file_path: Path, max_lines: int, warning_lines: int
) -> Tuple[bool, int, str]:
    """
    ファイルサイズをチェック

    Returns:
        (is_valid, line_count, message)
    """
    line_count = count_effective_lines(file_path)

    if line_count > max_lines:
        message = f"❌ {file_path}: {line_count}行 > 制限{max_lines}行 (超過: {line_count - max_lines}行)"
        return False, line_count, message

    elif line_count > warning_lines:
        message = f"⚠️  {file_path}: {line_count}行 > 警告{warning_lines}行 (制限まで残り: {max_lines - line_count}行)"
        return True, line_count, message

    else:
        message = f"✅ {file_path}: {line_count}行 (OK)"
        return True, line_count, message


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="ファイルサイズ制限チェック")
    parser.add_argument(
        "files", nargs="*", help="チェックするファイル (未指定時は全Pythonファイル)"
    )
    parser.add_argument(
        "--max-lines", type=int, default=300, help="最大行数制限 (デフォルト: 300)"
    )
    parser.add_argument(
        "--warning-lines", type=int, default=240, help="警告行数 (デフォルト: 240)"
    )
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="プロジェクトルート"
    )
    parser.add_argument("--show-stats", action="store_true", help="統計情報を表示")

    args = parser.parse_args()

    # チェック対象ファイルの決定
    if args.files:
        files_to_check = [Path(f) for f in args.files if f.endswith(".py")]
    else:
        files_to_check = list(args.project_root.glob("kumihan_formatter/**/*.py"))
        files_to_check = [f for f in files_to_check if not f.name.startswith("__")]

    if not files_to_check:
        print("チェックするPythonファイルが見つかりません。")
        return

    # ファイルサイズチェック実行
    results = []
    violations = []
    warnings = []

    for file_path in files_to_check:
        is_valid, line_count, message = check_file_size(
            file_path, args.max_lines, args.warning_lines
        )

        results.append((file_path, line_count, is_valid))

        if not is_valid:
            violations.append(message)
            print(message)
        elif line_count > args.warning_lines:
            warnings.append(message)
            print(message)
        else:
            # 詳細モードでのみOKメッセージを表示
            if args.show_stats:
                print(message)

    # 統計情報表示
    if args.show_stats or violations or warnings:
        print("\n" + "=" * 50)
        print("📊 ファイルサイズチェック結果")
        print("=" * 50)

        total_files = len(results)
        total_lines = sum(line_count for _, line_count, _ in results)
        avg_lines = total_lines / total_files if total_files > 0 else 0

        print(f"総ファイル数: {total_files}")
        print(f"総行数: {total_lines:,}")
        print(f"平均行数: {avg_lines:.1f}")
        print(f"制限違反: {len(violations)}件")
        print(f"警告: {len(warnings)}件")

        if results:
            max_file, max_lines, _ = max(results, key=lambda x: x[1])
            min_file, min_lines, _ = min(results, key=lambda x: x[1])
            print(f"最大ファイル: {max_file} ({max_lines}行)")
            print(f"最小ファイル: {min_file} ({min_lines}行)")

    # 違反がある場合はエラー終了
    if violations:
        print(f"\n🚨 {len(violations)}件のファイルサイズ制限違反があります。")
        print("ファイルを分割して、単一責任原則に従ってください。")
        sys.exit(1)
    elif warnings:
        print(f"\n⚠️  {len(warnings)}件のファイルが警告レベルです。")
        print("ファイル分割を検討してください。")
    else:
        print("\n✅ すべてのファイルがサイズ制限内です。")


if __name__ == "__main__":
    main()
