# Kumihan-Formatter 開発ガイド（統合版）

> **目的**: Kumihan-Formatterの開発に関する包括的な情報を提供
> **バージョン**: 1.0.0 (2025-01-24)
> **最終更新**: 2025-07-28

## 📋 目次

1. [概要](#-概要)
2. [アーキテクチャ](#-アーキテクチャ)
3. [開発環境・セットアップ](#-開発環境セットアップ)
4. [開発ワークフロー](#-開発ワークフロー)
5. [品質管理](#-品質管理)
6. [Claude Code 開発](#-claude-code-開発)
7. [テスト・デバッグ](#-テストデバッグ)
8. [リファクタリング](#-リファクタリング)
9. [リリース・配布](#-リリース配布)  
10. [コミュニケーション](#-コミュニケーション)
11. [トラブルシューティング](#-トラブルシューティング)
12. [プロジェクト履歴](#-プロジェクト履歴)

---

## 🎯 概要

### プロジェクト概要

Kumihan-Formatterは、モジュラーな設計に基づいたテキスト→HTML変換ツールです。コア機能は`kumihan_formatter/core/`に集約され、専門化されたサブモジュール群で構成されています。

### 基本設定

- **Python**: 3.12以上, Black, isort, mypy strict
- **エンコーディング**: UTF-8
- **ログ**: `from kumihan_formatter.core.utilities.logger import get_logger`
- **リリース**: v0.9.0-alpha.1 (正式リリースはユーザー許可必須)

### ディレクトリ構成

```
docs/dev/                         # 開発者向けドキュメント
├── ARCHITECTURE.md               # システム全体のアーキテクチャ
├── STYLE_GUIDE.md               # コーディングスタイルガイド
├── EMOJI_POLICY.md              # 絵文字使用ポリシー
├── LABEL_GUIDE.md               # GitHub Issueラベルガイド
├── TESTING.md                   # テスト実行・詳細ガイド
├── tools/                       # 開発ツール
│   └── SYNTAX_CHECKER_README.md # 記法チェッカーツールの説明
└── strategies/                  # 戦略・方針
    └── TESTING_STRATEGY.md      # テスト戦略（ユニット中心、E2E廃止）
```

---

## 🏗️ アーキテクチャ

### コンポーネント構成

```
kumihan_formatter/
├── cli.py                    # CLIエントリポイント (Click)
├── __main__.py              # パッケージ実行エントリポイント
├── parser.py                # 解析統括クラス
├── renderer.py              # レンダリング統括クラス
├── config.py                # 基本設定管理
├── simple_config.py         # 簡易設定クラス
├── sample_content.py        # サンプル生成機能
├── commands/                # CLIサブコマンド群
│   ├── convert.py           # 変換コマンド
│   ├── sample.py            # サンプル生成コマンド
│   ├── check_syntax.py      # 構文チェックコマンド
├── core/                    # 核心機能モジュール群
│   ├── ast_nodes.py         # AST ノード定義
│   ├── keyword_parser.py    # キーワード解析エンジン
│   ├── list_parser.py       # リスト解析エンジン
│   ├── block_parser.py      # ブロック解析エンジン
│   ├── template_manager.py  # テンプレート管理
│   ├── toc_generator.py     # 目次生成
│   ├── config_manager.py    # 拡張設定管理
│   ├── file_ops.py          # ファイル操作
│   ├── performance.py       # パフォーマンス監視
│   ├── error_reporting.py   # エラー報告
│   ├── doc_classifier.py    # ドキュメント分類
│   ├── distribution_manager.py # 配布管理
│   ├── markdown_converter.py   # Markdown変換
│   ├── rendering/           # レンダリング系
│   │   ├── main_renderer.py       # メインレンダラー
│   │   ├── element_renderer.py    # 要素レンダラー
│   │   ├── compound_renderer.py   # 複合要素レンダラー
│   │   ├── html_formatter.py      # HTML整形
│   │   └── html_utils.py          # HTML ユーティリティ
│   ├── error_handling/      # エラー処理系
│   │   ├── error_handler.py       # エラーハンドラー
│   │   ├── error_factories.py     # エラーファクトリー
│   │   ├── error_types.py         # エラー型定義
│   │   ├── error_recovery.py      # エラー回復
│   │   └── smart_suggestions.py   # 賢い修正提案
│   ├── syntax/              # 構文検証系
│   │   ├── syntax_validator.py    # 構文検証
│   │   ├── syntax_rules.py        # 構文ルール
│   │   ├── syntax_errors.py       # 構文エラー
│   │   └── syntax_reporter.py     # 構文報告
│   ├── validators/          # 検証系
│   │   ├── document_validator.py  # ドキュメント検証
│   │   ├── file_validator.py      # ファイル検証
│   │   ├── structure_validator.py # 構造検証
│   │   ├── syntax_validator.py    # 構文検証
│   │   ├── performance_validator.py # パフォーマンス検証
│   │   ├── validation_issue.py    # 検証問題
│   │   └── validation_reporter.py # 検証報告
│   ├── utilities/           # ユーティリティ系
│   │   ├── converters.py          # 変換ユーティリティ
│   │   ├── data_structures.py     # データ構造
│   │   ├── file_system.py         # ファイルシステム
│   │   ├── logging.py             # ログ
│   │   ├── string_similarity.py   # 文字列類似度
│   │   └── text_processor.py      # テキスト処理
│   └── common/              # 共通基盤
│       ├── error_framework.py     # エラーフレームワーク
│       ├── smart_cache.py         # スマートキャッシュ
│       └── validation_mixin.py    # 検証ミックスイン
├── templates/               # HTMLテンプレート
│   ├── base.html.j2         # ベーステンプレート
│   ├── base-with-source-toggle.html.j2 # ソース表示機能付き
│   ├── docs.html.j2         # ドキュメント用
│   └── experimental/        # 実験的テンプレート
├── ui/                      # ユーザーインターフェース
│   └── console_ui.py        # コンソールUI
└── utils/                   # 汎用ユーティリティ
    └── marker_utils.py      # マーカーユーティリティ
```

### データフロー

```
入力テキスト
    ↓
Parser (parser.py) ← 統括クラス
    ↓ 委譲
KeywordParser, ListParser, BlockParser (core/)
    ↓ [AST: Node型の配列]
Renderer (renderer.py) ← 統括クラス
    ↓ 委譲  
HTMLRenderer, TemplateManager, TOCGenerator (core/)
    ↓ [HTML文字列]
出力HTML
```

### 主要クラス

#### Parser (統括)
- **責務**: 解析フローの制御、特化パーサーへの委譲
- **依存**: KeywordParser, ListParser, BlockParser
- **メソッド**: 
  - `parse()`: メインの解析メソッド
  - 各特化パーサーへの委譲処理

#### KeywordParser (core/keyword_parser.py)
- **責務**: キーワード記法解析の中核
- **特徴**: Node構築の基盤、他パーサーから使用される
- **メソッド**: 
  - キーワード認識・解析
  - NodeBuilder との連携

#### Node (core/ast_nodes.py)
```python
@dataclass
class Node:
    type: str                    # 'paragraph', 'h1', 'image', etc.
    content: str                 # ノードの内容
    children: List['Node']       # 子ノード配列
    attributes: Dict[str, Any]   # 属性辞書
    # 追加フィールドによる拡張性
```

### アーキテクチャの特徴

#### 1. モジュラー設計
- 機能別の専門モジュールに分離
- `core/` 配下でドメイン別にサブディレクトリ構成
- 明確な責務分離による保守性向上

#### 2. 委譲パターン
- 統括クラス（Parser/Renderer）が特化クラスに処理を委譲
- 各特化クラスは単一責任を持つ
- 拡張時は特化クラスの追加で対応

#### 3. AST中心設計
- Node型による統一的な中間表現
- 解析とレンダリングの完全分離
- 変換パイプラインの明確化

### アーキテクチャ設計原則

#### 基本理念
**「予防的品質管理」** - 問題が発生する前に防ぐ設計

#### 設計原則

**1. 単一責任原則 (Single Responsibility)**

ファイルサイズ制限:
- **Python ファイル**: 最大300行
- **関数/メソッド**: 最大50行
- **クラス**: 最大200行

**2. 依存関係の単方向性**

レイヤー構造の厳格化:
```
┌─────────────────────────────────────┐
│  CLI Layer (cli.py, commands/)     │
├─────────────────────────────────────┤
│  Application Layer (parser.py,     │
│                     renderer.py)   │
├─────────────────────────────────────┤
│  Core Layer (core/)                │
├─────────────────────────────────────┤
│  Utilities Layer (utilities/)      │
└─────────────────────────────────────┘
```

**3. インターフェース駆動設計**

Protocol/ABC の積極活用:
```python
from typing import Protocol
from abc import ABC, abstractmethod

# インターフェース定義
class ErrorHandlerProtocol(Protocol):
    def handle_error(self, error: Exception, context: dict) -> None: ...

class ValidatorProtocol(Protocol):
    def validate(self, data: Any) -> ValidationResult: ...
```

### 循環依存の管理

#### HTMLRenderer ⟷ ElementRenderer
```python
# 意図的な循環依存（委譲パターン）
HTMLRenderer._main_renderer = self
ElementRenderer._main_renderer = renderer
```
**理由**: ElementRenderer が親レンダラーに再帰的レンダリングを委譲

### 拡張ポイント

#### 1. 新しい記法追加
- `core/keyword_parser.py` でキーワード定義
- `core/syntax/syntax_rules.py` でルール追加
- `core/rendering/` でHTML出力対応

#### 2. 新しい検証機能
- `core/validators/` に専門検証クラス追加
- `core/syntax/` に構文ルール追加

---

## 🔧 開発環境・セットアップ

### 必須コマンド

```bash
make test          # テスト実行
make lint          # リントチェック
make format        # コードフォーマット
make coverage      # カバレッジレポート生成
make pre-commit    # コミット前の全チェック実行
```

### 基本コマンド

```bash
kumihan convert input.txt output.txt  # 基本変換
kumihan sample --notation footnote    # 記法サンプル表示
kumihan check-syntax manuscript.txt  # 構文チェック
```

### デバッグ用コマンド

```bash
# GUIデバッグモード
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher

# 詳細ログレベル設定
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_LOG_LEVEL=DEBUG python3 -m kumihan_formatter.gui_launcher

# 開発ログ機能（Issue#446）
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# 構造化ログ機能（Issue#472）- JSON形式でClaude Code解析しやすく
KUMIHAN_DEV_LOG=true KUMIHAN_DEV_LOG_JSON=true kumihan convert input.txt output.txt

# 詳細ログ出力
KUMIHAN_DEBUG=1 kumihan convert input.txt output.txt

# プロファイリング
python -m cProfile -s cumulative cli.py
```

### 環境変数一覧

| 環境変数 | 説明 | 値 |
|---------|------|-----|
| `KUMIHAN_GUI_DEBUG` | GUIデバッグモード有効化 | `true` |
| `KUMIHAN_GUI_LOG_LEVEL` | GUIログレベル設定 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `KUMIHAN_GUI_CONSOLE_LOG` | コンソールログ出力有効化 | `true` |
| `KUMIHAN_DEV_LOG` | 開発ログ有効化 | `true` |
| `KUMIHAN_DEV_LOG_JSON` | JSON形式ログ出力 | `true` |
| `KUMIHAN_DEBUG` | 詳細デバッグ出力 | `1` |

---

## 🔄 開発ワークフロー

### 必須ルール

#### ブランチ管理
- **命名**: `feat/issue-{Issue番号}-{概要}`
- **作業前**: mainから最新取得、正しいブランチ作成
- **PR前**: rebase必須

### 基本ワークフロー

#### 作業開始時の手順
```bash
# 1. mainブランチを最新に更新
git checkout main
git pull origin main

# 2. 作業ブランチ作成・切り替え
git checkout -b feat/issue-xxx-description
# または既存ブランチ: git checkout feat/issue-xxx-description
```

#### PR作成前の必須手順
```bash
# 1. 現在の状態確認
git status
git log --oneline -5

# 2. mainブランチの最新を取得
git checkout main
git pull origin main

# 3. 作業ブランチにmainの最新を適用
git checkout feat/issue-xxx-description
git rebase main

# 4. コンフリクト解決（必要な場合）
# git add . && git rebase --continue

# 5. 強制プッシュ（rebase後）
git push --force-with-lease

# 6. PR作成
gh pr create --title "タイトル" --body "本文"
```

### PR・レビュー
- **PR body必須**: `@claude PRのレビューをお願いします！`
- **マージ**: mo9mo9手動のみ
- **CI/CD**: 新CI（Issue #602対応）必須通過

### GitHub Actions（Issue #602最適化）

**新シンプル構成**:
- **`ci.yml`**: 必須CI（Black/isort/flake8/pytest/mypy）
- **`quality-optional.yml`**: オプション品質チェック（週次実行）
- **`claude.yml`**: Claude自動レビュー

**最適化効果**: 実行時間15分→5分、複雑度大幅削減

---

## 🔍 品質管理

### 品質管理（Issue #583対応 - 現実的基準）

#### ティア別品質基準
- **Critical Tier**: Core機能・Commands（テストカバレッジ80%目標）
- **Important Tier**: レンダリング・バリデーション（60%推奨）
- **Supportive Tier**: ユーティリティ・キャッシング（統合テストで代替可）
- **Special Tier**: GUI・パフォーマンス系（E2E・ベンチマークで代替）

#### 品質チェック
- **新品質ゲート**: `python scripts/tiered_quality_gate.py`
- **段階的改善**: `python scripts/gradual_improvement_planner.py`
- **根本原因分析**: `python scripts/tdd_root_cause_analyzer.py`

#### 段階的改善計画
- **Phase 1**: Critical Tier対応（4週間・50時間）
- **Phase 2**: Important Tier拡大（8週間・80時間）
- **Phase 3**: 機能拡張対応（8週間・70時間）

### qcheck系コマンド（Issue #578）

Claude Code品質チェック用ショートカット:

```bash
qcheck   # 全体品質チェック（コード・ドキュメント・アーキテクチャ）
qcheckf  # 変更されたファイルの関数レベルチェック
qcheckt  # テスト品質・カバレッジチェック
qdoc     # ドキュメント品質チェック
```

#### `qcheck` - 全体品質チェック
```bash
# 実行方法
./scripts/qcheck
# または
python scripts/qcheck_commands.py qcheck
```

**実行内容**:
- 📏 ファイルサイズチェック（300行制限）
- 🏗️ アーキテクチャチェック
- 🔍 型チェック（mypy strict）
- 📚 ドキュメント品質チェック
- 🧪 基本テスト実行

**使用タイミング**: コミット前、PR作成前

#### `qcheckf` - 変更ファイル関数チェック
```bash
./scripts/qcheckf
```

**実行内容**:
- 📋 Git差分から変更ファイル一覧表示
- 🔍 変更ファイルの関数レベル品質チェック
- 📝 変更ファイル限定型チェック

**使用タイミング**: 個別ファイル修正後

#### `qcheckt` - テスト品質チェック
```bash
./scripts/qcheckt
```

**実行内容**:
- 🧪 カバレッジ付きテスト実行
- 📊 カバレッジレポート表示
- 🔍 テスト品質評価

**使用タイミング**: TDD実践時、テスト追加後

#### `qdoc` - ドキュメント品質チェック
```bash
./scripts/qdoc
```

**実行内容**:
- 📚 ドキュメント品質検証（リンク切れ等）
- 📝 Markdownリンター
- 🔗 リンク切れチェック

**使用タイミング**: ドキュメント更新後

### 推奨ワークフロー

#### 新機能実装時
```bash
# 1. 設計・計画段階
qdoc  # 既存ドキュメントの確認

# 2. TDD実装段階
qcheckt  # テストカバレッジ確認

# 3. 実装完了時
qcheckf  # 変更ファイルチェック

# 4. コミット前
qcheck  # 全体品質確認
```

#### バグ修正時
```bash
# 1. 修正前
qcheckt  # 現在のテスト状況確認

# 2. 修正後
qcheckf  # 修正ファイルチェック
qcheck   # 全体影響確認
```

### 技術的負債予防・対応ガイド

#### 300行ルール（厳守）
- **ファイル**: 300行以内（例外なし）
- **クラス**: 100行以内推奨
- **関数**: 20行以内推奨
- **⚠️ 違反時**: pre-commit hookが自動でブロック

#### アーキテクチャ原則
- **Single Responsibility Principle**: 1ファイル1責任
- **関数分割**: 複雑な処理は機能単位で分離
- **Boy Scout Rule**: コードを触ったら少しでも改善
- **循環依存**: 禁止（アーキテクチャチェックで検出）

#### 自動チェック体制
```bash
# コミット時自動実行（pre-commit hook）
scripts/check_file_size.py      # ファイルサイズチェック
scripts/architecture_check.py   # アーキテクチャ品質チェック

# 手動実行（必要時のみ）
.venv/bin/python scripts/check_file_size.py
.venv/bin/python scripts/architecture_check.py
```

#### pre-commit hookエラー対応

Claude Code使用時に以下のメッセージが表示される場合：
```
PreToolUse:Bash [~/.claude/hook_pre_commands.sh] failed with
non-blocking status code 1: No stderr output
```

**これは正常動作です。** status code 1は非ブロッキングエラーで、技術的負債の警告を表示しています。

**対応手順**:

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

---

## 🤖 Claude Code 開発

### 必須運用

#### 守るべきファイル/フォルダ

| 種別       | パス                            | 理由           |
| -------- | ----------------------------- | ------------ |
| アンカーファイル | `CLAUDE.md`                   | Claude 指示の中心 |
| 設定       | `.claude/`                    | セッションキー等の機密  |
| ローカル設定   | `.claude/settings.local.json` | 個人環境依存       |

**禁止**: 上記を Git へ push・削除・改名する行為。

### 開発方針

#### ログ実装方針

**目的**: Claude Codeでの問題解決を効率化するため、できる限りクラスにログを仕込む

**実装方針**:
1. **統一ログシステム**: `KumihanLogger`を使用（従来の`logging.getLogger()`は非推奨）
2. **ログレベル設定**:
   - `DEBUG`: 詳細なトレース情報（メソッド開始/終了、変数値等）
   - `INFO`: 一般的な処理状況（キャッシュヒット/ミス、ファイル読み込み等）
   - `WARNING`: 警告事象（設定値異常、パフォーマンス低下等）
   - `ERROR`: エラー事象（例外発生、処理失敗等）
   - `CRITICAL`: 致命的エラー（システム停止レベル）

3. **必須ログポイント**:
   - クラス初期化時
   - 重要なメソッド開始/終了
   - エラーハンドリング（try/except）
   - パフォーマンス測定ポイント
   - キャッシュ操作
   - ファイル入出力
   - 設定変更

**実装例**:
```python
from kumihan_formatter.core.utilities.logger import get_logger

class ExampleClass:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("ExampleClass initialized")

    def process_file(self, file_path):
        self.logger.debug(f"Starting file processing: {file_path}")
        try:
            # 処理実行
            self.logger.info(f"File processed successfully: {file_path}")
        except Exception as e:
            self.logger.error(f"File processing failed: {file_path}, error: {e}")
            raise
```

#### 開発ログ機能 (Issue#446)

Claude Code向けの専用ログ機能が実装されています：

**特徴**:
- **出力先**: `/tmp/kumihan_formatter/` （Claude Codeがアクセス可能）
- **有効化**: `KUMIHAN_DEV_LOG=true` 環境変数
- **セッション管理**: タイムスタンプ付きファイル名
- **自動管理**: 24時間後の自動削除、5MB制限

**使用方法**:
```bash
# 開発ログ有効化
KUMIHAN_DEV_LOG=true python -m kumihan_formatter convert input.txt

# ログファイル確認
ls /tmp/kumihan_formatter/
cat /tmp/kumihan_formatter/dev_log_*.log
```

**実装場所**: `kumihan_formatter/core/utilities/logger.py` の `DevLogHandler` クラス

### 構造化ログ機能 (Issue#472)

#### 基本的な構造化ログ
```python
from kumihan_formatter.core.utilities.logger import get_structured_logger

logger = get_structured_logger(__name__)

# 基本的な情報ログ
logger.info("ファイル処理開始", file_path="input.txt", size_bytes=1024)

# エラー時の推奨アクション付きログ
logger.error_with_suggestion(
    "ファイルが見つかりません",
    "ファイルパスと権限を確認してください",
    error_type="FileNotFoundError",
    file_path="missing.txt"
)

# ファイル操作ログ
logger.file_operation("read", "/path/to/file.txt", success=True, size_bytes=2048)

# パフォーマンス測定ログ
logger.performance("file_conversion", 0.125, lines=500)

# 状態変更ログ
logger.state_change("config updated", old_value="debug", new_value="info")
```

#### 自動パフォーマンス測定デコレータ
```python
from kumihan_formatter.core.utilities.logger import log_performance_decorator

# 基本的なパフォーマンス測定
@log_performance_decorator(operation="file_conversion")
def convert_file(input_path: str) -> str:
    # ファイル変換処理
    return output_path

# メモリ使用量も測定
@log_performance_decorator(include_memory=True)
def heavy_processing(data: list) -> dict:
    # 重い処理
    return result

# スタックトレースも記録
@log_performance_decorator(include_stack=True)
def debug_function(param: str) -> None:
    # デバッグ対象の処理
    pass
```

#### 構造化ログの特徴
- **JSON形式**: 機械解析可能な構造化データ
- **コンテキスト情報**: 豊富なメタデータ付きログ
- **機密情報フィルタリング**: パスワード・トークンなどの自動除去
- **パフォーマンス最適化**: キーキャッシュによる高速化
- **Claude Code最適化**: 自動解析・デバッグ支援

**JSON出力例**:
```json
{
    "timestamp": "2025-01-15T15:30:00",
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

### ブランチ管理・PR作成手順

#### 基本方針
**⚠️ 重要**: PR作成前は必ずmainブランチとの同期を確認すること

#### 緊急対応
PRが「ブランチが最新でない」エラーになった場合:
```bash
git checkout main && git pull origin main
git checkout feat/issue-xxx-description && git rebase main
git push --force-with-lease
```

#### よくある失敗パターン
❌ **NG**: mainブランチを更新せずにPR作成
❌ **NG**: rebaseせずに古いコミットでPR作成
❌ **NG**: `git merge main`を使用（履歴が汚くなる）
✅ **OK**: 必ずrebaseを使用してlinearな履歴を維持

---

## 🧪 テスト・デバッグ

### テスト戦略

- **ユニットテスト**: 各coreモジュールの境界値テスト
- **統合テスト**: Parser→Renderer のエンドツーエンドテスト  
- **E2Eテスト**: CLI経由の実ファイル変換テスト
- **ゴールデンテスト**: 期待出力との厳密比較
- **パフォーマンステスト**: 大容量ファイル処理検証

### デバッグ機能一覧

#### 1. GUIデバッグロガー

GUIアプリケーションの動作を詳細に追跡するための包括的なデバッグシステム。

**基本使用方法**
```bash
# GUIデバッグモードで起動
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher
```

**詳細設定**
```bash
# ログレベル指定
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_LOG_LEVEL=DEBUG python3 -m kumihan_formatter.gui_launcher

# カスタムログファイル
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_LOG_FILE=/tmp/custom_debug.log python3 -m kumihan_formatter.gui_launcher

# コンソール出力も有効
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_CONSOLE_LOG=true python3 -m kumihan_formatter.gui_launcher
```

**機能詳細**

**ログ記録対象:**
- GUI初期化プロセス
- モジュールインポート処理
- ボタンクリックなどのUIイベント
- ファイル選択、ディレクトリ操作
- エラーとスタックトレース
- パフォーマンス計測

**ログファイル出力:**
- デフォルト場所: `/tmp/kumihan_gui_debug.log`
- ローテーション機能付き
- セッションID付きで識別可能

**リアルタイムログビューアー:**
- GUI内で「ログ」ボタンをクリック
- レベル別フィルタリング（DEBUG, INFO, WARNING, ERROR）
- 自動スクロール機能
- ログクリア機能
- 外部エディタでファイルを開く機能

#### 2. 開発ログ機能 (CLI)

コマンドライン版での詳細ログ機能。

```bash
# 開発ログ有効化
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# ログファイル確認
ls /tmp/kumihan_formatter/
cat /tmp/kumihan_formatter/dev_log_*.log
```

**特徴**
- 出力先: `/tmp/kumihan_formatter/`
- ファイル名: `dev_log_<セッションID>.log`
- 自動クリーンアップ: 24時間経過後に削除
- サイズ制限: 5MB（超過時は自動ローテーション）

### 一般的な問題と対処法

#### GUIアプリがクラッシュする場合

1. **デバッグモードで起動**
   ```bash
   KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher
   ```

2. **ログファイルを確認**
   ```bash
   tail -f /tmp/kumihan_gui_debug.log
   ```

3. **インポートエラーの確認**
   - ログでインポート失敗の詳細を確認
   - Pythonパスの問題を特定

#### GUIが表示されない場合

1. **コンソール出力を有効化**
   ```bash
   KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_CONSOLE_LOG=true python3 -m kumihan_formatter.gui_launcher
   ```

2. **tkinterの動作確認**
   ```python
   import tkinter as tk
   root = tk.Tk()
   root.mainloop()
   ```

#### パフォーマンス問題の調査

1. **パフォーマンスログの確認**
   - ログビューアーで各操作の実行時間を確認
   - ボトルネックとなる処理を特定

2. **メモリ使用量の監視**
   - psutilがある場合、起動時メモリ使用量を記録

#### 変換処理のデバッグ

1. **CLIでの詳細ログ**
   ```bash
   KUMIHAN_DEV_LOG=true kumihan convert --debug input.txt output.txt
   ```

2. **構文チェック**
   ```bash
   kumihan check-syntax manuscript.txt
   ```

### 開発者向けTips

#### デバッグロガーの活用

**カスタムログ追加:**
```python
from kumihan_formatter.core.debug_logger import debug, info, warning, error

# 関数の開始/終了をログ
@log_gui_method
def my_function(self):
    info("カスタム処理開始")
    # 処理内容
    info("カスタム処理完了")

# GUIイベントのログ
log_gui_event("button_click", "custom_button", "追加情報")
```

**パフォーマンス計測:**
```python
import time
from kumihan_formatter.core.debug_logger import log_performance

start_time = time.time()
# 処理内容
duration = time.time() - start_time
log_performance("処理名", duration)
```

#### ログビューアーの使い方

1. **デバッグモードでGUI起動**
2. **「ログ」ボタンをクリック**
3. **フィルタリング設定:**
   - レベル選択でログを絞り込み
   - 自動スクロールのON/OFF切り替え
4. **ログクリア:** 不要なログを削除
5. **外部エディタ:** 詳細分析のためファイルを開く

#### トラブルシューティング手順

1. **現象の再現**
   - デバッグモードで同じ操作を実行
   - ログで問題箇所を特定

2. **ログ分析**
   - ERRORレベルでフィルタリング
   - スタックトレースを確認
   - 直前のINFO/DEBUGログで原因を推定

3. **修正と検証**
   - 修正後、同じ手順で動作確認
   - ログで正常な動作を確認

### 本番環境での注意事項

- デバッグ機能は開発/テスト環境でのみ使用
- 本番環境では環境変数を設定しない
- ログファイルのサイズと保存期間に注意
- 機密情報がログに含まれないよう確認

### 関連ファイル

- `kumihan_formatter/core/debug_logger.py` - デバッグロガー本体
- `kumihan_formatter/core/log_viewer.py` - ログビューアーウィンドウ
- `kumihan_formatter/gui_launcher.py` - GUI統合部分
- `/tmp/kumihan_gui_debug.log` - デフォルトログファイル
- `/tmp/kumihan_formatter/` - 開発ログディレクトリ

---

## 🔧 リファクタリング

### リファクタリングガイドライン

#### 概要
Kumihan-Formatterプロジェクトにおけるリファクタリングの判断基準、優先度、実施手順を明文化

#### リファクタリング判断基準

**ファイルレベル基準**

| 優先度 | 行数 | 複雑度 | 対応 |
|--------|------|--------|------|
| 🚨 **緊急** | 300行超過 | 15以上 | 即座にリファクタリング |
| 🔴 **高** | 250行超過 | 12以上 | 次回作業時に対応 |
| 🟡 **中** | 200行超過 | 10以上 | 機能追加時に考慮 |
| 🟢 **低** | 150行以下 | 8以下 | 現状維持 |

**関数レベル基準**

| 優先度 | 行数 | 複雑度 | 対応 |
|--------|------|--------|------|
| 🚨 **緊急** | 50行超過 | 8以上 | 即座に分割 |
| 🔴 **高** | 40行超過 | 6以上 | 次回作業時に分割 |
| 🟡 **中** | 30行超過 | 5以上 | 機能追加時に検討 |
| 🟢 **低** | 20行以下 | 3以下 | 現状維持 |

#### リファクタリング手順

**Phase 1: 事前準備**

1. **テストの確認**
   ```bash
   # 既存テストの実行
   make test
   
   # カバレッジ確認
   make coverage
   ```

2. **品質チェック**
   ```bash
   # 静的解析実行
   make lint
   
   # アーキテクチャ検証
   make arch-check
   ```

3. **Issue作成**
   - リファクタリング対象と理由を明記
   - ラベル `リファクタリング` を付与

**Phase 2: リファクタリング実施**

1. **小さな単位での実施**
   - 1つの関数・クラスずつ対応
   - 機能変更とリファクタリングを分離

2. **テスト駆動リファクタリング**
   ```bash
   # 各変更後にテスト実行
   make test
   
   # 品質チェック
   make pre-commit
   ```

3. **コミット単位の最適化**
   - 1つのリファクタリング = 1つのコミット
   - 明確なコミットメッセージ

### 漸進的リファクタリングガイド

#### 概要
大規模リファクタリングを回避し、継続的な品質改善を実現する

#### Claude Code Hook警告への対応

Claude Code使用時に以下のメッセージが表示される場合の対応手順：

```
PreToolUse:Bash [~/.claude/hook_pre_commands.sh] failed with
non-blocking status code 1: No stderr output
```

**警告の意味**
- **status code 1**: 非ブロッキングエラー（処理継続）
- **技術的負債検出**: 300行制限違反やアーキテクチャルール違反
- **予防システム**: Issue #476のような大規模リファクタリングを予防

**即座の対応手順**
1. **現状確認**
   ```bash
   python3 scripts/check_file_size.py --max-lines=300
   python3 scripts/architecture_check.py
   ```

2. **優先度付け**
   - **高**: 1000行超のファイル
   - **中**: 500-1000行のファイル
   - **低**: 300-500行のファイル

3. **段階的修正**
   ```bash
   # 最大違反ファイルから順に対応
   find kumihan_formatter -name "*.py" -exec wc -l {} + | sort -rn | head -5
   ```

#### 基本原則

**1. Boy Scout Rule（ボーイスカウトルール）**
> "キャンプ場は来た時よりも美しく去る"

```python
# ❌ 悪い例：コードを触ったが改善しない
def process_file(file_path):
    # 既存の長い関数に機能追加のみ
    ...  # 200行の既存コード
    new_feature_code()  # 新機能を追加するだけ

# ✅ 良い例：触ったコードは改善する
def process_file(file_path):
    # 機能追加と同時に既存コードも改善
    file_data = _load_file(file_path)  # 抽出
    processed_data = _process_data(file_data)  # 抽出
    new_feature_result = _apply_new_feature(processed_data)  # 新機能
    return _save_result(new_feature_result)  # 抽出

def _load_file(file_path):
    """ファイル読み込み処理を分離"""
    # 既存コードから抽出

def _process_data(data):
    """データ処理を分離"""
    # 既存コードから抽出
```

**2. 2つのハット原則**
機能追加とリファクタリングを同時に行わない：

```bash
# ✅ 正しいアプローチ
git commit -m "refactor: extract file loading logic"
git commit -m "feat: add new processing feature"

# ❌ 間違ったアプローチ
git commit -m "feat: add feature and refactor everything"
```

**3. 安全第一の原則**
- リファクタリング前後でテスト結果が変わらない
- 小さな変更を積み重ねる
- 一度に変更するファイル数を制限

#### 実践手法

**レベル1: 日常的改善（毎日）**

**命名改善**
```python
# Before
def proc(d):
    return d * 2

# After
def double_value(data: float) -> float:
    return data * 2
```

**コメント改善**
```python
# Before
# TODO: fix this later
def complex_function():
    pass

# After
def complex_function():
    """Calculate conversion rate based on input metrics

    Args:
        metrics: Input performance metrics

    Returns:
        Conversion rate as percentage

    TODO: Add caching for expensive calculations (Issue #123)
    """
    pass
```

**小さな関数抽出**
```python
# Before: 長い関数
def validate_input(data):
    # 30行の検証ロジック

# After: 機能分割
def validate_input(data):
    _validate_format(data)
    _validate_business_rules(data)
    _validate_constraints(data)
```

**レベル2: 週次改善（毎週）**

**クラス責任分離**
```python
# Before: 神クラス
class FileProcessor:
    def read_file(self): pass
    def validate_data(self): pass
    def transform_data(self): pass
    def save_file(self): pass
    def send_email(self): pass  # 責任外

# After: 責任分離
class FileReader:
    def read_file(self): pass

class DataValidator:
    def validate_data(self): pass

class DataTransformer:
    def transform_data(self): pass

class FileWriter:
    def save_file(self): pass

class NotificationService:  # 別責任
    def send_email(self): pass
```

#### リファクタリングパターン

**パターン1: Extract Method（メソッド抽出）**
```python
# Before
def process_order(order):
    # 50行の処理...
    total = 0
    for item in order.items:
        if item.category == 'book':
            total += item.price * 0.9  # 書籍割引
        elif item.category == 'electronics':
            total += item.price * 0.95  # 電子機器割引
        else:
            total += item.price
    # さらに20行の処理...

# After
def process_order(order):
    total = _calculate_total_with_discounts(order.items)
    # 残りの処理...

def _calculate_total_with_discounts(items):
    """割引適用後の総額を計算"""
    total = 0
    for item in items:
        total += _apply_category_discount(item)
    return total

def _apply_category_discount(item):
    """カテゴリ別割引を適用"""
    discounts = {
        'book': 0.9,
        'electronics': 0.95
    }
    return item.price * discounts.get(item.category, 1.0)
```

### 効率的リファクタリング・ガイド

#### 問題の背景

Issue #509: Token無駄遣い事例
- **問題**: 既存テストファイル分割時に、ゼロから書き直してしまった
- **影響**: 10,000+ tokenの無駄遣い（本来は1,000-2,000 tokenで済む）
- **原因**: 既存コード活用よりも新規作成を選択

#### 解決策

**1. 既存コード分割の正しい手順**

**❌ 間違った方法（Token無駄遣い）**
```bash
# 既存のtest_convert_command.py（406行）を分割する場合
# 1. 新しいテストファイルを作成
# 2. ゼロからテストケースを書き直し
# 3. 既存ロジックを再実装
```

**✅ 正しい方法（Token効率化）**
```bash
# 1. 既存ファイルの内容確認
wc -l tests/test_convert_command.py  # 406行

# 2. 分割ポイントの特定
# - line 1-135: 基本機能テスト
# - line 136-270: 高度機能テスト
# - line 271-406: 統合テスト

# 3. 機械的な分割実行
head -n 135 tests/test_convert_command.py > tests/test_convert_command_basic.py
sed -n '136,270p' tests/test_convert_command.py > tests/test_convert_command_advanced.py
tail -n +271 tests/test_convert_command.py > tests/test_convert_command_integration.py

# 4. import文の調整（最小限）
# 各ファイルの先頭に必要なimport文を追加

# 5. 元ファイルの削除
rm tests/test_convert_command.py
```

**効率化の効果**

| 作業方法 | Token使用量 | 作業時間 | 品質 |
|----------|-------------|----------|------|
| **効率的分割** | 1,000-2,000 | 10-15分 | 高 |
| **無駄な再作成** | 10,000+ | 60-90分 | 低 |

---

## 📦 リリース・配布

### リリースガイド

#### 重要な前提条件

- **mainブランチは保護されている**: 直接プッシュ不可
- **全変更はPR経由**: バージョン変更も含む
- **オートマージ必須**: `gh pr merge PR番号 --auto --merge`
- **正式リリースは要許可**: v1.0.0以上は明示的許可必須

#### リリース手順

**1. 事前準備**

```bash
# 最新の状態に更新
git checkout main
git pull origin main

# 現在のバージョンを確認
git tag --list "v*" | sort -V | tail -5
```

**2. バージョン変更（PR経由）**

```bash
# リリースブランチを作成
git checkout -b release/v0.9.0-alpha.X

# バージョン番号を更新
# - pyproject.toml の version
# - kumihan_formatter/__init__.py の __version__

# 変更をコミット
git add -A
git commit -m "release: bump version to v0.9.0-alpha.X"

# PRを作成
gh pr create --title "release: v0.9.0-alpha.X" --body "$(cat <<'EOF'
## Summary
- バージョン番号を v0.9.0-alpha.X に更新

## Changes
- pyproject.toml: version更新
- kumihan_formatter/__init__.py: __version__更新

## Test plan
- [ ] make test でテスト実行
- [ ] バージョン番号の一致確認

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"

# 🚨 重要: オートマージ設定（必須）
gh pr merge PR番号 --auto --merge
```

**3. マージ完了後のタグ作成**

```bash
# PRマージ完了を確認
git checkout main
git pull origin main

# テスト実行（推奨）
make test

# リリースタグを作成
git tag v0.9.0-alpha.X

# タグをプッシュ
git push origin v0.9.0-alpha.X
```

**4. リリース完了確認**

```bash
# タグが作成されたか確認
git tag --list "v0.9.0-alpha.X"

# リモートにタグがプッシュされたか確認
git ls-remote --tags origin | grep v0.9.0-alpha.X
```

#### リリースタイプ別手順

**αリリース（アルファ版）**

- **命名規則**: `v0.9.x-alpha.x`
- **用途**: テスト・改善用
- **制約**: 特になし
- **テスト**: `make test`で基本確認

**正式リリース**

- **命名規則**: `v1.0.0`以上
- **用途**: 本番利用
- **制約**: **ユーザーの明示的許可が必須**
- **テスト**: 全テストスイート実行

### 自動マージ設定ガイド

#### 概要

mo9mo9-uwu-mo9mo9 ユーザー専用の自動マージ機能を設定しました。

#### 実装済み機能

**1. 自動マージワークフロー**
- **ファイル**: `.github/workflows/auto-merge.yml`
- **対象**: mo9mo9-uwu-mo9mo9 のPRのみ
- **条件**: テスト成功時に自動squashマージ

**2. 動作条件**
- ✅ PRの作成者が `mo9mo9-uwu-mo9mo9`
- ✅ PRがdraftでない
- ✅ テストが成功している
- ✅ PRがマージ可能状態

**3. 機能詳細**

**自動コメント**
PRオープン時に自動で通知コメントを投稿：
```
🤖 **Auto-merge enabled**

This PR will be automatically merged when all tests pass.

- ✅ Author: mo9mo9-uwu-mo9mo9
- ⏳ Waiting for tests to complete...

*Auto-merge is only available for mo9mo9-uwu-mo9mo9's PRs*
```

**自動マージ**
- **マージ方式**: squash merge
- **コミットメッセージ**: `PR title (#PR番号)` + `🤖 Auto-merged after successful tests`

### ブランチ保護設定ガイド

#### なぜブランチ保護が必要か

**問題点**
- **CI/CDバイパス**: 直接プッシュでGitHub Actionsをスキップ可能
- **品質劣化リスク**: pre-commit hookとCI/CDを両方回避される危険性
- **技術的負債蓄積**: 300行制限・アーキテクチャチェックの強制力不足

**解決策**
GitHub Actionsの品質チェックを**必須**にして、全てのコード変更を強制的にチェック

#### 推奨ブランチ保護設定

**基本設定**
```
対象ブランチ: main
- Restrict pushes that create files: 有効
- Require a pull request before merging: 有効
- Require status checks to pass before merging: 有効
```

**必須ステータスチェック**
以下のGitHub Actionsチェックを**必須**に設定：

```yaml
必須チェック項目:
✅ quality-check / quality-check
```

**詳細設定**
```yaml
Branch Protection Rules:
  Branch name pattern: main

  Settings:
    ✅ Require a pull request before merging
        - Require approvals: 1
        - Dismiss stale reviews: 有効
        - Require review from code owners: 有効

    ✅ Require status checks to pass before merging
        - Require branches to be up to date: 有効
        - Status checks found in the last week:
          - quality-check / quality-check

    ✅ Require conversation resolution before merging

    ✅ Restrict pushes that create files
        - Restrict pushes that create files larger than 100 MB: 有効

    ✅ Require signed commits: 有効（推奨）

    ❌ Allow force pushes: 無効
    ❌ Allow deletions: 無効
```

---

## 💬 コミュニケーション

### PRレビューガイド

#### レビュー観点

**必須チェック項目**

1. **コード品質**: 既存のコーディング規約に準拠しているか
2. **テスト**: 変更に対する適切なテストが実施されているか
3. **ドキュメント**: 必要な更新が行われているか
4. **影響範囲**: 他の機能への影響がないか

**詳細チェックポイント**

- ✅ Black によるフォーマットが適用されている
- ✅ 型ヒントが適切に使用されている
- ✅ テストが全てパスしている（make test で確認）
- ✅ 変更内容がIssueの要件を満たしている

#### レビューコメントのテンプレート

**✅ Approved例**

```markdown
## レビュー結果: ✅ Approved

### レビュー観点
1. **コード品質**: 既存のコーディング規約に準拠しているか
2. **テスト**: 変更に対する適切なテストが実施されているか
3. **ドキュメント**: 必要な更新が行われているか
4. **影響範囲**: 他の機能への影響がないか

### 確認結果
- ✅ Black によるフォーマットが適用されている
- ✅ 型ヒントが適切に使用されている
- ✅ テストが全てパスしている（make test で確認）
- ✅ 変更内容が Issue #XXX の要件を満たしている

このPRは問題なくマージ可能です。
```

**❌ Changes Requested例**

```markdown
## レビュー結果: ❌ Changes Requested

### レビュー観点と問題点
1. **テスト不足**: 新規追加した機能に対するテストケースがありません
   - `src/new_feature.py` の `process_data()` メソッドのテストを追加してください

2. **エラーハンドリング**: 異常系の処理が不十分です
   - ファイル読み込み失敗時の例外処理を追加してください（src/utils.py:45）

修正後、再度レビューします。
```

### Issue管理

#### ラベル体系

**Issue作成時のラベル付与原則**

- **カテゴリラベル（必須）**: Issue の種別を明確にする
- **優先度ラベル（必須）**: 対応の緊急度を示す
- **難易度ラベル（推奨）**: 作業量の目安を提供
- **技術領域ラベル（該当時）**: 関連するコンポーネントを明示

**カテゴリラベル（必須）**
| ラベル | 説明 | 使用例 |
|-------|------|--------|
| `バグ` | 何かが正常に動作しない | エラー発生、予期しない動作 |
| `機能改善` | 新機能・機能改善のリクエスト | 新機能追加、既存機能の改良 |
| `ドキュメント` | ドキュメントの改善・追加 | README更新、API文書追加 |
| `リファクタリング` | コード改善・整理 | コード整理、設計改善 |

**優先度ラベル（必須）**
| ラベル | 説明 | 対応目安 |
|-------|------|----------|
| `緊急` | システム停止・セキュリティ問題 | 即座に対応 |
| `通常` | 通常の機能改善・軽微なバグ | 通常のスケジュール |
| `低優先度` | 時間があるときに対応 | 余裕のある時 |

**技術領域ラベル（該当時）**
| ラベル | 説明 |
|-------|------|
| `パーサー` | 解析エンジン関連 |
| `レンダラー` | HTML生成関連 |
| `テンプレート` | テンプレート関連 |
| `CI/CD` | 継続的インテグレーション・デプロイ関連 |
| `品質改善` | 品質メトリクス・テスト品質向上 |
| `UI改善` | ユーザーインターフェース・表示品質関連 |
| `仕様` | 仕様書と実装の整合性・仕様関連 |

#### Issue作成テンプレート

**バグ報告テンプレート**

```markdown
## バグ報告

### 環境
- OS: 
- Python バージョン: 
- Kumihan-Formatter バージョン: 

### 再現手順
1. 
2. 
3. 

### 期待する動作

### 実際の動作

### エラーメッセージ
```

**機能要望テンプレート**

```markdown
## 機能要望

### 概要
実現したい機能の概要を記載

### 背景・動機
なぜこの機能が必要なのか

### 詳細仕様
- 
- 
- 

### 受け入れ条件
- [ ] 
- [ ] 
- [ ] 

### 参考資料
```

#### Issue完了報告テンプレート

Issue駆動開発完了時は、Issueに以下のテンプレートを使用して詳細な完了報告をコメント：

```markdown
## 作業完了報告

### 実施内容
- 実装した機能・修正内容
- 変更したファイル一覧
- テスト結果

### 確認事項
- [ ] 期待動作の確認
- [ ] テスト全パス
- [ ] ドキュメント更新

### PR
- #XXX でマージ済み

作業完了のため、Issueをクローズします。
```

### 絵文字・特殊文字使用禁止ガイドライン

#### 概要

Kumihan-Formatterでは、**すべての絵文字・特殊文字の使用を原則禁止**としています。これは安定性、保守性、およびクロスプラットフォーム対応の観点から決定された開発方針です。

#### 使用禁止の背景

**発生した問題（Issue #85より）**
- **エンコーディング問題**: macOSでのダブルクリック実行時に絵文字が文字化け
- **環境依存**: ターミナル設定によって表示が異なる
- **保守性低下**: 文字化けがバグの根本原因となる

**影響範囲**
- CLI出力メッセージの文字化け
- ログファイルの可読性低下
- 国際化対応の阻害
- デバッグ作業の困難化

#### 対象・適用範囲

**禁止対象**

**絵文字全般**
```
🔍 📝 🎨 ⚠️ ✅ ❌ 💡 🚀 📁 🌐 🖱️ 🏗️ 📚 🔧 🐍 ⏳ 🏠 📄 🖼️ 📊
```

**特殊記号・装飾文字**
```
★ ☆ ◆ ◇ ■ □ ● ○ ▲ △ ▼ ▽ ◀ ◁ ▶ ▷ 
※ § ¶ † ‡ • ‰ ′ ″ ‴ ‵ ‶ ‷ ‸ ‹ › « »
```

**適用範囲**

**必須適用**
- **Python コード**: すべての出力メッセージ
- **シェルスクリプト**: 出力・エラーメッセージ
- **テストコード**: エラーメッセージ・ログ出力
- **技術文書**: 開発者向けドキュメント

**例外（限定的許可）**
- **README.md**: ユーザー向け視覚効果のため許可
- **プレゼン資料**: 外部発表用資料での限定使用
- **コード内コメント**: 説明目的での最小限使用

#### 推奨代替表現

**基本的な置換ルール**

| 絵文字 | 推奨代替 | 用途・説明 |
|--------|----------|------------|
| 🔍 | `[検証]` | 検証・確認処理 |
| 📝 | `[処理]` | データ処理・変換 |
| 🎨 | `[生成]` | HTML生成・レンダリング |
| ⚠️ | `[警告]` | 警告メッセージ |
| ✅ | `[完了]` | 成功・完了状態 |
| ❌ | `[エラー]` | エラー・失敗状態 |
| 💡 | `[ヒント]` | ヒント・補足情報 |
| 🚀 | `[開始]` | 処理開始・実行 |

**色付きタグ（Rich library使用時）**

```python
# 良い例: 色付きタグを使用
console.print("[green][完了][/green] ファイル変換が正常に完了しました")
console.print("[yellow][警告][/yellow] 設定ファイルが見つかりません")
console.print("[red][エラー][/red] ファイルの読み込みに失敗しました")

# 悪い例: 絵文字を使用
console.print("[green]✅[/green] ファイル変換が正常に完了しました")  # 禁止
console.print("[yellow]⚠️[/yellow] 設定ファイルが見つかりません")   # 禁止
console.print("[red]❌[/red] ファイルの読み込みに失敗しました")     # 禁止
```

**プレーンテキスト出力**

```bash
# 良い例: シェルスクリプトでの代替表現
echo "[完了] セットアップが正常に完了しました"
echo "[警告] Python 3.9以上が必要です"
echo "[エラー] ファイルが見つかりません"

# 悪い例: 絵文字を使用
echo "✅ セットアップが正常に完了しました"  # 禁止
echo "⚠️ Python 3.9以上が必要です"      # 禁止
echo "❌ ファイルが見つかりません"        # 禁止
```

---

## 🛠️ トラブルシューティング

### よくある問題

#### 1. 仮想環境エラー
```bash
# 仮想環境をアクティベート
source .venv/bin/activate
# または
source venv/bin/activate
```

#### 2. モジュール未見つけエラー
```bash
# プロジェクトルートディレクトリにいることを確認
pwd
# /Users/username/GitHub/Kumihan-Formatter であることを確認
```

#### 3. パーミッションエラー
```bash
# .commandファイルに実行権限を付与
chmod +x 記法ツール/*.command
```

### ファイルパス指定

```bash
# 絶対パス
python tools/dev/tools/syntax_fixer.py /path/to/file.txt --fix

# 相対パス（プロジェクトルートから）
python tools/dev/tools/syntax_fixer.py examples/01-quickstart.txt --fix

# ワイルドカード
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix
```

### macOS D&D制限について

**問題**: macOSではセキュリティ制限により、.commandファイルへのD&D機能が正常に動作しない場合があります。

**解決方法**: コマンドラインでの直接実行を推奨します。

### 記法ツール使用ガイド

#### 利用可能ツール

**1. syntax_validator.py（基本版）**
記法エラーの検証のみを行います。

```bash
# 基本的な使用方法
python tools/dev/tools/syntax_validator.py examples/*.txt

# 単一ファイル
python tools/dev/tools/syntax_validator.py examples/01-quickstart.txt
```

**2. syntax_fixer.py（推奨版）**
検証・プレビュー・自動修正の全機能を提供します。

```bash
# 記法エラーの検証のみ
python tools/dev/tools/syntax_fixer.py examples/*.txt

# 修正内容のプレビュー（ファイル変更なし）
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix --preview

# 自動修正の実行（ファイル変更あり）
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix
```

#### コマンドライン実行例

```bash
# プロジェクトルートディレクトリで実行

# 1. 記法エラーの検証
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt

# 2. 修正内容のプレビュー
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix --preview

# 3. 自動修正の実行
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix

# 4. 静かなモード（詳細出力を抑制）
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix --quiet
```

#### 使用パターン

**開発ワークフロー**

1. **エラー発見**: 記法問題の確認
   ```bash
   python tools/dev/tools/syntax_fixer.py examples/elements/item-template.txt
   ```

2. **修正確認**: 修正内容の事前確認
   ```bash
   python tools/dev/tools/syntax_fixer.py examples/elements/item-template.txt --fix --preview
   ```

3. **自動修正**: 実際のファイル修正
   ```bash
   python tools/dev/tools/syntax_fixer.py examples/elements/item-template.txt --fix
   ```

**バッチ処理**

```bash
# 全テンプレートファイルを一括処理
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix

# 全サンプルファイルを一括処理
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix --preview

# 特定パターンのファイルのみ
python tools/dev/tools/syntax_fixer.py examples/*template*.txt --fix
```

---

## 📚 プロジェクト履歴

### プロジェクト履歴・レポート

#### Issue #121 Phase 2: 大規模リファクタリング完了レポート

**概要**

Issue #121のPhase 2として、Kumihan-Formatterの大規模なリファクタリングを実施し、技術的負債の大幅な削減と保守性の向上を実現しました。

**達成された目標**

**1. コード複雑性の大幅削減**

| ファイル | 変更前 | 変更後 | 削減率 |
|----------|--------|--------|--------|
| `cli.py` | 737行 | 66行 | **91%** |
| `parser.py` | 454行 | 124行 | **73%** |
| `renderer.py` | 483行 | 196行 | **59%** |

**総削減効果**: 約1,674行から386行へ、**77%の削減**を達成

**2. モジュラー設計の実現**

**パーサーコンポーネント分割**
- `kumihan_formatter/core/keyword_parser.py` (360行) - キーワード解析
- `kumihan_formatter/core/list_parser.py` (325行) - リスト処理
- `kumihan_formatter/core/block_parser.py` (324行) - ブロック構造解析
- `kumihan_formatter/core/ast_nodes.py` (305行) - AST定義

**レンダラーコンポーネント分割**
- `kumihan_formatter/core/html_renderer.py` (384行) - HTML生成
- `kumihan_formatter/core/template_manager.py` (291行) - テンプレート管理
- `kumihan_formatter/core/toc_generator.py` (387行) - 目次生成

#### Issue #300 Phase3: 無駄要素削除完了レポート

**成果概要**

Issue #300 Phase3において、**関心分離とメンテナンス効率化**を重視した大規模な過設計解消を実施し、プロジェクトの大幅な簡素化を達成しました。

**削減効果（全体）**

| 指標 | 削除量 | 効果 |
|------|--------|------|
| **総削除行数** | **11,735行** | プロジェクト規模の大幅縮小 |
| **削除ファイル数** | **47ファイル** | ファイル構造の簡素化 |
| **統合ツール** | 11→3個 | 開発ツールの効率化 |
| **テスト階層** | 4→2層 | テスト構造の簡素化 |
| **ドキュメント統一** | Markdown→Kumihan記法 | 記法の一貫性確保 |

**主要削除カテゴリ**

**1. 過設計アーキテクチャの解消**

**DI Container（依存性注入システム）- 1,551行削除**
```
kumihan_formatter/core/di/          # 1,205行
dev/tests/test_di_container.py      # 346行
```
- **理由**: 完全に未使用、過剰なエンタープライズパターン
- **効果**: アーキテクチャの簡素化、学習コストの削減

**Services層 - 1,545行削除**
```
kumihan_formatter/services/         # 1,545行
```
- **理由**: 機能重複、不要な抽象化レイヤー
- **効果**: 直接的な処理フロー、理解しやすいコード

#### Issue #300 Phase4: 最終簡素化完了レポート

**成果概要**

Issue #300 Phase4において、プロジェクトの最終的な簡素化と最適化を実施し、**さらなる効率性の向上**を達成しました。

**削減効果（Phase4）**

| 指標 | 削除量 | 効果 |
|------|--------|------|
| **総削除行数** | **5,336行** | プロジェクト規模のさらなる縮小 |
| **削除ファイル数** | **39ファイル** | ファイル構造のさらなる簡素化 |
| **統合ツール効果** | 10→3個統合 | 開発ツールの大幅効率化 |
| **テスト構造改善** | 散在→分類配置 | テスト実行・保守効率向上 |
| **ドキュメント整理** | 重複解消 | 情報の一元化・一貫性確保 |

**累積削減効果（Phase1-4総計）**

**定量的成果**
- **Phase1-3削減**: 11,735行
- **Phase4削減**: 5,336行
- **総削減効果**: **17,071行** （プロジェクト規模の約50%削減）

**ファイル数削減**
- **Phase1-3削除**: 47ファイル
- **Phase4削除**: 39ファイル
- **総削除ファイル**: **86ファイル**

#### Phase2 技術的負債解消計画

**目的**: 37件の技術的負債を段階的に解消し、コードベースの健全性を向上
**期間**: 2025-01-15 ～ 2025-01-31
**基準**: 300行/ファイル、20関数/ファイル、5クラス/ファイル

**現状分析**

**優先度別分類**
| 優先度 | 行数範囲 | 件数 | 対象ファイル例 |
|--------|----------|------|----------------|
| **🔥 超高** | >600行 | 7件 | gui_views.py(539), performance/benchmark.py(676) |
| **🚨 高** | 400-600行 | 12件 | gui_controller.py(397), core/file_ops.py(475) |
| **⚠️ 中** | 300-400行 | 18件 | core/keyword_parser.py(521), core/list_parser.py(383) |

#### Issue #500 Phase 3A Implementation Report

**Overview**

Issue #500 Phase 3A implemented comprehensive CLI command testing and infrastructure improvements to establish a robust CLI foundation for the Kumihan-Formatter project.

**Key Metrics**

- **Tests Added**: 96 new test cases
- **Code Coverage**: Increased from 8% to 13%+
- **CLI Commands Tested**: 4 major command groups
- **Error Scenarios Covered**: 50+ error handling scenarios
- **Files Restructured**: 7 files split to meet 300-line limit

**Implementation Details**

**1. CLI Command Testing (`tests/test_cli.py`)**

**Added 18 comprehensive test cases:**

- CLI basic functionality validation
- Command registration testing
- Encoding setup verification
- Legacy routing support
- Error handling scenarios

**2. Convert Command Testing (`tests/test_convert_command.py`)**

**Added 17 test cases covering:**

- Command creation and validation
- CLI integration testing
- Option handling verification
- Error scenario testing

#### 暗黙仕様分析レポート - Issue #75

**Phase 1-2 完了**: 暗黙仕様の特定とサポート可否判断

**調査概要**

プロジェクト内での「暗黙的に期待される記法」の使用状況を全面調査し、正式サポートするか削除するかの技術的判断を実施。

**発見された重大な問題**

**問題の概要**
**ドキュメント内でのMarkdown記法大量使用により、ユーザーの期待と実際の仕様に深刻な乖離が発生**

**具体的な矛盾**

| 公式仕様（SPEC.md） | ドキュメント内の実態 | 影響度 |
|-------------------|-------------------|--------|
| 「行頭 # 記法は非サポート」 | 17ファイルで200回以上使用 | 🔴 極めて深刻 |
| 「**太字** 記法は非サポート」 | 15ファイルで100回以上使用 | 🔴 極めて深刻 |
| 「Markdown記法は使用禁止」 | 全ドキュメントで大量使用 | 🔴 極めて深刻 |

**Phase 1: 暗黙仕様の特定結果**

**examples/ フォルダ調査結果** ✅
**結果**: 高い一貫性を確認
- Kumihan-Formatter独自記法で統一されている
- 暗黙的Markdown記法はほぼ使用されていない
- 意図的なテスト用記法のみ含有

**docs/ フォルダ調査結果** 🚨
**結果**: 深刻な不整合を確認

**使用統計**
| 記法種類 | 使用ファイル数 | 総使用回数 | 状況 |
|----------|----------------|------------|------|
| 行頭 # 見出し | 17/22ファイル | 200回以上 | 🔴 極めて深刻 |
| **太字** 記法 | 15/22ファイル | 100回以上 | 🔴 極めて深刻 |
| テーブル記法 | 8/22ファイル | 50回以上 | 🟡 中程度 |
| コードブロック | 22/22ファイル | 300回以上 | 🟢 許容範囲 |
| 番号付きリスト | 10/22ファイル | 30回以上 | 🟢 正式サポート済み |

### スタイルガイド

#### 基本原則

**1. シンプルさを重視**
- 複雑な組み合わせより、シンプルで読みやすい記法を優先
- 必要最小限の装飾で十分な表現力を確保

**2. 一貫性の保持**
- 同じ意味の装飾には同じ記法を使用
- プロジェクト内で記法の使い方を統一

**3. 可読性の確保**
- ソースファイルが人間にとって読みやすいこと
- HTML出力も見やすく構造化されること

#### 推奨記法パターン

**基本的な文書構造**

```text
;;;見出し1
章タイトル
;;;

段落は空行で区切ります。
これは同じ段落の続きです。

新しい段落です。

;;;見出し2
節タイトル
;;;
```

**✅ Good:** 階層構造が明確で読みやすい

**文字装飾**

```text
;;;太字
重要な情報
;;;

;;;イタリック
補足説明
;;;

;;;太字+イタリック
非常に重要な情報
;;;
```

**✅ Good:** 目的に応じた適切な強調

#### 避けるべき記法

**非サポート記法の使用**

```text
❌ Bad:
# これはMarkdown記法です（非サポート）
**太字**（非サポート）
*イタリック*（非サポート）

✅ Good:
;;;見出し1
これは正しい見出し記法です
;;;

;;;太字
正しい太字記法
;;;
```

**color属性の誤用**

```text
❌ Bad:
;;;ハイライト color=#ff0000+太字;;;
（color属性の後に + は使えません）

✅ Good:
;;;太字+ハイライト color=#ff0000;;;
（+ の順序を正しく）
```

**目次マーカーの手動使用**

```text
❌ Bad:
;;;目次;;;
（手動で目次マーカーを書くのは禁止）

✅ Good:
（目次は自動生成されるため、マーカー不要）
```

### 更新履歴

- **2025-07-14**: GUIデバッグロガー機能を追加
- **2025-07-08**: 開発ログ機能を追加 (Issue#446)
- **2025-06-29**: Issue #300 Phase4完了
- **2025-06-29**: Issue #300 Phase3完了  
- **2025-06-26**: Issue #121 Phase2完了
- **2025-06-24**: 絵文字使用禁止ガイドライン策定（Issue #85対応）
- **2025-01-24**: CLAUDE.md バージョン2.0.0リリース
- **2025-01-15**: Phase2技術的負債解消計画策定

---

## 🔗 関連ドキュメント

**ルートレベル**: 
- [`README.md`](../../README.md) - プロジェクト概要
- [`CLAUDE.md`](../../CLAUDE.md) - Claude Code指示ファイル  
- [`SPEC.md`](../../SPEC.md) - 記法仕様書
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) - コントリビューションガイド
- [`CHANGELOG.md`](../../CHANGELOG.md) - 変更履歴

**ユーザー向け**: 
- [`docs/user/`](../user/) - エンドユーザー向けドキュメント

**分析レポート**: 
- [`docs/analysis/`](../analysis/) - 詳細分析結果

---

**このガイドは、Kumihan-Formatterの開発に関する包括的な情報を提供します。プロジェクトの成長とともに継続的に更新されます。**

*最終更新: 2025-07-28*
*バージョン: 1.0.0*
*統合ファイル数: 27ファイル*