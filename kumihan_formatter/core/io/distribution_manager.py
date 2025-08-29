"""
DistributionManager - 配布管理統合クラス
====================================

Issue #1215対応: 分割された配布機能の統合管理
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .distribution_structure import DistributionStructure
from .distribution_converter import DistributionConverter
from .distribution_processor import DistributionProcessor


class DistributionManager:
    """配布管理統合クラス - Issue #319対応完成版"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        DistributionManager初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 分割されたコンポーネントを統合
        self.structure = DistributionStructure(config)
        self.converter = DistributionConverter(config)
        self.processor = DistributionProcessor(config)

    def create_distribution(
        self, source_dir: Union[str, Path], output_dir: Union[str, Path]
    ) -> bool:
        """
        配布用ディレクトリを作成

        Args:
            source_dir: ソースディレクトリ
            output_dir: 出力ディレクトリ

        Returns:
            成功時True、失敗時False
        """
        try:
            # 1. ディレクトリ構造作成
            success = self.structure.create_structure(output_dir)
            if not success:
                return False

            # 2. ファイル変換
            success = self.converter.convert_files(source_dir, output_dir)
            if not success:
                return False

            # 3. 配布処理
            success = self.processor.process_distribution(output_dir)
            if not success:
                return False

            self.logger.info(f"配布作成完了: {output_dir}")
            return True

        except Exception as e:
            self.logger.error(f"配布作成中にエラー: {e}")
            return False

    def validate_distribution(self, dist_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        配布ディレクトリの検証

        Args:
            dist_dir: 配布ディレクトリ

        Returns:
            検証結果辞書
        """
        try:
            result = {"valid": True, "errors": [], "warnings": [], "files_checked": 0}

            dist_path = Path(dist_dir)
            if not dist_path.exists():
                result["valid"] = False
                result["errors"].append(f"配布ディレクトリが存在しません: {dist_dir}")
                return result

            # 基本的な検証
            required_files = ["index.html"]  # 必須ファイル例

            for required_file in required_files:
                file_path = dist_path / required_file
                if not file_path.exists():
                    result["warnings"].append(
                        f"推奨ファイルが見つかりません: {required_file}"
                    )
                else:
                    result["files_checked"] += 1

            return result

        except Exception as e:
            self.logger.error(f"配布検証中にエラー: {e}")
            return {
                "valid": False,
                "errors": [f"検証エラー: {str(e)}"],
                "warnings": [],
                "files_checked": 0,
            }

    def get_distribution_info(self) -> Dict[str, Any]:
        """配布管理情報を取得"""
        return {
            "name": "DistributionManager (Integrated)",
            "version": "1.0.0",
            "config": self.config,
            "components": {
                "structure": "DistributionStructure",
                "converter": "DistributionConverter",
                "processor": "DistributionProcessor",
            },
        }
