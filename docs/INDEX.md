# Kumihan-Formatter ドキュメント一覧

## 📚 ユーザー向けドキュメント

### 🚀 はじめての方
- [初回実行ガイド](user/FIRST_RUN.md) - 最初に読むファイル
- [起動ガイド](user/LAUNCH_GUIDE.md) - スクリプトの使い方
- [クイックスタート](QUICKSTART.md) - 5分で始める基本的な使い方
- [トラブルシューティング](user/TROUBLESHOOTING.md) - Windows・macOS問題解決

### 📖 基本的な使い方
- [記法リファレンス](SYNTAX_REFERENCE.md) - すべての記法を詳しく
- [改行処理ガイド](user/LINE_BREAK_GUIDE.md) - 直感的な改行処理の特長と使い方
- [ダブルクリックガイド](user/DOUBLE_CLICK_GUIDE.md) - マウスだけで使う方法
- [記法チートシート](user/SYNTAX_CHEATSHEET.txt) - 記法をコンパクトに

### 🔧 詳細・上級者向け
- [CLIリファレンス](user/CLI_REFERENCE.md) - コマンドラインの詳細
- [設定ガイド](user/CONFIG_GUIDE.md) - カスタマイズ方法
- [テスト生成機能](user/USAGE_GENERATE_TEST.md) - テストパターン生成
- [ユーザーマニュアル](user/USER_MANUAL.txt) - 完全ガイド（1566行）

## 🔧 開発者向けドキュメント

- [開発ガイドライン](dev/CLAUDE.md) - Claude Code向け開発指針
- [アーキテクチャ](dev/ARCHITECTURE.md) - システム設計と内部構造
- [コントリビューション](dev/CONTRIBUTING.md) - 開発参加ガイド
- [テストガイド](dev/TESTING.md) - テストの書き方と実行方法

## 📋 ドキュメントマップ

```
🚀 初めての方
  ↓
初回実行ガイド → クイックスタート → 記法リファレンス
  ↓
ダブルクリックガイド（非技術者）
または
CLIリファレンス（技術者）

🔧 開発者
  ↓
開発ガイドライン → コントリビューション → アーキテクチャ
  ↓
テストガイド
```

## 🔍 目的別ガイド

### 「初めてツールを使う」
→ [初回実行ガイド](user/FIRST_RUN.md)

### 「とりあえず使ってみたい」
→ [クイックスタート](QUICKSTART.md)

### 「問題が発生した」
→ [トラブルシューティング](user/TROUBLESHOOTING.md)

### 「どんな記法があるか知りたい」
→ [記法リファレンス](SYNTAX_REFERENCE.md)

### 「改行が期待通りにならない」
→ [改行処理ガイド](user/LINE_BREAK_GUIDE.md)

### 「コマンドラインは苦手」
→ [ダブルクリックガイド](user/DOUBLE_CLICK_GUIDE.md)

### 「すべてのオプションを知りたい」
→ [CLIリファレンス](user/CLI_REFERENCE.md)

### 「開発に参加したい」
→ [コントリビューション](dev/CONTRIBUTING.md)

### 「内部の仕組みを理解したい」
→ [アーキテクチャ](dev/ARCHITECTURE.md)

## 📝 メンテナンス情報

最終更新: 2025-06-23
- Issue #65: 改行処理ガイド追加 - 直感的な改行処理をアピールポイントとして整備
- Issue #40: ルートディレクトリのドキュメント散乱を解決
- docs/user/とdocs/dev/の統合ドキュメント構造完成
- Windows・macOS統合トラブルシューティング追加
- 段階的学習導線の構築完了