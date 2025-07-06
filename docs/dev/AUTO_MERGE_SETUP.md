# 自動マージ設定ガイド

## 概要

mo9mo9-uwu-mo9mo9 ユーザー専用の自動マージ機能を設定しました。

## 🤖 実装済み機能

### 1. 自動マージワークフロー
- **ファイル**: `.github/workflows/auto-merge.yml`
- **対象**: mo9mo9-uwu-mo9mo9 のPRのみ
- **条件**: テスト成功時に自動squashマージ

### 2. 動作条件
- ✅ PRの作成者が `mo9mo9-uwu-mo9mo9`
- ✅ PRがdraftでない
- ✅ テストが成功している
- ✅ PRがマージ可能状態

### 3. 機能詳細

#### 自動コメント
PRオープン時に自動で通知コメントを投稿：
```
🤖 **Auto-merge enabled**

This PR will be automatically merged when all tests pass.

- ✅ Author: mo9mo9-uwu-mo9mo9
- ⏳ Waiting for tests to complete...

*Auto-merge is only available for mo9mo9-uwu-mo9mo9's PRs*
```

#### 自動マージ
- **マージ方式**: squash merge
- **コミットメッセージ**: `PR title (#PR番号)` + `🤖 Auto-merged after successful tests`

#### エラー処理
マージ失敗時は以下のコメントを投稿：
```
🚫 Auto-merge failed: エラーメッセージ

Please merge manually or check for conflicts.
```

## ✅ 設定完了済み

以下の設定は既に自動で適用済みです：

### 1. ブランチ保護ルール ✅ 完了
- **Required status checks**: `quick-check` 必須（Issue #371の設計通り）
- **Strict checks**: ブランチを最新状態に保つ
- **Pull request reviews**: 承認不要（0件）
- **Stale review dismissal**: 有効

### 2. 権限設定 ✅ 完了
- **mo9mo9-uwu-mo9mo9**: Admin権限確認済み

### 3. 個人リポジトリの制限事項
個人リポジトリでは以下の機能は使用できません：
- ❌ Push restrictions (組織専用)
- ❌ Bypass allowances (組織専用)
- ✅ Required status checks (利用可能)
- ✅ Pull request reviews (利用可能)

## 📋 動作確認手順

### 1. テスト用PRの作成
```bash
# 新しいブランチ作成
git checkout -b test/auto-merge-feature

# 簡単な変更を作成
echo "# Auto-merge test" > test-auto-merge.md
git add test-auto-merge.md
git commit -m "test: auto-merge機能テスト"

# プッシュ
git push origin test/auto-merge-feature

# PR作成
gh pr create --title "test: auto-merge機能テスト" --body "自動マージ機能のテストPRです"
```

### 2. 動作確認ポイント
1. ✅ PRオープン時にauto-mergeコメントが投稿される
2. ✅ テスト完了後に自動でマージされる
3. ✅ マージコミットメッセージに🤖マークが付く

### 3. 他ユーザーでの確認
他のユーザーがPRを作成した場合：
- ❌ auto-mergeコメントは投稿されない
- ❌ 自動マージは実行されない
- ✅ 通常の手動マージのみ可能

## 🚨 トラブルシューティング

### Q: 自動マージが動作しない
**A: 以下を確認してください**
1. PRの作成者が `mo9mo9-uwu-mo9mo9` か？
2. テストが全て成功しているか？
3. PRがdraftでないか？
4. ブランチ保護ルールが正しく設定されているか？

### Q: テストが失敗した場合
**A: 通常の開発フロー**
1. 失敗したテストを修正
2. 新しいコミットをプッシュ
3. テスト成功後、自動マージが実行される

### Q: マージ競合が発生した場合
**A: 手動解決が必要**
1. ローカルでmainブランチをマージ
2. 競合を解決してプッシュ
3. テスト成功後、自動マージが実行される

## 🔄 無効化方法

自動マージを一時的に無効にしたい場合：

### 1. ワークフロー無効化
```bash
# ワークフローファイルを一時的にリネーム
mv .github/workflows/auto-merge.yml .github/workflows/auto-merge.yml.disabled
```

### 2. 特定PRでの無効化
PRタイトルまたは本文に以下を含める：
```
[skip auto-merge]
```
（現在の実装では未対応、将来的な拡張で追加予定）

## 📈 今後の拡張予定

### 短期改善
- [ ] `[skip auto-merge]` ラベルサポート
- [ ] マージ前の最終確認コメント
- [ ] より詳細なエラーレポート

### 中期改善
- [ ] 複数ユーザーサポート（設定ファイル化）
- [ ] カスタムマージメッセージテンプレート
- [ ] 条件付き自動マージ（特定ファイル変更時のみ等）

### 長期改善
- [ ] Slack/Discord通知連携
- [ ] マージ統計レポート
- [ ] A/Bテスト対応自動マージ

---

**設定完了後は、このPR自体も自動マージのテストケースとして機能します！**
