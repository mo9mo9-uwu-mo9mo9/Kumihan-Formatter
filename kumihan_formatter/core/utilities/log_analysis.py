"""
ログ分析 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - log_analysis.py分割
"""

from .log_analysis_factory import (
    get_dependency_tracker,
    get_error_analyzer,
    get_execution_flow_tracker,
)
from .log_dependency_tracker import DependencyTracker

# Re-export all classes from split modules for backward compatibility
from .log_error_analyzer import ErrorAnalyzer
from .log_execution_tracker import ExecutionFlowTracker

__all__ = [
    "ErrorAnalyzer",
    "DependencyTracker",
    "ExecutionFlowTracker",
    "get_error_analyzer",
    "get_dependency_tracker",
    "get_execution_flow_tracker",
]
