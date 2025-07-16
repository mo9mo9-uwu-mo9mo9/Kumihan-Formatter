# Kumihan-Formatter テストドキュメント

> **作成日**: 2025-07-06
> **バージョン**: 1.0.0
> **対象**: 開発者・CI/CD・テスト実行者

## 概要

このドキュメントは、Kumihan-Formatterプロジェクトのテスト環境、テスト種別、実行方法、既知の問題と対策について包括的に説明します。

## テスト環境

### ローカル環境

#### 必要な依存関係
```toml
[project.optional-dependencies]
dev = [
    "black>=23.0",
    "isort>=5.0",
    "flake8>=6.0",
    "beautifulsoup4>=4.9",
    "psutil>=5.9",
    "pytest>=7.0",
    "pytest-cov>=4.0",
]
```

#### サポート対象バージョン
- **Python**: 3.9, 3.10, 3.11, 3.12
- **OS**: Ubuntu (Linux), Windows, macOS

### GitHub Actions環境

#### Quick Check (Push時)
- **OS**: ubuntu-latest
- **Python**: 3.11
- **実行内容**:
  - 軽量リントチェック (flake8)
  - フォーマットチェック (black)
  - 高速テスト実行 (pytest -x --ff -q)

#### Full Test (PR時)
- **OS**: ubuntu-latest, windows-latest, macos-latest
- **Python**: 3.9, 3.10, 3.11, 3.12 (全組み合わせ)
- **実行内容**:
  - 完全リントチェック
  - フォーマット・インポートソートチェック
  - 完全テストスイート実行
  - カバレッジレポート生成

## テスト構造

### ディレクトリ構成
```
tests/
├── __init__.py                    # テストパッケージ初期化
├── unit/                          # ユニットテスト (0テスト - 空)
│   └── __init__.py               # 個別クラス・関数テスト用
├── integration/                   # 統合テスト (33テスト)
│   ├── test_basic_integration.py  # CLI基本動作テスト (2テスト)
│   ├── test_cli_integration.py    # CLI全体動作テスト (11テスト)
│   ├── test_file_io_integration.py # ファイルI/O統合テスト (12テスト)
│   ├── test_simple_integration.py # シンプル統合テスト (33テスト)
│   └── test_template_integration.py # テンプレート統合テスト (10テスト)
├── e2e/                          # エンドツーエンドテスト (51テスト)
│   ├── test_error_handling.py    # エラーハンドリングテスト (14テスト)
│   ├── test_option_combinations.py # オプション組み合わせテスト (12テスト)
│   ├── test_real_scenarios.py    # 実際の使用シナリオテスト (8テスト)
│   └── test_simple_e2e.py        # シンプルE2Eテスト (37テスト)
└── windows_permission_helper.py  # Windows権限制御ヘルパー
```

### テスト統計
- **総テスト数**: 84テスト
- **総テストファイル数**: 9ファイル
- **総コード行数**: 約4,170行

## テスト種別詳細

### 1. 統合テスト (Integration Tests)

#### CLI統合テスト
- **ファイル**: `test_cli_integration.py`, `test_basic_integration.py`
- **テスト数**: 13テスト
- **内容**:
  - CLIヘルプ表示
  - convert コマンド動作確認
  - オプション組み合わせ
  - 補助コマンド (check-syntax, generate-sample)

#### ファイルI/O統合テスト
- **ファイル**: `test_file_io_integration.py`
- **テスト数**: 12テスト
- **内容**:
  - テキストファイル読み込み (4テスト)
  - HTML出力処理 (4テスト)
  - エンコーディング処理 (4テスト)

#### テンプレート統合テスト
- **ファイル**: `test_template_integration.py`
- **テスト数**: 10テスト
- **内容**:
  - テンプレート読み込み (3テスト)
  - 変数展開・条件分岐・ループ (4テスト)
  - HTML/CSS/JavaScript統合出力 (3テスト)

### 2. エンドツーエンドテスト (E2E Tests)

#### エラーハンドリングテスト
- **ファイル**: `test_error_handling.py`
- **テスト数**: 14テスト
- **内容**:
  - ファイルエラー処理 (4テスト)
  - 構文エラー処理 (4テスト)
  - システムエラー処理 (3テスト)
  - 復旧機能 (3テスト)

#### オプション組み合わせテスト
- **ファイル**: `test_option_combinations.py`
- **テスト数**: 12テスト
- **内容**:
  - 基本オプション組み合わせ (4テスト)
  - 高度なオプション組み合わせ (4テスト)
  - 設定ファイル連携 (4テスト)

#### 実使用シナリオテスト
- **ファイル**: `test_real_scenarios.py`
- **テスト数**: 8テスト
- **内容**:
  - CoC6th/現代ホラー/ファンタジーシナリオ (3テスト)
  - 長文・多層構造ドキュメント (2テスト)
  - 複合コンテンツ・目次生成・画像リンク (3テスト)

## テスト設定

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
minversion = 6.0
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=kumihan_formatter
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
timeout = 300
log_cli = true
log_cli_level = INFO
```

### pyproject.toml テスト設定
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]

[tool.coverage.run]
source = ["kumihan_formatter"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
]
```

## テスト実行方法

### ローカル実行

#### 全テスト実行
```bash
# 基本実行
pytest

# 詳細実行（推奨）
pytest -v --cov=kumihan_formatter --cov-report=html --cov-report=term-missing

# 並列実行（高速化）
pytest -n auto  # pytest-xdistが必要
```

