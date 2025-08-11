"""
Logger setup module for lint command.

Issue #778: flake8自動修正ツール - logger機能分離
Technical Debt Reduction: lint.py分割による可読性向上
"""

import logging
from typing import Any

from kumihan_formatter.core.utilities.logger import get_logger


def setup_logger(verbose: bool) -> Any:
    """ロガーをセットアップ

    Args:
        verbose: 詳細ログ表示フラグ

    Returns:
        設定されたロガーインスタンス
    """
    logger = get_logger(__name__)
    if verbose:
        logger.setLevel(logging.DEBUG)
    return logger
