"""
ResourceManager - Issue #1171 Manager統合最適化
=============================================

リソース管理を統括する統一Managerクラス
ファイルI/O・テンプレート・アセット・分散処理リソースを統合
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from kumihan_formatter.core.utilities.logger import get_logger


class ResourceManager:
    """統合リソース管理Manager - Issue #1171対応

    CoreManagerのIO・テンプレート機能とOptimizationManagerのキャッシュ機能を統合
    """

    def __init__(
        self,
        template_path: Optional[Union[str, Path]] = None,
        asset_path: Optional[Union[str, Path]] = None,
        enable_cache: bool = True,
    ):
        self.logger = get_logger(__name__)

        # リソース管理基本設定
        self.template_path = (
            Path(template_path)
            if template_path
            else Path("kumihan_formatter/templates")
        )
        self.asset_path = (
            Path(asset_path) if asset_path else Path("kumihan_formatter/assets")
        )

        # CoreManager統合機能の遅延初期化
        self._file_manager = None
        self._template_manager = None

        # OptimizationManager統合機能（キャッシュ）
        self.enable_cache = enable_cache
        self._cache_manager = None
        self._file_cache = {}  # 簡易ファイルキャッシュ
        self._template_cache = {}  # テンプレートキャッシュ

        self.logger.info(
            "ResourceManager initialized - unified resource management with CoreManager and OptimizationManager integration"
        )

    @property
    def file_manager(self):
        """FileManagerの遅延初期化（CoreManager統合）"""
        if self._file_manager is None:
            try:
                from ..core.io.file_manager import FileManager

                self._file_manager = FileManager()
            except ImportError as e:
                self.logger.warning(f"FileManager not available: {e}")
                self._file_manager = None
        return self._file_manager

    @property
    def template_manager(self):
        """TemplateManagerの遅延初期化（CoreManager統合）"""
        if self._template_manager is None:
            try:
                from ..core.template_manager import TemplateManager

                self._template_manager = TemplateManager()
            except ImportError as e:
                self.logger.warning(f"TemplateManager not available: {e}")
                self._template_manager = None
        return self._template_manager

    @property
    def cache_manager(self):
        """CacheManagerの遅延初期化（OptimizationManager統合）"""
        if self._cache_manager is None and self.enable_cache:
            try:
                from ..core.optimization.cache.high_performance_cache_manager import (
                    HighPerformanceCacheManager,
                )

                self._cache_manager = HighPerformanceCacheManager()
            except ImportError as e:
                self.logger.warning(f"HighPerformanceCacheManager not available: {e}")
                self._cache_manager = None
        return self._cache_manager

    # ファイルリソース管理（CoreManager統合）
    def read_file(self, file_path: Union[str, Path], use_cache: bool = True) -> str:
        """ファイル読み込み - CoreManager統合 + キャッシュ機能"""
        file_path_str = str(file_path)

        # キャッシュから取得を試行
        if use_cache and self.enable_cache and file_path_str in self._file_cache:
            self.logger.debug(f"File read from cache: {file_path}")
            return self._file_cache[file_path_str]

        try:
            content = None

            # FileManagerによる読み込みを優先
            if self.file_manager:
                try:
                    content = self.file_manager.read_file(file_path)
                except Exception as e:
                    self.logger.warning(f"FileManager read failed for {file_path}: {e}")

            # フォールバック：直接読み込み
            if content is None:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            # キャッシュに保存
            if use_cache and self.enable_cache:
                self._file_cache[file_path_str] = content

            self.logger.debug(f"File read: {file_path}")
            return content

        except Exception as e:
            self.logger.error(f"File read error for {file_path}: {e}")
            raise

    def write_file(self, file_path: Union[str, Path], content: str) -> None:
        """ファイル書き込み - CoreManager統合"""
        try:
            # FileManagerによる書き込みを優先
            if self.file_manager:
                try:
                    self.file_manager.write_file(file_path, content)
                    # キャッシュを更新
                    if self.enable_cache:
                        self._file_cache[str(file_path)] = content
                    self.logger.info(f"File written via FileManager: {file_path}")
                    return
                except Exception as e:
                    self.logger.warning(
                        f"FileManager write failed for {file_path}: {e}"
                    )

            # フォールバック：直接書き込み
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # キャッシュを更新
            if self.enable_cache:
                self._file_cache[str(file_path)] = content

            self.logger.info(f"File written: {file_path}")

        except Exception as e:
            self.logger.error(f"File write error for {file_path}: {e}")
            raise

    def copy_file(
        self, source: Union[str, Path], destination: Union[str, Path]
    ) -> None:
        """ファイルコピー"""
        try:
            import shutil

            shutil.copy2(source, destination)

            # キャッシュを無効化（コピー先ファイル）
            if self.enable_cache:
                self._file_cache.pop(str(destination), None)

            self.logger.info(f"File copied from {source} to {destination}")
        except Exception as e:
            self.logger.error(f"File copy error: {e}")
            raise

    def delete_file(self, file_path: Union[str, Path]) -> None:
        """ファイル削除"""
        try:
            Path(file_path).unlink()

            # キャッシュから削除
            if self.enable_cache:
                self._file_cache.pop(str(file_path), None)

            self.logger.info(f"File deleted: {file_path}")
        except Exception as e:
            self.logger.error(f"File deletion error: {e}")
            raise

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """ファイル検証 - CoreManager統合"""
        # FileManagerの検証機能を優先
        if self.file_manager:
            try:
                return self.file_manager.validate_file(file_path)
            except Exception as e:
                self.logger.warning(f"FileManager validation failed: {e}")

        # フォールバック：基本的な検証
        return Path(file_path).exists() and Path(file_path).is_file()

    # テンプレートリソース管理（CoreManager統合）
    def load_template(self, template_name: str, use_cache: bool = True) -> Any:
        """テンプレート読み込み - CoreManager統合 + キャッシュ機能"""
        # キャッシュから取得を試行
        if use_cache and self.enable_cache and template_name in self._template_cache:
            self.logger.debug(f"Template loaded from cache: {template_name}")
            return self._template_cache[template_name]

        try:
            template = None

            # TemplateManagerによる読み込みを優先
            if self.template_manager:
                try:
                    template = self.template_manager.load_template(template_name)
                except Exception as e:
                    self.logger.warning(
                        f"TemplateManager load failed for {template_name}: {e}"
                    )

            # フォールバック：直接読み込み
            if template is None:
                template_path = self.template_path / template_name
                if template_path.exists():
                    template = self.read_file(template_path, use_cache=False)
                else:
                    raise FileNotFoundError(f"Template not found: {template_name}")

            # キャッシュに保存
            if use_cache and self.enable_cache:
                self._template_cache[template_name] = template

            return template

        except Exception as e:
            self.logger.error(f"Template loading error for {template_name}: {e}")
            raise

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """テンプレート描画 - CoreManager統合"""
        try:
            # TemplateManagerによる描画を優先
            if self.template_manager:
                try:
                    return self.template_manager.render_template(template_name, context)
                except Exception as e:
                    self.logger.warning(
                        f"TemplateManager render failed for {template_name}: {e}"
                    )

            # フォールバック：基本的な描画
            template_content = self.load_template(template_name)
            # 簡易的なテンプレート処理（本格的な実装は後で追加）
            for key, value in context.items():
                template_content = template_content.replace(
                    f"{{{{{key}}}}}", str(value)
                )
            return template_content

        except Exception as e:
            self.logger.error(f"Template rendering error for {template_name}: {e}")
            raise

    def get_available_templates(self) -> List[str]:
        """利用可能テンプレート一覧 - CoreManager統合"""
        try:
            # TemplateManagerの一覧取得を優先
            if self.template_manager:
                try:
                    return self.template_manager.get_available_templates()
                except Exception as e:
                    self.logger.warning(f"TemplateManager listing failed: {e}")

            # フォールバック：直接スキャン
            if not self.template_path.exists():
                return []
            return [p.name for p in self.template_path.glob("*.j2") if p.is_file()]

        except Exception as e:
            self.logger.error(f"Template listing error: {e}")
            return []

    def template_exists(self, template_name: str) -> bool:
        """テンプレート存在確認"""
        template_path = self.template_path / template_name
        return template_path.exists() and template_path.is_file()

    def read_template(self, template_name: str) -> str:
        """テンプレート読み込み"""
        template_path = self.template_path / template_name
        return self.read_file(template_path)

    # アセットリソース管理
    def get_asset_path(self, asset_name: str) -> Path:
        """アセットパス取得"""
        return self.asset_path / asset_name

    def read_asset(
        self,
        asset_name: str,
        mode: str = "r",
        encoding: str = "utf-8",
        use_cache: bool = True,
    ) -> Union[str, bytes]:
        """アセット読み込み - キャッシュ機能付き"""
        asset_path = self.get_asset_path(asset_name)

        # テキストモードのキャッシュのみ対応
        cache_key = f"{asset_name}_{mode}_{encoding}" if mode == "r" else None

        if (
            use_cache
            and self.enable_cache
            and cache_key
            and cache_key in self._file_cache
        ):
            self.logger.debug(f"Asset read from cache: {asset_name}")
            return self._file_cache[cache_key]

        try:
            if mode == "rb":
                with open(asset_path, mode) as f:
                    content = f.read()
            else:
                with open(asset_path, mode, encoding=encoding) as f:
                    content = f.read()

                # テキストモードの場合のみキャッシュ
                if use_cache and self.enable_cache and cache_key:
                    self._file_cache[cache_key] = content

            return content

        except Exception as e:
            self.logger.error(f"Asset reading error for {asset_name}: {e}")
            raise

    def asset_exists(self, asset_name: str) -> bool:
        """アセット存在確認"""
        return self.get_asset_path(asset_name).exists()

    def list_assets(self, pattern: str = "*") -> List[str]:
        """アセット一覧取得"""
        try:
            if not self.asset_path.exists():
                return []
            return [p.name for p in self.asset_path.glob(pattern) if p.is_file()]
        except Exception as e:
            self.logger.error(f"Asset listing error: {e}")
            return []

    # キャッシュ管理（OptimizationManager統合）
    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計取得 - OptimizationManager統合"""
        stats = {
            "cache_enabled": self.enable_cache,
            "file_cache_size": len(self._file_cache),
            "template_cache_size": len(self._template_cache),
        }

        # HighPerformanceCacheManagerの統計情報
        if self.cache_manager:
            try:
                if hasattr(self.cache_manager, "get_statistics"):
                    external_stats = self.cache_manager.get_statistics()
                    stats["external_cache"] = external_stats
                elif hasattr(self.cache_manager, "stats"):
                    stats["external_cache"] = self.cache_manager.stats
            except Exception as e:
                self.logger.warning(f"Failed to get cache manager statistics: {e}")

        return stats

    def clear_cache(self, cache_type: str = "all") -> None:
        """キャッシュクリア - OptimizationManager統合"""
        try:
            if cache_type in ["all", "file"]:
                self._file_cache.clear()
                self.logger.info("File cache cleared")

            if cache_type in ["all", "template"]:
                self._template_cache.clear()
                self.logger.info("Template cache cleared")

            if cache_type in ["all", "external"] and self.cache_manager:
                if hasattr(self.cache_manager, "clear_cache"):
                    self.cache_manager.clear_cache()
                elif hasattr(self.cache_manager, "clear"):
                    self.cache_manager.clear()
                self.logger.info("External cache cleared")

        except Exception as e:
            self.logger.warning(f"Cache clear failed: {e}")

    # 統計・監視
    def get_resource_statistics(self) -> Dict[str, Any]:
        """リソース統計情報"""
        stats = {
            "templates": {
                "available": len(self.get_available_templates()),
                "list": self.get_available_templates(),
                "cached": len(self._template_cache),
            },
            "assets": {
                "available": len(self.list_assets()),
                "list": self.list_assets(),
            },
            "files": {
                "cached": len(self._file_cache),
            },
            "paths": {
                "template_path": str(self.template_path),
                "asset_path": str(self.asset_path),
            },
            "cache": self.get_cache_stats(),
        }
        return stats

    def check_resources_health(self) -> Dict[str, Any]:
        """リソース健全性チェック"""
        health_status = {
            "template_path_exists": self.template_path.exists(),
            "template_path_readable": (
                self.template_path.is_dir() if self.template_path.exists() else False
            ),
            "asset_path_exists": self.asset_path.exists(),
            "asset_path_readable": (
                self.asset_path.is_dir() if self.asset_path.exists() else False
            ),
            "file_manager_available": self.file_manager is not None,
            "template_manager_available": self.template_manager is not None,
            "cache_manager_available": self.cache_manager is not None,
            "cache_enabled": self.enable_cache,
        }

        health_status["overall_healthy"] = all(
            [health_status["template_path_exists"], health_status["asset_path_exists"]]
        )
        return health_status

    def cleanup_resources(self, temp_files_only: bool = True) -> None:
        """リソースクリーンアップ"""
        try:
            # キャッシュクリア
            self.clear_cache()

            if temp_files_only:
                # 一時ファイルのみクリーンアップ
                temp_dir = Path("tmp")
                if temp_dir.exists():
                    import shutil

                    shutil.rmtree(temp_dir)
                    temp_dir.mkdir(exist_ok=True)
                    self.logger.info("Temporary resources cleaned up")
            else:
                self.logger.info("Full resource cleanup requested but not implemented")
        except Exception as e:
            self.logger.error(f"Resource cleanup error: {e}")

    def shutdown(self) -> None:
        """リソース解放"""
        try:
            # キャッシュクリア
            self.clear_cache()

            # 統合コンポーネントのシャットダウン
            for component_name, component in [
                ("_file_manager", self._file_manager),
                ("_template_manager", self._template_manager),
                ("_cache_manager", self._cache_manager),
            ]:
                if component and hasattr(component, "shutdown"):
                    try:
                        component.shutdown()
                    except Exception as e:
                        self.logger.warning(
                            f"Error shutting down {component_name}: {e}"
                        )

            # コンポーネント参照をクリア
            self._file_manager = None
            self._template_manager = None
            self._cache_manager = None

            self.logger.info("ResourceManager shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during ResourceManager shutdown: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
