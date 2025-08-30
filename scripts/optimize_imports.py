#!/usr/bin/env python3
"""
未使用import自動検出・削除ツール
Issue #1239: 品質保証システム再構築 - 依存関係整理
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import subprocess


class ImportOptimizer:
    """Import最適化クラス"""

    def __init__(self, src_dir: str = "kumihan_formatter"):
        self.src_dir = Path(src_dir)
        self.unused_imports = []
        self.stats = {"files_processed": 0, "imports_removed": 0, "imports_total": 0}

    def find_python_files(self) -> List[Path]:
        """Pythonファイル一覧を取得"""
        return list(self.src_dir.glob("**/*.py"))

    def analyze_file(self, file_path: Path) -> Dict:
        """ファイルのimport使用状況を分析"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # import文とその使用状況を分析
            imports = self._extract_imports(tree)
            used_names = self._extract_used_names(tree)

            unused = []
            for imp in imports:
                if not self._is_import_used(imp, used_names, content):
                    unused.append(imp)

            return {
                "file": file_path,
                "total_imports": len(imports),
                "unused_imports": unused,
                "content": content,
            }

        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"⚠️  {file_path}: 解析エラー - {e}")
            return None

    def _extract_imports(self, tree: ast.AST) -> List[Dict]:
        """import文を抽出"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "import",
                            "module": alias.name,
                            "name": alias.asname or alias.name.split(".")[0],
                            "line": node.lineno,
                            "full_line": f"import {alias.name}"
                            + (f" as {alias.asname}" if alias.asname else ""),
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": module,
                            "name": alias.asname or alias.name,
                            "imported": alias.name,
                            "line": node.lineno,
                            "full_line": f"from {module} import {alias.name}"
                            + (f" as {alias.asname}" if alias.asname else ""),
                        }
                    )

        return imports

    def _extract_used_names(self, tree: ast.AST) -> Set[str]:
        """使用されている名前を抽出"""
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # モジュール.関数形式の使用を検出
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        return used_names

    def _is_import_used(
        self, import_info: Dict, used_names: Set[str], content: str
    ) -> bool:
        """importが使用されているかチェック"""
        name = import_info["name"]

        # 基本的な名前チェック
        if name in used_names:
            return True

        # 特殊ケース: __all__ での明示的エクスポート
        if "__all__" in content and name in content:
            return True

        # 特殊ケース: 型注釈での使用
        if any(keyword in content for keyword in ["TYPE_CHECKING", "typing"]):
            if name in content:
                return True

        # 特殊ケース: デコレータでの使用
        if f"@{name}" in content:
            return True

        return False

    def optimize_file(self, analysis: Dict, dry_run: bool = True) -> bool:
        """ファイルのimport最適化実行"""
        if not analysis or not analysis["unused_imports"]:
            return False

        file_path = analysis["file"]
        content = analysis["content"]
        lines = content.splitlines()

        # 削除対象行を特定（逆順で削除）
        lines_to_remove = []
        for imp in analysis["unused_imports"]:
            lines_to_remove.append(imp["line"] - 1)  # 0-based index

        lines_to_remove.sort(reverse=True)

        if dry_run:
            print(f"📁 {file_path}")
            for line_idx in reversed(lines_to_remove):
                print(f"  🗑️  L{line_idx + 1}: {lines[line_idx].strip()}")
            return True

        # 実際の削除実行
        for line_idx in lines_to_remove:
            del lines[line_idx]

        # ファイル書き戻し
        new_content = "\n".join(lines) + "\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ {file_path}: {len(lines_to_remove)}個のimport削除")
        return True

    def run_optimization(self, dry_run: bool = True) -> Dict:
        """最適化メイン処理"""
        print(f"🔍 Import最適化開始 - {'DRY RUN' if dry_run else 'LIVE RUN'}")
        print(f"対象: {self.src_dir}")
        print("=" * 50)

        files = self.find_python_files()
        total_removed = 0

        for file_path in files:
            analysis = self.analyze_file(file_path)
            if analysis:
                self.stats["files_processed"] += 1
                self.stats["imports_total"] += analysis["total_imports"]

                if analysis["unused_imports"]:
                    self.unused_imports.append(analysis)
                    if self.optimize_file(analysis, dry_run):
                        total_removed += len(analysis["unused_imports"])

        self.stats["imports_removed"] = total_removed
        self._print_summary()

        return self.stats

    def _print_summary(self):
        """結果サマリー表示"""
        print("\n" + "=" * 50)
        print("📊 Import最適化結果サマリー")
        print(f"  - 処理ファイル数: {self.stats['files_processed']}")
        print(f"  - 総import文: {self.stats['imports_total']}")
        print(f"  - 削除対象: {self.stats['imports_removed']}")

        if self.stats["imports_total"] > 0:
            reduction_rate = (
                self.stats["imports_removed"] / self.stats["imports_total"]
            ) * 100
            print(f"  - 削減率: {reduction_rate:.1f}%")

        remaining = self.stats["imports_total"] - self.stats["imports_removed"]
        target = 300

        print(f"  - 最適化後予想: {remaining} (目標: <{target})")

        if remaining <= target:
            print("🎯 目標達成予定！")
        else:
            excess = remaining - target
            print(f"⚠️  目標まで あと{excess}個の削減が必要")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="未使用import自動検出・削除ツール")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="実際の削除は行わず、削除対象のみ表示 (デフォルト)",
    )
    parser.add_argument("--execute", action="store_true", help="実際にimportを削除実行")
    parser.add_argument(
        "--src-dir",
        default="kumihan_formatter",
        help="対象ソースディレクトリ (デフォルト: kumihan_formatter)",
    )

    args = parser.parse_args()

    # 安全性のため、デフォルトはdry-run
    dry_run = not args.execute

    if not dry_run:
        confirm = input("⚠️  実際にファイルを変更します。よろしいですか？ (y/N): ")
        if confirm.lower() != "y":
            print("❌ キャンセルされました")
            sys.exit(1)

    optimizer = ImportOptimizer(args.src_dir)
    stats = optimizer.run_optimization(dry_run=dry_run)

    if dry_run:
        print("\n💡 実際に削除するには: python scripts/optimize_imports.py --execute")


if __name__ == "__main__":
    main()
