"""
配布構造管理 - 互換性維持用レガシーファイル

Issue #319対応: 新しいdistributionモジュールへの移行用
このファイルは既存コードとの互換性維持のために残されています。

新しいコードでは以下を使用してください:
from kumihan_formatter.core.distribution import (
    DistributionStructure, DistributionConverter,
    DistributionProcessor, DistributionManager
)
"""

# 互換性のための再エクスポート
from .distribution import (
    DistributionManager,
)


# 便利な関数（後方互換性のため）
def create_user_distribution(  # type: ignore
    source_dir, output_dir, ui=None, convert_docs=True, include_developer_docs=False
):
    """配布構造を作成（後方互換性用）"""
    manager = DistributionManager(ui)  # type: ignore
    return manager.create_user_friendly_distribution(
        source_dir, output_dir, convert_docs, include_developer_docs
    )


# 廃止予定の警告
import warnings

warnings.warn(
    "distribution_manager.py は廃止予定です。"
    "新しいコードでは kumihan_formatter.core.distribution を使用してください。",
    DeprecationWarning,
    stacklevel=2,
)
