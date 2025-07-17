"""
ログ分析 ファクトリー

ログ分析コンポーネントのインスタンス取得
Issue #492 Phase 5A - log_analysis.py分割
"""

from .log_dependency_tracker import DependencyTracker
from .log_error_analyzer import ErrorAnalyzer
from .log_execution_tracker import ExecutionFlowTracker


def get_error_analyzer(name: str) -> ErrorAnalyzer:
    """Get an ErrorAnalyzer instance for a module

    Args:
        name: Module name

    Returns:
        ErrorAnalyzer instance
    """
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return ErrorAnalyzer(structured_logger)


def get_dependency_tracker(name: str) -> DependencyTracker:
    """Get a DependencyTracker instance for a module

    Args:
        name: Module name

    Returns:
        DependencyTracker instance
    """
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return DependencyTracker(structured_logger)


def get_execution_flow_tracker(name: str) -> ExecutionFlowTracker:
    """Get an ExecutionFlowTracker instance for a module

    Args:
        name: Module name

    Returns:
        ExecutionFlowTracker instance
    """
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return ExecutionFlowTracker(structured_logger)
