"""
ManagerCoordinator - Manager間の調整クラス

Issue #1249対応: 統合API設計統一
5つのManagerシステムの初期化・調整を担当
"""

from typing import Any, Dict
import logging
import time

from ...managers import (
    CoreManager,
    ProcessingManager,
    PluginManager,
)
from ...parsers.main_parser import MainParser
from ...core.rendering.main_renderer import MainRenderer


class ManagerCoordinator:
    """Managerシステム統合調整クラス"""

    def __init__(self, config: Dict[str, Any], performance_mode: str = "standard"):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.performance_mode = performance_mode

        # 遅延初期化フラグ
        self._managers_initialized = False
        self._main_parser_initialized = False
        self._main_renderer_initialized = False

        if performance_mode == "optimized":
            self._initialize_optimized_mode()
        else:
            self._initialize_standard_mode()

    def _initialize_optimized_mode(self) -> None:
        """最適化モード用の初期化（遅延初期化）"""
        # 遅延初期化フラグのみ設定
        self._managers_initialized = False
        self._main_parser_initialized = False
        self._main_renderer_initialized = False

        self.logger.debug("ManagerCoordinator: Optimized mode - lazy loading enabled")

    def _initialize_standard_mode(self) -> None:
        """標準モード用の初期化（従来通り）"""
        # 新統合Managerシステム初期化
        self.core_manager = CoreManager(self.config)
        self.processing_manager = ProcessingManager(self.config)
        self.plugin_manager = PluginManager(self.config)

        # メインコンポーネント
        self.main_parser = MainParser(self.config)
        self.main_renderer = MainRenderer(self.config)

        self._managers_initialized = True
        self._main_parser_initialized = True
        self._main_renderer_initialized = True

        self.logger.debug(
            "ManagerCoordinator: Standard mode - full initialization completed"
        )

    def ensure_managers_initialized(self) -> None:
        """Managerの遅延初期化（最適化モード用）"""
        if self.performance_mode == "optimized" and not self._managers_initialized:
            try:
                start_time = time.perf_counter()

                self.core_manager = CoreManager(self.config)
                self.processing_manager = ProcessingManager(self.config)
                self.plugin_manager = PluginManager(self.config)

                self._managers_initialized = True
                end_time = time.perf_counter()

                self.logger.debug(
                    f"Managers lazy initialized in {end_time - start_time:.4f}s"
                )

            except Exception as e:
                self.logger.error(f"Manager lazy initialization failed: {e}")
                self._initialize_standard_mode()  # フォールバック  # フォールバック

    def ensure_parser_initialized(self) -> None:
        """MainParserの遅延初期化（最適化モード用）"""
        if self.performance_mode == "optimized" and not self._main_parser_initialized:
            try:
                start_time = time.perf_counter()
                self.main_parser = MainParser(self.config)
                self._main_parser_initialized = True
                end_time = time.perf_counter()
                self.logger.debug(
                    f"MainParser lazy initialized in {end_time - start_time:.4f}s"
                )
            except Exception as e:
                self.logger.error(f"MainParser initialization failed: {e}")
                # Dummy fallback could be implemented here if needed

    def ensure_renderer_initialized(self) -> None:
        """MainRendererの遅延初期化（最適化モード用）"""
        if self.performance_mode == "optimized" and not self._main_renderer_initialized:
            try:
                start_time = time.perf_counter()
                self.main_renderer = MainRenderer(self.config)
                self._main_renderer_initialized = True
                end_time = time.perf_counter()
                self.logger.debug(
                    f"MainRenderer lazy initialized in {end_time - start_time:.4f}s"
                )
            except Exception as e:
                self.logger.error(f"MainRenderer initialization failed: {e}")
                # Dummy fallback could be implemented here if needed

    def get_system_info(self) -> Dict[str, Any]:
        """統合システム情報取得"""
        try:
            return {
                "architecture": "integrated_manager_system",
                "components": {
                    "core_manager": "CoreManager",
                    "processing_manager": "ProcessingManager",
                    "plugin_manager": "PluginManager",
                    "main_parser": "MainParser",
                    "main_renderer": "MainRenderer",
                },
                "version": "3.0.0-integrated",
                "status": "production_ready",
                "optimization_stats": getattr(self, "processing_manager", None)
                and self.processing_manager.get_optimization_statistics(),
                "core_stats": getattr(self, "core_manager", None)
                and self.core_manager.get_core_statistics(),
            }
        except Exception as e:
            self.logger.error(f"System info error: {e}")
            return {"status": "error", "error": str(e)}

    def close(self) -> None:
        """統合システムのリソース解放"""
        try:
            if hasattr(self, "core_manager"):
                self.core_manager.clear_cache()
            if hasattr(self, "processing_manager"):
                self.processing_manager.clear_optimization_cache()

            self.logger.info("ManagerCoordinator closed - 統合Managerシステム")
        except Exception as e:
            self.logger.error(f"クローズ処理中にエラー: {e}")
