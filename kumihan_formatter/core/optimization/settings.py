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
