"""
ConfigManager - Issue #1171 Manager統合最適化
===========================================

設定管理を統括する統一Managerクラス
従来のCoreManagerから設定機能を抽出・統合
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from kumihan_formatter.core.utilities.logger import get_logger


class ConfigManager:
    """統合設定管理Manager - Issue #1171対応

    CoreManagerの設定機能を統合し、全設定管理を統括する
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.logger = get_logger(__name__)

        # 設定管理の統合初期化
        self.config_path = config_path
        self._config_data = {}
        self._core_config = None

        # CoreManagerの設定機能統合（遅延初期化）
        self._core_config_manager = None

        self.logger.info(
            "ConfigManager initialized - unified configuration system with CoreManager integration"
        )

    @property
    def core_config_manager(self):
        """CoreConfigManagerの遅延初期化"""
        if self._core_config_manager is None and self.config_path:
            try:
                from ..core.config.core_config_manager import CoreConfigManager

                self._core_config_manager = CoreConfigManager(
                    config_file=self.config_path
                )
            except ImportError as e:
                self.logger.warning(f"CoreConfigManager not available: {e}")
                self._core_config_manager = None
        return self._core_config_manager

    def get_config(self, key: str, default: Any = None) -> Any:
        """設定値取得 - CoreManagerの機能統合"""
        # まずCoreConfigManagerから取得を試行
        if self.core_config_manager:
            try:
                value = self.core_config_manager.get(key, default)
                if value != default:
                    return value
            except Exception as e:
                self.logger.warning(f"CoreConfigManager get failed for {key}: {e}")

        # フォールバック：内部設定から取得
        return self._config_data.get(key, default)

    def set_config(self, key: str, value: Any, source: str = "user") -> None:
        """設定値設定 - CoreManagerの機能統合"""
        # CoreConfigManagerに設定を試行
        if self.core_config_manager:
            try:
                self.core_config_manager.set(key, value, source)
            except Exception as e:
                self.logger.warning(f"CoreConfigManager set failed for {key}: {e}")

        # 内部設定にも保存
        self._config_data[key] = value
        self.logger.debug(f"Config set: {key} = {value} (source: {source})")

    def validate_config(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """設定検証 - CoreManagerの機能統合"""
        try:
            # CoreConfigManagerの検証を優先
            if self.core_config_manager:
                try:
                    return self.core_config_manager.validate()
                except Exception as e:
                    self.logger.warning(f"CoreConfigManager validation failed: {e}")

            # フォールバック：基本的な検証
            if config_data:
                # 設定データの基本的な検証
                required_keys = ["output_format", "encoding"]
                for key in required_keys:
                    if key not in config_data:
                        self.logger.warning(f"Missing required config key: {key}")

            return True
        except Exception as e:
            self.logger.error(f"Config validation error: {e}")
            return False

    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            config_path = Path(config_path)
            self.logger.info(f"Loading config from {config_path}")

            if config_path.exists():
                import json

                with open(config_path, "r", encoding="utf-8") as f:
                    if config_path.suffix == ".json":
                        data = json.load(f)
                    else:
                        # 基本的なkey=value形式の処理
                        data = {}
                        for line in f:
                            line = line.strip()
                            if line and "=" in line and not line.startswith("#"):
                                key, value = line.split("=", 1)
                                data[key.strip()] = value.strip()

                # 読み込んだデータを内部設定に反映
                self._config_data.update(data)
                return data
            else:
                self.logger.warning(f"Config file not found: {config_path}")
                return {}

        except Exception as e:
            self.logger.error(f"Config loading error for {config_path}: {e}")
            raise

    def save_config(
        self, config_data: Dict[str, Any], config_path: Union[str, Path]
    ) -> None:
        """設定ファイル保存"""
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            import json

            with open(config_path, "w", encoding="utf-8") as f:
                if config_path.suffix == ".json":
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    # 基本的なkey=value形式で保存
                    for key, value in config_data.items():
                        f.write(f"{key}={value}\n")

            self.logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            self.logger.error(f"Config saving error for {config_path}: {e}")
            raise

    def reload_config(self) -> None:
        """設定再読み込み - CoreManagerの機能統合"""
        try:
            # CoreConfigManagerの再読み込み
            if self.core_config_manager:
                try:
                    self.core_config_manager.reload()
                except Exception as e:
                    self.logger.warning(f"CoreConfigManager reload failed: {e}")

            # 設定パスが指定されていれば再読み込み
            if self.config_path:
                self.load_config(self.config_path)

            self.logger.info("Config reloaded")
        except Exception as e:
            self.logger.error(f"Config reload error: {e}")

    def get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定取得"""
        return {
            "output_format": "html",
            "encoding": "utf-8",
            "template": "default",
            "debug": False,
            "cache_enabled": True,
            "optimization_level": "standard",
        }

    def get_all_configs(self) -> Dict[str, Any]:
        """全設定取得"""
        # CoreConfigManagerの設定も含める
        all_configs = self._config_data.copy()

        if self.core_config_manager:
            try:
                # CoreConfigManagerから全設定を取得（利用可能な場合）
                if hasattr(self.core_config_manager, "get_all"):
                    core_configs = self.core_config_manager.get_all()
                    all_configs.update(core_configs)
            except Exception as e:
                self.logger.warning(f"Failed to get CoreConfigManager configs: {e}")

        return all_configs

    def reset_config(self, key: Optional[str] = None) -> None:
        """設定リセット（キー指定なしで全リセット）"""
        if key is None:
            self._config_data.clear()
            # CoreConfigManagerもリセット（可能な場合）
            if self.core_config_manager and hasattr(self.core_config_manager, "reset"):
                try:
                    self.core_config_manager.reset()
                except Exception as e:
                    self.logger.warning(f"CoreConfigManager reset failed: {e}")
            self.logger.info("All configs reset")
        else:
            self._config_data.pop(key, None)
            # CoreConfigManagerからも削除（可能な場合）
            if self.core_config_manager and hasattr(self.core_config_manager, "remove"):
                try:
                    self.core_config_manager.remove(key)
                except Exception as e:
                    self.logger.warning(
                        f"CoreConfigManager remove failed for {key}: {e}"
                    )
            self.logger.info(f"Config key '{key}' reset")

    def get_config_statistics(self) -> Dict[str, Any]:
        """設定統計情報"""
        stats = {
            "total_configs": len(self._config_data),
            "config_keys": list(self._config_data.keys()),
            "has_custom_config": bool(self._config_data),
            "config_file": str(self.config_path) if self.config_path else None,
            "core_config_available": self.core_config_manager is not None,
        }

        # CoreConfigManagerの統計情報も追加
        if self.core_config_manager and hasattr(
            self.core_config_manager, "get_statistics"
        ):
            try:
                core_stats = self.core_config_manager.get_statistics()
                stats["core_config_stats"] = core_stats
            except Exception as e:
                self.logger.warning(f"Failed to get CoreConfigManager statistics: {e}")

        return stats

    def shutdown(self) -> None:
        """リソース解放"""
        try:
            # CoreConfigManagerのシャットダウン
            if self._core_config_manager and hasattr(
                self._core_config_manager, "shutdown"
            ):
                try:
                    self._core_config_manager.shutdown()
                except Exception as e:
                    self.logger.warning(f"CoreConfigManager shutdown failed: {e}")

            self._core_config_manager = None
            self._config_data.clear()

            self.logger.info("ConfigManager shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during ConfigManager shutdown: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
