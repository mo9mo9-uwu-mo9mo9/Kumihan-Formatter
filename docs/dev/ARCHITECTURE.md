# Kumihan-Formatter アーキテクチャガイド

## 概要

Kumihan-Formatterは、モジュラーな設計に基づいたテキスト→HTML変換ツールです。
コア機能は`kumihan_formatter/core/`に集約され、専門化されたサブモジュール群で構成されています。

## コンポーネント構成

```
kumihan_formatter/
├── cli.py                    # CLIエントリポイント (Click)
├── __main__.py              # パッケージ実行エントリポイント
├── parser.py                # 解析統括クラス
├── renderer.py              # レンダリング統括クラス
├── config.py                # 基本設定管理
├── simple_config.py         # 簡易設定クラス
├── sample_content.py        # サンプル生成機能
├── commands/                # CLIサブコマンド群
│   ├── convert.py           # 変換コマンド
│   ├── sample.py            # サンプル生成コマンド
│   ├── check_syntax.py      # 構文チェックコマンド
│   └── zip_dist.py          # 配布ZIP作成コマンド
├── core/                    # 核心機能モジュール群
│   ├── ast_nodes.py         # AST ノード定義
│   ├── keyword_parser.py    # キーワード解析エンジン
│   ├── list_parser.py       # リスト解析エンジン
│   ├── block_parser.py      # ブロック解析エンジン
│   ├── template_manager.py  # テンプレート管理
│   ├── toc_generator.py     # 目次生成
│   ├── config_manager.py    # 拡張設定管理
│   ├── file_ops.py          # ファイル操作
│   ├── performance.py       # パフォーマンス監視
│   ├── error_reporting.py   # エラー報告
│   ├── doc_classifier.py    # ドキュメント分類
│   ├── distribution_manager.py # 配布管理
│   ├── markdown_converter.py   # Markdown変換
│   ├── rendering/           # レンダリング系
│   │   ├── main_renderer.py       # メインレンダラー
│   │   ├── element_renderer.py    # 要素レンダラー
│   │   ├── compound_renderer.py   # 複合要素レンダラー
│   │   ├── html_formatter.py      # HTML整形
│   │   └── html_utils.py          # HTML ユーティリティ
│   ├── error_handling/      # エラー処理系
│   │   ├── error_handler.py       # エラーハンドラー
│   │   ├── error_factories.py     # エラーファクトリー
│   │   ├── error_types.py         # エラー型定義
│   │   ├── error_recovery.py      # エラー回復
│   │   └── smart_suggestions.py   # 賢い修正提案
│   ├── syntax/              # 構文検証系
│   │   ├── syntax_validator.py    # 構文検証
│   │   ├── syntax_rules.py        # 構文ルール
│   │   ├── syntax_errors.py       # 構文エラー
│   │   └── syntax_reporter.py     # 構文報告
│   ├── validators/          # 検証系
│   │   ├── document_validator.py  # ドキュメント検証
│   │   ├── file_validator.py      # ファイル検証
│   │   ├── structure_validator.py # 構造検証
│   │   ├── syntax_validator.py    # 構文検証
│   │   ├── performance_validator.py # パフォーマンス検証
│   │   ├── validation_issue.py    # 検証問題
│   │   └── validation_reporter.py # 検証報告
│   ├── utilities/           # ユーティリティ系
│   │   ├── converters.py          # 変換ユーティリティ
│   │   ├── data_structures.py     # データ構造
│   │   ├── file_system.py         # ファイルシステム
│   │   ├── logging.py             # ログ
│   │   ├── string_similarity.py   # 文字列類似度
│   │   └── text_processor.py      # テキスト処理
│   └── common/              # 共通基盤
│       ├── error_framework.py     # エラーフレームワーク
│       ├── smart_cache.py         # スマートキャッシュ
│       └── validation_mixin.py    # 検証ミックスイン
├── templates/               # HTMLテンプレート
│   ├── base.html.j2         # ベーステンプレート
│   ├── base-with-source-toggle.html.j2 # ソース表示機能付き
│   ├── docs.html.j2         # ドキュメント用
│   └── experimental/        # 実験的テンプレート
├── ui/                      # ユーザーインターフェース
│   └── console_ui.py        # コンソールUI
└── utils/                   # 汎用ユーティリティ
    └── marker_utils.py      # マーカーユーティリティ
```

## データフロー

```
入力テキスト
    ↓
Parser (parser.py) ← 統括クラス
    ↓ 委譲
KeywordParser, ListParser, BlockParser (core/)
    ↓ [AST: Node型の配列]
Renderer (renderer.py) ← 統括クラス
    ↓ 委譲  
HTMLRenderer, TemplateManager, TOCGenerator (core/)
    ↓ [HTML文字列]
出力HTML
```

