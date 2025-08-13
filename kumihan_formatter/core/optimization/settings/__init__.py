"""
Adaptive Settings Management System
===================================

動的設定調整とAI最適化統合システムを提供します。

主要コンポーネント:
- AdaptiveSettingsManager: 動的設定調整の中核
- TokenUsageAnalyzer: リアルタイムToken使用量監視
- FileSizeLimitOptimizer: ファイルサイズ制限最適化
- A/B Testing Framework: 統計的検定システム
- Phase B.1/B.2 Optimizers: 統合最適化システム

Issue #813 対応: adaptive_settings.py (3011行) 分割リファクタリング実装
Issue #804 対応: AI最適化システム統合
"""

# 循環インポート回避のため順序を重視したインポート
from typing import Any

# 2. A/Bテストフレームワーク
from .ab_testing import (
    ABTestConfig,
    ABTestResult,
    SimpleNumpy,
    SimpleStats,
    StatisticalTestingEngine,
    StatisticalTestResult,
)

# 3. 分析コンポーネント
from .analyzers import (
    ComplexityAnalyzer,
    TokenUsageAnalyzer,
)

# 6. メインマネージャー（最後にインポート）
# 1. 基本データクラスとユーティリティ
from .manager import AdaptiveSettingsManager, ConfigAdjustment, WorkContext

# 4. 最適化コンポーネント
from .optimizers import (
    ConcurrentToolCallLimiter,
    ContextAwareOptimizer,
    FileSizeLimitOptimizer,
    RealTimeConfigAdjuster,
)

# 5. Phase最適化システム
from .settings_optimizers import (
    IntegratedSettingsOptimizer,
    LearningBasedOptimizer,
)

# パブリックAPI定義
__all__ = [
    # メインマネージャー
    "AdaptiveSettingsManager",
    # データクラス
    "ConfigAdjustment",
    "WorkContext",
    # A/Bテストフレームワーク
    "ABTestConfig",
    "ABTestResult",
    "SimpleNumpy",
    "SimpleStats",
    "StatisticalTestResult",
    "StatisticalTestingEngine",
    # 分析システム
    "ComplexityAnalyzer",
    "TokenUsageAnalyzer",
    # 最適化システム
    "ConcurrentToolCallLimiter",
    "ContextAwareOptimizer",
    "FileSizeLimitOptimizer",
    "RealTimeConfigAdjuster",
    # Phase統合最適化
    "IntegratedSettingsOptimizer",
    "LearningBasedOptimizer",
]

# バージョン情報
__version__ = "1.0.0"
__status__ = "Production"  # Development -> Production (Issue #813完了)


# 統合システム便利関数
def create_adaptive_manager(config: Any) -> Any:
    """
    AdaptiveSettingsManagerの便利な作成関数

    Args:
        config: EnhancedConfigインスタンス

    Returns:
        設定済みのAdaptiveSettingsManagerインスタンス
    """
    return AdaptiveSettingsManager(config)


def create_full_optimization_stack(config: Any) -> Any:
    """
    完全最適化スタックを作成（開発・テスト用）

    Args:
        config: EnhancedConfigインスタンス

    Returns:
        全コンポーネントを含む辞書
    """
    manager = AdaptiveSettingsManager(config)

    return {
        "adaptive_manager": manager,
        "token_analyzer": TokenUsageAnalyzer(config),
        "file_size_optimizer": FileSizeLimitOptimizer(config),
        "concurrent_limiter": ConcurrentToolCallLimiter(config),
        "integrated_settings_optimizer": IntegratedSettingsOptimizer(config),
        "learning_based_optimizer": LearningBasedOptimizer(config, manager),
        "statistical_engine": StatisticalTestingEngine(),
        "complexity_analyzer": ComplexityAnalyzer(),
        "context_optimizer": ContextAwareOptimizer(),
    }


# モジュール情報
def get_module_info() -> dict[str, Any]:
    """モジュール情報を取得"""
    return {
        "name": "adaptive_settings",
        "version": __version__,
        "status": __status__,
        "components_count": len(__all__),
        "split_from": "adaptive_settings.py (3011 lines)",
        "issue": "#813 - Modular Refactoring",
        "ai_integration": "#804 - AI Optimization System",
        "target_reduction": "Total 66.8% (Phase B.1: 61.8% + Phase B.2: 5%)",
        "files_created": [
            "__init__.py",
            "manager.py",
            "ab_testing.py",
            "analyzers.py",
            "optimizers.py",
            "settings_optimizers.py",
        ],
    }
