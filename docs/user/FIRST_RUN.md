# 🚀 はじめての実行ガイド

Kumihan-Formatterを**初めて使う方向け**の詳細な手順書です。

## 📋 事前準備

### 必要な環境
- **Python 3.9以上** がインストールされていること
- **Windows** または **macOS**

### Python確認方法
```bash
python3 --version
```
→ `Python 3.9.x` 以降が表示されればOK

## 🎯 超簡単2ステップで始める

### ⚡ ステップ1: 初回セットアップ（1回だけ）

**Windows**: `WINDOWS/初回セットアップ.bat` をダブルクリック  
**macOS**: `MAC/初回セットアップ.command` をダブルクリック

✅ **成功の確認:**
- `[OK] Dependencies installed successfully` が表示される
- `Setup Complete!` のメッセージが表示される

### 🎉 ステップ2: すぐに使える！

**変換したい場合:**
- **Windows**: `WINDOWS/変換ツール.bat` をダブルクリック
- **macOS**: `MAC/変換ツール.command` をダブルクリック

**サンプルを試したい場合:**
- **Windows**: `WINDOWS/サンプル実行.bat` をダブルクリック  
- **macOS**: `MAC/サンプル実行.command` をダブルクリック

🎉 **おめでとうございます！** これで基本的な使い方をマスターしました。

## ✨ より詳しい使い方

### 🎨 サンプルで機能体験
セットアップ後、すぐに全機能を体験できます：

**Windows**: `WINDOWS/サンプル実行.bat` をダブルクリック  
**macOS**: `MAC/サンプル実行.command` をダブルクリック

→ `dist/samples/` フォルダに結果が生成されます

### 📝 自分のファイルを変換
セットアップ後、いつでもファイル変換できます：

**Windows**: `kumihan_convert.bat` をダブルクリック  
**macOS**: `kumihan_convert.command` をダブルクリック

→ `.txt` ファイルをドラッグ&ドロップするだけ

## 🎨 基本的な記法（コピペして試そう！）

以下をメモ帳に貼り付けて `test.txt` として保存し、変換してみてください：

```text
;;;見出し1
私の最初のシナリオ
;;;

これは普通の段落です。
空行で段落を区切ります。

;;;太字
重要な情報はこのように強調できます
;;;

;;;枠線
シーン情報や重要な部分を枠で囲めます：
- 場所：古い図書館
- 時間：深夜
- 参加者：3-4人
;;;

;;;見出し2
第1章：始まり
;;;

物語がここから始まります...

;;;ハイライト color=#ffffcc
黄色のハイライトで注意を引くことができます
;;;

;;;太字+枠線
複数のスタイルを組み合わせることも可能です
;;;
```

## ❗ よくあるエラーと解決法

### エラー1: `kumihan: command not found`
**原因:** インストールが正しく完了していない
**解決法:**
```bash
pip install -e .
# または
pip3 install -e .
```

### エラー2: `ModuleNotFoundError: No module named 'click'`
**原因:** 依存関係がインストールされていない
**解決法:**
```bash
pip install -e ".[dev]"
```

### エラー3: ブラウザが開かない
**原因:** `--no-preview` オプションが指定されている
**解決法:**
```bash
# --no-preview を外して実行
kumihan your_file.txt
```

### エラー4: ファイルが見つからない
**原因:** ファイルパスが間違っている
**解決法:**
```bash
# フルパスで指定
kumihan /path/to/your/file.txt

# または相対パスで
kumihan ./your_file.txt
```

## 🗂️ 起動ファイルの選び方

どのファイルを使うか迷ったときは **[LAUNCH_GUIDE.md](LAUNCH_GUIDE.md)** をご覧ください。

**基本的には:**
- **メイン変換**: `kumihan_convert.bat` (Windows) / `kumihan_convert.command` (macOS)
- **サンプル体験**: `run_examples.bat` (Windows) / `run_examples.command` (macOS)

## 📚 次のステップ

基本的な使い方をマスターしたら：

1. **[記法一覧](docs/user/SYNTAX_CHEATSHEET.txt)** - すべての記法を確認
2. **[ユーザーマニュアル](docs/user/USER_MANUAL.txt)** - 詳細な機能説明
3. **[サンプル集](examples/)** - 様々な使用例
4. **[設定ガイド](docs/user/CONFIG_GUIDE.md)** - カスタマイズ方法（上級者向け）

## 🆘 サポート

困ったときは：
- [よくある質問](docs/user/USER_MANUAL.txt) を確認
- [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues) で質問
- [プロジェクトページ](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter) で最新情報を確認

---

**🎯 目標**: 5分以内に最初のHTML変換を成功させること！
**💡 ヒント**: まずはサンプルファイルから始めるのがおすすめです。