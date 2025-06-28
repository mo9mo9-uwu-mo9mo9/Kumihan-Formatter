# GitHub Actions ワークフローステータス

最終更新: 2025-06-28 (Phase 3実装)

## 🚦 ワークフローステータス一覧

| ワークフロー | ステータス | トリガー | 説明 |
|------------|----------|--------|------|
| **quality-monitoring.yml** | ✅ 有効 | push (main, develop, feature/**, fix/**), pull_request | 品質メトリクス収集・分析 |
| **enhanced-quality-check.yml** | ✅ 有効 | push/pull_request (特定パス変更時) | 詳細な記法検証・パフォーマンステスト |
| **ci.yml** | ✅ 有効 | push/pull_request (main) | 基本的な機能テスト |
| **ci-full.yml** | ✅ 有効 | push/pull_request (main) | 完全なテストスイート実行 |
| **sample-syntax-check.yml** | ✅ 有効 | push/pull_request (サンプルファイル変更時) | サンプルファイル記法チェック |
| **coverage.yml** | ✅ 有効 | push (main) | テストカバレッジ測定 |
| **docs-check.yml** | ✅ 有効 | push/pull_request (ドキュメント変更時) | ドキュメント整合性チェック |
| **docs-validation.yml** | ✅ 有効 | push/pull_request (ドキュメント変更時) | ドキュメント検証 |
| **doc-consistency-check.yml** | ✅ 有効 | push/pull_request (ドキュメント変更時) | ドキュメント一貫性チェック |
| **emoji-check.yml** | ✅ 有効 | push/pull_request | 絵文字使用チェック |
| **auto-update.yml** | ✅ 有効 | schedule (毎週月曜), workflow_dispatch | 自動アップデート |
| **e2e-tests.yml** | ⏸️ 無効 | workflow_dispatch のみ | E2Eテスト（再構築中） |
| **e2e-tests-minimal.yml** | ⏸️ 無効 | workflow_dispatch のみ | 最小限E2Eテスト（再構築中） |

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