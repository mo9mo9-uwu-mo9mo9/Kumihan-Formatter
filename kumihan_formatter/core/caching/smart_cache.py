"""
キャッシュシステム - メイン制御

スマートキャッシュのメイン制御とAPI
Issue #319対応 - smart_cache.py から分離
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar

from .cache_storage import CacheStorage
from .cache_strategies import CacheStrategy, LRUStrategy
from .cache_types import CacheEntry

T = TypeVar("T")


class SmartCache:
    """インテリジェントキャッシュシステム

    機能:
    - メモリ・ファイルベースキャッシュ
    - 複数の削除戦略
    - 自動サイズ管理
    - パフォーマンスメトリクス
    - ハッシュベースキャッシュ検証

    責任: キャッシュの統合管理・API提供・統計管理
    """

    def __init__(
        self,
        name: str = "default",
        max_memory_entries: int = 1000,
        max_memory_mb: float = 100.0,
        default_ttl: int = 3600,  # 1時間
        strategy: CacheStrategy | None = None,  # type: ignore
        cache_dir: Optional[Path] = None,
        enable_file_cache: bool = True,
    ):
        """スマートキャッシュを初期化

        Args:
            name: キャッシュインスタンス名
            max_memory_entries: メモリエントリの最大数
            max_memory_mb: 最大メモリ使用量（MB）
            default_ttl: デフォルトTTL（秒）
            strategy: キャッシュ削除戦略
            cache_dir: ファイルキャッシュディレクトリ
            enable_file_cache: ファイルキャッシュを有効にするか
        """
        self.name = name
        self.default_ttl = default_ttl
        self.strategy = strategy or LRUStrategy()

        # ストレージ管理
        self.storage = CacheStorage(
            name=name,
            max_memory_entries=max_memory_entries,
            max_memory_bytes=int(max_memory_mb * 1024 * 1024),
            strategy=self.strategy,
            cache_dir=cache_dir,
            enable_file_cache=enable_file_cache,
        )

        # 統計
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "file_cache_hits": 0,
            "file_cache_misses": 0,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """キャッシュから値を取得

        Args:
            key: キャッシュキー
            default: キーが見つからない場合のデフォルト値

        Returns:
            キャッシュされた値またはデフォルト値
        """
        # メモリキャッシュから試行
        entry = self.storage.get_from_memory(key)
        if entry:
            self.stats["hits"] += 1
            return entry.value

        # ファイルキャッシュから試行
        entry = self.storage.load_from_file(key)
        if entry:
            # メモリキャッシュに昇格
            self.storage.store_in_memory(key, entry)
            self.stats["file_cache_hits"] += 1
            self.stats["hits"] += 1
            return entry.value

        # キャッシュミス
        self.stats["misses"] += 1
        self.stats["file_cache_misses"] += 1
        return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """キャッシュに値を設定

        Args:
            key: キャッシュキー
            value: 保存する値
            ttl: 生存時間（秒）、未指定時はデフォルトTTL
        """
        ttl = ttl if ttl is not None else self.default_ttl

        entry = CacheEntry(
            value=value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl,
        )

        # メモリキャッシュに保存
        self.storage.store_in_memory(key, entry)

        # ファイルキャッシュにも保存
        self.storage.save_to_file(key, entry)

    def get_or_compute(
        self, key: str, compute_func: Callable[[], T], ttl: Optional[int] = None
    ) -> T:
        """キャッシュから取得、なければ計算して保存

        Args:
            key: キャッシュキー
            compute_func: 値を計算する関数
            ttl: 生存時間（秒）

        Returns:
            キャッシュされた値または計算された値
        """
        # キャッシュから試行
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value  # type: ignore

        # 計算して保存
        computed_value = compute_func()
        self.set(key, computed_value, ttl)
        return computed_value

    def delete(self, key: str) -> bool:
        """キャッシュからキーを削除

        Args:
            key: 削除するキー

        Returns:
            削除が成功したかどうか
        """
        success = False

        # メモリキャッシュから削除
        if self.storage._remove_from_memory(key):
            success = True

        # ファイルキャッシュから削除
        try:
            file_path = self.storage._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
                success = True
        except Exception:
            pass

        return success

    def clear(self) -> None:
        """全キャッシュをクリア"""
        self.storage.clear_memory()

        # ファイルキャッシュもクリア
        if self.storage.cache_dir and self.storage.cache_dir.exists():
            for cache_file in self.storage.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass

    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        memory_stats = self.storage.get_memory_stats()

        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "cache_name": self.name,
            "memory_stats": memory_stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            **self.stats,
        }

    def invalidate_expired(self) -> int:
        """期限切れエントリを手動で削除

        Returns:
            削除されたエントリ数
        """
        return self.storage._evict_entries()
