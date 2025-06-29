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
- PR のレビューはClaudeが行ってください
- Issue に基づいて作業を行った場合、作業結果をそのIssue にコメントしてください
- PR のマージ後はCloseできるIssue があるかどうかを確認してください

### 4. コーディング規約
- Python 3.8+ 対応
- Black でコードフォーマット
- 型ヒントを積極的に使用
- 主要クラスの冒頭に、設計ドキュメントへの参照と、関連クラスのメモを、コメントとして付与する

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
- API 変更時は ./README.mdを更新