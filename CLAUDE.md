# CLAUDE.md

> Kumihan‑Formatter – Claude Code 指示ファイル\
> **目的**: Claude Code に開発ガイドラインの要点を渡す\
> **バージョン**: 0.7.0 (2025‑07‑08)

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


# インポート

**基本指示**: [PREAMBLE.md](PREAMBLE.md)
**開発詳細**: [docs/dev/CLAUDE_DETAILS.md](docs/dev/CLAUDE_DETAILS.md)
**開発フロー**: [CONTRIBUTING.md](CONTRIBUTING.md)
**プロジェクト仕様**: [SPEC.md](SPEC.md)
**リリース手順**: [docs/dev/RELEASE_GUIDE.md](docs/dev/RELEASE_GUIDE.md)

# リリース方針

**⚠️ 重要**: 正式リリース（v1.0.0以上）は**絶対に**ユーザーの明示的な許可なしに実行してはならない。

- **現在のバージョン**: v0.9.0-alpha.1 (アルファ版・テスト改善用)
- **アルファ版**: 0.9.x-alpha.x シリーズを使用
- **正式リリース**: ユーザー許可後のみ v1.0.0以上を使用

## リリース時の必須確認事項
1. アルファ版か正式版かをユーザーに必ず確認
2. 正式版の場合は明示的な許可を取得
3. 許可なしにv1.0.0以上のタグを作成・プッシュしない

## リリース手順（重要）
**⚠️ 必須**: 全リリースは [docs/dev/RELEASE_GUIDE.md](docs/dev/RELEASE_GUIDE.md) の手順に従う

### 基本原則
- **mainブランチ保護**: 直接プッシュ禁止
- **PR経由必須**: バージョン変更もPR経由
- **手動マージ**: レビュー後に手動でマージ実行
- **手順厳守**: ガイドに従わない場合は同じ失敗を繰り返す

# よく使うコマンド

## 開発用コマンド
```bash
make test          # テスト実行
make lint          # リントチェック
make format        # コードフォーマット
make coverage      # カバレッジレポート生成
make pre-commit    # コミット前の全チェック実行
```

## デバッグ用コマンド
```bash
# GUIデバッグモード
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher

# 詳細ログレベル設定
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_LOG_LEVEL=DEBUG python3 -m kumihan_formatter.gui_launcher

# コンソール出力も有効化
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_CONSOLE_LOG=true python3 -m kumihan_formatter.gui_launcher

# 開発ログ機能（Issue#446）
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# 構造化ログ機能（Issue#472）- JSON形式でClaude Code解析しやすく
KUMIHAN_DEV_LOG=true KUMIHAN_DEV_LOG_JSON=true kumihan convert input.txt output.txt
```

## CLI使用例
```bash
# 基本的な変換
kumihan convert input.txt output.txt

# 記法サンプル表示
kumihan sample --notation footnote

# 構文チェック
kumihan check-syntax manuscript.txt
```

# コーディング規約

## Python設定
- **バージョン**: Python 3.12以上
- **インデント**: スペース4つ
- **行長**: 88文字（Black設定）
- **フォーマッター**: Black, isort
- **型チェック**: mypy strict mode

## 命名規則
- 変数・関数: `snake_case`
- クラス: `PascalCase`
- 定数: `UPPER_SNAKE_CASE`
- プライベート: `_prefix`

## インポート順
1. 標準ライブラリ
2. サードパーティ
3. ローカルモジュール
（isortで自動整理）

# プロジェクト構造

```
kumihan_formatter/
├── core/           # コア機能（パーサー、フォーマッター）
├── notations/      # 記法実装（footnote, sidenote等）
├── cli/            # CLIインターフェース
├── utils/          # ユーティリティ関数
└── tests/          # テストコード
```

### 主要ディレクトリ
- `/kumihan_formatter` - メインパッケージ
  - `/cli.py` - CLIエントリポイント
  - `/parser.py` - 解析統括
  - `/renderer.py` - レンダリング統括
  - `/core/` - 核心機能モジュール群
  - `/templates/` - HTMLテンプレート
- `/tests/` - テストコード
- `/docs/` - ドキュメント
- `/examples/` - サンプルファイル

## 記法仕様
- **基本記法**: `;;;装飾名;;; 内容 ;;;`
- **脚注記法**: `((content))` → 巻末に移動
- **傍注記法**: `｜content《reading》` → ルビ表現
- **改行処理**: 入力改行をそのまま反映
- **エンコーディング**: UTF-8（BOM付きも対応）
- **変換フロー**: パース → 変換 → フォーマット

# 開発フロー

## t-wada推奨テスト駆動開発手法

### 基本原則
プロジェクトでは**和田卓人（t-wada）**氏の推奨するテスト駆動開発手法を採用します。

#### 段階的テスト手法
以下の3段階を理解し、プロジェクトの状況に応じて適切なレベルを選択：

1. **自動テスト**: 基礎的なテスト作成（最低限必要）
2. **テストファースト**: テストを先に書いてから実装
3. **テスト駆動開発（TDD）**: Red-Green-Refactorサイクル

#### TDDの基本手順（フルTDD実践時）
1. **テストリスト作成**: 網羅したいテストシナリオをリストアップ
2. **具体的なテスト作成**: リストから一つ選び、実行可能なテストコードに翻訳
3. **Red**: テストが失敗することを確認
4. **Green**: 最小限のコードでテストを通す
5. **Refactor**: 実装の設計を改善
6. **繰り返し**: テストリストが空になるまで2-5を繰り返し

