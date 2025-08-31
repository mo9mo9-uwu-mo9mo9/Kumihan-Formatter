"""
FormatterCore - コアロジック専用クラス

Issue #1249対応: 統合API設計統一
実際の変換・パーシング・レンダリング処理を担当
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging

from .manager_coordinator import ManagerCoordinator
from ..utilities.element_counter import count_elements


class FormatterCore:
    """統合API コアロジッククラス"""

    def __init__(self, coordinator: ManagerCoordinator):
        self.logger = logging.getLogger(__name__)
        self.coordinator = coordinator

    def convert_file(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """統合Managerシステムによる最適化変換"""
        try:
            # 最適化モードの場合は遅延初期化
            if self.coordinator.performance_mode == "optimized":
                self.coordinator.ensure_managers_initialized()
                self.coordinator.ensure_parser_initialized()
                self.coordinator.ensure_renderer_initialized()

            # ファイル読み込み（CoreManager使用）
            content = self.coordinator.core_manager.read_file(input_file)
            if not content:
                raise FileNotFoundError(f"Input file not found or empty: {input_file}")

            # 最適化解析（OptimizationManager + MainParser使用）
            parsed_result = self.coordinator.optimization_manager.optimize_parsing(
                content, lambda c: self.coordinator.main_parser.parse(c, "auto")
            )

            if not parsed_result:
                raise ValueError("パーシング処理に失敗しました")

            # 出力パス決定
            if not output_file:
                output_file = Path(input_file).with_suffix(".html")

            # レンダリング実行（MainRenderer使用）
            context = {"template": template, **(options or {})}
            rendered_content = self.coordinator.main_renderer.render(
                parsed_result, context
            )

            # ファイル出力（CoreManager使用、テスト環境自動対応）
            success = self.coordinator.main_renderer.render_to_file(
                parsed_result, output_file, None, context
            )

            if not success:
                raise IOError(f"ファイル出力に失敗: {output_file}")

            # 要素数カウント（テストインターフェース対応）
            elements_count = self._count_elements(parsed_result)

            # 実際の出力パス決定（テスト環境対応）
            actual_output_file = self._get_actual_output_path(output_file)

            result = {
                "status": "success",
                "input_file": str(input_file),
                "output_file": str(actual_output_file),
                "template": template,
                "parser_used": "MainParser (auto)",
                "optimization_applied": True,
                "elements_count": elements_count,
            }

            # パフォーマンスモード情報追加
            if self.coordinator.performance_mode == "optimized":
                result["performance_mode"] = "optimized"

            return result

        except Exception as e:
            self.logger.error(f"File conversion error: {e}")
            return {"status": "error", "error": str(e), "input_file": str(input_file)}

    def convert_text(self, text: str, template: str = "default") -> str:
        """テキスト→HTML変換（統合Managerシステム対応）"""
        try:
            # 最適化モードの場合は遅延初期化
            if self.coordinator.performance_mode == "optimized":
                self.coordinator.ensure_parser_initialized()
                self.coordinator.ensure_renderer_initialized()

            # 統合解析実行
            parsed_result = self.coordinator.main_parser.parse(text, "auto")
            if not parsed_result:
                raise ValueError("テキスト解析に失敗しました")

            # 統合レンダリング実行
            context = {"template": template}
            html_content = self.coordinator.main_renderer.render(parsed_result, context)

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
            self.coordinator.ensure_managers_initialized()
            # 統合解析・検証実行
            result = self.coordinator.parsing_manager.parse_and_validate(
                text, parser_type
            )
            return result
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return {"status": "error", "error": str(e)}

    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証（統合ParsingManager対応）"""
        try:
            self.coordinator.ensure_managers_initialized()
            validation_result = self.coordinator.parsing_manager.validate_syntax(text)
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
            self.coordinator.ensure_managers_initialized()
            # CoreManagerによるファイル読み込み
            content = self.coordinator.core_manager.read_file(file_path)
            if not content:
                raise FileNotFoundError(f"File not found or empty: {file_path}")

            # 統合解析実行
            result = self.coordinator.parsing_manager.parse_and_validate(
                content, parser_type
            )
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

    def _count_elements(self, parsed_result: Any) -> int:
        """要素数カウント（テスト互換性対応）"""
        return count_elements(parsed_result)

    def _get_actual_output_path(self, output_file: Union[str, Path]) -> Path:
        """実際の出力パス決定（MainRendererと同じロジック）"""
        output_path = Path(output_file)

        # テスト環境判定: 一時ディレクトリ内の場合は元パス使用
        if "/tmp" in str(output_path) or "tmp/" in str(output_path):
            # テスト用一時ディレクトリまたは既に tmp 配下の場合はそのまま使用
            return output_path
        else:
            # 通常環境：tmp/ 配下に出力
            return Path("tmp") / Path(output_file).name