## 主要クラス

### Parser (統括)
- **責務**: 解析フローの制御、特化パーサーへの委譲
- **依存**: KeywordParser, ListParser, BlockParser
- **メソッド**: 
  - `parse()`: メインの解析メソッド
  - 各特化パーサーへの委譲処理

### KeywordParser (core/keyword_parser.py)
- **責務**: キーワード記法解析の中核
- **特徴**: Node構築の基盤、他パーサーから使用される
- **メソッド**: 
  - キーワード認識・解析
  - NodeBuilder との連携

### ListParser (core/list_parser.py) 
- **責務**: リスト構造の解析
- **依存**: KeywordParser を使用
- **特徴**: ネストしたリスト構造の処理

### BlockParser (core/block_parser.py)
- **責務**: ブロック要素の解析
- **依存**: KeywordParser を使用
- **特徴**: 複合ブロック要素の処理

### Renderer (統括)
- **責務**: レンダリングフローの制御、出力統括
- **依存**: HTMLRenderer, TemplateManager, TOCGenerator
- **メソッド**:
  - `render()`: メインのレンダリングメソッド
  - 各専門レンダラーへの委譲

### HTMLRenderer (core/rendering/main_renderer.py)
- **責務**: HTML生成の中核処理
- **依存**: ElementRenderer, CompoundRenderer
- **特徴**: 循環依存を活用した委譲パターン

### Node (core/ast_nodes.py)
```python
@dataclass
class Node:
    type: str                    # 'paragraph', 'h1', 'image', etc.
    content: str                 # ノードの内容
    children: List['Node']       # 子ノード配列
    attributes: Dict[str, Any]   # 属性辞書
    # 追加フィールドによる拡張性
```

## アーキテクチャの特徴

### 1. モジュラー設計
- 機能別の専門モジュールに分離
- `core/` 配下でドメイン別にサブディレクトリ構成
- 明確な責務分離による保守性向上

### 2. 委譲パターン
- 統括クラス（Parser/Renderer）が特化クラスに処理を委譲
- 各特化クラスは単一責任を持つ
- 拡張時は特化クラスの追加で対応

### 3. AST中心設計
- Node型による統一的な中間表現
- 解析とレンダリングの完全分離
- 変換パイプラインの明確化

### 4. エラーハンドリング統合
- `core/error_handling/` による一元化
- 階層的なエラー処理とユーザーフレンドリーな報告
- 自動修正提案機能

### 5. 検証・品質保証
- `core/validators/` による多角的検証
- `core/syntax/` による構文チェック
- パフォーマンス監視機能

## 循環依存の管理

### HTMLRenderer ⟷ ElementRenderer
```python
# 意図的な循環依存（委譲パターン）
HTMLRenderer._main_renderer = self
ElementRenderer._main_renderer = renderer
```
**理由**: ElementRenderer が親レンダラーに再帰的レンダリングを委譲

## 拡張ポイント

### 1. 新しい記法追加
- `core/keyword_parser.py` でキーワード定義
- `core/syntax/syntax_rules.py` でルール追加
- `core/rendering/` でHTML出力対応

### 2. 新しい検証機能
- `core/validators/` に専門検証クラス追加
- `core/syntax/` に構文ルール追加

### 3. 新しい出力形式
- `core/rendering/` に専門レンダラー追加
- `templates/` にテンプレート追加

### 4. CLIサブコマンド追加
- `commands/` に新コマンドクラス追加
- `cli.py` でコマンド登録

## テスト戦略

- **ユニットテスト**: 各coreモジュールの境界値テスト
- **統合テスト**: Parser→Renderer のエンドツーエンドテスト  
- **E2Eテスト**: CLI経由の実ファイル変換テスト
- **ゴールデンテスト**: 期待出力との厳密比較
- **パフォーマンステスト**: 大容量ファイル処理検証

## 開発ガイドライン

### コアクラス修正時の注意点
1. **Parser系修正**: KeywordParserへの影響を必ず確認
2. **Renderer系修正**: ElementRendererとの循環依存を考慮
3. **Node構造変更**: Parser/Renderer両方への影響大
4. **エラー処理追加**: ErrorHandlerを経由して一元化

### AI開発での参照優先順位
1. **最重要**: Parser, Renderer, Node/NodeBuilder
2. **重要**: KeywordParser, HTMLRenderer, TemplateManager  
3. **補助**: ErrorHandler, TOCGenerator, console_ui