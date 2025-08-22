"""
Report generation module for lint command.

Issue #778: flake8自動修正ツール - レポート生成機能分離
Technical Debt Reduction: lint.py分割による可読性向上
"""

from typing import TYPE_CHECKING, Dict, Tuple

import click

if TYPE_CHECKING:
    from .auto_fixer import Flake8AutoFixer


def display_phase_info(advanced: bool, quality_monitoring: bool) -> None:
    """Phase機能の情報を表示

    Args:
        advanced: 高度機能フラグ
        quality_monitoring: 品質監視フラグ
    """
    if advanced:
        click.echo("🚀 Advanced mode enabled (Phase 3.2)")
        click.echo(
            "Features: E704 (multiple statements), error dependency analysis, "
            "HTML reports"
        )

    if quality_monitoring:
        click.echo("📊 Quality monitoring enabled (Phase 3.3)")
        click.echo("Features: Real-time metrics, performance analysis, quality reports")


def display_results(
    total_fixes: Dict[str, int], files: Tuple[str, ...], dry_run: bool, advanced: bool
) -> None:
    """結果を表示

    Args:
        total_fixes: 修正統計
        files: 処理したファイル
        dry_run: ドライランフラグ
        advanced: 高度機能フラグ
    """
    # 結果表示
    if dry_run:
        click.echo("Dry run completed. No files were modified.")
    else:
        click.echo("Auto-fix completed.")

    click.echo("Fixes applied:")
    click.echo(f"  E501 (line too long): {total_fixes['E501']}")
    click.echo(f"  E226 (missing whitespace): {total_fixes['E226']}")
    click.echo(f"  F401 (unused import): {total_fixes['F401']}")

    # Phase 3.2機能の結果表示
    if advanced:
        click.echo(f"  E704 (multiple statements): {total_fixes['E704']}")
        click.echo(f"  E702 (multiple statements): {total_fixes['E702']}")

    click.echo(f"  Total fixes: {total_fixes['total']}")

    # 統計情報
    if advanced and total_fixes["total"] > 0:
        py_files = [f for f in files if f.endswith(".py")]
        success_rate = round((total_fixes["total"] / len(py_files) * 100))
        click.echo("📈 Processing statistics:")
        click.echo(f"  Files processed: {len(py_files)}")
        click.echo(
            f"  Average fixes per file: "
            f"{round(total_fixes['total'] / len(py_files), 1)}"
        )
        click.echo(f"  Success rate: {success_rate}%")


def display_quality_report(fixer: "Flake8AutoFixer") -> None:
    """品質監視レポートを表示

    Args:
        fixer: Flake8AutoFixerインスタンス
    """
    quality_report = fixer.get_quality_report()
    click.echo("\n📊 Quality Monitoring Report (Phase 3.3)")
    click.echo("=" * 50)

    summary = quality_report["summary"]
    click.echo(f"Total Files Processed: {summary['total_files']}")
    click.echo(f"Total Errors Detected: {summary['total_errors']}")
    click.echo(f"Total Fixes Applied: {summary['total_fixes']}")
    click.echo(f"Overall Success Rate: {summary['overall_success_rate']}%")

    performance = quality_report["performance"]
    click.echo("\nPerformance Metrics:")
    click.echo(
        f"  Avg Processing Time: "
        f"{performance['avg_processing_time_per_file']:.3f}s per file"
    )
    click.echo(
        f"  Error Detection Rate: {performance['errors_per_second']:.1f} errors/sec"
    )
    click.echo(
        f"  Fix Application Rate: {performance['fixes_per_second']:.1f} fixes/sec"
    )

    metrics = quality_report["quality_metrics"]
    click.echo("\nQuality Metrics:")
    click.echo(f"  Average Errors per File: {metrics['average_errors_per_file']:.1f}")
    click.echo(f"  Total Processing Time: {metrics['processing_time']:.3f}s")
