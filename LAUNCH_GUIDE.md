# 🚀 Kumihan-Formatter 起動ガイド

どのファイルを使えばいいか迷ったときの**簡単な選択ガイド**です。

## ⚡ 初回利用時（重要！）

**まず最初にセットアップを実行してください:**

**Windows**: `setup.bat` をダブルクリック  
**macOS**: `setup.command` をダブルクリック

→ 1回実行すれば、後は他のファイルが使えるようになります！

---

## 🎯 目的別ファイル選択

### 📝 テキストファイルをHTMLに変換したい

**Windows:**
```
kumihan_convert.bat をダブルクリック
```

**macOS:**
```
kumihan_convert.command をダブルクリック
```

**使い方:**
1. 上記ファイルをダブルクリック
2. 変換したい `.txt` ファイルをドラッグ&ドロップ
3. 自動的にHTMLファイルが生成されます

---

### 🎨 機能を体験してみたい

**Windows:**
```
run_examples.bat をダブルクリック
```

**macOS:**
```
run_examples.command をダブルクリック
```

**使い方:**
1. 上記ファイルをダブルクリック
2. 自動的に全サンプルが生成されます
3. `examples/output/` フォルダで結果を確認できます

---

## 🗂️ ファイル一覧（整理済み）

| ファイル名 | 用途 | 使用頻度 | 実行順序 |
|----------|------|---------|----------|
| `setup.bat` | **初回セットアップ（Windows）** | ⭐⭐⭐ | **1番目** |
| `setup.command` | **初回セットアップ（macOS）** | ⭐⭐⭐ | **1番目** |
| `kumihan_convert.bat` | **メイン変換ツール（Windows）** | ⭐⭐⭐ | 2番目 |
| `kumihan_convert.command` | **メイン変換ツール（macOS）** | ⭐⭐⭐ | 2番目 |
| `run_examples.bat` | **サンプル実行（Windows）** | ⭐⭐ | 3番目 |
| `run_examples.command` | **サンプル実行（macOS）** | ⭐⭐ | 3番目 |

## 💡 使い分け

### 🔰 初心者の方（推奨フロー）
1. **最初に** `setup` でセットアップ
2. `run_examples` で機能を体験  
3. 慣れたら `kumihan_convert` で自分のファイルを変換

### 🏃‍♂️ すぐに使いたい方
1. **最初に** `setup` でセットアップ
2. `kumihan_convert` を直接使用

## ❓ トラブル時

何かうまくいかない場合は：
1. [FIRST_RUN.md](FIRST_RUN.md) - 初回セットアップガイド
2. [docs/user/USER_MANUAL.txt](docs/user/USER_MANUAL.txt) - 詳細マニュアル
3. [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues) - 質問・バグ報告

---

**🎉 迷ったときは `setup` → `kumihan_convert` の順で実行してください！**