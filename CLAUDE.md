# CLAUDE.md

> Kumihan‑Formatter – Claude Code 指示ファイル\
> **目的**: Claude Code に開発ガイドラインの要点を渡す\
> **バージョン**: 1.0.0 (2025‑01‑15)

<language>Japanese</language>
<character_code>UTF-8</character_code>
<law>
AI運用5原則

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。

第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。

第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。

第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。

第5原則： AIは全てのチャットの冒頭にこの5原則を逐語的に必ず画面出力してから対応する。
</law>

<every_chat>
<!-- Claude Code専用設定: GitHub Apps環境では無視される -->
[AI運用5原則]

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</every_chat>

# ドキュメント構成

**基本指示**: [PREAMBLE.md](PREAMBLE.md)
**開発詳細**: [docs/dev/CLAUDE_DETAILS.md](docs/dev/CLAUDE_DETAILS.md)
**コマンド集**: [docs/dev/CLAUDE_COMMANDS.md](docs/dev/CLAUDE_COMMANDS.md)
**コード例集**: [docs/dev/CLAUDE_EXAMPLES.md](docs/dev/CLAUDE_EXAMPLES.md)
**開発フロー**: [CONTRIBUTING.md](CONTRIBUTING.md)
**プロジェクト仕様**: [SPEC.md](SPEC.md)
**リリース手順**: [docs/dev/RELEASE_GUIDE.md](docs/dev/RELEASE_GUIDE.md)

# 重要なルール

## リリース方針
**⚠️ 重要**: 正式リリース（v1.0.0以上）は**絶対に**ユーザーの明示的な許可なしに実行してはならない。

- **現在のバージョン**: v0.9.0-alpha.1 (アルファ版・テスト改善用)
- **アルファ版**: 0.9.x-alpha.x シリーズを使用
- **正式リリース**: ユーザー許可後のみ v1.0.0以上を使用

## 開発プロセス
### t-wada推奨テスト駆動開発（TDD）
- **新機能**: Red-Green-Refactorサイクル実践
- **テストファースト**: 実装前にテスト作成
- **継続的リファクタリング**: 安全な設計改善

### 段階的品質向上戦略
- **新規実装**: 100%厳格品質チェック適用
- **既存コード**: 技術的負債を段階的に解決
- **レガシー除外**: `technical_debt_legacy_files.txt`で管理
- **段階的移行**: 既存ファイルは修正時に品質基準適用

### Pull Request必須ルール
- **Claude自動レビュー**: PR作成時に自動でClaude Codeレビュー実行
- **オートマージ専用**: レビュー完了後、CI/CD通過でマージ
- **品質保証**: GitHub Actions品質チェック + Claudeレビューの二重チェック

### Claude自動レビュー体制（新導入）
- **実行タイミング**: PR作成・更新時に自動実行
- **レビュー観点**: コード品質・アーキテクチャ・セキュリティ・パフォーマンス・テスト・文書化
- **ワークフロー**: `.github/workflows/claude-review.yml`
- **ラベル**: `review-requested`、`claude-review`を自動付与

### ブランチ保護設定（重要）
- **main ブランチ直接プッシュ禁止**: 全ての変更はPR経由必須
- **CI/CD必須通過**: GitHub Actions品質チェック必須
- **設定ガイド**: [docs/dev/BRANCH_PROTECTION.md](docs/dev/BRANCH_PROTECTION.md)
- **自動設定**: `scripts/setup_branch_protection.sh`実行

## コーディング規約
- **Python**: 3.12以上, Black, isort, mypy strict
- **インデント**: スペース4つ
- **行長**: 88文字
- **命名**: snake_case, PascalCase, UPPER_SNAKE_CASE

## 技術的負債予防ルール（Issue #476対応）
### 📏 300行ルール（厳守）
- **ファイル**: 300行以内（例外なし）
- **クラス**: 100行以内推奨
- **関数**: 20行以内推奨
- **⚠️ 違反時**: pre-commit hookが自動でブロック

### 🏗️ アーキテクチャ原則
- **Single Responsibility Principle**: 1ファイル1責任
- **関数分割**: 複雑な処理は機能単位で分離
- **Boy Scout Rule**: コードを触ったら少しでも改善
- **循環依存**: 禁止（アーキテクチャチェックで検出）

### 🔧 自動チェック体制
```bash
# コミット時自動実行（pre-commit hook）
scripts/check_file_size.py      # ファイルサイズチェック
scripts/architecture_check.py   # アーキテクチャ品質チェック

# 手動実行（必要時のみ）
.venv/bin/python scripts/check_file_size.py
.venv/bin/python scripts/architecture_check.py
```

