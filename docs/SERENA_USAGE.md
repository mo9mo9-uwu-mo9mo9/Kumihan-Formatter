# Serena MCP 使用ガイド（出力制御・失敗回避）

目的: Serenaツール呼び出し時の過大出力による失敗（"The answer is too long ..."）を回避し、安定運用する。

## 既定
- 検索は狭域から開始し、必要に応じて範囲を広げる。
- `restrict_search_to_code_files=true` を基本とする。
- 非コード/生成物は常時除外（`tmp/**`, `output/**`, `htmlcov/**`, `docs/**`, など）。
- `max_answer_chars` は低め（安全）から。足りなければ段階引き上げ。

## 推奨パラメータ
- search_for_pattern:
  - `paths_include_glob="kumihan_formatter/**|tests/**|scripts/**"`
  - `paths_exclude_glob="tmp/**|output/**|htmlcov/**|docs/**"`
  - `restrict_search_to_code_files=true`
  - `max_answer_chars=120000`
- find_symbol / find_referencing_symbols:
  - まず `relative_path` を対象ファイル/ディレクトリに限定
  - `max_answer_chars=90000`
- get_symbols_overview:
  - `max_answer_chars=60000`
- read_file:
  - 400–600 行単位で分割取得（`start_line`/`end_line`）
  - `max_answer_chars=120000`

## 再試行手順（順守）
1. 範囲をさらに絞る（`relative_path`/`paths_include_glob`）。
2. 検索語を分割して複数回に分ける。
3. `read_file` は 300–400 行単位に更に細分化。
4. それでも不足する場合に限り `max_answer_chars` を 1 段階上げる（+30k〜+60k）。

## メモ
- CLIのシェル出力は 250 行上限。長文は必ず分割。
- 詳細は `.serena/memories/serena_tool_output_limits.md` を参照。

## 初期化/リセット（ローカル運用前提のメモ）
- Serenaはローカルで動作するMCPサーバで、プロジェクト配下に `.serena/` ディレクトリ（`project.yml` と `memories/`）を生成し、設定やメモを保存する。
- リセットは簡単で、以下の流れで初期状態に戻せる:
  1) MCPクライアント/サーバを停止（例: IDEやデスクトップクライアント）。
  2) プロジェクトの `.serena/` を削除。
  3) 必要に応じて再インデックス（例: `uvx --from git+https://github.com/oraios/serena serena index-project`）。
- SSE常駐などを使う場合は、クライアントからポート指定で再接続すれば良い（設定は通常`.serena/`再生成時に復元される）。
