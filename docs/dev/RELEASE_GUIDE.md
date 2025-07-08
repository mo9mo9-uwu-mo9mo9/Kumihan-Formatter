# リリースガイド

> Kumihan-Formatter のリリース手順書
> **目的**: 正確なリリースプロセスの実行
> **バージョン**: 1.0.0 (2025-07-08)

## 🔒 重要な前提条件

- **mainブランチは保護されている**: 直接プッシュ不可
- **全変更はPR経由**: バージョン変更も含む
- **オートマージ必須**: `gh pr merge PR番号 --auto --merge`
- **正式リリースは要許可**: v1.0.0以上は明示的許可必須

## 📋 リリース手順

### 1. 事前準備

```bash
# 最新の状態に更新
git checkout main
git pull origin main

# 現在のバージョンを確認
git tag --list "v*" | sort -V | tail -5
```

### 2. バージョン変更（PR経由）

```bash
# リリースブランチを作成
git checkout -b release/v0.9.0-alpha.X

# バージョン番号を更新
# - pyproject.toml の version
# - kumihan_formatter/__init__.py の __version__

# 変更をコミット
git add -A
git commit -m "release: bump version to v0.9.0-alpha.X"

# PRを作成
gh pr create --title "release: v0.9.0-alpha.X" --body "$(cat <<'EOF'
## Summary
- バージョン番号を v0.9.0-alpha.X に更新

## Changes
- pyproject.toml: version更新
- kumihan_formatter/__init__.py: __version__更新

## Test plan
- [ ] make test でテスト実行
- [ ] バージョン番号の一致確認

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"

# 🚨 重要: オートマージ設定（必須）
gh pr merge PR番号 --auto --merge
```

### 3. マージ完了後のタグ作成

```bash
# PRマージ完了を確認
git checkout main
git pull origin main

# テスト実行（推奨）
make test

# リリースタグを作成
git tag v0.9.0-alpha.X

# タグをプッシュ
git push origin v0.9.0-alpha.X
```

### 4. リリース完了確認

```bash
# タグが作成されたか確認
git tag --list "v0.9.0-alpha.X"

# リモートにタグがプッシュされたか確認
git ls-remote --tags origin | grep v0.9.0-alpha.X
```

## 🔄 リリースタイプ別手順

### αリリース（アルファ版）

- **命名規則**: `v0.9.x-alpha.x`
- **用途**: テスト・改善用
- **制約**: 特になし
- **テスト**: `make test`で基本確認

### 正式リリース

- **命名規則**: `v1.0.0`以上
- **用途**: 本番利用
- **制約**: **ユーザーの明示的許可が必須**
- **テスト**: 全テストスイート実行

## ❌ よくある失敗パターン

### 1. mainブランチへの直接プッシュ
```bash
# ❌ 失敗例
git push origin main

# ✅ 正しい方法
# PR経由でのみ変更
```

### 2. オートマージ設定の忘れ
```bash
# ❌ 失敗例
gh pr create --title "..."

# ✅ 正しい方法
gh pr create --title "..."
gh pr merge PR番号 --auto --merge
```

### 3. バージョン変更のローカル保持
```bash
# ❌ 失敗例
# ローカルでバージョン変更 → タグ作成

# ✅ 正しい方法
# PR経由でバージョン変更 → マージ後にタグ作成
```

## 🛠️ トラブルシューティング

### PRマージ前のタグ作成エラー
```bash
# 問題: バージョン変更がリモートに反映されていない
# 解決: PRマージ完了を待つ
gh pr status
git pull origin main
```

### 保護されたブランチエラー
```bash
# エラー: remote rejected main -> main (protected branch)
# 解決: PR経由で変更
gh pr create --title "..." --body "..."
```

### タグの重複エラー
```bash
# エラー: tag 'v0.9.0-alpha.X' already exists
# 解決: タグを削除して再作成
git tag -d v0.9.0-alpha.X
git push origin :refs/tags/v0.9.0-alpha.X
git tag v0.9.0-alpha.X
git push origin v0.9.0-alpha.X
```

## 📚 関連ドキュメント

- [CLAUDE.md](../../CLAUDE.md) - オートマージ設定
- [PACKAGING.md](../PACKAGING.md) - パッケージング手順
- [CHANGELOG.md](../../CHANGELOG.md) - 変更履歴
- [AUTO_MERGE_SETUP.md](AUTO_MERGE_SETUP.md) - オートマージ詳細

## 🎯 チェックリスト

### リリース前
- [ ] テストが通る（`make test`）
- [ ] バージョン番号の整合性確認
- [ ] CHANGELOGの更新（必要に応じて）

### リリース実行
- [ ] リリースブランチ作成
- [ ] バージョン番号更新
- [ ] PR作成
- [ ] オートマージ設定
- [ ] マージ完了確認

### リリース後
- [ ] タグ作成・プッシュ
- [ ] リモートタグ確認
- [ ] 必要に応じて通知

---

**重要**: このガイドは mainブランチ保護とオートマージ設定を前提としています。設定変更時は本ドキュメントも更新してください。
