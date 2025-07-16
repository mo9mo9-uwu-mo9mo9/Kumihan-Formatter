# Phase2 技術的負債解消計画

> **目的**: 37件の技術的負債を段階的に解消し、コードベースの健全性を向上\
> **期間**: 2025-01-15 ～ 2025-01-31\
> **基準**: 300行/ファイル、20関数/ファイル、5クラス/ファイル

## 📊 現状分析

### 優先度別分類
| 優先度 | 行数範囲 | 件数 | 対象ファイル例 |
|--------|----------|------|----------------|
| **🔥 超高** | >600行 | 7件 | gui_views.py(539), performance/benchmark.py(676) |
| **🚨 高** | 400-600行 | 12件 | gui_controller.py(397), core/file_ops.py(475) |
| **⚠️ 中** | 300-400行 | 18件 | core/keyword_parser.py(521), core/list_parser.py(383) |

### カテゴリ別分析
| カテゴリ | 件数 | 主要課題 |
|----------|------|----------|
| **GUI系** | 3件 | 単一責任原則違反、ビュー・コントローラー混在 |
| **コアパーサー系** | 8件 | 複雑なパース処理、機能分散不足 |
| **パフォーマンス系** | 12件 | 監視・最適化・ベンチマーク機能混在 |
| **エラーハンドリング系** | 6件 | 例外処理・メッセージ・戦略の分離不足 |
| **レンダリング系** | 4件 | HTML生成・要素処理・ユーティリティ混在 |
| **キャッシュ系** | 4件 | 戦略・実装・管理の分離不足 |

## 🎯 Phase2実行計画

### Week 1: GUI系リファクタリング（🔥 超高優先度）
**目標**: GUIの責任分離とMVCパターン適用

#### 1.1 gui_views.py (539行) → 4ファイル分割
```python
gui_views/
├── __init__.py           # 統合エクスポート
├── main_window.py        # メインウィンドウ
├── preview_widget.py     # プレビューウィジェット  
├── settings_dialog.py    # 設定ダイアログ
└── status_bar.py         # ステータスバー
```

#### 1.2 gui_controller.py (397行) → 3ファイル分割  
```python
gui_controllers/
├── __init__.py           # 統合エクスポート
├── main_controller.py    # メインコントローラー
├── file_controller.py    # ファイル操作制御
└── preview_controller.py # プレビュー制御
```

#### 1.3 gui_models.py (37関数) → 機能別分割
```python
gui_models/
├── __init__.py           # 統合エクスポート  
├── file_model.py         # ファイルモデル（15関数）
├── settings_model.py     # 設定モデル（12関数）
└── preview_model.py      # プレビューモデル（10関数）
```

### Week 2: コアパーサー系リファクタリング（🚨 高優先度）

#### 2.1 keyword_parser.py (521行) → 戦略パターン適用
```python
parsers/keyword/
├── __init__.py           # 統合エクスポート
├── base_parser.py        # 基底パーサー
├── footnote_parser.py    # 脚注パーサー
├── sidenote_parser.py    # 傍注パーサー
├── decoration_parser.py  # 装飾パーサー
└── parser_factory.py     # ファクトリーパターン
```

#### 2.2 list_parser.py (383行) → 責任分離
```python
parsers/list/
├── __init__.py           # 統合エクスポート
├── list_detector.py      # リスト検出
├── list_formatter.py     # リスト整形
└── list_validator.py     # リスト検証
```

### Week 3: パフォーマンス系リファクタリング（⚠️ 中優先度）

#### 3.1 performance/benchmark.py (676行) → 機能分離
```python
performance/benchmarking/
├── __init__.py           # 統合エクスポート
├── scenario_runner.py    # シナリオ実行
├── metric_collector.py   # メトリクス収集
├── report_generator.py   # レポート生成
└── comparison_tool.py    # 比較ツール
```

#### 3.2 その他パフォーマンス系ファイル
- `memory_monitor.py` (652行) → 監視・分析・レポート分離
- `profiler.py` (577行) → プロファイル・分析・出力分離  
- `optimization_analyzer.py` (631行) → 解析・推奨・実行分離

### Week 4: 残存ファイル対応（⚠️ 中優先度）

#### 4.1 エラーハンドリング系
- `recovery_strategies.py` (615行) → 戦略別分離
- `unified_handler.py` (567行) → ハンドラー別分離
- `context_manager.py` (500行) → コンテキスト・管理分離

#### 4.2 レンダリング・その他
- `file_ops.py` (475行) → 操作別分離
- `toc_generator.py` (450行) → 生成・構築・出力分離
- `render_cache.py` (495行) → キャッシュ・戦略・管理分離

## 🔧 実装ガイドライン

### 分割基準
1. **Single Responsibility Principle**: 1ファイル1責任
2. **機能的凝集**: 関連する機能をグループ化
3. **疎結合**: モジュール間の依存を最小化
4. **テスタビリティ**: 単体テスト容易性の確保

### 命名規則
```python
# Before: 大きなファイル
large_module.py

# After: 機能別分割
large_module/
├── __init__.py      # re-export all
├── core_feature.py  # 主要機能
├── helper_utils.py  # ヘルパー機能  
└── config_types.py  # 設定・型定義
```

### テストカバレッジ維持
- 分割前: 既存テスト実行・通過確認
- 分割中: インポートパス更新
- 分割後: リグレッションテスト実行

## 📈 進捗管理

### 成功指標
- ファイル行数: 全て300行以下
- 関数数: 全て20個以下
- クラス数: 全て5個以下
- テストカバレッジ: 90%以上維持
- CI/CD: 全チェック通過

### 週次確認
```bash
# 進捗確認コマンド
python3 scripts/check_file_size.py --max-lines=300
python3 scripts/architecture_check.py
```

### リスク管理
- **リスク**: 大幅な変更による機能破綻
- **対策**: 小さな単位での段階的分割
- **検証**: 各分割後のテスト実行

---

**Phase1成果**: structured_logger.py 1,313行 → 194行（85%削減）\
**Phase2目標**: 37件の技術的負債を完全解消\
**最終目標**: 健全で保守性の高いコードベース実現