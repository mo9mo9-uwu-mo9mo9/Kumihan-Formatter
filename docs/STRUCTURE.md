# プロジェクト構造

Kumihan-Formatterのディレクトリ構造とファイル配置の説明です。

## ディレクトリ構造

```
Kumihan-Formatter/
│
├── kumihan_formatter/      # メインパッケージ
│   ├── __init__.py        # パッケージ初期化
│   ├── __main__.py        # パッケージ実行エントリポイント
│   ├── cli.py             # CLIエントリポイント
│   ├── parser.py          # 解析統括クラス
│   ├── renderer.py        # レンダリング統括クラス
│   ├── config.py          # 基本設定管理
│   ├── simple_config.py   # 簡易設定クラス
│   ├── sample_content.py  # サンプルコンテンツ定義
│   ├── commands/          # CLIサブコマンド群
│   │   ├── __init__.py
│   │   ├── convert.py     # 変換コマンド
│   │   ├── sample.py      # サンプル生成コマンド
│   │   ├── check_syntax.py # 構文チェックコマンド
│   │   └── zip_dist.py    # 配布ZIP作成コマンド
│   ├── core/              # 核心機能モジュール群
│   │   ├── __init__.py
│   │   ├── ast_nodes.py   # AST ノード定義
│   │   ├── keyword_parser.py # キーワード解析エンジン
│   │   ├── list_parser.py # リスト解析エンジン
│   │   ├── block_parser.py # ブロック解析エンジン
│   │   ├── template_manager.py # テンプレート管理
│   │   ├── toc_generator.py # 目次生成
│   │   ├── config_manager.py # 拡張設定管理
│   │   ├── file_ops.py    # ファイル操作
│   │   ├── performance.py # パフォーマンス監視
│   │   ├── error_reporting.py # エラー報告
│   │   ├── doc_classifier.py # ドキュメント分類
│   │   ├── distribution_manager.py # 配布管理
│   │   ├── markdown_converter.py # Markdown変換
│   │   ├── rendering/     # レンダリング系
│   │   │   ├── __init__.py
│   │   │   ├── main_renderer.py # メインレンダラー
│   │   │   ├── element_renderer.py # 要素レンダラー
│   │   │   ├── compound_renderer.py # 複合要素レンダラー
│   │   │   ├── html_formatter.py # HTML整形
│   │   │   └── html_utils.py # HTML ユーティリティ
│   │   ├── error_handling/ # エラー処理系
│   │   │   ├── __init__.py
│   │   │   ├── error_handler.py # エラーハンドラー
│   │   │   ├── error_factories.py # エラーファクトリー
│   │   │   ├── error_types.py # エラー型定義
│   │   │   ├── error_recovery.py # エラー回復
│   │   │   └── smart_suggestions.py # 賢い修正提案
│   │   ├── syntax/        # 構文検証系
│   │   │   ├── __init__.py
│   │   │   ├── syntax_validator.py # 構文検証
│   │   │   ├── syntax_rules.py # 構文ルール
│   │   │   ├── syntax_errors.py # 構文エラー
│   │   │   └── syntax_reporter.py # 構文報告
│   │   ├── validators/    # 検証系
│   │   │   ├── __init__.py
│   │   │   ├── document_validator.py # ドキュメント検証
│   │   │   ├── file_validator.py # ファイル検証
│   │   │   ├── structure_validator.py # 構造検証
│   │   │   ├── syntax_validator.py # 構文検証
│   │   │   ├── performance_validator.py # パフォーマンス検証
│   │   │   ├── validation_issue.py # 検証問題
│   │   │   └── validation_reporter.py # 検証報告
│   │   ├── utilities/     # ユーティリティ系
│   │   │   ├── __init__.py
│   │   │   ├── converters.py # 変換ユーティリティ
│   │   │   ├── data_structures.py # データ構造
│   │   │   ├── file_system.py # ファイルシステム
│   │   │   ├── logging.py # ログ
│   │   │   ├── string_similarity.py # 文字列類似度
│   │   │   └── text_processor.py # テキスト処理
│   │   └── common/        # 共通基盤
│   │       ├── __init__.py
│   │       ├── error_framework.py # エラーフレームワーク
│   │       ├── smart_cache.py # スマートキャッシュ
│   │       └── validation_mixin.py # 検証ミックスイン
│   ├── templates/         # HTMLテンプレート
│   │   ├── base.html.j2   # ベーステンプレート
│   │   ├── base-with-source-toggle.html.j2 # ソース表示機能付き
│   │   ├── docs.html.j2   # ドキュメント用
│   │   └── experimental/  # 実験的テンプレート
│   │       └── base-with-scroll-sync.html.j2
│   ├── ui/                # ユーザーインターフェース
│   │   ├── __init__.py
│   │   └── console_ui.py  # コンソールUI
│   └── utils/             # 汎用ユーティリティ
│       ├── __init__.py
│       └── marker_utils.py # マーカーユーティリティ
│
├── dev/                   # 開発用ファイル（開発者のみ）
│   ├── tests/            # テストコード
│   │   ├── test_parser.py
│   │   ├── test_renderer.py
│   │   ├── test_config.py
│   │   ├── test_cli.py
│   │   └── ...
│   ├── tools/            # 開発ツール
│   │   ├── generate_test_file.py  # テストファイル生成
│   │   ├── generate_showcase.py    # ショーケース生成
│   │   └── cleanup.py             # 一時ファイル削除
│   ├── test_data/        # テスト用データファイル
│   │   └── test_*.txt
│   └── README.md         # 開発者向け情報
│
├── examples/              # サンプルファイル（ユーザー向け）
│   ├── input/            # 入力サンプル
│   │   ├── sample.txt
│   │   └── comprehensive-sample.txt
│   ├── output/           # 出力サンプル
│   │   └── kumihan_sample/
│   └── config/           # 設定ファイルサンプル
│       └── config-sample.yaml
│
├── docs/                  # ドキュメント
│   ├── user/             # ユーザー向けドキュメント
│   │   ├── USER_MANUAL.txt
│   │   ├── QUICK_START.txt
│   │   └── ...
│   ├── dev/              # 開発者向けドキュメント
│   │   └── ...
│   └── STRUCTURE.md      # 本ファイル
│
├── kumihan_convert.bat    # Windows用実行スクリプト
├── kumihan_convert.command # macOS用実行スクリプト
├── setup_desktop_launcher.bat    # Windows用デスクトップ設定
├── setup_desktop_launcher.command # macOS用デスクトップ設定
│
├── pyproject.toml         # プロジェクト設定・依存関係
├── README.md              # プロジェクト概要
├── LICENSE                # ライセンス情報
├── CLAUDE.md              # 開発ガイドライン
└── .gitignore            # Git除外設定
```

