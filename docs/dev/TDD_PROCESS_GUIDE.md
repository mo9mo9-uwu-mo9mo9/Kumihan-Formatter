# TDD-First開発プロセスガイド

> **Issue #640** - TDD-First開発システム完全実装
> **Version**: 1.0.0 (2025-01-29)

## 📋 目次

1. [概要](#概要)
2. [TDD開発フロー](#tdd開発フロー)
3. [Makefileコマンド一覧](#makefileコマンド一覧)
4. [品質基準](#品質基準)
5. [実践例](#実践例)
6. [トラブルシューティング](#トラブルシューティング)

## 概要

Kumihan-FormatterプロジェクトではTDD-First開発を採用し、技術的負債ゼロを目指しています。
全ての新機能・バグ修正は必ずTDD手法で実装する必要があります。

### なぜTDD-First？

- **品質保証**: テストファーストで品質を担保
- **設計改善**: テスタブルなコード設計を強制
- **リグレッション防止**: 既存機能への影響を防ぐ
- **ドキュメント**: テストが仕様書として機能

## TDD開発フロー

### 1. TDDセッション開始

```bash
# Issue番号を指定してTDDセッションを開始
make tdd-start ISSUE_NUMBER=640
```

このコマンドで以下が実行されます：
- TDDセッションファイル（`.tdd_session.json`）の作成
- 正しいブランチへの切り替え（`feat/issue-640-*`）
- Issue情報の取得と初期設定

### 2. Red Phase（失敗するテストを書く）

```bash
# テスト仕様テンプレートを生成
make tdd-spec

# 失敗するテストを作成して実行
make tdd-red
```

**ポイント**:
- まず失敗するテストを書く
- テストは具体的で検証可能な仕様を表現
- 一度に1つの機能だけをテスト

### 3. Green Phase（最小限の実装）

```bash
# テストを通す最小限の実装を行う
make tdd-green
```

**ポイント**:
- テストを通すための最小限のコードのみ実装
- 過度な設計や最適化は避ける
- 全てのテストがグリーンになることを確認

### 4. Refactor Phase（品質改善）

```bash
# コードの品質を改善
make tdd-refactor
```

**ポイント**:
- テストを壊さない範囲でリファクタリング
- コードの重複を排除
- 可読性・保守性の向上

### 5. セキュリティテスト

```bash
# セキュリティテストの実行
make tdd-security
```

必須のセキュリティテスト：
- SQL Injection対策
- XSS対策
- CSRF対策
- ファイルアップロードセキュリティ

### 6. TDDサイクル完了

```bash
# 品質チェックと完了処理
make tdd-complete
```

## Makefileコマンド一覧

| コマンド | 説明 | 使用例 |
|---------|------|--------|
| `make tdd-start` | TDDセッション開始 | `make tdd-start ISSUE_NUMBER=640` |
| `make tdd-spec` | テスト仕様テンプレート生成 | `make tdd-spec` |
| `make tdd-red` | Red Phase実行 | `make tdd-red` |
| `make tdd-green` | Green Phase実行 | `make tdd-green` |
| `make tdd-refactor` | Refactor Phase実行 | `make tdd-refactor` |
| `make tdd-security` | セキュリティテスト実行 | `make tdd-security` |
| `make tdd-complete` | TDDサイクル完了 | `make tdd-complete` |
| `make tdd-status` | 現在のTDDセッション状況表示 | `make tdd-status` |

## 品質基準

### ティア別カバレッジ要求

| ティア | 対象 | カバレッジ要求 | 備考 |
|--------|------|----------------|------|
| Critical | Core機能・Commands | 90%以上必須 | PR必須要件 |
| Important | レンダリング・バリデーション | 80%以上推奨 | 段階的改善可 |
| Supportive | ユーティリティ・キャッシング | 統合テストで代替可 | - |
| Special | GUI・パフォーマンス | E2E・ベンチマークで代替 | - |

### GitHub Actions統合

PR作成時に自動的に以下がチェックされます：

1. **TDDセッション存在確認**: `.tdd_session.json`の存在
2. **TDDサイクル履歴**: Red→Green→Refactorの実行履歴
3. **カバレッジ基準**: Critical Tierは90%以上必須
4. **品質ゲート**: 全品質チェックのパス
5. **セキュリティテスト**: 100%パス必須

## 実践例

### 新機能追加の例

```bash
# 1. Issue #650の新機能開発を開始
make tdd-start ISSUE_NUMBER=650

# 2. テスト仕様を生成
make tdd-spec

# 3. 失敗するテストを書く
vim tests/unit/test_new_feature.py
# ... テストコードを記述 ...

# 4. Red Phaseを実行（テストが失敗することを確認）
make tdd-red

# 5. 実装を行う
vim kumihan_formatter/features/new_feature.py
# ... 最小限の実装 ...

# 6. Green Phaseを実行（テストが通ることを確認）
make tdd-green

# 7. リファクタリング
# ... コードの改善 ...

# 8. Refactor Phaseを実行
make tdd-refactor

# 9. セキュリティテスト
make tdd-security

# 10. 完了確認
make tdd-complete
```

### バグ修正の例

```bash
# 1. Issue #651のバグ修正を開始
make tdd-start ISSUE_NUMBER=651

# 2. バグを再現するテストを書く（Red Phase）
vim tests/unit/test_bug_fix.py
# ... バグを再現するテスト ...
make tdd-red

# 3. バグを修正（Green Phase）
vim kumihan_formatter/core/buggy_module.py
# ... バグ修正 ...
make tdd-green

# 4. 品質改善（Refactor Phase）
make tdd-refactor

# 5. 完了
make tdd-complete
```

## トラブルシューティング

### TDDセッションエラー

**問題**: `make tdd-status`でセッション読み込みエラー

**解決方法**:
```bash
# 古いセッションファイルを削除
rm .tdd_session.json

# 新しいセッションを開始
make tdd-start ISSUE_NUMBER=640
```

### カバレッジ不足

**問題**: テストカバレッジが90%に達しない

**解決方法**:
1. カバレッジレポートを確認
   ```bash
   pytest --cov=kumihan_formatter --cov-report=html
   open htmlcov/index.html
   ```

2. カバーされていない行を特定

3. 追加のテストケースを作成

### セキュリティテスト失敗

**問題**: セキュリティテストが失敗する

**解決方法**:
1. 具体的なエラーメッセージを確認
2. 該当するセキュリティスクリプトを実行
   ```bash
   python scripts/security_sql_injection_test.py
   ```
3. 脆弱性を修正

## ベストプラクティス

1. **小さなサイクル**: Red-Green-Refactorを小さく繰り返す
2. **明確なテスト名**: `test_機能名_期待される動作_条件`
3. **AAA パターン**: Arrange-Act-Assert構造を守る
4. **モックの適切な使用**: 外部依存はモックで分離
5. **境界値テスト**: エッジケースを必ずカバー

## 関連ドキュメント

- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - 開発全般のガイド
- [ARCHITECTURE.md](../ARCHITECTURE.md) - システムアーキテクチャ
- [CLAUDE.md](../../CLAUDE.md) - AI開発支援ガイド

---

**Note**: このガイドは継続的に更新されます。最新の情報はGitHubのmainブランチを参照してください。