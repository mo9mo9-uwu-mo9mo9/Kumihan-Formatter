# テスト保護ガイド

> **目的**: テストファイルの大量削除防止と安全な開発環境の構築
> **バージョン**: 1.0.0 (2025-01-19)

## 背景

Issue #518のPR #523で発生したテスト大量削除問題（55ファイル、-12,685行）を受けて、テスト保護機能を実装しました。

### 問題の根本原因
1. **コミット4606d0b**で意図しないテストファイル削除が発生
2. GUIコントローラー分割作業中に重要テストが含まれた
3. 手動での復旧作業が必要となった

## テスト保護機能

### 1. Test Guard スクリプト

**場所**: `scripts/test_guard.py`

**機能**:
- コミット前のテスト削除チェック
- 自動テストバックアップ
- 保護対象ファイルの削除防止
- 削除閾値チェック

```bash
# 使用例
python scripts/test_guard.py --check-staged   # ステージング変更チェック
python scripts/test_guard.py --backup-tests   # テストバックアップ作成
python scripts/test_guard.py --status         # 保護状況確認
```

### 2. 保護設定

```python
protection_config = {
    "max_deletions_allowed": 3,           # 最大削除許可数
    "min_test_files_required": 20,        # 最小必須テストファイル数
    "protected_patterns": [               # 削除禁止パターン
        "test_config_manager.py",
        "test_error_handling.py",
        "test_conversion_controller.py",
        "test_file_controller.py",
        "test_gui_controller.py"
    ],
    "deletion_warning_threshold": 1       # 警告閾値
}
```

### 3. Pre-commit Hook統合

**設定ファイル**: `.pre-commit-config-test-protection.yaml`

**自動実行機能**:
- テスト削除チェック
- 自動バックアップ作成
- 品質ゲート連携

## 運用ガイド

### 開発者向け

#### 1. 事前準備
```bash
# テスト保護機能の有効化
cp .pre-commit-config-test-protection.yaml .pre-commit-config.yaml
pre-commit install

# 現在の状況確認
python scripts/test_guard.py --status
```

#### 2. 安全な開発フロー
```bash
# 1. 作業前バックアップ
python scripts/test_guard.py --backup-tests

# 2. 開発作業
# ... コード変更 ...

# 3. コミット前チェック
git add .
python scripts/test_guard.py --check-staged

# 4. 問題なければコミット
git commit -m "feat: 安全な変更"
```

#### 3. テスト削除が必要な場合
```bash
# 1. 意図的削除の場合
# protection_config の設定を一時的に調整

# 2. 保護ファイル削除の場合
# メンテナー(mo9mo9)への相談が必要

# 3. 大量削除の場合
# 段階的削除で閾値以下に抑制
```

### メンテナー向け

#### 1. 保護設定の更新
```python
# scripts/test_guard.py の protection_config を編集
# 新規重要テストファイルの追加
# 閾値の調整
```

#### 2. バックアップ管理
```bash
# バックアップ一覧確認
ls -la .test_backups/

# 古いバックアップの清理
find .test_backups -name "backup_*" -mtime +30 -exec rm -rf {} \;
```

## 再発防止対策

### 1. 技術的対策
- ✅ **Test Guard スクリプト**: 自動削除検知
- ✅ **Pre-commit Hook**: コミット前検証
- ✅ **自動バックアップ**: 変更前の安全保障
- ✅ **保護パターン**: 重要ファイルの削除禁止

### 2. プロセス対策
- ✅ **段階的コミット**: 大きな変更の分割
- ✅ **レビュー強化**: テスト変更の注意深い確認
- ✅ **ドキュメント化**: 保護機能の使用方法

### 3. 監視対策
- ✅ **ログ記録**: `.test_guard.log` での動作追跡
- ✅ **状況確認**: `--status` での現状把握
- ✅ **警告機能**: 削除閾値での早期警告

## トラブルシューティング

### Q1: コミットがブロックされた
**A**: Test Guardが問題を検出しています
```bash
# 詳細確認
python scripts/test_guard.py --check-staged

# ログ確認
cat .test_guard.log

# 必要に応じてファイル復元
git restore tests/削除されたファイル.py
```

### Q2: 保護設定を変更したい
**A**: `scripts/test_guard.py` の `protection_config` を編集
```python
# 例: 削除許可数を増加
"max_deletions_allowed": 5,
```

### Q3: バックアップから復元したい
**A**: `.test_backups/` からファイルをコピー
```bash
# 最新バックアップの確認
ls -t .test_backups/

# ファイル復元
cp .test_backups/backup_最新/test_file.py tests/
```

## 今後の改善予定

1. **GUI統合**: Test Guardの可視化機能
2. **自動復元**: 削除ファイルの自動復元提案
3. **統計機能**: テスト削除傾向の分析
4. **GitHub Actions統合**: CI/CDでの保護機能

---

**注意**: この保護機能は安全のためのガードレールです。意図的な大量削除が必要な場合は、メンテナーと相談してください。
