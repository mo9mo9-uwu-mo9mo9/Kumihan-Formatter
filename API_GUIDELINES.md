# API設計ガイドライン - 統合API設計統一版

**Issue #1249対応完了: 統合API設計統一・レガシーファイル整理**

## 🎯 新APIアーキテクチャ概要

### 責任分離原則による4層構造
統合APIは以下の4つの専門クラスに分離されています：

```
┌─────────────────────┐
│   KumihanFormatter  │ ← 公開インターフェース（後方互換性保持）
└─────────────────────┘
           │
┌─────────────────────┐
│    FormatterAPI     │ ← ユーザーインターフェース層
└─────────────────────┘
    │        │        │
┌───────┐ ┌──────────┐ ┌──────────────┐
│Config │ │   Core   │ │ Coordinator  │
│Manager│ │ Logic    │ │   (5Manager) │
└───────┘ └──────────┘ └──────────────┘
```

## 📋 各層の責任範囲

### 1. KumihanFormatter（公開インターフェース）
**目的**: 既存コードとの完全後方互換性

```python
# 既存のコードはそのまま動作
formatter = KumihanFormatter()
result = formatter.convert("input.txt", "output.html")
```

**責任**:
- 既存APIの維持
- FormatterAPIへの委譲
- 後方互換性保証

### 2. FormatterAPI（ユーザーインターフェース層）
**目的**: ユーザー向けAPI・エラーハンドリング・リソース管理

```python
api = FormatterAPI(config_path="custom.json", performance_mode="optimized")
result = api.convert("input.txt")
api.close()
```

**責任**:
- 公開APIメソッドの提供
- エラーハンドリング
- リソース管理（__enter__/__exit__対応）
- ログ管理

### 3. FormatterConfig（設定管理）
**目的**: 設定読み込み・キャッシュ・パフォーマンスモード管理

```python
config = FormatterConfig("config.json", "optimized")
settings = config.get_config()
config.update_config({"enable_cache": True})
```

**責任**:
- 設定ファイル読み込み
- 設定キャッシュ管理
- パフォーマンスモード制御

### 4. ManagerCoordinator（Manager調整）
**目的**: 5つのManagerシステムの初期化・調整

```python
coordinator = ManagerCoordinator(config, "optimized")
coordinator.ensure_managers_initialized()
system_info = coordinator.get_system_info()
```

**責任**:
- 5Manager（Core/Parsing/Optimization/Plugin/Distribution）の管理
- 遅延初期化制御
- Manager間の調整

### 5. FormatterCore（コアロジック）
**目的**: 実際の変換・解析・レンダリング処理

```python
core = FormatterCore(coordinator)
result = core.convert_file("input.txt", "output.html")
html = core.convert_text("# Hello World")
```

**責任**:
- ファイル変換処理
- テキスト変換処理
- 解析・レンダリング・バリデーション

## 🔄 API使用パターン

### パターン1: シンプルな使用（推奨）
```python
from kumihan_formatter.unified_api import KumihanFormatter

# 従来と同じ使用方法
formatter = KumihanFormatter()
result = formatter.convert("input.txt", "output.html")
```

### パターン2: 高度な設定
```python
from kumihan_formatter.unified_api import KumihanFormatter

# パフォーマンス最適化モード
formatter = KumihanFormatter(
    config_path="production.json",
    performance_mode="optimized"
)

with formatter:
    result = formatter.convert("large_file.txt", template="custom")
    validation = formatter.validate_syntax("# Test")
```

### パターン3: 直接API使用（上級者向け）
```python
from kumihan_formatter.core.api import FormatterAPI

# 直接APIアクセス
api = FormatterAPI(performance_mode="optimized")
try:
    result = api.convert("input.txt")
    system_info = api.get_system_info()
finally:
    api.close()
```

## 🛡️ エラーハンドリング指針

### 1. グレースフルデグラデーション
```python
# 設定読み込み失敗時は基本設定で継続
config = self._load_config(config_path) or {}

# パフォーマンス初期化失敗時は標準モードにフォールバック
try:
    self._initialize_optimized_mode()
except Exception:
    self._initialize_standard_mode()  # フォールバック
```

