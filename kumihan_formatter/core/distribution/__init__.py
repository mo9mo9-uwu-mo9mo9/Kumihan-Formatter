"""
配布管理モジュール

Distribution Structure Manager の責任分離実装
Issue #319対応 - 単一責任原則に基づくリファクタリング

元ファイル: core/distribution_manager.py (371行) → 4つのモジュールに分割
"""

from .distribution_converter import DistributionConverter
from .distribution_manager import DistributionManager
from .distribution_processor import DistributionProcessor
from .distribution_structure import DistributionStructure

__all__ = [
    "DistributionStructure",
    "DistributionConverter",
    "DistributionProcessor",
    "DistributionManager",
]
