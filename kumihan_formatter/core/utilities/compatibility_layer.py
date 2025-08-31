"""
互換性レイヤー - Phase3最適化版

MainParser→MasterParser統合により更新
レガシーAPIとの互換性を保持しつつ、最新アーキテクチャに対応
"""

from typing import Any, Dict, List, Optional

from ...parsers.unified_keyword_parser import UnifiedKeywordParser as KeywordParser
from ...parsers.unified_list_parser import UnifiedListParser as ListParser
from ...parsers.unified_markdown_parser import UnifiedMarkdownParser as MarkdownParser
from ...parsers.main_parser import MainParser as ActualMainParser
from ..ast_nodes.node import Node


class HtmlFormatter:
    """HTML フォーマッター - 互換性用簡易実装"""

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    def format(self, content: str) -> str:
        return content


class MarkdownFormatter:
    """Markdown フォーマッター - 互換性用簡易実装"""

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    def format(self, content: str) -> str:
        return content


class LegacyParserAdapter:
    """レガシーParser互換性アダプター"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._main_parser = ActualMainParser(config)

    def parse(self, text: str, **kwargs: Any) -> List[Node]:
        """MainParser互換parse - Nodeリスト返却"""
        result = self._main_parser.parse(text, **kwargs)
        if result is None:
            return []
        elif isinstance(result, dict):
            # Dict結果からNodeリストを抽出
            elements = result.get("elements", [])
            return [elem for elem in elements if hasattr(elem, "type")]
        elif hasattr(result, "type"):  # Nodeインスタンス
            return [result]
        else:
            return []

    def parse_streaming(self, text: str, **kwargs: Any) -> List[Node]:
        """ストリーミング解析 (MainParser互換)"""
        # 簡易実装: 通常のparseを呼び出し
        result = self._main_parser.parse(text, **kwargs)
        if result is None:
            return []
        elif isinstance(result, dict):
            # Dict結果からNodeリストを抽出
            elements = result.get("elements", [])
            return [elem for elem in elements if hasattr(elem, "type")]
        elif hasattr(result, "type"):  # Nodeインスタンス
            return [result]
        else:
            return []

    def parse_file(self, file_path: str, **kwargs: Any) -> List[Node]:
        """ファイル解析 (MainParser互換)"""
        result = self._main_parser.parse_file(file_path, **kwargs)
        if result is None:
            return []
        elif hasattr(result, "type"):  # Nodeインスタンス
            return [result]
        else:
            return []

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計 (MainParser互換)"""
        # 簡易実装: 基本的な統計情報を返す
        return {"calls": 0, "total_time": 0.0}

    def reset_statistics(self) -> None:
        """統計リセット (MainParser互換)"""
        # 簡易実装: 何もしない
        pass


# MainParser互換性エイリアス
MainParser = LegacyParserAdapter

# MasterParser互換性エイリアス
MasterParser = LegacyParserAdapter

# Parser(core)互換性エイリアス
Parser = LegacyParserAdapter

# StreamingParser互換性
StreamingParser = LegacyParserAdapter

# パーサーエイリアス
BlockParser = MarkdownParser
ContentParser = MarkdownParser


# Node作成関数（互換性用）
def create_node(node_type: str = "text", content: str = "", **kwargs: Any) -> Node:
    """Node作成関数 - 互換性用簡易実装"""
    return Node(type=node_type, content=content, **kwargs)


def error_node(message: str = "Error", **kwargs: Any) -> Node:
    """エラーNode作成関数 - 互換性用簡易実装"""
    return Node(type="error", content=message, **kwargs)


# 旧ファクトリー関数の互換版
def create_keyword_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式キーワードパーサー作成"""
    return KeywordParser()


def create_list_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式リストパーサー作成"""
    return ListParser()


def create_block_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式ブロックパーサー作成"""
    # ブロックパーサーは統合されたMarkdownパーサーを使用
    return MarkdownParser()


def create_markdown_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式Markdownパーサー作成"""
    return MarkdownParser()


def create_html_renderer(**kwargs: Any) -> HtmlFormatter:
    """後方互換: 旧式HTMLレンダラー作成"""
    return HtmlFormatter(**kwargs)


def create_markdown_renderer(**kwargs: Any) -> MarkdownFormatter:
    """後方互換: 旧式Markdownレンダラー作成"""
    return MarkdownFormatter(**kwargs)


def parse_text(text: str, config: Optional[Dict[str, Any]] = None) -> List[Node]:
    """テキストを解析する便利関数"""
    parser = MasterParser(config)
    return parser.parse(text, return_nodes=True)


def parse_file(file_path: str, config: Optional[Dict[str, Any]] = None) -> List[Node]:
    """ファイルを解析する便利関数"""
    parser = MasterParser(config)
    result = parser.parse_file(file_path)
    # resultはList[Node]なのでelementsアクセスは不要
    return result if result else []


def parse_stream(stream: Any, config: Optional[Dict[str, Any]] = None) -> List[Node]:
    """ストリームを解析する便利関数"""
    parser = MasterParser(config)
    return parser.parse_streaming(stream)


# エクスポート対象（Phase 2: 公開APIの最小化）
__all__ = [
    "MasterParser",
    "parse_text",
    "parse_file",
    "parse_stream",
]
