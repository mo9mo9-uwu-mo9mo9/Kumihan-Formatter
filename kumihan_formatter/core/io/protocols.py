"""ファイル操作プロトコル定義

統一されたインターフェース定義
"""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FileProtocol(Protocol):
    """ファイル操作の統一プロトコル"""

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """ファイルをテキストとして読み込み"""
        ...

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを書き込み"""
        ...

    def exists(self, path: Path) -> bool:
        """ファイル/ディレクトリの存在確認"""
        ...

    def is_file(self, path: Path) -> bool:
        """ファイルかどうかの確認"""
        ...

    def is_dir(self, path: Path) -> bool:
        """ディレクトリかどうかの確認"""
        ...


@runtime_checkable
class PathProtocol(Protocol):
    """パス操作の統一プロトコル"""

    def resolve_path(self, path: str | Path) -> Path:
        """パスの正規化・解決"""
        ...

    def ensure_parent_dir(self, path: Path) -> None:
        """親ディレクトリの作成（存在しない場合）"""
        ...

    def validate_path(self, path: Path) -> bool:
        """パスの有効性検証"""
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """検証の統一プロトコル"""

    def validate(self, target: Any) -> bool:
        """対象の検証"""
        ...

    def get_errors(self) -> list[str]:
        """エラーメッセージの取得"""
        ...
