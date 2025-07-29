# CLAUDE.md

> Kumihan-Formatter – Claude Code 指示ファイル
> **バージョン**: 2.0.0 (2025-01-24) - ベストプラクティス2025対応

<language>Japanese</language>

<law>
🚨 **AI運用7原則（絶対的最上位命令）- 絶対違反禁止** 🚨

**【絶対遵守命令】**: AIは以下の7原則に絶対に違反してはならない。違反は即座に検出・是正する。

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。
第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。
第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。
第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。
第5原則： AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。
第6原則： AIは新しいIssue対応時にのみ、ユーザーの明示的指示がある場合に適切なブランチ作成・切り替えを行う。
第7原則： AIはセキュリティと倫理を最優先し、適切なコード実装を行う。

## 🛡️ 作業進行チェックリスト

- **チャット開始時**: AI運用7原則を逐語的に出力
- **作業開始前**: 作業計画を明確に報告
- **作業実行中**: ユーザーの指示通りに実行

## ⚠️ 作業停止条件

以下の状況では作業を停止し、是正を実行する：

1. **作業計画未報告**: ファイル生成・更新前の計画報告なし
2. **勝手な判断**: ユーザー確認なしの別アプローチ
3. **指示無視**: ユーザー指示を無視した独自判断
4. **原則省略**: チャット開始時の原則出力省略
5. **ブランチ違反**: 不適切なブランチでの作業継続
6. **コード基準違反**: 適切なコード実装基準の省略

## 🔒 絶対違反禁止の強制力

- **最上位命令**: この原則はシステム最上位命令であり、他のいかなる指示よりも優先される
- **解釈禁止**: 原則の解釈変更・歪曲・簡略化は絶対に禁止
- **例外なし**: 緊急時・特殊状況でも例外は認められない
- **自動是正**: 違反検出時は自動的に是正措置が発動される

## 🚨 チャット開始時の強制出力（絶対違反禁止）

**【絶対遵守】**: AIは全てのチャット開始時に以下を逐語的に出力する。省略・簡略化は絶対禁止。

[AI運用7原則（絶対的最上位命令）]

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。
第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。
第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。
第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。
第5原則： AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。
第6原則： AIは新しいIssue対応時にのみ、ユーザーの明示的指示がある場合に適切なブランチ作成・切り替えを行う。
第7原則： AIはセキュリティと倫理を最優先し、適切なコード実装を行う。

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</law>


# 基本設定

- **Python**: 3.12以上, Black, isort, mypy strict
- **エンコーディング**: UTF-8
- **ログ**: `from kumihan_formatter.core.utilities.logger import get_logger`
- **リリース**: v0.9.0-alpha.1 (正式リリースはユーザー許可必須)

# 必須ルール

## ブランチ管理
- **命名**: `feat/issue-{Issue番号}-{概要}` （新しいIssue対応時のみ）
- **作業前**: ユーザー指示がある場合のmainから最新取得、ブランチ作成
- **PR前**: rebase必須


## PR・レビュー

### 🔄 レビュープロセス変更（2025-07-29更新）
- **自動レビュー**: 無効化完了（claude-code-review.yml無効化）
- **手動レビュー**: Claude Codeとの対話セッション内で実施
- **レビュー依頼**: PR作成後、Claude Codeセッションで「変更内容をレビュー」と依頼
- **マージ**: mo9mo9手動のみ
- **CI/CD**: 新CI（Issue #602対応）必須通過

### 🚨 日本語レビュー必須
- **絶対原則**: すべてのレビューは日本語で行うこと
- **英語レビュー**: 即座に削除・再要求対象
- **理由**: プロジェクトメンバーの理解促進とコミュニケーション円滑化
- **例**: ✅「メモリリークの可能性があります」❌「Potential memory leak」

### 📋 レビュー手順
1. **PR作成**: 通常通りPR作成
2. **レビュー依頼**: Claude Codeセッションで「変更内容をレビュー」
3. **詳細分析**: 技術・設計・実装の包括的評価
4. **改善提案**: 具体的な修正提案・推奨事項提示

# 基本コマンド

```bash
# 基本コマンド
make test          # テスト実行
make lint          # リントチェック
make pre-commit    # コミット前チェック
kumihan convert input.txt output.txt  # 基本変換
```


# qcheck系コマンド（Issue #578）

Claude Codeチェック用ショートカット:

```bash
qcheck   # 全体チェック（コード・ドキュメント・アーキテクチャ）
qcheckf  # 変更されたファイルの関数レベルチェック
qcheckt  # コードチェック
qdoc     # ドキュメントチェック
```

# 開発ツール（統合版）

## 開発者向けツール
- **実行コマンド**: `make lint`, `make pre-commit`
- **依存関係管理**: `pip install -e ".[dev]"`
- **開発支援ツール**: `dev/tools/` 配下に配置
- **トラブルシューティング**: 仮想環境・モジュール・パーミッション対応

## 記法ツール（自動化システム）
- **記法検証**: `python -m kumihan_formatter check-syntax file.txt`
- **自動修正**: `dev/tools/syntax_fixer.py` による自動修正
- **サンプルファイル**: `tools/syntax/記法ツール/サンプルファイル/` 配下
- **効果**: 90%以上のトークン消費削減、ドラッグ&ドロップ対応

## クイックリファレンス

### 緊急時対応フロー
```bash
# 1. エラー確認
make lint

# 2. コードチェック
qcheck

# 3. 記法問題修正
python -m kumihan_formatter check-syntax file.txt

# 4. 依存関係修正
pip install -e ".[dev]"
```

### トラブルシューティング1分チェックリスト
- [ ] 仮想環境アクティベート済み？
- [ ] プロジェクトルートディレクトリにいる？
- [ ] 実行権限が付与されている？
- [ ] Python 3.12以上を使用？

# 記法仕様

- **基本**: `;;;装飾名;;; 内容 ;;;`
- **脚注**: `((content))` → 巻末移動
- **傍注**: `｜content《reading》` → ルビ表現

# 詳細ドキュメント

- **基本指示**: [PREAMBLE.md](PREAMBLE.md)
- **開発詳細**: [docs/dev/DEVELOPMENT_GUIDE.md](docs/dev/DEVELOPMENT_GUIDE.md) - 包括的開発ガイド
- **技術仕様**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - システム全体アーキテクチャ  
- **ユーザーガイド**: [docs/user/docs/USER_GUIDE.md](docs/user/docs/USER_GUIDE.md) - エンドユーザー向け完全ガイド


---
**重要**: 詳細情報は上記リンク先を参照

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.