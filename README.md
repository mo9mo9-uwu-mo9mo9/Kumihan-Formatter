# Kumihan-Formatter

![Tests](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/workflows/Tests/badge.svg)
![Version](https://img.shields.io/badge/version-0.9.0--alpha.1-orange.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)

> CoC6th同人シナリオなどのテキストファイルを、**ワンコマンドで美しいHTML**に変換する日本語ツール

**⚠️ 現在のバージョン**: v0.9.0-alpha.1 (アルファ版・テスト改善用)
**注意**: このバージョンはテスト目的です。正式リリースではありません。

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

# 開発用CLI使用例
python -m kumihan_formatter convert input.txt

# 開発ログの有効化（Claude Code向け）
KUMIHAN_DEV_LOG=true python -m kumihan_formatter convert input.txt
```

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

- **[📚 はじめてのガイド](docs/user/quickstart.md)** - 初回セットアップから使い方まで
- **[📝 記法リファレンス](docs/user/syntax.md)** - Kumihan記法の完全ガイド
- **[⚙️ インストール詳細](docs/user/installation.md)** - Python環境構築
- **[🛠️ 開発者向け](docs/dev/)** - API・貢献方法

## 🔧 開発者向け機能

### デバッグ機能
GUIアプリケーションやCLI版で問題が発生した場合、詳細なデバッグ機能を利用できます：

```bash
# GUIデバッグモード
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher

# CLI開発ログ
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt
```

**詳細**: [デバッグガイド](docs/dev/DEBUGGING.md)

### Pre-commit Hook警告への対応
このプロジェクトでは技術的負債を防ぐため、pre-commit hookでファイルサイズ制限（300行）をチェックしています。

**警告が表示された場合**:
- `status code 1`は正常動作です（警告表示）
- 警告は無視せず、必ず対応してください
- 詳細な対応手順は[CONTRIBUTING.md](CONTRIBUTING.md#pre-commit-hook警告への対応)を参照

```bash
# 違反ファイルの確認
python3 scripts/check_file_size.py --max-lines=300
```

## 🤝 サポート

- **バグ報告・機能要望**: [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **使い方相談**: [Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)
- **開発に参加**: [Contributing Guide](CONTRIBUTING.md)

## 📄 ライセンス

Proprietary License - Copyright © 2025 mo9mo9-uwu-mo9mo9
All rights reserved.
