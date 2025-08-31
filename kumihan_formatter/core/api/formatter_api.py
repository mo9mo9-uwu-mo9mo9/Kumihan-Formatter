"""
FormatterAPI - ユーザーインターフェース専用クラス

Issue #1249対応: 統合API設計統一
公開API・ユーザーインターフェース・エラーハンドリングを担当
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging

from .formatter_config import FormatterConfig
from .manager_coordinator import ManagerCoordinator
from .formatter_core import FormatterCore


class FormatterAPI:
    """統合API ユーザーインターフェースクラス"""

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        performance_mode: str = "standard",
    ):
        self.logger = logging.getLogger(__name__)

        # 責任分離されたコンポーネントの初期化
        self.config = FormatterConfig(config_path, performance_mode)
        self.coordinator = ManagerCoordinator(
            self.config.get_config(), performance_mode
        )
        self.core = FormatterCore(self.coordinator)

        mode_message = (
            "統合Managerシステム対応版"
            if performance_mode == "standard"
            else "高性能最適化版"
        )
        self.logger.info(f"FormatterAPI initialized - {mode_message}")

    # 公開API メソッド群

    def convert(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """統合Managerシステムによる最適化変換"""
        return self.core.convert_file(input_file, output_file, template, options)

    def convert_text(self, text: str, template: str = "default") -> str:
        """テキスト→HTML変換（統合Managerシステム対応）"""
        return self.core.convert_text(text, template)

    def parse_text(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """テキスト解析（統合ParsingManager対応）"""
        return self.core.parse_text(text, parser_type)

    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証（統合ParsingManager対応）"""
        return self.core.validate_syntax(text)

    def parse_file(
        self, file_path: Union[str, Path], parser_type: str = "auto"
    ) -> Dict[str, Any]:
        """ファイル解析（統合Managerシステム対応）"""
        return self.core.parse_file(file_path, parser_type)

    def get_available_templates(self) -> List[str]:
        """利用可能テンプレート取得（CoreManager対応）"""
        return self.core.get_available_templates()

    def get_system_info(self) -> Dict[str, Any]:
        """統合システム情報取得"""
        return self.coordinator.get_system_info()

    # リソース管理

    def close(self) -> None:
        """統合システムのリソース解放"""
        try:
            self.coordinator.close()
            self.config.clear_cache()
            self.logger.info("FormatterAPI closed - 統合Managerシステム")
        except Exception as e:
            self.logger.error(f"クローズ処理中にエラー: {e}")

    def __enter__(self) -> "FormatterAPI":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
