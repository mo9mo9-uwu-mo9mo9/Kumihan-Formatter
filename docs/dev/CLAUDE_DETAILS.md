# CLAUDE開発詳細指示

> Kumihan-Formatter のClaude開発詳細ガイド
> **メイン指示**: [CLAUDE.md](../../CLAUDE.md) を優先参照
> **このファイルの役割**: 開発者向けの補助的な詳細情報を提供

## 1️⃣ 必須運用

### 前提

**言語設定**: [CLAUDE.md](../../CLAUDE.md) を参照

### セッション管理

**詳細**: [CLAUDE.md](../../CLAUDE.md) および [PREAMBLE.md](../../PREAMBLE.md) を参照

### 守るべきファイル/フォルダ

| 種別       | パス                            | 理由           |
| -------- | ----------------------------- | ------------ |
| アンカーファイル | `CLAUDE.md`                   | Claude 指示の中心 |
| 設定       | `.claude/`                    | セッションキー等の機密  |
| ローカル設定   | `.claude/settings.local.json` | 個人環境依存       |

**禁止**: 上記を Git へ push・削除・改名する行為。

---

## 2️⃣ ドキュメント構造

**ドキュメント構造**: [CLAUDE.md](../../CLAUDE.md) のインポートセクションを参照

> 詳細は各ファイルを参照し、**CLAUDE.md には追記をしない** こと。

---

## 3️⃣ 更新手順

1. 追加情報が必要な場合は **別ファイル** を作成し標準Markdownリンク `[title](filename)` で参照。
2. 例外として、本ファイルの「必須運用」節に関連する改訂のみ直接編集。
3. 変更後は `make lint-docs` でリンク切れチェック。

---

## 4️⃣ 開発方針

### ログ実装方針

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

4. **ログメッセージ設計**:
   - コンテキスト情報を含める（ファイルサイズ、処理時間等）
   - Claude Codeが問題を特定しやすい具体的な情報
   - 日本語メッセージでOK

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

---

開発を楽しみましょう 🎉
