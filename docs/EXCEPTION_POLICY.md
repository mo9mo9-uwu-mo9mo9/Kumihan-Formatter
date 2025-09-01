# 例外ポリシー（設計）

目的: 例外の統一的な設計指針を定め、API契約・保守性を向上する。

## スコープ
- 公開API（`unified_api.KumihanFormatter`、`parser` ファサード）
- コア層（parsing/processing/rendering/io）
- ユーティリティ層（file ops など）

## 命名・階層
- ルート例外: `KumihanError`（共通の基底、`Exception` を継承）
- 分類例外:
  - `KumihanSyntaxError`（構文/入力記法エラー）
  - `KumihanProcessingError`（解析・変換処理エラー）
  - `KumihanFileError`（入出力・パス・権限エラー）
  - `KumihanConfigError`（設定・環境・前提条件エラー）
- 配置: `kumihan_formatter/core/common/exceptions.py`（将来導入）

## 送出指針
- 例外は「呼び出し側で予防不能な失敗」に限定して送出する。
- 入力妥当性は「API境界」または「コンポーネント境界」で早期検証。
- 外部例外（`OSError`, `UnicodeError`, など）は `from` でラップして原因を保持する。
- メッセージは簡潔に（ユーザー向け→日本語、開発者向け→詳細はログ）。

## API契約
- `KumihanFormatter`：
  - `convert/convert_text/parse_text/validate_syntax` は「通常成功/失敗を返す」現行契約を維持。
  - 重大障害（例: テンプレート読み込み不能、I/O不可、内部不変条件違反）のみ例外を送出。
- `parser` ファサード：
  - `parse()` は「失敗時もNodeで表現（エラーNode）」を基本。プログラマブルに扱う前提。
  - ただし I/O の失敗は `KumihanFileError` を送出。

## ログと例外の使い分け
- 例外を送出する場合：INFO/DEBUG で前後関係を残し、ERROR は上位ハンドラに任せる。
- リカバリ可能な状況：WARNING を記録し、フォールバック（例: デフォルトテンプレート）。

## メッセージ標準
- 先頭は要点を短く（1行）。詳細は括弧や追記で簡潔に。
- ファイル/パス/サイズなど定量情報は必ず含める。
- ユーザー向け文言は日本語、内部Causeはログで英語でも可。

## 例外マッピング（現状→将来）
- 現在：標準例外 + エラーノード/エラーHTMLで通知
- 将来：
  - I/O層：`KumihanFileError`
  - 構文層：`KumihanSyntaxError`
  - 処理層：`KumihanProcessingError`
  - 設定層：`KumihanConfigError`

## サンプル（将来導入時）
```python
try:
    html = formatter.convert_text(text)
except KumihanFileError as e:
    logger.error("入出力で失敗: %s", e)
    raise
```

## 段階導入の方針
1. 例外クラスの追加（コード未切替）
2. I/O層→構文層→処理層の順に段階置換（小PR分割）
3. ドキュメント/サンプル更新、移行ガイド追記

