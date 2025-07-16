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

### Pull Request必須ルール
- **手動マージ**: オートマージ使用禁止
- **GitHub Apps Claude必須**: 全PRでレビュー実施
- **1コミット＝1レビュー**: 各コミット個別レビュー
- **⚠️ レビュー依頼必須**: PR作成後、必ず @claude にレビュー依頼コメント送信

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

**🚨 Claude Code向け重要指示**:
- **Hook警告を絶対に無視しないこと**
- 警告が出た場合は、必ず以下の対応手順に従って修正作業を実施すること
- 警告を無視して作業を続行することは技術的負債の蓄積につながるため禁止

**対応方法**: [CONTRIBUTING.md](CONTRIBUTING.md#pre-commit-hook警告への対応) または [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md#pre-commit-hook警告) を参照

# 詳細情報へのリンク

- **プロジェクト構造・記法仕様**: [SPEC.md](SPEC.md)
- **コマンド・オプション**: [docs/dev/CLAUDE_COMMANDS.md](docs/dev/CLAUDE_COMMANDS.md)
- **コーディング規約**: [CONTRIBUTING.md](CONTRIBUTING.md#コーディング規約)

---

**注意**: 詳細な実装例・設定は上記リンク先を参照してください。
