# ブランチ保護設定ガイド

> GitHub Actionsと連携したブランチ保護設定\
> **目的**: メインブランチの品質保証を強制\
> **対象**: リポジトリ管理者・メンテナー

## 🚨 なぜブランチ保護が必要か

### 問題点
- **CI/CDバイパス**: 直接プッシュでGitHub Actionsをスキップ可能
- **品質劣化リスク**: pre-commit hookとCI/CDを両方回避される危険性
- **技術的負債蓄積**: 300行制限・アーキテクチャチェックの強制力不足

### 解決策
GitHub Actionsの品質チェックを**必須**にして、全てのコード変更を強制的にチェック

## 📋 推奨ブランチ保護設定

### 基本設定
```
対象ブランチ: main
- Restrict pushes that create files: 有効
- Require a pull request before merging: 有効
- Require status checks to pass before merging: 有効
```

### 必須ステータスチェック
以下のGitHub Actionsチェックを**必須**に設定：

```yaml
必須チェック項目:
✅ quality-check / quality-check
```

### 詳細設定
```yaml
Branch Protection Rules:
  Branch name pattern: main

  Settings:
    ✅ Require a pull request before merging
        - Require approvals: 1
        - Dismiss stale reviews: 有効
        - Require review from code owners: 有効

    ✅ Require status checks to pass before merging
        - Require branches to be up to date: 有効
        - Status checks found in the last week:
          - quality-check / quality-check

    ✅ Require conversation resolution before merging

    ✅ Restrict pushes that create files
        - Restrict pushes that create files larger than 100 MB: 有効

    ✅ Require signed commits: 有効（推奨）

    ❌ Allow force pushes: 無効
    ❌ Allow deletions: 無効
```

## 🔧 設定手順

### 1. GitHub Web UIでの設定

1. **リポジトリ設定を開く**
   ```
   GitHub リポジトリ → Settings → Branches
   ```

2. **Branch protection rule を追加**
   ```
   Branch name pattern: main
   ```

3. **必須チェック項目を設定**
   ```
   Status checks found in the last week で以下を選択:
   - quality-check / quality-check
   ```

### 2. GitHub CLI での設定（自動化）

```bash
# ブランチ保護ルール作成
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["quality-check / quality-check"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### 3. 設定確認

```bash
# 設定確認
gh api repos/{owner}/{repo}/branches/main/protection
```

## 💡 効果とメリット

### 開発フローの改善
```
従来: 開発者 → 直接main push → デプロイ
改善: 開発者 → PR作成 → CI/CD必須通過 → レビュー → マージ
```

### 品質保証の強化
- **300行制限**: 必ず守られる
- **アーキテクチャチェック**: 違反時はマージ不可
- **型安全性**: mypy strict必須
- **テスト**: 全テスト通過必須

### 技術的負債の予防
- **Boy Scout Rule**: 強制的に適用
- **段階的改善**: PR単位で確実に改善
- **品質低下防止**: 劣化コードの混入阻止

## 🚨 緊急時の対応

### 管理者権限での緊急マージ
```bash
# 緊急時のみ使用（非推奨）
gh pr merge {PR_NUMBER} --admin --merge
```

### 一時的な保護無効化
```bash
# 緊急時のみ（使用後は必ず再有効化）
gh api repos/{owner}/{repo}/branches/main/protection \
  --method DELETE
```

## 📊 監視・メトリクス

### 品質指標の追跡
- **PR通過率**: quality-check成功率
- **修正回数**: PR作成からマージまでの修正回数
- **レビュー時間**: レビュー完了までの時間

### アラート設定
```yaml
監視対象:
- CI/CD失敗率の急上昇
- 品質チェック回避の試行
- 大量のファイルサイズ違反
```

## 🔄 継続的改善

### 設定の見直し
- **3ヶ月ごと**: 効果測定と設定調整
- **新規チェック追加**: 品質基準の向上
- **チーム規模対応**: 承認者数の調整

---

**注意**: この設定により、main ブランチへの直接プッシュは完全に禁止されます。全ての変更は必ずPRとCI/CDチェックを通過する必要があります。
