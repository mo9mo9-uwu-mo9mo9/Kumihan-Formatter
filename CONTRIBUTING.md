# CONTRIBUTING.md

Kumihan-Formatter への貢献ガイドライン

## 📋 目次

1. [開発ワークフロー](#-開発ワークフロー)
2. [作業種別と手順](#-作業種別と手順)
3. [Pull Request](#-pull-request)
4. [Issue管理](#-issue管理)
5. [コーディング規約](#-コーディング規約)
6. [テスト・リンター](#-テストリンター)

---

## 🔄 開発ワークフロー

### 基本フロー

**Issue駆動開発**（推奨）
1. Issue確認 → 作業中ラベル → ブランチ作成 → 実装・テスト → PR作成・マージ → Issue完了報告

**直接作業**
- 小規模: mainブランチで直接作業 → コミット・プッシュ
- 中〜大規模: ブランチ作成 → 実装・テスト → PR作成・マージ

### 作業完了の定義

**基本原則**: すべての作業において **コミット・プッシュまでが最低限の作業完了**

| 作業種別 | 作業完了の条件 | Issue完了報告タイミング |
|---------|---------------|---------------------|
| **Issue駆動開発（PR経由）** | コミット・プッシュ + PR作成・マージ + Issue完了報告・クローズ | **PRマージ後** |
| **Issue駆動開発（直接main）** | コミット・プッシュ + Issue完了報告・クローズ | **コミット・プッシュ後** |
| **直接作業（小規模）** | コミット・プッシュ | なし |
| **直接作業（中〜大規模）** | コミット・プッシュ + PR作成・マージ | なし |

**⚠️ 重要**: Issue完了報告は必ず **コミット・プッシュ後**（PR経由の場合は**マージ後**）に実施してください。コミット前の完了報告は手順違反です。

---

## 📝 作業種別と手順

### 1. Issue駆動開発（推奨）

新機能・バグ修正・大規模変更は必ずIssue駆動で行ってください。

#### 手順
1. **Issue確認・分析**
   - 既存Issueの確認、または新規Issue作成
   - 作業内容と範囲の明確化

2. **作業開始**
   ```bash
   # 作業中ラベル付与
   gh issue edit {ISSUE_NUMBER} --add-label "作業中"

   # ブランチ作成
   git checkout -b fix/issue-{番号}-{概要}
   # または
   git checkout -b feature/issue-{番号}-{概要}
   ```

3. **実装・テスト**
   - コード実装

4. **完了処理**
   ```bash
   # コミット・プッシュ
   git add .
   git commit -m "fix: Issue #XXX の概要"
   git push -u origin ブランチ名

   # PR作成
   gh pr create --title "タイトル" --body "Closes #XXX"

   # レビュー・マージ
   # Issue完了報告・クローズ
   ```

### 2. 直接作業

緊急修正や小規模な変更の場合。

#### 小規模変更（直接mainブランチOK）
- **条件**: タイポ修正、簡単なドキュメント更新、1ファイル・数行程度の変更
- **手順**:
  ```bash
  # mainブランチで直接作業
  git checkout main
  git pull origin main
  # 変更作業
  git add .
  git commit -m "docs: タイポ修正"
  git push origin main
  ```

#### 中〜大規模変更（ブランチ作業）
- **条件**: 複数ファイル変更、機能追加、リファクタリング
- **手順**: Issue駆動開発と同様（Issueなしでブランチ作成・PR）

---

## 🔍 Pull Request

### 作成タイミング
- **必須**: Issue駆動開発、中〜大規模変更
- **任意**: 小規模な直接作業

### PR作成手順

```bash
gh pr create --title "適切なタイトル" --body "$(cat <<'EOF'
## Summary
変更内容の概要

## Changes
- 変更点1
- 変更点2

## Test plan
- [ ] テスト項目1
- [ ] テスト項目2

Closes #XXX (該当する場合)
EOF
)"
```

### レビューコメントの記載方法

**詳細なレビューガイド**: [PR_REVIEW_GUIDE.md](docs/dev/PR_REVIEW_GUIDE.md) を参照

---

## 📋 Issue管理

### ラベル管理

#### Issue作成時
- **Issue作成直後**: 内容に応じて適切なラベルを付与
- **詳細なラベル管理**: [LABEL_GUIDE.md](docs/dev/LABEL_GUIDE.md) を参照

#### 作業段階別ラベル
- **作業開始時**: 「作業中」ラベル付与
- **作業完了時**: 「完了待ち」ラベル付与
- **完全終了時**: Issueクローズ

### Issue完了報告

**Issue完了報告テンプレート**: [ISSUE_TEMPLATE.md](docs/dev/ISSUE_TEMPLATE.md) を参照

---

## 💻 コーディング規約

- **Python**: 3.8+ 対応
- **フォーマット**: Black適用
- **型ヒント**: 積極的に使用
- **ドキュメント**: 主要クラスに設計参照コメント付与

### コミット前クリーンアップ

**クリーンアップ詳細**: [QUALITY_GUIDE.md](docs/dev/QUALITY_GUIDE.md) を参照

---

## 🧪 テスト・リンター

### 💡 最低限のチェック項目（必須）

**コミット前に必ず実行してください:**

```bash
# 1. コードフォーマット
black .

# 2. インポート整理
isort .

# 3. 基本的な構文チェック
flake8 --select=E9,F63,F7,F82 .

# 4. 軽量テストチェック
python -m pytest -x --ff -q tests/
```

### ⚡ 軽量チェック（推奨）

```bash
# pre-commitフックを使用（軽量版）
pre-commit run

# または手動で軽量チェック
make check
```

### 🚀 フルチェック（PR前推奨）

```bash
# 重いチェックも含む（PR作成前に実行）
SKIP=heavy-checks pre-commit run --all-files

# またはフルテストスイート
make test-full
```

### 📊 段階的チェック体制（Issue #371対応）

**push時（軽量）**:
- ✅ flake8基本チェック
- ✅ black/isortフォーマット
- ✅ 高速テスト（fail-fast）

**PR時（フル）**:
- ✅ 全OS・Python版でのテスト
- ✅ カバレッジ計測
- ✅ アーキテクチャ原則チェック
- ✅ 複雑度・ファイルサイズチェック

### 🔧 開発者向けコマンド

```bash
# 基本的な開発サイクル
make format      # フォーマット適用
make lint        # 軽量チェック
make test        # テスト実行

# 高度なチェック
make coverage    # カバレッジ付きテスト
make pre-commit  # コミット前フルチェック

# テスト実行（新しい統一設定）
pytest           # 全テスト実行（pyproject.tomlの設定を使用）
pytest -m unit   # ユニットテストのみ
pytest -m integration # 統合テストのみ
pytest -m e2e    # E2Eテストのみ
```

### 📝 テスト設定の変更

- **pytest.ini** は廃止され、**pyproject.toml** に統一されました
- GitHub Actions と ローカル環境でテストコマンドが統一されました
- マーカーを使用したテスト分類が可能になりました

### ⚠️ CI失敗時の対処

1. **ローカルで再現**: `make test-full`
2. **段階的修正**: 軽量チェック → フルチェック
3. **ヘルプ**: Issue作成またはDiscussion利用

### ドキュメント更新
- 変更内容は `CHANGELOG.md` に記録
- API変更時は `docs/` と `README.md` を更新

---

## 🌿 ブランチ戦略

- **`main`**: 安定版（保護ブランチ）
- **`feature/*`**: 新機能開発
- **`fix/*`**: バグ修正
- **`docs/*`**: ドキュメント更新

**重要**: mainブランチは保護されているため、大規模変更は必ずブランチ作成→PR経由で行ってください。

---

**開発を楽しみましょう！ 🎉**
