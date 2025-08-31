from typing import Any, Dict, List, Optional, Union, Callable
import logging
import time
import inspect
from functools import wraps

"""
ProcessingManager - 解析・最適化処理統合管理クラス (Issue #1253対応)
ParsingManager + OptimizationManager の機能を統合
"""

# パーシング関連インポート
from kumihan_formatter.core.processing.parsing_coordinator import ParsingCoordinator
from kumihan_formatter.core.validation.validation_reporter import ValidationReporter
from kumihan_formatter.parsers.unified_list_parser import UnifiedListParser
from kumihan_formatter.parsers.unified_keyword_parser import UnifiedKeywordParser
from kumihan_formatter.parsers.unified_markdown_parser import UnifiedMarkdownParser
from kumihan_formatter.core.ast_nodes.node import Node


class PerformanceMetrics:
    """パフォーマンス測定メトリクス（OptimizationManager統合）"""

    def __init__(
        self,
        operation_name: str,
        execution_time: float,
        memory_usage: int,
        input_size: int,
        optimization_applied: bool,
    ):
        self.operation_name = operation_name
        self.execution_time = execution_time
        self.memory_usage = memory_usage
        self.input_size = input_size
        self.optimization_applied = optimization_applied


class ProcessingManager:
    """解析・最適化処理統合管理クラス - パーシング・バリデーション・パフォーマンス最適化の統合API (Issue #1253対応)"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        ProcessingManager初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # パーシング機能初期化（旧ParsingManager）
        self.coordinator = ParsingCoordinator(config)
        self.reporter = ValidationReporter()

        # 統合パーサー初期化
        self.list_parser = UnifiedListParser()
        self.keyword_parser = UnifiedKeywordParser()
        self.markdown_parser = UnifiedMarkdownParser()

        # 検証設定
        self.strict_mode = self.config.get("strict_validation", False)
        self.error_threshold = self.config.get("error_threshold", 10)

        # 最適化設定（旧OptimizationManager）
        self.enable_caching = self.config.get("enable_caching", True)
        self.enable_parallel = self.config.get("enable_parallel", True)
        self.memory_limit = self.config.get("memory_limit_mb", 512)
        self.performance_monitoring = self.config.get("performance_monitoring", True)

        # パフォーマンス測定
        self._metrics: List[PerformanceMetrics] = []
        self._operation_cache: Dict[str, Any] = {}

    # ========== パーシング機能（旧ParsingManager） ==========

    def parse(
        self, content: Union[str, List[str]], parser_type: str = "auto"
    ) -> Optional[Node]:
        """
        コンテンツを解析してASTノードを生成

        Args:
            content: 解析対象コンテンツ
            parser_type: パーサー種類（"auto", "list", "keyword", "markdown"）

        Returns:
            解析結果のASTノード、エラー時はNone
        """
        try:
            # 自動選択の場合はコーディネーターを使用
            if parser_type == "auto":
                result = self.coordinator.parse_document(content)
                if result:
                    selected_type = result["parser_type"]
                    return self._parse_with_type(content, selected_type)
                return None

            # 指定された種類でパーサーを実行
            return self._parse_with_type(content, parser_type)

        except Exception as e:
            self.logger.error(f"パース処理中にエラーが発生: {e}")
            return None

    def _parse_with_type(
        self, content: Union[str, List[str]], parser_type: str
    ) -> Optional[Node]:
        """指定された種類のパーサーで解析実行"""
        try:
            # コンテンツを文字列に正規化
            content_str = content if isinstance(content, str) else "\n".join(content)

            if parser_type == "list":
                return self.list_parser.parse(content_str)
            elif parser_type == "keyword":
                return self.keyword_parser.parse(content_str)
            elif parser_type == "markdown":
                return self.markdown_parser.parse(content_str)
            elif parser_type == "kumihan":
                # kumihanパーサーはMarkdownParserでサポート
                return self.markdown_parser.parse(content_str)
            else:
                self.logger.warning(f"未知のパーサー種類: {parser_type}")
                return None

        except Exception as e:
            self.logger.error(f"{parser_type}パーサー実行中にエラー: {e}")
            return None

    def parse_file(self, file_path: str, parser_type: str = "auto") -> Optional[Node]:
        """
        ファイルを読み込んで解析

        Args:
            file_path: 解析対象ファイルパス
            parser_type: パーサー種類

        Returns:
            解析結果のASTノード、エラー時はNone
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse(content, parser_type)

        except Exception as e:
            self.logger.error(f"ファイル解析中にエラー: {file_path}, {e}")
            return None

    # ========== 最適化パーシング（OptimizationManager統合） ==========

    def optimize_parsing(
        self, content: Union[str, List[str]], parser_func: Callable[[str], Any]
    ) -> Any:
        """
        パーシング処理の最適化

        Args:
            content: 解析対象コンテンツ
            parser_func: パーサー関数

        Returns:
            最適化された解析結果
        """
        try:
            start_time = time.time()

            # コンテンツサイズチェック
            if isinstance(content, str):
                input_size = len(content)
                content_hash = hash(content)
            else:
                input_size = sum(len(line) for line in content)
                content_hash = hash(str(content))

            # キャッシュチェック
            cache_key = f"parse_{content_hash}_{parser_func.__name__}"
            if self.enable_caching and cache_key in self._operation_cache:
                self.logger.debug(f"キャッシュヒット: {parser_func.__name__}")
                cached_result = self._operation_cache[cache_key]

                # メトリクス記録
                execution_time = time.time() - start_time
                self._record_metrics(
                    "parse_cached", execution_time, 0, input_size, True
                )

                return cached_result

            # 最適化されたパーシング実行
            content_str = content if isinstance(content, str) else "\n".join(content)
            if input_size > 50000:  # 大きなコンテンツの場合
                result = self._optimize_large_parsing(content_str, parser_func)
            else:
                result = parser_func(content_str)

            # キャッシュ保存
            if self.enable_caching:
                self._operation_cache[cache_key] = result

            # メトリクス記録
            execution_time = time.time() - start_time
            self._record_metrics(
                parser_func.__name__,
                execution_time,
                self._estimate_memory_usage(result),
                input_size,
                True,
            )

            return result

        except Exception as e:
            self.logger.error(f"パーシング最適化中にエラー: {e}")
            # フォールバック: 通常のパーシング
            content_str = content if isinstance(content, str) else "\n".join(content)
            return parser_func(content_str)

    def _optimize_large_parsing(
        self, content: Union[str, List[str]], parser_func: Callable[[str], Any]
    ) -> Any:
        """大きなコンテンツの最適化パーシング"""
        try:
            if isinstance(content, str):
                lines = content.split("\n")
            else:
                lines = content

            # チャンク分割による並列処理（簡易版）
            chunk_size = self.config.get("large_parse_chunk_size", 1000)
            chunks = [
                lines[i : i + chunk_size] for i in range(0, len(lines), chunk_size)
            ]

            results = []
            for chunk in chunks:
                chunk_str = "\n".join(chunk)
                chunk_result = parser_func(chunk_str)
                if chunk_result:
                    results.append(chunk_result)

            # 結果統合（簡易版）
            if results:
                return results[0]  # 最初の有効な結果を使用

            return None

        except Exception as e:
            self.logger.warning(f"大容量パーシング最適化に失敗、フォールバック: {e}")
            content_str = content if isinstance(content, str) else "\n".join(content)
            return parser_func(content_str)

    # ========== バリデーション機能（旧ParsingManager） ==========

    def validate_node(
        self, node: Node, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        単一ノードのバリデーション

        Args:
            node: 検証対象ノード
            context: バリデーションコンテキスト

        Returns:
            バリデーション結果辞書
        """
        try:
            context = context or {}
            result: Dict[str, Any] = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "node_info": {
                    "type": getattr(node, "tag", "unknown"),
                    "content": getattr(node, "content", "")[:100],  # 最初の100文字
                },
            }
            errors: List[str] = result["errors"]
            warnings: List[str] = result["warnings"]

            # 基本構造検証
            self._validate_node_structure(node, result)

            # コンテンツ検証
            self._validate_node_content(node, result, context)

            # 最終判定
            result["valid"] = len(errors) == 0

            return result

        except Exception as e:
            self.logger.error(f"ノードバリデーション中にエラー: {e}")
            return {
                "valid": False,
                "errors": [f"バリデーション処理エラー: {e}"],
                "warnings": [],
                "node_info": {"type": "error"},
            }

    def validate_nodes(
        self, nodes: List[Node], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        複数ノードのバリデーション

        Args:
            nodes: 検証対象ノードリスト
            context: バリデーションコンテキスト

        Returns:
            統合バリデーション結果
        """
        try:
            overall_result: Dict[str, Any] = {
                "valid": True,
                "total_nodes": len(nodes),
                "valid_nodes": 0,
                "errors": [],
                "warnings": [],
                "node_results": [],
            }

            for i, node in enumerate(nodes):
                node_result = self.validate_node(node, context)
                overall_result["node_results"].append(node_result)

                if node_result["valid"]:
                    overall_result["valid_nodes"] += 1
                else:
                    node_errors = node_result.get("errors", [])
                    overall_result["errors"].extend(
                        [f"ノード{i}: {error}" for error in node_errors]
                    )

                node_warnings = node_result.get("warnings", [])
                overall_result["warnings"].extend(
                    [f"ノード{i}: {warning}" for warning in node_warnings]
                )

            # 全体の妥当性判定
            error_count = len(overall_result["errors"])
            overall_result["valid"] = (
                error_count == 0 and error_count <= self.error_threshold
            )

            return overall_result

        except Exception as e:
            self.logger.error(f"ノードリストバリデーション中にエラー: {e}")
            return {
                "valid": False,
                "errors": [f"バリデーション処理エラー: {e}"],
                "warnings": [],
                "total_nodes": len(nodes) if nodes else 0,
            }

    def validate_syntax(self, content: Union[str, List[str]]) -> Dict[str, Any]:
        """
        構文バリデーション

        Args:
            content: 検証対象コンテンツ

        Returns:
            構文検証結果
        """
        try:
            if isinstance(content, str):
                lines = content.split("\n")
            else:
                lines = content

            result: Dict[str, Any] = {
                "valid": True,
                "syntax_errors": [],
                "syntax_warnings": [],
                "line_count": len(lines),
            }

            # 基本的な構文チェック
            for i, line in enumerate(lines, 1):
                self._check_line_syntax(line, i, result)

            syntax_errors: List[str] = result["syntax_errors"]
            result["valid"] = len(syntax_errors) == 0
            return result

        except Exception as e:
            self.logger.error(f"構文バリデーション中にエラー: {e}")
            return {
                "valid": False,
                "syntax_errors": [f"構文検証エラー: {e}"],
                "syntax_warnings": [],
            }

    # ========== 内部ヘルパーメソッド ==========

    def _validate_node_structure(self, node: Node, result: Dict[str, Any]) -> None:
        """ノード構造の基本検証"""
        # 必須属性の確認
        if not hasattr(node, "tag"):
            result["errors"].append("ノードにtagが設定されていません")

        # 無効なタグ名の検証
        tag = getattr(node, "tag", "")
        if tag and not tag.replace("_", "").replace("-", "").isalnum():
            result["warnings"].append(f"無効な可能性のあるタグ名: {tag}")

    def _validate_node_content(
        self, node: Node, result: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """ノードコンテンツの検証"""
        content = getattr(node, "content", "")

        if isinstance(content, str):
            # 空コンテンツの警告
            if not content.strip():
                result["warnings"].append("コンテンツが空です")

            # 長すぎるコンテンツの警告
            if len(content) > 10000:
                result["warnings"].append(
                    f"コンテンツが非常に長いです: {len(content)}文字"
                )

        # 子ノードの検証
        children = getattr(node, "children", [])
        if children:
            for i, child in enumerate(children):
                child_result = self.validate_node(child, context)
                if not child_result["valid"]:
                    result["warnings"].append(f"子ノード{i}に問題があります")

    def _check_line_syntax(
        self, line: str, line_num: int, result: Dict[str, Any]
    ) -> None:
        """行レベルの構文チェック"""
        import re

        # ブロック記法の基本チェック
        if "#" in line and "##" not in line:
            # 開始タグの妥当性
            if re.match(r"^[#＃]\s*[^#＃\s]+\s*[#＃]$", line.strip()):
                pass  # 正常な開始タグ
            elif re.search(r"[#＃][^#＃]*[#＃]", line):
                pass  # インライン記法
            elif line.strip().startswith("#") and not line.strip().startswith("##"):
                # Markdown形式との混在チェック
                if not re.match(r"^#+\s+", line.strip()):
                    result["syntax_warnings"].append(
                        f"行{line_num}: 記法が曖昧です - {line.strip()[:50]}"
                    )

    # ========== パフォーマンス監視（OptimizationManager統合） ==========

    def performance_monitor(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        関数実行パフォーマンス監視デコレーター

        Args:
            func: 監視対象関数

        Returns:
            監視付き関数
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self.performance_monitoring:
                return func(*args, **kwargs)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # メトリクス記録
                self._record_metrics(
                    func.__name__,
                    execution_time,
                    self._estimate_memory_usage(result),
                    self._estimate_input_size(args, kwargs),
                    False,
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                self.logger.error(f"監視対象関数でエラー ({func.__name__}): {e}")
                self._record_metrics(func.__name__, execution_time, 0, 0, False)
                raise

        return wrapper

    def _record_metrics(
        self,
        operation_name: str,
        execution_time: float,
        memory_usage: int,
        input_size: int,
        optimization_applied: bool,
    ) -> None:
        """パフォーマンスメトリクスの記録"""
        metric = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            memory_usage=memory_usage,
            input_size=input_size,
            optimization_applied=optimization_applied,
        )

        self._metrics.append(metric)

        # メトリクス数制限（メモリ節約）
        if len(self._metrics) > 1000:
            self._metrics = self._metrics[-500:]  # 最新500件を保持

    # ========== メモリ最適化 ==========

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        メモリ使用量最適化

        Returns:
            最適化結果
        """
        try:
            initial_cache_size = len(self._operation_cache)

            # 古いキャッシュエントリの削除（簡易版LRU）
            if len(self._operation_cache) > 100:
                # 最近使用されたもの以外を削除
                cache_items = list(self._operation_cache.items())
                recent_items = cache_items[-50:]  # 最新50項目を保持
                self._operation_cache = dict(recent_items)

            optimized_size = len(self._operation_cache)

            return {
                "cache_cleaned": True,
                "initial_cache_size": initial_cache_size,
                "optimized_cache_size": optimized_size,
                "memory_freed": initial_cache_size - optimized_size,
            }

        except Exception as e:
            self.logger.error(f"メモリ最適化中にエラー: {e}")
            return {"cache_cleaned": False, "error": str(e)}

    # ========== 統合API ==========

    def parse_and_validate(
        self, content: Union[str, List[str]], parser_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        解析と検証を一括実行

        Args:
            content: 解析対象コンテンツ
            parser_type: パーサー種類

        Returns:
            解析・検証統合結果
        """
        try:
            # 解析実行
            parsed_node = self.parse(content, parser_type)

            # 構文検証
            syntax_result = self.validate_syntax(content)

            # ノード検証
            node_result = None
            if parsed_node:
                node_result = self.validate_node(parsed_node)

            return {
                "parsing_success": parsed_node is not None,
                "parsed_node": parsed_node,
                "syntax_validation": syntax_result,
                "node_validation": node_result,
                "overall_valid": (
                    parsed_node is not None
                    and syntax_result["valid"]
                    and (node_result["valid"] if node_result else False)
                ),
            }

        except Exception as e:
            self.logger.error(f"統合解析・検証中にエラー: {e}")
            return {
                "parsing_success": False,
                "syntax_validation": {"valid": False, "errors": [str(e)]},
                "node_validation": None,
                "overall_valid": False,
            }

    # ========== 情報取得 ==========

    def get_available_parsers(self) -> List[str]:
        """利用可能なパーサー一覧を取得"""
        return ["auto", "list", "keyword", "markdown"]

    def get_parsing_statistics(self) -> Dict[str, Any]:
        """パーシング統計情報を取得"""
        coordinator_stats = self.coordinator.get_parsing_statistics()
        return {
            "coordinator": coordinator_stats,
            "available_parsers": self.get_available_parsers(),
            "validation_config": {
                "strict_mode": self.strict_mode,
                "error_threshold": self.error_threshold,
            },
            "config": self.config,
        }

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """最適化統計情報を取得"""
        if not self._metrics:
            return {"total_operations": 0, "optimization_rate": 0.0}

        total_ops = len(self._metrics)
        optimized_ops = sum(1 for m in self._metrics if m.optimization_applied)

        avg_execution_time = sum(m.execution_time for m in self._metrics) / total_ops

        return {
            "total_operations": total_ops,
            "optimized_operations": optimized_ops,
            "optimization_rate": optimized_ops / total_ops,
            "avg_execution_time": avg_execution_time,
            "cache_size": len(self._operation_cache),
            "config": {
                "caching_enabled": self.enable_caching,
                "parallel_enabled": self.enable_parallel,
                "memory_limit_mb": self.memory_limit,
            },
        }

    def clear_optimization_cache(self) -> None:
        """最適化キャッシュをクリア"""
        self._operation_cache.clear()
        self._metrics.clear()
        self.logger.info("最適化キャッシュをクリアしました")

    def _estimate_memory_usage(self, obj: Any) -> int:
        """オブジェクトのメモリ使用量推定（簡易版）"""
        try:
            import sys

            return sys.getsizeof(obj)
        except Exception:
            return 0

    def _estimate_input_size(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> int:
        """入力サイズの推定"""
        try:
            total_size = 0
            for arg in args:
                if isinstance(arg, str):
                    total_size += len(arg)
                elif isinstance(arg, list) and arg and isinstance(arg[0], str):
                    total_size += sum(len(line) for line in arg)
            return total_size
        except Exception:
            return 0
