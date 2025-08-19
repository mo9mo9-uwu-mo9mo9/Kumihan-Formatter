"""
Kumihan-Formatter 品質ダッシュボード

Phase 4-3: 品質ダッシュボード構築
- リアルタイム品質可視化
- メトリクス収集システム
- 品質トレンド分析
- 包括的レポート生成
"""

from .dashboard import QualityDashboard
from .metrics_collector import MetricsCollector
from .report_generator import ReportGenerator

__all__ = ["QualityDashboard", "MetricsCollector", "ReportGenerator"]

__version__ = "1.0.0"
