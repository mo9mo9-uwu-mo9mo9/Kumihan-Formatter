"""ファイル・パス検証実装

ファイル操作の検証機能
"""

import os
from pathlib import Path
from typing import List, Any

from .protocols import ValidatorProtocol


class FileValidator(ValidatorProtocol):
    """ファイル検証クラス"""

    def __init__(self) -> None:
        self._errors: List[str] = []

    def validate(self, target: Any) -> bool:
        """汎用検証（パスとして扱う）"""
        if isinstance(target, (str, Path)):
            return self.validate_readable(Path(target))
        return False

    def validate_readable(self, path: Path) -> bool:
        """ファイルが読み込み可能かどうかを検証"""
        self._errors.clear()
        
        try:
            if not path.exists():
                self._errors.append(f"ファイルが存在しません: {path}")
                return False
            
            if not path.is_file():
                self._errors.append(f"ファイルではありません: {path}")
                return False
            
            if not os.access(path, os.R_OK):
                self._errors.append(f"読み込み権限がありません: {path}")
                return False
            
            return True
            
        except Exception as e:
            self._errors.append(f"ファイル検証中にエラー: {e}")
            return False

    def validate_writable(self, path: Path) -> bool:
        """ファイルが書き込み可能かどうかを検証"""
        self._errors.clear()
        
        try:
            # ファイルが存在する場合は書き込み権限をチェック
            if path.exists():
                if not os.access(path, os.W_OK):
                    self._errors.append(f"書き込み権限がありません: {path}")
                    return False
                return True
            
            # ファイルが存在しない場合は親ディレクトリの書き込み権限をチェック
            parent = path.parent
            if not parent.exists():
                # 親ディレクトリが存在しない場合は作成可能かチェック
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                    return True
                except Exception as e:
                    self._errors.append(f"親ディレクトリを作成できません: {e}")
                    return False
            
            if not os.access(parent, os.W_OK):
                self._errors.append(f"親ディレクトリに書き込み権限がありません: {parent}")
                return False
            
            return True
            
        except Exception as e:
            self._errors.append(f"書き込み検証中にエラー: {e}")
            return False

    def get_errors(self) -> List[str]:
        """エラーメッセージリストを取得"""
        return self._errors.copy()


class PathValidator(ValidatorProtocol):
    """パス検証クラス"""

    def __init__(self) -> None:
        self._errors: List[str] = []

    def validate(self, target: Any) -> bool:
        """汎用検証"""
        if isinstance(target, (str, Path)):
            return self.validate_path(Path(target))
        return False

    def validate_path(self, path: Path) -> bool:
        """パスの有効性を検証"""
        self._errors.clear()
        
        try:
            # パス文字列の基本チェック
            path_str = str(path)
            
            if not path_str.strip():
                self._errors.append("パスが空です")
                return False
            
            # 無効な文字のチェック（基本的なもの）
            invalid_chars = ['<', '>', '"', '|', '?', '*']
            for char in invalid_chars:
                if char in path_str:
                    self._errors.append(f"無効な文字が含まれています: {char}")
                    return False
            
            # パスの長さチェック（システム制限）
            if len(path_str) > 260:  # Windows制限を考慮
                self._errors.append(f"パスが長すぎます: {len(path_str)} 文字")
                return False
            
            # 予約語チェック（Windows）
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]
            
            if path.name.upper() in reserved_names:
                self._errors.append(f"予約語が使用されています: {path.name}")
                return False
            
            return True
            
        except Exception as e:
            self._errors.append(f"パス検証中にエラー: {e}")
            return False

    def resolve_path(self, path: str | Path) -> Path:
        """パスの正規化・解決"""
        try:
            return Path(path).resolve()
        except Exception as e:
            self._errors.append(f"パス解決中にエラー: {e}")
            return Path(path)

    def ensure_parent_dir(self, path: Path) -> None:
        """親ディレクトリの作成（存在しない場合）"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._errors.append(f"親ディレクトリ作成中にエラー: {e}")

    def get_errors(self) -> List[str]:
        """エラーメッセージリストを取得"""
        return self._errors.copy()