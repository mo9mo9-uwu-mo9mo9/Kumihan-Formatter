# Kumihan-Formatter ユーザーガイド（統合版）

> **開発中 (α-dev)** - CoC6th TRPGシナリオ作成に特化したテキスト→HTML変換ツール
> **重要**: α-devから全記法がブロック形式に統一されました

## 📚 目次

1. [はじめに](#-はじめに)
2. [インストールとセットアップ](#-インストールとセットアップ)
3. [クイックスタート](#-クイックスタート)
4. [基本的な使い方](#-基本的な使い方)
5. [Kumihan記法完全リファレンス](#-kumihan記法完全リファレンス)
6. [コマンドラインリファレンス](#-コマンドラインリファレンス)
7. [設定とカスタマイズ](#-設定とカスタマイズ)
8. [実践ガイド](#-実践ガイド)
9. [よくある質問（FAQ）](#-よくある質問faq)
10. [トラブルシューティング](#-トラブルシューティング)
11. [配布と共有](#-配布と共有)

---

## 🚀 はじめに

### Kumihan-Formatterとは

Kumihan-Formatterは、**CoC6th TRPGシナリオ**の作成に特化したテキスト変換ツールです。独自の「Kumihan記法」を使用して、簡単にプロ品質のHTMLドキュメントを生成できます。

### ✨ 主な特徴

- **CoC6thシナリオに最適化** - ネタバレ隠し、NPC情報、ハンドアウトなど
- **直感的な記法** - `#太字#
内容
##` のように分かりやすい
- **プログラミング知識不要** - テキストファイルを書くだけ
- **A4印刷対応** - 同人誌やBooth配布に最適
- **多様な出力形式** - HTML、PDF（外部ツール使用）対応
- **自動目次生成** - 見出しから自動的に目次を作成

### 🎯 こんな方におすすめ

- **CoC6thシナリオ**を美しく配布したい同人作家
- **HTMLの知識なし**でも、きれいな文書を作りたい方
- **即売会やBooth**で配布可能な形式がほしい方
- **プロ品質**の文書を簡単に作成したい方

---

## 💻 インストールとセットアップ

### 前提条件

- **Python 3.12以上**がインストールされていること
- **pip**（Pythonパッケージマネージャー）が使用可能なこと

### Pythonのインストール確認

```bash
# バージョン確認
python --version
# または
python3 --version
```

Python 3.12以上が表示されれば準備完了です。

### Pythonのインストール方法

#### Windows
1. [python.org](https://www.python.org/downloads/)から最新版をダウンロード
2. インストーラーを実行
3. **"Add Python to PATH"にチェック**を入れてインストール

#### macOS
```bash
# Homebrewを使用
brew install python

# または公式インストーラーを使用
# python.orgからダウンロード
```

### インストール方法

#### 1. 基本インストール（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# インストール
pip install -e .
```

#### 2. 開発環境のインストール

開発やテストを行う場合は、追加の依存関係をインストールします：

```bash
# 仮想環境の作成（推奨）
python -m venv .venv

# 仮想環境の有効化
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 開発用依存関係を含めてインストール
pip install -e ".[dev]"
```

### インストール確認

インストールが成功したか確認：

```bash
# コマンドの確認
kumihan --help

# または
python -m kumihan_formatter --help
```

### アンインストール

```bash
pip uninstall kumihan-formatter
```

---

## ⚡ クイックスタート

### 🎯 超簡単2ステップで始める

#### ステップ1: アプリを起動

**GUI版（推奨）**:
1. [リリースページ](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases)からダウンロード
2. **Windows**: `Kumihan-Formatter.exe` をダブルクリック
3. **macOS**: `Kumihan-Formatter.app` をダブルクリック

**開発者向け**:
- **Windows**: `scripts/setup/Windows用初回セットアップ.bat` をダブルクリック
- **macOS**: `scripts/setup/macOS用初回セットアップ.command` をダブルクリック

✅ **成功の確認:**
- `[OK] Dependencies installed successfully` が表示される
- `Setup Complete!` のメッセージが表示される

#### ステップ2: すぐに使える！

**GUI版を使う場合:**
1. アプリを起動
2. 「参照」ボタンから.txtファイルを選択
3. 「変換実行」ボタンをクリック

**開発者向けコマンドライン:**
```bash
python -m kumihan_formatter convert input.txt -o output/
```

### 🎨 基本的な記法（コピペして試そう！）

以下をメモ帳に貼り付けて `test.txt` として保存し、変換してみてください：

```text
#見出し1#
私の最初のシナリオ
##

これは普通の段落です。
空行で段落を区切ります。

#太字#
重要な情報はこのように強調できます
##

#枠線#
シーン情報や重要な部分を枠で囲めます：
- 場所：古い図書館
- 時間：深夜
- 参加者：3-4人
##

#見出し2#
第1章：始まり
##

物語がここから始まります...

#ハイライト color=#ffffcc#
黄色のハイライトで注意を引くことができます
##

#太字+枠線#
複数のスタイルを組み合わせることも可能です
##
```

---

## 📖 基本的な使い方

### 起動方法の選択

どのファイルを使うか迷ったときは：

| ファイル名 | 用途 | 使用頻度 | 実行順序 |
|----------|------|---------|----------|
| `setup.bat`/`setup.command` | **初回セットアップ** | ⭐⭐⭐ | **1番目** |
| `kumihan_convert.bat`/`kumihan_convert.command` | **メイン変換ツール** | ⭐⭐⭐ | 2番目 |
| `run_examples.bat`/`run_examples.command` | **サンプル実行** | ⭐⭐ | 3番目 |

### 🔰 初心者の方（推奨フロー）
1. **最初に** `setup` でセットアップ
2. `run_examples` で機能を体験
3. 慣れたら `kumihan_convert` で自分のファイルを変換

### 🏃‍♂️ すぐに使いたい方
1. **最初に** `setup` でセットアップ
2. `kumihan_convert` を直接使用

### バッチファイル・コマンドファイルの使い方

#### ドラッグ&ドロップ機能

1. バッチファイルをダブルクリックで起動
2. コマンドプロンプト/ターミナル画面が表示
3. エクスプローラー/Finderから`.txt`ファイルを画面にドラッグ
4. ファイルをドロップ（マウスボタンを離す）
5. 自動で変換開始

### テキストエディタの選択

**Windows**:
- メモ帳（標準）
- Notepad++（無料・高機能）
- Visual Studio Code（無料・多機能）

**macOS**:
- テキストエディット（標準）
- CotEditor（無料・日本語対応）
- Visual Studio Code（無料・多機能）

**保存時の注意**:
- 文字コード: **UTF-8** を選択
- ファイル拡張子: **.txt**

---

## 📝 Kumihan記法完全リファレンス

> **詳細な仕様については**: [記法仕様詳細](../specs/notation.md)を参照してください

### 📌 基本記法（必須習得）

**🚨 重要なルール（α-dev）**:
- **ブロック記法必須**: 全記法がブロック形式に統一、単一行記法は完全廃止
- **混在禁止**: 半角`#`と全角`＃`を同じブロック内で混在させることは禁止
  - ✅ `#太字#
内容
##` または `＃太字＃
内容
＃＃`
  - ❌ `#太字＃
内容
##` (半角・全角混在)
- **color属性**: 英単語色名（red/Red/RED）3形式対応、混在は禁止
  - ✅ `#ハイライト color=red#
内容
##` または `#ハイライト color=RED#
内容
##`
  - ❌ `#ハイライト color=rEd#
内容
##` (大文字小文字混在)

#### 1. 見出し

**Kumihan記法:**
```
#見出し1#
第1章 古館の調査
##

#見出し2#
1.1 館の外観
##

#見出し3#
1.1.1 正面玄関
##

#見出し4#
詳細な描写
##

#見出し5#
補足情報
##
```

**表示結果:**
- **見出し1**: 章・大項目
- **見出し2**: 節・中項目  
- **見出し3**: 項・小項目
- **見出し4-5**: 補足・詳細

#### 2. 太字（強調）

**Kumihan記法:**
```
#太字#
重要：この部屋には入らないでください
##
```

**表示結果:** **重要：この部屋には入らないでください**

**使い方のコツ:**
- **注意事項**の強調
- **重要なヒント**の明示
- **危険情報**の警告

#### 3. 枠線

**Kumihan記法:**
```
#枠線#
NPCの基本情報：
- 名前：田中一郎
- 年齢：42歳
- 職業：私立探偵
- 特徴：鋭い観察眼
##
```

**使い方のコツ:**
- **情報のまとめ**
- **重要なデータ**の区別
- **参考資料**の明示

### 📋 リスト系記法

#### 4. 箇条書きリスト（ハイフン）

**Kumihan記法:**
```
調査可能な場所：
- 書斎の本棚
- 暖炉の周辺
- 窓際のテーブル
- 床に落ちている紙切れ
```

#### 5. 箇条書きリスト（中黒）

**Kumihan記法:**
```
持参すべきアイテム：
・懐中電灯
・ロープ（10m以上）
・救急キット
・予備の電池
```

#### 6. 番号付きリスト

**Kumihan記法:**
```
探索の手順：
1. まず外観を観察する
2. 正面玄関から侵入を試みる
3. 1階から順番に調査する
4. 気になる箇所は詳細に調べる
5. 証拠品は写真を撮る
```

#### 7. キーワード付きリスト

**Kumihan記法:**
```
重要なNPC：
- #太字# 田中探偵：事件の鍵を握る人物
- #太字+ハイライト color=#ffe6e6# 山田容疑者：要注意人物
・#太字# 佐藤証人：重要な目撃情報を持つ
・#ハイライト color=#e6ffe6# 鈴木警官：協力的な味方
```

### 🎨 装飾系記法

#### 8. ハイライト（背景色）

**Kumihan記法:**
```
#ハイライト#
SANチェック：1d6/1d20の正気度減少
##

#ハイライト color=#ffe6e6#
危険！この扉を開けるとトラップが発動します
##

#ハイライト color=#e6ffe6#
安全：ここで休憩を取ることができます
##

#ハイライト color=#fff3cd#
ヒント：鍵は本棚の後ろにあります
##

#ハイライト color=#e1f5fe#
情報：この部屋で重要な手がかりが見つかります
##
```

**推奨カラーパレット:**
- **赤系** (`#ffe6e6`): 危険・警告
- **緑系** (`#e6ffe6`): 安全・成功
- **黄系** (`#fff3cd`): 注意・ヒント
- **青系** (`#e1f5fe`): 情報・補足
- **紫系** (`#f3e5f5`): 特別・神秘

#### 9. イタリック（斜体）

**Kumihan記法:**
```
#イタリック#
古文書からの引用：「月が満ちる夜、死者は甦らん...」
##
```

**使い方のコツ:**
- **引用文**の表現
- **心の声**や**独白**
- **雰囲気のある文章**

### 🔧 特殊記法

#### 10. 折りたたみ

**Kumihan記法:**
```
#折りたたみ#
NPC詳細設定：
本名：田中一郎（45歳）
経歴：元警察官、10年前に退職後私立探偵として活動
性格：慎重で正義感が強い。やや頑固な面もある
重要な情報：事件の真相を知っているが、探索者を試そうとしている
##
```

**使い方のコツ:**
- **詳細情報**の格納
- **ページを見やすく**保つ
- **追加設定**の整理

#### 11. ネタバレ防止

**Kumihan記法:**
```
#ネタバレ#
真犯人は執事の山田でした。
動機は相続問題で、被害者が遺言を変更しようとしていたため。
証拠は書斎の金庫に隠されている血痕付きの手袋。
##
```

**使い方のコツ:**
- **重要な真相**の隠蔽
- **GM専用情報**の管理
- **段階的な情報開示**

#### 12. 画像の埋め込み

**Kumihan記法:**
```
#画像#
mansion_exterior.jpg
##

#画像#
bloody_letter.png
##

#画像#
dungeon_map.gif
##
```

**ファイル配置:**
```
プロジェクト/
├── scenario.txt
├── images/
│   ├── mansion_exterior.jpg
│   ├── bloody_letter.png
│   └── dungeon_map.gif
└── dist/
    └── scenario.html
```

**推奨事項:**

- **ファイル名**は英数字のみ推奨
- **画像サイズ**は1MB以下が理想

### 🎯 複合記法（上級者向け）

#### 13. 複数スタイルの組み合わせ

**Kumihan記法:**
```
#太字+枠線#
最重要手がかり：被害者の日記
##

#見出し2+太字#
第2章：事件の真相
##

#枠線+ハイライト color=#fff3cd#
ヒント：暖炉の煉瓦の3段目を押すと隠し扉が開きます
##

#太字+イタリック#
「真実は必ず明らかになる」- 探偶の信念
##

#見出し3+ハイライト color=#e1f5fe#
1.2 重要な証拠品
##
```

**組み合わせルール:**
- **連結記号**: `+` または `＋`
- **順序**: 気にしなくてOK（自動で最適化）
- **色指定**: 最後に記述（`color=#色コード`）

### 📑 段落と改行

#### 14. 段落の区切り

**Kumihan記法:**
```
これは最初の段落です。
同じ段落内では文章が続けて表示されます。改行は<br>タグになります。

空行を入れることで新しい段落が始まります。
段落間には適度な余白が入り、読みやすくなります。

3つ目の段落も同様です。
```

#### 15. 段落内の改行

**Kumihan記法:**
```
連絡先：
田中探偵事務所
〒123-4567 東京都○○区△△1-2-3
TEL: 03-1234-5678
```

### 💡 実用テンプレート集

#### NPCテンプレート

```
#見出し3+太字
田中一郎（私立探偵）
# 
枠線
基本情報：
- 年齢：42歳
- 職業：私立探偵（元警察官）
- 外見：中肉中背、鋭い目つき、いつもコートを着用
- 性格：慎重で正義感強い、やや頑固
#

# 太字
探索者との関係
#
依頼人。妻の失踪事件について調査を依頼してくる。

# ハイライト color=#fff3cd
重要な情報
#
妻は失踪前夜、「誰かに見られている気がする」と不安を漏らしていた。

# ネタバレ
GMのみ（真相）
#
実は妻は邪教団に目を付けられており、儀式の生贄として狙われている。
田中は薄々感づいているが、確証がないため探索者に依頼した。
```

#### アイテムテンプレート

```
# 見出し4+太字
古い日記
#

# 枠線
アイテム詳細：
- 発見場所：書斎の机の引き出し
- 外見：革製の表紙、ページの一部が破れている
- 重要度：★★★★☆
- 持ち運び：可能（文庫本サイズ）
#

# ハイライト color=#e1f5fe
記載内容（抜粋）
#
「6月15日：また例の夢を見た。暗い森の中で何かが私を呼んでいる...」
「6月20日：町の古老が話していた伝説が気になる。満月の夜に...」

# ネタバレ
解読成功時の追加情報
#
日記の最後のページに血文字で「助けて」と書かれている。
筆跡鑑定により、被害者の筆跡と一致することが判明する。
```

#### 場所テンプレート

```
# 見出し2
廃洋館・1階ホール
#

# 枠線+ハイライト color=#f0f8ff
第一印象：
天井の高い広々としたホール。大理石の床は埃に覆われ、
巨大なシャンデリアが不気味に揺れている。
壁には古い肖像画が並び、どれも目が探索者を追うように見える。
#

# 枠線
部屋の詳細：
- 広さ：約40平米（10m × 4m）
- 天井高：約5m
- 照明：シャンデリア（一部電球切れ）
- 出入口：正面玄関、書斎、食堂、2階への階段
- 調査難易度：目星50%
#

調査可能なポイント：
1. 暖炉とその周辺
2. 階段の手すりと足跡
3. 肖像画の並び
4. 床の埃の状況

# 折りたたみ
調査成功時の詳細
#
**暖炉周辺（目星成功）:**
暖炉の前に血痕らしき茶色いシミが点在している。
灰の中から燃え残った紙片を発見（古い手紙の断片）。

**階段（目星困難）:**
手すりに新しい指紋らしき跡。最近誰かが通った形跡。
3段目の板が少し浮いている（隠し物の可能性）。

**肖像画（知識80%）:**
描かれている人物はこの館の初代当主。
しかし肖像画の配置に不自然な点がある（後から移動された？）。
```

### ⚠️ よくある間違いとNG例

#### ❌ 間違った記法

```text
# Markdownの見出し（使用不可）
見出し
=======

**Markdownの太字**（使用不可）

*Markdownのイタリック*（使用不可）

# 太字
内容
# ← 閉じマーカー # がない（エラー）

# 太文字
内容
#
# ← 正しくは「太字」

# ハイライト+太字 color=#ff0000
内容
#
# ← color指定の位置が間違い
```

#### ✅ 正しい記法

```text
# 見出し1
見出し
#

# 太字
太字
#

# イタリック
イタリック
#

# 太字
内容
#

# 太字+ハイライト color=#ff0000
内容
#
```

### 改行処理について

**基本ルール:**

| 入力 | 出力 | 説明 |
|------|------|------|
| 1行のテキスト | そのまま1行 | **直感的** |
| 改行 | `<br>`タグ | **期待通り** |
| 空行 | 段落区切り (`<p>`) | **自然** |

**注意点:**
- 行頭の特殊文字（`#`、`-`、数字+`.`）は特別な処理がされます
- 完全に空の行を使って段落を区切ってください
- エディタの改行設定はLF改行、UTF-8にしてください

---

## ⌨️ コマンドラインリファレンス

> **詳細な機能仕様については**: [機能仕様](../specs/functional.md)を参照してください

### 基本構文

```bash
kumihan convert [オプション] [入力ファイル]
kumihan docs [オプション]
```

または

```bash
python -m kumihan_formatter convert [オプション] [入力ファイル]
python -m kumihan_formatter docs [オプション]
```

### convert - テキストファイル変換

```bash
# 基本構文
kumihan convert [オプション] [入力ファイル]

# 基本的な変換
kumihan convert input.txt

# 出力先を指定
kumihan convert input.txt -o output_folder/

# ブラウザプレビューなし
kumihan convert input.txt --no-preview
```

### docs - ドキュメント変換

```bash
# ドキュメントをHTMLに変換
kumihan docs

# カスタム設定
kumihan docs -o docs_html --docs-dir my_docs --no-preview
```

### ファイル監視モード

```bash
# ファイルの変更を監視して自動再生成
kumihan convert input.txt --watch

# 監視モード + プレビューなし
kumihan convert input.txt --watch --no-preview
```

### サンプル生成

```bash
# 機能ショーケースを生成
kumihan convert --generate-sample

# カスタムディレクトリに生成
kumihan convert --generate-sample --sample-output my_sample

# ソーストグル機能付きで生成
kumihan convert --generate-sample --with-source-toggle
```

### ソーストグル機能

```bash
# 記法と結果を切り替え表示できるHTMLを生成
kumihan convert input.txt --with-source-toggle

# 実験的機能：スクロール同期
kumihan convert input.txt --with-source-toggle --experimental scroll-sync
```

### テストパターン生成

```bash
# デフォルト設定でテストパターン生成
kumihan convert --generate-test

# 詳細なオプション指定
kumihan convert --generate-test --test-output test.txt --pattern-count 200

# テストケース名を表示
kumihan convert test.txt --show-test-cases
```

### 設定ファイル使用

```bash
# YAML設定ファイルを使用
kumihan convert input.txt --config config.yaml

# JSON設定ファイルを使用
kumihan convert input.txt --config config.json
```

### 環境変数サポート

プログレス関連のオプションは環境変数でも設定できます：

| 環境変数 | 対応オプション | 説明 |
|---------|----------------|------|
| `KUMIHAN_PROGRESS_LEVEL` | `--progress-level` | プログレス表示レベル |
| `KUMIHAN_NO_PROGRESS_TOOLTIP` | `--no-progress-tooltip` | ツールチップ無効化 |
| `KUMIHAN_DISABLE_CANCELLATION` | `--disable-cancellation` | キャンセル機能無効化 |
| `KUMIHAN_PROGRESS_STYLE` | `--progress-style` | プログレス表示スタイル |
| `KUMIHAN_PROGRESS_LOG` | `--progress-log` | プログレスログ出力先 |

```bash
# 環境変数での設定例
export KUMIHAN_PROGRESS_LEVEL=minimal
export KUMIHAN_PROGRESS_STYLE=spinner
kumihan convert large_file.txt
```

### convert コマンドオプション詳細

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--output` | `-o` | 出力ディレクトリ | `dist` |
| `--no-preview` | - | HTML生成後にブラウザを開かない | False |
| `--watch` | - | ファイル変更を監視 | False |
| `--config` | - | 設定ファイルのパス | なし |
| `--generate-sample` | - | サンプルファイルを生成 | False |
| `--sample-output` | - | サンプルの出力先 | `kumihan_sample` |
| `--with-source-toggle` | - | 記法と結果を切り替えるトグル機能付きで出力 | False |
| `--experimental` | - | 実験的機能を有効化 (例: scroll-sync) | なし |
| `--generate-test` | - | テストパターンを生成 | False |
| `--test-output` | - | テストファイル名 | `test_patterns.txt` |
| `--pattern-count` | - | テストパターン数 | 100 |
| `--show-test-cases` | - | テストケース名を表示（テスト用ファイル変換時） | False |
| `--progress-level` | `-p` | プログレス表示レベル (silent/minimal/detailed/verbose) | `detailed` |
| `--no-progress-tooltip` | - | プログレス表示でツールチップ情報を無効化 | False |
| `--disable-cancellation` | - | 処理のキャンセル機能を無効化 | False |
| `--progress-style` | - | プログレス表示スタイル (bar/spinner/percentage) | `bar` |
| `--progress-log` | - | プログレスログの出力先ファイル（JSONフォーマット） | なし |
| `--double-click-mode` | - | ダブルクリック実行モード | False |
| `--help` | `-h` | ヘルプを表示 | - |

### 使用例

#### 1. シンプルな変換

```bash
# sample.txtをHTMLに変換
kumihan convert sample.txt
# → dist/sample.html が生成される
```

#### 2. プログレス表示のカスタマイズ

```bash
# 詳細なプログレス表示（デフォルト）
kumihan convert large_file.txt -p detailed

# 最小限のプログレス表示
kumihan convert large_file.txt -p minimal

# 静音モード（プログレス表示なし）
kumihan convert large_file.txt -p silent

# プログレスログを保存
kumihan convert large_file.txt --progress-log progress.json

# スピナー形式でプログレス表示
kumihan convert large_file.txt --progress-style spinner
```

#### 3. ソーストグル機能の活用

```bash
# 記法学習用：記法と結果を並べて表示
kumihan convert tutorial.txt --with-source-toggle

# 実験的機能：スクロール同期で記法学習を強化
kumihan convert tutorial.txt --with-source-toggle --experimental scroll-sync
```

#### 3. 複数ファイルの一括変換

```bash
# Bashの場合
for file in *.txt; do
    kumihan convert "$file" -o "output/${file%.txt}"
done

# PowerShellの場合
Get-ChildItem -Filter *.txt | ForEach-Object {
    kumihan convert $_.Name -o "output/$($_.BaseName)"
}
```

### 環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `KUMIHAN_OUTPUT` | デフォルト出力ディレクトリ | `export KUMIHAN_OUTPUT=~/Documents/html` |
| `KUMIHAN_CONFIG` | デフォルト設定ファイル | `export KUMIHAN_CONFIG=~/.kumihan.yaml` |

### 終了コード

| コード | 説明 |
|--------|------|
| 0 | 正常終了 |
| 1 | 一般的なエラー |
| 2 | ファイルが見つからない |
| 3 | 構文エラー |
| 4 | 設定エラー |

---

## ⚙️ 設定とカスタマイズ

> **注意**: 基本的な使用では設定ファイルは不要です。特殊なカスタマイズが必要な場合のみご利用ください。

### 設定ファイルの基本

Kumihan-Formatterは、YAML/JSON形式の設定ファイルでカスタマイズ可能です。

```bash
kumihan input.txt --config my_config.yaml
```

### 設定可能な項目

#### 1. カスタムマーカー

新しいマーカー（記法）を追加できます：

```yaml
# config.yaml
markers:
  カスタム注意:
    tag: div
    classes: ["custom-warning"]
    styles:
      background-color: "#ffcc00"
      border: "2px solid #ff9900"
      padding: "10px"
```

使用例：
```
#カスタム注意
これはカスタムマーカーの例です
# 
```

#### 2. テーマのカスタマイズ

既存テーマの色やフォントを調整：

```yaml
theme:
  name: "カスタムテーマ"
  base: "default"  # default, dark, sepia から選択
  overrides:
    colors:
      background: "#f5f5f5"
      text: "#2c3e50"
      heading: "#34495e"
    fonts:
      body: "Noto Sans JP, sans-serif"
      heading: "Noto Serif JP, serif"
```

#### 3. 出力設定

HTML出力の詳細を制御：

```yaml
output:
  # タイトルタグの設定
  title_suffix: " - My Document"
  
  # メタタグの追加
  meta_tags:
    author: "Your Name"
    description: "Document description"
  
  # カスタムCSS/JSの追加
  custom_css: |
    .custom-class {
      color: blue;
    }
  custom_js: |
    console.log('Document loaded');
```

### 完全な設定例

#### YAML形式（推奨）

```yaml
# my_config.yaml
# カスタムマーカーの定義
markers:
  重要:
    tag: div
    classes: ["important-box"]
    styles:
      background-color: "#fff3cd"
      border-left: "5px solid #ffc107"
      padding: "15px"
      margin: "10px 0"
  
  メモ:
    tag: div
    classes: ["memo"]
    styles:
      background-color: "#e3f2fd"
      border: "1px dashed #2196f3"
      padding: "10px"
      font-style: "italic"

# テーマ設定
theme:
  name: "My Custom Theme"
  base: "default"
  overrides:
    colors:
      background: "#fafafa"
      text: "#333333"
      link: "#0066cc"
      heading: "#222222"

# 出力設定
output:
  title_suffix: " | My Project"
  meta_tags:
    author: "Your Name"
    keywords: "CoC, シナリオ, TRPG"
```

#### JSON形式

```json
{
  "markers": {
    "重要": {
      "tag": "div",
      "classes": ["important-box"],
      "styles": {
        "background-color": "#fff3cd",
        "border-left": "5px solid #ffc107",
        "padding": "15px",
        "margin": "10px 0"
      }
    }
  },
  "theme": {
    "name": "My Custom Theme",
    "base": "default",
    "overrides": {
      "colors": {
        "background": "#fafafa",
        "text": "#333333"
      }
    }
  }
}
```

---

## 🎮 実践ガイド

### 📝 効率的な制作ワークフロー

#### 推奨制作スケジュール

**フェーズ1: 計画・準備**
- 文書の構成・章立てを決定
- 必要な画像・資料を整理
- ディレクトリ構造を作成
- **所要時間**: 全体の20%

**フェーズ2: 執筆・記法適用**
- Kumihan記法での本文執筆
- 画像の配置・最適化
- 段階的なHTML変換・確認
- **所要時間**: 全体の60%

**フェーズ3: 調整・配布準備**
- レイアウト調整・スタイル適用
- 動作確認・互換性テスト
- 配布パッケージ作成
- **所要時間**: 全体の20%

#### 推奨ディレクトリ構造

```
プロジェクト/
├── document.txt           ← メイン文書
├── images/                ← 画像ファイル
│   ├── thumbnail.jpg      ← サムネイル
│   └── content_*.jpg      ← コンテンツ画像
├── config.yaml            ← 設定ファイル
├── backup/                ← バックアップ
│   └── document_v*.txt    ← 過去バージョン
└── dist/                  ← 出力先
    └── document.html      ← 最終HTML
```

### 📊 文書構造の最適化

#### 見出し階層の設計

```
#見出し1
文書タイトル
# 
見出し2
第1章 - 大項目
#

# 見出し3
1.1 中項目
#

# 見出し4
詳細説明
#
```

**推奨階層深度**: 最大4レベルまで

#### 情報の重要度別記法

```
# ハイライト color=#ffe6e6
緊急・重要な情報
#

# ハイライト color=#fff3cd
注意・ヒント
#

# ハイライト color=#e6ffe6
参考・補足情報
#

# 枠線
まとめ・要点
#
```

### 🖼️ 画像の効果的な活用

#### 推奨画像仕様
- **形式**: JPEG（写真）、PNG（図表）
- **サイズ**: 幅1200px以下
- **容量**: 1ファイル500KB以下
- **命名**: 連番 + 内容説明

#### 画像記法の使い分け

```
# 画像#

# 画像#
```

### ⌨️ ショートカット的記法

#### エイリアス設定例（bashrc/zshrc）

```bash
alias kumi="python -m kumihan_formatter"
alias kumic="python -m kumihan_formatter --config config.yaml"
alias kumip="python -m kumihan_formatter --no-preview"

# 使用例
kumi document.txt          # 基本変換
kumic document.txt         # 設定適用変換
kumip document.txt         # プレビューなし変換
```

#### 繰り返し処理の自動化

```bash
#!/bin/bash
# convert_all.sh - 全文書変換スクリプト

for file in *.txt; do
    echo "Converting $file..."
    python -m kumihan_formatter "$file" --config config.yaml
done

echo "変換完了！"
```

### 📈 品質向上のチェックポイント

#### 変換前チェック
- [ ] **記法確認**: 全ての`#キーワード#`マーカーが正しく閉じられている
- [ ] **画像確認**: 全ての画像ファイルが存在する
- [ ] **リンク確認**: 内部リンクが正しく設定されている
- [ ] **文字コード**: UTF-8で保存されている

#### 変換後チェック
- [ ] **表示確認**: 意図した通りに表示されている
- [ ] **レスポンシブ**: モバイルで正常に表示される
- [ ] **パフォーマンス**: ページ読み込みが2秒以内
- [ ] **互換性**: 主要ブラウザで動作する

#### 配布前最終チェック
- [ ] **ファイルサイズ**: 合計5MB以下
- [ ] **オフライン動作**: インターネット接続なしで閲覧可能
- [ ] **エラーなし**: ブラウザコンソールにエラーが出ない
- [ ] **完全性**: 全てのコンテンツが含まれている

---

## ❓ よくある質問（FAQ）

### 💻 基本的な使い方

#### Q1: Pythonって何ですか？インストールしても大丈夫？

**A:** Pythonは世界中で使われている安全なプログラミング言語です。

- **安全性**: Google、Netflix、Instagram等の大企業も使用
- **影響範囲**: 他のソフトウェアには一切影響しません
- **必要性**: Kumihan-Formatterの動作に必要

**インストール方法**:
1. [Python公式サイト](https://www.python.org/downloads/)にアクセス
2. 「Download Python 3.x.x」をクリック
3. インストール時に **「Add Python to PATH」にチェック**

#### Q2: どんなテキストエディタを使えばいいですか？

**A:** 以下のエディタが推奨です：

**Windows**:
- メモ帳（標準）
- Notepad++（無料・高機能）
- Visual Studio Code（無料・多機能）

**macOS**:
- テキストエディット（標準）
- CotEditor（無料・日本語対応）
- Visual Studio Code（無料・多機能）

**保存時の注意**:
- 文字コード: **UTF-8** を選択
- ファイル拡張子: **.txt**

#### Q3: 変換したファイルはどこに保存されますか？

**A:** デフォルトでは **`dist/`** フォルダに保存されます。

```
あなたのプロジェクト/
├── input.txt        ← 元ファイル
└── dist/           ← 出力先
    └── input.html  ← 変換結果
```

**出力先を変更したい場合**:
```bash
kumihan input.txt -o my_output/
```

#### Q4: 複数のファイルを一度に変換できますか？

**A:** はい、複数の方法があります：

**方法1: ワイルドカード使用**
```bash
kumihan *.txt  # すべての.txtファイル
```

**方法2: ファイルを個別指定**
```bash
kumihan file1.txt file2.txt file3.txt
```

**方法3: フォルダ全体**
```bash
kumihan examples/  # フォルダ内のすべて
```

### 📝 機能・記法について

#### Q5: Markdownとの違いは何ですか？

**A:** Kumihan記法はCoC6th TRPGシナリオに特化した記法です：

| 項目 | Markdown | Kumihan記法 |
|------|----------|-------------|
| **見出し** | `# 見出し` | `#見出し1#
見出し
##` |
| **太字** | `**太字**` | `#太字#
太字
##` |
| **特徴** | 汎用的 | TRPG特化（枠線、ネタバレ等） |

#### Q6: よく使う記法のチートシートはありますか？

**A:** 基本記法TOP5：

```
#見出し1#
章タイトル
##

#太字#
重要な情報
##

#枠線#
- リスト項目1
- リスト項目2
##

#ハイライト color=#ffe6e6#
注意事項
##

#ネタバレ#
重要なネタバレ情報
##
```

#### Q7: 画像を埋め込むことはできますか？

**A:** はい、可能です：

**フォルダ構成**:
```
プロジェクト/
├── シナリオ.txt
├── images/          ← 画像専用フォルダ
│   └── map.jpg
└── dist/           ← 出力先
```

**記法例**:
```
#画像#
map.jpg
##
```

**対応形式**: JPG、PNG、GIF、WebP

#### Q8: 目次は自動生成されますか？

**A:** はい、見出しがある場合は自動生成されます。

- **自動検出**: `#見出し1#` ~ `#見出し5#` を検出
- **リンク付き**: クリックでその場所にジャンプ
- **手動挿入**: `#目次#` は使用禁止（自動のみ）

### 🎨 カスタマイズ・設定

#### Q9: HTMLのデザインを変更したいです

**A:** `config.yaml` ファイルで設定可能です：

```yaml
# config.yaml
styles:
  body_font: "游ゴシック, YuGothic, sans-serif"
  heading_color: "#2c3e50"
  background_color: "#ffffff"

custom_css: |
  .box {
    border: 2px solid #3498db;
    border-radius: 8px;
  }
```

**適用方法**:
```bash
kumihan input.txt --config config.yaml
```

#### Q10: フォントを変更したいです

**A:** config.yamlで日本語フォントを指定できます：

```yaml
styles:
  body_font: "ヒラギノ角ゴ Pro W3, Hiragino Kaku Gothic Pro, sans-serif"
  heading_font: "游明朝, YuMincho, serif"
```

**おすすめフォント**:
- **ゴシック**: 游ゴシック、ヒラギノ角ゴ、Noto Sans JP
- **明朝**: 游明朝、ヒラギノ明朝、Noto Serif JP

### 📦 配布・共有

#### Q12: 作成したHTMLファイルを配布したいです

**A:** 複数の配布方法があります：

**方法1: HTML単体配布**
- そのまま共有可能
- メール添付、クラウドストレージ

**方法2: PDF変換後配布**
```bash
# 1. HTMLを生成
kumihan シナリオ.txt

# 2. PDFに変換（要wkhtmltopdf）
wkhtmltopdf dist/シナリオ.html シナリオ.pdf
```

#### Q13: 商用利用は可能ですか？

**A:** はい、可能です：

**利用可能な用途**:
- 同人誌即売会での販売
- Boothでの商品販売
- 有料セッション資料
- 商業出版（出版社要相談）

**禁止事項**:
- Kumihan-Formatter自体の再配布・販売
- 「Kumihan-Formatter製」の表記削除

---

## 🚨 トラブルシューティング

> **エラーメッセージの詳細については**: [エラーメッセージ仕様](../specs/error-messages.md)を参照してください

### よくあるエラーと解決方法

#### 「Python が見つかりません」

**原因**: Python 3.12以上がインストールされていない

**解決方法**:
1. [Python公式サイト](https://www.python.org/downloads/)からPython 3.12以上をダウンロード
2. インストール時に「Add to PATH」をチェック
3. インストール後、バッチファイルを再実行

#### 「仮想環境の作成に失敗しました」

**原因**: 権限不足またはディスク容量不足

**解決方法**:
- **Windows**: 管理者として実行
- **macOS**: `chmod +x` でファイルに実行権限を付与
- ディスク容量を確認（最低500MB必要）

#### 「ファイルが見つかりません」

**原因**: ファイルパスに日本語や特殊文字が含まれている

**解決方法**:
- ファイル名とフォルダ名を半角英数字に変更
- スペースを含むパスは避ける
- または、プロジェクトフォルダにファイルをコピー

#### 「変換中にエラーが発生しました」

**原因**: テキストファイルの記法にエラーがある

**解決方法**:
1. 生成されたHTMLファイルを確認
2. 赤い背景の`[ERROR:]`箇所を修正
3. 記法ガイドを参照

#### pipが見つからない場合

```bash
# pipのインストール
python -m ensurepip --upgrade
```

#### 権限エラーが発生する場合

```bash
# ユーザー領域にインストール
pip install --user -e .
```

#### 依存関係の問題

```bash
# 依存関係を再インストール
pip install --upgrade -r requirements.txt
```

### 改行が期待通りにならない場合

#### 診断フロー

```
1. 空行は完全に空？
   NO → スペース・タブを削除
   ↓ YES

2. 行頭に特殊文字（#, -, 数字+.）？
   YES → 全角文字に変更
   ↓ NO

3. ブロック記法の直後？
   YES → 空行を追加
   ↓ NO

4. エディタの改行設定は適切？
   NO → LF改行、UTF-8に設定
   ↓ YES

5. まだ解決しない場合
   → Issue報告をお願いします
```

#### 特殊文字の回避

| 行頭文字 | 処理 | 回避策 |
|----------|------|--------|
| `#` | コメント（無視） | `＃`（全角）を使用 |
| `- ` | リスト | `－`（全角）または`—`を使用 |
| `1. ` | 番号付きリスト | `１.`（全角）または`1`のみ |
| `#` | ブロック記法 | `###`でエスケープ |

### パフォーマンス最適化

#### 大きなファイルの処理

- ファイルサイズ1MB以上: 処理に数分かかる場合があります
- 推奨: 章ごとに分割して処理
- メモリ不足時: 他のアプリケーションを終了

#### 高速化のコツ

- 不要な画像ファイルを削除
- 複雑な複合キーワードを減らす
- SSDでの実行を推奨

---

## 📦 配布と共有

### 配布用HTML最適化

#### 基本的な配布準備

```bash
# 配布用HTMLの作成
python -m kumihan_formatter convert document.txt -o release/

# ファイルサイズの確認
ls -lh release/*.html
```

#### 最適化チェックリスト

- [ ] HTMLファイルサイズ（1MB以下推奨）
- [ ] 画像合計サイズ（5MB以下推奨）
- [ ] モバイル表示の確認
- [ ] オフライン閲覧の確認

### Booth販売時の注意点

#### ライセンス関係

- **Kumihan-Formatter**: 改変自由、再配布禁止
- **あなたの作品**: 自由に販売・配布可能
- **使用素材**: 画像等のライセンス確認必須

#### 販売時の推奨事項

- サンプル版（無料）の提供
- 動作環境の明記（「HTMLファイル、モダンブラウザ対応」）
- 問い合わせ先の記載

#### ファイル形式

- **HTML**: そのまま販売OK
- **PDF**: 印刷用途におすすめ

### Web配布の最適化

#### SEO対応（オプション）

```yaml
# config.yaml
metadata:
  title: "文書タイトル"
  description: "文書の説明（120文字以内）"
  keywords: "キーワード1, キーワード2"
  author: "作成者名"
```

#### ソーシャル共有対応

```yaml
# config.yaml
social_media:
  og_title: "ソーシャル用タイトル"
  og_description: "ソーシャル用説明"
  og_image: "images/thumbnail.jpg"
```

### 他形式への変換

#### PDF変換

```bash
# HTMLを生成
kumihan input.txt

# PDFに変換
wkhtmltopdf dist/input.html output.pdf
```

#### EPUB変換

```bash
# Pandocを使用
pandoc dist/input.html -o output.epub
```

#### 推奨ツール

- **PDF**: wkhtmltopdf, Chrome headless
- **EPUB**: Pandoc, Calibre
- **Word**: Pandoc

---

## 🤝 サポート・コミュニティ

### バグ報告

**報告先**: [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)

**報告時に含める情報**:
- OS（Windows 10、macOS Big Sur等）
- Pythonバージョン（`python --version`）
- エラーメッセージの全文
- 問題のあるファイル（可能な範囲で）
- 期待していた動作

### 機能要望

**GitHubIssues**: 詳細な要望
**Twitter**: @username（カジュアルな提案）

**要望例**:
- 新しい記法の追加
- 出力形式の拡張
- UI/UXの改善
- ドキュメントの改善

### 関連リソース

- **[GitHubリポジトリ](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter)** - ソースコード・Issue報告
- **[リリースページ](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases)** - 最新版ダウンロード

---

## 📚 技術情報・上級者向け

### APIとしての利用

```python
from kumihan_formatter import parse, render

# テキストを読み込み
with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# パース
ast = parse(text)

# HTML生成
html = render(ast, config={
    'styles': {'body_font': 'Arial'}
})

print(html)
```

### 大容量ファイル対応

**現在の推奨**:
- 1ファイル: 10,000行以下
- 画像: 合計50MB以下
- メモリ: 1GB以下

**大容量対応策**:
```bash
# ファイル分割
kumihan chapter1.txt chapter2.txt chapter3.txt

# 軽量オプション（実装予定）
kumihan large_file.txt --streaming
```

---

## 📋 まとめ

Kumihan-Formatterを使って、あなたの**CoC6thシナリオ**を美しいHTMLドキュメントに変換しましょう。

### 🎯 このガイドで学んだこと

- ✅ **インストール**: Python環境のセットアップ
- ✅ **基本操作**: GUI/CLIでの変換方法
- ✅ **記法習得**: 豊富なKumihan記法の使い方
- ✅ **実践応用**: 効率的なワークフローと品質管理
- ✅ **配布準備**: HTML最適化と配布方法
- ✅ **問題解決**: トラブルシューティングとサポート

### 🚀 次のステップ

1. **練習**: サンプルファイルで記法を体験
2. **作成**: 実際のシナリオファイルを変換
3. **カスタマイズ**: 設定ファイルで見た目を調整
4. **配布**: 完成したHTMLを共有・販売

---

**解決できない問題がありましたら、[GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues) までお気軽にご報告ください。コミュニティ全体でサポートいたします！**

**🎉 素敵なCoC6thシナリオ作成をお楽しみください！**

---

## 🔧 開発者・貢献者向け情報

### 開発に参加したい方へ

Kumihan-Formatterは**オープンソースプロジェクト**です。バグ修正、新機能の提案・実装、ドキュメントの改善など、様々な形での貢献を歓迎しています。

#### 開発環境のセットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# 2. Python仮想環境の作成
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または .venv\Scripts\activate  # Windows

# 3. 開発用依存関係のインストール
pip install -e .[dev,test]

# 4. 品質チェックの実行
make lint  # Black + mypy
make test  # pytest実行
```

#### 貢献の方法

1. **バグ報告**: [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues) で詳細を報告
2. **機能提案**: 新しいKumihan記法や機能のアイデアを提案
3. **プルリクエスト**: コードの修正・改善を直接提出
4. **ドキュメント**: 使い方の改善や翻訳の協力

#### 詳細な開発者向けドキュメント

- **[開発環境構築](../dev/getting_started.md)** - 詳細なセットアップ手順
- **[コーディング規約](../dev/coding-standards.md)** - プロジェクトの開発ルール
- **[テストガイド](../dev/testing_guide.md)** - テスト作成・実行方法
- **[アーキテクチャ](../dev/architecture.md)** - システム設計思想
- **[API リファレンス](../api/)** - Parser/Renderer/CLI APIの詳細

### APIの利用

Kumihan-FormatterはPythonライブラリとしても利用できます。

```python
from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer

# パーサーとレンダラーの初期化
parser = Parser()
renderer = Renderer()

# Kumihanテキストの変換
kumihan_text = """
# 見出し1 #
シナリオタイトル
##

# 太字 #
重要な情報
##
"""

# パース処理
nodes = parser.parse(kumihan_text)

# HTML変換
html = renderer.render(nodes, title="マイシナリオ")

print(html)
```

詳細は[APIリファレンス](../api/)をご確認ください。

### カスタム拡張の開発

独自のKumihan記法や出力形式を追加することも可能です。

```python
# カスタムレンダラーの例
from kumihan_formatter.renderer import Renderer

class CustomRenderer(Renderer):
    def render_custom_node(self, node):
        # カスタム記法の処理
        return f"<custom>{node.content}</custom>"
```

### 国際化対応

現在は日本語に特化していますが、将来的な多言語対応への準備も進めています。翻訳にご協力いただける方は[Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)までご連絡ください。

---

**開発に参加していただき、ありがとうございます！** 
**一緒により良いツールを作りましょう！** 🚀