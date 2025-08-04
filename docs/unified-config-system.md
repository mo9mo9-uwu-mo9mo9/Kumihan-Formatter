# 統一設定管理システム

> Issue #771対応: 分散した設定管理を統合する新しいシステム

## 概要

Kumihan-Formatterの統一設定管理システムは、従来分散していた14個の設定クラスを1つの統合システムに集約し、型安全性、環境変数サポート、ホットリロード機能を提供します。

## 主要機能

### 1. 統一設定モデル

Pydanticベースの型安全な設定モデル：

- **ParallelConfig**: 並列処理設定
- **LoggingConfig**: ログ設定
- **ErrorConfig**: エラー処理設定
- **RenderingConfig**: レンダリング設定
- **UIConfig**: UI設定

### 2. 設定の優先順位

1. **CLI引数** (最優先) ※今後実装予定
2. **環境変数**
3. **設定ファイル**
4. **デフォルト値**

### 3. 環境変数サポート

全ての設定項目は環境変数でオーバーライド可能：

```bash
# 基本形式
KUMIHAN_<SECTION>__<KEY>=value

# 例
export KUMIHAN_DEBUG_MODE=true
export KUMIHAN_PARALLEL__PARALLEL_THRESHOLD_LINES=20000
export KUMIHAN_LOGGING__LOG_LEVEL=DEBUG
export KUMIHAN_ERROR__GRACEFUL_ERRORS=true
export KUMIHAN_RENDERING__MAX_WIDTH=1200px
```

### 4. 設定ファイル形式

#### YAML形式
```yaml
config_version: "1.0"
environment: "production"
debug_mode: false

parallel:
  parallel_threshold_lines: 10000
  parallel_threshold_size: 10485760  # 10MB
  memory_warning_threshold_mb: 150

logging:
  log_level: "INFO"
  log_dir: "~/.kumihan/logs"
  dev_log_enabled: false

error:
  graceful_errors: true
  continue_on_error: false
  show_suggestions: true

rendering:
  max_width: "800px"
  background_color: "#f9f9f9"
  font_family: "Hiragino Kaku Gothic ProN, sans-serif"

ui:
  auto_preview: true
  progress_level: "detailed"
```

#### JSON形式
```json
{
  "config_version": "1.0",
  "parallel": {
    "parallel_threshold_lines": 10000
  },
  "logging": {
    "log_level": "INFO"
  }
}
```

## 使用方法

### 基本的な使用例

```python
from kumihan_formatter.core.unified_config import get_unified_config_manager

# 統一設定マネージャーの取得
manager = get_unified_config_manager(
    config_file="kumihan.yaml",
    auto_reload=True  # ホットリロード有効
)

# 設定の取得
config = manager.get_config()

# 各種設定へのアクセス
parallel_config = config.parallel
logging_config = config.logging
error_config = config.error
rendering_config = config.rendering
ui_config = config.ui
```

### ホットリロード機能

設定ファイルの変更を自動検出し、再読み込みします：

```python
# コールバックの登録
def on_config_reload(new_config):
    print("設定が更新されました")
    
manager.add_reload_callback(on_config_reload)
```

### 設定の保存

```python
# 現在の設定を保存
manager.save_config("my_config.yaml")
```

## 移行ガイド

### 既存コードの移行

既存のコードは互換アダプターにより動作を継続しますが、新しいAPIへの移行を推奨します：

#### ParallelProcessingConfig
```python
# 旧コード（非推奨）
from kumihan_formatter.parser import ParallelProcessingConfig
config = ParallelProcessingConfig()

# 新コード（推奨）
from kumihan_formatter.core.unified_config import get_unified_config_manager
config = get_unified_config_manager().get_parallel_config()
```

#### ErrorConfigManager
```python
# 旧コード（非推奨）
from kumihan_formatter.core.error_analysis.error_config import ErrorConfigManager
manager = ErrorConfigManager()

# 新コード（推奨）
from kumihan_formatter.core.unified_config import get_unified_config_manager
config = get_unified_config_manager().get_error_config()
```

#### BaseConfig
```python
# 旧コード（非推奨）
from kumihan_formatter.config.base_config import BaseConfig
config = BaseConfig()

# 新コード（推奨）
from kumihan_formatter.core.unified_config import get_unified_config_manager
config = get_unified_config_manager().get_rendering_config()
```

## 設定検証

統一設定システムは自動的に設定を検証し、問題があれば警告や修正提案を提供します：

- 値の妥当性チェック
- 設定間の依存関係検証
- システム環境との整合性確認
- 自動修正機能

## トラブルシューティング

### 設定ファイルが見つからない

デフォルトの検索パス：
1. カレントディレクトリ
2. `~/.kumihan/`
3. `~/.config/kumihan/`
4. `/etc/kumihan/` (Unix系のみ)

### 環境変数が反映されない

- プレフィックスが正しいか確認（`KUMIHAN_`）
- ネストした設定は`__`で区切る
- 大文字小文字に注意

### ホットリロードが動作しない

- `auto_reload=True`が設定されているか確認
- ファイルの書き込み権限を確認
- ファイルシステムの監視機能がサポートされているか確認

## API リファレンス

詳細なAPIドキュメントは[こちら](api/unified-config.md)を参照してください。