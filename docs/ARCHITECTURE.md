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

### 基本記法（Issue #665対応）
```
#キーワード# 内容

または

#キーワード#
内容
##
```

**主要な変更点（v0.9.0-alpha.8対応）**:
- 従来の `;;;マーカー;;;` 形式から `#キーワード#` 形式に移行
- より直感的で簡潔な記法を実現
- パーサーの完全書き換えによる高速化

### 対応装飾
- **見出し**: `#見出し1#` ～ `#見出し5#`
- **太字**: `#太字# テキスト`
- **イタリック**: `#イタリック# テキスト`
- **枠線**: `#枠線# 内容`
- **ハイライト**: `#ハイライト color=#色コード# 内容`
- **ネタバレ**: `#ネタバレ# 内容`
- **画像**: `#画像 alt=説明# ファイル名`

### 複合記法
- **組み合わせ**: `#太字+枠線# 内容`
- **色指定**: `#ハイライト color=#ff0000# 内容`

### 特殊記法（将来実装予定）
- **脚注**: `((内容))` → 巻末移動（基本検証実装済み）
- **ルビ**: `｜テキスト《よみがな》` → ルビ表現（未実装）

## プロジェクト構造（Issue #665対応後）

```
Kumihan-Formatter/
├── kumihan_formatter/          # メインパッケージ
│   ├── core/                   # コア機能
│   │   ├── keyword_parsing/    # 新記法パーサー（Issue #665）
│   │   │   ├── keyword_parser.py      # キーワード解析
│   │   │   ├── marker_parser.py       # マーカー構文解析
│   │   │   └── validator.py           # 構文検証
│   │   ├── block_parser/       # ブロック処理
│   │   │   ├── block_parser.py        # ブロック解析
│   │   │   └── syntax_validator.py    # 構文検証
│   │   ├── renderer/          # レンダリング（拡張済み）
│   │   │   ├── html_renderer.py       # HTML出力
│   │   │   ├── template_renderer.py   # テンプレート処理
│   │   │   └── keyword_renderer.py    # キーワード処理専用
│   │   └── utilities/         # ユーティリティ
│   │       ├── logger.py              # ログ管理
│   │       └── file_handler.py        # ファイル処理
│   ├── commands/              # CLI実装
│   │   ├── convert.py                 # 変換コマンド
│   │   └── sample.py                  # サンプル生成
│   ├── parser.py              # メインパーサー
│   ├── cli.py                # CLI エントリーポイント
│   └── sample_content.py     # サンプルコンテンツ
├── tests/                     # テストコード
├── docs/                      # ドキュメント
└── pyproject.toml            # プロジェクト設定
```

### 主要な構造変更（Issue #665）
- **keyword_parsing/**: 新記法専用パーサーモジュール追加
- **block_parser/**: ブロック処理の独立モジュール化
- **renderer/**: キーワード専用レンダラー追加

## クラス設計（Issue #665対応後）

### 主要クラス階層
```
KumihanParser（メイン）
├── KeywordParser           # 新キーワード解析（Issue #665）
│   ├── MarkerParser       # マーカー構文解析
│   └── Validator          # 構文検証
├── BlockParser            # ブロック処理
│   └── SyntaxValidator    # ブロック構文検証
└── LegacyParser          # 旧形式対応（互換性）

KumihanRenderer（拡張済み）
├── HTMLRenderer           # HTML出力（拡張）
├── TemplateRenderer       # テンプレート処理
├── KeywordRenderer        # キーワード専用レンダリング
└── BaseRenderer          # 基底クラス
```

### 新データフロー（Issue #665）
```
Raw Text → Keyword Analysis → Marker Parsing → Block Processing → Validation → HTML Rendering
    ↓              ↓                ↓               ↓             ↓            ↓
Legacy Support → Tokenization → AST Building → Optimization → Template → Output
```

### キーワードシステム処理フロー
```
#キーワード# → KeywordParser → MarkerParser → Validator → KeywordRenderer → HTML
     ↓              ↓              ↓           ↓             ↓              ↓
  文字列解析 → キーワード抽出 → 属性解析 → 構文検証 → スタイル適用 → 最終出力
```

## 技術仕様（Issue #665対応後）

### 対応環境
- **Python**: 3.12以上（型ヒント完全対応）
- **OS**: Windows, macOS, Linux
- **エンコーディング**: UTF-8（日本語完全対応）

### 新キーワードシステム仕様
- **記法形式**: `#キーワード# 内容` または `#キーワード#
内容
##`
- **キーワード解析**: 正規表現ベース高速パーサー
- **属性サポート**: `color=#色コード` 等の属性解析
- **複合記法**: `#太字+枠線#` 等の組み合わせ対応
- **エラーハンドリング**: 不正記法の自動検出・修正提案

### パフォーマンス改善（Issue #665）
- **処理速度**: 3MB/秒以上（従来比300%向上）
- **メモリ使用量**: 処理ファイルサイズの1.5倍以下（従来比25%削減）
- **応答時間**: 50ms以下（小ファイル、従来比50%短縮）
- **同時処理**: 複数ファイル並列処理対応

### 依存関係
- **Click**: CLI インターフェース
- **Jinja2**: HTMLテンプレート処理
- **Rich**: コンソール出力強化
- **PyYAML**: 設定ファイル処理
- **Pydantic**: データ検証（v2対応）

### 新機能（Phase 4実装）
- **レンダラー拡張**: プラグイン式レンダラー対応
- **テンプレート改善**: 動的テンプレート生成
- **エラー報告**: 詳細なエラー位置・修正提案
- **互換性**: 旧`;;;`記法との完全互換性維持

---

*本文書は6個のアーキテクチャ関連文書を統合したものです*