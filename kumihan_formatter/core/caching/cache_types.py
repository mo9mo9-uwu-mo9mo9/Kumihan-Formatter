"""
キャッシュシステム - 型定義

キャッシュエントリとメタデータの管理
Issue #319対応 - smart_cache.py から分離
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class CacheEntry:
    """キャッシュエントリとメタデータ"""

    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: Optional[int] = None

    def is_expired(self) -> bool:
        """キャッシュエントリが期限切れかチェック"""
        if self.ttl_seconds is None:
            return False

        age = datetime.now() - self.created_at
        return age.total_seconds() > self.ttl_seconds

    def update_access(self) -> None:
        """アクセス統計を更新"""
        self.last_accessed = datetime.now()
        self.access_count += 1
