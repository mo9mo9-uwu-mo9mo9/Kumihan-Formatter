# サンプルファイル

Kumihan-Formatterの使い方を学ぶためのサンプルファイル集です。

## ディレクトリ構成

```
examples/
├── 01-quickstart.txt         # 初心者向けサンプル
├── 02-basic.txt             # 基本機能サンプル  
├── 03-comprehensive.txt      # 全機能網羅サンプル
├── 04-image-embedding.txt    # 画像埋め込みサンプル
├── 05-table-of-contents.txt  # 目次生成サンプル
├── config.yaml              # 設定ファイルサンプル
├── images/                  # サンプル画像フォルダ
├── templates/               # 🆕 シナリオテンプレート集
├── elements/                # 🆕 要素別テンプレート集  
├── showcase/                # 🆕 完成版サンプルシナリオ
└── README.md                # 本ファイル
```

## サンプルファイル詳細

### 01-quickstart.txt ⭐ 初心者向け
最初に試すための超シンプルなサンプルです。

- 基本的な見出し
- 太字・枠線
- ハイライト
- 複合キーワードの例

### 02-basic.txt
基本的な記法を使った標準的なサンプルです。

- 段落
- リスト
- 基本的なブロック（太字、枠線など）

### 03-comprehensive.txt
すべての機能を網羅した包括的なサンプルです。

- 複合キーワード（太字+枠線など）
- 見出し
- ハイライト
- エラーハンドリング例

### 04-image-embedding.txt
画像埋め込み機能のサンプルです。

- 画像の埋め込み方法
- 画像とテキストの組み合わせ
- レスポンシブ対応

### 05-table-of-contents.txt  
目次自動生成機能のサンプルです。

- 見出し構造の作成
- 目次の自動生成
- ナビゲーション機能

## 設定ファイル

### config.yaml
カスタマイズ可能な設定項目の例です。

- HTML出力の設定
- CSS スタイルのカスタマイズ
- マーカーの追加・変更

## 使い方

### 🎯 初心者におすすめ
```bash
# 最初に試す（超シンプル）
kumihan convert examples/01-quickstart.txt

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
kumihan convert examples/02-basic.txt

# 出力先を指定
kumihan convert examples/02-basic.txt -o my_output/

# 設定ファイルを使用
kumihan convert examples/03-comprehensive.txt --config examples/config.yaml
```

## 学習の順序

1. **01-quickstart.txt** ⭐ - 最初の一歩（5分）
2. **02-basic.txt** - 基本機能を理解（10分）  
3. **03-comprehensive.txt** - 全機能を体験（15分）
4. **04-image-embedding.txt** - 画像機能を学習（10分）
5. **05-table-of-contents.txt** - 目次機能を学習（10分）
6. **config.yaml** - カスタマイズ方法を学習（上級者向け）

## 自分のファイルを作成する際のヒント

1. **段落**: 空行で区切る
2. **リスト**: `- ` で開始
3. **キーワード付きリスト**: `- ;;;キーワード;;; 内容`
4. **ブロック**: `;;;キーワード\n内容\n;;;` で囲む
5. **複合キーワード**: `;;;太字+枠線\n内容\n;;;` のように`+`で結合

詳細な記法については、`docs/user/USER_MANUAL.txt` を参照してください。

## 🆕 CoC6thシナリオ作成支援

### 📋 テンプレート集 (templates/)
コピー&ペーストで使える実用的なシナリオテンプレート
- **basic-scenario.txt** - 初心者向け汎用テンプレート
- **closed-scenario.txt** - クローズド型シナリオ
- **city-scenario.txt** - シティアドベンチャー型
- **combat-scenario.txt** - 戦闘重視型

### 🧩 要素別テンプレート (elements/)
シナリオ作成に必要な個別要素のテンプレート
- **npc-template.txt** - NPC作成ガイド
- **item-template.txt** - アイテム・クリーチャー設計
- **skill-template.txt** - 技能ロール・判定システム

### 🎯 完成版シナリオ (showcase/)
実際にプレイできる完全なサンプルシナリオ
- **complete-scenario.txt** - 「深夜図書館の怪」（3-4時間・初心者向け）

### 活用方法
```bash
# テンプレートをHTMLに変換
kumihan convert examples/templates/basic-scenario.txt

# 完成版シナリオを確認
kumihan convert examples/showcase/complete-scenario.txt

# 要素別テンプレートを参照
kumihan convert examples/elements/npc-template.txt
```