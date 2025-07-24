# Claude Code qcheck系コマンドガイド

> Issue #578: Claude Code最適化ドキュメント改善 - qcheck系コマンド実装

## 概要

Claude Code開発に最適化された品質チェックショートカットシステム。
2025年ベストプラクティスに基づく、効率的な開発ワークフローを提供。

## コマンド一覧

### `qcheck` - 全体品質チェック
```bash
# 実行方法
./scripts/qcheck
# または
python scripts/qcheck_commands.py qcheck
```

**実行内容**:
- 📏 ファイルサイズチェック（300行制限）
- 🏗️ アーキテクチャチェック
- 🔍 型チェック（mypy strict）
- 📚 ドキュメント品質チェック
- 🧪 基本テスト実行

**使用タイミング**: コミット前、PR作成前

### `qcheckf` - 変更ファイル関数チェック
```bash
./scripts/qcheckf
```

**実行内容**:
- 📋 Git差分から変更ファイル一覧表示
- 🔍 変更ファイルの関数レベル品質チェック
- 📝 変更ファイル限定型チェック

**使用タイミング**: 個別ファイル修正後

### `qcheckt` - テスト品質チェック
```bash
./scripts/qcheckt
```

**実行内容**:
- 🧪 カバレッジ付きテスト実行
- 📊 カバレッジレポート表示
- 🔍 テスト品質評価

**使用タイミング**: TDD実践時、テスト追加後

### `qdoc` - ドキュメント品質チェック
```bash
./scripts/qdoc
```

**実行内容**:
- 📚 ドキュメント品質検証（リンク切れ等）
- 📝 Markdownリンター
- 🔗 リンク切れチェック

**使用タイミング**: ドキュメント更新後

## Claude Code統合

### CLAUDE.mdでの使用
```markdown
# 品質確認手順

1. 実装完了後:
   ```bash
   qcheck
   ```

2. 個別ファイル修正時:
   ```bash
   qcheckf
   ```

3. テスト追加時:
   ```bash
   qcheckt
   ```

4. ドキュメント更新時:
   ```bash
   qdoc
   ```
```

### 推奨ワークフロー

#### 新機能実装時
```bash
# 1. 設計・計画段階
qdoc  # 既存ドキュメントの確認

# 2. TDD実装段階
qcheckt  # テストカバレッジ確認

# 3. 実装完了時
qcheckf  # 変更ファイルチェック

# 4. コミット前
qcheck  # 全体品質確認
```

#### バグ修正時
```bash
# 1. 修正前
qcheckt  # 現在のテスト状況確認

# 2. 修正後
qcheckf  # 修正ファイルチェック
qcheck   # 全体影響確認
```

## 実装詳細

### 技術仕様
- **言語**: Python 3.12+
- **依存関係**: requests, radon（オプション）
- **実行環境**: 仮想環境自動活性化対応

### エラーハンドリング
- コマンド未存在時の適切なフォールバック
- 部分的失敗の許容（allow_failure）
- 詳細なエラーレポート

### パフォーマンス最適化
- Git差分ベースのファイル限定チェック
- 軽量テスト優先実行
- 外部URLチェックのレート制限

## カスタマイズ

### 除外設定
`scripts/qcheck_commands.py`で設定変更可能:

```python
# ファイル除外パターン
exclude_patterns = {
    'venv', 'node_modules', '.git', 'dist',
    '__pycache__', '.pytest_cache'
}
```

### チェック項目追加
各コマンドの`checks`リストに項目追加:

```python
checks = [
    ("新しいチェック", self._new_check_function),
    # 既存チェック...
]
```

## トラブルシューティング

### よくある問題

#### 1. `markdownlint`コマンドが見つからない
```bash
npm install -g markdownlint-cli
```

#### 2. `radon`がインストールされていない
```bash
pip install radon
```

#### 3. 仮想環境が見つからない
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### ログ確認
詳細ログは以下で確認:
```bash
KUMIHAN_DEV_LOG=true ./scripts/qcheck
cat /tmp/kumihan_formatter/dev_log_*.log
```

## 統合テスト

### pre-commitフック統合
`.pre-commit-config.yaml`に自動統合済み:

```yaml
- id: doc-validator
  name: 📚 ドキュメント品質チェック
  entry: python scripts/doc_validator.py
```

### GitHub Actions統合
`.github/workflows/quality-check.yml`に統合済み:

```yaml
- name: Documentation Quality Check
  run: python scripts/doc_validator.py --report-format json
```

## 今後の拡張予定

### Phase 2: インタラクティブ要素
- コードプレイグラウンド統合
- リアルタイム品質表示

### Phase 3: AI統合
- AI支援品質チェック
- 自動修正提案

---

**Issue #578 Phase 1 実装完了**
**次のフェーズ**: Week 2 品質ゲート統合、Week 3 アクセシビリティ対応
