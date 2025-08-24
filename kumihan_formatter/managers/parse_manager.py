"""
ParseManager - Issue #1171 Manager統合最適化
============================================

一般的な解析処理を統括する統一Managerクラス
従来のParsingManagerから改名・機能整理
"""

from pathlib import Path
from typing import Any, Dict, List, Union

from kumihan_formatter.core.utilities.logger import get_logger


class ParseManager:
    """統合解析処理Manager - Issue #1171対応

    ParsingManagerの機能を統合し、全解析機能を統括する
    """

    def __init__(self):
        self.logger = get_logger(__name__)

        # 主要パーサー統合（遅延インポートで循環依存回避）
        self._main_parser = None
        self._block_parser = None
        self._keyword_parser = None
        self._list_parser = None
        self._content_parser = None
        self._markdown_parser = None

        self.logger.info(
            "ParseManager initialized - unified parsing system with integrated ParsingManager"
        )

    @property
    def main_parser(self):
        """メインパーサーの遅延初期化"""
        if self._main_parser is None:
            try:
                from ..parsers.main_parser import MainParser

                self._main_parser = MainParser()
            except ImportError as e:
                self.logger.warning(f"MainParser not available: {e}")
                self._main_parser = None
        return self._main_parser

    @property
    def block_parser(self):
        """ブロックパーサーの遅延初期化"""
        if self._block_parser is None:
            try:
                from ..parsers.block_parser import UnifiedBlockParser

                self._block_parser = UnifiedBlockParser()
            except ImportError as e:
                self.logger.warning(f"UnifiedBlockParser not available: {e}")
                self._block_parser = None
        return self._block_parser

    @property
    def keyword_parser(self):
        """キーワードパーサーの遅延初期化"""
        if self._keyword_parser is None:
            try:
                from ..parsers.keyword_parser import UnifiedKeywordParser

                self._keyword_parser = UnifiedKeywordParser()
            except ImportError as e:
                self.logger.warning(f"UnifiedKeywordParser not available: {e}")
                self._keyword_parser = None
        return self._keyword_parser

    @property
    def list_parser(self):
        """リストパーサーの遅延初期化"""
        if self._list_parser is None:
            try:
                from ..parsers.list_parser import UnifiedListParser

                self._list_parser = UnifiedListParser()
            except ImportError as e:
                self.logger.warning(f"UnifiedListParser not available: {e}")
                self._list_parser = None
        return self._list_parser

    @property
    def content_parser(self):
        """コンテンツパーサーの遅延初期化"""
        if self._content_parser is None:
            try:
                from ..parsers.content_parser import UnifiedContentParser

                self._content_parser = UnifiedContentParser()
            except ImportError as e:
                self.logger.warning(f"UnifiedContentParser not available: {e}")
                self._content_parser = None
        return self._content_parser

    @property
    def markdown_parser(self):
        """Markdownパーサーの遅延初期化"""
        if self._markdown_parser is None:
            try:
                from ..parsers.markdown_parser import UnifiedMarkdownParser

                self._markdown_parser = UnifiedMarkdownParser()
            except ImportError as e:
                self.logger.warning(f"UnifiedMarkdownParser not available: {e}")
                self._markdown_parser = None
        return self._markdown_parser

    def parse(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """統合解析エントリーポイント"""
        try:
            if parser_type == "auto":
                if self.main_parser:
                    return self.main_parser.parse(text)
                else:
                    # フォールバック：基本的な解析結果を返す
                    return {
                        "parsed_content": text,
                        "parser_type": parser_type,
                        "success": True,
                        "elements": [],
                        "fallback": True,
                    }
            elif parser_type == "block":
                if self.block_parser:
                    return self.block_parser.parse(text)
            elif parser_type == "keyword":
                if self.keyword_parser:
                    return self.keyword_parser.parse(text)
            elif parser_type == "list":
                if self.list_parser:
                    return self.list_parser.parse(text)
            elif parser_type == "content":
                if self.content_parser:
                    return self.content_parser.parse(text)
            elif parser_type == "markdown":
                if self.markdown_parser:
                    return self.markdown_parser.parse(text)
            else:
                self.logger.warning(
                    f"Unknown parser type: {parser_type}, using main parser"
                )
                if self.main_parser:
                    return self.main_parser.parse(text)

            # パーサーが利用できない場合のフォールバック
            self.logger.warning(f"Parser {parser_type} not available, using fallback")
            return {
                "parsed_content": text,
                "parser_type": parser_type,
                "success": True,
                "elements": [],
                "fallback": True,
            }

        except Exception as e:
            self.logger.error(f"Parsing error with {parser_type}: {e}")
            raise

    def parse_file(
        self, file_path: Union[str, Path], parser_type: str = "auto"
    ) -> Dict[str, Any]:
        """ファイル解析"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse(content, parser_type)
        except Exception as e:
            self.logger.error(f"File parsing error for {file_path}: {e}")
            raise

    def get_available_parsers(self) -> List[str]:
        """利用可能パーサー一覧"""
        return ["auto", "block", "keyword", "list", "content", "markdown"]

    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証"""
        try:
            if self.main_parser and hasattr(self.main_parser, "validate_syntax"):
                return self.main_parser.validate_syntax(text)
            else:
                return {"valid": True, "errors": [], "warnings": []}
        except Exception as e:
            self.logger.error(f"Syntax validation error: {e}")
            raise

    def get_parser_statistics(self) -> Dict[str, Any]:
        """パーサー統計情報"""
        stats = {
            "available_parsers": self.get_available_parsers(),
            "total_parsers": len(self.get_available_parsers()),
        }

        # メインパーサーの統計情報を追加
        if self.main_parser and hasattr(self.main_parser, "get_statistics"):
            try:
                stats["main_parser"] = self.main_parser.get_statistics()
            except Exception as e:
                self.logger.warning(f"Failed to get main parser statistics: {e}")

        return stats

    def shutdown(self) -> None:
        """リソース解放"""
        try:
            # 各パーサーのリソース解放
            for parser_name in [
                "_main_parser",
                "_block_parser",
                "_keyword_parser",
                "_list_parser",
                "_content_parser",
                "_markdown_parser",
            ]:
                parser = getattr(self, parser_name, None)
                if parser and hasattr(parser, "shutdown"):
                    try:
                        parser.shutdown()
                    except Exception as e:
                        self.logger.warning(f"Error shutting down {parser_name}: {e}")
                setattr(self, parser_name, None)

            self.logger.info("ParseManager shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during ParseManager shutdown: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
