# テスト構造ガイド

このディレクトリは Kumihan-Formatter のテストファイルを体系的に整理しています。

## 📁 ディレクトリ構造

```
dev/tests/
├── README.md                    # このファイル
├── __init__.py                  # テストパッケージ初期化
│
├── 📁 integration/             # 統合テスト
│   ├── test_core_functionality.py      # コア機能統合テスト
│   ├── test_new_features.py             # 新機能統合テスト
│   ├── test_compound_block.py           # 複合ブロックテスト
│   ├── test_comprehensive_bold.py       # 太字機能包括テスト
│   ├── test_parsing_only.py             # パーサー単体テスト
│   ├── test_recursion_check.py          # 再帰制限テスト
│   ├── test_sample_generation.py        # サンプル生成テスト
│   └── test_simple_renderer.py          # シンプルレンダラーテスト
│
├── 📁 fixtures/                # テストデータ・フィクスチャ
│   ├── test_simple.txt                  # シンプルテスト用データ
│   └── test_simple_bold.txt             # 太字テスト用データ
│
├── 📁 debug/                   # デバッグ用テスト
│   ├── debug_bold_test.py               # 太字機能デバッグ
│   └── debug_marker.py                  # マーカー機能デバッグ
│
├── 📁 test_*_check/            # 一時的な検証用ディレクトリ
│   ├── test_fix_check/                  # バグ修正検証
│   ├── test_parser_check/               # パーサー検証
│   └── test_renderer_check/             # レンダラー検証
│
└── 📄 ユニットテスト (ルートレベル)
    ├── test_cli.py                      # CLI機能テスト
    ├── test_parser.py                   # パーサーユニットテスト
    ├── test_renderer.py                 # レンダラーユニットテスト
    ├── test_config.py                   # 設定機能テスト
    ├── test_syntax_validation.py        # 構文検証テスト
    ├── test_toc.py                      # 目次機能テスト
    ├── test_image_embedding.py          # 画像埋め込みテスト
    ├── test_sample_generation.py        # サンプル生成テスト
    ├── test_distribution_tools.py       # 配布ツールテスト
    ├── test_distignore.py               # 配布除外テスト
    ├── test_batch_security.py           # バッチセキュリティテスト
    ├── simple_syntax_test.py            # シンプル構文テスト
    ├── test_patterns.txt                # テストパターンデータ
    └── ...
```

## 🧪 テストカテゴリ

### **統合テスト** (`integration/`)
- **目的**: 複数コンポーネントの連携動作確認
- **特徴**: 実際のワークフロー全体をテスト
- **実行**: `python -m pytest dev/tests/integration/`

### **ユニットテスト** (ルートレベル)
- **目的**: 個別モジュール・機能の動作確認
- **特徴**: 外部依存最小、高速実行
- **実行**: `python -m pytest dev/tests/test_*.py`

### **デバッグテスト** (`debug/`)
- **目的**: 特定バグの再現・修正確認
- **特徴**: 問題特化、詳細ログ出力
- **実行**: `python dev/tests/debug/<ファイル名>.py`

### **フィクスチャ** (`fixtures/`)
- **目的**: テストデータ・入力ファイル
- **特徴**: 再利用可能、標準化された入力
- **使用**: 他のテストから import/読み込み

## 🚀 テスト実行方法

### **全テスト実行**
```bash
python -m pytest dev/tests/ -v
```

### **カテゴリ別実行**
```bash
# 統合テストのみ
python -m pytest dev/tests/integration/ -v

# ユニットテストのみ  
python -m pytest dev/tests/test_*.py -v

# 特定テスト
python -m pytest dev/tests/test_parser.py -v
```

### **デバッグテスト実行**
```bash
# 直接実行
python dev/tests/debug/debug_bold_test.py

# または詳細デバッグ
python -m pdb dev/tests/debug/debug_bold_test.py
```

## 📋 テスト追加ガイドライン

### **新しいテストの配置**

1. **ユニットテスト** → `dev/tests/test_<モジュール名>.py`
2. **統合テスト** → `dev/tests/integration/test_<機能名>.py`
3. **デバッグテスト** → `dev/tests/debug/debug_<問題名>.py`
4. **テストデータ** → `dev/tests/fixtures/<データ名>`

### **命名規則**

- **ユニット**: `test_<module_name>.py`
- **統合**: `test_<feature_name>.py`
- **デバッグ**: `debug_<issue_name>.py`
- **フィクスチャ**: `<test_type>_<description>.<ext>`

## 🛠️ メンテナンス

### **定期クリーンアップ**
- `test_*_check/` ディレクトリは一時的なもので、定期的に削除
- 不要になったデバッグテストの整理
- フィクスチャファイルの重複チェック

### **移行完了**
- ✅ ルートディレクトリからテストファイル除去
- ✅ 体系的なディレクトリ構造構築
- ✅ テスト実行方法の標準化

---

*更新日: 2025-06-26*  
*🤖 Generated with Claude Code*