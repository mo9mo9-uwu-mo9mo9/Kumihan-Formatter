# タスク完了時の必須要件

## 必須チェック項目
1. **コード品質チェック**: `make lint` を実行し、すべてパスすること
2. **記法検証**: 記法関連変更時は `python -m kumihan_formatter check-syntax file.txt` で確認
3. **依存関係確認**: `pip install -e ".[dev]"` で依存関係が正常であること

## 品質チェック詳細
```bash
# 必須実行コマンド
make lint

# 内部で実行される項目:
# - Black コードフォーマットチェック
# - isort import順序チェック  
# - flake8 コード品質チェック
# - mypy 型チェック
```

## ブランチ・コミット規則
- **ブランチ名**: `{type}/issue-{Issue番号}-{英語概要}` 形式必須
- **日本語ブランチ名**: システム的に禁止（Git hooks・GitHub Actionsで拒否）
- **Git hooks**: `./scripts/install-hooks.sh` で事前セットアップ必須

## レビュープロセス
- **自動レビュー**: 無効化済み
- **手動レビュー**: Claude Codeセッション内での対話レビュー
- **日本語レビュー**: 必須（英語レビューは即座に削除対象）

## CI/CD要件
- 新CI（Issue #602対応）必須通過
- すべてのチェックがパスしてからマージ可能