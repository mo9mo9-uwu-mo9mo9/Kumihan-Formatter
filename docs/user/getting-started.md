# Kumihan-Formatter クイックスタート

> 30分でKumihan-Formatterの基本的な使い方をマスターしましょう

## インストール

### GUI版（推奨）
1. [リリースページ](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases)からダウンロード
2. `.txtファイル`をドラッグ&ドロップで変換完了！

### 開発者向け
```bash
# リポジトリのクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# インストール
python -m pip install -e .

# 使用例
python -m kumihan_formatter convert input.txt
```

## 最初の文書作成

### 1. テキストファイルを作成

`my-scenario.txt`:
```
# 見出し1 #
シナリオタイトル
##

このシナリオは...

# 太字 #
重要な情報
##

# ハイライト color=yellow #
注目すべきポイント
##

# 目次 #
##
```

### 2. 変換実行

**GUI版**: ファイルをドラッグ&ドロップ

**CLI版**:
```bash
kumihan convert my-scenario.txt -o output/
```

### 3. 結果確認

`output/my-scenario.html`が生成されます。ブラウザで開いて確認してください。

## 基本的な記法

### 文字の装飾
```
# 太字 #
重要なテキスト
##

# イタリック #
英単語など
##
```

### 見出しと構造
```
# 見出し1 #
章タイトル
##

# 見出し2 #
節タイトル
##
```

### 重要な情報
```
# 枠線 #
重要な注意事項
##

# ハイライト #
強調したいポイント
##
```

## 次のステップ

- [記法リファレンス](notation-reference.md) - 全記法の詳細
- [ユーザーガイド](user-guide.md) - 詳細な使い方
- [FAQ](faq.md) - よくある質問と解決方法

## サポート

- **バグ報告**: [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **使い方相談**: [Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)