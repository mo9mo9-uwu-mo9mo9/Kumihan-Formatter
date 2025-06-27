# 🔧 Kumihan-Formatter トラブルシューティングガイド

> **初心者の自己解決率80%を目指す包括的なトラブルシューティングガイド**
>
> 問題解決の **症状 → 原因 → 解決法** の順で整理しています。目次から該当する症状を探してください。

---

## 📋 トラブルシューティング目次

### 🚨 **緊急度：高（変換できない）**

#### **[Python環境の問題](TROUBLESHOOTING_PYTHON.md)**
- `Python not found` / `python: command not found`
- `Virtual environment not found` / 仮想環境エラー
- `pip: command not found` / pipエラー
- `ImportError` / モジュールインポートエラー

#### **[エンコーディング・変換エラー](TROUBLESHOOTING_CONVERSION.md)**  
- テキストファイルが文字化けして読み込めない
- コンソール・コマンドプロンプトで日本語が文字化け
- Kumihan記法エラー / 構文エラー
- `FileNotFoundError` / ファイルが見つからない
- `PermissionError` / `Access denied`

### ⚠️ **緊急度：中（操作に支障）**

#### **[OS固有の問題](TROUBLESHOOTING_OS.md)**
- **Windows**: Defender警告、長いパス名エラー
- **macOS**: Gatekeeper警告、SIP関連エラー
- ファイル・権限関連の問題

#### **[表示・出力の問題](TROUBLESHOOTING_OUTPUT.md)**
- ブラウザが開かない / プレビューが表示されない
- 画像が表示されない / 画像リンクエラー
- 出力HTMLが崩れている / レイアウト問題

### 💡 **緊急度：低（予防・最適化）**

#### **[パフォーマンス・最適化](TROUBLESHOOTING_PERFORMANCE.md)**
- 変換が非常に遅い / ハングアップする
- 文字数制限 / 極端に長い行のエラー

#### **[高度なトラブルシューティング](TROUBLESHOOTING_ADVANCED.md)**
- デバッグ手法
- 予防的対策
- 完全リセット手順

---

## 🎯 **緊急対応チートシート**

### ⚡ **5分で解決！よくある問題TOP3**

#### **1. 変換が実行されない**
```bash
# ステップ1: Python確認
python --version  # Python 3.9以上必要

# ステップ2: セットアップ実行
# Windows: セットアップ_Windows.bat
# macOS: セットアップ_Mac.command

# ステップ3: 変換テスト
python -m kumihan_formatter examples/sample.txt
```

#### **2. 文字化けする**
**原因**: ファイルの文字コードがUTF-8でない
**解決法**: 
1. テキストエディタで「UTF-8」を選択して保存
2. メモ帳 → 「名前を付けて保存」→ 文字コード「UTF-8」

#### **3. 画像が表示されない**
**原因**: 画像ファイルが正しい場所にない
**解決法**:
```
プロジェクト/
├── document.txt       ← テキストファイル
├── images/            ← 画像フォルダ
│   └── picture.jpg    ← 画像ファイル
└── dist/             ← 出力先
    └── document.html
```

---

## 🔍 **症状別クイック検索**

| 症状 | 原因 | 解決法 | 詳細ページ |
|------|------|-------|-----------|
| **`Python not found`** | Pythonが未インストール | [Python公式サイト](https://python.org)からインストール | [Python環境](TROUBLESHOOTING_PYTHON.md) |
| **文字化け** | 文字コードがUTF-8でない | UTF-8で保存し直す | [エンコーディング](TROUBLESHOOTING_CONVERSION.md) |
| **画像表示されない** | 画像ファイルのパス間違い | `images/`フォルダに配置 | [出力問題](TROUBLESHOOTING_OUTPUT.md) |
| **ブラウザが開かない** | ブラウザの既定設定問題 | `--no-preview`で変換後手動で開く | [出力問題](TROUBLESHOOTING_OUTPUT.md) |
| **Defender警告** | 実行ファイルの誤検知 | 除外設定に追加 | [Windows問題](TROUBLESHOOTING_OS.md) |
| **変換が遅い** | ファイルサイズが大きすぎる | ファイル分割または軽量化 | [パフォーマンス](TROUBLESHOOTING_PERFORMANCE.md) |

---

## 📞 **サポートが必要な場合**

### 🎯 **効果的なサポート依頼の書き方**

以下の情報を含めて [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues) に報告してください：

```
## 環境情報
- OS: [Windows 10 / macOS Big Sur など]
- Pythonバージョン: [python --version の結果]
- Kumihan-Formatterバージョン: [バージョン番号]

## 問題の詳細
- 何をしようとしていたか: [具体的な操作]
- 実際に起こったこと: [エラーメッセージ等]
- 期待していた結果: [どうなるべきだったか]

## エラーメッセージ
```
[エラーメッセージを完全にコピペ]
```

## 再現手順
1. [具体的な手順]
2. [順番に記載]
3. [エラーが発生する]

## 試した解決方法
- [試した方法1]
- [試した方法2]
```

### 📋 **サポートチャンネル**

| チャンネル | 用途 | 応答時間 |
|-----------|------|----------|
| **[GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)** | バグ報告・機能要望 | 1-3日 |
| **[Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)** | 使い方相談・質問 | 1-7日 |

---

## 📚 **関連リソース**

### 🛠️ **基本ガイド**
- **[クイックスタートガイド](QUICKSTART.md)** - 初回セットアップ
- **[よくある質問（FAQ）](FAQ.md)** - 一般的な疑問
- **[実践ガイド](PRACTICAL_GUIDE.md)** - 効率的な使い方

### 🔧 **詳細トラブルシューティング**
- **[Python環境問題](TROUBLESHOOTING_PYTHON.md)** - インストール・環境設定
- **[変換・エンコーディング問題](TROUBLESHOOTING_CONVERSION.md)** - 文字化け・構文エラー
- **[OS固有問題](TROUBLESHOOTING_OS.md)** - Windows・macOS特有の問題
- **[出力・表示問題](TROUBLESHOOTING_OUTPUT.md)** - ブラウザ・画像・レイアウト
- **[パフォーマンス問題](TROUBLESHOOTING_PERFORMANCE.md)** - 速度・メモリ最適化
- **[高度なトラブルシューティング](TROUBLESHOOTING_ADVANCED.md)** - デバッグ・リセット手順

---

**問題が解決することを願っています！ 🙏**