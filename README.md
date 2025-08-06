# Kumihan-Formatter

![Status](https://img.shields.io/badge/status-Development-orange.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)

> CoC6th同人シナリオなどのテキストファイルを、**ワンコマンドで美しいHTML**に変換する日本語ツール

**⚠️ 現在のステータス**: 開発中 (Development) - リリース前アルファ版

**🇯🇵 言語サポート**: 本ツールは**日本語専用**です。英語やその他の言語への対応予定はありません。

## ✨ 特徴

- **🎯 直感的な改行処理** - 改行したら、そのまま改行される
- **🎨 プロ品質の出力** - 美しい組版、A4印刷対応
- **📱 クロスプラットフォーム** - Windows・macOS対応

## 🚀 クイックスタート

**GUI版**:
1. [リリースページ](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases)からダウンロード
2. `.txtファイル`をドラッグ&ドロップで変換完了！

**開発者向け**:
```bash
# 開発環境セットアップ
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# 開発環境セットアップ
python -m pip install -e .
python -m pip install -r requirements-dev.txt

# Git hooks セットアップ（必須）
./scripts/install-hooks.sh

# 開発用CLI使用例
python -m kumihan_formatter convert input.txt

# 開発ログの有効化（Claude Code向け）
KUMIHAN_DEV_LOG=true python -m kumihan_formatter convert input.txt

# 品質チェック
make lint           # コード品質チェック
```

### 🌟 開発参加者向け重要事項

**ブランチ命名規則**（厳格適用）:
```bash
# ✅ 正しいブランチ名
feat/issue-123-add-user-authentication
fix/issue-456-fix-parsing-error
docs/issue-789-update-readme

# ❌ 禁止（システム的に拒否される）
feat/issue-123-ユーザー認証追加  # 日本語禁止
feature-branch                    # Issue番号なし
```

**システム的制約**:
- 日本語ブランチ名は **Git hooks・GitHub Actions で自動検出・拒否**
- **初回セットアップ時は必ず** `./scripts/install-hooks.sh` を実行
- **一時ファイル出力は `tmp/` 配下必須** - プロジェクトルート直下への出力は禁止
- 詳細は [CLAUDE.md](./CLAUDE.md) と [コーディング規約](./docs/dev/coding-standards.md) を参照

### 🚀 初回セットアップガイド

開発環境の初回セットアップは以下の順序で実行してください：

```bash
# 1. リポジトリクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# 2. Python依存関係インストール
python -m pip install -e .
python -m pip install -r requirements-dev.txt

# 3. Git hooks インストール（重要！）
./scripts/install-hooks.sh

# 4. 動作確認
make lint
```

**⚠️ 重要**: `./scripts/install-hooks.sh` を実行しないと、日本語ブランチ名でのプッシュ時にローカルでエラーが発生しません。GitHub Actions でのみ検出されるため、必ず実行してください。

## ⚙️ オプション依存関係

Kumihan-Formatterでは、特定機能を利用する際に追加パッケージのインストールが必要です：

### 📊 パフォーマンス監視機能
```bash
# メモリ使用量追跡機能を利用する場合
pip install "kumihan-formatter[performance]"

# または個別インストール
pip install psutil>=5.9
```

**利用可能な機能**:
- リアルタイムメモリ使用量表示
- プログレスバーでのメモリ統計
- パフォーマンス監視レポート

**対応コマンド**:
```bash
# メモリ監視付き変換（psutil必須）
kumihan convert input.txt --progress-level verbose

# プログレスログ出力（メモリ統計含む）
kumihan convert input.txt --progress-log progress.json
```

## 💡 基本的な記法（α-dev）

```
#見出し1#
シナリオタイトル
##

このシナリオは...

#太字#
重要な情報
##

#ハイライト color=yellow#
注目すべきポイント
##

#目次#
##
```

→ **プロ品質のHTML出力**

**⚠️ 重要変更**: α-devから全記法がブロック形式に統一され、単一行記法は完全廃止されました。

## 📁 プロジェクト構造

```
Kumihan-Formatter/
├── kumihan_formatter/      # メインパッケージ
├── tests/                  # テストファイル
│   └── debug/             # デバッグ用テストファイル
├── docs/                   # ドキュメント
│   ├── reports/           # テストレポート
│   └── specs/    # 詳細仕様書
├── scripts/               # ユーティリティスクリプト
├── samples/               # サンプルファイル
├── output/                # 出力ファイル（gitignore対象）
├── tools/                 # 開発ツール
├── archive/               # アーカイブファイル
└── [設定ファイル]         # .gitignore, pyproject.toml等
```

## 📖 ドキュメント

### ユーザー向け
- **[🚀 クイックスタート](docs/user/getting-started.md)** - 30分で始める
- **[📚 ユーザーガイド](docs/user/user-guide.md)** - 詳細な使い方
- **[📝 記法リファレンス](docs/user/notation-reference.md)** - 記法のクイックリファレンス
- **[❓ FAQ](docs/user/faq.md)** - よくある質問

### 開発者向け
- **[🏗️ アーキテクチャ](docs/dev/architecture.md)** - システム設計
- **[🚀 デプロイガイド](docs/dev/deployment.md)** - パッケージング・配布

### 仕様書
- **[📝 記法仕様概要](SPEC.md)** - 基本的な記法仕様
- **[📋 記法仕様詳細](docs/specs/notation.md)** - 完全な記法仕様
- **[⚙️ 機能仕様](docs/specs/functional.md)** - システム機能仕様
- **[❗ エラーメッセージ仕様](docs/specs/error-messages.md)** - エラー仕様

### Claude Code向け
- **[🔧 Claude Code リファレンス](docs/claude/reference.md)** - Claude Code効率化ガイド

## 🔧 開発者向け機能

### デバッグ機能
GUIアプリケーションやCLI版で問題が発生した場合、詳細なデバッグ機能を利用できます：

```bash
# GUIデバッグモード
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher

# CLI開発ログ
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt
```


## 🤝 サポート

- **バグ報告・機能要望**: [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **使い方相談**: [Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)
- **開発に参加**: [Contributing Guide](CONTRIBUTING.md)

### 🚨 コードレビュー規則
**重要**: このプロジェクトでは **日本語でのレビューを義務付け** しています。
- ✅ すべてのPRレビューは日本語で行ってください
- ❌ 英語でのレビューは受け付けません
- 詳細: [CONTRIBUTING.md](CONTRIBUTING.md#-日本語レビュー必須規則)

## 📄 ライセンス

Proprietary License - Copyright © 2025 mo9mo9-uwu-mo9mo9
All rights reserved.
