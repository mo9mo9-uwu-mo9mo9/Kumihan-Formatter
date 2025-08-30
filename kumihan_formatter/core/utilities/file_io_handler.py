"""ファイルI/Oハンドラモジュール

Issue #1217対応: ディレクトリ構造最適化によるファイルI/O機能
"""

import shutil
from pathlib import Path
from typing import List, Optional, Union

from .logger import get_logger


class FileIOHandler:
    """ファイルI/Oハンドラクラス - 基本的なファイル操作"""

    def __init__(self) -> None:
        """FileIOHandler初期化"""
        self.logger = get_logger(__name__)

    def read_file(
        self, file_path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[str]:
        """ファイル読み込み"""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return None

    def write_file(
        self, file_path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> bool:
        """ファイル書き込み"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            return False

    def read_lines(
        self, file_path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[List[str]]:
        """ファイル行読み込み"""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.readlines()
        except Exception as e:
            self.logger.error(f"Failed to read lines from {file_path}: {e}")
            return None

    def write_lines(
        self, file_path: Union[str, Path], lines: List[str], encoding: str = "utf-8"
    ) -> bool:
        """ファイル行書き込み"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding=encoding) as f:
                f.writelines(lines)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write lines to {file_path}: {e}")
            return False

    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """ファイルコピー"""
        try:
            dst_path = Path(dst)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy file {src} to {dst}: {e}")
            return False

    def move_file(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """ファイル移動"""
        try:
            dst_path = Path(dst)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return True
        except Exception as e:
            self.logger.error(f"Failed to move file {src} to {dst}: {e}")
            return False

    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """ファイル削除"""
        try:
            Path(file_path).unlink()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """ファイル存在確認"""
        return Path(file_path).exists()

    def get_file_size(self, file_path: Union[str, Path]) -> Optional[int]:
        """ファイルサイズ取得"""
        try:
            return Path(file_path).stat().st_size
        except Exception as e:
            self.logger.error(f"Failed to get file size for {file_path}: {e}")
            return None
