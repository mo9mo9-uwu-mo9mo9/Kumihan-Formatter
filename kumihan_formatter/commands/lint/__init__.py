"""
Lint command module - 機能分離による統合インポート

Issue #778: flake8自動修正ツール - 技術的負債修正
Critical問題解決: 988行lint.pyを機能別モジュールに分割

アーキテクチャ:
- auto_fixer.py: Flake8AutoFixerクラス
- file_processor.py: ファイル処理機能
- error_analyzer.py: エラー解析機能
- report_generator.py: レポート生成機能
- logger_setup.py: ログ設定機能

後方互換性: 既存のimport文をすべてサポート
"""

from typing import Optional, Tuple

# 後方互換性のためのメインコマンド実装
import click

# 主要クラスのインポート
from .auto_fixer import Flake8AutoFixer

# エラー解析関数
from .error_analyzer import parse_error_types, run_flake8_check

# ファイル処理関数
from .file_processor import get_target_files, process_files

# ログ設定関数
from .logger_setup import setup_logger

# レポート生成関数
from .report_generator import (
    display_phase_info,
    display_quality_report,
    display_results,
)


@click.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("--fix", is_flag=True, help="自動修正を実行する")
@click.option(
    "--dry-run", is_flag=True, help="修正内容を表示のみ（実際には変更しない）"
)
@click.option("--config", "-c", help="flake8設定ファイルのパス")
@click.option("--verbose", "-v", is_flag=True, help="詳細ログを表示")
@click.option("--report", "-r", help="HTML修正レポートの出力先ファイル")
@click.option(
    "--advanced", is_flag=True, help="Phase 3.2: 高度修正機能を有効にする（E704対応）"
)
@click.option(
    "--quality-monitoring", is_flag=True, help="Phase 3.3: 品質監視機能を有効にする"
)
@click.option(
    "--type", "-t", help="修正するエラータイプを指定（カンマ区切り） 例: E501,E226,F401"
)
def lint_command(
    files: Tuple[str, ...],
    fix: bool,
    dry_run: bool,
    config: Optional[str],
    verbose: bool,
    report: Optional[str],
    advanced: bool,
    quality_monitoring: bool,
    type: Optional[str],
) -> None:
    """コードの品質チェックと自動修正

    Issue #778: flake8自動修正ツール
    Phase 3.1: E501, E226, F401エラーの自動修正
    Phase 3.2: E704, 複合エラー処理, HTML レポート
    Phase 3.3: 品質監視機能, リアルタイム統計
    """
    setup_logger(verbose)
    files = get_target_files(files)

    if not fix:
        run_flake8_check(files, config)
        return

    # 自動修正実行
    error_types = parse_error_types(type)
    fixer = Flake8AutoFixer(config, error_types)

    display_phase_info(advanced, quality_monitoring)

    total_fixes, reports = process_files(fixer, files, dry_run, report)

    # HTML レポート生成
    if report and reports:
        fixer.generate_html_report(reports, report)
        click.echo(f"📊 HTML report generated: {report}")

    display_results(total_fixes, files, dry_run, advanced)

    # Phase 3.3: Quality monitoring report
    if quality_monitoring:
        display_quality_report(fixer)


# 後方互換性エクスポート
__all__ = [
    "Flake8AutoFixer",
    "get_target_files",
    "process_files",
    "run_flake8_check",
    "parse_error_types",
    "display_phase_info",
    "display_results",
    "display_quality_report",
    "setup_logger",
    "lint_command",
]
