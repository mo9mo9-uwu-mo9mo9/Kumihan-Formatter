# コードベース構造

## ディレクトリ構造
```
kumihan_formatter/
├── core/                    # コアロジック
│   ├── ast_nodes/          # AST(抽象構文木)ノード
│   ├── block_parser/       # ブロック解析
│   ├── config/             # 設定管理
│   ├── distribution/       # 配布用処理
│   ├── keyword_parsing/    # キーワード解析
│   ├── rendering/          # HTML出力
│   ├── syntax/             # 構文検証
│   ├── utilities/          # 共通ユーティリティ
│   └── validators/         # 検証ロジック
├── gui_*/                  # GUI関連
│   ├── gui_controllers/    # GUI制御
│   ├── gui_models/         # GUIモデル
│   └── gui_views/          # GUI表示
├── commands/               # CLIコマンド実装
├── config/                 # 設定ファイル管理
├── models/                 # データモデル
├── ui/                     # コンソールUI
└── utils/                  # ユーティリティ
```

## メインモジュール
- `cli.py` - CLIエントリーポイント
- `parser.py` - メインパーサー
- `renderer.py` - HTMLレンダラー
- `gui_launcher.py` - GUIランチャー

## 重要な設計パターン
- Factory パターン（各種コンポーネント生成）
- Strategy パターン（レンダリング戦略）
- Command パターン（CLIコマンド）
- MVC パターン（GUIアーキテクチャ）

## テンプレートとアセット
- `templates/` - Jinja2テンプレート
- `assets/` - CSS/JSファイル

## 外部ファイル
- `docs/` - ドキュメント
- `scripts/` - 開発スクリプト
- `tools/` - 開発ツール