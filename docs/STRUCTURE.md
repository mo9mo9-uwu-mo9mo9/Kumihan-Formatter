# プロジェクト構造

Kumihan-Formatterのディレクトリ構造とファイル配置の説明です。

## ディレクトリ構造

```
Kumihan-Formatter/
│
├── kumihan_formatter/      # メインパッケージ
│   ├── __init__.py        # パッケージ初期化
│   ├── cli.py             # CLIエントリポイント
│   ├── parser.py          # テキスト解析エンジン
│   ├── renderer.py        # HTML生成エンジン
│   ├── config.py          # 設定ファイル管理
│   ├── sample_content.py  # サンプルコンテンツ定義
│   ├── templates/         # HTMLテンプレート
│   │   └── base.html.j2   # ベーステンプレート
│   └── utils/             # ユーティリティ関数
│       └── __init__.py
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
- **サンプル出力**: `examples/output/`
- **テスト出力**: `*-output/`、`test_*/`など（.gitignoreで除外）

## 新機能追加時の配置ガイド

1. **機能コード**: `kumihan_formatter/` 内の適切なモジュールに追加
2. **テストコード**: `dev/tests/test_機能名.py` として追加
3. **サンプル**: `examples/input/` に入力例、`examples/output/` に出力例
4. **ドキュメント**: ユーザー向けは `docs/user/`、開発者向けは `docs/dev/`

## 注意事項

- `CLAUDE.md` は削除・移動禁止（開発ガイドライン）
- `.claude/` ディレクトリは削除・移動禁止（Claude Code設定）
- テスト出力ディレクトリは自動的に.gitignoreされます