from typing import Any, Callable, Dict, List, Optional, Union

"""
MainParser - 統合パーサーシステム
全てのパーサーを統合管理する中央インターフェース
"""

import logging
from pathlib import Path

from kumihan_formatter.core.ast_nodes.node import Node
from typing import cast
from kumihan_formatter.parsers.unified_list_parser import UnifiedListParser
from kumihan_formatter.parsers.unified_keyword_parser import UnifiedKeywordParser
from kumihan_formatter.parsers.unified_markdown_parser import UnifiedMarkdownParser
from kumihan_formatter.core.parsing.core_marker_parser import CoreMarkerParser
from kumihan_formatter.core.processing.parsing_coordinator import ParsingCoordinator


class MainParser:
    """統合パーサーシステム - 全パーサーの中央管理

    Kumihan-Formatterの中核となる統合パーサーシステム。
    複数の専用パーサー（リスト、キーワード、マークダウン等）を統合し、
    自動パーサー選択、フォールバック機能、カスタムパーサー登録を提供。

    Attributes:
        logger (Logger): ロガーインスタンス
        config (Dict[str, Any]): パーサー設定辞書
        list_parser (UnifiedListParser): リスト専用パーサー
        keyword_parser (UnifiedKeywordParser): キーワード専用パーサー
        markdown_parser (UnifiedMarkdownParser): マークダウン専用パーサー
        marker_parser (CoreMarkerParser): マーカー専用パーサー
        coordinator (ParsingCoordinator): パーシング統合管理
        default_parser (str): デフォルトパーサー種類
        fallback_parser (str): フォールバックパーサー種類

    Examples:
        >>> parser = MainParser()
        >>> result = parser.parse("# 見出し #内容##")
        >>> print(result)

        >>> # カスタムパーサー登録
        >>> parser.register_custom_parser("custom", custom_func)
        >>> result = parser.parse(content, "custom")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """MainParser初期化

        統合パーサーシステムを初期化し、各種専用パーサーと
        統合管理機能を設定する。

        Args:
            config (Optional[Dict[str, Any]]): パーサー設定辞書。
                Noneの場合はデフォルト設定を使用。

        Config Options:
            - default_parser (str): デフォルトパーサー種類（デフォルト: "auto"）
            - fallback_parser (str): フォールバックパーサー種類（デフォルト: "simple"）
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
        """統合パーシング実行

        指定されたパーサー種類でコンテンツを解析し、ASTノードまたは
        解析結果辞書を返す。エラー時はフォールバック機能が動作。

        Args:
            content (Union[str, List[str]]): 解析対象コンテンツ。
                文字列または行のリスト形式
            parser_type (Optional[str]): パーサー種類。
                None=デフォルト使用。利用可能: "auto", "list", "keyword",
                "markdown", "simple", "marker", およびカスタム登録済み

        Returns:
            Optional[Union[Node, Dict[str, Any]]]: 解析結果。
                成功時: ASTノードまたは解析結果辞書
                エラー時: None

        Examples:
            >>> parser = MainParser()
            >>> result = parser.parse("# 見出し #内容##")
            >>> result = parser.parse(content, "keyword")
        """
        # 型安全: None は受け付けない（テスト互換のため明示的にTypeError）
        if content is None:
            raise TypeError("content must be str or List[str]")
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
            result_any = cast(
                Optional[Union[Node, Dict[str, Any]]], parser_func(content)
            )

            if result_any:
                self.logger.debug(f"パーシング成功: {selected_parser}")
                # 返り値型は Node | Dict[str, Any] | None を満たす想定
                return result_any
            else:
                # フォールバック試行
                if selected_parser != self.fallback_parser:
                    self.logger.info(
                        f"パーシング失敗、フォールバック試行: {self.fallback_parser}"
                    )
                    fallback_func = self._parsers[self.fallback_parser]
                    result_fb = cast(
                        Optional[Union[Node, Dict[str, Any]]], fallback_func(content)
                    )
                    return result_fb

                return None

        except Exception as e:
            self.logger.error(f"パーシング中にエラー: {e}")
            return self._emergency_fallback(content)

    def _auto_parse(
        self, content: Union[str, List[str]]
    ) -> Optional[Union[Node, Dict[str, Any]]]:
        """自動パーサー選択

        コンテンツを解析し、最適なパーサーを自動選択して実行。
        Kumihanブロック検出 → コーディネーター推奨 → 順次試行の順序で動作。

        Args:
            content (Union[str, List[str]]): 解析対象コンテンツ

        Returns:
            Optional[Union[Node, Dict[str, Any]]]: 解析結果
        """
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
        """順次パーサー試行

        利用可能な全パーサーを優先度順に試行し、最初に成功したものを返す。

        Args:
            content (Union[str, List[str]]): 解析対象コンテンツ

        Returns:
            Optional[Union[Node, Dict[str, Any]]]: 最初に成功した解析結果
        """
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
        """緊急時フォールバック

        全パーサーが失敗した際の最終的なフォールバック処理。
        SimpleKumihanParserで基本的な解析を試行。

        Args:
            content (Union[str, List[str]]): 解析対象コンテンツ

        Returns:
            Optional[Node]: 緊急フォールバック解析結果
        """
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
        """ファイルパーシング

        指定されたファイルを読み込み、パーシングを実行。
        結果はNode形式のみ返す（Dict結果は変換またはNone）。

        Args:
            file_path (Union[str, Path]): 解析対象ファイルのパス
            parser_type (Optional[str]): 使用するパーサー種類

        Returns:
            Optional[Node]: 解析結果のASTノード

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            UnicodeDecodeError: ファイルエンコーディングエラー
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
        """カスタムパーサー登録

        独自のパーサー関数を登録し、parse()メソッドで使用可能にする。

        Args:
            name (str): パーサー名（一意である必要あり）
            parser_func (Callable[..., Any]): パーサー関数。
                content引数を受け取り、NodeまたはDict[str, Any]を返す

        Returns:
            bool: 登録成功フラグ

        Examples:
            >>> def custom_parser(content):
            ...     return {"type": "custom", "content": content}
            >>> parser.register_custom_parser("custom", custom_parser)
            True
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
        """利用可能パーサー一覧取得

        Returns:
            List[str]: 登録済みパーサー名のリスト
        """
        return list(self._parsers.keys())

    def validate_content_for_parser(
        self, content: Union[str, List[str]], parser_type: str
    ) -> Dict[str, Any]:
        """パーサー適性検証

        指定されたコンテンツが特定のパーサーに適しているかを検証し、
        適性スコアと推奨事項を返す。

        Args:
            content (Union[str, List[str]]): 検証対象コンテンツ
            parser_type (str): 検証対象パーサー種類

        Returns:
            Dict[str, Any]: 検証結果辞書
                - suitable (bool): 適性判定
                - score (float): 適性スコア（0.0-1.0）
                - total_lines (int): 総行数
                - non_empty_lines (int): 非空行数
                - recommendation (str): 推奨パーサー
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
        """パーサー統計情報取得

        Returns:
            Dict[str, Any]: パーサーシステムの統計情報
        """
        return {
            "available_parsers": self.get_available_parsers(),
            "default_parser": self.default_parser,
            "fallback_parser": self.fallback_parser,
            "config": self.config,
        }

    def benchmark_parsers(
        self, sample_content: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """パーサーベンチマーク実行

        サンプルコンテンツを使用して各パーサーの性能を測定し、
        実行時間と成功率を比較する。

        Args:
            sample_content (Union[str, List[str]]): ベンチマーク用コンテンツ

        Returns:
            Dict[str, Any]: ベンチマーク結果
                各パーサーごとに success, execution_time, result_type を含む
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
