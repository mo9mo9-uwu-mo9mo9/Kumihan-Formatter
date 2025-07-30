# Kumihan-Formatter アーキテクチャ仕様（統合版）

> システム設計・技術仕様書 - 6ファイル統合版
> **最終更新**: 2025-01-28

## 📋 目次

- [システム概要](#システム概要)
- [全体アーキテクチャ](#全体アーキテクチャ)
- [記法仕様](#記法仕様)
- [プロジェクト構造](#プロジェクト構造)
- [クラス設計](#クラス設計)
- [技術仕様](#技術仕様)

## システム概要

**日本語テキスト装飾・整形フォーマッター** - Claude Code専用最適化

### 基本特徴
- **記法ベース**: 独自のKumihan記法
- **多様な出力**: HTML、Markdown、テキスト対応
- **高性能**: Python 3.12+ による最適化

## 全体アーキテクチャ

### コンポーネント構成
```
CLI Interface → Parser Core → Renderer Core
     ↓             ↓              ↓
 Utilities ←→ Templates ←→ Configuration
```

## 記法仕様

### 基本記法
```
#装飾名# 内容

または

#装飾名#
内容
##
```

### 対応装飾
- **傍点**: `#傍点# テキスト`
- **太字**: `#太字# テキスト`
- **イタリック**: `#イタリック# テキスト`

### 特殊記法
- **脚注**: `((内容))` → 巻末移動
- **ルビ**: `｜テキスト《よみがな》`

## プロジェクト構造

```
Kumihan-Formatter/
├── kumihan_formatter/          # メインパッケージ
│   ├── core/                   # コア機能
│   │   ├── parser/            # 解析エンジン
│   │   ├── renderer/          # レンダリング
│   │   └── utilities/         # ユーティリティ
│   ├── commands/              # CLI実装
│   └── templates/             # テンプレート
├── tests/                     # テストコード
├── docs/                      # ドキュメント
└── pyproject.toml            # プロジェクト設定
```

## クラス設計

### 主要クラス階層
```
KumihanParser
├── Lexer
├── Parser
└── ASTBuilder

KumihanRenderer  
├── BaseRenderer
├── HTMLRenderer
├── MarkdownRenderer
└── TextRenderer
```

### データフロー
```
Raw Text → Tokens → AST → Validated AST → Rendered Output
```

## 技術仕様

### 対応環境
- **Python**: 3.12以上
- **OS**: Windows, macOS, Linux
- **エンコーディング**: UTF-8

### パフォーマンス要件
- **処理速度**: 1MB/秒以上
- **メモリ使用量**: 処理ファイルサイズの2倍以下
- **応答時間**: 100ms以下（小ファイル）

---

*本文書は6個のアーキテクチャ関連文書を統合したものです*