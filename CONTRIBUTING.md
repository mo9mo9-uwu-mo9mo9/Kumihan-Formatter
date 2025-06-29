# CONTRIBUTING.md

Kumihan-Formatter への貢献ガイドライン

## 開発参加の方法

### 1. Issue の作成
- バグ報告や機能提案は Issue で行ってください
- 既存の Issue を確認してから新規作成してください

### 2. Pull Request
- `main` ブランチへの直接コミットは避けてください
- 機能ブランチを作成して作業してください
- PR にはテスト結果を含めてください

### 3. コーディング規約
- Python 3.8+ 対応
- Black でコードフォーマット
- 型ヒントを積極的に使用

## ブランチ戦略

- `main`: 安定版
- `feature/*`: 新機能開発
- `fix/*`: バグ修正

## テスト

```bash
make test
```

## リンター

```bash
make lint
```

## ドキュメント

- 変更内容は CHANGELOG.md に記録
- API 変更時は docs/ を更新