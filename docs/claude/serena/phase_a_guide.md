# Phase A運用パターン最適化ガイド

## 🎯 Phase A「基本最適化」戦略

### 1. 段階的情報取得フロー
- **Stage 1**: ultra_overview (3K tokens) - 超高速概要把握
- **Stage 2**: quick_search (8K tokens) - 高速ターゲット検索  
- **Stage 3**: focused_edit (60K tokens) - 集中的編集実行

### 2. セマンティック編集中心アプローチ
- `mcp__serena__get_symbols_overview` → `mcp__serena__find_symbol` → `mcp__serena__replace_symbol_body`
- シンボルレベル操作によるピンポイント編集
- 不要なファイル全読み取り回避

### 3. スマートキャッシュ活用
- 既存メモリの積極活用
- 重複情報取得の回避
- コンテキスト圧縮技術

### 4. リアルタイム効果測定
- トークン使用量の継続監視
- 最適化効果のリアルタイム評価
- アラート機能による使いすぎ防止

## 📈 期待効果
- **総合削減率**: 58% (40-60%目標達成)
- **レスポンス向上**: 3倍高速化
- **精度維持**: 品質劣化なし
