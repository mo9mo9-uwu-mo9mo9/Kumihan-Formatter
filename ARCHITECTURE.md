# Kumihan-Formatter アーキテクチャ概要

**2025年最適化版**: 統合最適化・オーバーエンジニアリング解消後  
**設計思想**: シンプル・効率・保守性重視

---

## 🏗️ 全体アーキテクチャ

### 構成概要
```
kumihan_formatter/
├── 🎯 unified_api.py        # 統合エントリーポイント
├── core/                    # コア機能群（api/ rendering/ utilities/ など）
├── parsers/                 # パーサー群（unified_markdown_parser 等）
└── ui/ / managers/          # UI補助・マネージャ群
```

### 統合設計思想
- **Single Entry Point**: unified_api.py経由で全機能アクセス
- **Simple Components**: SimpleParser + SimpleRenderer 組み合わせ
- **Backward Compatibility**: 既存システムとの互換性維持

---

## 🎯 コアコンポーネント

### 1. 統合API (unified_api.py)
```python
class KumihanFormatter:
    """メインエントリーポイント - 175行"""
    - SimpleParser統合
    - SimpleRenderer統合  
    - 設定管理統合
    - エラー処理統合
```

**責任**:
- 外部インターフェース提供
- コンポーネント協調制御
- 設定・状態管理
- エラー統合処理

### 2. MainParser（parsers/main_parser.py）
- 統合パーサー。入力テキストを解析し、内部ノード（Node）へ変換。

### 3. MainRenderer（core/rendering/main_renderer.py）
- 解析結果（Dict/Node）からHTMLを組み立てる統合レンダラー。

---

## 🔄 データフロー

### 処理フロー
```
テキスト入力
    ↓
📝 SimpleParser
    ↓ (ParseResult)
🎨 SimpleRenderer  
    ↓ (HTML)
📄 出力ファイル
```

### データ構造（概要）
- 解析結果は内部ノード（`core.ast_nodes.Node`）または辞書（Dict）で扱われます。
  公開API（`KumihanFormatter`）経由ではDict形式を基本とし、レンダラーがHTML文字列を生成します。

---

## 🚀 最適化された機能

### パフォーマンス最適化
```python
# チャンク処理 (chunk_manager.py)
class ChunkManager:
    """大容量ファイル効率処理 - 200行"""
    - 適応的チャンクサイズ
    - メモリ効率最適化
    - CPU並列処理対応

# 並列処理 (parallel_processing_config.py)  
class ParallelProcessingConfig:
    """並列処理設定 - 129行"""
    - CPU最適ワーカー数
    - 自動チューニング
    - メモリ制限管理
```

### ファイル操作最適化
```python
# ファイル操作 (file_operations_core.py)
- ストリーミング処理
- エンコーディング自動検出
- 大容量ファイル対応
- エラー回復機能
```

---

## 🔌 拡張性・統合性

### プラグイン設計
```python
# パーサー拡張
parsers/
├── unified_keyword_parser.py    # キーワード統合
├── unified_list_parser.py       # リスト統合  
├── unified_markdown_parser.py   # Markdown統合
└── parser_utils.py             # 共通ユーティリティ
```

### レンダラー拡張
```python
rendering/
├── html_formatter.py           # HTML特化
├── element_renderer.py         # 要素レンダリング
├── css_processor.py           # CSS処理
└── output_formatter.py        # 出力フォーマット
```

---

## 🛡️ 品質保証・エラー処理

### 品質保証システム
```python
# バリデーション
core/validation/
- 構文検証
- データ整合性チェック
- パフォーマンス監視

# ログ・監視
core/utilities/logger.py
- 構造化ログ
- パフォーマンス計測
- エラー追跡
```

### エラーハンドリング
```python
※ 現行実装では専用例外は未導入。標準例外で通知（将来導入を検討）。
```

---

## 📊 品質指標・パフォーマンス

### 現状品質指標
```
コード行数:     22,606行 → 8,000行目標 (65%削減計画中)
テストカバレッジ: 2.22% → 6%目標 (向上計画中)
インポート速度:   0.015秒 (優秀)
テスト実行:      1.65秒/39テスト (高速)
```

### パフォーマンス特性
```
小規模ファイル:   <1秒 (即座処理)
中規模ファイル:   1-5秒 (効率処理)  
大規模ファイル:   並列処理 (スケーラブル)
メモリ使用:      最適化済み (チャンク処理)
```

---

## 🔄 進化・保守戦略

### 段階的最適化計画
1. **Phase 1完了**: レガシーファイル削除 (920行削除)
2. **Phase 2進行中**: 巨大ファイル分割 (400行超解消)
3. **Phase 3計画**: 機能重複削除 (8,000行目標)

### 持続可能性確保
- **コード行数制限**: 300行/ファイル上限
- **責任分離**: 単一責任原則厳守
- **テスト品質**: カバレッジ段階的向上
- **文書最小化**: 必要最小限維持

### 開発効率指標
- **機能追加時間**: 50%短縮目標
- **バグ修正効率**: 40%向上目標  
- **新規理解時間**: 1日以下目標
- **保守負荷**: 週2時間以下目標

---

## 🎯 設計原則・哲学

### シンプルさ重視
- **複雑性隠蔽**: 統合API経由で簡単操作
- **合理的デフォルト**: 設定不要で即利用可能
- **段階的学習**: 簡単→高度な順序で習得

### 効率性追求  
- **パフォーマンス**: 高速インポート・実行
- **スケーラビリティ**: 小規模→大規模対応
- **リソース効率**: CPU・メモリ最適利用

### 保守性確保
- **可読性**: 自明なコード・命名
- **テスト品質**: 段階的カバレッジ向上
- **文書同期**: コード変更と連動更新

**最終目標**: 個人開発として持続可能な高品質システム
