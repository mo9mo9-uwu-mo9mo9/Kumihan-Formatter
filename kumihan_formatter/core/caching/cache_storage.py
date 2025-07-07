"""
キャッシュシステム - ストレージ管理

メモリ・ファイルキャッシュの管理とI/O処理
Issue #319対応 - smart_cache.py から分離
"""

import hashlib
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..common.error_framework import ErrorCategory, KumihanError
from .cache_strategies import CacheStrategy
from .cache_types import CacheEntry


class CacheStorage:
    """キャッシュストレージ管理クラス

    責任: メモリ・ファイルキャッシュのI/O・削除戦略の実行
    """

    def __init__(
        self,
        name: str,
        max_memory_entries: int,
        max_memory_bytes: int,
        strategy: CacheStrategy,
        cache_dir: Path | None = None,
        enable_file_cache: bool = True,
    ):
        """
        Args:
            name: キャッシュ名
            max_memory_entries: メモリ最大エントリ数
            max_memory_bytes: メモリ最大使用量（バイト）
            strategy: キャッシュ戦略
            cache_dir: ファイルキャッシュディレクトリ
            enable_file_cache: ファイルキャッシュを有効にするか
        """
        self.name = name
        self.max_memory_entries = max_memory_entries
        self.max_memory_bytes = max_memory_bytes
        self.strategy = strategy
        self.enable_file_cache = enable_file_cache

        # メモリキャッシュ
        self._memory_cache: dict[str, CacheEntry] = {}
        self._memory_size = 0

        # ファイルキャッシュ
        if enable_file_cache:
            self.cache_dir = cache_dir or Path.cwd() / ".kumihan_cache" / name
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None  # type: ignore

    def calculate_size(self, value: Any) -> int:
        """値のサイズを推定（バイト）"""
        try:
            if isinstance(value, str):
                return len(value.encode("utf-8"))
            elif isinstance(value, (bytes, bytearray)):
                return len(value)
            else:
                # その他の型はpickleを使用
                return len(pickle.dumps(value))
        except Exception:
            # フォールバック推定
            return 1024  # 1KBデフォルト

    def get_from_memory(self, key: str) -> CacheEntry | None:
        """メモリキャッシュから取得"""
        entry = self._memory_cache.get(key)
        if entry and not entry.is_expired():
            entry.update_access()
            return entry
        elif entry:
            # 期限切れエントリを削除
            self._remove_from_memory(key)
        return None

    def store_in_memory(self, key: str, entry: CacheEntry) -> None:
        """メモリキャッシュに保存"""
        # 既存エントリがある場合は削除
        if key in self._memory_cache:
            self._remove_from_memory(key)

        # サイズを計算
        entry.size_bytes = self.calculate_size(entry.value)

        # メモリキャッシュに追加
        self._memory_cache[key] = entry
        self._memory_size += entry.size_bytes

        # 必要に応じて削除
        self._evict_entries()

    def _remove_from_memory(self, key: str) -> bool:
        """メモリキャッシュから削除"""
        if key in self._memory_cache:
            entry = self._memory_cache.pop(key)
            self._memory_size -= entry.size_bytes or 0
            return True
        return False

    def save_to_file(self, key: str, entry: CacheEntry) -> bool:
        """ファイルキャッシュに保存"""
        if not self.enable_file_cache:
            return False

        try:
            file_path = self._get_file_path(key)

            cache_data = {
                "value": entry.value,
                "created_at": entry.created_at.isoformat(),
                "ttl_seconds": entry.ttl_seconds,
                "key": key,  # 検証用に元のキーを保存
            }

            with open(file_path, "wb") as f:
                pickle.dump(cache_data, f)

            return True

        except Exception as e:
            # エラーをログ出力するが失敗しない
            print(f"Warning: Failed to save cache entry to file: {e}")
            return False

    def load_from_file(self, key: str) -> CacheEntry | None:
        """ファイルキャッシュから読み込み"""
        if not self.enable_file_cache:
            return None

        try:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return None

            with open(file_path, "rb") as f:
                cache_data = pickle.load(f)

            # キーが一致するか検証
            if cache_data.get("key") != key:
                return None

            # エントリを再構築
            entry = CacheEntry(
                value=cache_data["value"],
                created_at=datetime.fromisoformat(cache_data["created_at"]),
                last_accessed=datetime.now(),
                ttl_seconds=cache_data.get("ttl_seconds"),
            )

            # 期限切れをチェック
            if entry.is_expired():
                file_path.unlink(missing_ok=True)
                return None

            return entry

        except Exception:
            # 破損ファイルを削除
            try:
                self._get_file_path(key).unlink(missing_ok=True)
            except Exception:
                pass
            return None

    def _evict_entries(self) -> int:
        """戦略に基づいてエントリを削除"""
        evicted_count = 0

        if not self._memory_cache:
            return evicted_count

        # まず期限切れエントリを削除
        expired_keys = [
            key for key, entry in self._memory_cache.items() if entry.is_expired()
        ]

        for key in expired_keys:
            if self._remove_from_memory(key):
                evicted_count += 1

        # まだ制限を超えている場合は戦略を使用
        while (
            len(self._memory_cache) > self.max_memory_entries
            or self._memory_size > self.max_memory_bytes
        ):

            if not self._memory_cache:
                break

            # 最も優先度の低いエントリを検索
            min_priority = float("inf")
            evict_key = None

            for key, entry in self._memory_cache.items():
                priority = self.strategy.get_priority(entry)
                if priority < min_priority:
                    min_priority = priority
                    evict_key = key

            if evict_key and self._remove_from_memory(evict_key):
                evicted_count += 1
            else:
                break

        return evicted_count

    def _generate_cache_key(self, key: str) -> str:
        """ファイル保存用の安全なキャッシュキーを生成"""
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def _get_file_path(self, key: str) -> Path:
        """キャッシュキーのファイルパスを取得"""
        if not self.cache_dir:
            raise KumihanError(
                "File cache not enabled", category=ErrorCategory.CONFIGURATION
            )

        safe_key = self._generate_cache_key(key)
        return self.cache_dir / f"{safe_key}.cache"

    def clear_memory(self) -> None:
        """メモリキャッシュをクリア"""
        self._memory_cache.clear()
        self._memory_size = 0

    def get_memory_stats(self) -> dict[str, int]:
        """メモリキャッシュの統計を取得"""
        return {
            "entries": len(self._memory_cache),
            "size_bytes": self._memory_size,
            "max_entries": self.max_memory_entries,
            "max_bytes": self.max_memory_bytes,
        }
