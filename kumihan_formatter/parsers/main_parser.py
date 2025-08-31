from typing import Any, Callable, Dict, List, Optional, Union

"""
MainParser - 統合パーサーシステム
全てのパーサーを統合管理する中央インターフェース
"""

import logging
from pathlib import Path

from kumihan_formatter.core.ast_nodes.node import Node
from kumihan_formatter.parsers.unified_list_parser import UnifiedListParser
from kumihan_formatter.parsers.unified_keyword_parser import UnifiedKeywordParser
from kumihan_formatter.parsers.unified_markdown_parser import UnifiedMarkdownParser
from kumihan_formatter.core.parsing.core_marker_parser import CoreMarkerParser
from kumihan_formatter.core.processing.parsing_coordinator import ParsingCoordinator


class MainParser:
    """統合パーサーシステム - 全パーサーの中央管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        MainParser初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 統合パーサー群初期化
        self.list_parser = UnifiedListParser()
        self.keyword_parser = UnifiedKeywordParser()
        self.markdown_parser = UnifiedMarkdownParser()
        self.marker_parser = CoreMarkerParser()

        # パーシング統合管理
        self.coordinator = ParsingCoordinator(config)

        # パーサー登録
        self._parsers: Dict[str, Callable[..., Any]] = {
            "list": self.list_parser.parse,
            "keyword": self.keyword_parser.parse,
            "markdown": self.markdown_parser.parse,
            "simple": self.marker_parser.parse_simple_kumihan,
            "marker": self.marker_parser.parse,
            "auto": self._auto_parse,
        }

        # デフォルト設定
        self.default_parser = self.config.get("default_parser", "auto")
        self.fallback_parser = self.config.get("fallback_parser", "simple")

    def parse(
        self, content: Union[str, List[str]], parser_type: Optional[str] = None
    ) -> Optional[Union[Node, Dict[str, Any]]]:
        """
        統合パーシング実行

        Args:
            content: 解析対象コンテンツ
            parser_type: パーサー種類（None=デフォルト使用）

        Returns:
            解析結果AST、エラー時はNone
        """
        try:
            # パーサー種類決定
            selected_parser = parser_type or self.default_parser

            if selected_parser not in self._parsers:
                self.logger.warning(
                    f"未知のパーサー種類: {selected_parser}、フォールバック使用"
                )
                selected_parser = self.fallback_parser

            # パーシング実行
            parser_func = self._parsers[selected_parser]
            result = parser_func(content)

            if result:
                self.logger.debug(f"パーシング成功: {selected_parser}")
                # 明示的な型キャスト
                return result  # type: ignore[no-any-return]
            else:
                # フォールバック試行
                if selected_parser != self.fallback_parser:
                    self.logger.info(
                        f"パーシング失敗、フォールバック試行: {self.fallback_parser}"
                    )
                    fallback_func = self._parsers[self.fallback_parser]
                    # 明示的な型キャスト
                    return fallback_func(content)  # type: ignore[no-any-return]

                return None

        except Exception as e:
            self.logger.error(f"パーシング中にエラー: {e}")
            return self._emergency_fallback(content)

    def _auto_parse(
        self, content: Union[str, List[str]]
    ) -> Optional[Union[Node, Dict[str, Any]]]:
        """自動パーサー選択"""
        try:
            # Kumihanブロックの存在チェック（優先）
            content_str = content if isinstance(content, str) else "\n".join(content)
            if "##" in content_str and "#" in content_str:
                # Kumihanブロック記法を検出した場合は直接SimpleKumihanParserを試行
                try:
                    result = self.marker_parser.parse_simple_kumihan(content_str)
                    if result and result.get("elements"):
                        # Kumihanブロックが含まれている場合は辞書結果を返す
                        has_kumihan_blocks = any(
                            elem.get("type") == "kumihan_block"
                            for elem in result.get("elements", [])
                        )
                        if has_kumihan_blocks:
                            self.logger.info(
                                "Auto-parse: SimpleKumihanParser成功 - Kumihanブロックを検出"
                            )
                            return result
                except Exception as e:
                    self.logger.debug(f"Auto-parse SimpleKumihanParser試行失敗: {e}")

            # コーディネーターによる自動選択（Kumihanブロックが検出されなかった場合）
            coordinator_result = self.coordinator.parse_document(content)
            if (
                coordinator_result
                and isinstance(coordinator_result, dict)
                and "parser_type" in coordinator_result
            ):
                recommended_type = coordinator_result["parser_type"]

                # 推奨パーサーで実行
                if recommended_type in self._parsers:
                    parser_func = self._parsers[recommended_type]
                    return parser_func(content)  # type: ignore

            # 順次試行戦略
            return self._sequential_try_parsing(content)

        except Exception as e:
            self.logger.error(f"自動パーシング中にエラー: {e}")
            return self._sequential_try_parsing(content)

    def _sequential_try_parsing(
        self, content: Union[str, List[str]]
    ) -> Optional[Union[Node, Dict[str, Any]]]:
        """順次パーサー試行"""
        # Kumihanブロックの存在チェック
        content_str = content if isinstance(content, str) else "\n".join(content)
        if "##" in content_str and "#" in content_str:
            # Kumihanブロック記法を検出した場合は直接SimpleKumihanParserを試行
            try:
                result = self.marker_parser.parse_simple_kumihan(content_str)
                if result and result.get("elements"):
                    # Kumihanブロックが含まれている場合は辞書結果を返す
                    has_kumihan_blocks = any(
                        elem.get("type") == "kumihan_block"
                        for elem in result.get("elements", [])
                    )
                    if has_kumihan_blocks:
                        self.logger.info(
                            "SimpleKumihanParser成功: Kumihanブロックを検出"
                        )
                        return result
            except Exception as e:
                self.logger.debug(f"SimpleKumihanParser試行失敗: {e}")

        # 通常の順次試行（Kumihanブロックが検出されなかった場合）
        try_order = ["keyword", "list", "markdown", "marker", "simple"]

        for parser_type in try_order:
            try:
                parser_func = self._parsers[parser_type]
                result = parser_func(content)
                if result:
                    self.logger.info(f"順次試行成功: {parser_type}")
                    return result  # type: ignore
            except Exception as e:
                self.logger.debug(f"パーサー試行失敗 {parser_type}: {e}")
                continue

        return None

    def _emergency_fallback(self, content: Union[str, List[str]]) -> Optional[Node]:
        """緊急時フォールバック"""
        try:
            self.logger.warning("緊急時フォールバック実行")
            content_str = content if isinstance(content, str) else "\n".join(content)
            result = self.marker_parser.parse_simple_kumihan(content_str)

            # Dict結果からNodeを抽出（parse_simple_kumihanはDict[str, Any]を返す）
            if result and isinstance(result, dict):
                elements = result.get("elements", [])
                if elements and len(elements) > 0:
                    # 最初の要素をNodeとして返す（必要に応じて統合も可能）
                    first_element = elements[0]
                    if hasattr(first_element, "tag"):  # Node型の場合
                        return first_element  # type: ignore

            return None
        except Exception as e:
            self.logger.error(f"緊急時フォールバックも失敗: {e}")
            return None

    def parse_file(
        self, file_path: Union[str, Path], parser_type: Optional[str] = None
    ) -> Optional[Node]:
        """
        ファイルパーシング

        Args:
            file_path: ファイルパス
            parser_type: パーサー種類

        Returns:
            解析結果AST（Nodeのみ）
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            result = self.parse(content, parser_type)

            # Dictの場合はNodeに変換またはNoneを返す
            if isinstance(result, dict):
                # 辞書結果の場合は最初のNodeを抽出
                elements = result.get("elements", [])
                if elements and len(elements) > 0:
                    first_element = elements[0]
                    if hasattr(first_element, "tag"):  # Node型チェック
                        return first_element  # type: ignore
                return None

            return result  # すでにNodeまたはNone

        except Exception as e:
            self.logger.error(f"ファイルパーシング中にエラー {file_path}: {e}")
            return None

    def register_custom_parser(
        self, name: str, parser_func: Callable[..., Any]
    ) -> bool:
        """
        カスタムパーサー登録

        Args:
            name: パーサー名
            parser_func: パーサー関数

        Returns:
            登録成功フラグ
        """
        try:
            if name in self._parsers:
                self.logger.warning(f"パーサー名が重複、上書きします: {name}")

            self._parsers[name] = parser_func
            self.logger.info(f"カスタムパーサー登録完了: {name}")
            return True

        except Exception as e:
            self.logger.error(f"カスタムパーサー登録中にエラー: {name}, {e}")
            return False

    def get_available_parsers(self) -> List[str]:
        """利用可能パーサー一覧取得"""
        return list(self._parsers.keys())

    def validate_content_for_parser(
        self, content: Union[str, List[str]], parser_type: str
    ) -> Dict[str, Any]:
        """
        パーサー適性検証

        Args:
            content: コンテンツ
            parser_type: パーサー種類

        Returns:
            検証結果
        """
        try:
            if parser_type not in self._parsers:
                return {"suitable": False, "reason": f"未知のパーサー: {parser_type}"}

            # 基本適性チェック
            if isinstance(content, str):
                lines = content.split("\n")
            else:
                lines = content

            total_lines = len(lines)
            non_empty_lines = sum(1 for line in lines if line.strip())

            suitability_score = 0.5  # ベース適性

            # パーサー別適性判定
            if parser_type == "list":
                list_indicators = sum(
                    1 for line in lines if line.strip().startswith(("-", "*", "+"))
                )
                if list_indicators > total_lines * 0.3:
                    suitability_score += 0.3

            elif parser_type == "keyword":
                keyword_indicators = sum(
                    1 for line in lines if "#" in line and "##" in line
                )
                if keyword_indicators > 0:
                    suitability_score += 0.4

            elif parser_type == "markdown":
                md_indicators = sum(1 for line in lines if line.strip().startswith("#"))
                if md_indicators > 0:
                    suitability_score += 0.3

            suitable = suitability_score >= 0.6

            return {
                "suitable": suitable,
                "score": suitability_score,
                "total_lines": total_lines,
                "non_empty_lines": non_empty_lines,
                "recommendation": parser_type if suitable else "auto",
            }

        except Exception as e:
            self.logger.error(f"パーサー適性検証中にエラー: {e}")
            return {"suitable": False, "reason": f"検証エラー: {e}"}

    def get_parser_statistics(self) -> Dict[str, Any]:
        """パーサー統計情報取得"""
        return {
            "available_parsers": self.get_available_parsers(),
            "default_parser": self.default_parser,
            "fallback_parser": self.fallback_parser,
            "config": self.config,
        }

    def benchmark_parsers(
        self, sample_content: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """
        パーサーベンチマーク実行

        Args:
            sample_content: ベンチマーク用コンテンツ

        Returns:
            ベンチマーク結果
        """
        import time

        results = {}

        for parser_name, parser_func in self._parsers.items():
            if parser_name == "auto":  # 自動選択は除外
                continue

            try:
                start_time = time.time()
                result = parser_func(sample_content)
                end_time = time.time()

                results[parser_name] = {
                    "success": result is not None,
                    "execution_time": end_time - start_time,
                    "result_type": type(result).__name__ if result else None,
                }

            except Exception as e:
                results[parser_name] = {
                    "success": False,
                    "execution_time": 0.0,
                    "error": str(e),
                }

        return results
