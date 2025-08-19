"""
Kumihan-Formatter 自動品質チェックツール

Phase 4-2: 自動品質チェック実装
- pre-commitフック統合
- 品質チェッカー
- 自動フォーマッター
- PR時自動検証
"""

from .auto_formatter import AutoFormatter
from .pre_commit_hooks import PreCommitHookManager
from .quality_checker import QualityChecker

__all__ = ["PreCommitHookManager", "QualityChecker", "AutoFormatter"]

__version__ = "1.0.0"
