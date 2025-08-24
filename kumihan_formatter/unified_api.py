"""
統合API - Issue #1146 アーキテクチャ簡素化
==========================================

従来の複雑なManager/Parserクラス群を統合し、
シンプルで直感的なAPIを提供します。

使用例:
    from kumihan_formatter.unified_api import KumihanFormatter

    formatter = KumihanFormatter()
    result = formatter.convert("input.txt", "output.html")
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path

from .managers import (
    CoreManager,
    ParsingManager,
    OptimizationManager,
    PluginManager,
    DistributionManager,
)
from .parsers import MainParser
from .core.utilities.logger import get_logger


class KumihanFormatter:
    """統合Kumihan-Formatterクラス - 全機能へのシンプルなエントリーポイント"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.logger = get_logger(__name__)

        # 統合Managerシステム初期化
        self.core = CoreManager(config_path)
        self.parser = ParsingManager()
        self.optimization = OptimizationManager(
            self.core.config if hasattr(self.core, "config") else None
        )
        self.plugins = PluginManager()
        self.distribution = DistributionManager()

        # メインパーサー初期化
        self.main_parser = MainParser()

        self.logger.info("KumihanFormatter initialized - unified architecture")

    def convert(
        self,
        input_file: Union[str, Path],
        output_file: Union[str, Path] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """ファイル変換のメインエントリーポイント"""
        try:
            # ファイル読み込み
            content = self.core.read_file(input_file)

            # 解析
            parsed_result = self.parser.parse(content)

            # レンダリング
            if not output_file:
                output_file = Path(input_file).with_suffix(".html")

            rendered_content = self.core.render_template(
                template, {"content": parsed_result, "options": options or {}}
            )

            # ファイル出力
            self.core.write_file(output_file, rendered_content)

            return {
                "status": "success",
                "input_file": str(input_file),
                "output_file": str(output_file),
                "template": template,
            }

        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            return {"status": "error", "error": str(e), "input_file": str(input_file)}

    def parse_text(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """テキスト解析"""
        return self.parser.parse(text, parser_type)

    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証"""
        return self.main_parser.validate_syntax(text)

    def get_available_templates(self) -> list:
        """利用可能テンプレート一覧"""
        return self.core.get_available_templates()

    def get_system_info(self) -> Dict[str, Any]:
        """システム情報取得"""
        return {
            "managers": {
                "core": "CoreManager",
                "parsing": "ParsingManager",
                "optimization": "OptimizationManager",
                "plugins": "PluginManager",
                "distribution": "DistributionManager",
            },
            "parsers": self.parser.get_available_parsers(),
            "templates": self.get_available_templates(),
            "optimization_status": self.optimization.get_optimization_status(),
        }

    def close(self) -> None:
        """リソース解放"""
        try:
            self.core.shutdown()
            self.logger.info("KumihanFormatter closed successfully")
        except Exception as e:
            self.logger.error(f"Error during close: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便利関数
def quick_convert(
    input_file: Union[str, Path], output_file: Union[str, Path] = None
) -> Dict[str, Any]:
    """クイック変換関数"""
    with KumihanFormatter() as formatter:
        return formatter.convert(input_file, output_file)


def quick_parse(text: str) -> Dict[str, Any]:
    """クイック解析関数"""
    with KumihanFormatter() as formatter:
        return formatter.parse_text(text)
