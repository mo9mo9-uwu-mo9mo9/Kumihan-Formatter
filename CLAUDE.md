# CLAUDE.md

> Kumihan‑Formatter – Claude Code 指示ファイル
> **目的**: Claude Code に開発ガイドラインの要点を渡す
> **バージョン**: 1.1.0 (2025‑01‑18) - 整理・統合版

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

**品質管理**: [docs/dev/QUALITY_GATE.md](docs/dev/QUALITY_GATE.md)
**技術的負債**: [docs/dev/TECHNICAL_DEBT.md](docs/dev/TECHNICAL_DEBT.md)
**効率化**: [docs/dev/EFFICIENT_REFACTORING.md](docs/dev/EFFICIENT_REFACTORING.md)

# 重要なルール

## リリース方針
**⚠️ 重要**: 正式リリース（v1.0.0以上）は**絶対に**ユーザーの明示的な許可なしに実行してはならない。

- **現在のバージョン**: v0.9.0-alpha.1 (アルファ版・テスト改善用)
- **アルファ版**: 0.9.x-alpha.x シリーズを使用
- **正式リリース**: ユーザー許可後のみ v1.0.0以上を使用

## 開発プロセス

### TDD（テスト駆動開発）
- **新機能**: Red-Green-Refactorサイクル実践
- **テストファースト**: 実装前にテスト作成
- **継続的リファクタリング**: 安全な設計改善

### Pull Request必須ルール
- **PR作成時レビュー依頼必須**: PR作成時のbodyに必ず`@claude`メンションを含める
- **Claude自動レビュー**: PR作成時に自動でClaude Codeレビュー実行
- **mo9mo9手動マージ**: レビュー完了後、mo9mo9による手動マージ実行
- **品質保証**: GitHub Actions品質チェック + Claudeレビューの二重チェック

### ブランチ保護設定
- **main ブランチ直接プッシュ禁止**: 全ての変更はPR経由必須
- **CI/CD必須通過**: GitHub Actions品質チェック必須
- **設定ガイド**: [docs/dev/BRANCH_PROTECTION.md](docs/dev/BRANCH_PROTECTION.md)

## コーディング規約
- **Python**: 3.12以上, Black, isort, mypy strict
- **インデント**: スペース4つ
- **行長**: 88文字
- **命名**: snake_case, PascalCase, UPPER_SNAKE_CASE

### ログ使用規約（統一必須）
**⚠️ 重要**: 全てのモジュールでKumihanLogger統一ログシステムを使用すること

```python
# ✅ 正しい実装（必須）
from kumihan_formatter.core.utilities.logger import get_logger

class ExampleClass:
    def __init__(self):
        self.logger = get_logger(__name__)  # 統一ログ取得
        self.logger.info("ExampleClass initialized")

    def process(self):
        try:
            # 処理実行
            self.logger.info("Processing started")
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")  # エラーログ記録
```

```python
# ❌ 禁止事項
import logging  # 標準loggingの直接import禁止
logging.error("直接使用は禁止")  # 統一性を破る
```

**規約詳細**:
- **統一ログ取得**: `get_logger(__name__)` を使用
- **インスタンス変数**: `self.logger = get_logger(__name__)` でクラス内保持
- **エラーハンドリング**: 全ての`try/except`でログ記録必須
- **標準logging禁止**: `import logging` による直接使用は禁止

## 核心ルール

### 1. 品質ゲート（詳細: [docs/dev/QUALITY_GATE.md](docs/dev/QUALITY_GATE.md)）
```bash
# 実装前必須チェック
python scripts/claude_quality_gate.py
```

### 2. 技術的負債予防（詳細: [docs/dev/TECHNICAL_DEBT.md](docs/dev/TECHNICAL_DEBT.md)）
- **300行制限**: ファイル300行以内（例外なし）
- **Single Responsibility**: 1ファイル1責任
- **Boy Scout Rule**: コードを触ったら少しでも改善

### 3. Token効率化（詳細: [docs/dev/EFFICIENT_REFACTORING.md](docs/dev/EFFICIENT_REFACTORING.md)）
- **既存コード分割優先**: 移動・コピーで行う
- **新規作成禁止**: ファイル分割時に新しいコードを書かない
- **Token節約**: 80-90%削減を目指す

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

---

**注意**: 詳細な実装例・設定は上記リンク先を参照してください。


# GitHub Claudeメンション方法

## PR作成時の必須レビュー依頼テンプレート
**重要**: Pull Request作成時は必ずbodyに以下のClaudeレビュー依頼を含める：

```
@claude PRのレビューをお願いします！

## レビュー観点
- CI/CD設定の確認
- コード品質の評価
- 型安全性の検証
- セキュリティチェック

Claude レビューをお願いします！
```

## 重要事項
- **正しいメンション**: `@claude` （小文字）
- **間違ったメンション**: `@claude-actions`, `@Claude`, `/claude` 等は無効
- **実行タイミング**: PR作成後、レビュー依頼時
- **期待結果**: Claude GitHub Actionsによる自動レビュー実行
