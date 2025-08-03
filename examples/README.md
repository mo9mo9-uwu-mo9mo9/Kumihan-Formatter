# Kumihan-Formatter サンプルファイル集

> **バージョン**: v2.2.0-alpha対応
> **作成日**: 2025-01-01
> **目的**: 包括的テスト・学習用サンプル

## 📁 ディレクトリ構成

```
samples/
├── README.md                    # このファイル
├── NOTATION_CHECKLIST.md        # 記法チェックリスト
├── basic/                       # 基本機能サンプル
│   ├── 01_basic_features.txt    # 基本記法デモ
│   ├── 02_all_notations.txt     # 全記法網羅
│   └── 03_mixed_content.txt     # 混合コンテンツ
├── performance/                 # パフォーマンステスト
│   ├── 10_large_document_10k.txt     # 1万行
│   ├── 11_complex_nested_5k.txt      # 複雑ネスト
│   └── 12_heavy_decoration_7k.txt    # 高密度装飾
├── practical/                   # 実用例サンプル
│   ├── 20_trpg_scenario.txt     # TRPGシナリオ
│   ├── 21_technical_manual.txt  # 技術マニュアル
│   ├── 22_novel_chapter.txt     # 小説章
│   └── 23_mixed_media_doc.txt   # 複合メディア文書
├── special/                     # 特殊ケーステスト
│   ├── 30_edge_cases.txt        # エッジケース
│   ├── 31_error_patterns.txt    # エラーパターン
│   └── 32_unicode_special.txt   # Unicode特殊文字
└── ultra_large/                 # 超大規模テスト
    ├── 40_ultra_large_200k.txt  # 20万行
    └── 41_ultra_large_300k.txt  # 30万行
```

## 🎯 使用目的別ガイド

### 🔰 初心者・学習用
**おすすめファイル**: `basic/` ディレクトリ

- **`01_basic_features.txt`** - Kumihan記法の基本を学ぶ
- **`02_all_notations.txt`** - 全21種類の記法を確認
- **`03_mixed_content.txt`** - 実際の使用例を参照

### 🔧 開発者・テスト用
**おすすめファイル**: `performance/` + `special/` ディレクトリ

- **`10_large_document_10k.txt`** - 標準的な大容量ファイル
- **`30_edge_cases.txt`** - 境界条件のテスト
- **`31_error_patterns.txt`** - エラーハンドリングの確認

### 📚 実用例・参考用
**おすすめファイル**: `practical/` ディレクトリ

- **`20_trpg_scenario.txt`** - ゲーム用文書の作成例
- **`21_technical_manual.txt`** - API仕様書などの技術文書
- **`22_novel_chapter.txt`** - 文学作品での記法活用
- **`23_mixed_media_doc.txt`** - ビジネス文書での総合活用

### ⚡ パフォーマンステスト用
**おすすめファイル**: `ultra_large/` ディレクトリ

- **`40_ultra_large_200k.txt`** - 20万行の大規模テスト
- **`41_ultra_large_300k.txt`** - 30万行の限界テスト

## 📋 記法カバレッジ

### ✅ 完全対応記法（21種類）

| カテゴリ | 記法キーワード | サンプルファイル |
|----------|----------------|------------------|
| **基本装飾** | 太字、イタリック、下線、取り消し線 | 全ファイル |
| **コード系** | コード、コードブロック | 全ファイル |
| **引用・枠** | 引用、枠線 | 全ファイル |
| **ハイライト** | ハイライト（30色+16進） | 全ファイル |
| **構造系** | 見出し1-5、目次、中央寄せ | 全ファイル |
| **機能系** | 折りたたみ、ネタバレ | 全ファイル |
| **情報系** | 注意、情報 | 全ファイル |

### 📊 記法使用統計

```
基本装飾記法:    100% (全ファイル)
複合記法:        85% (17/20ファイル)
色指定:          90% (18/20ファイル)
ネスト構造:      75% (15/20ファイル)
エラーパターン:  5% (1/20ファイル - 意図的)
```

## 🧪 テストケース分類

### 1. **正常系テスト**
- 基本記法の動作確認
- 複合記法の組み合わせ
- 色指定の妥当性確認
- ネスト構造の処理

### 2. **パフォーマンステスト**
- 大容量ファイル処理
- 高密度記法処理
- 複雑ネスト構造処理
- メモリ効率の確認

### 3. **エラーハンドリングテスト**
- 不正な記法構文
- 不完全なマーカー
- 無効な属性値
- エンコーディング問題

### 4. **国際化テスト**
- Unicode文字対応
- 多言語コンテンツ
- RTL（右から左）テキスト
- 特殊文字・絵文字

