# CLAUDE.md

> Kumihan‑Formatter – Claude Code 指示ファイル\
> **目的**: Claude Code に開発ガイドラインの要点を渡す\
> **バージョン**: 0.7.0 (2025‑07‑08)

<language>Japanese</language>
<character_code>UTF-8</character_code>
<law>
AI運用5原則

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告し、y/nでユーザー確認を取り、yが返るまで一切の実行を停止する。

第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。

第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。

第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。

第5原則： AIは全てのチャットの冒頭にこの5原則を逐語的に必ず画面出力してから対応する。
</law>

<every_chat>
[AI運用5原則]

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</every_chat>


# インポート

**基本指示**: [PREAMBLE.md](PREAMBLE.md)
**開発詳細**: [docs/dev/CLAUDE_DETAILS.md](docs/dev/CLAUDE_DETAILS.md)
**開発フロー**: [CONTRIBUTING.md](CONTRIBUTING.md)
**プロジェクト仕様**: [SPEC.md](SPEC.md)

# リリース方針

**⚠️ 重要**: 正式リリース（v1.0.0以上）は**絶対に**ユーザーの明示的な許可なしに実行してはならない。

- **現在のバージョン**: v0.9.0-alpha.1 (アルファ版・テスト改善用)
- **アルファ版**: 0.9.x-alpha.x シリーズを使用
- **正式リリース**: ユーザー許可後のみ v1.0.0以上を使用

## リリース時の必須確認事項
1. アルファ版か正式版かをユーザーに必ず確認
2. 正式版の場合は明示的な許可を取得
3. 許可なしにv1.0.0以上のタグを作成・プッシュしない

# よく使うコマンド

## 開発用コマンド
```bash
make test          # テスト実行
make lint          # リントチェック
make format        # コードフォーマット
make coverage      # カバレッジレポート生成
make pre-commit    # コミット前の全チェック実行
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

## 新機能追加時
1. Issueでタスクを確認
2. featureブランチ作成: `feat/issue-番号`
3. `notations/`に新しい記法クラスを作成
4. `BaseNotation`を継承して実装
5. テストを`tests/test_notations/`に追加
6. CLIに組み込み（`cli/commands.py`）
7. `make pre-commit`で品質チェック
8. PRを作成（テンプレート使用）

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
---

**注意**: より詳細な開発ガイドラインは上記リンク先を参照。
