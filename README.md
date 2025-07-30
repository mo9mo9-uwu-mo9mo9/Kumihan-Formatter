# Kumihan-Formatter

![Version](https://img.shields.io/badge/version-0.9.0--alpha.8-orange.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)

> CoC6th同人シナリオなどのテキストファイルを、**ワンコマンドで美しいHTML**に変換する日本語ツール

**⚠️ 現在のバージョン**: v0.9.0-alpha.8 (アルファ版・開発中)

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
- 詳細は [CLAUDE.md](./CLAUDE.md) を参照

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

## 💡 基本的な記法

```
;;;見出し1
シナリオタイトル
;;;

このシナリオは...

;;;太字
重要な情報
;;;
```

→ **プロ品質のHTML出力**

## 📖 ドキュメント

- **[📚 ユーザーガイド](docs/USER_GUIDE.md)** - エンドユーザー向け完全ガイド
- **[📝 記法仕様](SPEC.md)** - Kumihan記法の詳細仕様
- **[🛠️ 開発者向け](docs/DEVELOPMENT_GUIDE.md)** - 開発ガイド
- **[🔧 Claude Code向け](docs/REFERENCE.md)** - Claude Code効率化リファレンス

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
