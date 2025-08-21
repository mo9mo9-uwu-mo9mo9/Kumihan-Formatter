"""
Kumihan-Formatter 自動品質チェックツール

Phase 4-2: 自動品質チェック実装
- pre-commitフック統合
- 品質チェッカー
- 自動フォーマッター
- PR時自動検証
"""


# sys.modules重複インポートWarning回避のため、遅延インポートを使用
def get_auto_formatter():
    """AutoFormatterを取得（遅延インポート）"""
    from .auto_formatter import AutoFormatter

    return AutoFormatter


def get_pre_commit_hook_manager():
    """PreCommitHookManagerを取得（遅延インポート）"""
    from .pre_commit_hooks import PreCommitHookManager

    return PreCommitHookManager


def get_quality_checker():
    """QualityCheckerを取得（遅延インポート）"""
    from .quality_checker import QualityChecker

    return QualityChecker


__version__ = "1.0.0"
