# Manager システム 役割明確化ドキュメント

**Issue #1249対応: 統合API設計統一・Managerシステム役割明確化**

## 🎯 Manager システム概要

Kumihan-Formatterでは、機能を5つの専門Managerに分割し、それぞれが明確な責任を持つ構成になっています。

## 📋 Manager 詳細仕様

### 1. CoreManager - コア基盤機能
**責任範囲**: システム基盤・ファイル操作・基本的なI/O処理

**主要機能**:
- ファイル読み書き操作
- 基本的な設定管理  
- システムキャッシュ管理
- 基盤的なユーティリティ機能
- エラーログ・システム統計

**使用場面**: 
- ファイル入出力が必要な全ての処理
- システム全体の基盤機能として

**API例**:
```python
core_manager.read_file(path)
core_manager.write_file(path, content)
core_manager.get_core_statistics()
core_manager.clear_cache()
```

### 2. ParsingManager - 解析処理管理
**責任範囲**: テキスト解析・構文検証・パーサー選択

**主要機能**:
- 自動パーサー選択
- テキスト解析処理
- 構文検証・エラー検出
- パーシング結果の品質保証

**使用場面**:
- Kumihanテキストの解析処理
- 構文チェック・バリデーション
- パーサーの動的選択

**API例**:
```python
parsing_manager.parse_and_validate(text, parser_type)
parsing_manager.validate_syntax(text)
parsing_manager.select_optimal_parser(content)
```

### 3. OptimizationManager - パフォーマンス最適化
**責任範囲**: 処理速度向上・メモリ使用量最適化・パフォーマンス監視

**主要機能**:
- 処理パフォーマンス最適化
- メモリ使用量管理
- 並列処理制御
- 最適化統計・監視

**使用場面**:
- 大きなファイルの処理時
- パフォーマンスが重要な処理
- リソース制約がある環境

**API例**:
```python
optimization_manager.optimize_parsing(content, parser_func)
optimization_manager.get_optimization_statistics()
optimization_manager.clear_optimization_cache()
```

### 4. PluginManager - プラグインシステム
**責任範囲**: 拡張機能・プラグイン管理・カスタム処理

**主要機能**:
- プラグインの動的読み込み
- 拡張機能の管理
- カスタム処理の統合
- プラグイン間の調整

**使用場面**:
- カスタム記法の追加
- 特殊な処理要件への対応
- システムの機能拡張

**API例**:
```python
plugin_manager.load_plugin(plugin_name)
plugin_manager.execute_custom_processing(content, plugin_list)
plugin_manager.get_available_plugins()
```

### 5. DistributionManager - 配布・出力管理 ⚠️ 
**責任範囲**: ファイル出力・配布形式・最終出力処理

**現在のステータス**: `core.io.distribution_manager` に移動済み

**主要機能**:
- 複数形式での出力
- 配布用ファイル生成
- 出力先ディレクトリ管理
- 最終出力品質保証

**使用場面**:
- HTML出力・配布ファイル生成
- 複数形式での同時出力
- 配布パッケージ作成

## 🔄 Manager間の連携パターン

### パターン1: 標準変換処理
```
1. CoreManager → ファイル読み込み
2. ParsingManager → テキスト解析・検証
3. OptimizationManager → 処理最適化
4. DistributionManager → HTML出力
```

### パターン2: カスタム処理
```
1. CoreManager → ファイル読み込み
2. PluginManager → カスタム前処理
3. ParsingManager → 拡張解析
4. PluginManager → カスタム後処理
5. DistributionManager → カスタム出力
```

### パターン3: 大規模ファイル処理
```
1. CoreManager → ファイル読み込み
2. OptimizationManager → 並列処理準備
3. ParsingManager → 並列解析
4. OptimizationManager → 結果統合
5. DistributionManager → 最適化出力
```

## 📖 使用ガイドライン

### 新機能開発時
1. 機能の責任範囲を特定
2. 適切なManagerを選択
3. Manager間のインターフェースを設計
4. 統合テストで動作確認

### パフォーマンス改善時
1. OptimizationManagerの機能を活用
2. 必要に応じてCoreManagerのキャッシュを調整
3. Manager間の通信コストを最小化

### 拡張機能開発時
1. PluginManagerのインターフェースに準拠
2. 既存Managerとの互換性を保持
3. 適切なエラーハンドリングを実装

## 🚨 注意事項

- **循環依存の回避**: Manager間の直接依存は最小限に
- **責任境界の遵守**: 各Managerの責任範囲を厳格に守る
- **エラーハンドリング**: 各Manager内で適切なエラー処理を実装
- **テスト容易性**: 各Managerは独立してテスト可能な設計を保持

---

*Issue #1249: 統合API設計統一完了 - Managerシステム役割明確化版*