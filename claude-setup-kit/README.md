# 🔧 Claude Code - Serena統合支援ツール

> Kumihan-Formatter開発者向けのSerena統合設定支援ツールキット

## 📋 概要

このツールキットは、Kumihan-Formatterプロジェクトの開発者がSerena-localを利用したAI最適化開発環境を構築するための支援ツールです。

**重要：このツールキットは手動設定支援のみを提供します。自動実行やワンクリック設定機能はありません。**

## 🎯 目的

- **Kumihan-Formatter開発効率向上**: serena-localによるシンボリック編集の活用
- **MCP設定支援**: Model Context Protocol設定の手動手順ガイド
- **開発環境統一**: チーム開発での設定統一化支援
- **トラブルシューティング**: 実際の問題解決策提供

## ⚠️ 前提条件

### 必須要件
- **Claude Desktop**: 最新版インストール済み
- **Python**: 3.12以上
- **Node.js**: 18以上
- **UV**: パッケージマネージャー
- **Git**: バージョン管理

### 推奨知識
- MCP（Model Context Protocol）の基本理解
- JSON設定ファイルの編集経験
- コマンドライン操作の基本知識

## 📁 ツールキット構成

```
claude-setup-kit/
├── README.md                    # このファイル
├── INSTALLATION_GUIDE.md        # serena-local設定手順
├── TROUBLESHOOTING.md          # トラブルシューティング
├── BEGINNER_GUIDE.md           # 初心者向けガイド
├── scripts/
│   ├── install-serena-local.sh # serena-localインストール
│   └── emergency-fix.sh        # 緊急修復スクリプト
└── templates/
    └── claude_desktop_config.json.template
```

## 🚀 基本的な使い方

### 1. インストールガイドの確認
```bash
cat claude-setup-kit/INSTALLATION_GUIDE.md
```

### 2. 手動設定実行
serena-localの設定は手動で行います：
```bash
# インストールスクリプトの実行
./claude-setup-kit/scripts/install-serena-local.sh

# 設定ファイルの手動編集が必要
# 詳細はINSTALLATION_GUIDE.mdを参照
```

### 3. 動作確認
```bash
# Claude Desktopを再起動
# Kumihan-Formatterプロジェクトで動作確認
```

## 📊 期待される効果

### Serena-local使用時の利点
- **シンボリック編集**: `find_symbol`、`replace_symbol_body`等の精密編集
- **トークン効率化**: 必要な部分のみの編集によるトークン節約
- **コード品質向上**: 構文解析に基づく正確な編集
- **開発速度向上**: ピンポイント編集による高速化

**注意：具体的な数値効果は環境や使用方法により変動します。**

## 🛠️ Kumihan-Formatterとの関係

### なぜSerenaが必要か
1. **大規模コードベース**: Kumihan-Formatterは複雑なパーサー・レンダラー構造
2. **精密編集要求**: ブロック記法処理の正確な実装が必要
3. **テスト品質**: 包括的テストスイートのメンテナンス
4. **チーム開発**: 一貫した開発環境の維持

### 活用場面
- パーサー機能の拡張・修正
- レンダラーの出力形式調整
- CLI機能の追加・改善
- テストケースの追加・修正

## 🔧 トラブルシューティング

一般的な問題と解決策については以下を参照：
```bash
cat claude-setup-kit/TROUBLESHOOTING.md
```

### 緊急時の対処
```bash
# 設定リセット（手動バックアップ推奨）
./claude-setup-kit/scripts/emergency-fix.sh
```

## 📚 段階的導入

### 初心者の方
1. [初心者ガイド](BEGINNER_GUIDE.md)から開始
2. 基本設定のみ適用
3. 慣れてから高度な機能を追加

### 経験者の方
1. [インストールガイド](INSTALLATION_GUIDE.md)で一括設定
2. カスタマイズ設定の適用
3. チーム設定の共有

## ⚡ 制限事項

### できないこと
- **自動設定**: 全設定は手動実行が必要
- **自然言語コマンド**: 「Serenaセットアップして」等は動作しません
- **ワンクリック設定**: 段階的な手動設定が必要
- **保証された効果**: 具体的な削減効果の保証はありません

### 注意点
- Claude Desktop再起動が必要な場合があります
- 設定ファイルの手動編集が必要です
- バックアップは各自で実施してください

## 📞 サポート

### 問題報告
- **GitHub Issues**: Kumihan-Formatterプロジェクト
- **対象**: 実際の設定問題・エラー報告のみ
- **非対象**: 使い方の質問・要望

### 貢献
- **プルリクエスト歓迎**: 実際に動作する改善のみ
- **ドキュメント改善**: 正確性向上の提案
- **テスト報告**: 実際の動作環境での検証結果

---

**実用的で正確な情報のみを提供しています。**  
**誇大な宣伝や虚偽の機能説明はありません。**

*Kumihan-Formatter Claude Setup Kit - 実用版*