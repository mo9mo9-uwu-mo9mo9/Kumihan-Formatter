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

### 基本的な変換

```bash
# デフォルト出力（distフォルダ）
kumihan input.txt

# 出力先を指定
kumihan input.txt -o output_folder/

# ブラウザプレビューなし
kumihan input.txt --no-preview
```

### ファイル監視モード

```bash
# ファイルの変更を監視して自動再生成
kumihan input.txt --watch

# 監視モード + プレビューなし
kumihan input.txt --watch --no-preview
```

### サンプル生成

```bash
# 機能ショーケースを生成
kumihan --generate-sample

# カスタムディレクトリに生成
kumihan --generate-sample --sample-output my_sample
```

### テストパターン生成

```bash
# デフォルト設定でテストパターン生成
kumihan --generate-test

# 詳細なオプション指定
kumihan --generate-test --test-output test.txt --pattern-count 200
```

### 設定ファイル使用

```bash
# YAML設定ファイルを使用
kumihan input.txt --config config.yaml

# JSON設定ファイルを使用
kumihan input.txt --config config.json
```

## オプション詳細

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--output` | `-o` | 出力ディレクトリ | `dist` |
| `--no-preview` | - | HTML生成後にブラウザを開かない | False |
| `--watch` | `-w` | ファイル変更を監視 | False |
| `--config` | `-c` | 設定ファイルのパス | なし |
| `--generate-sample` | - | サンプルファイルを生成 | False |
| `--sample-output` | - | サンプルの出力先 | `kumihan_sample` |
| `--generate-test` | - | テストパターンを生成 | False |
| `--test-output` | - | テストファイル名 | `test_patterns.txt` |
| `--pattern-count` | - | テストパターン数 | 100 |
| `--double-click-mode` | - | ダブルクリック実行モード | False |
| `--help` | `-h` | ヘルプを表示 | - |
| `--version` | - | バージョンを表示 | - |

## 使用例

### 1. シンプルな変換

```bash
# sample.txtをHTMLに変換
kumihan sample.txt
# → dist/sample.html が生成される
```

### 2. 複数ファイルの一括変換

```bash
# Bashの場合
for file in *.txt; do
    kumihan "$file" -o "output/${file%.txt}"
done

# PowerShellの場合
Get-ChildItem -Filter *.txt | ForEach-Object {
    kumihan $_.Name -o "output/$($_.BaseName)"
}
```

### 3. 開発時の自動更新

```bash
# エディタで編集しながら結果をリアルタイムで確認
kumihan draft.txt --watch
```

### 4. CI/CDでの使用

```bash
# エラー時に非ゼロ終了コードを返す
kumihan input.txt --no-preview || exit 1
```

### 5. カスタムテーマ適用

```yaml
# theme.yaml
theme:
  name: "カスタムテーマ"
  colors:
    background: "#f0f0f0"
    text: "#333333"
```

```bash
kumihan input.txt --config theme.yaml
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