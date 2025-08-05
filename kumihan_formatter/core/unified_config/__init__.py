"""統一設定管理システム

Issue #771対応: 分散した設定クラスを統合し、
一元的な設定管理・環境変数対応・設定ファイル対応を提供

このモジュールは以下を提供:
- 統一設定管理マネージャー
- Pydanticベース型安全設定モデル
- YAML/JSON設定ファイル対応
- 包括的環境変数サポート
- ホットリロード機能
- 既存設定クラスとの互換性
"""

from .config_adapters import (
    BaseConfigAdapter,
    ErrorConfigManagerAdapter,
    ParallelProcessingConfigAdapter,
)
from .config_loader import ConfigFormat, ConfigLoader
from .config_models import (
    ErrorConfig,
    KumihanConfig,
    LoggingConfig,
    ParallelConfig,
    RenderingConfig,
    UIConfig,
)
from .config_validator import ConfigValidator
from .unified_config_manager import UnifiedConfigManager

__all__ = [
    "UnifiedConfigManager",
    "KumihanConfig",
    "ParallelConfig",
    "LoggingConfig",
    "ErrorConfig",
    "RenderingConfig",
    "UIConfig",
    "ConfigLoader",
    "ConfigFormat",
    "ConfigValidator",
    "ParallelProcessingConfigAdapter",
    "ErrorConfigManagerAdapter",
    "BaseConfigAdapter",
]
