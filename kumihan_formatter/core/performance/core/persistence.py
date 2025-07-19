"""パフォーマンス監視システムのデータ永続化管理
Single Responsibility Principle適用: データ保存・読み込み処理の一元化
Issue #476 Phase2対応 - パフォーマンスモジュール統合

分割後の統合インターフェース:
- data_persistence.py: 基本データ永続化
- baseline_manager.py: ベースライン管理
- report_exporter.py: レポートエクスポート
"""

# 後方互換性のために既存のAPIを再エクスポート
from .baseline_manager import BaselineManager
from .data_persistence import (
    DataPersistence,
    get_global_persistence,
    initialize_persistence,
)
from .report_exporter import ReportExporter

__all__ = [
    "DataPersistence",
    "BaselineManager",
    "ReportExporter",
    "get_global_persistence",
    "initialize_persistence",
]
