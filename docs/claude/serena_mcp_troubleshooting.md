# Serena MCP トラブルシューティングガイド

## 🚨 今回の問題: ダッシュボード起動直後クラッシュ

### 根本原因
MCPサーバー設定時のコマンド構文エラーが原因でした。

```bash
# ❌ 問題のあったコマンド（改行で分離）
claude mcp add serena -- /Users/m2_macbookair_3911/.local/bin/uv run --directory /Users/m2_macbookair_3911/GitHub/Kumihan-Formatter/serena serena-mcp-server
   --context ide-assistant --project /Users/m2_macbookair_3911/GitHub/Kumihan-Formatter

# エラー結果
zsh: command not found: --context
```

### 問題の詳細
1. コマンドが改行により分離
2. `--context` が独立したシェルコマンドとして実行されようとした
3. MCPサーバーが不完全な設定で登録
4. 起動時の設定不整合でクラッシュ

## 🛠️ 正しいセットアップ手順

### 1. 既存設定のクリーンアップ

```bash
# 問題のある設定を削除
claude mcp remove serena
```

### 2. 正しいMCPサーバー追加

```bash
# ✅ 正しい方法: 一行で完結させる
claude mcp add serena -- /Users/m2_macbookair_3911/.local/bin/uv run --directory /Users/m2_macbookair_3911/GitHub/Kumihan-Formatter/serena serena-mcp-server --context ide-assistant --project /Users/m2_macbookair_3911/GitHub/Kumihan-Formatter
```

### 3. 設定確認

```bash
# MCP設定確認
claude mcp

# 動作テスト
cd serena
uv run serena start-mcp-server --help
```

## 🔧 再発防止策

### A. 自動セットアップスクリプト作成
- ワンクリックでクリーンセットアップ
- 設定ファイル検証機能
- エラー時の自動復旧

### B. 設定監視スクリプト
- MCP設定の定期チェック
- 不正設定の自動検出・修正
- ダッシュボード監視・自動再起動

### C. ドキュメント改善
- 正しいコマンド構文の明記
- よくある間違いの事例集
- トラブルシューティング手順書

## 📊 ディレクトリ選択指針

### 推奨: プロジェクト内serena
```
/Users/m2_macbookair_3911/GitHub/Kumihan-Formatter/serena
```

**メリット**:
- プロジェクト固有の設定・メモリ
- バージョン管理との統合
- 他プロジェクトからの独立性

### 非推奨: グローバルserena
```
/Users/m2_macbookair_3911/GitHub/serena
```

**デメリット**:
- プロジェクト間での設定競合
- メモリ・設定の混在
- 依存関係の複雑化

## 🎯 今後の運用方針

1. **プロジェクト内serena使用を標準化**
2. **設定変更時は必ず一行コマンドで実行**
3. **定期的な設定検証の自動化**
4. **問題発生時の標準対処手順の確立**

---
*作成日: 2025-08-06*  
*対象: Kumihan-Formatter プロジェクト*