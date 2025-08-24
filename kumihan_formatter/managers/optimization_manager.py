"""
OptimizationManager - 統合最適化管理システム

統合対象:
- kumihan_formatter/core/config/optimization/manager.py
- kumihan_formatter/core/optimization/performance/cache_manager.py
- その他最適化関連Manager
"""

from typing import Any, Dict, Optional
from ..core.config.optimization.manager import AdaptiveSettingsManager
from ..core.optimization.performance.cache_manager import HighPerformanceCacheManager
from ..core.utilities.logger import get_logger


class OptimizationManager:
    """統合最適化管理システム - 全最適化機能を統括"""
    
    def __init__(self, config: Optional[Any] = None):
        self.logger = get_logger(__name__)
        
        # 最適化機能統合
        try:
            if config:
                self.adaptive_manager = AdaptiveSettingsManager(config)
            else:
                self.adaptive_manager = None
                self.logger.info("AdaptiveSettingsManager disabled - no config provided")
        except Exception as e:
            self.logger.warning(f"AdaptiveSettingsManager initialization failed: {e}")
            self.adaptive_manager = None
        
        self.cache_manager = HighPerformanceCacheManager()
        
        self.logger.info("OptimizationManager initialized - unified optimization system")
    
    def optimize_for_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキスト最適化"""
        if not self.adaptive_manager:
            return {"status": "optimization_disabled"}
        
        try:
            from ..core.config.optimization.manager_core import WorkContext
            work_context = WorkContext(
                operation_type=context.get("operation", "unknown"),
                content_size=context.get("content_size", 0),
                complexity_score=context.get("complexity", 0.5)
            )
            return self.adaptive_manager.adjust_for_context(work_context)
        except Exception as e:
            self.logger.error(f"Context optimization error: {e}")
            return {"status": "optimization_failed", "error": str(e)}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計取得"""
        try:
            if hasattr(self.cache_manager, 'get_statistics'):
                return self.cache_manager.get_statistics()
            elif hasattr(self.cache_manager, 'stats'):
                return self.cache_manager.stats
            else:
                return {"status": "cache_active", "method": "unknown"}
        except Exception as e:
            return {"status": "cache_error", "error": str(e)}
    
    def clear_cache(self) -> None:
        """キャッシュクリア"""
        try:
            if hasattr(self.cache_manager, 'clear_cache'):
                self.cache_manager.clear_cache()
            elif hasattr(self.cache_manager, 'clear'):
                self.cache_manager.clear()
        except Exception as e:
            self.logger.warning(f"Cache clear failed: {e}")
    
    def enable_optimization(self, config: Any) -> bool:
        """最適化機能有効化"""
        try:
            self.adaptive_manager = AdaptiveSettingsManager(config)
            self.logger.info("Optimization enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable optimization: {e}")
            return False
    
    def disable_optimization(self) -> None:
        """最適化機能無効化"""
        self.adaptive_manager = None
        self.logger.info("Optimization disabled")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """最適化状態取得"""
        return {
            "adaptive_optimization": self.adaptive_manager is not None,
            "cache_enabled": True,
            "cache_stats": self.get_cache_stats()
        }