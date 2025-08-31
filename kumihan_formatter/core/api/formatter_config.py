"""
FormatterConfig - 設定管理専用クラス

Issue #1249対応: 統合API設計統一
設定読み込み、キャッシュ、パフォーマンスモード管理を担当
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path
import logging


class FormatterConfig:
    """統合API設定管理クラス"""

    # クラスレベルキャッシュ（パフォーマンス最適化用）
    _config_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        performance_mode: str = "standard",
    ):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.performance_mode = performance_mode

        # パフォーマンスモード対応設定読み込み
        if performance_mode == "optimized":
            self.config = self._load_config_cached(config_path)
        else:
            self.config = self._load_config(config_path)

        self.logger.info(f"FormatterConfig initialized - mode: {performance_mode}")

    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        if config_path and Path(config_path).exists():
            try:
                import json

                with open(config_path, "r", encoding="utf-8") as f:
                    result = json.load(f)
                    return result  # type: ignore[no-any-return]
            except Exception as e:
                self.logger.warning(f"設定ファイル読み込み失敗: {e}")

        return {}

    def _load_config_cached(
        self, config_path: Optional[Union[str, Path]]
    ) -> Dict[str, Any]:
        """キャッシュ機能付き設定読み込み（最適化モード用）"""
        cache_key = str(config_path) if config_path else "default"

        if cache_key in self._config_cache:
            self.logger.debug(f"Config cache hit: {cache_key}")
            return self._config_cache[cache_key]

        # 設定読み込み
        config = self._load_config(config_path)
        self._config_cache[cache_key] = config
        self.logger.debug(f"Config cached: {cache_key}")

        return config

    def get_config(self) -> Dict[str, Any]:
        """現在の設定を取得"""
        return self.config.copy()

    def update_config(self, updates: Dict[str, Any]) -> None:
        """設定を更新"""
        self.config.update(updates)
        self.logger.debug(f"Config updated: {list(updates.keys())}")

    def is_optimized_mode(self) -> bool:
        """最適化モードかどうか判定"""
        return self.performance_mode == "optimized"

    @classmethod
    def clear_cache(cls) -> None:
        """設定キャッシュをクリア"""
        cls._config_cache.clear()