## ディレクトリの役割

### ユーザー向けディレクトリ

- **kumihan_formatter/**: メインのPythonパッケージ。変換エンジンの本体
- **examples/**: 使い方を学ぶためのサンプルファイル群
- **docs/user/**: ユーザー向けの詳細なドキュメント
- **ルートの実行スクリプト**: すぐに使い始められる実行ファイル

### 開発者向けディレクトリ

- **dev/**: 開発・テスト用のファイル（通常のユーザーは触る必要なし）
  - **tests/**: 自動テストコード
  - **tools/**: 開発支援ツール
  - **test_data/**: テスト用データ
- **docs/dev/**: 開発者向けドキュメント

## ファイル命名規則

### Pythonファイル
- **一般モジュール**: `snake_case.py`（例：`parser.py`）
- **テストファイル**: `test_モジュール名.py`（例：`test_parser.py`）
- **実行スクリプト**: 機能を表す動詞から始める（例：`generate_test_file.py`）

### ドキュメント
- **ユーザー向け**: 大文字で分かりやすい名前（例：`QUICK_START.txt`）
- **技術文書**: Markdown形式（例：`STRUCTURE.md`）

### 出力ディレクトリ
- **正式な出力**: `dist/`（ユーザーが指定可能）
- **サンプル出力**: `dist/samples/`
- **テスト出力**: `*-output/`、`test_*/`など（.gitignoreで除外）

## 新機能追加時の配置ガイド

### 1. 機能コードの配置
- **解析機能**: `kumihan_formatter/core/` 内の適切なサブディレクトリ
- **レンダリング機能**: `kumihan_formatter/core/rendering/`
- **検証機能**: `kumihan_formatter/core/validators/` または `kumihan_formatter/core/syntax/`
- **CLIサブコマンド**: `kumihan_formatter/commands/`
- **ユーティリティ**: `kumihan_formatter/core/utilities/`

### 2. テストコードの配置
- **ユニットテスト**: `dev/tests/test_機能名.py`
- **統合テスト**: `dev/tests/integration/`
- **E2Eテスト**: `dev/tests/e2e/`

### 3. サンプル・出力の配置
- **入力サンプル**: `examples/input/`
- **出力サンプル**: `dist/samples/`
- **テストデータ**: `dev/test_data/`

### 4. ドキュメントの配置
- **ユーザー向け**: `docs/user/`
- **開発者向け**: `docs/dev/`
- **アーキテクチャ**: `docs/dev/ARCHITECTURE.md`
- **クラス依存関係**: `docs/CLASS_DEPENDENCY_MAP.md`

## 注意事項

- `CLAUDE.md` は削除・移動禁止（開発ガイドライン）
- `.claude/` ディレクトリは削除・移動禁止（Claude Code設定）
- テスト出力ディレクトリは自動的に.gitignoreされます