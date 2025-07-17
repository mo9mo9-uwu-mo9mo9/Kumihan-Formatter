"""パフォーマンス監視システムのデータ永続化管理
Single Responsibility Principle適用: データ保存・読み込み処理の一元化
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from ...utilities.logger import get_logger
class DataPersistence:
    """データ永続化の統一インターフェース"""
    def __init__(self, base_directory: Path | None = None) -> None:
        """データ永続化を初期化
        Args:
            base_directory: 基本ディレクトリ
        """
        self.base_directory = base_directory or Path("./performance_data")
        self.base_directory.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
    def save_json(self, data: Any, filename: str, subdirectory: str = "") -> Path:
        """JSON形式でデータを保存
        Args:
            data: 保存するデータ
            filename: ファイル名
            subdirectory: サブディレクトリ
        Returns:
            保存したファイルのパス
        """
        save_dir = (
            self.base_directory / subdirectory if subdirectory else self.base_directory
        )
        save_dir.mkdir(parents=True, exist_ok=True)
        filepath = save_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    data, f, indent=2, ensure_ascii=False, default=self._json_serializer
                )
            self.logger.debug(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save data to {filepath}: {e}")
            raise
    def load_json(self, filename: str, subdirectory: str = "") -> Dict[str, Any] | None:
        """JSON形式でデータを読み込み
        Args:
            filename: ファイル名
            subdirectory: サブディレクトリ
        Returns:
            読み込んだデータ
        """
        load_dir = (
            self.base_directory / subdirectory if subdirectory else self.base_directory
        )
        filepath = load_dir / filename
        if not filepath.exists():
            self.logger.warning(f"File not found: {filepath}")
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
            self.logger.debug(f"Data loaded from {filepath}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load data from {filepath}: {e}")
            raise
    def list_files(self, subdirectory: str = "", pattern: str = "*.json") -> List[Path]:
        """ファイル一覧を取得
        Args:
            subdirectory: サブディレクトリ
            pattern: ファイルパターン
        Returns:
            ファイルパスのリスト
        """
        search_dir = (
            self.base_directory / subdirectory if subdirectory else self.base_directory
        )
        if not search_dir.exists():
            return []
        return list(search_dir.glob(pattern))
    def delete_file(self, filename: str, subdirectory: str = "") -> bool:
        """ファイルを削除
        Args:
            filename: ファイル名
            subdirectory: サブディレクトリ
        Returns:
            削除成功かどうか
        """
        delete_dir = (
            self.base_directory / subdirectory if subdirectory else self.base_directory
        )
        filepath = delete_dir / filename
        if not filepath.exists():
            self.logger.warning(f"File not found for deletion: {filepath}")
            return False
        try:
            filepath.unlink()
            self.logger.debug(f"File deleted: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {filepath}: {e}")
            return False
    def cleanup_old_files(self, subdirectory: str = "", max_age_days: int = 30) -> int:
        """古いファイルをクリーンアップ
        Args:
            subdirectory: サブディレクトリ
            max_age_days: 最大保持日数
        Returns:
            削除したファイル数
        """
        import time
        cleanup_dir = (
            self.base_directory / subdirectory if subdirectory else self.base_directory
        )
        if not cleanup_dir.exists():
            return 0
        current_time = time.time()
        cutoff_time = current_time - (max_age_days * 24 * 60 * 60)
        deleted_count = 0
        for filepath in cleanup_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    deleted_count += 1
                    self.logger.debug(f"Deleted old file: {filepath}")
                except Exception as e:
                    self.logger.error(f"Failed to delete old file {filepath}: {e}")
        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old files from {cleanup_dir}")
        return deleted_count
    def _json_serializer(self, obj: Any) -> str:
        """JSON シリアライザー
        Args:
            obj: シリアライズ対象オブジェクト
        Returns:
            シリアライズされた文字列
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "to_dict"):
            return str(obj.to_dict())
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
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
# グローバルインスタンス
_global_persistence: Optional[DataPersistence] = None
def get_global_persistence() -> DataPersistence:
    """グローバルなデータ永続化インスタンスを取得
    Returns:
        データ永続化インスタンス
    """
    global _global_persistence
    if _global_persistence is None:
        _global_persistence = DataPersistence()
    return _global_persistence
def initialize_persistence(base_directory: Path | None = None) -> DataPersistence:
    """データ永続化を初期化
    Args:
        base_directory: 基本ディレクトリ
    Returns:
        データ永続化インスタンス
    """
    global _global_persistence
    _global_persistence = DataPersistence(base_directory)
    return _global_persistence
