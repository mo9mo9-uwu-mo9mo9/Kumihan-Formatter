# Kumihan-Formatter CLIリファレンス

## 基本構文

```bash
kumihan [オプション] [入力ファイル]
```

または

```bash
python -m kumihan_formatter [オプション] [入力ファイル]
```

## コマンド一覧

Kumihan-Formatterは以下の2つのメインコマンドを提供します：

### convert - テキストファイル変換

```bash
# 基本構文
kumihan convert [オプション] [入力ファイル]
# または
python -m kumihan_formatter convert [オプション] [入力ファイル]
```

```bash
# デフォルト出力（distフォルダ）
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

### ソーストグル機能（NEW）

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

### ダブルクリック実行モード

```bash
# ユーザーフレンドリーな表示形式
kumihan convert --generate-test --double-click-mode
kumihan convert input.txt --double-click-mode
```

## convert コマンドオプション詳細

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
| `--double-click-mode` | - | ダブルクリック実行モード | False |
| `--help` | `-h` | ヘルプを表示 | - |

## docs コマンドオプション詳細

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--output` | `-o` | 出力ディレクトリ | `docs_html` |
| `--docs-dir` | - | ドキュメントディレクトリ | `docs` |
| `--no-preview` | - | HTML生成後にブラウザを開かない | False |
| `--help` | `-h` | ヘルプを表示 | - |

## 使用例

### 1. シンプルな変換

```bash
# sample.txtをHTMLに変換
kumihan convert sample.txt
# → dist/sample.html が生成される
```

### 2. ソーストグル機能の活用

```bash
# 記法学習用：記法と結果を並べて表示
kumihan convert tutorial.txt --with-source-toggle

# 実験的機能：スクロール同期で記法学習を強化
kumihan convert tutorial.txt --with-source-toggle --experimental scroll-sync
```

### 3. ドキュメント変換

```bash
# プロジェクトドキュメントをHTMLに変換
kumihan docs

# 出力先を指定してプレビューなし
kumihan docs -o public/docs --no-preview
```

### 4. 複数ファイルの一括変換

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

### 5. 開発時の自動更新

```bash
# エディタで編集しながら結果をリアルタイムで確認
kumihan convert draft.txt --watch

# ソーストグル機能付きで自動更新
kumihan convert draft.txt --watch --with-source-toggle
```

### 6. CI/CDでの使用

```bash
# エラー時に非ゼロ終了コードを返す
kumihan convert input.txt --no-preview || exit 1

# ドキュメント自動生成
kumihan docs --no-preview
```

### 7. カスタムテーマ適用

```yaml
# theme.yaml
theme:
  name: "カスタムテーマ"
  colors:
    background: "#f0f0f0"
    text: "#333333"
```

```bash
kumihan convert input.txt --config theme.yaml
```

## 環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `KUMIHAN_OUTPUT` | デフォルト出力ディレクトリ | `export KUMIHAN_OUTPUT=~/Documents/html` |
| `KUMIHAN_CONFIG` | デフォルト設定ファイル | `export KUMIHAN_CONFIG=~/.kumihan.yaml` |

## 終了コード

| コード | 説明 |
|--------|------|
| 0 | 正常終了 |
| 1 | 一般的なエラー |
| 2 | ファイルが見つからない |
| 3 | 構文エラー |
| 4 | 設定エラー |

## エラーメッセージ

### ファイルエラー
```
エラー: 入力ファイルが見つかりません: example.txt
```

### 構文エラー
```
警告: 1個のエラーが検出されました
HTMLファイルでエラー箇所を確認してください
```

### 設定エラー
```
エラー: 設定ファイルの読み込みに失敗しました: config.yaml
```

## ヒントとコツ

### パフォーマンス最適化
- 大きなファイルの場合は `--no-preview` オプションを使用
- 監視モードでは必要なファイルのみを対象に

### エラーのデバッグ
- 生成されたHTMLで赤い背景の箇所を確認
- `[ERROR:]` で始まるメッセージに注目

### バッチ処理
- シェルスクリプトやバッチファイルで自動化
- CI/CDパイプラインに組み込み可能