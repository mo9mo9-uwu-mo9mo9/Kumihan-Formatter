"""
コア機能パッケージ

Kumihan-Formatterのコア機能を提供するパッケージ
Issue #1217対応: ディレクトリ構造最適化による新体系
"""

# 新しいディレクトリ構造に基づくインポート

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
    "ast_nodes",
    "common",
    "syntax",
]
