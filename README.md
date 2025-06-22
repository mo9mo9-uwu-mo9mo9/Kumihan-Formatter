# Kumihan-Formatter

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**CoC6th同人シナリオ**などのテキストファイルを、**ワンコマンドで配布可能なHTML**に自動組版するクロスプラットフォームCLIツールです。

## 🎯 特徴

- 📝 **シンプルな記法** - 直感的なブロック記法で簡単組版
- 🎨 **美しい出力** - CSS知識不要でプロ品質のHTML
- ⚡ **高速変換** - ワンコマンドで即座に変換完了
- 🖱️ **初心者にやさしい** - ダブルクリックで使える簡単操作

## 🚀 超簡単3ステップ

### ⚡ ステップ1: 初回セットアップ（1回だけ）
**Windows**: `setup.bat` をダブルクリック  
**macOS**: `setup.command` をダブルクリック

→ 自動で環境構築完了！

### 📝 ステップ2: 基本的な変換
**Windows**: `kumihan_convert.bat` をダブルクリック  
**macOS**: `kumihan_convert.command` をダブルクリック  

→ `.txt` ファイルをドラッグ&ドロップで変換

### 🎨 ステップ3: サンプル体験（お好みで）
**Windows**: `run_examples.bat` をダブルクリック  
**macOS**: `run_examples.command` をダブルクリック  

→ 全機能のサンプルを一括生成

### ⌨️ コマンドライン（上級者向け）
```bash
# インストール
pip install -e .

# 基本変換
kumihan your_file.txt

# サンプル生成
kumihan --generate-sample
```

### 📖 詳細ガイド
- **初回実行**: [FIRST_RUN.md](FIRST_RUN.md) - エラー解決法も含む詳細手順
- **基本的な使い方**: [クイックスタート](docs/user/QUICK_START.txt) - 5分で理解
- **マウス操作**: [ダブルクリックガイド](docs/user/DOUBLE_CLICK_GUIDE.md) - コマンド不要

## 📚 ドキュメント

### ユーザー向け
- [クイックスタート](docs/user/QUICK_START.txt) - 5分で始める使い方
- [インストールガイド](docs/user/INSTALL.md) - 詳細なインストール方法
- [記法一覧](docs/user/SYNTAX_CHEATSHEET.txt) - すべての記法をコンパクトに
- [ユーザーマニュアル](docs/user/USER_MANUAL.txt) - 完全な使用ガイド（1566行）
- [CLIリファレンス](docs/user/CLI_REFERENCE.md) - コマンドラインオプション詳細
- [ダブルクリックガイド](docs/user/DOUBLE_CLICK_GUIDE.md) - マウスだけで使う方法

### 開発者向け
- [開発者情報](dev/README.md) - 開発環境セットアップと基本情報
- [プロジェクト構造](docs/STRUCTURE.md) - ディレクトリ構成の詳細
- [アーキテクチャ](docs/dev/ARCHITECTURE.md) - 内部構造の解説
- [コントリビューション](docs/dev/CONTRIBUTING.md) - 開発参加ガイド
- [テストガイド](docs/dev/TESTING.md) - テストの実行方法
- [テストパターン生成](docs/user/USAGE_GENERATE_TEST.md) - 全記法の動作確認用
- [CLAUDE.md](CLAUDE.md) - Claude Code向けプロジェクト仕様書（ルートに配置）

### 上級者向け
- [設定ガイド](docs/user/CONFIG_GUIDE.md) - カスタマイズ方法（通常は不要）

## 📝 記法の例

```text
;;;見出し1
第1章：はじめに
;;;

これは通常の段落です。

;;;太字
重要な情報
;;;

;;;枠線
- 項目1
- 項目2
- 項目3
;;;

# エスケープ記法
###で始まる行は ;;; として表示されます
```

→ 美しいHTMLに自動変換されます！

## 📁 サンプルファイル

- [examples/](examples/) - 入力・出力・設定の各種サンプル
  - [入力サンプル](examples/input/) - 基本的な記法から高度な記法まで
  - [出力サンプル](examples/output/) - 変換結果の確認用
  - [設定サンプル](examples/config/) - カスタマイズ用設定ファイル

## 🤝 コントリビューション

バグ報告・機能要望は[Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)へ。
プルリクエストも歓迎します。

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照

---

**Kumihan-Formatter** - 美しい組版を、誰でも簡単に。