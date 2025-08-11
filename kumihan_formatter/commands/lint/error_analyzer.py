"""
Error analysis module for lint command.

Issue #778: flake8自動修正ツール - エラー解析機能分離
Technical Debt Reduction: lint.py分割による可読性向上
"""

import subprocess
from typing import List, Optional, Tuple

import click

from kumihan_formatter.core.utilities.logger import get_logger


def run_flake8_check(files: Tuple[str, ...], config: Optional[str]) -> None:
    """flake8チェックを実行

    Args:
        files: チェック対象ファイル
        config: 設定ファイルパス
    """
    logger = get_logger(__name__)
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            ["python3", "-m", "flake8", "--config", config or ".flake8", *files],
            timeout=60,
        )
        click.echo(f"flake8 check completed with exit code: {result.returncode}")
    except subprocess.TimeoutExpired:
        click.echo("flake8 check timed out", err=True)
    except Exception as e:
        click.echo(f"Failed to run flake8: {e}", err=True)


def parse_error_types(type_str: Optional[str]) -> Optional[List[str]]:
    """エラータイプを解析

    Args:
        type_str: エラータイプ文字列（カンマ区切り）

    Returns:
        解析されたエラータイプのリスト
    """
    if type_str:
        error_types = [t.strip() for t in type_str.split(",")]
        click.echo(f"Fixing only specified error types: {', '.join(error_types)}")
        return error_types
