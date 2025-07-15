"""パフォーマンス監視システムの基底クラスとインターフェース

Single Responsibility Principle適用: 共通インターフェースの定義
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

import platform
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ...utilities.logger import get_logger


@dataclass
class SystemInfo:
    """システム情報"""

    platform: str
    python_version: str
    cpu_count: int
    memory_total: int  # バイト
    architecture: str

    @classmethod
    def capture(cls) -> "SystemInfo":
        """現在のシステム情報を取得"""
        try:
            import psutil

            memory_total = psutil.virtual_memory().total
        except ImportError:
            memory_total = 0

        import os

        return cls(
            platform=platform.platform(),
            python_version=sys.version,
            cpu_count=os.cpu_count() or 1,
            memory_total=memory_total,
            architecture=platform.architecture()[0],
        )

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "platform": self.platform,
            "python_version": self.python_version,
            "cpu_count": self.cpu_count,
            "memory_total_mb": (
                self.memory_total / 1024 / 1024 if self.memory_total > 0 else 0
            ),
            "architecture": self.architecture,
        }


@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクスの基底クラス"""

    name: str
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any]
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "category": self.category,
            "metadata": self.metadata,
        }


class PerformanceComponent(ABC):
    """パフォーマンスコンポーネントの基底クラス"""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        """基底クラスの初期化

        Args:
            config: コンポーネント設定
        """
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        self.is_initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """コンポーネントを初期化"""
        pass

    @abstractmethod
    def collect_metrics(self) -> List[PerformanceMetric]:
        """メトリクスを収集

        Returns:
            収集されたメトリクスのリスト
        """
        pass

    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """レポートを生成

        Returns:
            レポートデータ
        """
        pass

    def validate_configuration(self) -> bool:
        """設定の妥当性を検証

        Returns:
            設定が妥当かどうか
        """
        return True

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        self.logger.debug(f"{self.__class__.__name__} cleanup completed")


class MeasurementSession:
    """測定セッション管理クラス"""

    def __init__(self, name: str, description: str = "") -> None:
        """測定セッションを初期化

        Args:
            name: セッション名
            description: セッション説明
        """
        self.name = name
        self.description = description
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.components: List[PerformanceComponent] = []
        self.metrics: List[PerformanceMetric] = []
        self.logger = get_logger(__name__)

    def add_component(self, component: PerformanceComponent) -> None:
        """コンポーネントを追加

        Args:
            component: 追加するコンポーネント
        """
        if not component.is_initialized:
            component.initialize()
        self.components.append(component)

    def start(self) -> None:
        """測定セッションを開始"""
        import time

        self.start_time = time.time()
        self.logger.info(f"Measurement session '{self.name}' started")

    def stop(self) -> Dict[str, Any]:
        """測定セッションを終了

        Returns:
            セッション結果
        """
        import time

        self.end_time = time.time()

        # 全コンポーネントからメトリクスを収集
        for component in self.components:
            try:
                component_metrics = component.collect_metrics()
                self.metrics.extend(component_metrics)
            except Exception as e:
                self.logger.error(
                    f"Failed to collect metrics from {component.__class__.__name__}: {e}"
                )

        duration = self.end_time - (self.start_time or 0)
        self.logger.info(
            f"Measurement session '{self.name}' completed in {duration:.3f}s"
        )

        return {
            "session_name": self.name,
            "description": self.description,
            "duration": duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metrics_count": len(self.metrics),
            "components_count": len(self.components),
            "system_info": SystemInfo.capture().to_dict(),
        }

    def get_metrics_by_category(self, category: str) -> List[PerformanceMetric]:
        """カテゴリ別メトリクスを取得

        Args:
            category: メトリクスカテゴリ

        Returns:
            該当カテゴリのメトリクス
        """
        return [metric for metric in self.metrics if metric.category == category]

    def __enter__(self) -> "MeasurementSession":
        """コンテキストマネージャー開始"""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """コンテキストマネージャー終了"""
        self.stop()
        for component in self.components:
            component.cleanup()


# パフォーマンス測定のファクトリー関数
def create_measurement_session(name: str, description: str = "") -> MeasurementSession:
    """測定セッションを作成

    Args:
        name: セッション名
        description: セッション説明

    Returns:
        新しい測定セッション
    """
    return MeasurementSession(name, description)
