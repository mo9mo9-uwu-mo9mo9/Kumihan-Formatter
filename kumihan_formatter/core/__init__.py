"""
コア機能パッケージ

Kumihan-Formatterのコア機能を提供するパッケージ
Issue #1217対応: ディレクトリ構造最適化による新体系
"""

# 新しいディレクトリ構造に基づくインポート
from . import processing
from . import templates
from . import utilities
from . import validation
from . import types
from . import patterns
from . import parsing
from . import rendering
from . import io
from . import config
from . import ast_nodes
from . import common
from . import error_handling
from . import syntax

# 主要コンポーネントの公開
__all__ = [
    # 新設モジュール
    "processing",
    "templates",
    "utilities",
    "validation",
    "types",
    "patterns",
    # 既存モジュール
    "parsing",
    "rendering",
    "io",
    "config",
    "ast_nodes",
    "common",
    "error_handling",
    "syntax",
]
