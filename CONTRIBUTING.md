# CONTRIBUTING.md

Kumihan-Formatter への貢献ガイドライン

## 📋 目次

1. [開発ワークフロー](#-開発ワークフロー)
2. [作業種別と手順](#-作業種別と手順)
3. [Pull Request](#-pull-request)
4. [Issue管理](#-issue管理)
5. [コーディング規約](#-コーディング規約)
6. [リンター](#-リンター)

---

## 🔄 開発ワークフロー

### 基本フロー

**Issue駆動開発**（推奨）

1. Issue確認 → 作業中ラベル → ブランチ作成 → 実装 → PR作成・マージ → Issue完了報告

**作業規模による違い**：
- 小規模: 直接mainブランチで作業
- 中〜大規模: ブランチ作成 → 実装 → PR作成・マージ

---

## 🛠️ 作業種別と手順

### 1. Issue駆動開発（推奨）

新機能・バグ修正など、ほとんどの作業でこの手法を使用。

1. **Issue作成・確認**
   - 既存Issueを確認、または新規Issue作成
   - `in progress` ラベルを付与（作業開始を表明）

2. **ブランチ作成**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b fix/issue-{番号}-{概要}
   # または
   git checkout -b feature/issue-{番号}-{概要}
   ```

3. **実装**
   コードを実装します。

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

  # 直接コミット・プッシュ
  git add .
  git commit -m "docs: タイポ修正"
  git push origin main
  ```

#### 中規模変更（ブランチ使用）
- **条件**: 複数ファイル変更、新機能追加、設計変更を伴う修正

---

## 📤 Pull Request

### PR作成時のチェックリスト

- [ ] Issue番号を含むタイトル（例: `fix: Issue #123 記法パーサーのバグ修正`）
- [ ] `Closes #123` をPR本文に記載
- [ ] 変更内容を簡潔に記述
- [ ] 影響範囲を記載

### 📋 PRテンプレート

```markdown
## 概要
Issue #XXX の修正

## 変更内容
- xxx

## 影響範囲
- xxx

## その他
- xxx

Closes #XXX
```

---

## 📋 Issue管理

### Issue作成ガイドライン

**Bug Report**:
```markdown
## 問題の概要
xxx

## 再現手順
1. xxx
2. xxx

## 期待する動作
xxx

## 実際の動作
xxx

## 環境
- OS: xxx
- Python: xxx
- バージョン: xxx
```

**Feature Request**:
```markdown
## 機能の概要
xxx

## 必要な理由
xxx

## 実装案（あれば）
xxx
```

### ラベル管理

- `bug`: バグ修正
- `enhancement`: 新機能・改善
- `documentation`: ドキュメント関連
- `in progress`: 作業中
- `priority-high`: 高優先度

---

## 📝 コーディング規約

### 基本ルール
- **言語**: Python 3.12+
- **フォーマッター**: Black（88文字制限）
- **インポート整理**: isort
- **リンター**: flake8, mypy
- **型ヒント**: 必須（mypy strict対応）

### ファイル構成
```
kumihan_formatter/
├── core/           # コア機能
├── cli.py          # CLIエントリーポイント
├── commands/       # CLIコマンド
└── ...
```

### 命名規則
- **関数・変数**: `snake_case`
- **クラス**: `PascalCase`
- **定数**: `UPPER_CASE`
- **プライベート**: `_leading_underscore`

---

## 🧪 リンター

### 💡 最低限のチェック項目（必須）

**コミット前に必ず実行してください:**

```bash
# コード品質チェック
make lint
```

### 📋 利用可能コマンド

```bash
make setup       # 開発環境セットアップ
make lint        # コード品質チェック
make clean       # 一時ファイル削除
```

---

## 🌏 日本語レビュー必須規則

**重要**: このプロジェクトでは **日本語でのレビューを義務付け** しています。

### ✅ 推奨レビュー例
```
変更内容を確認しました。以下の点についてコメントします：

1. エラーハンドリングが適切に実装されています
2. ドキュメントも更新されており、完成度が高いです
3. テストケースの追加を検討してはいかがでしょうか

全体的に良い実装だと思います。LGTM!
```

### ❌ 禁止事項
- 英語でのレビューコメント
- 自動翻訳ツールを使った機械的な日本語
- レビューなしでのマージ

### 理由
- プロジェクトメンバーの理解促進
- 日本語コミュニティでの知識共有
- コミュニケーションの円滑化

---

## 🤝 サポート

質問やサポートが必要な場合：
- **バグ報告**: [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **機能要望**: [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **ディスカッション**: [Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)

---

**Happy Contributing! 🎉**