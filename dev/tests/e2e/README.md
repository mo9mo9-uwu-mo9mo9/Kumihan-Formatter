# E2E Test Suite Documentation

> **Kumihan-Formatter エンドツーエンドテストスイート**

---

## 📋 概要

このE2Eテストスイートは、Kumihan-Formatterの実際のユーザー利用シナリオに基づいた包括的なテストを提供します。ユニットテストでは検出できない統合的な問題を発見し、システム全体の品質を保証します。

## 🎯 テスト範囲

### テストカテゴリ

| テストファイル | カテゴリ | 対象範囲 | 重要度 |
|---------------|---------|----------|--------|
| `test_basic_workflow.py` | 基本ワークフロー | CLI・バッチファイル・D&D操作 | 🔴 高 |
| `test_file_operations.py` | ファイル操作 | 権限・エンコーディング・ディスク操作 | 🟡 中 |
| `test_output_quality.py` | 出力品質 | HTML5準拠・CSS品質・アクセシビリティ | 🟡 中 |
| `test_error_recovery.py` | エラー復旧 | 記法エラー・システムエラー・復旧能力 | 🟡 中 |

### プラットフォーム対応

- **Windows**: `.bat` ファイル経由のテスト
- **macOS**: `.command` ファイル経由のテスト  
- **Linux**: CLI直接実行のテスト
- **クロスプラットフォーム**: 出力一貫性の検証

## 🏗️ アーキテクチャ

```text
dev/tests/e2e/
├── conftest.py              # pytest設定・フィクスチャ
├── utils/
│   ├── execution.py         # ユーザー操作シミュレータ
│   ├── validation.py        # HTML出力検証
│   └── file_operations.py   # ファイル操作ユーティリティ
├── test_basic_workflow.py   # 基本ワークフロー
├── test_file_operations.py  # ファイル操作テスト
├── test_output_quality.py   # 出力品質テスト
└── test_error_recovery.py   # エラー復旧テスト
```

### 主要コンポーネント

#### UserActionSimulator
実際のユーザー操作をシミュレート：
- CLI変換実行
- バッチファイル実行
- D&Dシミュレーション
- プラットフォーム固有操作

#### HTMLValidator
HTML出力の包括的検証：
- HTML5準拠性チェック
- CSS埋め込み品質検証
- コンテンツ構造整合性
- アクセシビリティ準拠性

## 🚀 実行方法

### ローカル実行

```bash
# 全E2Eテスト実行
pytest dev/tests/e2e/ -v

# カテゴリ別実行
pytest dev/tests/e2e/test_basic_workflow.py -v
pytest dev/tests/e2e/test_output_quality.py -v

# 特定テスト実行
pytest dev/tests/e2e/test_basic_workflow.py::TestBasicWorkflow::test_cli_basic_conversion -v

# パフォーマンステスト
pytest dev/tests/e2e/test_basic_workflow.py::TestBasicWorkflow::test_performance_baseline -v
```

### GitHub Actions実行

E2Eテストは以下のトリガーで自動実行されます：

- **Push**: `main`ブランチへのプッシュ時
- **PR**: メインブランチへのプルリクエスト時
- **手動**: `workflow_dispatch`での手動実行

```yaml
# .github/workflows/e2e-tests.yml で設定
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ['3.9', '3.11']
```

## 📊 テスト詳細

### 1. 基本ワークフローテスト (`test_basic_workflow.py`)

**目的**: 実際のユーザー利用パターンの検証

**主要テスト**:
- `test_cli_basic_conversion`: CLI経由の基本変換
- `test_windows_batch_conversion`: Windowsバッチファイル実行
- `test_macos_command_conversion`: macOSコマンドファイル実行
- `test_drag_and_drop_simulation`: D&Dシミュレーション
- `test_performance_baseline`: パフォーマンス基準

**成功基準**:
- 変換完了時間 < 10秒
- HTML生成成功率 100%
- プラットフォーム固有操作の成功

### 2. ファイル操作テスト (`test_file_operations.py`)

**目的**: 様々なファイル状況での動作確認

**主要テスト**:
- `test_permission_variations`: 権限設定バリエーション
- `test_invalid_file_handling`: 無効ファイル処理
- `test_file_encoding_variations`: エンコーディングバリエーション
- `test_concurrent_file_access`: 同時アクセス処理

