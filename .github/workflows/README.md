# GitHub Actions ワークフロー構成

本プロジェクトのCI/CD構成の説明です。

## ワークフロー一覧

### 1. CI / Quick Test (`ci.yml`)
- **目的**: PRやpush時の高速な基本動作確認
- **実行環境**: Ubuntu + Python 3.9のみ
- **トリガー**: 
  - `main`ブランチへのpush/PR
  - ドキュメントのみの変更時はスキップ
- **実行時間**: 約1分

### 2. CI / Full Test Matrix (`ci-full.yml`)
- **目的**: 全OS・全Pythonバージョンでの完全なテスト
- **実行環境**: 
  - OS: Ubuntu, Windows, macOS
  - Python: 3.9, 3.10, 3.11, 3.12
- **トリガー**: 
  - `main`ブランチへのpush/PR
  - 手動実行可能
- **特徴**:
  - 構文検証を含む統合テスト
  - キャッシュによる高速化
  - 並列実行で効率化
- **実行時間**: 約5-10分

### 3. Code Quality / Emoji Check (`emoji-check.yml`)
- **目的**: 絵文字使用ポリシーの遵守確認
- **トリガー**: 
  - Python/シェルスクリプト変更時
  - 手動実行可能
- **特徴**: Markdownファイルは警告のみ

### 4. Docs / Consistency Check (`docs-check.yml`)
- **目的**: バージョン情報とドキュメントの整合性確認
- **トリガー**: 
  - ドキュメントやコード変更時
  - バージョン更新時
- **チェック項目**:
  - バージョン番号の一致
  - 新機能のドキュメント更新

## ワークフロー最適化の要点

### 実行時間の短縮
1. **2段階CI**: 高速な基本テスト → 完全なマトリックステスト
2. **キャッシュ活用**: pip依存関係のキャッシュ
3. **条件付き実行**: path-ignoreで不要な実行を回避
4. **並列化**: 独立したジョブは並列実行

### 保守性の向上
1. **統合されたワークフロー**: 重複を排除し、一元管理
2. **明確な命名規則**: `カテゴリ / 内容`形式
3. **手動実行オプション**: `workflow_dispatch`でデバッグ可能

### 削除されたワークフロー
- `ci-full-matrix.yml` → `ci-full.yml`に統合
- `syntax-check.yml` → `ci-full.yml`に統合
- `syntax-validation.yml` → `ci-full.yml`に統合
- `monthly-docs-review.yml.disabled` → 削除

## トラブルシューティング

### CI失敗時の対処
1. Quick Testが失敗 → 基本的な構文エラーの可能性
2. Full Testの特定OS/Pythonで失敗 → 環境依存の問題
3. Emoji Checkが失敗 → 絵文字を[タグ]形式に置換
4. Docs Checkが失敗 → バージョン番号を統一

### 手動実行方法
GitHubのActionsタブから対象ワークフローを選択し、"Run workflow"ボタンをクリック。