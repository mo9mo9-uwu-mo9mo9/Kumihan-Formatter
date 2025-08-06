# TOCGenerator包括的テスト要件 - Issue #799

## 対象クラス分析
- **TOCGeneratorクラス**: 8つの主要メソッド
  - `__init__()`: 初期化
  - `generate_toc(nodes)`: メイン処理
  - `_collect_headings(nodes)`: ヘッディング収集（再帰処理）
  - `_build_toc_structure(headings)`: 階層構造構築
  - `_generate_toc_html(entries)`: HTML生成
  - `_render_toc_entry(entry)`: 単一エントリHTML生成
  - `should_generate_toc(nodes)`: 自動生成判定
  - `get_toc_statistics(entries)`: 統計情報

- **TOCEntryクラス**: 依存関係
  - `__init__(level, title, heading_id, node)`
  - `add_child(child)`, `is_root_level()`, `get_depth()`, `get_text_content()`

## テストケース設計
### 1. 初期化テスト
- TOCEntryクラスの正常インポート
- 初期状態の確認（entries空リスト、heading_counter=0）

### 2. generate_tocテスト
- **正常系**: 複数ヘッディングでのTOC生成
- **空ノード**: 空リストでの処理
- **単一ヘッディング**: 1つのヘッディングでの処理
- **戻り値検証**: entries, html, has_toc, heading_countの正確性

### 3. _collect_headingsテスト
- **基本収集**: レベル別ヘッディング収集
- **再帰処理**: ネストしたノード構造
- **IDなしヘッディング**: 自動ID生成
- **無限再帰防止**: max_depth制限
- **異常系**: 不正なノード構造

### 4. _build_toc_structureテスト
- **階層構築**: 正しい親子関係
- **レベルジャンプ**: レベル2→4の飛び越し
- **空リスト**: ヘッディングなしの場合
- **同レベル連続**: 同じレベルの複数ヘッディング

### 5. HTML生成テスト
- **_generate_toc_html**: 完全なHTML構造
- **_render_toc_entry**: 単一エントリとネスト
- **HTMLエスケープ**: 特殊文字の適切な処理
- **CSSクラス**: 正しいクラス名付与

### 6. should_generate_tocテスト
- **自動生成判定**: 2つ以上で生成、1つ以下で非生成
- **境界値**: ちょうど2つのヘッディング

### 7. get_toc_statisticsテスト
- **統計情報**: total_entries, levels_used, max_depth, entries_by_level
- **深いネスト**: 複雑な階層での統計
- **空エントリ**: 統計情報の初期値

### 8. エッジケース・異常系
- **循環参照防止**: 不正なネスト構造
- **大量データ**: パフォーマンステスト
- **メモリリーク**: オブジェクト参照の適切な管理

## 実装方針
- **pytest使用**: 標準的なPythonテストフレームワーク
- **モック活用**: Nodeクラスのモック作成
- **フィクスチャ**: 再利用可能なテストデータ
- **アサーション**: 厳密な期待値検証
- **カバレッジ**: 全メソッド・全分岐の網羅