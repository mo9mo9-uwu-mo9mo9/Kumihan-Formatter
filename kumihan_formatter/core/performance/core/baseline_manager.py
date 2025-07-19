"""ベースラインデータ管理
Single Responsibility Principle適用: ベースライン管理の分離
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ....utilities.logger import get_logger
from .data_persistence import DataPersistence


class BaselineManager:
    """ベースラインデータ管理"""

    def __init__(self, persistence: DataPersistence) -> None:
        """ベースラインマネージャーを初期化
        Args:
            persistence: データ永続化インスタンス
        """
        self.persistence = persistence
        self.logger = get_logger(__name__)

    def save_baseline(self, name: str, data: Dict[str, Any]) -> Path:
        """ベースラインデータを保存
        Args:
            name: ベースライン名
            data: ベースラインデータ
        Returns:
            保存したファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}_baseline.json"
        baseline_data = {
            "name": name,
            "timestamp": timestamp,
            "data": data,
            "metadata": {"created_by": "BaselineManager", "version": "1.0"},
        }
        return self.persistence.save_json(baseline_data, filename, "baselines")

    def load_baseline(self, name: str) -> Optional[Dict[str, Any]]:
        """最新のベースラインデータを読み込み
        Args:
            name: ベースライン名
        Returns:
            ベースラインデータ（見つからない場合はNone）
        """
        baselines = self.persistence.list_files("baselines", f"{name}_*_baseline.json")
        if not baselines:
            return None
        # 最新のベースラインを選択
        latest_baseline = max(baselines, key=lambda p: p.stat().st_mtime)
        return self.persistence.load_json(latest_baseline.name, "baselines")

    def list_baselines(self, name_pattern: str = "*") -> List[Dict[str, Any]]:
        """ベースライン一覧を取得
        Args:
            name_pattern: 名前パターン
        Returns:
            ベースライン情報のリスト
        """
        baselines = self.persistence.list_files(
            "baselines", f"{name_pattern}_*_baseline.json"
        )
        baseline_info = []
        for baseline_file in baselines:
            try:
                data = self.persistence.load_json(baseline_file.name, "baselines")
                if data:
                    baseline_info.append(
                        {
                            "name": data.get("name", "unknown"),
                            "timestamp": data.get("timestamp", "unknown"),
                            "file_path": baseline_file,
                            "file_size": baseline_file.stat().st_size,
                        }
                    )
            except Exception as e:
                self.logger.warning(f"Failed to load baseline {baseline_file}: {e}")
        return sorted(baseline_info, key=lambda x: x["timestamp"], reverse=True)

    def delete_baseline(self, name: str, timestamp: str) -> bool:
        """指定したベースラインを削除
        Args:
            name: ベースライン名
            timestamp: タイムスタンプ
        Returns:
            削除成功かどうか
        """
        filename = f"{name}_{timestamp}_baseline.json"
        return self.persistence.delete_file(filename, "baselines")
