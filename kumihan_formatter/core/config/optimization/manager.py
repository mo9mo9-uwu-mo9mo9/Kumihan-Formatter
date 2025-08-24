"""
Adaptive Settings Manager - Unified Interface
============================================

分割されたコンポーネントを統合し、動的設定調整の統一インターフェースを提供します。

機能:
- 分割されたコア機能と最適化機能の統合
- 外部APIの提供
- 設定調整の一元管理
"""

from typing import Any, Dict, List, Optional, Tuple

from kumihan_formatter.core.config.config_manager import EnhancedConfig
from kumihan_formatter.core.utilities.logger import get_logger

# 分割されたコンポーネントをインポート
from .manager_core import (
    AdaptiveSettingsManagerCore,
    ConfigAdjustment,
    WorkContext,
)
from .manager_optimizer import AdaptiveSettingsManagerOptimizer


class AdaptiveSettingsManager:
    """
    動的設定調整の統合マネージャークラス

    機能:
    - 分割されたコア機能と最適化機能の統合
    - 統一された外部API提供
    - コンテキスト認識による設定最適化
    - AI駆動型最適化システム
    - 学習型調整システム
    - A/Bテスト自動実行
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)

        # 分割されたコンポーネントを初期化
        self.core = AdaptiveSettingsManagerCore(config)
        self.optimizer = AdaptiveSettingsManagerOptimizer(self.core)

        # 後方互換性のためのプロパティ委譲
        self.config = self.core.config
        self.adjustment_history = self.core.adjustment_history
        self.context_patterns = self.core.context_patterns
        self.active_tests = self.optimizer.active_tests
        self.test_results = self.optimizer.test_results

        self.logger.info("AdaptiveSettingsManager (unified) initialized")

    # コンポーネント初期化は各分割クラスで実行

    def adjust_for_context(self, context: WorkContext) -> List[Any]:
        """コンテキストに応じた設定調整（Issue #804 AI最適化統合版）"""
        # コア調整を実行
        core_adjustments = self.core.adjust_for_context(context)

        # AI最適化を実行
        ai_adjustments = self.optimizer.apply_ai_optimizations(context)

        # 統合結果を返す
        all_adjustments = core_adjustments + ai_adjustments

        self.logger.info(
            f"Applied {len(all_adjustments)} total adjustments "
            f"(core: {len(core_adjustments)}, ai: {len(ai_adjustments)}) "
            f"for context: {context.operation_type}"
        )
        return all_adjustments

    # AI最適化機能は optimizer コンポーネントに委譲

    def get_ai_optimization_summary(self) -> Dict[str, Any]:
        """AI最適化システムの総合サマリーを取得 - Issue #804"""
        return self.optimizer.get_ai_optimization_summary()

    # ================================
    # 外部API - 主要公開メソッド群（委譲）
    # ================================

    def optimize_for_file_operation(
        self, file_path: str, operation_type: str = "read"
    ) -> Dict[str, Any]:
        """ファイル操作の最適化（公開API）"""
        return self.core.optimize_for_file_operation(file_path, operation_type)

    def acquire_tool_permission(
        self, tool_name: str, estimated_complexity: float = 0.5
    ) -> Tuple[bool, str]:
        """ツール呼び出し許可を取得（公開API）"""
        return self.core.acquire_tool_permission(tool_name, estimated_complexity)

    def release_tool_permission(self, permission_id: str) -> None:
        """ツール呼び出し許可を解放（公開API）"""
        self.core.release_tool_permission(permission_id)

    def get_current_optimization_status(self) -> Dict[str, Any]:
        """現在の最適化状況を取得（公開API）"""
        base_status = self.core.get_current_optimization_status()
        base_status["ai_optimization_summary"] = self.get_ai_optimization_summary()
        base_status["system_status"]["active_ab_tests"] = len(self.active_tests)
        return base_status

    # 内部調整メソッドは core コンポーネントに委譲

    # ================================
    # A/Bテスト関連メソッド群（委譲）
    # ================================

    def start_ab_test(
        self, parameter: str, test_values: List[Any], sample_size: int = 10
    ) -> Optional[str]:
        """A/Bテストを開始"""
        return self.optimizer.start_ab_test(parameter, test_values, sample_size)

    def record_ab_test_result(
        self, test_id: str, metric_value: float, context: Optional[WorkContext] = None
    ) -> bool:
        """A/Bテスト結果を記録"""
        return self.optimizer.record_ab_test_result(test_id, metric_value, context)

    def run_simple_ab_test(
        self, parameter: str, test_values: List[Any], sample_size: int = 8
    ) -> Optional[str]:
        """簡易A/Bテスト実行（Phase B.2用）"""
        return self.optimizer.run_simple_ab_test(parameter, test_values, sample_size)

    def get_ab_test_results(self, parameter: str) -> List[Dict[str, Any]]:
        """A/Bテスト結果を取得"""
        return self.optimizer.get_ab_test_results(parameter)

    # ================================
    # 学習システム関連メソッド群（委譲）
    # ================================

    def learn_usage_patterns(self) -> Dict[str, Any]:
        """使用パターンを学習し、効率性洞察を生成"""
        return self.optimizer.learn_usage_patterns()

    def apply_learned_optimizations(self) -> List[Any]:
        """学習した最適化を適用"""
        return self.optimizer.apply_learned_optimizations()

    def get_learning_status(self) -> Dict[str, Any]:
        """学習システムの状況を取得"""
        return self.optimizer.get_learning_status()

    # ================================
    # ステータス・サマリー取得メソッド群（委譲）
    # ================================

    def get_adjustment_summary(self) -> Dict[str, Any]:
        """調整サマリーを取得"""
        return self.core.get_adjustment_summary()

    # ================================
    # 補助メソッド群（委譲）
    # ================================

    def is_initialized(self) -> bool:
        """初期化状態チェック"""
        return self.core.is_initialized()

    def optimize_settings(
        self, current_settings: Dict[str, Any], recent_operations: List[str]
    ) -> Dict[str, Any]:
        """設定最適化実行"""
        return self.core.optimize_settings(current_settings, recent_operations)

    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """設定更新"""
        return self.core.update_settings(settings)

    def _apply_adjustment(self, adjustment: ConfigAdjustment) -> None:
        """設定調整を適用（内部メソッド）"""
        return self.core._apply_adjustment(adjustment)


# 分割されたファイルをエクスポートして後方互換性を維持
__all__ = ["AdaptiveSettingsManager", "ConfigAdjustment", "WorkContext"]
