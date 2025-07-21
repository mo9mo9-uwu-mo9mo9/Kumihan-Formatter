"""File management model for Kumihan-Formatter GUI

Single Responsibility Principle適用: ファイル管理モデルの分離
Issue #476 Phase2対応 - gui_models.py分割（2/3）
Issue #516 Phase 5A対応 - Thread-Safe設計とエラーハンドリング強化
"""

import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional


class FileManager:
    """ファイル操作管理クラス（Thread-Safe対応）

    ファイル選択、パス管理、出力パス生成等のファイル関連処理
    マルチスレッド環境での安全なファイル操作を保証
    """

    def __init__(self) -> None:
        """ファイル管理の初期化"""
        self._lock = threading.Lock()
        self._file_cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def get_output_html_path(input_file: str, output_dir: str) -> Path:
        """入力ファイルから出力HTMLファイルのパスを生成（Thread-Safe）"""
        try:
            if not input_file:
                raise ValueError("入力ファイルが指定されていません")
            if not isinstance(input_file, str):
                raise TypeError(
                    f"入力ファイルは文字列である必要があります: {type(input_file)}"
                )
            if not isinstance(output_dir, str):
                raise TypeError(
                    f"出力ディレクトリは文字列である必要があります: {type(output_dir)}"
                )

            input_path = Path(input_file)

            # パスの妥当性チェック
            if not input_path.name:
                raise ValueError("有効なファイル名が含まれていません")

            output_path = Path(output_dir) / f"{input_path.stem}.html"
            return output_path
        except Exception as e:
            logging.error(f"出力パス生成エラー: {e}")
            raise

    @staticmethod
    def validate_file_exists(file_path: str) -> bool:
        """ファイルの存在確認（エラーハンドリング強化）"""
        try:
            if not file_path or not isinstance(file_path, str):
                return False
            path = Path(file_path)
            return path.exists() and path.is_file()
        except (OSError, ValueError) as e:
            logging.warning(f"ファイル存在確認エラー: {e}")
            return False

    @staticmethod
    def validate_directory_writable(dir_path: str) -> bool:
        """ディレクトリの書き込み可能性確認（エラーハンドリング強化）"""
        try:
            if not dir_path or not isinstance(dir_path, str):
                return False

            directory = Path(dir_path)
            directory.mkdir(parents=True, exist_ok=True)

            # 書き込みテストを実行
            test_file = directory / ".write_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()

            return directory.is_dir()
        except (OSError, PermissionError) as e:
            logging.warning(f"ディレクトリ書き込み確認エラー: {e}")
            return False

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """ファイルサイズをMB単位で取得（エラーハンドリング強化）"""
        try:
            if not file_path or not isinstance(file_path, str):
                return 0.0
            path = Path(file_path)
            if not path.exists():
                return 0.0
            return path.stat().st_size / (1024 * 1024)
        except (OSError, FileNotFoundError) as e:
            logging.warning(f"ファイルサイズ取得エラー: {e}")
            return 0.0

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """ファイル情報を取得（キャッシュ機能付き）"""
        try:
            with self._lock:
                # キャッシュ確認
                if file_path in self._file_cache:
                    cached = self._file_cache[file_path]
                    # キャッシュが新しい場合は使用
                    path = Path(file_path)
                    if path.exists() and path.stat().st_mtime <= cached.get("mtime", 0):
                        return cached

                # ファイル情報取得
                if not self.validate_file_exists(file_path):
                    return None

                path = Path(file_path)
                stat = path.stat()

                info = {
                    "path": str(path.absolute()),
                    "name": path.name,
                    "size_mb": stat.st_size / (1024 * 1024),
                    "mtime": stat.st_mtime,
                    "exists": True,
                }

                # キャッシュに保存
                self._file_cache[file_path] = info
                return info

        except Exception as e:
            logging.error(f"ファイル情報取得エラー: {e}")
            return None

    @staticmethod
    def get_sample_output_path(output_dir: str = "kumihan_sample") -> Path:
        """サンプル生成用の出力パスを取得（エラーハンドリング強化）"""
        try:
            if not isinstance(output_dir, str):
                output_dir = str(output_dir)
            return Path(output_dir)
        except Exception as e:
            logging.warning(f"サンプル出力パス生成エラー: {e}")
            return Path("kumihan_sample")

    def clear_cache(self) -> None:
        """ファイルキャッシュをクリア"""
        with self._lock:
            self._file_cache.clear()