### 2. 統一エラー形式
```python
# 成功時
{"status": "success", "result": data, "metadata": {}}

# 失敗時
{"status": "error", "error": "詳細メッセージ", "input_file": path}
```

### 3. ログレベル統一
```python
logger.info("正常完了")      # ユーザーに有用な情報
logger.debug("詳細状況")     # 開発者向け詳細情報
logger.warning("注意事項")   # 継続可能な問題
logger.error("エラー詳細")   # エラー状況
```

## ⚡ パフォーマンス設計

### 1. 遅延初期化（Lazy Loading）
最適化モードでは重いコンポーネントを必要時まで初期化延期
```python
if performance_mode == "optimized":
    # 実際の使用時まで初期化を延期
    self._ensure_managers_initialized()
```

### 2. キャッシュ戦略
```python
# 設定ファイルキャッシュ
_config_cache: Dict[str, Dict[str, Any]] = {}

# Manager初期化状態追跡
self._managers_initialized = False
```

### 3. 計測・モニタリング
```python
start_time = time.perf_counter()
# 処理実行
end_time = time.perf_counter()
logger.debug(f"処理完了: {end_time - start_time:.4f}s")
```

## 🧪 テスト設計指針

### 1. 各層の独立テスト
```python
# 設定管理のテスト
def test_formatter_config():
    config = FormatterConfig(None, "standard")
    assert config.get_config() == {}

# コアロジックのテスト
def test_formatter_core():
    coordinator = MockCoordinator()
    core = FormatterCore(coordinator)
    result = core.convert_text("# Test")
    assert "Test" in result
```

### 2. 統合テスト
```python
# 全体フローのテスト
def test_full_integration():
    formatter = KumihanFormatter()
    result = formatter.convert("test.txt")
    assert result["status"] == "success"
```

### 3. モック使用推奨
```python
# 外部依存をモック化
@patch('kumihan_formatter.core.api.manager_coordinator.CoreManager')
def test_with_mock(mock_core_manager):
    # テスト実装
    pass
```

## 📈 マイグレーション戦略

### 既存コードの対応
✅ **変更不要**: 既存のKumihanFormatterコードはそのまま動作
```python
# これらはすべてそのまま動作
formatter = KumihanFormatter()
formatter.convert("input.txt", "output.html")
formatter.parse_text("# Hello")
formatter.validate_syntax("content")
```

### 新機能への移行（任意）
🔄 **段階的移行**: 必要に応じて新機能を採用
```python
# パフォーマンス向上が必要な場合
formatter = KumihanFormatter(performance_mode="optimized")

# より詳細な制御が必要な場合
from kumihan_formatter.core.api import FormatterAPI
api = FormatterAPI(config_path="advanced.json")
```

## 🚀 将来の拡張指針

### 1. 新Manager追加時
1. `kumihan_formatter/managers/` に新Managerクラス作成
2. `ManagerCoordinator` に統合
3. 必要に応じて `FormatterCore` でメソッド追加
4. テスト・ドキュメント更新

### 2. 新API機能追加時
1. `FormatterCore` にロジック追加
2. `FormatterAPI` にインターフェース追加
3. `KumihanFormatter` で公開（後方互換性考慮）
4. APIガイドライン更新

### 3. パフォーマンス改善時
1. `OptimizationManager` で最適化実装
2. `ManagerCoordinator` で遅延初期化制御
3. パフォーマンステスト追加

## ⚠️ 制約事項

### 1. 後方互換性
- `KumihanFormatter` の公開APIは変更禁止
- 戻り値構造は既存形式維持
- エラーハンドリング動作は既存準拠

### 2. パフォーマンス
- 標準モードのパフォーマンスは既存レベル以上維持
- 最適化モードは大幅な性能向上を実現
- メモリ使用量は現状維持または改善

### 3. 保守性
- 各クラス500行以下推奨
- 単一責任原則の厳格遵守
- Manager間の依存は最小限に制限

---

*Issue #1249完了: 統合API設計統一・責任分離リファクタリング達成版*