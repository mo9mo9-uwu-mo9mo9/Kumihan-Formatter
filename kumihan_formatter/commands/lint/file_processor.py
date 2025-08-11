"""
File processing module for lint command.

Issue #778: flake8自動修正ツール - ファイル処理機能分離
Technical Debt Reduction: lint.py分割による可読性向上
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import click

if TYPE_CHECKING:
    from .auto_fixer import Flake8AutoFixer


def get_target_files(files: Tuple[str, ...]) -> Tuple[str, ...]:
    """対象ファイルを取得

    Args:
        files: 指定されたファイルのタプル

    Returns:
        処理対象のファイルパスのタプル
    """
    if not files:
        # デフォルト対象：Pythonファイル
        files = tuple(
            str(p) for p in Path(".").rglob("*.py") if not str(p).startswith(".")
        )
    return files


def process_files(
    fixer: "Flake8AutoFixer",
    files: Tuple[str, ...],
    dry_run: bool,
    report: Optional[str],
) -> Tuple[Dict[str, int], List[Any]]:
    """ファイルを処理して修正を適用

    Args:
        fixer: Flake8AutoFixerインスタンス
        files: 処理対象ファイル
        dry_run: ドライランフラグ
        report: レポートファイルパス

    Returns:
        修正統計とレポートデータのタプル
    """
    total_fixes = {"E501": 0, "E226": 0, "F401": 0, "E704": 0, "E702": 0, "total": 0}
    reports = []

    with click.progressbar(files, label="Fixing files") as file_list:
        for file_path in file_list:
            if file_path.endswith(".py"):
                fixes = fixer.fix_file(file_path, dry_run=dry_run)

                if "error" not in fixes:
                    # Phase 3.2: E704/E702を集計に追加
                    for code in ["E501", "E226", "F401", "E704", "E702"]:
                        total_fixes[code] += fixes.get(code, 0)
                    total_fixes["total"] += sum(
                        fixes.get(code, 0)
                        for code in ["E501", "E226", "F401", "E704", "E702"]
                    )

                    # レポート用データ収集
                    if report:
                        file_report = fixer.generate_fix_report(fixes, file_path)
                        reports.append(file_report)

    return total_fixes, reports
