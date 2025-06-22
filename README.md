# Kumihan-Formatter

CoC6th同人シナリオなどのテキストファイルを、**ワンコマンドで美しいHTML**に変換する日本語ツールです。

![バージョン](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![プラットフォーム](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)

## 🚀 3ステップで始める

### ステップ1: ダウンロード
1. [最新版をダウンロード](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases) 
2. zipファイルを解凍してフォルダを開く

### ステップ2: 初回セットアップ
**Windows**
- `WINDOWS/` フォルダ内の `初回セットアップ.bat` をダブルクリック

**macOS**  
- `MAC/` フォルダ内の `初回セットアップ.command` をダブルクリック

*自動で必要な環境がセットアップされます（数分かかります）*

### ステップ3: 変換開始
**Windows**
- `WINDOWS/` フォルダ内の `変換ツール.bat` をダブルクリック

**macOS**
- `MAC/` フォルダ内の `変換ツール.command` をダブルクリック

**.txtファイル**をドラッグ&ドロップするだけで変換完了！

## 💡 こんな方におすすめ

- **CoC6thシナリオ**を美しく配布したい同人作家の方
- **HTMLの知識はない**けれど、きれいな文書を作りたい方  
- **Word等の組版ソフトを使わず**に、テキストファイルから直接変換したい方
- **即売会やBooth**で配布可能な形式がほしい方

## ✨ 何ができるの？

### 入力（.txtファイル）
```
;;;見出し1
クトゥルフ神話TRPG シナリオサンプル
;;;

このシナリオは、フォーマッターのテスト用サンプルです。

;;;見出し2
シナリオ概要
;;;

;;;太字
探索者たちは、とある不可解な事件の調査を依頼されます。
;;;

- 推奨人数: 2〜4人
- プレイ時間: 3〜4時間
- 推奨技能: 図書館、目星、心理学

;;;枠線
舞台は1920年代のアメリカ、マサチューセッツ州アーカム。
霧深い港町で、奇妙な失踪事件が相次いでいる。
;;;
```

### 出力（美しいHTML）
- **プロ品質の組版**：きれいなフォント、適切な行間、美しいレイアウト
- **印刷対応**：A4サイズで美しく印刷可能
- **配布可能**：HTMLファイル単体で完結、どこでも表示可能

## 🔧 基本的な記法

| 記法 | 効果 |
|------|------|
| `;;;太字\n内容\n;;;` | **太字で強調** |
| `;;;枠線\n内容\n;;;` | 枠線で囲んで強調 |
| `;;;見出し1\nタイトル\n;;;` | 大見出し |
| `;;;見出し2\nサブタイトル\n;;;` | 中見出し |
| `- 項目` | 箇条書きリスト |

[→ 詳しい記法を見る](docs/SYNTAX_REFERENCE.md)

## 🎯 サンプルを試してみる

**Windows**
- `WINDOWS/` フォルダ内の `サンプル実行.bat` をダブルクリック

**macOS**
- `MAC/` フォルダ内の `サンプル実行.command` をダブルクリック

サンプルファイルが変換され、`examples/output/` フォルダに結果が保存されます。

## 🛠️ うまくいかない時は

よくある問題と解決策：

### Python が見つからないエラー
```
💡 Python 3.9以上が必要です
→ https://python.org からダウンロードしてインストール
```

### 仮想環境エラー
```  
💡 もう一度セットアップを実行してください
→ WINDOWS/初回セットアップ.bat (Windows) または MAC/初回セットアップ.command (macOS) をダブルクリック
```

### 変換がうまくいかない
```
💡 ファイル名を確認してください
→ .txt ファイルのみ対応しています
→ ファイル名に特殊文字が含まれていませんか？
```

[→ 詳しいトラブルシューティング](docs/TROUBLESHOOTING.md)

## 📖 もっと詳しく

### 📚 基本レベル
- **[QUICKSTART.md](docs/QUICKSTART.md)** - はじめての方向け詳細ガイド
- **[examples/](examples/)** - サンプルファイル集

### 📖 応用レベル  
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** - 全機能の使い方
- **[SYNTAX_REFERENCE.md](docs/SYNTAX_REFERENCE.md)** - 完全記法リファレンス

### ⚙️ 上級者向け
- **[ADVANCED.md](docs/ADVANCED.md)** - カスタマイズ・設定ファイル（JSON/YAML）

## 🤝 フィードバック・お問い合わせ

- **バグ報告・機能要望**: [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **使い方がわからない**: [Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)

## 📄 ライセンス

MIT License - 自由に改変・利用可能です（再配布は禁止）

---

**Kumihan-Formatter** - 美しい組版を、誰でも簡単に。 ✨