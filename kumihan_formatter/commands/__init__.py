"""
変換コマンドモジュール

Issue #1207対応: 技術的負債削除・存在するモジュールのみインポート
過度なファイル分割による参照エラーを解消
"""

# Issue #1207: 安全なモジュールのみインポート
from .sample_command import SampleCommand

__all__ = ["SampleCommand"]