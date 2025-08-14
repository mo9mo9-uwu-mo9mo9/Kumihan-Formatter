#!/usr/bin/env python3
"""
Advanced Development Systems
Issue #870: 複雑タスクパターン拡張 - 高度実装・マルチファイル協業強化

Gemini協業システムの高度な開発機能を提供するモジュール群
"""

from .dependency_analyzer import DependencyAnalyzer, DependencyGraph, DependencyNode
from .multi_file_coordinator import MultiFileCoordinator, CoordinationStrategy, ImplementationPlan
from .pattern_implementation_engine import PatternImplementationEngine, DesignPattern, PatternRequirement
from .refactoring_engine import RefactoringEngine, RefactoringType, RefactoringOpportunity
from .performance_optimizer import PerformanceOptimizer, OptimizationType, PerformanceIssue

__version__ = "1.0.0"
__author__ = "Claude Code + Kumihan Development Team"

__all__ = [
    "DependencyAnalyzer", "DependencyGraph", "DependencyNode",
    "MultiFileCoordinator", "CoordinationStrategy", "ImplementationPlan",
    "PatternImplementationEngine", "DesignPattern", "PatternRequirement",
    "RefactoringEngine", "RefactoringType", "RefactoringOpportunity",
    "PerformanceOptimizer", "OptimizationType", "PerformanceIssue",
]
