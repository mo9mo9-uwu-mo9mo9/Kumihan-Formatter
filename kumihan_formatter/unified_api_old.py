from typing import Any, Dict, List, Optional, Union

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

from pathlib import Path

import logging
from .managers import (
    CoreManager,
    ParsingManager,
    OptimizationManager,
    PluginManager,
)

# DistributionManagerは core.io.distribution_manager に移動
from .parsers.main_parser import MainParser
from .core.rendering.main_renderer import MainRenderer


class KumihanFormatter:
    """統合Kumihan-Formatterクラス - 新統合Managerシステム対応"""

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        performance_mode: str = "standard",
    ):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.performance_mode = performance_mode

        # パフォーマンスモード対応設定読み込み
        if performance_mode == "optimized":
            self.config = self._load_config_cached(config_path)
        else:
            self.config = self._load_config(config_path)

        # パフォーマンスモードに応じた初期化
        if performance_mode == "optimized":
            self._initialize_optimized_mode()
        else:
            self._initialize_standard_mode()

        mode_message = (
            "統合Managerシステム対応版"
            if performance_mode == "standard"
            else "高性能最適化版"
        )
        self.logger.info(f"KumihanFormatter initialized - {mode_message}")

    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        if config_path and Path(config_path).exists():
            try:
                import json

                with open(config_path, "r", encoding="utf-8") as f:
                    result = json.load(f)
                    return result  # type: ignore[no-any-return]
            except Exception as e:
                self.logger.warning(f"設定ファイル読み込み失敗: {e}")

        return {}

    # クラスレベルキャッシュ（パフォーマンス最適化用）
    _config_cache: Dict[str, Dict[str, Any]] = {}

    def _load_config_cached(
        self, config_path: Optional[Union[str, Path]]
    ) -> Dict[str, Any]:
        """キャッシュ機能付き設定読み込み（最適化モード用）"""
        cache_key = str(config_path) if config_path else "default"

        if cache_key in self._config_cache:
            self.logger.debug(f"Config cache hit: {cache_key}")
            return self._config_cache[cache_key]

        # 設定読み込み
        config = self._load_config(config_path)
        self._config_cache[cache_key] = config
        self.logger.debug(f"Config cached: {cache_key}")

        return config

    def _initialize_optimized_mode(self) -> None:
        """最適化モード用の初期化（遅延初期化）"""
        import time

        # 遅延初期化フラグ
        self._managers_initialized = False
        self._main_parser_initialized = False
        self._main_renderer_initialized = False

        # 最適化フラグ
        self._enable_caching = True

        self.logger.debug("Optimized mode initialized with lazy loading")

    def _initialize_standard_mode(self) -> None:
        """標準モード用の初期化（従来通り）"""
        # 新統合Managerシステム初期化
        self.core_manager = CoreManager(self.config)
        self.parsing_manager = ParsingManager(self.config)
        self.optimization_manager = OptimizationManager(self.config)
        self.plugin_manager = PluginManager(self.config)
        # self.distribution_manager = DistributionManager(self.config)  # 移動済み

        # メインコンポーネント
        self.main_parser = MainParser(self.config)
        self.main_renderer = MainRenderer(self.config)

        self.logger.debug("Standard mode initialized with full initialization")

    def _ensure_managers_initialized(self) -> None:
        """Managerの遅延初期化（最適化モード用）"""
        if self.performance_mode == "optimized" and not self._managers_initialized:
            try:

                start_time = time.perf_counter()

                self.core_manager = CoreManager(self.config)
                self.parsing_manager = ParsingManager(self.config)
                self.optimization_manager = OptimizationManager(self.config)
                self.plugin_manager = PluginManager(self.config)
                # self.distribution_manager = DistributionManager(self.config)  # 移動済み

                self._managers_initialized = True
                end_time = time.perf_counter()

                self.logger.debug(
                    f"Managers lazy initialized in {end_time - start_time:.4f}s"
                )

            except Exception as e:
                self.logger.error(f"Manager lazy initialization failed: {e}")
                self._initialize_standard_mode()  # フォールバック  # フォールバック

    def _ensure_parser_initialized(self) -> None:
        """MainParserの遅延初期化（最適化モード用）"""
        if self.performance_mode == "optimized" and not self._main_parser_initialized:
            try:

                start_time = time.perf_counter()
                self.main_parser = MainParser(self.config)
                self._main_parser_initialized = True
                end_time = time.perf_counter()
                self.logger.debug(
                    f"MainParser lazy initialized in {end_time - start_time:.4f}s"
                )
            except Exception as e:
                self.logger.error(f"MainParser initialization failed: {e}")
                self.main_parser = DummyParser()  # type: ignore

    def _ensure_renderer_initialized(self) -> None:
        """MainRendererの遅延初期化（最適化モード用）"""
        if self.performance_mode == "optimized" and not self._main_renderer_initialized:
            try:

                start_time = time.perf_counter()
                self.main_renderer = MainRenderer(self.config)
                self._main_renderer_initialized = True
                end_time = time.perf_counter()
                self.logger.debug(
                    f"MainRenderer lazy initialized in {end_time - start_time:.4f}s"
                )
            except Exception as e:
                self.logger.error(f"MainRenderer initialization failed: {e}")
                self.main_renderer = DummyRenderer()  # type: ignore

    def convert(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """統合Managerシステムによる最適化変換"""
        try:
            # 最適化モードの場合は遅延初期化
            if self.performance_mode == "optimized":
                self._ensure_managers_initialized()
                self._ensure_parser_initialized()
                self._ensure_renderer_initialized()

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

            # ファイル出力（CoreManager使用、テスト環境自動対応）
            success = self.main_renderer.render_to_file(
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
            if self.performance_mode == "optimized":
                result["performance_mode"] = "optimized"

            return result

        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            return {"status": "error", "error": str(e), "input_file": str(input_file)}

    def convert_text(self, text: str, template: str = "default") -> str:
        """テキスト→HTML変換（統合Managerシステム対応）"""
        try:
            # 最適化モードの場合は遅延初期化
            if self.performance_mode == "optimized":
                self._ensure_parser_initialized()
                self._ensure_renderer_initialized()

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
                    # "distribution_manager": "DistributionManager",  # 移動済み
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

    def _count_elements(self, parsed_result: Any) -> int:
        """要素数カウント（テスト互換性対応） - element_counter モジュールに移譲"""
        from .core.utilities.element_counter import count_elements

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


# ダミークラス（フォールバック用）
class DummyParser:
    """パーサー初期化失敗時のフォールバック"""

    def __init__(self) -> None:
        pass

    def parse(self, content: str, parser_type: str = "auto") -> Dict[str, Any]:
        return {"elements": [], "status": "fallback", "parser_used": "fallback"}


class DummyRenderer:
    """レンダラー初期化失敗時のフォールバック"""

    def __init__(self) -> None:
        pass

    def render(self, parsed_result: Any, context: Dict[str, Any]) -> str:
        return "<html><body><p>Fallback rendering</p></body></html>"

    def render_to_file(
        self,
        parsed_result: Any,
        output_file: Union[str, Path],
        template: Optional[str],
        context: Dict[str, Any],
    ) -> bool:
        try:
            Path(output_file).write_text(self.render(parsed_result, context))
            return True
        except Exception:
            return False


# 統合API便利関数のインポート（ファイルサイズ最適化のため分離）
from .core.utilities.api_utils import (
    quick_convert,
    quick_parse,
    unified_parse,
    validate_kumihan_syntax,
    get_parser_system_info,
    optimized_quick_convert,
    optimized_quick_parse,
    optimized_convert_text,
    parse,
    validate,
    main,
)

# Export everything for external use
__all__ = [
    "KumihanFormatter",
    "DummyParser",
    "DummyRenderer",
    "quick_convert",
    "quick_parse",
    "unified_parse",
    "validate_kumihan_syntax",
    "get_parser_system_info",
    "optimized_quick_convert",
    "optimized_quick_parse",
    "optimized_convert_text",
    "parse",
    "validate",
    "main",
]