## ⚙️ 使用方法

### 基本的な変換テスト

```bash
# 基本機能テスト
kumihan convert samples/basic/01_basic_features.txt -o output/

# 全記法テスト
kumihan convert samples/basic/02_all_notations.txt -o output/

# パフォーマンステスト（大容量）
kumihan convert samples/performance/10_large_document_10k.txt -o output/
```

### プログラマティックテスト

```python
from kumihan_formatter import convert_file

# 複数ファイルのバッチテスト
test_files = [
    'samples/basic/01_basic_features.txt',
    'samples/practical/20_trpg_scenario.txt',
    'samples/special/30_edge_cases.txt'
]

for file_path in test_files:
    result = convert_file(file_path)
    print(f"{file_path}: {'✅ 成功' if result.success else '❌ 失敗'}")
```

### エラーテスト

```bash
# エラーパターンテスト（エラーが出力されることを確認）
kumihan convert samples/special/31_error_patterns.txt -o output/ --strict
```

## 📈 ファイルサイズと処理時間の目安

| ファイル | 行数 | サイズ | 処理時間（目安） |
|----------|------|--------|------------------|
| basic/* | ~100行 | ~5KB | <1秒 |
| performance/* | ~1-1.5万行 | ~500KB-1MB | 1-5秒 |
| practical/* | ~400-600行 | ~20-40KB | <2秒 |
| special/* | ~300-800行 | ~15-50KB | 1-3秒 |
| ultra_large/* | 20-30万行 | 10-20MB | 数分～数十分 |

## 🔍 品質保証

### テスト内容
- ✅ 全21種類の記法を網羅
- ✅ 複合記法の全組み合わせをテスト
- ✅ 30種類の色名 + 16進カラーコードを確認
- ✅ エラーパターンを意図的に含有
- ✅ Unicode特殊文字に対応
- ✅ 大規模ファイルでのパフォーマンス確認

### 品質チェック項目
- [ ] 構文の正確性
- [ ] マーカーの整合性
- [ ] 色指定の妥当性
- [ ] ネスト構造の正当性
- [ ] エンコーディングの正確性

## 📝 カスタムサンプル作成ガイド

### 新しいサンプルファイルを作成する場合

1. **適切なディレクトリを選択**
   - `basic/`: 学習・デモ用
   - `performance/`: パフォーマンステスト用
   - `practical/`: 実用例
   - `special/`: 特殊ケース・エラーテスト

2. **ファイル命名規則**
   - `{カテゴリ番号}_{説明的な名前}.txt`
   - 例: `50_custom_test.txt`

3. **必須チェック項目**
   - [ ] ファイル先頭にタイトルと目次
   - [ ] 使用する記法の明確な説明
   - [ ] 適切なエラーハンドリング（特殊ケースの場合）
   - [ ] ファイル末尾に情報セクション

## 🚨 注意事項

### ⚠️ エラーパターンファイル
**`31_error_patterns.txt`** には意図的にエラーとなる記法が含まれています。
- 実際の文書作成では参考にしないでください
- テスト目的でのみ使用してください
- エラー出力が正常な動作です

### ⚠️ 大容量ファイル
**`ultra_large/`** ディレクトリのファイルは非常に大きなサイズです。
- 処理に数分〜数十分かかる場合があります
- メモリ不足に注意してください
- テスト環境での使用を推奨します

### ⚠️ Unicode対応
**`32_unicode_special.txt`** は特殊なUnicode文字を含みます。
- 一部の環境で正しく表示されない場合があります
- これはファイルの問題ではなく環境の制限です

## 🔗 関連ドキュメント

- **[記法仕様詳細](../docs/specs/notation.md)** - 完全な記法仕様
- **[ユーザーガイド](../docs/USER_GUIDE.md)** - 基本的な使用方法
- **[記法チェックリスト](NOTATION_CHECKLIST.md)** - 記法の完全リスト

## 🤝 コントリビューション

新しいサンプルファイルの追加や既存ファイルの改善提案は歓迎します。

### コントリビューション手順
1. Issue作成で提案内容を説明
2. 適切なブランチでサンプルファイル作成
3. Pull Request作成
4. レビュー・マージ

## 📄 ライセンス

このサンプルファイル集は、Kumihan-Formatterプロジェクトと同じライセンスの下で提供されています。

---

**最終更新**: 2025-01-01  
**対応バージョン**: Kumihan-Formatter v2.2.0-alpha  
**サンプルファイル数**: 20ファイル  
**総記法カバレッジ**: 100%（21/21種類）