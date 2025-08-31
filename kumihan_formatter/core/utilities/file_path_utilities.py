"""
ファイル パス ユーティリティ

パス処理・フィルタリング・サイズ情報取得機能
Issue #492 Phase 5A - file_operations.py分割
"""

from pathlib import Path
from typing import Dict, List

import logging


class FilePathUtilities:
    """File path processing and filtering utilities"""

    @staticmethod
    def load_distignore_patterns() -> List[str]:
        """
        Load exclusion patterns from .distignore file

        Returns:
            list: List of exclusion patterns
        """
        logger = logging.getLogger(__name__)
        patterns = []
        distignore_path = Path(".distignore")

        if distignore_path.exists():
            logger.debug(f"Loading exclusion patterns from {distignore_path}")
            with open(distignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comment lines and empty lines
                    if line and not line.startswith("#"):
                        patterns.append(line)

        logger.debug(f"Loaded {len(patterns)} exclusion patterns")
        return patterns

    @staticmethod
    def should_exclude(path: Path, patterns: List[str], base_path: Path) -> bool:
        """
        Check if the specified path matches exclusion patterns

        Args:
            path: Path to check
            patterns: List of exclusion patterns
            base_path: Base path for relative calculation

        Returns:
            bool: True if should be excluded
        """
        relative_path = path.relative_to(base_path)
        relative_str = str(relative_path)

        for pattern in patterns:
            # Directory pattern handling
            if pattern.endswith("/"):
                # Check files under directory
                dir_pattern = pattern.rstrip("/")

                # Complete path matching
                if (
                    relative_str.startswith(dir_pattern + "/")
                    or relative_str == dir_pattern
                ):
                    return True

        # No patterns matched
        return False

    @staticmethod
    def get_file_size_info(path: Path) -> Dict[str, Any]:
        """Get file size information"""
        if path.exists():
            size = path.stat().st_size
            return {
                "size_bytes": size,
                "size_mb": size / (1024 * 1024),
                "size_formatted": f"{size:,}",
                "is_large": size > 10 * 1024 * 1024,  # 10MB以上
            }
        return {
            "size_bytes": 0,
            "size_mb": 0.0,
            "size_formatted": "0",
            "is_large": False,
        }

    @staticmethod
    def estimate_processing_time(size_mb: float) -> str:
        """
        ファイルサイズから処理時間を推定

        Args:
            size_mb: ファイルサイズ（MB）

        Returns:
            str: 推定時間の説明
        """
        if size_mb < 1:
            return "数秒"
        elif size_mb < 5:
            return "10-30秒"
        elif size_mb < 20:
            return "1-2分"
        else:
            return "2分以上"
