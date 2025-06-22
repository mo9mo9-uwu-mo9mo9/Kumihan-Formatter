# サンプルファイル

Kumihan-Formatterの使い方を学ぶためのサンプルファイル集です。

## ディレクトリ構成

```
examples/
├── input/          # 入力サンプル（.txt）
├── output/         # 出力サンプル（.html）
├── config/         # 設定ファイルサンプル（.yaml）
└── README.md       # 本ファイル
```

## 入力サンプル (input/)

### quickstart.txt ⭐ 初心者向け
最初に試すための超シンプルなサンプルです。

- 基本的な見出し
- 太字・枠線
- ハイライト
- 複合キーワードの例

### sample.txt
基本的な記法を使った標準的なサンプルです。

- 段落
- リスト
- 基本的なブロック（太字、枠線など）

### comprehensive-sample.txt
すべての機能を網羅した包括的なサンプルです。

- 複合キーワード（太字+枠線など）
- 見出し
- ハイライト
- 画像埋め込み
- 目次自動生成

## 出力サンプル (output/)

### kumihan_sample/
機能ショーケース用の出力結果です。

- `showcase.html` - 完成したHTMLファイル
- `showcase.txt` - 元となる入力ファイル
- `images/` - 埋め込まれた画像ファイル

## 設定ファイルサンプル (config/)

### config-sample.yaml
カスタマイズ可能な設定項目の例です。

- HTML出力の設定
- CSS スタイルのカスタマイズ
- マーカーの追加・変更

## 使い方

### 🎯 初心者におすすめ
```bash
# 最初に試す（超シンプル）
kumihan examples/input/quickstart.txt

# 一括でサンプル実行（Windows）
run_examples.bat

# 一括でサンプル実行（macOS）
./run_examples.command
```

### 🖱️ マウスで使いたい方
```bash
# Windows: ダブルクリック
kumihan_convert.bat

# macOS: ダブルクリック
kumihan_convert.command
```

### ⌨️ コマンドで詳細制御
```bash
# 基本的な変換
kumihan examples/input/sample.txt

# 出力先を指定
kumihan examples/input/sample.txt -o my_output/

# 設定ファイルを使用
kumihan examples/input/comprehensive-sample.txt --config examples/config/config-sample.yaml
```

## 学習の順序

1. **quickstart.txt** ⭐ - 最初の一歩（5分）
2. **sample.txt** - 基本機能を理解（10分）
3. **comprehensive-sample.txt** - 全機能を体験（15分）
4. **config-sample.yaml** - カスタマイズ方法を学習（上級者向け）

## 自分のファイルを作成する際のヒント

1. **段落**: 空行で区切る
2. **リスト**: `- ` で開始
3. **キーワード付きリスト**: `- :キーワード: 内容`
4. **ブロック**: `:::キーワード` で囲む
5. **複合キーワード**: `:::太字+枠線` のように`+`で結合

詳細な記法については、`docs/user/USER_MANUAL.txt` を参照してください。