**成功基準**:
- 読み取り専用ファイルの正常処理
- 無効ファイルの適切なエラー処理
- UTF-8ファイルの完全サポート

### 3. 出力品質テスト (`test_output_quality.py`)

**目的**: 生成HTML・CSSの品質保証

**主要テスト**:
- `test_html5_compliance`: HTML5準拠性
- `test_css_embedding_quality`: CSS埋め込み品質
- `test_accessibility_compliance`: アクセシビリティ準拠
- `test_cross_platform_rendering_consistency`: プラットフォーム一貫性

**成功基準**:
- DOCTYPE・メタタグの完全性
- 必須CSS要素の包含
- アクセシビリティ要素の確認
- プラットフォーム非依存性

### 4. エラー復旧テスト (`test_error_recovery.py`)

**目的**: エラー状況での適切な動作確認

**主要テスト**:
- `test_malformed_syntax_recovery`: 不正記法の復旧
- `test_file_access_error_recovery`: ファイルアクセスエラー
- `test_memory_pressure_handling`: メモリ負荷処理
- `test_cleanup_after_errors`: エラー後クリーンアップ

**成功基準**:
- 部分的エラーでもHTML生成
- 適切なエラーマーカー表示
- システム状態の復旧

## 🔧 設定・カスタマイズ

### pytest設定 (`conftest.py`)

```python
@pytest.fixture(scope="session")
def test_workspace() -> Generator[Path, None, None]:
    """E2Eテスト用の一時作業領域"""
    # テストワークスペースの作成・設定
```

### 環境変数

```bash
# テストデバッグ用
PYTEST_CURRENT_TEST=1      # 現在のテスト表示
E2E_DEBUG=1               # E2Eテストデバッグ出力
E2E_KEEP_OUTPUT=1         # テスト出力保持
```

### カスタムマーカー

```python
@pytest.mark.slow        # 時間のかかるテスト
@pytest.mark.platform    # プラットフォーム固有テスト
@pytest.mark.integration # 統合テスト
```

## 📈 パフォーマンス基準

### 実行時間基準

| 操作 | 期待時間 | 最大許容時間 | 測定対象 |
|------|----------|-------------|----------|
| 基本変換 | < 1秒 | < 10秒 | `test_performance_baseline` |
| 大規模ファイル | < 30秒 | < 120秒 | `test_memory_pressure_handling` |
| 同時変換 | < 15秒 | < 60秒 | `test_concurrent_conversion` |

### リソース使用量

- **メモリ使用量**: 100MB以下（通常変換）
- **出力ファイルサイズ**: 入力の100倍以下
- **一時ファイル**: テスト完了後に自動削除

## 🐛 トラブルシューティング

### よくある問題

#### 1. プラットフォーム固有のスキップ

```python
# Windows専用テストのスキップ
@pytest.mark.skipif(platform.system() != "Windows", reason="Windows batch file test")
```

#### 2. タイムアウトエラー

```bash
# タイムアウト延長
pytest dev/tests/e2e/ --timeout=300 -v
```

#### 3. 権限エラー（macOS/Linux）

```bash
# 実行権限の付与
chmod +x 記法ツール/*.command
```

### デバッグ方法

```bash
# 詳細出力でテスト実行
pytest dev/tests/e2e/ -v -s --tb=long

# 特定のテストのみ、ログ出力込み
pytest dev/tests/e2e/test_basic_workflow.py::test_cli_basic_conversion -v -s --log-cli-level=DEBUG
```

## 🔄 継続的改善

### 定期タスク

1. **月次**: パフォーマンス基準の見直し
2. **リリース前**: 全プラットフォームでの包括テスト
3. **機能追加時**: 対応するE2Eテストの追加

### 品質指標

- **テストカバレッジ**: E2Eテストが主要ユーザーシナリオの90%以上をカバー
- **実行安定性**: CI環境での成功率95%以上
- **実行時間**: 全E2Eテスト30分以内完了

---

## 📚 関連ドキュメント

- [CONTRIBUTING.md](../../../CONTRIBUTING.md) - 開発ガイドライン
- [SPEC.md](../../../SPEC.md) - Kumihan記法仕様
- [GitHub Actions workflows](../../../.github/workflows/) - CI/CD設定

このE2Eテストスイートは、Kumihan-Formatterの品質保証の要として、継続的に改善・拡張していきます。