"""
エラーコンテキストデータモデル - Issue #401対応

エラー発生時のコンテキスト情報を表現するデータクラス群。
システム情報、ファイル情報、操作情報を自動収集・管理。
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class OperationContext:
    """操作コンテキスト情報"""

    operation_name: str
    component: str  # Parser, Renderer, FileOps等
    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    user_input: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemContext:
    """システム環境コンテキスト"""

    platform: str = field(default_factory=lambda: sys.platform)
    python_version: str = field(default_factory=lambda: sys.version)
    working_directory: str = field(default_factory=lambda: os.getcwd())
    memory_usage: int | None = None
    cpu_usage: float | None = None
    disk_space: int | None = None

    def __post_init__(self) -> None:
        """システム情報を自動収集"""
        try:
            import psutil

            process = psutil.Process()
            self.memory_usage = process.memory_info().rss
            self.cpu_usage = process.cpu_percent()

            # ディスク使用量も取得
            disk_usage = psutil.disk_usage(self.working_directory)
            self.disk_space = disk_usage.free

        except ImportError:
            # psutil が利用できない場合は基本情報のみ
            pass
        except Exception:
            # エラーが発生した場合も無視（コンテキスト収集の失敗でメイン処理を止めない）
            pass


@dataclass
class FileContext:
    """ファイル操作関連コンテキスト"""

    file_path: str | None = None
    file_size: int | None = None
    last_modified: datetime | None = None
    encoding: str | None = None
    line_count: int | None = None
    is_readable: bool | None = None
    is_writable: bool | None = None

    def __post_init__(self) -> None:
        """ファイル情報を自動収集"""
        if self.file_path:
            try:
                path = Path(self.file_path)
                if path.exists():
                    stat = path.stat()
                    self.file_size = stat.st_size
                    self.last_modified = datetime.fromtimestamp(stat.st_mtime)
                    self.is_readable = os.access(path, os.R_OK)
                    self.is_writable = os.access(path, os.W_OK)

                    # エンコーディング検出
                    try:
                        with open(path, "rb") as f:
                            raw_data = f.read(1024)  # 最初の1KBで判定
                            try:
                                import chardet  # type: ignore

                                result = chardet.detect(raw_data)
                                self.encoding = result.get("encoding", "unknown")
                            except ImportError:
                                self.encoding = "utf-8"  # chardetがない場合のデフォルト
                    except Exception:
                        self.encoding = "unknown"

                    # 行数カウント（小さなファイルのみ）
                    if self.file_size and self.file_size < 1024 * 1024:  # 1MB未満
                        try:
                            with open(
                                path, "r", encoding=self.encoding or "utf-8"
                            ) as f:
                                self.line_count = sum(1 for _ in f)
                        except Exception:
                            pass

            except Exception:
                # ファイル情報の取得に失敗してもメイン処理を止めない
                pass

    def to_dict(self) -> dict[str, Any]:
        """辞書形式でファイル情報を返す"""
        return {
            "file_path": self.file_path,
            "file_size": self.file_size,
            "last_modified": (
                self.last_modified.isoformat() if self.last_modified else None
            ),
            "encoding": self.encoding,
            "line_count": self.line_count,
            "is_readable": self.is_readable,
            "is_writable": self.is_writable,
        }

    def get_file_summary(self) -> str:
        """ファイル情報の要約を返す"""
        if not self.file_path:
            return "No file specified"

        path = Path(self.file_path)
        if not path.exists():
            return f"File not found: {self.file_path}"

        parts = []
        if self.file_size is not None:
            if self.file_size < 1024:
                parts.append(f"{self.file_size} bytes")
            elif self.file_size < 1024 * 1024:
                parts.append(f"{self.file_size / 1024:.1f} KB")
            else:
                parts.append(f"{self.file_size / (1024 * 1024):.1f} MB")

        if self.line_count:
            parts.append(f"{self.line_count} lines")

        if self.encoding:
            parts.append(f"encoding: {self.encoding}")

        permissions = []
        if self.is_readable:
            permissions.append("readable")
        if self.is_writable:
            permissions.append("writable")
        if permissions:
            parts.append(f"permissions: {', '.join(permissions)}")

        return f"{path.name} ({', '.join(parts)})" if parts else str(path.name)
