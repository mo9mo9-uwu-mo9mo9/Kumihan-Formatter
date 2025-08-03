"""
構文解析コーディネーター

複数のパーサーを統括し、最適な解析戦略を選択・実行する
Issue #616対応 - CI/CDテスト修正用の基本実装
"""

from typing import Any, Dict, List, Optional, Union

from kumihan_formatter.core.utilities.logger import get_logger


class ParsingCoordinator:
    """構文解析コーディネーター - 複数パーサーの統括管理

    文書内容を解析し、最適なパーサーを自動選択して処理を実行する。

    使用例:
        >>> coordinator = ParsingCoordinator()
        >>> content = ["# Markdownタイトル", "**太字**テキスト"]
        >>> result = coordinator.parse_document(content)
        >>> result["parser_type"]  # "markdown"
        >>>
        >>> block_content = ["#重要#", "重要な内容", "##"]
        >>> result = coordinator.parse_document(block_content)
        >>> result["parser_type"]  # "block"
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 設定オプション辞書
        """
        self.logger = get_logger(__name__)
        self.config = config or {}

        # パーサー優先順位設定
        self.parser_priorities = {
            "block": 1,  # ブロック要素
            "keyword": 2,  # キーワード記法
            "list": 3,  # リスト構造
            "markdown": 4,  # Markdown要素
        }

        # 結果キャッシュ（将来の最適化用）
        # 現在は基本実装のため未使用だが、パフォーマンス改善時に活用予定
        self._result_cache: Dict[str, Any] = {}

    def parse_document(
        self, content: Union[List[str], str]
    ) -> Optional[Dict[str, Any]]:
        """
        文書を解析し、最適なパーサーで処理する

        Args:
            content: 解析対象の文書内容（行リストまたは文字列）

        Returns:
            解析結果辞書、エラー時はNone
        """
        try:
            # 文字列の場合は行リストに変換
            if isinstance(content, str):
                content_lines = content.split("\n")
            else:
                content_lines = content

            # 空の場合は基本結果を返す
            if not content_lines:
                return {"parser_type": "empty", "content": [], "metadata": {}}

            # 内容解析と最適パーサー決定
            optimal_parser = self._determine_optimal_parser(content_lines)

            # 基本解析結果を生成
            result = {
                "parser_type": optimal_parser,
                "primary_parser": optimal_parser,
                "content": content_lines,
                "metadata": {
                    "line_count": len(content_lines),
                    "strategy": "coordinator_basic",
                },
            }

            self.logger.debug(f"文書解析完了: {optimal_parser}パーサーを使用")
            return result

        except Exception as e:
            self.logger.error(f"文書解析エラー: {e}")
            return None

    def _determine_optimal_parser(self, content_lines: List[str]) -> str:
        """
        最適なパーサーを決定する

        Args:
            content_lines: 文書の行リスト

        Returns:
            選択されたパーサー名
        """
        parser_scores = {"block": 0, "keyword": 0, "list": 0, "markdown": 0}

        for line in content_lines:
            line_content = line.strip()
            self._analyze_line_for_parser_scoring(line_content, parser_scores)

        # 最高スコアのパーサーを選択
        optimal_parser_info = max(parser_scores.items(), key=lambda x: x[1])

        # スコアが同じ場合は優先順位で決定
        if optimal_parser_info[1] == 0:
            return "coordinator"  # どの記法も検出されない場合

        return optimal_parser_info[0]

    def _analyze_line_for_parser_scoring(
        self, line_content: str, parser_scores: Dict[str, int]
    ) -> None:
        """
        行の内容を解析してパーサースコアを更新する

        Args:
            line_content: 解析対象の行内容（トリム済み）
            parser_scores: 更新対象のパーサースコア辞書
        """
        import re

        # 新記法 # リスト # の検出
        if re.match(r"^[#＃]\s*リスト\s*[#＃]", line_content):
            parser_scores["list"] += 5  # 高スコア

        # 新記法インライン形式の検出 # キーワード # 内容
        if re.search(r"[#＃][^#＃]+[#＃]", line_content):
            parser_scores["keyword"] += 3

        # 新記法ブロック開始の検出 # キーワード #
        if re.match(r"^[#＃]\s*[^#＃\s]+\s*[#＃]$", line_content):
            parser_scores["block"] += 4

        # ブロック終了マーカーの検出
        if line_content in ["##", "＃＃"]:
            parser_scores["block"] += 2

        # Markdown記法の検出（互換性維持）
        if line_content.startswith("#") and not re.match(
            r"^[#＃]\s*[^#＃\s]+\s*[#＃]", line_content
        ):
            parser_scores["markdown"] += 2
        elif "**" in line_content or "*" in line_content:
            parser_scores["markdown"] += 1
        elif line_content.startswith("```"):
            parser_scores["markdown"] += 3

    def get_parsing_statistics(self) -> Dict[str, Any]:
        """
        解析統計情報を取得

        Returns:
            統計情報辞書
        """
        return {
            "cache_size": len(self._result_cache),
            "parser_priorities": self.parser_priorities,
            "config": self.config,
        }

    def clear_cache(self) -> None:
        """結果キャッシュをクリア"""
        self._result_cache.clear()
        self.logger.debug("解析結果キャッシュをクリアしました")
