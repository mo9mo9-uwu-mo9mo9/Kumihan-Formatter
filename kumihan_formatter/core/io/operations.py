"""ファイル操作実装

統合されたファイル操作の実装
"""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Union

from .protocols import FileProtocol, PathProtocol
from .validators import FileValidator, PathValidator


class FileOperations(FileProtocol):
    """統合ファイル操作クラス"""

    def __init__(self) -> None:
        self._validator = FileValidator()
        self._path_validator = PathValidator()

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """ファイルをテキストとして読み込み"""
        if not self._validator.validate_readable(path):
            errors = self._validator.get_errors()
            raise FileNotFoundError(f"ファイル読み込みエラー: {'; '.join(errors)}")

        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as e:
            raise ValueError(f"エンコーディングエラー: {e}")
        except Exception as e:
            raise IOError(f"ファイル読み込み失敗: {e}")

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを書き込み"""
        # 親ディレクトリ作成
        path.parent.mkdir(parents=True, exist_ok=True)

        if not self._validator.validate_writable(path):
            errors = self._validator.get_errors()
            raise PermissionError(f"ファイル書き込みエラー: {'; '.join(errors)}")

        try:
            path.write_text(content, encoding=encoding)
        except Exception as e:
            raise IOError(f"ファイル書き込み失敗: {e}")

    def read_binary(self, path: Path) -> bytes:
        """ファイルをバイナリとして読み込み"""
        if not self._validator.validate_readable(path):
            errors = self._validator.get_errors()
            raise FileNotFoundError(f"ファイル読み込みエラー: {'; '.join(errors)}")

        try:
            return path.read_bytes()
        except Exception as e:
            raise IOError(f"バイナリファイル読み込み失敗: {e}")

    def write_binary(self, path: Path, data: bytes) -> None:
        """ファイルにバイナリデータを書き込み"""
        # 親ディレクトリ作成
        path.parent.mkdir(parents=True, exist_ok=True)

        if not self._validator.validate_writable(path):
            errors = self._validator.get_errors()
            raise PermissionError(f"ファイル書き込みエラー: {'; '.join(errors)}")

        try:
            path.write_bytes(data)
        except Exception as e:
            raise IOError(f"バイナリファイル書き込み失敗: {e}")

    def copy_file(self, src: Path, dst: Path) -> None:
        """ファイルコピー"""
        if not self._validator.validate_readable(src):
            errors = self._validator.get_errors()
            raise FileNotFoundError(f"コピー元ファイルエラー: {'; '.join(errors)}")

        # 親ディレクトリ作成
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(src, dst)
        except Exception as e:
            raise IOError(f"ファイルコピー失敗: {e}")

    def move_file(self, src: Path, dst: Path) -> None:
        """ファイル移動"""
        if not self._validator.validate_readable(src):
            errors = self._validator.get_errors()
            raise FileNotFoundError(f"移動元ファイルエラー: {'; '.join(errors)}")

        # 親ディレクトリ作成
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(src), str(dst))
        except Exception as e:
            raise IOError(f"ファイル移動失敗: {e}")

    def delete_file(self, path: Path) -> None:
        """ファイル削除"""
        if not path.exists():
            return  # 存在しない場合は何もしない

        if not path.is_file():
            raise ValueError(f"ファイルではありません: {path}")

        try:
            path.unlink()
        except Exception as e:
            raise IOError(f"ファイル削除失敗: {e}")

    def exists(self, path: Path) -> bool:
        """ファイル/ディレクトリの存在確認"""
        return path.exists()

    def is_file(self, path: Path) -> bool:
        """ファイルかどうかの確認"""
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """ディレクトリかどうかの確認"""
        return path.is_dir()

    def get_file_info(self, path: Path) -> Dict[str, Any]:
        """ファイル情報取得"""
        if not path.exists():
            raise FileNotFoundError(f"ファイルが存在しません: {path}")

        stat = path.stat()
        return {
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "extension": path.suffix,
        }

    def list_files(
        self, directory: Path, pattern: str = "*", recursive: bool = False
    ) -> List[Path]:
        """ディレクトリ内のファイル一覧取得"""
        if not directory.exists():
            raise FileNotFoundError(f"ディレクトリが存在しません: {directory}")

        if not directory.is_dir():
            raise ValueError(f"ディレクトリではありません: {directory}")

        if recursive:
            return list(directory.rglob(pattern))
        else:
            return list(directory.glob(pattern))


class PathOperations(PathProtocol):
    """パス操作クラス"""

    def __init__(self) -> None:
        self._validator = PathValidator()

    def resolve_path(self, path: Union[str, Path]) -> Path:
        """パスの正規化・解決"""
        if isinstance(path, str):
            if not self._validator.validate_path(Path(path)):
                # エラーメッセージ取得の試み
                try:
                    errors = self._validator.get_errors() if hasattr(self._validator, 'get_errors') else ["パス検証失敗"]
                    raise ValueError(f"無効なパス形式: {'; '.join(errors)}")
                except AttributeError:
                    raise ValueError(f"無効なパス形式: {path}")
            path = Path(path)

        try:
            return path.resolve()
        except Exception as e:
            raise ValueError(f"パス解決失敗: {e}")

    def ensure_parent_dir(self, path: Path) -> None:
        """親ディレクトリの作成（存在しない場合）"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise IOError(f"ディレクトリ作成失敗: {e}")

    def validate_path(self, path: Path) -> bool:
        """パスの有効性検証"""
        # 循環参照を避けるため、基本的な検証を実行
        try:
            if hasattr(self._validator, 'validate_path'):
                return self._validator.validate_path(path)
            else:
                # フォールバック: 基本的なパス検証
                return path.is_absolute() or len(str(path)) > 0
        except Exception:
            return False

    def get_relative_path(self, path: Path, base: Path) -> Path:
        """相対パスの取得"""
        try:
            return path.relative_to(base)
        except ValueError:
            # 相対パスにできない場合は絶対パスを返す
            return path.resolve()

    def join_paths(self, *parts: str) -> Path:
        """パスの結合"""
        if not parts:
            raise ValueError("パス要素が指定されていません")

        result = Path(parts[0])
        for part in parts[1:]:
            result = result / part

        return result

    def get_safe_filename(self, filename: str) -> str:
        """安全なファイル名の生成"""
        # 禁止文字の置換
        forbidden_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
        safe_name = filename

        for char in forbidden_chars:
            safe_name = safe_name.replace(char, "_")

        # 長さ制限
        if len(safe_name) > 200:
            name_part = safe_name[:190]
            ext_part = Path(safe_name).suffix[-10:] if Path(safe_name).suffix else ""
            safe_name = name_part + ext_part

        return safe_name
