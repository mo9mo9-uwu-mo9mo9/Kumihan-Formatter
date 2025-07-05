"""クロスプラットフォーム対応の権限設定ヘルパー

Windows環境でのファイル権限テスト失敗を解決するため、
プラットフォーム別の権限設定方法を提供します。
"""

import os
import platform
import subprocess
import tempfile
from pathlib import Path


class PermissionHelper:
    """プラットフォーム別の権限設定ヘルパークラス"""

    @staticmethod
    def is_windows() -> bool:
        """Windows環境かどうかを判定"""
        return platform.system() == "Windows"

    @staticmethod
    def deny_file_read_permission(file_path: Path) -> bool:
        """ファイルの読み込み権限を拒否

        Returns:
            bool: 権限変更が成功したかどうか
        """
        if PermissionHelper.is_windows():
            return PermissionHelper._deny_windows_file_read(file_path)
        else:
            return PermissionHelper._deny_unix_file_read(file_path)

    @staticmethod
    def deny_directory_write_permission(dir_path: Path) -> bool:
        """ディレクトリの書き込み権限を拒否

        Returns:
            bool: 権限変更が成功したかどうか
        """
        if PermissionHelper.is_windows():
            return PermissionHelper._deny_windows_directory_write(dir_path)
        else:
            return PermissionHelper._deny_unix_directory_write(dir_path)

    @staticmethod
    def restore_file_permissions(file_path: Path) -> bool:
        """ファイルの権限を復元

        Returns:
            bool: 権限復元が成功したかどうか
        """
        if PermissionHelper.is_windows():
            return PermissionHelper._restore_windows_file_permissions(file_path)
        else:
            return PermissionHelper._restore_unix_file_permissions(file_path)

    @staticmethod
    def restore_directory_permissions(dir_path: Path) -> bool:
        """ディレクトリの権限を復元

        Returns:
            bool: 権限復元が成功したかどうか
        """
        if PermissionHelper.is_windows():
            return PermissionHelper._restore_windows_directory_permissions(dir_path)
        else:
            return PermissionHelper._restore_unix_directory_permissions(dir_path)

    # Unix/Linux/macOS用の権限設定メソッド

    @staticmethod
    def _deny_unix_file_read(file_path: Path) -> bool:
        """Unix系OSでファイルの読み込み権限を拒否"""
        try:
            os.chmod(file_path, 0o000)
            return True
        except OSError:
            return False

    @staticmethod
    def _deny_unix_directory_write(dir_path: Path) -> bool:
        """Unix系OSでディレクトリの書き込み権限を拒否"""
        try:
            os.chmod(dir_path, 0o444)
            return True
        except OSError:
            return False

    @staticmethod
    def _restore_unix_file_permissions(file_path: Path) -> bool:
        """Unix系OSでファイルの権限を復元"""
        try:
            os.chmod(file_path, 0o644)
            return True
        except OSError:
            return False

    @staticmethod
    def _restore_unix_directory_permissions(dir_path: Path) -> bool:
        """Unix系OSでディレクトリの権限を復元"""
        try:
            os.chmod(dir_path, 0o755)
            return True
        except OSError:
            return False

    # Windows用の権限設定メソッド

    @staticmethod
    def _deny_windows_file_read(file_path: Path) -> bool:
        """Windowsでファイルの読み込み権限を拒否"""
        try:
            # icaclsコマンドを使用してアクセス権を拒否
            cmd = [
                "icacls",
                str(file_path),
                "/deny",
                f"{os.environ.get('USERNAME', 'Everyone')}:R",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            # icaclsコマンドが使用できない場合は、
            # ファイルを削除して権限エラーをシミュレート
            try:
                # 一時的にファイルを移動して読み込み不可にする
                temp_dir = Path(tempfile.gettempdir()) / "permission_test_backup"
                temp_dir.mkdir(exist_ok=True)
                backup_path = temp_dir / file_path.name
                file_path.rename(backup_path)
                # 元の場所に権限のないファイルとして復元情報を保存
                (file_path.parent / f".{file_path.name}.backup").write_text(
                    str(backup_path)
                )
                return True
            except OSError:
                return False

    @staticmethod
    def _deny_windows_directory_write(dir_path: Path) -> bool:
        """Windowsでディレクトリの書き込み権限を拒否"""
        try:
            # icaclsコマンドを使用してディレクトリの書き込み権を拒否
            cmd = [
                "icacls",
                str(dir_path),
                "/deny",
                f"{os.environ.get('USERNAME', 'Everyone')}:W",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            # icaclsが使用できない場合の代替案
            try:
                # ディレクトリ内に読み取り専用マーカーファイルを作成
                marker_file = dir_path / ".permission_denied_marker"
                marker_file.write_text("permission denied simulation")
                # Windowsでディレクトリを読み取り専用にする
                if hasattr(os, "system"):
                    os.system(f'attrib +R "{dir_path}"')
                return True
            except OSError:
                return False

    @staticmethod
    def _restore_windows_file_permissions(file_path: Path) -> bool:
        """Windowsでファイルの権限を復元"""
        try:
            # icaclsで拒否権限を削除
            cmd = [
                "icacls",
                str(file_path),
                "/remove:d",
                os.environ.get("USERNAME", "Everyone"),
            ]
            subprocess.run(cmd, capture_output=True, text=True)

            # バックアップファイルがある場合は復元
            backup_info = file_path.parent / f".{file_path.name}.backup"
            if backup_info.exists():
                backup_path = Path(backup_info.read_text().strip())
                if backup_path.exists():
                    backup_path.rename(file_path)
                backup_info.unlink()

            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    @staticmethod
    def _restore_windows_directory_permissions(dir_path: Path) -> bool:
        """Windowsでディレクトリの権限を復元"""
        try:
            # icaclsで拒否権限を削除
            cmd = [
                "icacls",
                str(dir_path),
                "/remove:d",
                os.environ.get("USERNAME", "Everyone"),
            ]
            subprocess.run(cmd, capture_output=True, text=True)

            # 読み取り専用属性を削除
            if hasattr(os, "system"):
                os.system(f'attrib -R "{dir_path}"')

            # マーカーファイルを削除
            marker_file = dir_path / ".permission_denied_marker"
            if marker_file.exists():
                marker_file.unlink()

            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    @staticmethod
    def create_permission_test_context(file_path: Path = None, dir_path: Path = None):
        """権限テスト用のコンテキストマネージャーを作成"""
        return PermissionTestContext(file_path=file_path, dir_path=dir_path)


class PermissionTestContext:
    """権限テスト用のコンテキストマネージャー"""

    def __init__(self, file_path: Path = None, dir_path: Path = None):
        self.file_path = file_path
        self.dir_path = dir_path
        self.file_permission_changed = False
        self.dir_permission_changed = False

    def __enter__(self):
        """権限を変更"""
        if self.file_path:
            self.file_permission_changed = PermissionHelper.deny_file_read_permission(
                self.file_path
            )

        if self.dir_path:
            self.dir_permission_changed = (
                PermissionHelper.deny_directory_write_permission(self.dir_path)
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """権限を復元"""
        if self.file_path and self.file_permission_changed:
            PermissionHelper.restore_file_permissions(self.file_path)

        if self.dir_path and self.dir_permission_changed:
            PermissionHelper.restore_directory_permissions(self.dir_path)

    def permission_denied_should_occur(self) -> bool:
        """権限拒否が発生するはずかどうかを判定"""
        return self.file_permission_changed or self.dir_permission_changed
