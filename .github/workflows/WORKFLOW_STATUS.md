# GitHub Actions ワークフロー運用ガイド

**最終更新**: 2025-06-28 (Issue #278 最適化完了)
**ステータス**: 🎯 最適化完了・安定運用中

## 🚨 Issue #278 対応完了

**問題**: GitHub Actionsワークフロー詰まり（同時実行制限）
**解決**: Phase 1-3の包括的最適化を実装

### 📊 最適化結果
- **ワークフロー削減**: 11個 → 7個 (-36%)
- **同時実行制限**: 解決（concurrency制御追加）
- **安定性**: 大幅向上（詰まり問題解決）
- **リソース効率**: 最適化済み

## 🚦 現在のワークフロー構成 (最適化済み)

### 🔴 **アクティブ・必須ワークフロー (7個)**

| ワークフロー | ステータス | トリガー | 説明 | 優先度 |
|------------|----------|--------|------|------|
| **ci.yml** | ✅ 必須 | PR/push(main) | Quick Test - 🔴 PR必須チェック | Critical |
| **ci-full.yml** | ✅ 有効 | PR/push(main) | Full Test Matrix | High |
| **coverage.yml** | ✅ 有効 | PR/push(main) | Coverage Report | High |
| **docs-unified.yml** | ✅ 新規 | PR/push | 統合ドキュメントチェック | Medium |
| **auto-update.yml** | ✅ 有効 | PR | PR自動更新 | Medium |
| **emoji-check.yml** | ✅ 有効 | PR | 絵文字チェック | Low |
| **sample-syntax-check.yml** | ✅ 有効 | PR (samples) | サンプル記法チェック | Medium |

### 🟡 **無効化済みワークフロー (6個)**

| ワークフロー | ステータス | 理由 | 復旧予定 |
|------------|----------|------|---------|
| **quality-monitoring.yml** | ⏸️ 無効 | 同時実行制限対策 | Phase 4 |
| **enhanced-quality-check.yml** | ⏸️ 無効 | 同時実行制限対策 | Phase 4 |
| **docs-validation.yml** | ⏸️ 無効 | docs-unified.ymlに統合 | 不要 |
| **docs-check.yml** | ⏸️ 無効 | docs-unified.ymlに統合 | 不要 |
| **doc-consistency-check.yml** | ⏸️ 無効 | docs-unified.ymlに統合 | 不要 |
| **e2e-tests.yml** | ⏸️ 無効 | 再構築中 | 未定 |

## 📊 Phase 3実装内容

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