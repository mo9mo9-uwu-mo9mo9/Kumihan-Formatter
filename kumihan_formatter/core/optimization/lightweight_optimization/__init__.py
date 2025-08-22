"""
軽量最適化システム - Lightweight Optimization System

AI駆動型最適化システムの簡素化版（16,546行 → 850行）
Claude Code最適化によりコスト効率最適化実現

Components:
- ConfigOptimizer: 設定最適化エンジン（200行）
- RuleEngine: ルールベース最適化（250行）
- WorkflowBridge: Claude統合連携（200行）
- Utils: 共通ユーティリティ（200行）

Target: 90%以上のToken削減・95%品質維持
"""

from .config_optimizer import ConfigOptimizer, OptimizationResult
from .rule_engine import Rule, RuleEngine, RulePriority, RuleResult
from .utils import OptimizationUtils, PerformanceMetrics
from .workflow_bridge import WorkflowBridge, WorkflowRequest, WorkflowResponse

__all__ = [
    # Core Classes
    "ConfigOptimizer",
    "RuleEngine",
    "WorkflowBridge",
    "OptimizationUtils",
    # Data Classes
    "OptimizationResult",
    "Rule",
    "RuleResult",
    "RulePriority",
    "WorkflowRequest",
    "WorkflowResponse",
    "PerformanceMetrics",
]

# Version
__version__ = "1.0.0-lightweight"

# Configuration
LIGHTWEIGHT_CONFIG = {
    "target_efficiency": 0.95,  # 95%効率目標
    "token_reduction_target": 0.90,  # 90%Token削減目標
    "quality_threshold": 0.95,  # 95%品質維持
    "workflow_integration": True,  # Claude統合
    "fallback_mode": "local",  # ローカルフォールバック
}
