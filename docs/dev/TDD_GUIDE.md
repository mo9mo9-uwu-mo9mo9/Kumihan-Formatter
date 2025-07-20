# TDD開発ガイド

> Test-Driven Development (TDD) 実践ガイド for Kumihan-Formatter

## 🧪 TDDサイクル

### Red-Green-Refactorサイクル

```
🔴 Red → 🟢 Green → 🔄 Refactor → 🔴 Red → ...
```

1. **🔴 Red Phase**: 失敗するテストを書く
2. **🟢 Green Phase**: テストを通すための最小実装
3. **🔄 Refactor Phase**: コードを改善（動作は変更しない）

## 📋 TDD実践手順

### 1. Red Phase - 失敗するテストを書く

```python
import pytest
from kumihan_formatter.core.new_feature import NewFeature

@pytest.mark.tdd_red
def test_new_feature_basic_functionality():
    """新機能の基本動作テスト（まず失敗させる）"""
    # Arrange
    feature = NewFeature()

    # Act & Assert - まだ実装されていないので失敗する
    result = feature.process("input")
    assert result == "expected_output"
```

### 2. Green Phase - 最小実装でテスト通過

```python
# kumihan_formatter/core/new_feature.py
class NewFeature:
    def process(self, input_data):
        # 最小実装 - とりあえずテストが通るだけ
        if input_data == "input":
            return "expected_output"
        return None
```

### 3. Refactor Phase - コード改善

```python
# 改善版
class NewFeature:
    def process(self, input_data):
        # より汎用的で読みやすい実装
        return self._transform_input(input_data)

    def _transform_input(self, data):
        # 変換ロジックを分離
        return f"processed_{data}"
```

## 🛠️ TDDヘルパーの使用

### 基本的な使用例

```python
def test_with_tdd_helper(tdd_helper):
    """TDDヘルパーを使用したテスト"""

    # Red Phase の確認
    def failing_test():
        result = non_existent_function()
        assert result == "expected"

    tdd_helper.assert_red_phase(failing_test)

    # Green Phase の確認
    def passing_test():
        result = "actual_result"
        assert result == "actual_result"

    tdd_helper.assert_green_phase(passing_test)
```

### リファクタリング安全性確認

```python
def test_refactor_safety(tdd_helper):
    """リファクタリング前後で動作が変わらないことを確認"""

    def before_refactor(input_data):
        # リファクタリング前の実装
        return input_data.upper()

    def after_refactor(input_data):
        # リファクタリング後の実装
        return input_data.upper()

    test_input = "hello"
    tdd_helper.verify_refactor_safety(
        before_refactor,
        after_refactor,
        test_input
    )
```

## 📊 テストマーカーの活用

### TDD用マーカー

```python
@pytest.mark.tdd_red
def test_should_fail_initially():
    """Red Phase - 最初は失敗すべきテスト"""
    pass

@pytest.mark.tdd_green
def test_should_pass_after_implementation():
    """Green Phase - 実装後に成功すべきテスト"""
    pass

@pytest.mark.tdd_refactor
def test_behavior_preservation():
    """Refactor Phase - 動作保持確認テスト"""
    pass
```

### テスト分類マーカー

```python
@pytest.mark.unit
def test_unit_functionality():
    """ユニットテスト"""
    pass

@pytest.mark.integration
def test_component_integration():
    """統合テスト"""
    pass

@pytest.mark.performance
def test_performance_requirement():
    """パフォーマンステスト"""
    pass
```

## 🏃‍♂️ 高速TDD実行

### 軽量テスト実行

```bash
# 失敗した時点で停止（Red Phase確認用）
make test-quick

# 特定のマーカーのみ実行
pytest -m tdd_red -v
pytest -m unit -v

# 並行実行で高速化
make test-parallel
```

### ファイル監視での自動テスト

```bash
# ファイル変更時に自動でテスト実行
pytest-watch -- -x --tb=short
```

## 📈 TDD品質チェック

### カバレッジ目標

- **新機能**: 90%以上のカバレッジ
- **既存コード**: 段階的にカバレッジ向上
- **統合テスト**: 主要フローの網羅

```bash
# カバレッジ付きテスト実行
make coverage

# カバレッジレポート確認
open htmlcov/index.html
```

### コード品質

```bash
# 完全品質チェック
make full-quality-check

# TDD準拠チェック
make tdd-check
```

## 🎯 TDDベストプラクティス

### DO（推奨事項）

1. **小さなステップ**: 一度に一つの機能をテスト
2. **明確な命名**: テスト名で意図を明示
3. **arrange-act-assert**: テスト構造を統一
4. **高速実行**: テストは数秒以内で完了
5. **独立性**: テスト間で依存関係を持たない

### DON'T（避けるべき）

1. **複雑なテスト**: 一つのテストで複数の機能をテスト
2. **実装詳細のテスト**: 内部実装に依存したテスト
3. **スキップの乱用**: テストスキップは最小限に
4. **モックの過度な使用**: 必要以上にモックを使わない

## 🔧 便利なフィクスチャ

### ファイル操作

```python
def test_file_processing(temp_dir, sample_file):
    """ファイル処理テスト"""
    # temp_dir: 一時ディレクトリ
    # sample_file: サンプルファイル
    pass
```

### モック

```python
def test_with_mocks(mock_renderer, mock_parser):
    """モックを使用したテスト"""
    # mock_renderer: モックレンダラー
    # mock_parser: モックパーサー
    pass
```

### パフォーマンス

```python
def test_performance(performance_monitor):
    """パフォーマンステスト"""
    performance_monitor.start()

    # 測定対象の処理
    result = heavy_computation()

    performance_monitor.stop()
    performance_monitor.assert_faster_than(1.0)  # 1秒以内
```

## 🚀 実践例

### 新機能開発の完全な例

```python
# 1. Red Phase - 失敗するテストを書く
@pytest.mark.tdd_red
def test_footnote_parser_basic():
    from kumihan_formatter.core.footnote_parser import FootnoteParser

    parser = FootnoteParser()
    result = parser.parse("((footnote))")
    assert result.type == "footnote"
    assert result.content == "footnote"

# 2. Green Phase - 最小実装
class FootnoteParser:
    def parse(self, text):
        if text == "((footnote))":
            return type('Result', (), {
                'type': 'footnote',
                'content': 'footnote'
            })()

# 3. Green Phase - テスト通過確認
@pytest.mark.tdd_green
def test_footnote_parser_passes():
    from kumihan_formatter.core.footnote_parser import FootnoteParser

    parser = FootnoteParser()
    result = parser.parse("((footnote))")
    assert result.type == "footnote"

# 4. Refactor Phase - 改善とテスト
@pytest.mark.tdd_refactor
def test_footnote_parser_multiple_cases():
    from kumihan_formatter.core.footnote_parser import FootnoteParser

    parser = FootnoteParser()

    # 複数のケースで動作確認
    cases = [
        ("((note1))", "note1"),
        ("((note2))", "note2"),
        ("((longer footnote))", "longer footnote"),
    ]

    for input_text, expected_content in cases:
        result = parser.parse(input_text)
        assert result.type == "footnote"
        assert result.content == expected_content
```

## 📚 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [Test-Driven Development: By Example](https://www.amazon.com/dp/0321146530)
- [Clean Code](https://www.amazon.com/dp/0132350882)

---

**TDDは習慣です。小さなステップから始めて、継続的に改善していきましょう！** 🎯
