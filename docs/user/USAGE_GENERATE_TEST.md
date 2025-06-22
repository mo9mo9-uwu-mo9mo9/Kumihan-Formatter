# テスト用記法網羅ファイル生成機能

## 概要

Kumihan-Formatterの全記法パターンを網羅したテストファイルを自動生成する機能です。開発者が回帰テストや新機能検証に活用できます。

## 簡単実行（コマンド）

テストパターンファイルを生成する最も簡単な方法：

```bash
python -m kumihan_formatter --generate-test
```

このコマンドは自動的に：
1. 全記法パターンを網羅したテストファイルを生成
2. HTMLに変換してブラウザで表示
3. 出力フォルダを自動で開く

## 基本的な使用方法

### テストファイルの生成

```bash
# 基本的な生成
python -m kumihan_formatter --generate-test

# 出力ファイル名を指定
python -m kumihan_formatter --generate-test --test-output my_test.txt

# パターン数を制限
python -m kumihan_formatter --generate-test --pattern-count 50

# 生成後にHTMLに変換してブラウザで確認
python -m kumihan_formatter --generate-test --output dist
```

### 生成されるパターン

1. **単一ブロック記法**
   - 全キーワード（見出し1-5、太字、イタリック、枠線、ハイライト）
   - ハイライトの色指定パターン

2. **複合ブロック記法**
   - 2つの組み合わせ（例：見出し2+太字）
   - 3つの組み合わせ（例：見出し2+枠線+太字）
   - 4つ以上の組み合わせ（最大複合パターン）

3. **キーワード付きリスト**
   - 単一キーワード付きリスト
   - 複合キーワード付きリスト
   - 色指定付きリスト

4. **混在パターン**
   - 通常段落とブロック記法の混在
   - リストとブロックの混在
   - エラーケース（意図的な無効パターン）

5. **パフォーマンステスト**
   - 大量リスト項目
   - 長いコンテンツのブロック

## 出力例

```
# ============================================
# 複合ブロック記法（3つ）: 見出し2+太字+枠線
# ============================================
;;;見出し2+太字+枠線
見出し2、太字、枠線の組み合わせです。
複雑なネスト構造のテストケースです。
;;;

# ============================================
# キーワード付きリスト（複合キーワード）
# ============================================
- :太字+枠線: 太字+枠線を適用したリスト項目です
- :見出し3+イタリック: 見出し3+イタリックを適用したリスト項目です
- 通常のリスト項目
```

## 出力先

生成されたファイルは以下の場所に保存されます：

```
dev/test-output/2025-06-21_12-34-56/
├── test_patterns.txt   # 生成されたテストファイル
└── test_patterns.html  # HTML変換結果
```

フォルダ名はタイムスタンプ付きで、複数回実行しても過去の結果が保持されます。

## オプション詳細

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--generate-test` | テストファイル生成モードを有効化 | - |
| `--test-output` | 出力ファイル名 | `test_patterns.txt` |
| `--pattern-count` | 生成するパターン数の上限 | 100 |
| `--output` | HTML変換時の出力ディレクトリ | `dist` |
| `--no-preview` | HTML生成後のブラウザ自動起動を無効化 | - |

## 検証機能

生成されたテストファイルは自動的に以下の検証が行われます：

1. **パース検証**: 生成ファイルが正常にパースできるか
2. **HTML変換検証**: HTMLへの変換が正常に完了するか
3. **統計情報表示**: 生成パターン数、ブロック数等の統計

## 活用例

### 回帰テストでの使用

```bash
# テストファイル生成
python -m kumihan_formatter --generate-test --test-output regression_test.txt

# HTML変換してエラーチェック
python -m kumihan_formatter regression_test.txt --output test_results

# 結果をブラウザで確認
# エラーブロック（赤背景）がないことを目視確認
```

### 新機能開発時の検証

```bash
# 全パターン網羅ファイル生成
python -m kumihan_formatter --generate-test --pattern-count 200 --test-output comprehensive.txt

# 新機能適用後の変換テスト（設定ファイル使用例）
python -m kumihan_formatter comprehensive.txt --config new_feature_config.yaml
```

### パフォーマンステスト

```bash
# 大量パターン生成
python -m kumihan_formatter --generate-test --pattern-count 500 --test-output performance_test.txt

# 変換時間測定
time python -m kumihan_formatter performance_test.txt
```

## 注意事項

- 生成されるファイルサイズは `--pattern-count` の値に比例します
- エラーケースも意図的に含まれるため、HTMLでエラー表示（赤背景）が出ることは正常です
- 大きな `--pattern-count` 値では生成に時間がかかる場合があります

## トラブルシューティング

### 生成ファイルが大きすぎる場合
```bash
# パターン数を制限
python -m kumihan_formatter --generate-test --pattern-count 30
```

### 特定パターンのみテストしたい場合
生成されたファイルを手動編集して不要部分を削除してください。

### HTML変換でエラーが多発する場合
- パーサーの実装に問題がある可能性があります
- エラーメッセージを確認して対象箇所を修正してください