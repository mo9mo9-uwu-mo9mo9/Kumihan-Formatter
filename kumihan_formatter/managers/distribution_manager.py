"""
DistributionManager - 統合配布管理システム

統合対象:
- kumihan_formatter/core/io/distribution/distribution_manager.py
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path
from ..core.io.distribution.distribution_manager import DistributionManager as CoreDistributionManager
from ..core.utilities.logger import get_logger


class DistributionManager:
    """統合配布管理システム"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # コア配布マネージャー統合
        self.core_distribution_manager = CoreDistributionManager()
        
        self.logger.info("DistributionManager initialized - unified distribution system")
    
    def create_distribution(
        self, 
        input_path: Union[str, Path], 
        output_path: Union[str, Path],
        distribution_type: str = "html"
    ) -> Dict[str, Any]:
        """配布パッケージ作成"""
        try:
            return self.core_distribution_manager.create_distribution(
                input_path, output_path, distribution_type
            )
        except Exception as e:
            self.logger.error(f"Distribution creation error: {e}")
            raise
    
    def validate_distribution(self, distribution_path: Union[str, Path]) -> bool:
        """配布パッケージ検証"""
        try:
            return self.core_distribution_manager.validate_distribution(distribution_path)
        except Exception as e:
            self.logger.error(f"Distribution validation error: {e}")
            return False
    
    def get_distribution_info(self, distribution_path: Union[str, Path]) -> Dict[str, Any]:
        """配布パッケージ情報取得"""
        return self.core_distribution_manager.get_distribution_info(distribution_path)
    
    def get_supported_formats(self) -> list:
        """サポート配布形式一覧"""
        return self.core_distribution_manager.get_supported_formats()
    
    def optimize_distribution(self, distribution_path: Union[str, Path]) -> Dict[str, Any]:
        """配布パッケージ最適化"""
        try:
            return self.core_distribution_manager.optimize_distribution(distribution_path)
        except Exception as e:
            self.logger.error(f"Distribution optimization error: {e}")
            return {"status": "optimization_failed", "error": str(e)}