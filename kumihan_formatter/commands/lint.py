"""
Lint command - 技術的負債修正後の統合エントリポイント

Issue #778: flake8自動修正ツール
Critical問題解決: 988行 → 機能別モジュール分割による可読性・保守性向上

変更履歴:
- 2025-08-10: 988行の巨大ファイルを機能別モジュールに分割
- 分割先: kumihan_formatter/commands/lint/
- 後方互換性: 既存のimport文をすべてサポート

旧構造: 1ファイル988行
新構造: 5モジュール + 統合__init__.py
"""

# kumihan_formatter.commands.lintディレクトリから必要な関数をインポート
from .lint import lint_command

# 既存のCLIコマンドとして動作
if __name__ == "__main__":
    lint_command()
