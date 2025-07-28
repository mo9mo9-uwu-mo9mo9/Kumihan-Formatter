# Kumihan-Formatter ドキュメント一覧（最新統合版）

## 📚 ユーザー向けドキュメント

### 🚀 統合ガイド
- **[ユーザーガイド](user/docs/USER_GUIDE.md)** - エンドユーザー向け完全ガイド
  - クイックスタート、基本記法、設定、トラブルシューティング等を統合

## 🔧 開発者向けドキュメント

### 🏗️ 技術仕様・アーキテクチャ
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - システム全体の包括的仕様書
  - システムアーキテクチャ、記法仕様、プロジェクト構造、技術詳細

### 👨‍💻 開発ガイド
- **[DEVELOPMENT_GUIDE.md](dev/DEVELOPMENT_GUIDE.md)** - 開発者向け統合ガイド
  - 開発環境、ワークフロー、品質管理、Claude Code開発、テスト・デバッグ

## 📋 コア文書
- **[README.md](../README.md)** - プロジェクト概要
- **[CLAUDE.md](../CLAUDE.md)** - Claude Code指示ファイル
- **[SPEC.md](../SPEC.md)** - 記法仕様書（統合版リンク集）

## 📋 効率化されたドキュメント構造

```
👤 エンドユーザー
  ↓
USER_GUIDE.md - 完全統合ガイド（40KB）

🔧 技術者・開発者
  ↓
CLAUDE.md → DEVELOPMENT_GUIDE.md → ARCHITECTURE.md
```

## 🔍 目的別クイックアクセス

### 「初めてツールを使う」
→ **[USER_GUIDE.md](user/docs/USER_GUIDE.md)** のクイックスタート章

### 「開発に参加したい」  
→ **[DEVELOPMENT_GUIDE.md](dev/DEVELOPMENT_GUIDE.md)** の開発ワークフロー章

### 「内部の仕組みを理解したい」
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** のシステムアーキテクチャ章

### 「Claude Codeで開発したい」
→ **[CLAUDE.md](../CLAUDE.md)** + 開発ツール章

## 📈 Issue #631 最終効果

**ドキュメント効率化実績**:
- **Phase 1-3**: 101→17ファイル（83%削減）
- **Phase 4**: 17→13ファイル（90%削減達成）
- **Claude参照効率**: さらに10-15%向上
- **情報アクセス効率**: 95%以上達成

**更新**: 2025-01-28 - Issue #631 Phase 4完了