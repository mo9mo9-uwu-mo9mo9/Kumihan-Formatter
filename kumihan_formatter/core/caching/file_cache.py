"""
ファイルキャッシュ - 専用実装

ファイル読み込みとハッシュベースキャッシュ
Issue #402対応 - パフォーマンス最適化
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from ..performance import get_global_monitor
from .cache_strategies import AdaptiveStrategy
from .smart_cache import SmartCache


class FileCache(SmartCache):
    """ファイル読み込み専用キャッシュ

    機能:
    - ファイルのハッシュベース検証
    - 修正時刻によるキャッシュ無効化
    - ファイルサイズに応じた戦略切り替え
    - パフォーマンス統計の収集
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_memory_mb: float = 50.0,
        max_entries: int = 500,
        default_ttl: int = 7200,  # 2時間
    ):
        """ファイルキャッシュを初期化

        Args:
            cache_dir: キャッシュディレクトリ
            max_memory_mb: 最大メモリ使用量（MB）
            max_entries: 最大エントリ数
            default_ttl: デフォルト有効期限（秒）
        """
        super().__init__(
            name="file_cache",
            max_memory_entries=max_entries,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl,
            strategy=AdaptiveStrategy(frequency_weight=0.7, size_weight=0.3),
            cache_dir=cache_dir,
            enable_file_cache=True,
        )

        # ファイル情報のキャッシュ
        self._file_info: Dict[str, Dict[str, Any]] = {}

    def get_file_content(self, file_path: Path) -> Optional[str]:
        """ファイル内容をキャッシュから取得または読み込み

        Args:
            file_path: 読み込むファイルパス

        Returns:
            ファイル内容またはNone
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        # ファイル情報を取得
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            modified_time = stat.st_mtime
        except OSError:
            return None

        # キャッシュキーを生成
        cache_key = self._generate_file_cache_key(file_path)

        # キャッシュされた情報と比較
        cached_info = self._file_info.get(cache_key)
        if cached_info and cached_info["modified_time"] == modified_time:
            # ファイルが変更されていない場合、キャッシュから取得
            with get_global_monitor().measure("file_cache_hit", file_size=file_size):
                content = self.get(cache_key)
                if content is not None:
                    return content

        # ファイルを読み込み
        with get_global_monitor().measure("file_read", file_size=file_size):
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = file_path.read_text(encoding="shift_jis")
                except UnicodeDecodeError:
                    return None
            except Exception:
                return None

        # キャッシュに保存
        self._cache_file_content(
            cache_key, content, file_path, modified_time, file_size
        )

        return content

    def get_file_hash(self, file_path: Path) -> Optional[str]:
        """ファイルのハッシュ値をキャッシュから取得または計算

        Args:
            file_path: 対象ファイルパス

        Returns:
            ファイルのMD5ハッシュ値
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        # ファイル情報を取得
        try:
            stat = file_path.stat()
            modified_time = stat.st_mtime
        except OSError:
            return None

        # ハッシュ用キャッシュキー
        hash_key = f"hash_{self._generate_file_cache_key(file_path)}"

        # キャッシュされた情報と比較
        cached_info = self._file_info.get(hash_key)
        if cached_info and cached_info["modified_time"] == modified_time:
            hash_value = self.get(hash_key)
            if hash_value is not None:
                return hash_value

        # ハッシュを計算
        with get_global_monitor().measure("file_hash_calculation"):
            try:
                hash_value = self._calculate_file_hash(file_path)
            except Exception:
                return None

        # キャッシュに保存
        self.set(hash_key, hash_value, ttl=self.default_ttl)
        self._file_info[hash_key] = {
            "modified_time": modified_time,
            "file_path": str(file_path),
        }

        return hash_value

    def invalidate_file(self, file_path: Path) -> bool:
        """特定ファイルのキャッシュを無効化

        Args:
            file_path: 無効化するファイルパス

        Returns:
            無効化が成功したかどうか
        """
        cache_key = self._generate_file_cache_key(file_path)
        hash_key = f"hash_{cache_key}"

        success = False

        # コンテンツキャッシュを削除
        if self.delete(cache_key):
            success = True

        # ハッシュキャッシュを削除
        if self.delete(hash_key):
            success = True

        # ファイル情報を削除
        self._file_info.pop(cache_key, None)
        self._file_info.pop(hash_key, None)

        return success

    def cleanup_stale_entries(self) -> int:
        """存在しないファイルのキャッシュエントリを削除

        Returns:
            削除されたエントリ数
        """
        cleanup_count = 0
        stale_keys = []

        # 存在しないファイルを特定
        for key, info in self._file_info.items():
            file_path = Path(info["file_path"])
            if not file_path.exists():
                stale_keys.append(key)

        # 古いエントリを削除
        for key in stale_keys:
            if self.delete(key):
                cleanup_count += 1
            self._file_info.pop(key, None)

        return cleanup_count

    def _generate_file_cache_key(self, file_path: Path) -> str:
        """ファイルパスからキャッシュキーを生成"""
        abs_path = str(file_path.resolve())
        return f"file_{hashlib.md5(abs_path.encode('utf-8')).hexdigest()}"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのMD5ハッシュを計算"""
        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            # 大きなファイルの場合はチャンクごとに読み込み
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _cache_file_content(
        self,
        cache_key: str,
        content: str,
        file_path: Path,
        modified_time: float,
        file_size: int,
    ) -> None:
        """ファイル内容をキャッシュに保存"""
        # TTLをファイルサイズに応じて調整
        ttl = self._calculate_ttl_for_file_size(file_size)

        # キャッシュに保存
        self.set(cache_key, content, ttl=ttl)

        # ファイル情報を記録
        self._file_info[cache_key] = {
            "modified_time": modified_time,
            "file_path": str(file_path),
            "file_size": file_size,
        }

    def _calculate_ttl_for_file_size(self, file_size: int) -> int:
        """ファイルサイズに応じたTTLを計算"""
        # 小さなファイルは短いTTL、大きなファイルは長いTTL
        if file_size < 1024:  # 1KB未満
            return 1800  # 30分
        elif file_size < 10240:  # 10KB未満
            return 3600  # 1時間
        elif file_size < 102400:  # 100KB未満
            return 7200  # 2時間
        else:  # 100KB以上
            return 14400  # 4時間

    def get_cache_stats(self) -> Dict[str, Any]:
        """ファイルキャッシュの統計情報を取得"""
        base_stats = self.get_stats()

        # ファイル固有の統計を追加
        total_files = len(self._file_info)
        total_size = sum(info.get("file_size", 0) for info in self._file_info.values())

        base_stats.update(
            {
                "cached_files": total_files,
                "total_cached_size": total_size,
                "avg_file_size": total_size / total_files if total_files > 0 else 0,
            }
        )

        return base_stats
