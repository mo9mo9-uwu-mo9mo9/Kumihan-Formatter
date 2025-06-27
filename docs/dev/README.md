# 開発者向けドキュメント

このディレクトリには、Kumihan-Formatterの開発に関するドキュメントが整理されています。

## 📋 ディレクトリ構成

### 🏗️ アーキテクチャ・設計
- `ARCHITECTURE.md` - システム全体のアーキテクチャ
- `../../CONTRIBUTING.md` - コントリビューションガイド（ルートレベル）

### 📊 戦略・方針
- `strategies/`
  - `TESTING_STRATEGY.md` - テスト戦略（ユニット中心、E2E廃止）

### 🛠️ ツール・プロセス
- `tools/`
  - `SYNTAX_CHECKER_README.md` - 記法チェッカーツールの説明
- `STYLE_GUIDE.md` - コーディングスタイルガイド
- `EMOJI_POLICY.md` - 絵文字使用ポリシー
- `LABEL_GUIDE.md` - GitHub Issueラベルガイド

### 📈 履歴・分析
- `REFACTORING_SUMMARY.md` - リファクタリング履歴
- `BRANCH_CLEANUP.md` - ブランチ整理記録
- `issue_summary.md` - Issue管理履歴
- `../CHANGELOG.md` - 変更履歴

### 🧪 テスト関連
- `TESTING.md` - テスト実行・詳細ガイド

## 🎯 用途別インデックス

### 新規開発者向け
1. `ARCHITECTURE.md` - 全体構造を理解
2. `CONTRIBUTING.md` - 開発プロセスを確認
3. `strategies/TESTING_STRATEGY.md` - テスト方針を理解

### 既存開発者向け
- `STYLE_GUIDE.md` - コーディング規約
- `tools/SYNTAX_CHECKER_README.md` - ツール使用方法
- `REFACTORING_SUMMARY.md` - 過去の変更履歴

### CI/CD・プロセス
- `EMOJI_POLICY.md` - 自動チェック対象
- `LABEL_GUIDE.md` - Issue管理方針

## 🔗 関連ドキュメント

- **ルートレベル**: [`README.md`](../../README.md), [`CLAUDE.md`](../../CLAUDE.md), [`SPEC.md`](../../SPEC.md), [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- **ユーザー向け**: [`docs/user/`](../user/) - エンドユーザー向けドキュメント
- **分析レポート**: [`docs/analysis/`](../analysis/) - 詳細分析結果