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

## 🎯 3ステップで始める

### ステップ1: インストール

```bash
# プロジェクトディレクトリに移動
cd Kumihan-Formatter

# インストール実行
pip install -e .
```

💡 **エラーが出た場合:**
- `pip3 install -e .` を試してください
- 権限エラーの場合: `pip install -e . --user`

### ステップ2: 機能を体験

```bash
# サンプル生成（どんなことができるか確認）
kumihan --generate-sample
```

✅ **成功の確認:**
- `showcase.txt` と `showcase.html` が生成される
- ブラウザが自動で開いて結果が表示される

### ステップ3: 自分のファイルを変換

```bash
# 基本的なサンプルを変換
kumihan examples/input/sample.txt

# より高度なサンプルを変換
kumihan examples/input/comprehensive-sample.txt
```

🎉 **おめでとうございます！** これで基本的な使い方をマスターしました。

## 🖱️ マウスだけで使う方法（推奨）

コマンドが苦手な方は、**ダブルクリック**だけで使えます：

### Windows
1. `kumihan_convert.bat` をダブルクリック
2. 変換したい `.txt` ファイルを選択
3. 自動的にHTMLが生成されます

### macOS
1. `kumihan_convert.command` をダブルクリック
2. 変換したい `.txt` ファイルを選択
3. 自動的にHTMLが生成されます

詳細は [ダブルクリックガイド](docs/user/DOUBLE_CLICK_GUIDE.md) をご覧ください。

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

## 🔧 デスクトップランチャーの設定

### Windows
```bash
setup_desktop_launcher.bat
```
→ デスクトップにショートカットが作成されます

### macOS
```bash
./setup_desktop_launcher.command
```
→ デスクトップにエイリアスが作成されます

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