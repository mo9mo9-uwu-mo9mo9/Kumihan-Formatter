"""最適化設定モジュール

このモジュールは最適化システムの設定を管理します。
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizationSettings:
    """最適化設定クラス"""

    enabled: bool = True
    max_iterations: int = 100
    threshold: float = 0.01
    learning_rate: float = 0.1
    batch_size: int = 32
    verbose: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "enabled": self.enabled,
            "max_iterations": self.max_iterations,
            "threshold": self.threshold,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "verbose": self.verbose,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationSettings":
        """辞書から設定を作成"""
        return cls(
            enabled=data.get("enabled", True),
            max_iterations=data.get("max_iterations", 100),
            threshold=data.get("threshold", 0.01),
            learning_rate=data.get("learning_rate", 0.1),
            batch_size=data.get("batch_size", 32),
            verbose=data.get("verbose", False),
        )


class SettingsManager:
    """設定管理クラス"""

    def __init__(self, settings: Optional[OptimizationSettings] = None):
        """初期化

        Args:
            settings: 初期設定
        """
        self.settings = settings or OptimizationSettings()
        logger.debug("設定管理システムが初期化されました")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        return getattr(self.settings, key, default)

    def update_setting(self, key: str, value: Any) -> None:
        """設定値を更新

        Args:
            key: 設定キー
            value: 新しい値
        """
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            logger.debug(f"設定が更新されました: {key} = {value}")
        else:
            logger.warning(f"不明な設定キー: {key}")

    def reset_to_defaults(self) -> None:
        """設定をデフォルトにリセット"""
        self.settings = OptimizationSettings()
        logger.info("設定がデフォルトにリセットされました")


# デフォルト設定インスタンス
default_settings = OptimizationSettings()


# __init__.pyでの互換性用クラス（基本実装）
@dataclass
class WorkContext:
    """作業コンテキスト"""

    task_id: str = ""
    task_type: str = ""
    priority: int = 1
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ABTestConfig:
    """A/Bテスト設定"""

    test_id: str = ""
    variant_a: Optional[Dict[str, Any]] = None
    variant_b: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.variant_a is None:
            self.variant_a = {}
        if self.variant_b is None:
            self.variant_b = {}


@dataclass
class ABTestResult:
    """A/Bテスト結果"""

    test_id: str = ""
    winner: str = ""
    confidence: float = 0.0
    metrics: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metrics is None:
            self.metrics = {}


@dataclass
class ConfigAdjustment:
    """設定調整"""

    key: str = ""
    old_value: Any = None
    new_value: Any = None
    reason: str = ""


class AdaptiveSettingsManager(SettingsManager):
    """適応的設定管理（SettingsManagerの拡張）"""

    def __init__(self) -> None:
        super().__init__()
        self.adaptations: list[ConfigAdjustment] = []

    def adapt_setting(self, adjustment: ConfigAdjustment) -> None:
        """設定を適応的に調整"""
        self.adaptations.append(adjustment)
        self.update_setting(adjustment.key, adjustment.new_value)


class ContextAwareOptimizer:
    """コンテキスト認識最適化器"""

    def __init__(self, context: WorkContext) -> None:
        self.context = context
        self.settings = SettingsManager()

    def optimize(self, data: Any) -> Any:
        """最適化実行"""
        logger.info(f"Optimizing with context: {self.context.task_id}")
        return data


class IntegratedSettingsOptimizer:
    """統合設定最適化器"""

    def __init__(self) -> None:
        self.manager = AdaptiveSettingsManager()
        self.context: Optional[WorkContext] = None

    def set_context(self, context: WorkContext) -> None:
        """コンテキスト設定"""
        self.context = context


class LearningBasedOptimizer:
    """学習ベース最適化器"""

    def __init__(self) -> None:
        self.learning_rate = 0.1
        self.history: list[Dict[str, Any]] = []

    def learn(self, data: Dict[str, Any]) -> None:
        """学習実行"""
        self.history.append(data)


class RealTimeConfigAdjuster:
    """リアルタイム設定調整器"""

    def __init__(self) -> None:
        self.manager = AdaptiveSettingsManager()
        self.adjustments: list[ConfigAdjustment] = []

    def adjust_realtime(self, key: str, value: Any, reason: str = "") -> None:
        """リアルタイム調整"""
        old_value = getattr(self.manager.settings, key, None)
        adjustment = ConfigAdjustment(
            key=key, old_value=old_value, new_value=value, reason=reason
        )
        self.adjustments.append(adjustment)
        self.manager.adapt_setting(adjustment)
