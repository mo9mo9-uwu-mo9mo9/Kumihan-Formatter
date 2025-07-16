"""File management model for Kumihan-Formatter GUI

Single Responsibility Principle適用: ファイル管理モデルの分離
Issue #476 Phase2対応 - gui_models.py分割（2/3）
"""

from pathlib import Path


class FileManager:
    """ファイル操作管理クラス

    ファイル選択、パス管理、出力パス生成等のファイル関連処理
    """

    @staticmethod
    def get_output_html_path(input_file: str, output_dir: str) -> Path:
        """入力ファイルから出力HTMLファイルのパスを生成"""
        if not input_file:
            raise ValueError("入力ファイルが指定されていません")

        input_path = Path(input_file)
        output_path = Path(output_dir) / f"{input_path.stem}.html"
        return output_path

    @staticmethod
    def validate_file_exists(file_path: str) -> bool:
        """ファイルの存在確認"""
        if not file_path:
            return False
        return Path(file_path).exists()

    @staticmethod
    def validate_directory_writable(dir_path: str) -> bool:
        """ディレクトリの書き込み可能性確認"""
        try:
            directory = Path(dir_path)
            directory.mkdir(parents=True, exist_ok=True)
            return directory.is_dir()
        except (OSError, PermissionError):
            return False

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """ファイルサイズをMB単位で取得"""
        try:
            return Path(file_path).stat().st_size / (1024 * 1024)
        except (OSError, FileNotFoundError):
            return 0.0

    @staticmethod
    def get_sample_output_path(output_dir: str = "kumihan_sample") -> Path:
        """サンプル生成用の出力パスを取得"""
        return Path(output_dir)