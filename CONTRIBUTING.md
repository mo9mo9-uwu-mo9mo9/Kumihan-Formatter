# CONTRIBUTING.md

Kumihan-Formatter への貢献ガイドライン

## 📋 目次

1. [開発ワークフロー](#-開発ワークフロー)
2. [Pull Request](#-pull-request)
3. [コーディング規約](#-コーディング規約)
4. [テスト・リンター](#-テストリンター)
5. [Pre-commit Hook警告への対応](#pre-commit-hook警告への対応)

**詳細な手順**: [docs/dev/CONTRIBUTING_DETAILED.md](docs/dev/CONTRIBUTING_DETAILED.md)

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

## 🔍 Pull Request

### 基本手順
1. 適切なタイトルでPR作成
2. @claude をレビュアーに指定
3. コミット毎にレビュー依頼コメント
4. 指摘事項への対応
5. 承認後マージ

**詳細手順**: [docs/dev/CONTRIBUTING_DETAILED.md](docs/dev/CONTRIBUTING_DETAILED.md#pr作成の詳細手順)

---

## 💻 コーディング規約

- **Python**: 3.8+ 対応
- **フォーマット**: Black適用
- **型ヒント**: 積極的に使用
- **ドキュメント**: 主要クラスに設計参照コメント付与

---

## 🧪 テスト・リンター

### 🎯 t-wada推奨TDD実践方法

このプロジェクトでは**和田卓人（t-wada）**氏の推奨するテスト駆動開発手法を採用しています。

#### TDD実践手順（新機能開発時）
```bash
# 1. テストリスト作成（手動）
# - 実装予定機能のテストシナリオをリストアップ
# - tests/test_<module>/test_<feature>.py にコメントで記載

# 2. Red-Green-Refactorサイクル開始
# Red: 失敗するテストを作成
python -m pytest tests/test_<新機能>.py::test_<具体的機能> -v

# Green: 最小限の実装でテストを通す
# （実装作業）

# テスト確認
python -m pytest tests/test_<新機能>.py::test_<具体的機能> -v

# Refactor: 設計改善
# （リファクタリング作業）

# 全テスト確認
python -m pytest tests/test_<新機能>.py -v
```

#### 段階的テスト手法の選択
- **新機能開発**: フルTDD（Red-Green-Refactor）推奨
- **バグ修正**: テストファースト（テスト→修正）
- **緊急修正**: 修正後に回帰テスト追加
- **リファクタリング**: 既存テスト活用

### 💡 最低限のチェック項目（必須）

**コミット前に必ず実行してください:**

```bash
# 1. コードフォーマット
black .

# 2. インポート整理
isort .

# 3. 基本的な構文チェック
flake8 --select=E9,F63,F7,F82 .

# 4. 軽量テストチェック（fail-fast）
python -m pytest -x --ff -q tests/
```

### Pre-commit Hook警告への対応

このプロジェクトでは技術的負債を防ぐため、pre-commit hookで以下をチェックしています：

#### ファイルサイズ制限（300行ルール）
- **ファイル**: 300行以内（厳守）
- **クラス**: 100行以内推奨
- **関数**: 20行以内推奨

#### Hook警告が表示された場合の対応

```bash
# 1. エラー内容を確認
python3 scripts/check_file_size.py --max-lines=300

# 2. 違反ファイルの検索
find kumihan_formatter -name "*.py" -exec wc -l {} + | awk '$1 > 300'

# 3. 機能別にファイルを分割
# 例: large_file.py → feature_a.py + feature_b.py + feature_c.py

# 4. 修正後の再確認
python3 scripts/check_file_size.py --max-lines=300
```

**⚠️ 重要**:
- `status code 1`は正常動作です（警告表示）
- **警告は無視しないでください** - 技術的負債の蓄積を防ぐため必ず対応
- Boy Scout Ruleに従って継続的に改善してください

## 🌿 ブランチ戦略

- **`main`**: 安定版（保護ブランチ）
- **`feature/*`**: 新機能開発
- **`fix/*`**: バグ修正
- **`docs/*`**: ドキュメント更新

---

**開発を楽しみましょう！ 🎉**
