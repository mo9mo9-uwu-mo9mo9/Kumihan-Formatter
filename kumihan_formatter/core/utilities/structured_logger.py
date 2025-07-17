"""Structured logging and analysis for Kumihan-Formatter

This module provides advanced structured logging capabilities with error analysis,
dependency tracking, and execution flow monitoring for Claude Code integration.

Single Responsibility Principle適用: 機能別モジュールに分割
Issue #476 Phase5対応 - 676行から約250行に削減
"""

from __future__ import annotations

from functools import lru_cache

# 分割されたモジュールから必要なクラスをインポート
from .dependency_tracker import DependencyTracker
from .error_analyzer import ErrorAnalyzer
from .execution_flow_tracker import ExecutionFlowTracker
from .structured_logger_base import StructuredLogger, get_structured_logger

# エクスポートするクラスと関数
__all__ = [
    "StructuredLogger",
    "ErrorAnalyzer",
    "DependencyTracker",
    "ExecutionFlowTracker",
    "get_structured_logger",
    "get_error_analyzer",
    "get_dependency_tracker",
    "get_execution_flow_tracker",
]

# キャッシュされたインスタンス管理
_error_analyzers: dict[str, ErrorAnalyzer] = {}
_dependency_trackers: dict[str, DependencyTracker] = {}
_execution_trackers: dict[str, ExecutionFlowTracker] = {}


@lru_cache(maxsize=128)
def get_error_analyzer(name: str) -> ErrorAnalyzer:
    """Get a cached error analyzer instance

    Args:
        name: Logger name

    Returns:
        ErrorAnalyzer instance
    """
    if name not in _error_analyzers:
        logger = get_structured_logger(name)
        _error_analyzers[name] = ErrorAnalyzer(logger)
    return _error_analyzers[name]


@lru_cache(maxsize=128)
def get_dependency_tracker(name: str) -> DependencyTracker:
    """Get a cached dependency tracker instance

    Args:
        name: Logger name

    Returns:
        DependencyTracker instance
    """
    if name not in _dependency_trackers:
        logger = get_structured_logger(name)
        _dependency_trackers[name] = DependencyTracker(logger)
    return _dependency_trackers[name]


@lru_cache(maxsize=128)
def get_execution_flow_tracker(name: str) -> ExecutionFlowTracker:
    """Get a cached execution flow tracker instance

    Args:
        name: Logger name

    Returns:
        ExecutionFlowTracker instance
    """
    if name not in _execution_trackers:
        logger = get_structured_logger(name)
        _execution_trackers[name] = ExecutionFlowTracker(logger)
    return _execution_trackers[name]
