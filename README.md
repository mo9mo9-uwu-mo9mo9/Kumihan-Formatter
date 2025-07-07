# Kumihan-Formatter

CoC6th同人シナリオなどのテキストファイルを、**ワンコマンドで美しいHTML**に変換する日本語ツールです。

![バージョン](https://img.shields.io/badge/version-0.3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![プラットフォーム](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)

## ✨ 特長

### 🎯 直感的な改行処理
**「改行したら、そのまま改行される」** - 他のツールでは複雑な操作が必要な改行処理が、期待通りに動作します。

| 他のツール | Kumihan-Formatter |
|-----------|-------------------|
| 2スペース+改行（Markdown） | **そのまま改行** |
| `<br>`タグ手動入力（HTML） | **自動で`<br>`挿入** |
| 学習コストあり | **学習コスト不要** |

[→ 改行処理について詳しく](docs/user/LINE_BREAK_GUIDE.md)

### 🎨 プロ品質の出力
- **美しい組版**: 適切なフォント・行間・レイアウト
- **印刷対応**: A4サイズで美しく印刷可能
- **配布可能**: HTMLファイル単体で完結

## 🚀 3ステップで始める

### 事前準備: Python インストール
このツールを使うには、**Python**（無料のプログラム実行環境）が必要です。

[→ 詳しいインストール手順](docs/user/INSTALLATION.md)

### ステップ1: ダウンロード
このページの緑色の「Code」ボタン → 「Download ZIP」→ 解凍

### ステップ2: 初回セットアップ
- **Windows**: `WINDOWS/初回セットアップ.bat` をダブルクリック
- **macOS**: `MAC/初回セットアップ.command` をダブルクリック

### ステップ3: 変換開始
- **Windows**: `WINDOWS/変換ツール.bat` をダブルクリック
- **macOS**: `MAC/変換ツール.command` をダブルクリック

**.txtファイル**をドラッグ&ドロップで変換完了！

### サンプル実行
- **Windows**: `WINDOWS/サンプル実行.bat`
- **macOS**: `MAC/サンプル実行.command`

## 💡 こんな方におすすめ・何ができるの？

### 🎯 おすすめの方
- **CoC6thシナリオ**を美しく配布したい同人作家の方
- **HTMLの知識なし**でも、きれいな文書を作りたい方
- **即売会やBooth**で配布可能な形式がほしい方

### ✨ 入力・出力例

**入力例（.txtファイル）**
```
;;;見出し1
シナリオタイトル
;;;

このシナリオは...

;;;太字
重要な情報
;;;
```

**出力**
プロ品質のHTML（A4印刷対応・配布可能）

## 🔧 基本的なKumihan記法

| 入力 | 説明 |
|------|------|
| `;;;見出し1\n内容\n;;;` | 見出し |
| `;;;太字\n内容\n;;;` | 太字 |
| `;;;枠線\n内容\n;;;` | 枠線 |
| `- 項目` | 箇条書きリスト |
| `;;;image.png;;;` | 画像埋め込み（imagesフォルダ内） |

[→ 完全な記法リファレンス](docs/user/SYNTAX_REFERENCE.md)

## 🛠️ うまくいかない時は

### よくあるエラー
- **Pythonが見つからない**: [インストール手順](docs/user/INSTALLATION.md)を確認
- **仮想環境エラー**: 初回セットアップを再実行
- **変換失敗**: .txtファイル・ファイル名を確認

[→ 詳しいトラブルシューティング](docs/user/TROUBLESHOOTING.md)

## 🤝 フィードバック・お問い合わせ

- **バグ報告・機能要望**: [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **使い方相談**: [Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)

## 📖 もっと詳しく

### 📚 基本レベル
- **[QUICKSTART.md](docs/user/QUICKSTART.md)** - はじめての方向け詳細ガイド
- **[examples/](examples/)** - サンプルファイル集

### 📖 応用レベル
- **[実践ガイド](docs/user/PRACTICAL_GUIDE.md)** - 全機能の使い方
- **[SYNTAX_REFERENCE.md](docs/user/SYNTAX_REFERENCE.md)** - 完全Kumihan記法リファレンス

### ⚙️ 上級者向け
- **[設定ガイド](docs/user/CONFIG_GUIDE.md)** - カスタマイズ・設定ファイル（JSON/YAML）

### 🛠️ 開発者向け
- **[記法ツール使用ガイド](docs/dev/SYNTAX_TOOLS.md)** - 記法チェック・自動修正ツール（macOS D&D制限対応）

## 📄 ライセンス

MIT License

---

**Kumihan-Formatter** - 美しい組版を、誰でも簡単に。 ✨
