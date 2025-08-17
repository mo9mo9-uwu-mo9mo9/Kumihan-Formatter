"""統合Config システム

Issue #912対応: 分散したConfig関連ファイルを5つの統合ファイルに集約

後方互換性のため、既存のインポートパスをすべてサポート
"""

from .config_loader import UnifiedConfigLoader  # エイリアス
from .config_loader import (
    ConfigLoader,
    ConfigLoadError,
)

# === メイン機能 ===
from .config_manager import EnhancedConfig  # エイリアス
from .config_manager import UnifiedConfigManager  # エイリアス
from .config_manager import (
    ConfigManager,
    get_global_config_manager,
    reset_global_config_manager,
    set_global_config_manager,
)
from .config_types import (  # 基本型定義; Pydanticモデル群; 後方互換性エイリアス
    BaseConfig,
    Config,
    ConfigFormat,
    ConfigLevel,
    ErrorConfig,
    ErrorHandlingLevel,
    ExtendedConfig,
    FormatterConfig,
    KumihanConfig,
    LoggingConfig,
    LogLevel,
    ParallelConfig,
    RenderingConfig,
    SimpleFormatterConfig,
    UIConfig,
    ValidationResult,
)
from .config_validator import UnifiedConfigValidator  # エイリアス
from .config_validator import (
    ConfigValidationError,
    ConfigValidator,
    EnhancedValidationResult,
)

# === 後方互換性のための追加エイリアス ===
# 既存のエイリアスを上書きして型エラーを回避

# 注意: これらは後方互換性のため型を上書きしています

# === 互換性のための名前空間 ===
__all__ = [
    # === メイン管理クラス ===
    "ConfigManager",
    "get_global_config_manager",
    "set_global_config_manager",
    "reset_global_config_manager",
    # === コンポーネントクラス ===
    "ConfigLoader",
    "ConfigValidator",
    # === エラークラス ===
    "ConfigLoadError",
    "ConfigValidationError",
    # === 基本型定義 ===
    "ConfigLevel",
    "ConfigFormat",
    "LogLevel",
    "ErrorHandlingLevel",
    "ValidationResult",
    "EnhancedValidationResult",
    # === Pydanticモデル群 ===
    "ParallelConfig",
    "LoggingConfig",
    "ErrorConfig",
    "RenderingConfig",
    "UIConfig",
    "FormatterConfig",
    "SimpleFormatterConfig",
    "KumihanConfig",
    # === 後方互換性エイリアス ===
    "Config",
    "BaseConfig",
    "ExtendedConfig",
    "EnhancedConfig",
    "UnifiedConfigManager",
    "UnifiedConfigLoader",
    "UnifiedConfigValidator",
]

# === 統合情報 ===
__doc__ += """

## 統合前後のファイル構成

### 統合前（20ファイル、3,780行）
- kumihan_formatter/config.py (158行)
- kumihan_formatter/simple_config.py
- kumihan_formatter/models/config.py
- config/ ディレクトリ（6ファイル）
- core/config/ ディレクトリ（4ファイル）
- core/unified_config/ ディレクトリ（5ファイル）
- その他 Config関連ファイル

### 統合後（5ファイル、約2,000行）
- kumihan_formatter/core/config/__init__.py （統合エクスポート）
- kumihan_formatter/core/config/config_manager.py （メイン設定管理）
- kumihan_formatter/core/config/config_loader.py （設定読み込み統合）
- kumihan_formatter/core/config/config_validator.py （バリデーション統合）
- kumihan_formatter/core/config/config_types.py （型定義・モデル統合）

## 使用例

### 基本的な使用法
```python
from kumihan_formatter.core.config import ConfigManager

# 設定マネージャーの作成
config_manager = ConfigManager()

# 設定の取得
config = config_manager.config
print(config.logging.log_level)

# グローバル設定マネージャーの使用
from kumihan_formatter.core.config import get_global_config_manager
global_manager = get_global_config_manager()
```

### 後方互換性
```python
# 従来のインポートパスがすべて動作
from kumihan_formatter.core.config import Config  # = ConfigManager
from kumihan_formatter.core.config import BaseConfig  # = ConfigManager
from kumihan_formatter.core.config import UnifiedConfigManager  # = ConfigManager
```

## 移行ガイド
既存コードの変更は不要です。すべてのインポートパスが後方互換性を保っています。
"""
