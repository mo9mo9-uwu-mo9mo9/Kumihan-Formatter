"""Inline Marker Processor - インライン記法処理専用モジュール

core_marker_parser.py分割により抽出 (Phase3最適化)
インラインマーカー処理関連の機能をすべて統合
"""

import re
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Match
import logging

from ..ast_nodes import Node, create_node, error_node

if TYPE_CHECKING:
    from .protocols import ParseResult


class InlineMarkerProcessor:
    """インラインマーカー処理クラス - インライン記法の解析と処理"""

    def __init__(self) -> None:
        """インラインマーカープロセッサーを初期化"""
        self.logger = logging.getLogger(__name__)

        # インライン記法パターン
        self.inline_patterns = {
            "strong": re.compile(r"\*\*(.*?)\*\*"),
            "emphasis": re.compile(r"\*(.*?)\*"),
            "code": re.compile(r"`(.*?)`"),
            "link": re.compile(r"\[([^\]]*)\]\(([^)]+)\)"),
            "marker": re.compile(r"#([^#\s]+)#([^#]*?)##"),
        }

    def process_inline_markers(self, text: str) -> List[Node]:
        """インラインマーカーを処理してノードリストを生成

        Args:
            text: 処理対象テキスト

        Returns:
            処理結果ノードリスト
        """
        try:
            if not text or not text.strip():
                return []

            nodes = []
            remaining_text = text

            # 各パターンを順次処理
            for marker_type, pattern in self.inline_patterns.items():
                matches = list(pattern.finditer(remaining_text))

                for match in matches:
                    node = self._create_inline_node(marker_type, match)
                    if node:
                        nodes.append(node)

            # 残りのテキストをプレーンテキストノードとして追加
            if remaining_text.strip():
                text_node = create_node("text", content=remaining_text.strip())
                nodes.append(text_node)

            return nodes

        except Exception as e:
            self.logger.error(f"インラインマーカー処理中にエラー: {e}")
            return [error_node(f"インライン処理エラー: {e}")]

    def _create_inline_node(
        self, marker_type: str, match: Match[str]
    ) -> Optional[Node]:
        """マッチした内容からインラインノードを作成

        Args:
            marker_type: マーカータイプ
            match: 正規表現マッチオブジェクト

        Returns:
            作成されたノード
        """
        try:
            if marker_type == "strong":
                return create_node("strong", content=match.group(1))
            elif marker_type == "emphasis":
                return create_node("em", content=match.group(1))
            elif marker_type == "code":
                return create_node("code", content=match.group(1))
            elif marker_type == "link":
                text, url = match.groups()
                return create_node("a", content=text, attributes={"href": url})
            elif marker_type == "marker":
                marker_name, content = match.groups()
                return create_node(f"marker-{marker_name}", content=content)
            else:
                return create_node("span", content=match.group(0))

        except Exception as e:
            self.logger.error(f"インラインノード作成中にエラー: {e}")
            return error_node(f"ノード作成エラー: {e}")

    def extract_inline_markers(self, text: str) -> List[Dict[str, Any]]:
        """テキストからインラインマーカーを抽出

        Args:
            text: 解析対象テキスト

        Returns:
            抽出されたマーカー情報のリスト
        """
        try:
            markers: List[Dict[str, Any]] = []

            for marker_type, pattern in self.inline_patterns.items():
                for match in pattern.finditer(text):
                    marker_info: Dict[str, Any] = {
                        "type": marker_type,
                        "start": match.start(),
                        "end": match.end(),
                        "content": match.group(0),
                        "groups": match.groups(),
                    }
                    markers.append(marker_info)

            # 開始位置でソート
            markers.sort(key=lambda x: x["start"])
            return markers

        except Exception as e:
            self.logger.error(f"インラインマーカー抽出中にエラー: {e}")
            return []

    def validate_inline_syntax(self, text: str) -> List[str]:
        """インライン記法の構文検証

        Args:
            text: 検証対象テキスト

        Returns:
            エラーメッセージリスト
        """
        try:
            errors = []

            # 未閉じマーカーのチェック
            open_markers = ["**", "*", "`"]
            for marker in open_markers:
                count = text.count(marker)
                if count % 2 != 0:
                    errors.append(f"未閉じのマーカー: {marker}")

            # リンク記法のチェック
            link_opens = text.count("[")
            link_closes = text.count("]")
            if link_opens != link_closes:
                errors.append("リンク記法の括弧が対応していません")

            return errors

        except Exception as e:
            self.logger.error(f"インライン構文検証中にエラー: {e}")
            return [f"検証エラー: {e}"]

    def get_processor_info(self) -> Dict[str, Any]:
        """プロセッサー情報を取得"""
        return {
            "name": "InlineMarkerProcessor",
            "version": "1.0.0",
            "supported_patterns": list(self.inline_patterns.keys()),
            "description": "インライン記法処理専用プロセッサー",
        }
