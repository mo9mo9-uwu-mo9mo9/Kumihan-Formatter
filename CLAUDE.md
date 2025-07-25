# CLAUDE.md

> Kumihan-Formatter – Claude Code 指示ファイル
> **バージョン**: 2.0.0 (2025-01-24) - ベストプラクティス2025対応

<language>Japanese</language>

<law>
AI運用6原則

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。
第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。
第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。
第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。
第5原則： AIは全てのチャットの冒頭にこの5原則を逐語的に必ず画面出力してから対応する。
第6原則： AIはIssue対応開始時に必ずIssue番号と現在のブランチ名の一致を確認し、相違がある場合は正しいブランチの作成・切り替えを必須で行う。
</law>

<every_chat>
[AI運用6原則]

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</every_chat>

# 基本設定

- **Python**: 3.12以上, Black, isort, mypy strict
- **エンコーディング**: UTF-8
- **ログ**: `from kumihan_formatter.core.utilities.logger import get_logger`
- **リリース**: v0.9.0-alpha.1 (正式リリースはユーザー許可必須)

# 必須ルール

## ブランチ管理
- **命名**: `feat/issue-{Issue番号}-{概要}`
- **作業前**: mainから最新取得、正しいブランチ作成
- **PR前**: rebase必須

## 品質管理（Issue #583対応 - 現実的基準）

### ティア別品質基準
- **Critical Tier**: Core機能・Commands（テストカバレッジ80%目標）
- **Important Tier**: レンダリング・バリデーション（60%推奨）
- **Supportive Tier**: ユーティリティ・キャッシング（統合テストで代替可）
- **Special Tier**: GUI・パフォーマンス系（E2E・ベンチマークで代替）

### 品質チェック
- **新品質ゲート**: `python scripts/tiered_quality_gate.py`
- **段階的改善**: `python scripts/gradual_improvement_planner.py`
- **根本原因分析**: `python scripts/tdd_root_cause_analyzer.py`

### 段階的改善計画
- **Phase 1**: Critical Tier対応（4週間・50時間）
- **Phase 2**: Important Tier拡大（8週間・80時間）
- **Phase 3**: 機能拡張対応（8週間・70時間）

## PR・レビュー
- **PR body必須**: `@claude PRのレビューをお願いします！`
- **マージ**: mo9mo9手動のみ
- **CI/CD**: GitHub Actions必須通過

# 基本コマンド

```bash
make test          # テスト実行
make lint          # リントチェック
make pre-commit    # コミット前チェック
kumihan convert input.txt output.txt  # 基本変換
```

# qcheck系コマンド（Issue #578）

Claude Code品質チェック用ショートカット:

```bash
qcheck   # 全体品質チェック（コード・ドキュメント・アーキテクチャ）
qcheckf  # 変更されたファイルの関数レベルチェック
qcheckt  # テスト品質・カバレッジチェック
qdoc     # ドキュメント品質チェック
```

# 記法仕様

- **基本**: `;;;装飾名;;; 内容 ;;;`
- **脚注**: `((content))` → 巻末移動
- **傍注**: `｜content《reading》` → ルビ表現

# 詳細ドキュメント

- **基本指示**: [PREAMBLE.md](PREAMBLE.md)
- **開発詳細**: [docs/dev/CLAUDE_DETAILS.md](docs/dev/CLAUDE_DETAILS.md)
- **コマンド集**: [docs/dev/CLAUDE_COMMANDS.md](docs/dev/CLAUDE_COMMANDS.md)
- **qcheckガイド**: [docs/dev/CLAUDE_QCHECK_GUIDE.md](docs/dev/CLAUDE_QCHECK_GUIDE.md)
- **品質管理**: [docs/dev/QUALITY_GATE.md](docs/dev/QUALITY_GATE.md)
- **技術的負債**: [docs/dev/TECHNICAL_DEBT.md](docs/dev/TECHNICAL_DEBT.md)

# AI防止システム

## 回答前チェック
- CLAUDE.md確認済み？
- 推測要素はゼロ？
- 文脈理解は正確？
- 作業計画は報告済み？

## 停止トリガー
- プロジェクト指示と矛盾
- 不明確で推測が必要
- 複数解釈が可能
- Issue/PR番号とブランチ名不一致

---
**重要**: 詳細情報は上記リンク先を参照
