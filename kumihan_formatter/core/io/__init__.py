"""
配布管理モジュール

Distribution Structure Manager の責任分離実装
Issue #319対応 - 単一責任原則に基づくリファクタリング

元ファイル: core/distribution_manager.py (371行) → 4つのモジュールに分割
"""

__all__ = [
    "DistributionStructure",
    "DistributionConverter",
    "DistributionProcessor",
    "DistributionManager",
]
