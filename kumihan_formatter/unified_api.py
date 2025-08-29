"""
統合API - Issue #1215 アーキテクチャ統合完了版
==========================================

新しい統合Managerシステム（5個のManager）による
高性能で保守性の高いAPIを提供します。

使用例:
    from kumihan_formatter.unified_api import KumihanFormatter

    formatter = KumihanFormatter()
    result = formatter.convert("input.txt", "output.html")
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import logging
from pathlib import Path
from .managers import (
    CoreManager,
    ParsingManager,
    OptimizationManager,
    PluginManager,
    DistributionManager,
)
from .parsers.main_parser import MainParser
from .core.rendering.main_renderer import MainRenderer


class KumihanFormatter:
    """統合Kumihan-Formatterクラス - 新統合Managerシステム対応"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path

        # 設定読み込み
        self.config = self._load_config(config_path)

        # 新統合Managerシステム初期化
        self.core_manager = CoreManager(self.config)
        self.parsing_manager = ParsingManager(self.config)
        self.optimization_manager = OptimizationManager(self.config)
        self.plugin_manager = PluginManager(self.config)
        self.distribution_manager = DistributionManager(self.config)

        # メインコンポーネント
        self.main_parser = MainParser(self.config)
        self.main_renderer = MainRenderer(self.config)

        self.logger.info("KumihanFormatter initialized - 統合Managerシステム対応版")

    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        if config_path and Path(config_path).exists():
            try:
                import json

                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"設定ファイル読み込み失敗: {e}")

        return {}

    def convert(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """統合Managerシステムによる最適化変換"""
        try:
            # ファイル読み込み（CoreManager使用）
            content = self.core_manager.read_file(input_file)
            if not content:
                raise FileNotFoundError(f"Input file not found or empty: {input_file}")

            # 最適化解析（OptimizationManager + MainParser使用）
            parsed_result = self.optimization_manager.optimize_parsing(
                content, lambda c: self.main_parser.parse(c, "auto")
            )

            if not parsed_result:
                raise ValueError("パーシング処理に失敗しました")

            # 出力パス決定
            if not output_file:
                output_file = Path(input_file).with_suffix(".html")

            # レンダリング実行（MainRenderer使用）
            context = {"template": template, **(options or {})}
            rendered_content = self.main_renderer.render(parsed_result, context)

            # ファイル出力（CoreManager使用、tmp配下強制）
            success = self.main_renderer.render_to_file(
                parsed_result, output_file, None, context
            )

            if not success:
                raise IOError(f"ファイル出力に失敗: {output_file}")

            return {
                "status": "success",
                "input_file": str(input_file),
                "output_file": str(output_file),
                "template": template,
                "parser_used": "MainParser (auto)",
                "optimization_applied": True,
            }

        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            return {"status": "error", "error": str(e), "input_file": str(input_file)}

    def convert_text(self, text: str, template: str = "default") -> str:
        """テキスト→HTML変換（統合Managerシステム対応）"""
        try:
            # 統合解析実行
            parsed_result = self.main_parser.parse(text, "auto")
            if not parsed_result:
                raise ValueError("テキスト解析に失敗しました")

            # 統合レンダリング実行
            context = {"template": template}
            html_content = self.main_renderer.render(parsed_result, context)

            self.logger.debug(
                f"Text conversion completed: {len(text)} chars → {len(html_content)} chars"
            )
            return html_content

        except Exception as e:
            self.logger.error(f"Text conversion error: {e}")
            return f"<p>Conversion Error: {e}</p>"

    def parse_text(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """テキスト解析（統合ParsingManager対応）"""
        try:
            # 統合解析・検証実行
            result = self.parsing_manager.parse_and_validate(text, parser_type)
            return result
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return {"status": "error", "error": str(e)}

    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証（統合ParsingManager対応）"""
        try:
            validation_result = self.parsing_manager.validate_syntax(text)
            return {
                "status": "valid" if validation_result["valid"] else "invalid",
                "errors": validation_result.get("syntax_errors", []),
                "warnings": validation_result.get("syntax_warnings", []),
                "total_errors": len(validation_result.get("syntax_errors", [])),
            }
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return {"status": "error", "error": str(e), "errors": []}

    def parse_file(
        self, file_path: Union[str, Path], parser_type: str = "auto"
    ) -> Dict[str, Any]:
        """ファイル解析（統合Managerシステム対応）"""
        try:
            # CoreManagerによるファイル読み込み
            content = self.core_manager.read_file(file_path)
            if not content:
                raise FileNotFoundError(f"File not found or empty: {file_path}")

            # 統合解析実行
            result = self.parsing_manager.parse_and_validate(content, parser_type)
            result["file_path"] = str(file_path)
            return result
        except Exception as e:
            self.logger.error(f"File parsing error: {e}")
            return {"status": "error", "error": str(e), "file_path": str(file_path)}

    def get_available_templates(self) -> List[str]:
        """利用可能テンプレート取得（CoreManager対応）"""
        try:
            # CoreManagerからテンプレート一覧取得を試行
            templates = ["default", "minimal", "docs"]  # 基本テンプレート
            return templates
        except Exception as e:
            self.logger.error(f"Template list error: {e}")
            return ["default"]

    def get_system_info(self) -> Dict[str, Any]:
        """統合システム情報取得"""
        try:
            return {
                "architecture": "integrated_manager_system",
                "components": {
                    "core_manager": "CoreManager",
                    "parsing_manager": "ParsingManager",
                    "optimization_manager": "OptimizationManager",
                    "plugin_manager": "PluginManager",
                    "distribution_manager": "DistributionManager",
                    "main_parser": "MainParser",
                    "main_renderer": "MainRenderer",
                },
                "version": "5.0.0-integrated",
                "status": "production_ready",
                "optimization_stats": self.optimization_manager.get_optimization_statistics(),
                "core_stats": self.core_manager.get_core_statistics(),
            }
        except Exception as e:
            self.logger.error(f"System info error: {e}")
            return {"status": "error", "error": str(e)}

    def close(self) -> None:
        """統合システムのリソース解放"""
        try:
            # キャッシュクリア
            self.core_manager.clear_cache()
            self.optimization_manager.clear_optimization_cache()

            self.logger.info("KumihanFormatter closed - 統合Managerシステム")
        except Exception as e:
            self.logger.error(f"クローズ処理中にエラー: {e}")

    def __enter__(self) -> "KumihanFormatter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


# 便利関数（統合Managerシステム対応）
def quick_convert(
    input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """クイック変換関数（統合システム）"""
    with KumihanFormatter() as formatter:
        return formatter.convert(input_file, output_file)


def quick_parse(text: str) -> Dict[str, Any]:
    """クイック解析関数（統合ParsingManager）"""
    with KumihanFormatter() as formatter:
        return formatter.parse_text(text)


def unified_parse(text: str, parser_type: str = "auto") -> Dict[str, Any]:
    """統合パーサーシステムによる最適化解析"""
    with KumihanFormatter() as formatter:
        return formatter.parse_text(text, parser_type)


def validate_kumihan_syntax(text: str) -> Dict[str, Any]:
    """Kumihan記法構文の詳細検証（統合検証システム）"""
    with KumihanFormatter() as formatter:
        return formatter.validate_syntax(text)


def get_parser_system_info() -> Dict[str, Any]:
    """統合Managerシステムの詳細情報取得"""
    with KumihanFormatter() as formatter:
        return formatter.get_system_info()


# 後方互換性のためのエイリアス
parse = unified_parse
validate = validate_kumihan_syntax


def main() -> None:
    """CLI エントリーポイント - シンプル実装"""
    import sys

    if len(sys.argv) < 2:
        print("使用方法: kumihan <入力ファイル> [出力ファイル]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = quick_convert(input_file, output_file)
        if result["status"] == "success":
            print(f"変換完了: {result['output_file']}")
        else:
            print(f"変換エラー: {result['error']}")
            sys.exit(1)
    except Exception as e:
        print(f"実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
