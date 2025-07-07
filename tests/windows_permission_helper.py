"""Windows権限制御ヘルパー関数

Windows環境でのファイル・ディレクトリ権限制御を行うためのヘルパー関数。
icaclsコマンドを使用してファイル権限を変更・復元する。
"""

import getpass
import platform
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class WindowsPermissionHelper:
    """Windows権限制御ヘルパークラス"""

    def __init__(self) -> None:
        self.is_windows = platform.system() == "Windows"
        self.current_user = getpass.getuser()
        self._original_permissions = {}

    def deny_read_permission(self, file_path: Path) -> bool:
        """ファイルの読み取り権限を拒否する

        Args:
            file_path: 対象ファイルのパス

        Returns:
            bool: 権限変更が成功したかどうか
        """
        if not self.is_windows:
            return False

        try:
            # 現在の権限を保存
            self._save_original_permissions(file_path)

            # 読み取り権限を拒否
            cmd = [
                "icacls",
                str(file_path),
                "/deny",
                f"{self.current_user}: (R)",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            return result.returncode == 0

        except Exception:
            return False

    def deny_write_permission(self, dir_path: Path) -> bool:
        """ディレクトリの書き込み権限を拒否する

        Args:
            dir_path: 対象ディレクトリのパス

        Returns:
            bool: 権限変更が成功したかどうか
        """
        if not self.is_windows:
            return False

        try:
            # 現在の権限を保存
            self._save_original_permissions(dir_path)

            # 書き込み権限を拒否
            cmd = [
                "icacls",
                str(dir_path),
                "/deny",
                f"{self.current_user}: (W)",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            return result.returncode == 0

        except Exception:
            return False

    def restore_permissions(self, path: Path) -> bool:
        """権限を復元する

        Args:
            path: 対象パスのパス

        Returns:
            bool: 権限復元が成功したかどうか
        """
        if not self.is_windows:
            return False

        try:
            # 拒否権限を削除
            cmd = ["icacls", str(path), "/remove:d", self.current_user]

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            # 保存された権限情報をクリア
            if str(path) in self._original_permissions:
                del self._original_permissions[str(path)]

            return result.returncode == 0

        except Exception:
            return False

    def _save_original_permissions(self, path: Path) -> None:
        """元の権限情報を保存する

        Args:
            path: 対象パス
        """
        if not self.is_windows:
            return

        try:
            cmd = ["icacls", str(path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                self._original_permissions[str(path)] = result.stdout

        except Exception:
            pass

    def cleanup_all(self) -> None:
        """すべての変更した権限を復元する"""
        if not self.is_windows:
            return

        for path_str in list(self._original_permissions.keys()):
            self.restore_permissions(Path(path_str))


def create_windows_permission_helper() -> WindowsPermissionHelper:
    """Windows権限ヘルパーを作成する

    Returns:
        WindowsPermissionHelper: Windows権限ヘルパーインスタンス
    """
    return WindowsPermissionHelper()


def set_read_only_file_windows(
    file_path: Path,
) -> Tuple[bool, Optional[WindowsPermissionHelper]]:
    """Windows環境でファイルを読み取り専用にする

    Args:
        file_path: 対象ファイルのパス

    Returns:
        Tuple[bool, Optional[WindowsPermissionHelper]]:
            (成功/失敗, ヘルパーインスタンス)
    """
    if platform.system() != "Windows":
        return False, None

    helper = create_windows_permission_helper()
    success = helper.deny_read_permission(file_path)

    return success, helper if success else None


def set_write_denied_directory_windows(
    dir_path: Path,
) -> Tuple[bool, Optional[WindowsPermissionHelper]]:
    """Windows環境でディレクトリを書き込み禁止にする

    Args:
        dir_path: 対象ディレクトリのパス

    Returns:
        Tuple[bool, Optional[WindowsPermissionHelper]]:
            (成功/失敗, ヘルパーインスタンス)
    """
    if platform.system() != "Windows":
        return False, None

    helper = create_windows_permission_helper()
    success = helper.deny_write_permission(dir_path)

    return success, helper if success else None
