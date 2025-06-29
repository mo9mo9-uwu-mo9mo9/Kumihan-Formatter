# GitHub Actions ワークフロー運用ガイド

**最終更新**: 2025-06-29 (Issue #284 Phase 1実装完了)
**ステータス**: 🎯 最適化継続中・Phase 1完了

## 🚨 Issue #284 Phase 1対応完了

**問題**: GitHub Actionsワークフロー詰まり（同時実行制限）継続
**対応**: Phase 1緊急対策実装

### 📊 最適化結果
- **ワークフロー削減**: 17個 → 9個 (-47%)
- **Concurrency制御**: 全アクティブワークフローに追加
- **Timeout設定**: 適切な値を設定（テスト:10分、品質:15分、監視:5分）
- **無効化ワークフロー**: 物理削除完了（8個）

## 🚦 現在のワークフロー構成 (Phase 1最適化済み)

### 🔴 **アクティブ・必須ワークフロー (9個)**

| ワークフロー | ステータス | トリガー | 説明 | 優先度 |
|------------|----------|--------|------|------|
| **critical-tests.yml** | ✅ 必須 | PR/push(main) | Critical Test - 🔴 PR必須チェック | Critical |
| **ci-full.yml** | ✅ 有効 | PR/push(main) | Full Test Matrix | High |
| **coverage.yml** | ✅ 有効 | PR/push(main) | Coverage Report | High |
| **docs-unified.yml** | ✅ 新規 | PR/push | 統合ドキュメントチェック | Medium |
| **auto-update.yml** | ✅ 有効 | PR | PR自動更新 | Medium |
| **emoji-check.yml** | ✅ 有効 | PR | 絵文字チェック | Low |
| **sample-syntax-check.yml** | ✅ 有効 | PR (samples) | サンプル記法チェック | Medium |
| **quality-tests.yml** | ✅ 有効 | PR/push(main) | 品質テスト | High |
| **workflow-health-monitor.yml** | ✅ 有効 | schedule | ワークフロー健全性監視 | Low |

### 🗑️ **削除されたワークフロー (8個) - Phase 1**

| ワークフロー | 削除日 | 理由 |
|------------|--------|------|
| **ci.yml** | 2025-06-29 | レガシー（テスト階層システムに置換） |
| **quality-monitoring.yml** | 2025-06-29 | 一時無効化から削除 |
| **enhanced-quality-check.yml** | 2025-06-29 | 一時無効化から削除 |
| **docs-validation.yml** | 2025-06-29 | docs-unified.ymlに統合 |
| **docs-check.yml** | 2025-06-29 | docs-unified.ymlに統合 |
| **doc-consistency-check.yml** | 2025-06-29 | docs-unified.ymlに統合 |
| **e2e-tests.yml** | 2025-06-29 | 再構築中のため削除 |
| **e2e-tests-minimal.yml** | 2025-06-29 | 無効化のため削除 |

## 📊 Phase 1実装内容（Issue #284）

### ✅ 実装済み (2025-06-29)
1. **Concurrency制御追加**
   - 全アクティブワークフローに`concurrency`設定を追加
   - `cancel-in-progress: true`で重複実行を自動キャンセル

2. **Timeout設定追加**
   - テストジョブ: 10分
   - 品質・カバレッジジョブ: 15分
   - 監視・自動更新ジョブ: 5分

3. **無効化ワークフロー削除**
   - 8個の非アクティブワークフローを物理削除
   - リポジトリのクリーンアップ完了

## 📊 過去の実装内容（Issue #278）

### ✅ 実装済み
1. **quality-monitoring.yml**
   - pull_requestトリガー追加
   - pushトリガーをmain/develop/feature/**/fix/**に拡張
   - 品質ゲート失敗時もワークフロー継続する設定に変更

2. **enhanced-quality-check.yml**
   - pull_requestトリガー追加
   - pathsフィルタを拡張（dev/tools/**/*.py, kumihan_formatter/**/*.py追加）
   - main/developブランチでの自動実行復旧

### 🔄 今後の作業
1. E2Eテストワークフローの段階的復旧
2. 24時間の安定性モニタリング
3. 完全自動化の最終確認

## 🛡️ 品質ゲート設定（Phase 2調整済み）

| メトリクス | 閾値 | クリティカル |
|-----------|------|-------------|
| 記法合格率 | 90%以上 | Yes |
| テスト合格率 | 80%以上 | No |
| 総合品質スコア | 70点以上 | No |
| 平均変換時間 | 10秒以下 | No |

## 📝 注意事項

- 品質ゲートチェックは失敗してもワークフローは継続します
- 失敗時は改善推奨事項が表示されますが、マージはブロックされません
- E2Eテストは再構築中のため、手動実行のみ可能です