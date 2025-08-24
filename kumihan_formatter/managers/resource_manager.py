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
    """統合リソース管理Manager - Issue #1171対応"""

    def __init__(
        self,
        template_path: Optional[Union[str, Path]] = None,
        asset_path: Optional[Union[str, Path]] = None,
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

        self.logger.info(
            "ResourceManager initialized - unified resource management system"
        )

    # ファイルリソース管理
    def read_file(self, file_path: Union[str, Path]) -> str:
        """ファイル読み込み"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.debug(f"File read: {file_path}")
            return content
        except Exception as e:
            self.logger.error(f"File read error for {file_path}: {e}")
            raise

    def write_file(self, file_path: Union[str, Path], content: str) -> None:
        """ファイル書き込み"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
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
            self.logger.info(f"File copied from {source} to {destination}")
        except Exception as e:
            self.logger.error(f"File copy error: {e}")
            raise

    def delete_file(self, file_path: Union[str, Path]) -> None:
        """ファイル削除"""
        try:
            Path(file_path).unlink()
            self.logger.info(f"File deleted: {file_path}")
        except Exception as e:
            self.logger.error(f"File deletion error: {e}")
            raise

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """ファイル検証"""
        return Path(file_path).exists() and Path(file_path).is_file()

    # テンプレートリソース管理
    def get_available_templates(self) -> List[str]:
        """利用可能テンプレート一覧"""
        try:
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
        self, asset_name: str, mode: str = "r", encoding: str = "utf-8"
    ) -> Union[str, bytes]:
        """アセット読み込み"""
        asset_path = self.get_asset_path(asset_name)
        try:
            if mode == "rb":
                with open(asset_path, mode) as f:
                    return f.read()
            else:
                with open(asset_path, mode, encoding=encoding) as f:
                    return f.read()
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

    # 統計・監視
    def get_resource_statistics(self) -> Dict[str, Any]:
        """リソース統計情報"""
        return {
            "templates": {
                "available": len(self.get_available_templates()),
                "list": self.get_available_templates(),
            },
            "assets": {
                "available": len(self.list_assets()),
                "list": self.list_assets(),
            },
            "paths": {
                "template_path": str(self.template_path),
                "asset_path": str(self.asset_path),
            },
        }

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
        }

        health_status["overall_healthy"] = all(health_status.values())
        return health_status

    def cleanup_resources(self, temp_files_only: bool = True) -> None:
        """リソースクリーンアップ"""
        try:
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
            self.logger.info("ResourceManager shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during ResourceManager shutdown: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