### ⚠️ pre-commit hookエラー対応
Claude Code使用時に以下のメッセージが表示される場合：
```
PreToolUse:Bash [~/.claude/hook_pre_commands.sh] failed with
non-blocking status code 1: No stderr output
```

**これは正常動作です。** status code 1は非ブロッキングエラーで、技術的負債の警告を表示しています。

#### 📋 対応手順
1. **エラー内容を確認**
   ```bash
   python3 scripts/check_file_size.py --max-lines=300
   ```

2. **300行制限違反の修正**
   - ファイルを機能別に分割
   - Single Responsibility Principleに従う
   - 大きな関数・クラスを小さく分割

3. **修正例**
   ```bash
   # 違反ファイルの確認
   find kumihan_formatter -name "*.py" -exec wc -l {} + | awk '$1 > 300'

   # 分割実行（例）
   # large_file.py → feature_a.py + feature_b.py + feature_c.py
   ```

4. **修正後の確認**
   ```bash
   python3 scripts/check_file_size.py --max-lines=300
   # ✅ 違反件数が減少していることを確認
   ```

#### 🚨 重要
- **status code 1は処理継続**: エラーではなく警告
- **無視しない**: 技術的負債の蓄積を防ぐため必ず対応
- **継続的改善**: Boy Scout Ruleに従って少しずつ改善

# プロジェクト構造

```
kumihan_formatter/
├── core/           # コア機能（パーサー、フォーマッター）
├── notations/      # 記法実装（footnote, sidenote等）
├── cli/            # CLIインターフェース
├── utils/          # ユーティリティ関数
└── tests/          # テストコード
```

## 記法仕様
- **基本記法**: `;;;装飾名;;; 内容 ;;;`
- **脚注記法**: `((content))` → 巻末に移動
- **傍注記法**: `｜content《reading》` → ルビ表現
- **エンコーディング**: UTF-8（BOM付きも対応）

# 基本コマンド

```bash
make test          # テスト実行
make lint          # リントチェック
make pre-commit    # コミット前の全チェック実行

# 基本的な変換
kumihan convert input.txt output.txt

# 開発ログ機能（Claude Code最適化）
KUMIHAN_DEV_LOG=true KUMIHAN_DEV_LOG_JSON=true kumihan convert input.txt output.txt
```

詳細なコマンドとオプションは [docs/dev/CLAUDE_COMMANDS.md](docs/dev/CLAUDE_COMMANDS.md) を参照。

# 🚨 Claude Code 品質ゲート（絶対遵守）

## 実装前必須チェック

**Claude Code は実装作業前に以下を必ず実行すること：**

```bash
# 品質ゲートチェック（必須）
python scripts/claude_quality_gate.py

# 失敗した場合の修正
make pre-commit
```

## 🔒 絶対ルール（違反禁止）

### 1. **mypy strict mode は絶対必須**
- `SKIP=mypy-strict` の使用は**絶対禁止**
- 型エラーが1個でもあるとコミット不可
- 実装前に必ず型安全性を確保

### 2. **TDD（テスト駆動開発）の強制**
- **実装前にテストを書く**（Red-Green-Refactor）
- テストが存在しない機能の実装は禁止
- `python scripts/enforce_tdd.py kumihan_formatter/` で確認

### 3. **品質チェック通過必須**
- Black, isort, flake8 の完全通過
- 全テストの成功
- アーキテクチャルールの遵守

## ⚡ 実装フロー（厳格遵守）

```bash
# 1. 品質ゲートチェック
python scripts/claude_quality_gate.py

# 2. テスト作成（RED）
# 新機能のテストを先に作成（失敗することを確認）

# 3. 最小実装（GREEN）
# テストが通る最小限の実装

# 4. リファクタリング（REFACTOR）
# テストを保持したまま改善

# 5. 最終確認
make pre-commit

# 6. コミット
git commit -m "..."
```

## 💥 違反時の対応

### 品質ゲート失敗時
```bash
🚨 Quality gate FAILED!
❌ The following checks failed:
   - mypy strict mode
   - TDD compliance

🛑 IMPLEMENTATION BLOCKED
```

**対応**:
1. エラーメッセージを必ず確認
2. 指摘された問題を完全に修正
3. 再度品質ゲートを実行
4. 成功するまで実装作業禁止

### 緊急時の例外処理
- 緊急時でも品質ゲートのスキップは**禁止**
- 問題の根本原因を修正してから進行
- 技術的負債の蓄積を防ぐ

## 🎯 品質保証の目標

- **型安全性**: 100% mypy strict mode 準拠
- **テストカバレッジ**: 新機能は必ずテスト付き
- **コード品質**: リンターエラー0個
- **アーキテクチャ**: 300行制限・単一責任原則

---

**注意**: 詳細な実装例・設定は上記リンク先を参照してください。