#### 設計原則
- **ボトムアップ設計**: シンプルで責務が明確なコンポーネントから構築
- **変化への対応力**: テストを通じて安全にリファクタリング可能な設計
- **段階的な複雑性の管理**: 複雑なものを複雑なまま設計せず、組み合わせで対処

### 実践レベルの選択指針
- **新機能**: TDD推奨（Red-Green-Refactorサイクル）
- **バグ修正**: 最低限テストファースト
- **緊急修正**: 修正後に自動テスト追加
- **リファクタリング**: 既存テストで安全性確保

## 新機能追加時
1. Issueでタスクを確認
2. featureブランチ作成: `feat/issue-番号`
3. **テストリスト作成**: 実装予定の機能のテストシナリオをリストアップ
4. **TDD実践**: Red-Green-Refactorサイクルで実装
   - `tests/test_notations/`にテストを先に作成
   - `notations/`に新しい記法クラスを作成
   - `BaseNotation`を継承して実装
5. CLIに組み込み（`cli/commands.py`）
6. `make pre-commit`で品質チェック
7. PRを作成（テンプレート使用）
8. **レビュー待ち**: オートマージは使用せず手動マージ

## Pull Request作成・マージ手順

### ⚠️ 重要: オートマージは無効
このプロジェクトは**手動マージ**を基本とします。オートマージは**使用禁止**です。

### レビュー方針（必須）
- **1コミット＝1レビュー**: 各コミットに対して個別にレビューを実施
- **GitHub Apps Claude必須**: すべてのPRでGitHub Apps Claudeを使用してレビュー
- **レビュー完了後マージ**: レビュー承認後に手動マージ実行

### PR作成
```bash
# PR作成
gh pr create --title "タイトル" --body "内容"

# オートマージは使用しない（手動でマージ）
# gh pr merge PR番号 --auto --merge  # 使用禁止

# オートマージが自動有効化された場合は明示的に無効化
gh pr merge PR番号 --disable-auto
```

### レビュー手順
1. **PR作成後**: GitHub Apps Claudeを招待
2. **コミット単位レビュー**: 各コミットの変更内容を個別にレビュー依頼
3. **Claude レビュー実行**: PRのコメント欄で @claude にメンションしてレビュー開始
4. **⚠️ 重要 - 変更後レビュー**: 修正やコミット追加でプッシュした場合は必ず @claude にレビュー依頼
5. **レビュー対応**: 指摘事項があれば修正・追加コミット
6. **承認取得**: すべてのコミットでレビュー承認を確認

### 手動マージの手順
- **作成**: PRを作成してGitHub Apps Claudeでレビューを実施
- **レビュー**: 1コミット＝1レビューでGitHub Apps Claude必須利用
- **マージ**: レビュー完了後に手動でマージ
- **方式**: squash merge推奨

## デバッグ
```bash
# 詳細ログ出力
KUMIHAN_DEBUG=1 kumihan convert input.txt output.txt

# プロファイリング
python -m cProfile -s cumulative cli.py
```

### デバッグオプション
- ログレベル: `--debug`オプション使用
- エラートレース: `--traceback`オプション

## 開発ログ機能 (Issue#446)
Claude Code向けの開発ログ機能が利用可能です：

```bash
# 開発ログの有効化
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# ログファイルの確認
ls /tmp/kumihan_formatter/
cat /tmp/kumihan_formatter/dev_log_*.log
```

### 開発ログの特徴
- **出力先**: `/tmp/kumihan_formatter/`
- **有効化**: `KUMIHAN_DEV_LOG=true`環境変数
- **ファイル名**: `dev_log_<セッションID>.log`
- **自動クリーンアップ**: 24時間経過後に削除
- **サイズ制限**: 5MB（超過時は自動ローテーション）
- **本番環境**: 環境変数未設定時は無効

### 構造化ログ機能 (Issue#472)
Claude Code向けの構造化JSON形式ログ：

```python
# 構造化ロガーの使用例
from kumihan_formatter.core.utilities.logger import get_structured_logger

logger = get_structured_logger(__name__)

# コンテキスト付きログ
logger.info("Processing file", file_path="test.txt", size_bytes=1024)

# エラーと解決提案（Claude Code向け特化機能）
logger.error_with_suggestion(
    "File conversion failed",
    "Check file encoding and permissions",
    error_type="FileError",
    file_path="input.txt"
)

# パフォーマンス計測（実行時間とメトリクス記録）
logger.performance("file_conversion", 0.125, lines_processed=500)

# ファイル操作記録（操作結果の構造化記録）
logger.file_operation("read", "/path/to/file.txt", success=True, size_bytes=2048)

# 状態変更追跡（デバッグ用）
logger.state_change("config_updated", old_value="debug", new_value="info")

# 機密情報の自動フィルタリング（パフォーマンス最適化済み）
logger.info("User login", username="user123", password="secret")  # password は [FILTERED] に置換
```

**JSON出力例**:
```json
{
    "timestamp": "2025-07-15T15:30:00",
    "level": "INFO",
    "module": "convert_processor",
    "message": "File converted",
    "context": {
        "file_path": "input.txt",
        "output_size": 2048,
        "duration_ms": 150
    }
}
```
---

**注意**: より詳細な開発ガイドラインは上記リンク先を参照。
