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

## 🔧 手動設定が必要な項目

自動マージを完全に機能させるために、以下の設定をGitHub Web UIで行ってください：

### 1. ブランチ保護ルール設定

リポジトリの **Settings > Branches** で以下を設定：

```
Branch name pattern: main

✅ Restrict pushes that create files
✅ Require a pull request before merging
   - Required number of approvals: 0
   - Dismiss stale PR approvals when new commits are pushed: ☑️
   - Require review from code owners: ☐
   - Restrict reviews to users with write access: ☐
   - Allow specified actors to bypass required pull requests:
     👤 mo9mo9-uwu-mo9mo9

✅ Require status checks to pass before merging
   - Require branches to be up to date before merging: ☑️
   - Status checks that are required:
     - Tests / quick-check
     - Tests / full-test

✅ Restrict pushes
   - People with push access: 👤 mo9mo9-uwu-mo9mo9

☐ Require conversation resolution before merging
☐ Require signed commits
☐ Require linear history
☐ Require deployments to succeed before merging
☐ Lock branch
☐ Do not allow bypassing the above settings
```

### 2. 権限設定確認

**Settings > Collaborators and teams** で確認：
- mo9mo9-uwu-mo9mo9: Admin または Write 権限

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
