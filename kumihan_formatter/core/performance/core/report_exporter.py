"""レポートエクスポート機能
Single Responsibility Principle適用: レポート出力の分離
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from kumihan_formatter.core.utilities.logger import get_logger

from .data_persistence import DataPersistence


class ReportExporter:
    """レポートエクスポート機能"""

    def __init__(self, persistence: DataPersistence) -> None:
        """レポートエクスポーターを初期化
        Args:
            persistence: データ永続化インスタンス
        """
        self.persistence = persistence
        self.logger = get_logger(__name__)

    def export_report(
        self, report_data: Dict[str, Any], report_type: str = "benchmark"
    ) -> Path:
        """レポートをエクスポート
        Args:
            report_data: レポートデータ
            report_type: レポートタイプ
        Returns:
            エクスポートしたファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{timestamp}.json"
        export_data = {
            "report_type": report_type,
            "timestamp": timestamp,
            "data": report_data,
            "metadata": {"exported_by": "ReportExporter", "version": "1.0"},
        }
        return self.persistence.save_json(export_data, filename, "reports")

    def export_summary(self, summary_data: Dict[str, Any]) -> Path:
        """サマリーをエクスポート
        Args:
            summary_data: サマリーデータ
        Returns:
            エクスポートしたファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_summary_{timestamp}.json"
        return self.persistence.save_json(summary_data, filename, "summaries")
