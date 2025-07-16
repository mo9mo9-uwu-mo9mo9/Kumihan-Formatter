"""
最適化効果分析ツール - パフォーマンス改善の定量的評価（分割後統合インポート）

キャッシュ最適化とパフォーマンス向上の効果を測定・分析
Issue #402対応 - パフォーマンス最適化

このファイルは技術的負債解消（Issue #476）により分割されました：
- optimization/models.py: データモデル
- optimization/analyzer.py: 分析ロジック
"""

# 後方互換性のため、分割されたモジュールからインポート
from .optimization import OptimizationAnalyzer, OptimizationMetrics, OptimizationReport

__all__ = [
    "OptimizationAnalyzer",
    "OptimizationMetrics",
    "OptimizationReport",
]