#### 特定テスト実行
```bash
# 統合テストのみ
pytest tests/integration/

# E2Eテストのみ
pytest tests/e2e/

# 特定ファイル
pytest tests/integration/test_cli_integration.py

# 特定テスト関数
pytest tests/integration/test_cli_integration.py::TestCLIIntegration::test_cli_help_display
```

#### マーカー別実行
```bash
# 統合テストのみ
pytest -m integration

# E2Eテストのみ
pytest -m e2e

# 遅いテストを除外
pytest -m "not slow"
```

### GitHub Actions実行

#### Manual Trigger
```bash
# ワークフローディスパッチでPR用完全テスト実行
gh workflow run test.yml
```

#### 自動実行
- **Push**: Quick check実行
- **Pull Request**: Full test実行

## 既知の問題と対策

### プラットフォーム固有の問題

#### Windowsファイル権限テスト
**問題**: Unix系の`chmod`がWindows環境で動作しない

**対策**:
- `windows_permission_helper.py`による権限制御実装
- `@pytest.mark.skipif`によるプラットフォーム固有テストのスキップ
- `icacls`コマンドを使用したWindows権限制御

```python
@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Windows file permission tests need platform-specific implementation",
)
def test_permission_denied_file(self):
    # Unix系でのみ実行されるテスト
```

#### 文字エンコーディング問題
**問題**: プラットフォーム間での文字エンコーディング差異

**対策**:
- 明示的な`encoding="utf-8"`指定
- エンコーディング検出機能のテスト
- フォールバック処理の実装

### テスト安定性の問題

#### 複雑なシナリオテスト
**問題**: 長時間実行されるテストやリソース集約的なテストの不安定性

**対策**:
- `@unittest.skip`による一時的な無効化
- タイムアウト設定 (300秒)
- リソース使用量の制限

```python
@unittest.skip("Complex scenario tests - skipping for CI stability")
def test_complex_scenario(self):
    # CI環境での安定性のため一時無効化
```

#### 並行実行時の競合
**問題**: テンポラリファイル・ディレクトリの競合

**対策**:
- `tempfile.mkdtemp()`による一意なテンポラリディレクトリ生成
- `setUp()`/`tearDown()`での確実なクリーンアップ
- プロセス分離による競合回避

### 依存関係の問題

#### テスト間依存
**現状**: 各テストは独立しており、テスト間依存は最小限

**確認項目**:
- テンポラリファイルの適切なクリーンアップ
- グローバル状態の変更なし
- 外部リソースへの依存最小化

## パフォーマンス考慮事項

### 実行時間最適化
- **Quick Check**: 軽量テストのみで高速フィードバック
- **Parallel Execution**: マトリックス実行による並列化
- **Test Selection**: 失敗テスト優先実行 (`--ff`)

### リソース使用量
- **Memory**: 大きなファイルテストでのメモリ使用量制限
- **Disk**: テンポラリファイルの確実なクリーンアップ
- **Network**: 外部リソースへの依存最小化

## トラブルシューティング

### よくある問題

#### 1. テスト実行失敗
```bash
# 依存関係の再インストール
pip install -e ".[dev]"

# キャッシュクリア
pytest --cache-clear

# 特定テストの詳細実行
pytest -v -s tests/path/to/test.py
```

#### 2. カバレッジレポート生成失敗
```bash
# カバレッジデータクリア
coverage erase

# 手動でカバレッジ実行
coverage run -m pytest
coverage report
coverage html
```

#### 3. 権限エラー (Windows)
```bash
# 管理者権限でコマンドプロンプト実行
# または PowerShell を管理者として実行
```

### ログとデバッグ

#### テストログ確認
```bash
# 詳細ログ付き実行
pytest -v -s --log-cli-level=DEBUG

# 特定テストのトレース
pytest --tb=long tests/path/to/test.py::test_function
```

#### GitHub Actions ログ確認
1. GitHub リポジトリの Actions タブ
2. 該当ワークフロー実行を選択
3. 失敗したジョブの詳細ログを確認

## メンテナンス

### 定期的な確認項目

#### テスト追加時
- [ ] 適切なマーカー追加
- [ ] プラットフォーム固有の考慮
- [ ] テンポラリファイルのクリーンアップ
- [ ] 実行時間の妥当性確認

#### 依存関係更新時
- [ ] 全テスト環境での動作確認
- [ ] 新しい警告・非推奨機能の対応
- [ ] パフォーマンス回帰の確認

### 今後の改善計画

#### 短期 (1-2ヶ月)
- [ ] Unit テストの充実
- [ ] Windows権限テストの安定化
- [ ] カバレッジ率向上 (目標: 90%+)

#### 中期 (3-6ヶ月)
- [ ] パフォーマンステストの自動化
- [ ] インテグレーションテストの拡充
- [ ] テストデータの体系化

#### 長期 (6ヶ月+)
- [ ] E2Eテストの完全自動化
- [ ] クロスプラットフォームテストの強化
- [ ] 継続的パフォーマンス監視

## 参考資料

- [CONTRIBUTING.md](../../CONTRIBUTING.md) - 開発ガイドライン
- [SPEC.md](../../SPEC.md) - プロジェクト仕様
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

**最終更新**: 2025-07-06
**次回レビュー予定**: 2025-08-06
